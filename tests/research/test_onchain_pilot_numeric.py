"""Invented data only: projected decoding and cross-midnight attribution."""
import importlib.util
from pathlib import Path
import io
from itertools import combinations
import pyarrow.parquet as pq
import pytest

ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=load('pilot_numeric_test','research/onchain-graph-2026-09-16/pilot/numeric.py')
f=load('prototype_fixture','tests/research/test_onchain_graph_prototype.py')


def test_projected_decode_stable_id_and_hole_exclusion():
    old,raw,footer,blocks=f.parquet_fixture()
    types={field.name:str(field.type) for field in pq.read_metadata(io.BytesIO(raw)).schema.to_arrow_schema() if field.name in n.COLUMNS}
    limits=dict(max_logical_bytes=1000000,max_footer_bytes=100000,max_projection_bytes=100000,max_response_bytes=10000)
    plan=n.projection(old['object'],footer,limits,types)
    events,integrity,activity=n.decode(plan,footer,blocks,lambda i:raw[plan['ranges'][i]['start']:plan['ranges'][i]['end']+1],f.START//10**9,f.END//10**9)
    assert activity['events']==3 and integrity['admitted']
    assert [e[1] for e in events]==[(100<<32)|i for i in range(3)]
    with pytest.raises(ValueError,match='schema'):n.projection(old['object'],footer,limits,{**types,'value':'int64'})
    with pytest.raises(ValueError,match='allowance'):n.projection(old['object'],footer,{**limits,'max_projection_bytes':1},types)


def test_completion_summary_matches_exhaustive_triples_and_overlap_nodes():
    prefix=[(99,1,'a','b'),(99,2,'b','a')]
    events=[(100,3,'a','b'),(100,4,'a','c'),(101,5,'c','b')]
    counts,summary,checks,timing=n.count_day(prefix,events,100,200)
    expected={v:[0]*40 for e in prefix+events for v in e[2:]}
    for triple in combinations(prefix+events,3):
        if triple[-1][0]<100:continue
        for node,row in n.oracle.brute_local(triple,3600).items():
            expected[node]=[a+b for a,b in zip(expected[node],row)]
    assert counts==expected and summary['cross_midnight_unique_occurrences']>0
    assert len(checks['samples'])==2 and summary['unique_occurrences']>=summary['cross_midnight_unique_occurrences']
    assert all(v>=0 for v in timing.values())


def test_chain_link_rejects_height_hash_and_clock_gaps():
    before=[100,'abc','def',1000,0];after=[101,'ghi','abc',2000,0]
    n.linked(before,after)
    for index,bad in [(0,102),(2,'wrong'),(3,1000)]:
        changed=after.copy();changed[index]=bad
        with pytest.raises(ValueError,match='discontinuity'):n.linked(before,changed)
