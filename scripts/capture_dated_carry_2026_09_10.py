"""One registered public snapshot measurement; no accounts, orders or historical replay."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

KEY = 'dated_carry_feasibility_2026_09_10'
DOC = Path('docs/carry-feasibility-2026-09-10')
OUTPUT = Path('data/carry-feasibility/2026-09-10/capture')
HOSTS = {'spot': 'https://api.binance.com/api/v3/', 'future': 'https://fapi.binance.com/fapi/v1/'}
ASSETS = ('BTC', 'ETH')
D = Decimal


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, obj):
    with path.open('x') as stream:
        json.dump(obj, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def preflight(source):
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    if head != source:
        raise ValueError('source HEAD differs from reviewed execution source')
    baseline = json.loads((DOC / 'baseline.json').read_text())
    gates = json.loads(Path('data/predlab/gates.json').read_text())
    gate = gates[KEY]
    if sha(Path(gate['charter']).read_bytes()) != gate['charter_sha256']:
        raise ValueError('registered charter hash differs')
    for key, expected in baseline['old_gate_objects'].items():
        raw = json.dumps(gates[key], sort_keys=True, separators=(',', ':')).encode()
        if sha(raw) != expected:
            raise ValueError('original gate changed: ' + key)
    if sha(Path('data/predlab/trial_ledger.jsonl').read_bytes()) != baseline['financial_ledger_sha256']:
        raise ValueError('financial ledger changed')
    for path in ('scripts/capture_dated_carry_2026_09_10.py', 'scripts/carry_feasibility_math_2026_09_10.py', 'data/predlab/gates.json', str(DOC / 'charter.md')):
        expected = subprocess.check_output(['git', 'show', f'{head}:{path}'])
        if Path(path).read_bytes() != expected:
            raise ValueError('execution input differs from committed source: ' + path)
    return {'source_commit': head, 'gate': gate, 'baseline': baseline}


class Capture:
    def __init__(self, directory):
        self.directory = directory
        (directory / 'raw').mkdir(parents=True, exist_ok=False)
        self.lock = threading.Lock()
        self.number = 0
        self.receipts = []
        self.stopped = False

    def get(self, market, endpoint, parameters=None):
        if market not in HOSTS or endpoint not in {'time', 'exchangeInfo', 'depth'}:
            raise ValueError('unregistered public endpoint')
        parameters = parameters or {}
        url = HOSTS[market] + endpoint + ('?' + urllib.parse.urlencode(parameters) if parameters else '')
        with self.lock:
            number = self.number
            self.number += 1
            stopped = self.stopped
        stem = f'{number:03d}_{market}_{endpoint}'
        start_ns = time.time_ns()
        start_mono = time.monotonic_ns()
        body, status, headers, error = b'', None, {}, None
        safe_headers = ('Date', 'Content-Type', 'X-MBX-USED-WEIGHT-1M', 'Retry-After')
        try:
            if stopped:
                raise ValueError('not_attempted_after_http_denial')
            request = urllib.request.Request(url, headers={'User-Agent': 'DatedCarryResearch/1.0', 'Accept': 'application/json'})
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read(32_000_001)
                status = response.status
                headers = {key: response.headers[key] for key in safe_headers if key in response.headers}
                if len(body) > 32_000_000:
                    error = 'response_exceeds_32MB_limit'
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read(32_000_001)
            headers = {key: exc.headers[key] for key in safe_headers if key in exc.headers}
            error = 'HTTPError'
            if status in {403, 418, 429, 451}:
                with self.lock:
                    self.stopped = True
        except (OSError, ValueError) as exc:
            error = 'not_attempted_after_denial' if stopped else type(exc).__name__ + ': ' + str(exc)
        end_ns, elapsed_ns = time.time_ns(), time.monotonic_ns() - start_mono
        raw_path = self.directory / 'raw' / (stem + '.bin')
        with raw_path.open('xb') as stream:
            stream.write(body)
        parsed = None
        if status == 200 and error is None:
            try:
                parsed = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                error = 'invalid_json'
        receipt = {'id': stem, 'url': url, 'parameters': parameters, 'market': market, 'endpoint': endpoint,
                   'start_ns': start_ns, 'end_ns': end_ns, 'elapsed_ns': elapsed_ns,
                   'start_utc': datetime.fromtimestamp(start_ns / 1e9, timezone.utc).isoformat(),
                   'end_utc': datetime.fromtimestamp(end_ns / 1e9, timezone.utc).isoformat(),
                   'http_status': status, 'headers': headers, 'error': error, 'attempted': not stopped,
                   'raw_path': str(raw_path), 'bytes': len(body), 'sha256': sha(body)}
        write_json(self.directory / 'raw' / (stem + '.json'), receipt)
        with self.lock:
            self.receipts.append(receipt)
        return receipt, parsed


def calibrate(receipt, payload):
    if receipt['error'] or not isinstance(payload, dict):
        raise ValueError('server clock unavailable')
    milliseconds = payload.get('serverTime')
    if type(milliseconds) is not int or not 1_500_000_000_000 < milliseconds < 4_100_000_000_000:
        raise ValueError('server clock is not valid UTC milliseconds')
    uncertainty = D(receipt['elapsed_ns']) / D(2_000_000)
    if uncertainty > D('2500'):
        raise ValueError('server clock calibration exceeds five seconds')
    midpoint = D(receipt['start_ns'] + receipt['end_ns']) / D(2_000_000)
    return {'offset_ms': str(D(milliseconds) - midpoint), 'uncertainty_ms': str(uncertainty), 'server_ms': milliseconds}


def normalize_rules(symbol):
    filters = {item['filterType']: item for item in symbol['filters']}
    lot = filters['LOT_SIZE']
    notional = filters.get('NOTIONAL', filters.get('MIN_NOTIONAL'))
    if not notional:
        raise ValueError('minimum notional filter unavailable')
    minimum = notional.get('minNotional', notional.get('notional'))
    if minimum is None:
        raise ValueError('minimum notional units unavailable')
    return {'step_size': lot['stepSize'], 'min_qty': lot['minQty'], 'max_qty': lot['maxQty'],
            'min_notional': minimum, 'max_notional': notional.get('maxNotional')}


def inventory(futures, spots, server_ms):
    if not isinstance(futures, dict) or not isinstance(futures.get('symbols'), list):
        raise ValueError('future inventory unavailable')
    if not isinstance(spots, dict) or not isinstance(spots.get('symbols'), list):
        raise ValueError('spot inventory unavailable')
    if any(not isinstance(symbol, dict) for symbol in futures['symbols'] + spots['symbols']):
        raise ValueError('instrument metadata item is not an object')
    spot_map = {s['symbol']: s for s in spots['symbols']}
    if len(spot_map) != len(spots['symbols']):
        raise ValueError('duplicate spot identity')
    seen, all_rows, selected = set(), [], {}
    for symbol in futures['symbols']:
        if symbol.get('baseAsset') not in ASSETS:
            continue
        identity = symbol.get('symbol')
        if not identity or identity in seen:
            raise ValueError('missing or duplicate future identity')
        seen.add(identity)
        reason = []
        if symbol.get('status') != 'TRADING':
            reason.append('not_trading')
        if symbol.get('quoteAsset') != 'USDT' or symbol.get('marginAsset') != 'USDT':
            reason.append('unsupported_quote_or_collateral')
        if symbol.get('contractType') not in {'CURRENT_QUARTER', 'NEXT_QUARTER', 'CURRENT_MONTH', 'NEXT_MONTH'}:
            reason.append('not_supported_conventional_dated_future')
        expiry = symbol.get('deliveryDate')
        if type(expiry) is not int or not 7 * 86400000 <= expiry - server_ms <= 180 * 86400000:
            reason.append('expiry_outside_fixed_window_or_unknown')
        spot = spot_map.get(symbol['baseAsset'] + 'USDT')
        if not spot or spot.get('status') != 'TRADING' or spot.get('isSpotTradingAllowed') is not True:
            reason.append('spot_pair_not_admitted')
        if spot and (spot.get('baseAsset') != symbol['baseAsset'] or spot.get('quoteAsset') != 'USDT'):
            reason.append('spot_pair_not_admitted')
        try:
            future_rules = normalize_rules(symbol)
            spot_rules = normalize_rules(spot) if spot else None
        except (KeyError, TypeError, ValueError):
            future_rules, spot_rules = None, None
            reason.append('quantity_or_notional_rules_unavailable')
        row = {'asset': symbol['baseAsset'], 'future_id': identity, 'spot_id': symbol['baseAsset'] + 'USDT',
               'expiry_ms': expiry, 'contract_type': symbol.get('contractType'), 'reasons': reason,
               'future_rules': future_rules, 'spot_rules': spot_rules, 'future_multiplier': '1', 'selected': False}
        all_rows.append(row)
    for asset in ASSETS:
        eligible = [row for row in all_rows if row['asset'] == asset and not row['reasons']]
        if eligible:
            row = min(eligible, key=lambda r: (r['expiry_ms'], r['future_id']))
            row['selected'] = True
            selected[asset] = row
    return {'inventory': all_rows, 'selected': selected, 'selection_server_ms': server_ms}


def admit_pair(spot_result, future_result, clocks):
    pairs = {'spot': spot_result, 'future': future_result}
    errors, qualifications, books = [], [], {}
    starts = [value[0]['start_ns'] for value in pairs.values()]
    ends = [value[0]['end_ns'] for value in pairs.values()]
    span = D(max(ends) - min(starts)) / D(1_000_000_000)
    if span > 5:
        errors.append('quote_pair_exceeds_five_seconds')
    ages = {}
    for market, (receipt, payload) in pairs.items():
        if receipt['error'] or not isinstance(payload, dict) or 'bids' not in payload or 'asks' not in payload:
            errors.append(market + '_book_unavailable')
            continue
        books[market] = {'bids': payload['bids'], 'asks': payload['asks']}
        event = payload.get('E')
        if event is None:
            qualifications.append(market + '_event_timestamp_unavailable')
            continue
        if type(event) is not int or not 1_500_000_000_000 < event < 4_100_000_000_000:
            errors.append(market + '_event_time_invalid')
            continue
        clock = clocks[market]
        estimated = D(receipt['end_ns']) / D(1_000_000) + D(clock['offset_ms'])
        uncertainty = D(clock['uncertainty_ms'])
        maximum_age = estimated + uncertainty - D(event)
        ages[market] = str(maximum_age)
        if maximum_age > 5000:
            errors.append(market + '_book_stale')
        if D(event) > estimated + uncertainty + 1000:
            errors.append(market + '_book_future_dated')
    return {'errors': errors, 'qualifications': qualifications, 'books': books,
            'pair_span_seconds': str(span), 'maximum_age_ms': ages,
            'decision_future_ms': str(D(max(ends)) / D(1_000_000) + D(clocks['future']['offset_ms'])),
            'receipts': {market: value[0]['id'] for market, value in pairs.items()}}


def calculate(snapshot, gate):
    from scripts.carry_feasibility_math_2026_09_10 import size_hedge, terminal_case
    entries, rows = [], []
    for asset, capital, reserve, fee in itertools.product(ASSETS, gate['capital'], gate['reserve_fractions'], gate['fee_multipliers']):
        pair = snapshot['pairs'].get(asset)
        identity = f"{snapshot['number']}|{asset}|{capital}|{reserve}|{fee}"
        errors = snapshot.get('errors', []) + (pair.get('errors', []) if pair else ['no_admitted_dated_instrument'])
        entry = {'status': 'unavailable', 'reason': ';'.join(errors)}
        seconds = None
        if not errors:
            spec = pair['instrument']
            seconds = (D(spec['expiry_ms']) - D(pair['decision_future_ms'])) / 1000
            try:
                entry = size_hedge(spot_book=pair['books']['spot'], future_book=pair['books']['future'],
                    spot_rules=spec['spot_rules'], future_rules=spec['future_rules'], capital=capital,
                    reserve_fraction=reserve, fee_multiplier=fee, future_multiplier=spec['future_multiplier'],
                    spot_fee=gate['spot_fee'], future_entry_fee=gate['future_entry_fee'], future_expiry_fee=gate['future_expiry_fee'])
            except (ValueError, ArithmeticError) as exc:
                entry = {'status': 'unavailable', 'reason': str(exc)}
        entries.append({'id': identity, 'asset': asset, 'snapshot': snapshot['number'], 'capital': capital,
                        'reserve': reserve, 'fee_multiplier': fee, 'entry': entry})
        for ratio, bps in itertools.product(gate['terminal_index_ratios'], gate['adverse_exit_bps']):
            result = entry
            if entry['status'] == 'complete':
                try:
                    result = terminal_case(entry, terminal_index_ratio=ratio, adverse_exit_bps=bps,
                        seconds_to_expiry=seconds, cash_benchmark_annual=gate['cash_benchmark_annual'])
                except (ValueError, ArithmeticError) as exc:
                    result = {'status': 'unavailable', 'reason': str(exc)}
            rows.append({'measurement_id': identity + '|' + ratio + '|' + bps, 'experiment': KEY,
                'asset': asset, 'snapshot': snapshot['number'], 'capital': capital, 'reserve': reserve,
                'fee_multiplier': fee, 'terminal_index_ratio': ratio, 'adverse_exit_bps': bps,
                'instrument': pair['instrument']['future_id'] if pair else None,
                'qualifications': (pair.get('qualifications', []) if pair else []) +
                    ['fee_basis_and_account_rates_unverified', 'margin_survival_unverified', 'public_depth_not_fills', 'USDT_capital_scenario_not_fiat_conversion'],
                'executable_admission': False, 'strategy_validated': False, 'result': result})
    return entries, rows


def execute(source):
    admitted = preflight(source)
    if OUTPUT.exists() or (OUTPUT.parent / 'measurement_ledger.jsonl').exists():
        raise FileExistsError('capture or measurement ledger already exists; no replacement acquisition')
    capture = Capture(OUTPUT)
    gate = admitted['gate']
    write_json(OUTPUT / 'start.json', admitted)
    errors, clocks, selected = [], {}, {}
    metadata_results = {}
    for market in HOSTS:
        result = capture.get(market, 'time')
        try:
            clocks[market] = calibrate(*result)
        except ValueError as exc:
            errors.append(market + ': ' + str(exc))
    metadata_results['future'] = capture.get('future', 'exchangeInfo')
    metadata_results['spot'] = capture.get('spot', 'exchangeInfo', {'symbols': json.dumps(['BTCUSDT', 'ETHUSDT'], separators=(',', ':'))})
    initial = None
    if not errors and all(not r[0]['error'] for r in metadata_results.values()):
        try:
            initial = inventory(metadata_results['future'][1], metadata_results['spot'][1], clocks['future']['server_ms'])
            selected = initial['selected']
        except (ValueError, TypeError, KeyError) as exc:
            errors.append('metadata: ' + str(exc))
    else:
        errors.append('metadata_or_clock_unavailable')
    write_json(OUTPUT / 'inventory.json', {'clocks': clocks, 'errors': errors, 'inventory': initial})
    start_mono = time.monotonic()
    snapshots, entries, rows = [], [], []
    for number, offset in enumerate(gate['snapshot_offsets_seconds']):
        delay = start_mono + offset - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        snapshot = {'number': number, 'scheduled_offset_seconds': offset,
                    'actual_offset_seconds': time.monotonic() - start_mono, 'errors': list(errors), 'pairs': {}}
        with ThreadPoolExecutor(max_workers=4) as pool:
            calls = {asset: (pool.submit(capture.get, 'spot', 'depth', {'symbol': spec['spot_id'], 'limit': 100}),
                             pool.submit(capture.get, 'future', 'depth', {'symbol': spec['future_id'], 'limit': 100}))
                     for asset, spec in selected.items()}
            for asset, (spot_call, future_call) in calls.items():
                pair = admit_pair(spot_call.result(), future_call.result(), clocks)
                pair['instrument'] = selected[asset]
                snapshot['pairs'][asset] = pair
        write_json(OUTPUT / f'snapshot_{number}.json', snapshot)
        new_entries, new_rows = calculate(snapshot, gate)
        entries.extend(new_entries)
        rows.extend(new_rows)
        snapshots.append(snapshot)
        print(json.dumps({'snapshot': number, 'measured_cells': len(new_rows),
                          'complete': sum(r['result']['status'] == 'complete' for r in new_rows),
                          'errors': snapshot['errors']}), flush=True)
    expected = len(ASSETS) * len(gate['capital']) * len(gate['reserve_fractions']) * len(gate['fee_multipliers']) * len(gate['terminal_index_ratios']) * len(gate['adverse_exit_bps']) * gate['snapshots']
    assert len(rows) == expected and len({r['measurement_id'] for r in rows}) == expected
    write_json(OUTPUT / 'entries.json', entries)
    ledger = OUTPUT.parent / 'measurement_ledger.jsonl'
    with ledger.open('x') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    preflight(source)
    manifest = {'experiment': KEY, 'source_commit': source, 'measurement_rows': len(rows),
                'complete_rows': sum(r['result']['status'] == 'complete' for r in rows),
                'financial_ledger_unchanged': True, 'requests': sorted(capture.receipts, key=lambda r: r['id']),
                'ledger_path': str(ledger), 'ledger_sha256': sha(ledger.read_bytes()),
                'files': {str(p): sha(p.read_bytes()) for p in sorted(OUTPUT.rglob('*')) if p.is_file()},
                'finished_utc': datetime.now(timezone.utc).isoformat(), 'validated_strategies': 0}
    write_json(OUTPUT / 'manifest.json', manifest)
    print(json.dumps({'manifest': str(OUTPUT / 'manifest.json'), 'rows': len(rows), 'complete': manifest['complete_rows']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-source', required=True)
    arguments = parser.parse_args()
    execute(arguments.execute_source)
