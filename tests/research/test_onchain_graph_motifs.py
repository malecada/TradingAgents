"""Independent exhaustive fixtures for the pinned Raphtory motif adapter."""
import importlib.util
from itertools import product
from pathlib import Path
import random

import pytest

raphtory = pytest.importorskip('raphtory')
from raphtory import Graph, algorithms

DIRECTORY = Path(__file__).resolve().parents[2] / 'research/onchain-graph-2026-09-16/motifs'
spec = importlib.util.spec_from_file_location('motif_oracle', DIRECTORY / 'oracle.py')
oracle = importlib.util.module_from_spec(spec); spec.loader.exec_module(oracle)


def library(events, delta, reverse=False):
    graph = Graph()
    for t, order, u, v in reversed(events) if reverse else events:
        graph.add_edge(t, u, v, event_id=order)
    assert graph.count_temporal_edges() == len(events)
    result = algorithms.local_temporal_three_node_motifs(graph, delta, threads=2)
    return {node.name: item['motif_counter'] for node, item in result.items()}


def test_all_three_event_topologies_and_directions():
    edges = [(u,v) for u in 'abc' for v in 'abc' if u != v]
    for triple in product(edges, repeat=3):
        events = [(10, n, *edge) for n, edge in enumerate(triple)]
        assert library(events, 0) == oracle.brute_local(events, 0), triple


@pytest.mark.parametrize('last,delta', [(3599,3600), (3600,3600), (3601,3600), (0,0)])
def test_inclusive_seconds_and_ties(last, delta):
    events = [(0,0,'a','b'), (0,1,'b','c'), (last,2,'c','a')]
    assert library(events, delta) == oracle.brute_local(events, delta)


def test_repeated_same_second_edges_preserved_and_event_id_orders():
    events = [(100,n,u,v) for n,(u,v) in enumerate([('a','b'),('b','a'),('a','b'),('a','b'),('b','a')])]
    assert library(events, 0, reverse=True) == oracle.brute_local(events, 0)


def test_many_small_graphs_against_combinations():
    rng = random.Random(16092026)
    for _ in range(80):
        events = []
        for i in range(14):
            u, v = rng.sample('abcd', 2)
            events.append((rng.randrange(8), i, u, v))
        for delta in (0, 1, 3, 8):
            assert library(events, delta, reverse=True) == oracle.brute_local(events, delta)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


benchmark = load('motif_benchmark_tested',DIRECTORY/'benchmark.py')


def test_export_role_conservation_and_fingerprint():
    import hashlib,json
    events = [(0,0,'a','b'),(0,1,'b','a'),(1,2,'a','b'),(2,3,'b','c'),(3,4,'c','a')]
    graph = benchmark.graph_for(events)
    local = algorithms.local_temporal_three_node_motifs(graph,3600,threads=2)
    output = {}
    summary = benchmark.export_local(graph,local,lambda n,v:output.setdefault(n,v))
    expected = oracle.brute_local(events,3600)
    decoded = dict(json.loads(line) for line in output['local-000.json']['rows_jsonl'].splitlines())
    assert decoded == expected
    totals = [sum(row[i] for row in expected.values()) for i in range(40)]
    assert summary['local40_sums'] == totals
    assert summary['unique_three_event_occurrences'] == sum(totals[:24])+sum(totals[24:32])//2+sum(totals[32:])//3
    assert summary['local_rows_sha256'] == hashlib.sha256(output['local-000.json']['rows_jsonl'].encode()).hexdigest()
    assert summary['node_count'] == 3


def test_end_to_end_saved_projection_is_offline(monkeypatch):
    import base64,hashlib,json
    from unittest.mock import patch
    root = DIRECTORY.parents[2]
    fixtures = load('motif_projection_fixtures',root/'tests/research/test_onchain_graph_prototype.py')
    forensic = load('motif_forensic_fixture',DIRECTORY.parent/'forensic/reconstruct.py')
    rows = [list(r) for r in fixtures.rows()]; rows[4][6] = 'None'
    monkeypatch.setattr(fixtures,'rows',lambda:rows)
    plan,raw,footer,blocks = fixtures.parquet_fixture()
    def receipt(body):
        return {'body_base64':base64.b64encode(body).decode(),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
    inputs = {'plan':json.dumps(plan).encode(),'footer':json.dumps(receipt(footer)).encode(),
              'blocks':json.dumps(receipt(blocks)).encode()}
    for number,span in enumerate(plan['ranges'],1):
        body=raw[span['start']:span['end']+1]
        inputs[f'range-{number:03d}']=json.dumps(dict(receipt(body),status=206,url=plan['base_url']+plan['object']['key'],
            request_number=number,request_headers={'Range':f'bytes={span["start"]}-{span["end"]}','If-Match':'"fixture"'},
            response_headers={'content-range':f'bytes {span["start"]}-{span["end"]}/{len(raw)}','etag':'"fixture"'})).encode()
    expected=forensic.reconstruct(plan,footer,blocks,lambda n:inputs[f'range-{n:03d}'])
    inputs['forensic_result']=json.dumps(expected).encode()
    output={}
    with patch.object(benchmark.original.transport.urllib.request.OpenerDirector,'open',side_effect=AssertionError('network prohibited')) as network:
        cells=benchmark.execute(inputs.__getitem__,lambda n,v:output.setdefault(n,v))
    network.assert_not_called()
    assert len(cells)==5 and all(c['status']=='complete' for c in cells)
    assert output['graph-build.json']['events']==3
    assert output['integrity.json']['exact_sentinels_excluded']==1
    assert output['motif-summary.json']['engineering_only']
    assert not output['motif-summary.json']['financial_evaluation_admitted']
    # Corrupting an input must reject before building the actual graph.
    bad=json.loads(inputs['range-001']);bad['sha256']='0'*64
    inputs['range-001']=json.dumps(bad).encode()
    with pytest.raises(ValueError):benchmark.recover_events(inputs.__getitem__)
