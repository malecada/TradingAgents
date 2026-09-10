"""Offline admission regressions; no market values or network are consumed."""
from __future__ import annotations

import copy
from decimal import Decimal
from email.message import Message
import hashlib
import io
import json
from pathlib import Path
import types
import urllib.error

import pytest

from scripts import capture_dated_carry_2026_09_10 as collector

NOW = 1_800_000_000_000
DAY = 86_400_000


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Unexpected live network request in offline test')
    monkeypatch.setattr(collector.urllib.request, 'urlopen', forbidden)


def filters(*, future=False):
    return [
        {'filterType': 'PRICE_FILTER', 'minPrice': '0.01', 'maxPrice': '1000000', 'tickSize': '0.01'},
        {'filterType': 'LOT_SIZE', 'minQty': '0.01', 'maxQty': '1000', 'stepSize': '0.01'},
        ({'filterType': 'MIN_NOTIONAL', 'notional': '5'} if future else
         {'filterType': 'NOTIONAL', 'minNotional': '5', 'maxNotional': '1000000',
          'applyMinToMarket': True, 'applyMaxToMarket': False, 'avgPriceMins': 5}),
    ]


def future(asset='BTC', days=30, identity=None, **changes):
    value = {'symbol': identity or f'{asset}USDT_270115', 'pair': asset + 'USDT',
             'baseAsset': asset, 'quoteAsset': 'USDT', 'marginAsset': 'USDT',
             'contractType': 'CURRENT_QUARTER', 'status': 'TRADING',
             'deliveryDate': NOW + days * DAY, 'onboardDate': NOW - 30 * DAY,
             'filters': filters(future=True)}
    value.update(changes)
    return value


def spot(asset='BTC', **changes):
    value = {'symbol': asset + 'USDT', 'baseAsset': asset, 'quoteAsset': 'USDT',
             'status': 'TRADING', 'isSpotTradingAllowed': True,
             'filters': filters()}
    value.update(changes)
    return value


def inventory(rows, spot_rows=None):
    return collector.inventory({'symbols': rows}, {'symbols': spot_rows or [spot(), spot('ETH')]}, NOW)


def receipt(*, market='future', start_ms=NOW, end_ms=NOW + 100, elapsed_ns=100_000_000, error=None):
    return {'id': 'fixture_' + market, 'start_ns': start_ms * 1_000_000,
            'end_ns': end_ms * 1_000_000, 'elapsed_ns': elapsed_ns, 'error': error,
            'http_status': 200}


def clock(offset='0', uncertainty='0'):
    return {'offset_ms': offset, 'uncertainty_ms': uncertainty, 'server_ms': NOW}


def book(event=NOW + 100):
    value = {'lastUpdateId': 123, 'bids': [['99', '10']], 'asks': [['100', '10']]}
    if event is not None:
        value['E'] = event
    return value


def gate():
    return {'capital': ['1000', '10000'], 'reserve_fractions': ['1', '1/3'],
            'fee_multipliers': ['1', '2'], 'terminal_index_ratios': ['0.5', '1', '2'],
            'adverse_exit_bps': ['0', '10', '50'], 'cash_benchmark_annual': ['0', '0.03', '0.05'],
            'snapshot_offsets_seconds': [0, 30, 60], 'snapshots': 3,
            'spot_fee': '0.001', 'future_entry_fee': '0.0005', 'future_expiry_fee': '0.0005'}


def test_calendar_selection_uses_earliest_expiry_then_symbol_and_keeps_all_candidates():
    rows = [future(days=60, identity='BTCUSDT_270201'),
            future(days=30, identity='BTCUSDT_270102'),
            future(days=30, identity='BTCUSDT_270101'), future('ETH', days=31)]
    result = inventory(rows)
    assert result['selected']['BTC']['future_id'] == 'BTCUSDT_270101'
    assert result['selected']['ETH']['expiry_ms'] == NOW + 31 * DAY
    assert len(result['inventory']) == 4
    assert sum(r['selected'] for r in result['inventory']) == 2


@pytest.mark.parametrize('days,eligible', [(6, False), (7, True), (180, True), (181, False)])
def test_expiry_admission_includes_only_registered_calendar_boundary(days, eligible):
    result = inventory([future(days=days)])
    assert ('BTC' in result['selected']) is eligible
    assert len(result['inventory']) == 1
    assert bool(result['inventory'][0]['reasons']) is not eligible


@pytest.mark.parametrize('changes', [
    {'contractType': 'PERPETUAL'}, {'contractType': 'UNKNOWN'}, {'status': 'PENDING_TRADING'},
    {'quoteAsset': 'USDC'}, {'marginAsset': 'BTC'}, {'deliveryDate': str(NOW + 30 * DAY)},
    {'deliveryDate': NOW // 1000 + 30 * 86400},
])
def test_unsupported_contracts_remain_visible_but_never_selected(changes):
    result = inventory([future(**changes)])
    assert result['selected'] == {}
    assert len(result['inventory']) == 1 and result['inventory'][0]['reasons']


@pytest.mark.parametrize('changes', [{'status': 'BREAK'}, {'isSpotTradingAllowed': False}])
def test_untradeable_spot_blocks_derivative_pair(changes):
    assert inventory([future()], [spot(**changes)])['selected'] == {}


@pytest.mark.parametrize('changes', [{'baseAsset': 'ETH'}, {'quoteAsset': 'USDC'}])
def test_contradictory_spot_asset_metadata_never_admits_pair(changes):
    result = inventory([future()], [spot(**changes)])
    assert result['selected'] == {}, 'A symbol name cannot override contradictory base/quote metadata'
    assert result['inventory'][0]['reasons']


@pytest.mark.parametrize('duplicate_spot', [False, True])
def test_duplicate_identities_are_unavailable_instead_of_last_row_wins(duplicate_spot):
    with pytest.raises(ValueError, match='duplicate'):
        inventory([future()] if duplicate_spot else [future(), future()],
                  [spot(), spot()] if duplicate_spot else [spot()])


def test_normalized_spot_and_future_notional_rules_keep_native_fields():
    result = inventory([future()])['selected']['BTC']
    assert result['future_rules'] == {'step_size': '0.01', 'min_qty': '0.01', 'max_qty': '1000',
                                      'min_notional': '5', 'max_notional': None}
    assert result['spot_rules']['max_notional'] == '1000000'
    assert result['future_multiplier'] == '1'


def test_missing_lot_or_notional_rules_retain_unavailable_candidate():
    bad = future(filters=[{'filterType': 'PRICE_FILTER', 'tickSize': '0.01'}])
    result = inventory([bad])
    assert not result['selected']
    assert 'quantity_or_notional_rules_unavailable' in result['inventory'][0]['reasons']


def test_calibrated_clock_carries_hand_checked_half_round_trip_uncertainty():
    result = collector.calibrate(receipt(start_ms=NOW, end_ms=NOW + 200, elapsed_ns=200_000_000),
                                 {'serverTime': NOW + 125})
    assert result == {'offset_ms': '25', 'uncertainty_ms': '100', 'server_ms': NOW + 125}


@pytest.mark.parametrize('bad_clock', [NOW // 1000, NOW * 1000, str(NOW), True, None])
def test_clock_rejects_seconds_microseconds_and_untyped_values(bad_clock):
    with pytest.raises(ValueError, match='milliseconds'):
        collector.calibrate(receipt(), {'serverTime': bad_clock})


def test_clock_round_trip_five_seconds_is_inclusive():
    assert collector.calibrate(receipt(elapsed_ns=5_000_000_000), {'serverTime': NOW})['uncertainty_ms'] == '2500'
    with pytest.raises(ValueError, match='five seconds'):
        collector.calibrate(receipt(elapsed_ns=5_000_000_001), {'serverTime': NOW})


def test_missing_spot_event_is_qualified_and_futures_clock_is_checked():
    result = collector.admit_pair((receipt(market='spot'), book(None)), (receipt(), book()),
                                  {'spot': clock(), 'future': clock()})
    assert result['errors'] == []
    assert result['qualifications'] == ['spot_event_timestamp_unavailable']
    assert result['maximum_age_ms']['future'] == '0'


@pytest.mark.parametrize('event_delta,uncertainty,want_error', [
    (-4900, '100', True), (-4900, '0', False), (-4899, '0', False),
])
def test_event_age_uses_upper_uncertainty_bound(event_delta, uncertainty, want_error):
    result = collector.admit_pair((receipt(market='spot'), book(None)),
                                  (receipt(), book(NOW + event_delta)),
                                  {'spot': clock(), 'future': clock(uncertainty=uncertainty)})
    assert ('future_book_stale' in result['errors']) is want_error


@pytest.mark.parametrize('event_delta,want_error', [(1200, False), (1201, True)])
def test_future_event_tolerance_uses_calibrated_upper_bound(event_delta, want_error):
    result = collector.admit_pair((receipt(market='spot'), book(None)),
                                  (receipt(), book(NOW + event_delta)),
                                  {'spot': clock(), 'future': clock(uncertainty='100')})
    assert ('future_book_future_dated' in result['errors']) is want_error


@pytest.mark.parametrize('bad_event', [NOW // 1000, str(NOW), True])
def test_present_malformed_event_cannot_be_treated_as_missing(bad_event):
    result = collector.admit_pair((receipt(market='spot'), book(None)), (receipt(), book(bad_event)),
                                  {'spot': clock(), 'future': clock()})
    assert 'future_event_time_invalid' in result['errors']


@pytest.mark.parametrize('end_delta,want_error', [(5000, False), (5001, True)])
def test_pair_skew_includes_earliest_request_and_latest_receipt(end_delta, want_error):
    result = collector.admit_pair((receipt(market='spot', end_ms=NOW + end_delta), book(None)),
                                  (receipt(start_ms=NOW + 100, end_ms=NOW + end_delta), book(NOW + end_delta)),
                                  {'spot': clock(), 'future': clock()})
    assert ('quote_pair_exceeds_five_seconds' in result['errors']) is want_error


class Response:
    def __init__(self, body, status=200, headers=None):
        self.body, self.status, self.headers = body, status, headers or {'Content-Type': 'application/json'}
    def read(self, n):
        return self.body[:n]
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


def test_raw_receipt_is_byte_exact_immutable_public_and_single_attempt(tmp_path, monkeypatch):
    raw = b'{ "serverTime": 1800000000000 }\n'
    requests = []
    def transport(request, timeout):
        requests.append((request, timeout))
        return Response(raw)
    monkeypatch.setattr(collector.urllib.request, 'urlopen', transport)
    capture = collector.Capture(tmp_path / 'capture')
    rec, parsed = capture.get('future', 'time')
    assert parsed == {'serverTime': NOW}
    assert Path(rec['raw_path']).read_bytes() == raw
    assert rec['sha256'] == hashlib.sha256(raw).hexdigest()
    assert rec['start_utc'].endswith('+00:00') and rec['end_utc'].endswith('+00:00')
    assert len(requests) == 1 and requests[0][1] == 15
    request = requests[0][0]
    assert request.get_method() == 'GET' and request.data is None
    assert not any(k.lower() in {'authorization', 'cookie', 'x-mbx-apikey'} for k, _ in request.header_items())
    assert set(rec['parameters']) == set()
    with pytest.raises(FileExistsError):
        collector.Capture(tmp_path / 'capture')
    assert Path(rec['raw_path']).read_bytes() == raw


def test_http_denial_retains_body_and_retry_after_without_retry(tmp_path, monkeypatch):
    body = b'{"code": -1003, "msg": "Rate limit"}'
    headers = Message()
    headers['Retry-After'] = '60'
    headers['X-MBX-USED-WEIGHT-1M'] = '2400'
    attempts = []
    def transport(request, timeout):
        attempts.append(request.full_url)
        raise urllib.error.HTTPError(request.full_url, 429, 'limit', headers, io.BytesIO(body))
    monkeypatch.setattr(collector.urllib.request, 'urlopen', transport)
    rec, parsed = collector.Capture(tmp_path / 'capture').get('spot', 'depth', {'symbol': 'BTCUSDT', 'limit': 100})
    assert len(attempts) == 1 and parsed is None and rec['http_status'] == 429
    assert Path(rec['raw_path']).read_bytes() == body
    assert rec['headers'].get('Retry-After') == '60', 'Denial headers are part of the immutable source evidence'


def test_invalid_json_and_timeout_are_retained_as_unavailable(tmp_path, monkeypatch):
    def transport(request, timeout):
        if request.full_url.endswith('time'):
            return Response(b'not-json')
        raise TimeoutError('synthetic timeout')
    monkeypatch.setattr(collector.urllib.request, 'urlopen', transport)
    capture = collector.Capture(tmp_path / 'capture')
    first, data = capture.get('future', 'time')
    second, data2 = capture.get('future', 'exchangeInfo')
    assert data is None and data2 is None
    assert first['error'] == 'invalid_json' and 'TimeoutError' in second['error']
    assert len(list((tmp_path / 'capture' / 'raw').glob('*.json'))) == 2
    assert Path(second['raw_path']).read_bytes() == b''


def test_private_or_unregistered_endpoint_is_rejected_before_request(tmp_path):
    capture = collector.Capture(tmp_path / 'capture')
    with pytest.raises(ValueError, match='unregistered'):
        capture.get('future', 'account')
    with pytest.raises(ValueError, match='unregistered'):
        capture.get('other', 'depth')
    assert capture.receipts == []


def test_existing_measurement_ledger_refuses_before_network_or_new_capture(tmp_path, monkeypatch):
    ledger = tmp_path / 'measurement_ledger.jsonl'
    ledger.write_bytes(b'{"preserved":true}\n')
    monkeypatch.setattr(collector, 'OUTPUT', tmp_path / 'capture')
    monkeypatch.setattr(collector, 'preflight', lambda source: {'gate': gate(), 'source_commit': source})
    with pytest.raises((FileExistsError, ValueError)):
        collector.execute('synthetic')
    assert ledger.read_bytes() == b'{"preserved":true}\n'
    assert not (tmp_path / 'capture').exists(), 'Existing ledger must stop a second acquisition before namespace reservation'


@pytest.mark.parametrize('status', [403, 418, 429, 451])
def test_denial_stops_later_requests_and_keeps_not_attempted_receipt(tmp_path, monkeypatch, status):
    calls = []
    def transport(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            raise urllib.error.HTTPError(request.full_url, status, 'denied', Message(), io.BytesIO(b'denied'))
        return Response(b'{"serverTime":1800000000000}')
    monkeypatch.setattr(collector.urllib.request, 'urlopen', transport)
    capture = collector.Capture(tmp_path / 'capture')
    first, _ = capture.get('future', 'time')
    later, parsed = capture.get('spot', 'time')
    assert len(calls) == 1, 'A later planned request must not continue after a provider denial'
    assert first['http_status'] == status
    assert parsed is None and later['error'] == 'not_attempted_after_denial'
    assert Path(later['raw_path']).read_bytes() == b''
    assert len(capture.receipts) == 2


def test_global_source_unavailability_retains_all_432_scenarios_and_48_entries(tmp_path, monkeypatch):
    import sys
    mathematical_calls = []
    def no_math(*args, **kwargs):
        mathematical_calls.append(True)
        raise AssertionError('Unavailable inputs must not enter the cash model')
    monkeypatch.setitem(sys.modules, 'scripts.carry_feasibility_math_2026_09_10',
                        types.SimpleNamespace(size_hedge=no_math, terminal_case=no_math))
    monkeypatch.setattr(collector, 'OUTPUT', tmp_path / 'capture')
    monkeypatch.setattr(collector, 'preflight', lambda source: {'gate': gate(), 'source_commit': source})
    clock_state = [1000.0]
    monkeypatch.setattr(collector.time, 'monotonic', lambda: clock_state[0])
    monkeypatch.setattr(collector.time, 'monotonic_ns', lambda: int(clock_state[0] * 1_000_000_000))
    monkeypatch.setattr(collector.time, 'sleep', lambda delay: clock_state.__setitem__(0, clock_state[0] + delay))
    requests = []
    def transport(request, timeout):
        requests.append(request.full_url)
        raise urllib.error.HTTPError(request.full_url, 451, 'unavailable', Message(), io.BytesIO(b'region denied'))
    monkeypatch.setattr(collector.urllib.request, 'urlopen', transport)
    collector.execute('synthetic')
    rows = [json.loads(line) for line in (tmp_path / 'measurement_ledger.jsonl').read_text().splitlines()]
    entries = json.loads((tmp_path / 'capture' / 'entries.json').read_text())
    assert len(rows) == 432 and len({r['measurement_id'] for r in rows}) == 432
    assert len(entries) == 48 and len({r['id'] for r in entries}) == 48
    assert {r['snapshot'] for r in rows} == {0, 1, 2}
    assert {r['asset'] for r in rows} == {'BTC', 'ETH'}
    assert all(r['result']['status'] == 'unavailable' and r['result']['reason'] for r in rows)
    assert all(not r['strategy_validated'] and not r['executable_admission'] for r in rows)
    assert mathematical_calls == []
    assert len(requests) == 1
    manifest = json.loads((tmp_path / 'capture' / 'manifest.json').read_text())
    assert manifest['measurement_rows'] == 432 and manifest['complete_rows'] == 0
    assert len(manifest['requests']) == 4
    for filename, digest in manifest['files'].items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == digest


def report_fixture(tmp_path, monkeypatch):
    """Full dimensional identities, with unavailable outcomes and real saved hashes."""
    import itertools
    from scripts import report_dated_carry_2026_09_10 as report
    root, docs = tmp_path / 'data', tmp_path / 'docs'
    capture_dir = root / 'capture'
    capture_dir.mkdir(parents=True)
    docs.mkdir()
    monkeypatch.setattr(report, 'ROOT', root)
    monkeypatch.setattr(report, 'DOC', docs)
    rows, entries = [], []
    for snap, asset, cap, reserve, fee in itertools.product(range(3), ('BTC', 'ETH'), ('1000', '10000'), ('1', '1/3'), ('1', '2')):
        identity = f'{snap}|{asset}|{cap}|{reserve}|{fee}'
        entries.append({'id': identity, 'asset': asset, 'snapshot': snap, 'capital': cap,
                        'reserve': reserve, 'fee_multiplier': fee,
                        'entry': {'status': 'unavailable', 'reason': 'fixture unavailable'}})
        for ratio, bps in itertools.product(('0.5', '1', '2'), ('0', '10', '50')):
            rows.append({'measurement_id': f'{identity}|{ratio}|{bps}', 'experiment': collector.KEY,
                         'snapshot': snap, 'asset': asset, 'capital': cap, 'reserve': reserve,
                         'fee_multiplier': fee, 'terminal_index_ratio': ratio, 'adverse_exit_bps': bps,
                         'instrument': None, 'qualifications': ['fixture unavailable'],
                         'executable_admission': False, 'strategy_validated': False,
                         'result': {'status': 'unavailable', 'reason': 'fixture unavailable'}})
    (capture_dir / 'inventory.json').write_text(json.dumps({'inventory': None, 'errors': ['fixture unavailable']}))
    (capture_dir / 'entries.json').write_text(json.dumps(entries))
    def save(changed_rows=rows):
        ledger = root / 'measurement_ledger.jsonl'
        ledger.write_text(''.join(json.dumps(r) + '\n' for r in changed_rows))
        manifest = {'source_commit': 'synthetic', 'experiment': collector.KEY,
                    'measurement_rows': len(changed_rows),
                    'complete_rows': sum(r['result']['status'] == 'complete' for r in changed_rows),
                    'ledger_path': str(ledger), 'ledger_sha256': hashlib.sha256(ledger.read_bytes()).hexdigest(),
                    'files': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in capture_dir.iterdir() if p.name != 'manifest.json'},
                    'financial_ledger_unchanged': True}
        (capture_dir / 'manifest.json').write_text(json.dumps(manifest))
    save()
    return report, rows, save, root, docs


def test_report_rejects_changed_ledger_instead_of_rebinding_unverified_values(tmp_path, monkeypatch):
    report, rows, save, root, docs = report_fixture(tmp_path, monkeypatch)
    with (root / 'measurement_ledger.jsonl').open('a') as stream:
        stream.write(json.dumps(rows[0]) + '\n')
    with pytest.raises((ValueError, AssertionError)):
        report.build()
    assert not (docs / 'RESULTS.md').exists()


def test_report_rejects_duplicate_screen_identities_even_with_matching_hash(tmp_path, monkeypatch):
    report, rows, save, root, docs = report_fixture(tmp_path, monkeypatch)
    target = [i for i,r in enumerate(rows) if r['asset'] == 'BTC' and r['capital'] == '1000'
              and r['reserve'] == '1' and r['fee_multiplier'] == '2' and r['adverse_exit_bps'] == '10']
    assert len(target) == 9
    fabricated = copy.deepcopy(rows[target[0]])
    fabricated['result'] = {'status': 'complete', 'net_cash_profit': '1',
                            'net_return_on_capital': '0.001', 'annualized_simple_return': '0.01'}
    for index in target:
        rows[index] = copy.deepcopy(fabricated)
    save(rows)
    with pytest.raises((ValueError, AssertionError)):
        report.build()
    assert not (docs / 'screen-summary.json').exists()


def test_report_refuses_existing_outputs_before_touching_either_file(tmp_path, monkeypatch):
    report, rows, save, root, docs = report_fixture(tmp_path, monkeypatch)
    (docs / 'screen-summary.json').write_bytes(b'{"preserved": true}\n')
    with pytest.raises((ValueError, FileExistsError)):
        report.build()
    assert (docs / 'screen-summary.json').read_bytes() == b'{"preserved": true}\n'
    assert not (docs / 'RESULTS.md').exists()


def test_real_calculation_retains_missing_asset_and_malformed_book_cells():
    spec = inventory([future()])['selected']['BTC']
    pair = collector.admit_pair((receipt(market='spot'), book(None)), (receipt(), book()),
                                {'spot': clock(), 'future': clock()})
    pair['instrument'] = spec
    snapshot = {'number': 0, 'errors': [], 'pairs': {'BTC': pair}}
    entries, rows = collector.calculate(snapshot, gate())
    assert len(entries) == 16 and len(rows) == 144
    assert sum(e['entry']['status'] == 'complete' for e in entries) == 8
    assert sum(r['result']['status'] == 'complete' for r in rows) == 72
    assert all(r['result']['status'] == 'unavailable' for r in rows if r['asset'] == 'ETH')
    assert all(not r['executable_admission'] and not r['strategy_validated'] for r in rows)
    pair['books']['spot']['asks'] = [['98', '10']]  # Crossed against bid99; cannot be a coherent source book.
    entries, rows = collector.calculate(snapshot, gate())
    assert len(rows) == 144 and all(r['result']['status'] == 'unavailable' for r in rows)
    assert all(r['result']['reason'] for r in rows)


@pytest.mark.parametrize('malformed_symbol', [None, 'BTCUSDT'])
def test_malformed_future_metadata_retains_all_unavailable_identities(tmp_path, monkeypatch, malformed_symbol):
    monkeypatch.setattr(collector, 'OUTPUT', tmp_path / 'capture')
    monkeypatch.setattr(collector, 'preflight', lambda source: {'gate': gate(), 'source_commit': source})
    clock_state = [1000.0]
    monkeypatch.setattr(collector.time, 'monotonic', lambda: clock_state[0])
    monkeypatch.setattr(collector.time, 'sleep', lambda delay: clock_state.__setitem__(0, clock_state[0] + delay))
    def transport(request, timeout):
        if request.full_url.endswith('/time'):
            payload = {'serverTime': NOW}
        elif '/fapi/v1/exchangeInfo' in request.full_url:
            payload = {'symbols': [malformed_symbol]}
        elif '/api/v3/exchangeInfo' in request.full_url:
            payload = {'symbols': [spot(), spot('ETH')]}
        else:
            raise AssertionError('Bad inventory must not cause depth capture')
        return Response(json.dumps(payload).encode())
    monkeypatch.setattr(collector.urllib.request, 'urlopen', transport)
    collector.execute('synthetic')
    rows = [json.loads(line) for line in (tmp_path / 'measurement_ledger.jsonl').read_text().splitlines()]
    assert len(rows) == 432 and len({r['measurement_id'] for r in rows}) == 432
    assert all(r['result']['status'] == 'unavailable' and r['result']['reason'] for r in rows)


def test_successful_synthetic_capture_freezes_two_ids_and_retains_all_scenarios(tmp_path, monkeypatch):
    import urllib.parse
    monkeypatch.setattr(collector, 'OUTPUT', tmp_path / 'capture')
    monkeypatch.setattr(collector, 'preflight', lambda source: {'gate': gate(), 'source_commit': source})
    clock_state = [1000.0]
    monkeypatch.setattr(collector.time, 'monotonic', lambda: clock_state[0])
    monkeypatch.setattr(collector.time, 'monotonic_ns', lambda: int(clock_state[0] * 1_000_000_000))
    monkeypatch.setattr(collector.time, 'time_ns', lambda: (NOW + int((clock_state[0] - 1000) * 1000)) * 1_000_000)
    monkeypatch.setattr(collector.time, 'sleep', lambda delay: clock_state.__setitem__(0, clock_state[0] + delay))
    requests = []
    def transport(request, timeout):
        url = urllib.parse.urlparse(request.full_url)
        params = urllib.parse.parse_qs(url.query)
        requests.append((url.path, params))
        current = NOW + int((clock_state[0] - 1000) * 1000)
        if url.path.endswith('/time'):
            payload = {'serverTime': current}
        elif url.path == '/fapi/v1/exchangeInfo':
            payload = {'symbols': [future(), future(days=60, identity='BTCUSDT_270201'), future('ETH')]}
        elif url.path == '/api/v3/exchangeInfo':
            assert params == {'symbols': ['["BTCUSDT","ETHUSDT"]']}
            payload = {'symbols': [spot(), spot('ETH')]}
        elif url.path.endswith('/depth'):
            assert params['limit'] == ['100']
            if url.path.startswith('/fapi/'):
                assert params['symbol'][0] in {'BTCUSDT_270115', 'ETHUSDT_270115'}
                payload = {'E': current, 'T': current, 'lastUpdateId': 1,
                           'bids': [['102', '100']], 'asks': [['103', '100']]}
            else:
                assert params['symbol'][0] in {'BTCUSDT', 'ETHUSDT'}
                payload = book(None)
        else:
            raise AssertionError('Unexpected endpoint')
        return Response(json.dumps(payload).encode())
    monkeypatch.setattr(collector.urllib.request, 'urlopen', transport)
    collector.execute('synthetic')
    ledger = [json.loads(line) for line in (tmp_path / 'measurement_ledger.jsonl').read_text().splitlines()]
    entries = json.loads((tmp_path / 'capture' / 'entries.json').read_text())
    assert len(requests) == 16
    assert sum(p == '/fapi/v1/exchangeInfo' for p, _ in requests) == 1
    assert len(ledger) == 432 and len(entries) == 48
    assert all(r['result']['status'] == 'complete' for r in ledger)
    assert {r['instrument'] for r in ledger} == {'BTCUSDT_270115', 'ETHUSDT_270115'}
    assert all('spot_event_timestamp_unavailable' in r['qualifications'] for r in ledger)
    for n, expected_offset in enumerate((0, 30, 60)):
        snap = json.loads((tmp_path / 'capture' / f'snapshot_{n}.json').read_text())
        assert snap['scheduled_offset_seconds'] == expected_offset == snap['actual_offset_seconds']


def test_full_unavailable_report_keeps_denominator_and_never_promotes(tmp_path, monkeypatch):
    report, rows, save, root, docs = report_fixture(tmp_path, monkeypatch)
    report.build()
    saved = json.loads((docs / 'screen-summary.json').read_text())
    assert saved['statuses'] == {'unavailable': 432}
    assert len(saved['screens']) == 4
    assert all(r['retained_cells'] == 9 and not r['complete'] and not r['necessary_cash_screen_pass']
               and not r['executable_admission'] and not r['strategy_validated'] for r in saved['screens'])
    text = (docs / 'RESULTS.md').read_text()
    assert '**432 scenario rows**' in text and '**0** are calculable' in text
    assert 'All 48 entry-size cases' in text
