"""Invented source-history tests; no real RPC or financial calculations."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest
from eth_utils import keccak

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'research/defi-depth-2026-09-15'
loader=importlib.util.spec_from_file_location('q2_tests',HERE/'q2_source.py')
q2=importlib.util.module_from_spec(loader); loader.loader.exec_module(q2)

def word(v):
    if isinstance(v,str): v=int(v,16)
    return format(int(v)%2**256,'064x')

def fixture():
    s=json.loads((HERE/'q2-spec.json').read_text())
    s['days']=[{'date':'invented-a','timestamp':1000,'candidate_block':100}, {'date':'invented-b','timestamp':1002,'candidate_block':101}]
    s['boundaries']=['invented-a']
    s['cohorts']={'invented':{'start':'invented-a','end':'invented-b'}}
    return s

def fake(s,mode=None):
    calls=[]
    def fetch(url,payload):
        calls.append(payload)
        if mode=='denied':
            return dict(body=b'denied',http_status=429,headers={},error='HTTP429',body_complete=True)
        responses=[]
        for p in payload:
            method=p['method']
            if method=='eth_chainId': result=hex(1 if mode=='wrong-chain' else 8453)
            elif method=='eth_getBlockByNumber':
                n=int(p['params'][0],16)
                seed=s['days'][0]
                stamp=seed['timestamp']+2*(n-seed['candidate_block'])
                result={'number':hex(n),'timestamp':hex(stamp),'hash':'0x'+word(n),'parentHash':'0x'+word(n-1),'baseFeePerGas':'0x1'}
                if mode=='wrong-parent': result['parentHash']='0x'+word(999)
                if mode=='forward': result['timestamp']=hex(1001+2*(n-100))
            elif method=='eth_getCode': result='0x' if mode=='absent-code' else '0x6001'
            elif method=='eth_getStorageAt': result='0x'+word(0 if mode=='absent-implementation' else 100)
            else:
                actions=s['daily_actions']+s['boundary_actions']
                a=next(a for a in actions if a.get('data')==p['params'][0]['data'] and a['to']==p['params'][0]['to'])
                k=a['key']
                if 'expected' in a: values=a['expected']
                elif k=='aave-income': values=[10**27]
                elif k in ('aave-scaled-supply','aave-total-supply'): values=[1000]
                elif k=='lp-slot0': values=[2**96,0,0,1,1,0,True]
                elif k in ('lp-lower','lp-upper'): values=[0]*8
                else: values=[100]
                result='0x'+''.join(word(v) for v in values)
            responses.append({'jsonrpc':'2.0','id':p['id'],'result':result})
        if mode=='missing-state' and payload[0]['method']=='eth_call': responses.pop(0)
        body=json.dumps(list(reversed(responses))).encode()
        return dict(body=body,http_status=200,headers={},error=None,body_complete=True)
    return fetch,calls

def run_fixture(mode=None):
    s=fixture(); f,calls=fake(s,mode); outputs={}
    def publish(name,value):
        assert name not in outputs
        if name.endswith('-receipt.json'): assert name.replace('-receipt.json','-attempt.json') in outputs
        outputs[name]=value
    r=q2.capture(s,publish,f)
    assert [x['id'] for x in r['cells']]==q2.cells_for(s)
    assert set(outputs)==set(q2.outputs_for(s))-{'summary.json'}
    return s,r,outputs,calls

def test_complete_shuffled_batches_and_source_only(capsys):
    s,r,o,calls=run_fixture()
    assert r['http_requests']==5
    assert r['rpc_subcalls']==49
    assert sum(x['status']=='unavailable' for x in r['cells'])==1
    assert r['financial_outcomes_computed'] is False
    assert r['elapsed_time_kill'] is False
    assert r['raw_bytes']==sum(v['body_bytes'] for k,v in o.items() if k.endswith('-receipt.json'))
    for p in calls:
        for member in p:
            if member['method'] not in ('eth_getBlockByNumber','eth_chainId'):
                assert member['params'][-1]['requireCanonical'] is True

def test_denied_endpoint_retains_full_denominator(capsys):
    s,r,o,calls=run_fixture('denied')
    assert len(calls)==1 and r['rpc_subcalls']==1
    assert all(x['status']=='unavailable' for x in r['cells'])

@pytest.mark.parametrize('mode',['wrong-chain','wrong-parent','forward'])
def test_dependent_state_not_requested_when_anchor_unavailable(mode,capsys):
    s,r,o,calls=run_fixture(mode)
    assert not any(p[0]['method']=='eth_call' for p in calls)
    assert any('canonical-bracket' in x['id'] and x['status']=='unavailable' for x in r['cells'])

@pytest.mark.parametrize('mode,key',[('absent-code','oracle-code'),('absent-implementation','aave-implementation'),('missing-state','aave-income')])
def test_unknown_deployment_and_missing_member_not_zero(mode,key,capsys):
    s,r,o,calls=run_fixture(mode)
    assert any(x['id'].endswith(key) and x['status']=='unavailable' for x in r['cells'])

def test_batch_extra_duplicate_and_bad_envelope():
    p=[dict(id='a')]; good=dict(jsonrpc='2.0',id='a',result='0x1')
    bad=[good,{**good,'id':'b'}]
    for data in ([good,good],bad,[{**good,'jsonrpc':'1.0'}],good):
        with pytest.raises(ValueError): q2.batch_envelopes(json.dumps(data).encode(),p)
    assert q2.batch_envelopes(b'[]',p)=={}

def test_frozen_inventory_and_selectors():
    s=json.loads((HERE/'q2-spec.json').read_text())
    assert len(s['days'])==1096
    assert len(q2.cells_for(s))==20890
    assert len(q2.outputs_for(s))==5484
    assert s['max_rpc_subcalls']==18689
    assert s['max_raw_bytes']==574881792
    for a in s['daily_actions']+s['boundary_actions']:
        if 'signature' in a:
            assert a['data'][:10]=='0x'+keccak(text=a['signature'])[:4].hex()
    for c in s['cohorts'].values():
        from datetime import date
        assert (date.fromisoformat(c['end'])-date.fromisoformat(c['start'])).days==365

def test_nonpublic_and_mutating_transport_rejected_before_network():
    with pytest.raises(ValueError): q2.transport.public_post('https://example.com',[])
    with pytest.raises(ValueError): q2.transport.public_post('https://mainnet.base.org',[dict(jsonrpc='2.0',id='a',method='eth_sendRawTransaction')])
    with pytest.raises(ValueError): q2.transport.public_post('https://mainnet.base.org',[dict(jsonrpc='2.0',id='a',method='eth_chainId')]*33)
