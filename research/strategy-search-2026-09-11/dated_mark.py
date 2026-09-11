"""Exactly two historical dated-mark source cells; no economic calculation."""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
import dated_mark_transport

EXPERIMENT = 'dated-mark-20260911'
REGISTRATION = 'research/strategy-search-2026-09-11/gates-dated-mark.json'
START = 1777593600000
DAY = 86400000
COUNT = 56
END = START + COUNT * DAY - 1
MAX_OUTPUT_BYTES = 4 * 1024**2
MAX_PROJECTION_BYTES = 512 * 1024


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def default_spec():
    return {'schema_version': 1, 'experiment': EXPERIMENT,
            'requests': [{'id': asset.lower() + '-dated-mark', 'symbol': asset + 'USDT_260626',
                          'endpoint': 'https://fapi.binance.com/fapi/v1/markPriceKlines',
                          'parameters': {'symbol': asset + 'USDT_260626', 'interval': '1d',
                                         'startTime': START, 'endTime': END, 'limit': 100}}
                         for asset in ('BTC', 'ETH')],
            'expected_open_ms': [START + i * DAY for i in range(COUNT)],
            'expected_row_fields': 12, 'ignored_fields': [5, 7, 8, 9, 10, 11],
            'max_requests': 2, 'timeout_seconds': 20, 'capture_seconds': 45,
            'max_response_bytes': 256 * 1024, 'max_output_bytes': MAX_OUTPUT_BYTES,
            'max_projection_bytes': MAX_PROJECTION_BYTES,
            'numeric_characters': 64, 'numeric_adjusted_exponent': [-32, 32]}


def unavailable_slots(reason):
    return [{'open_ms': START + i * DAY, 'status': 'unavailable', 'reason': reason}
            for i in range(COUNT)]


def unavailable(reason):
    return {'status': 'unavailable', 'reason': reason, 'slots': unavailable_slots(reason),
            'expected_slots': COUNT, 'complete_slots': 0, 'unavailable_slots': COUNT}


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def reject(_):
        raise ValueError('nonfinite JSON literal')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=reject,
                      parse_float=Decimal)


def price(value):
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError('price must be a bounded literal string')
    number = Decimal(value)
    if not number.is_finite() or number <= 0 or not -32 <= number.adjusted() <= 32:
        raise ValueError('price finite positive range required')
    return number


def schema(raw):
    rows = decode(raw)
    if not isinstance(rows, list):
        raise ValueError('mark bar array required')
    by_open = {}
    issues = Counter()
    previous = None
    malformed_rows = []
    for index, row in enumerate(rows):
        stamp = row[0] if isinstance(row, list) and row else None
        if type(stamp) is not int or not 0 < stamp <= 2**63 - 1:
            issues['invalid_open_timestamp'] += 1
            malformed_rows.append({'row_index': index, 'reason': 'invalid_open_timestamp'})
            continue
        if previous is not None and stamp <= previous:
            issues['nonascending_timestamp'] += 1
        previous = stamp
        if stamp < START or stamp > END or (stamp - START) % DAY:
            issues['unexpected_timestamp'] += 1
            malformed_rows.append({'row_index': index, 'reason': 'unexpected_timestamp'})
            continue
        by_open.setdefault(stamp, []).append((index, row))
    slots = []
    for stamp in (START + i * DAY for i in range(COUNT)):
        observed = by_open.get(stamp, [])
        if not observed:
            slots.append({'open_ms': stamp, 'status': 'unavailable', 'reason': 'missing'})
            continue
        if len(observed) != 1:
            issues['duplicate_timestamp'] += 1
            slots.append({'open_ms': stamp, 'status': 'unavailable', 'reason': 'duplicate_timestamp',
                          'row_indices': [index for index, _ in observed]})
            continue
        index, row = observed[0]
        try:
            if len(row) != 12:
                raise ValueError('twelve fields required')
            if type(row[6]) is not int or row[6] != stamp + DAY - 1:
                raise ValueError('exact daily close timestamp required')
            opened, high, low, closed = [price(value) for value in row[1:5]]
            if not low <= opened <= high or not low <= closed <= high:
                raise ValueError('inconsistent OHLC range')
            slots.append({'open_ms': stamp, 'close_ms': row[6], 'row_index': index,
                          'status': 'complete', 'open': row[1], 'high': row[2],
                          'low': row[3], 'close': row[4]})
        except (ValueError, ArithmeticError, TypeError) as exc:
            issues['invalid_expected_row'] += 1
            slots.append({'open_ms': stamp, 'row_index': index, 'status': 'unavailable',
                          'reason': type(exc).__name__ + ': ' + str(exc)[:100]})
    complete = sum(slot['status'] == 'complete' for slot in slots)
    result = {'status': 'complete' if complete == COUNT and not issues and len(rows) == COUNT else 'unavailable',
              'expected_slots': COUNT, 'observed_rows': len(rows), 'complete_slots': complete,
              'unavailable_slots': COUNT - complete, 'issues': dict(issues), 'slots': slots,
              'malformed_or_unexpected_rows': malformed_rows,
              'scope': 'Literal daily mark rows only; ignored fields are not trade activity, margin or execution.'}
    if result['status'] == 'unavailable':
        result['reason'] = 'fixed daily source incomplete or structurally ambiguous'
    if len(encoded(result)) > MAX_PROJECTION_BYTES:
        return unavailable('bounded normalized projection exceeded')
    return result


def admit(receipt):
    if receipt['attempted'] is not True or type(receipt['http_status']) is not int or receipt['http_status'] != 200 or receipt['body_complete'] is not True or receipt['error'] is not None:
        return unavailable(receipt['error'] or 'HTTP/body unavailable')
    try:
        raw = base64.b64decode(receipt['body_base64'], validate=True)
        if len(raw) != receipt['body_bytes'] or digest(raw) != receipt['body_sha256']:
            raise ValueError('retained raw hash/length mismatch')
        return schema(raw)
    except MemoryError:
        raise
    except Exception as exc:
        return unavailable(type(exc).__name__ + ': ' + str(exc)[:100])


def utc():
    return datetime.now(timezone.utc).isoformat()


def run(spec, persist, transport=None):
    if canonical(spec) != canonical(default_spec()):
        raise ValueError('fixed specification differs')
    deadline = time.monotonic() + 45
    receipts = []
    references = []
    written = 0
    denied = False
    for request in spec['requests']:
        url = request['endpoint'] + '?' + urlencode(request['parameters'])
        reason = 'same-host denial suppresses remaining slot' if denied else None
        if reason is None and time.monotonic() + 20 > deadline:
            reason = 'remaining capture budget cannot admit full request'
        before = time.monotonic()
        request_utc = utc()
        if reason is None:
            try:
                response = (transport or dated_mark_transport.public_get)(url)
            except MemoryError:
                raise
            except Exception as exc:
                response = {'body': b'', 'http_status': None, 'headers': {},
                            'body_complete': False, 'error': type(exc).__name__}
        else:
            response = {'body': b'', 'http_status': None, 'headers': {},
                        'body_complete': False, 'error': reason}
        raw = response['body']
        if not isinstance(raw, bytes):
            raise ValueError('transport bytes required')
        if len(raw) > spec['max_response_bytes']:
            raw = raw[:spec['max_response_bytes']]
            response = {**response, 'body_complete': False, 'error': '256KiB overflow; prefix retained'}
        if response['http_status'] in dated_mark_transport.DENIALS:
            denied = True
        receipt = {**request, 'request_url': url, 'request_utc': request_utc,
                   'retrieval_utc': utc(), 'elapsed_seconds': time.monotonic() - before,
                   'attempted': reason is None, 'http_status': response['http_status'],
                   'headers': {name: value for name, value in response['headers'].items()
                               if name.lower() in ('date', 'content-type')},
                   'body_complete': response['body_complete'], 'error': response['error'],
                   'body_bytes': len(raw), 'body_sha256': digest(raw),
                   'body_base64': base64.b64encode(raw).decode()}
        name = request['id'] + '-receipt.json'
        persist(name, receipt)
        written += len(encoded(receipt))
        receipts.append(receipt)
        references.append({'id': request['id'], 'path': name,
                           'receipt_sha256': digest(encoded(receipt)),
                           'body_sha256': digest(raw), 'body_bytes': len(raw),
                           'request_utc': request_utc, 'retrieval_utc': receipt['retrieval_utc']})
    closed = utc()
    admissions = [{'id': receipt['id'], **admit(receipt)} for receipt in receipts]
    capture = {'request_spec': spec, 'receipts': references, 'capture_closed_utc': closed,
               'scope': 'Both raw receipts persisted before schema interpretation; no financial calculation.'}
    admission = {'cells': admissions, 'planned_cells': 2, 'planned_subslots': 112,
                 'graduation': False, 'expected_profit': 'unavailable',
                 'risk_scope': 'Daily marks do not establish intraday liquidation, actual margin rules or fills.'}
    outputs = {'capture.json': capture, 'admission.json': admission}
    if written + sum(len(encoded(value)) for value in outputs.values()) > MAX_OUTPUT_BYTES:
        raise ValueError('actual combined4MiB output cap')
    for name, value in outputs.items():
        persist(name, value)
    cells = [{'id': value['id'], 'status': value['status'],
              **({'reason': value['reason']} if value['status'] == 'unavailable' else {})}
             for value in admissions]
    return capture, admission, cells


def main():
    from tradingagents.research_extended import ResearchRun
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2], registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as registered:
        spec = decode(registered.read_input('request_spec'))
        _, _, cells = run(spec, registered.write_json)
        registered.finish(cells)


if __name__ == '__main__':
    main()
