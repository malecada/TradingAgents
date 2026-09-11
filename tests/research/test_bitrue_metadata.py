"""Invented Bitrue metadata; never calls a market endpoint."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

DIRECTORY = Path(__file__).resolve().parents[2] / 'research/strategy-search-2026-09-11'
for name in ('options_metadata', 'bitrue_metadata'):
    spec = importlib.util.spec_from_file_location(name, DIRECTORY / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
collector = sys.modules['bitrue_metadata']


def frozen():
    return json.loads((DIRECTORY / 'bitrue-request-spec.json').read_text())


def contract(asset='BTC'):
    return dict(symbol=f'E-{asset}-USDT', multiplierCoin=asset, type='E', side=1,
                status=1, multiplier=0.01, minOrderVolume=1, minOrderMoney=0.01)


def parse(data):
    return collector.parse_response(json.dumps(data).encode(), frozen()['requests'][0])


def response(raw=b'{}', status=200, complete=True):
    return dict(body=raw, http_status=status, body_complete=complete, error=None, headers={})


def test_literal_rows_and_conditional_identity_only():
    rows = [contract(), contract('ETH'), dict(contract(), symbol='BTCUSDT')]
    result = parse(rows)
    assert result['contract_rows'] == rows
    assert [r['conditional_target_asset'] for r in result['row_metadata']] == ['BTC', 'ETH', None]
    assert all(r['account_eligibility'] == 'unavailable' for r in result['row_metadata'])


@pytest.mark.parametrize('field,value', [('side', True), ('side', 0), ('status', 0), ('type', 'H'),
                                         ('multiplierCoin', 'USDT'), ('multiplier', 'NaN'),
                                         ('minOrderVolume', 0)])
def test_ambiguous_rows_retained_without_mapping(field, value):
    row = dict(contract(), **{field: value})
    result = parse([row])
    assert result['contract_rows'] == [row]
    assert result['row_metadata'][0]['conditional_target_asset'] is None


def test_duplicate_names_and_empty_array_are_literal_not_eligibility():
    with pytest.raises(ValueError, match='unique nonempty'):
        parse([contract(), contract()])
    with pytest.raises(ValueError, match='unique nonempty'):
        parse([dict(contract(), symbol=None)])
    assert parse([dict(contract(), minOrderMoney=0)])['row_metadata'][0]['conditional_target_asset'] == 'BTC'
    assert parse([])['observed_rows'] == 0


@pytest.mark.parametrize('raw', [b'{"data":[]}', b'[1]', b'[],"extra":1', b'[{"symbol":"x","symbol":"y"}]', b'[NaN]'])
def test_unregistered_roots_and_non_strict_json_rejected(raw):
    with pytest.raises((ValueError, TypeError)):
        collector.parse_response(raw, frozen()['requests'][0])


def test_time_object_has_no_invented_clock_units():
    for data in ({}, {'serverTime': 123}):
        result = collector.parse_response(json.dumps(data).encode(), frozen()['requests'][1])
        assert result['raw_fields'] == data
        assert result['clock_semantics']['status'] == 'unavailable'


def test_immediate_receipts_hashes_and_complete_denominator():
    receipts = []
    calls = []
    def fake(url):
        assert len(receipts) == len(calls)
        calls.append(url)
        return response(json.dumps([contract()]).encode() if len(calls) == 1 else b'{}')
    raw, admission, cells = collector.capture(frozen(), fake, lambda name, row: receipts.append((name, row)))
    assert len(receipts) == len(cells) == 2
    assert all(row['status'] == 'complete' for row in cells)
    for _, row in receipts:
        body = base64.b64decode(row['body_base64'])
        assert hashlib.sha256(body).hexdigest() == row['body_sha256']
    assert raw['requests'][0]['attempted'] is True
    assert admission['cells'][1]['clock_semantics']['status'] == 'unavailable'


@pytest.mark.parametrize('status', [403, 418, 429, 451])
def test_denial_suppresses_same_host_but_preserves_two_cells(status):
    calls = []
    def fake(url):
        calls.append(url)
        return response(status=status)
    raw, _, cells = collector.capture(frozen(), fake)
    assert len(calls) == 1 and len(cells) == 2
    assert all(row['status'] == 'unavailable' for row in cells)
    assert raw['requests'][1]['attempted'] is False


def test_incomplete_and_recoverable_parser_errors_preserve_all_receipts(monkeypatch):
    receipts = []
    monkeypatch.setattr(collector, 'parse_response', lambda *_: (_ for _ in ()).throw(RuntimeError('invented parser error')))
    _, _, cells = collector.capture(frozen(), lambda _: response(), lambda *args: receipts.append(args))
    assert len(cells) == len(receipts) == 2
    assert all(row['status'] == 'unavailable' for row in cells)


def test_cooperative_deadline_and_frozen_spec(monkeypatch):
    times = iter([0, 50, 50, 50, 50])
    monkeypatch.setattr(collector.time, 'monotonic', lambda: next(times))
    raw, _, cells = collector.capture(frozen(), lambda _: pytest.fail('insufficient time'))
    assert len(cells) == 2 and all(not row['attempted'] for row in raw['requests'])
    spec = frozen()
    spec['requests'][0]['url'] += '?extra=1'
    with pytest.raises(ValueError, match='frozen definition'):
        collector.capture(spec, lambda _: pytest.fail('mutated spec'))


def test_partial_raw_prefix_retained_and_numeric_strings_are_not_admitted():
    result = parse([dict(contract(), multiplier='0.01')])
    assert result['row_metadata'][0]['metadata_status'] == 'unavailable'
    raw, _, cells = collector.capture(frozen(), lambda _: response(b'{"partial":', complete=False))
    assert len(cells) == 2 and all(row['status'] == 'unavailable' for row in cells)
    assert all(base64.b64decode(row['body_base64']) == b'{"partial":' for row in raw['requests'])


def test_actual_normalization_cap_keeps_receipts_and_denominator(monkeypatch):
    monkeypatch.setattr(collector, 'parse_response', lambda *_: {'status': 'complete', 'large': 'x' * (10 * 1024**2)})
    receipts = []
    _, admission, cells = collector.capture(frozen(), lambda _: response(), lambda *args: receipts.append(args))
    assert len(receipts) == len(cells) == 2
    assert all(row['status'] == 'unavailable' for row in cells)
    assert len(collector.lifecycle_bytes(admission)) <= frozen()['max_admission_bytes']
