"""Synthetic transport/stop contracts; no actual archive requests."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('graph_capture_test', HERE/'research/onchain-graph-2026-09-16/comparison/graph_capture.py')
graph = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(graph)


def plan():
    return json.loads((HERE/'research/onchain-graph-2026-09-16/pilot/plan.json').read_text())


def test_missing_inventory_has_all_cells_no_network(tmp_path):
    with patch.object(graph.storage.BinaryCapture, 'get', side_effect=AssertionError('network')):
        result = graph.capture_graph(tmp_path/'capture', {'inventories':[]}, plan())
    assert len(result['days']) == 7
    assert all(r['status']=='unavailable' for r in result['days'])
    assert result['requests'] == 0


def test_low_disk_latches_even_if_space_recovers(tmp_path):
    calls = []
    def free(path):
        calls.append(path)
        return SimpleNamespace(free=0 if len(calls)==1 else 10**15)
    obj = dict(size=100, key='synthetic', etag='fake')
    with patch.object(graph.day, 'object_for', return_value=obj), patch.object(
            graph.storage.BinaryCapture, 'get', side_effect=AssertionError('network')):
        result = graph.capture_graph(tmp_path/'capture', {}, plan(), disk_usage=free)
    assert len(calls) == 1
    assert all('disk reserve' in r['reason'] for r in result['days'])


def test_denial_stops_remaining_days(tmp_path):
    def denied(self, url, headers):
        self.denied = True
        self.count += 1
        return None, dict(status=403, error='denied', response_headers={})
    obj = dict(size=100, key='synthetic', etag='fake')
    with patch.object(graph.day, 'object_for', return_value=obj), patch.object(
            graph.storage.BinaryCapture, 'get', denied):
        result = graph.capture_graph(tmp_path/'capture', {}, plan(),
                                     disk_usage=lambda _:SimpleNamespace(free=10**15))
    assert result['requests'] == 1
    assert all(r['status']=='unavailable' for r in result['days'])
    assert all('source denied' in r['reason'] for r in result['days'][1:])


def test_complete_projection_requests_exact_ranges(tmp_path):
    import io
    import pyarrow as pa
    import pyarrow.parquet as pq
    settings = plan()
    def parquet(types):
        columns = {}
        for name, kind in types.items():
            dtype = {'string':pa.string(), 'int64':pa.int64(),
                     'double':pa.float64(), 'timestamp[ns]':pa.timestamp('ns')}[kind]
            columns[name] = pa.array(['synthetic'] if kind=='string' else [1], type=dtype)
        output = io.BytesIO()
        pq.write_table(pa.table(columns), output)
        return output.getvalue()
    bodies = {'blocks':parquet(settings['block_required_types']),
              'transactions':parquet(settings['required_types'])}
    objects = {name:dict(size=len(raw), key=name, etag='fixed') for name,raw in bodies.items()}
    requests = []
    def get(self, url, headers):
        key = url.rsplit('/',1)[-1]
        raw = bodies[key]
        response = {'etag':'fixed'}
        status = 200
        if 'Range' in headers:
            start,end = map(int,headers['Range'][6:].split('-'))
            response['content-range'] = f'bytes {start}-{end}/{len(raw)}'
            raw = raw[start:end+1]
            status = 206
        requests.append((key,headers.copy()))
        self.count += 1
        self.total += len(raw)
        return raw,dict(status=status,response_headers=response)
    with patch.object(graph.day, 'object_for', side_effect=lambda _,table,date:objects[table]), patch.object(
            graph.storage.BinaryCapture, 'get', get):
        result = graph.capture_graph(tmp_path/'capture', {}, settings,
                                     disk_usage=lambda _:SimpleNamespace(free=10**15))
    assert len(requests) == 7*12
    assert all(r['status']=='complete' and r['projected_rows']==1 for r in result['days'])
    projection = json.loads((tmp_path/'capture/2022-01-01/projection.json').read_text())
    assert [h['Range'] for _,h in requests[3:12]] == [
        f'bytes={r["start"]}-{r["end"]}' for r in projection['ranges']]
