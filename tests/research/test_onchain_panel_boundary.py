"""Independent completion-time enumeration, including midnight and exact delta."""
import importlib.util
from itertools import combinations, product
from pathlib import Path
import random

import pytest

pytest.importorskip('raphtory')
DIRECTORY = Path(__file__).resolve().parents[2] / 'research/onchain-graph-2026-09-16'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


adapter = load('panel_boundary', DIRECTORY/'panel_readiness/boundary.py')
oracle = load('panel_boundary_oracle', DIRECTORY/'motifs/oracle.py')


def expected(events, start, end, delta):
    selected = [e for e in events if start-delta <= e[0] < end]
    counts = {v: [0]*40 for e in selected for v in e[2:]}
    for triple in combinations(selected, 3):
        if start <= triple[-1][0] < end and triple[-1][0]-triple[0][0] <= delta:
            for node, row in oracle.brute_local(triple, delta).items():
                counts[node] = [a+b for a,b in zip(counts[node], row, strict=True)]
    return counts


def calculate(events, start=10, end=20, delta=3):
    return adapter.completion_window(events, start=start, end=end, delta=delta,
                                     coverage_start=0, coverage_end=30)


@pytest.mark.parametrize('times', [(7,9,10),(6,9,10),(8,9,9),(17,19,20),(10,10,10)])
def test_every_topology_at_boundaries(times):
    edges = [(u,v) for u in 'abc' for v in 'abc' if u != v]
    for shape in product(edges, repeat=3):
        events = [(t,i,*edge) for i,(t,edge) in enumerate(zip(times,shape,strict=True))]
        assert calculate(events)['local_counts'] == expected(events,10,20,3)


def test_random_windows_and_future_invariance():
    rng = random.Random(16092026)
    for _ in range(60):
        events = sorted((rng.randrange(30),i,*rng.sample('abcde',2)) for i in range(18))
        for delta in (0,1,3,9):
            actual = calculate(events,delta=delta)
            assert actual['local_counts'] == expected(events,10,20,delta)
            assert actual == calculate([e for e in events if e[0]<20],delta=delta)
            assert actual['active_day_nodes'] == sorted({v for e in events if 10<=e[0]<20 for v in e[2:]})


def test_adjacent_windows_assign_every_occurrence_once():
    events = [(7,0,'a','b'),(9,1,'b','c'),(10,2,'c','a'),(11,3,'a','b'),
              (18,4,'b','a'),(19,5,'a','c'),(20,6,'c','b'),(22,7,'a','b')]
    whole = calculate(events,start=3,end=27)['local_counts']
    parts = [calculate(events,start=a,end=b)['local_counts'] for a,b in [(3,10),(10,20),(20,27)]]
    for node,row in whole.items():
        assert row == [sum(p.get(node,[0]*40)[i] for p in parts) for i in range(40)]


def test_missing_overlap_and_invalid_event_identity_rejected():
    with pytest.raises(ValueError,match='overlap'):
        adapter.completion_window([],start=10,end=20,delta=3,coverage_start=8,coverage_end=20)
    for events in [[(10,1,'a','b'),(11,1,'b','a')],[(11,0,'a','b'),(10,1,'a','b')],[(10,0,'a','a')]]:
        with pytest.raises(ValueError):calculate(events)
    assert calculate([])['local_counts']=={}
