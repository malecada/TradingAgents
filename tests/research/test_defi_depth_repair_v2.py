"""Regression for actual provider's max10 batch rule using invented states."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'research/defi-depth-2026-09-15'
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fixture=load('depth_repair_fixture',ROOT/'tests/research/test_defi_depth_history.py')
r1=load('depth_repair_runner',HERE/'r1_source_v2.py')

def bounded_fake(spec,mode=None):
    inner,calls=fixture.fake(spec,mode)
    attempted=[]
    def fetch(url,payload):
        attempted.append(payload)
        if len(payload)>10:
            return dict(body=b'{"jsonrpc":"2.0","error":{"code":-32014,"message":"maximum 10 calls in 1 batch"},"id":null}',http_status=200,headers={},error=None,body_complete=True)
        return inner(url,payload)
    return fetch,attempted

def test_old_batch_defect_and_repair_same_cells(capsys):
    s=fixture.fixture();bad,_=bounded_fake(s)
    prior=fixture.q2.capture(s,lambda *_:None,bad)
    fake,calls=bounded_fake(s);output={}
    fixed=r1.capture(s,lambda k,v:output.__setitem__(k,v),fake)
    assert [r['id'] for r in prior['cells']]==[r['id'] for r in fixed['cells']]
    assert sum(r['status']=='unavailable' for r in prior['cells'])>1
    assert sum(r['status']=='unavailable' for r in fixed['cells'])==1
    assert fixed['rpc_subcalls']==49
    assert fixed['http_requests']==8
    assert max(map(len,calls))==10
    assert set(output)==set(r1.outputs_for(s))-{'summary.json'}
    assert len(output)==19

def test_full_repaired_inventory_no_network(capsys):
    s=json.loads((HERE/'q2-spec.json').read_text());fake,calls=bounded_fake(s);output={}
    result=r1.capture(s,lambda k,v:output.__setitem__(k,v),fake)
    assert len(result['cells'])==20890
    assert len(output)==7683
    assert sum(r['status']=='unavailable' for r in result['cells'])==3
    assert result['http_requests']==3293 and result['rpc_subcalls']==18689
    assert result['repair_transport_bounds']=={'max_http_requests':3293,'max_raw_bytes':863240192,'max_batch_members':10}
    assert max(map(len,calls))==10
    assert result['elapsed_time_kill'] is False
    assert result['financial_outcomes_computed'] is False
    assert result['raw_bytes']==sum(v['body_bytes'] for k,v in output.items() if k.endswith('-receipt.json'))

@pytest.mark.parametrize('mode',['denied','wrong-chain','wrong-parent','absent-implementation','absent-code'])
def test_repair_keeps_unavailable_denominators(mode,capsys):
    s=fixture.fixture();fake,calls=bounded_fake(s,mode);output={}
    result=r1.capture(s,lambda k,v:output.__setitem__(k,v),fake)
    assert [r['id'] for r in result['cells']]==r1.cells_for(s)
    assert set(output)==set(r1.outputs_for(s))-{'summary.json'}
    if mode=='denied': assert len(calls)==1

def test_one_bad_chunk_does_not_invalidate_or_repeat_other_chunk(capsys):
    s=fixture.fixture();inner,_=bounded_fake(s);calls=[]
    def fake(url,payload):
        calls.append(payload)
        if payload[0]['id']=='invented-b-aave-income':
            return dict(body=b'partial',http_status=200,headers={},error='partial body',body_complete=False)
        return inner(url,payload)
    result=r1.capture(s,lambda *_:None,fake)
    rows={r['id']:r for r in result['cells']}
    assert rows['invented-b-aave-income']['status']=='unavailable'
    assert rows['invented-b-atoken-implementation']['status']=='complete'
    assert len(calls)==8
