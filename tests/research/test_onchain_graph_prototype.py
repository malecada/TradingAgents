"""Invented transactions only; no network or archived financial observations."""
import importlib.util
import io
from pathlib import Path
import struct
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('onchain_graph_prototype', ROOT / 'research/onchain-graph-2026-09-16/prototype/run.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
math = runner.math
A, B, C = ['0x' + c * 40 for c in 'abc']
H, P = '0x' + '7' * 64, '0x' + '8' * 64
START, END = 1704067200000000000, 1704153600000000000


def rows():
    edges = [(A, B, 1., 1), (A, B, 2., 1), (B, A, 1., 1),
             (A, C, 1., 0), (A, None, 1., 1), (A, C, 0., 1), (A, A, 1., 1)]
    return [(f'0x{i:064x}', H, 100, START, i, a, b, v, s) for i, (a, b, v, s) in enumerate(edges)]


def state():
    return math.Integrity([(100, H, P, START, 7)], START, END)


def test_exclusions_and_hand_counted_directed_graph():
    s = state()
    for row in rows(): s.add(row)
    result = s.finish()
    assert result['admitted'] and result['missing_block_positions'] == 0
    assert result['categories'] == {'invalid': 0, 'reverted': 1, 'null_recipient': 1, 'zero_value': 1, 'self_transfer': 1, 'graph_event': 3}
    graph = math.graph_features(s.pairs)
    assert (graph['nodes'], graph['directed_pairs'], graph['events'], graph['reciprocal_dyads']) == (2, 2, 3, 1)
    assert graph['repeated_event_fraction'] == 1 / 3
    assert graph['sender_event_hhi'] == graph['recipient_event_hhi'] == 5 / 9
    assert graph['in_degree_histogram'] == {1: 2}


def test_normalization_and_file_order_do_not_change_static_graph():
    s = state()
    for row in reversed(rows()):
        row = list(row); row[5] = '0x' + row[5][2:].upper()
        s.add(row)
    assert s.finish()['admitted'] and s.finish()['source_order_inversions'] == 6
    expected = state()
    for row in rows(): expected.add(row)
    assert math.graph_features(s.pairs) == math.graph_features(expected.pairs)


@pytest.mark.parametrize('index,value,error', [(1, P, 'block_hash_mismatch'), (2, 101, 'unknown_block'),
    (3, END, 'timestamp_outside_day_or_missing'), (4, 7, 'invalid_transaction_index'),
    (4, 1.0, 'invalid_transaction_index'), (5, 'bad', 'invalid_sender'),
    (6, 'bad', 'invalid_recipient'), (7, float('nan'), 'invalid_amount'),
    (7, float('inf'), 'invalid_amount'), (7, -1., 'invalid_amount'), (8, 2, 'invalid_receipt_status')])
def test_invalid_rows_block_admission(index, value, error):
    s = state(); data = rows(); changed = list(data[0]); changed[index] = value; data[0] = changed
    for row in data: s.add(row)
    result = s.finish()
    assert not result['admitted'] and result['errors'][error] == 1
    assert sum(result['categories'].values()) == 7


def test_duplicate_and_missing_positions_are_not_silently_dropped():
    s = state(); data = rows(); data[1] = data[0]
    for row in data: s.add(row)
    r = s.finish()
    assert not r['admitted'] and r['errors']['duplicate_transaction_hash'] == 1
    assert r['errors']['duplicate_block_position'] == 1 and r['missing_block_positions'] == 1


def test_empty_graph_ratios_remain_undefined():
    r = math.graph_features({})
    assert r['nodes'] == r['events'] == 0 and r['sender_event_hhi'] is None


def parquet_fixture():
    names = ['hash', 'block_hash', 'block_number', 'block_timestamp', 'transaction_index', 'from_address', 'to_address', 'value', 'receipt_status']
    data = dict(zip(names, zip(*rows(), strict=True), strict=True))
    data['block_timestamp'] = pa.array(data['block_timestamp'], type=pa.timestamp('ns'))
    data['input'] = ['unneeded payload' * 1000] * 7
    sink = io.BytesIO(); pq.write_table(pa.table(data), sink, row_group_size=3)
    raw = sink.getvalue(); length = struct.unpack('<I', raw[-8:-4])[0]; footer = raw[-length-8:]
    meta = pq.read_metadata(io.BytesIO(raw)); ranges = []
    for group in range(meta.num_row_groups):
        g = meta.row_group(group)
        for j in range(g.num_columns):
            c = g.column(j)
            if c.path_in_schema not in names: continue
            start = c.dictionary_page_offset if c.has_dictionary_page else c.data_page_offset
            ranges.append({'id': f'group-{group:02d}-{c.path_in_schema}', 'group': group,
                           'column': c.path_in_schema, 'start': start, 'end': start + c.total_compressed_size - 1,
                           'bytes': c.total_compressed_size})
    plan = {'base_url': 'https://example.invalid/', 'object': {'size': len(raw), 'key': 'sample.parquet', 'etag': '"fixture"'},
            'columns': sorted(names), 'rows': 7, 'groups': [3, 3, 1], 'ranges': ranges,
            'footer_start': len(raw) - len(footer), 'start_ns': START, 'end_ns': END,
            'max_requests': len(ranges), 'max_total_bytes': 1000000, 'max_response_bytes': 100000, 'timeout_seconds': 20}
    b = io.BytesIO(); pq.write_table(pa.table({'number': [100], 'hash': [H], 'parent_hash': [P],
        'timestamp': pa.array([START], type=pa.timestamp('ns')), 'transaction_count': [7]}), b)
    return plan, raw, footer, b.getvalue()


class Response(io.BytesIO):
    def __init__(self, body, status, headers):
        super().__init__(body); self.status, self.headers = status, headers


def test_sparse_projection_decodes_only_acquired_columns_end_to_end():
    plan, raw, footer, blocks = parquet_fixture(); outputs = {}
    def network(req, **kwargs):
        start, end = map(int, req.get_header('Range').removeprefix('bytes=').split('-'))
        assert req.get_header('If-match') == '"fixture"'
        body = raw[start:end+1]
        return Response(body, 206, {'ETag': '"fixture"', 'Content-Length': str(len(body)),
                                  'Content-Range': f'bytes {start}-{end}/{len(raw)}'})
    with patch.object(runner.transport.urllib.request.OpenerDirector, 'open', side_effect=network) as requests:
        cells = runner.execute(plan, footer, blocks, outputs.__setitem__)
    assert requests.call_count == 27 and len(cells) == 29
    assert all(c['status'] == 'complete' for c in cells), outputs['integrity.json']
    assert outputs['graph.json']['events'] == 3
    assert len(outputs) == 60


def test_denial_retains_every_cell_and_output_without_retry():
    plan, raw, footer, blocks = parquet_fixture(); outputs = {}
    with patch.object(runner.transport.urllib.request.OpenerDirector, 'open',
                      return_value=Response(b'denied', 403, {'Content-Length': '6'})) as requests:
        cells = runner.execute(plan, footer, blocks, outputs.__setitem__)
    assert requests.call_count == 1 and len(cells) == 29 and len(outputs) == 60
    assert all(c['status'] == 'unavailable' for c in cells)
    assert outputs['request-01.json']['bytes'] == 6


def test_plan_mutation_and_unacquired_hole_read_rejected():
    plan, raw, footer, blocks = parquet_fixture()
    plan['ranges'][0]['start'] += 1
    with pytest.raises(ValueError, match='differs'):
        runner.validate_plan(plan, footer)
    guarded = runner.AcquiredReader(io.BytesIO(b'0123456789'), [(0, 2), (7, 9)])
    with pytest.raises(ValueError, match='unacquired'):
        guarded.read(4)
