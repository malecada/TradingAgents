"""Invented RPC replies only; never accesses public endpoints or actual research inputs."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import pytest

DIRECTORY=Path(__file__).resolve().parents[2]/'research/broader-allocation-2026-09-15'
loader=importlib.util.spec_from_file_location('tested_broader_dex',DIRECTORY/'dex_source.py')
m=importlib.util.module_from_spec(loader);loader.loader.exec_module(m)
SPEC=json.loads((DIRECTORY/'dex-source-spec.json').read_text())


def response(payload,result):
    return dict(body=json.dumps({'jsonrpc':'2.0','id':payload['id'],'result':result}).encode(),http_status=200,headers={},error=None,body_complete=True)


def invented(url,payload):
    chain=next(c for c in SPEC['chains'] if c['url']==url)
    kind=payload['id'].split('-',1)[1]
    result={'chain':hex(chain['chain_id']),'finalized':{'number':hex(chain['historical_block']+100),'hash':'0x'+'ab'*32,'timestamp':hex(1700000100)},
        'pool':'0x'+'0'*24+'12'*20,'gas':'0x64',
        'history_header':{'number':hex(chain['historical_block']),'hash':'0x'+'cd'*32,'timestamp':hex(1700000000)},'history_code':'0x6001600055'}[kind]
    return response(payload,result)


def test_complete_cells_preserve_raw_bytes_and_canonical_hash_requests():
    calls=[]; saved=[]
    def fetch(url,payload):
        calls.append(payload)
        return invented(url,payload)
    summary,receipts=m.capture(SPEC,fetch,lambda n,v:saved.append(n))
    assert len(summary['cells'])==len(receipts)==len(calls)==len(saved)==18
    assert all(c['status']=='complete' for c in summary['cells'])
    assert not summary['implementation_admitted']
    assert all(r['body_sha256']==hashlib.sha256(base64.b64decode(r['body_base64'])).hexdigest() for r in receipts)
    assert calls[2]['params'][1]=={'blockHash':'0x'+'ab'*32,'requireCanonical':True}
    assert calls[5]['params'][1]=={'blockHash':'0x'+'cd'*32,'requireCanonical':True}
    # Literal ABI layout independently checks both addresses and fee, not a mirrored hash.
    calldata=calls[2]['params'][0]['data']
    assert calldata[:10]=='0x1698ee82'
    assert calldata[10:74]=='0'*24+SPEC['chains'][0]['weth'][2:]
    assert calldata[74:138]=='0'*24+SPEC['chains'][0]['usdc'][2:]
    assert int(calldata[138:],16)==3000


def test_http_denial_retains_all_cells_and_stops_only_that_chain():
    def fetch(url,payload):
        if payload['id']=='ethereum-chain':
            return dict(body=b'denied',http_status=403,headers={},error='HTTP403',body_complete=True)
        return invented(url,payload)
    summary,receipts=m.capture(SPEC,fetch)
    assert summary['attempted_requests']==13
    assert len(summary['cells'])==18
    assert all(c['status']=='unavailable' for c in summary['cells'][:6])
    assert [r['attempted'] for r in receipts[:6]]==[True]+[False]*5
    assert base64.b64decode(receipts[0]['body_base64'])==b'denied'


def test_bad_identity_null_anchor_and_unsupported_hash_do_not_get_substitutes():
    def fetch(url,payload):
        if payload['id']=='ethereum-chain':return response(payload,'0x2')
        if payload['id']=='base-finalized':return response(payload,None)
        if payload['id']=='arbitrum-history_code':
            r=response(payload,None);r['body']=json.dumps({'jsonrpc':'2.0','id':payload['id'],'error':{'code':-32602}}).encode();return r
        return invented(url,payload)
    summary,receipts=m.capture(SPEC,fetch)
    assert summary['attempted_requests']==12
    assert len(summary['cells'])==18
    assert summary['cells'][8]['status']=='unavailable' # Base pool depends on anchor.
    assert not receipts[8]['attempted']
    assert summary['cells'][-1]['status']=='unavailable'


@pytest.mark.parametrize('raw',[b'{"jsonrpc":"2.0","id":"x","result":NaN}', b'{"a":1,"a":2}',b'null',b'[]'])
def test_malformed_envelope_unavailable(raw):
    p=m.request_for(SPEC['chains'][0],'chain',{})
    with pytest.raises((ValueError,TypeError)):
        m.parse(raw,p,SPEC['chains'][0],'chain',1800000000,{})


@pytest.mark.parametrize('value',['0x00','0x-1','0x',False,1,'100','0xgg'])
def test_quantity_encoding_is_strict(value):
    with pytest.raises(ValueError):m.quantity(value)


def test_zero_pool_is_observed_absence_not_successful_tradability():
    c=SPEC['chains'][0];ctx={'finalized':{'hash':'0x'+'ab'*32}}
    p=m.request_for(c,'pool',ctx)
    parsed=m.parse(response(p,'0x'+'0'*64)['body'],p,c,'pool',1800000000,ctx)
    assert parsed['pool_found'] is False
    assert parsed['pool_address']=='0x'+'0'*40


def test_wrong_header_future_time_empty_code_and_bad_padding_rejected():
    c=SPEC['chains'][0];ctx={'history_header':{'hash':'0x'+'cd'*32},'finalized':{'number':c['historical_block']+100,'timestamp':1700000100,'hash':'0x'+'ab'*32}}
    for kind,value in [('history_header',{'number':'0x1','hash':'0x'+'cd'*32,'timestamp':hex(1700000000)}),('finalized',{'number':'0x1','hash':'0x'+'ab'*32,'timestamp':hex(1900000000)}),('history_code','0x'),('pool','0x'+'ab'*32)]:
        p=m.request_for(c,kind,ctx)
        with pytest.raises(ValueError):m.parse(response(p,value)['body'],p,c,kind,1800000000,ctx)


def test_partial_body_and_oversize_prefix_are_retained_unavailable():
    def fetch(url,p):
        if p['id']=='ethereum-chain':return dict(body=b'x'*(262144+1),http_status=200,headers={},error=None,body_complete=True)
        if p['id']=='base-chain':return dict(body=b'{',http_status=200,headers={},error='timeout',body_complete=False)
        return invented(url,p)
    summary,receipts=m.capture(SPEC,fetch)
    assert receipts[0]['body_bytes']==262144 and not receipts[0]['body_complete']
    assert base64.b64decode(receipts[6]['body_base64'])==b'{'
    assert summary['cells'][0]['status']==summary['cells'][6]['status']=='unavailable'


def test_spec_rejects_unregistered_chain_or_grid():
    spec={**SPEC,'max_requests':19}
    with pytest.raises(ValueError):m.capture(spec,lambda *a:pytest.fail('must not fetch'))


def test_transport_forbids_mutations_and_unregistered_endpoints():
    for url,p in [('https://example.invalid',{'jsonrpc':'2.0','method':'eth_chainId'}), (SPEC['chains'][0]['url'],{'jsonrpc':'2.0','method':'eth_sendRawTransaction'})]:
        with pytest.raises(ValueError):m.transport.public_post(url,p)


def test_transport_keeps_incomplete_received_prefix_and_restores_alarm():
    class FakeResponse:
        code=200;headers={};length=10
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read1(self,n):return b''
    class FakeOpener:
        def open(self,*args,**kwargs):return FakeResponse()
    with patch.object(m.transport.urllib.request,'build_opener',return_value=FakeOpener()):
        r=m.transport.public_post(SPEC['chains'][0]['url'],m.request_for(SPEC['chains'][0],'chain',{}))
    assert r['body']==b'' and not r['body_complete'] and 'premature' in r['error']
    assert m.transport.signal.getitimer(m.transport.signal.ITIMER_REAL)==(0.0,0.0)


def test_header_timestamp_cannot_exceed_receipt_even_by_one_second():
    c=SPEC['chains'][0];p=m.request_for(c,'finalized',{})
    header={'number':'0x1','hash':'0x'+'ab'*32,'timestamp':hex(1800000001)}
    with pytest.raises(ValueError,match='future'):
        m.parse(response(p,header)['body'],p,c,'finalized',1800000000,{})
    header['timestamp']=hex(1800000000)
    assert m.parse(response(p,header)['body'],p,c,'finalized',1800000000,{})['timestamp']==1800000000


def test_rpc_id_mismatch_and_persist_failure_cannot_be_success():
    c=SPEC['chains'][0];p=m.request_for(c,'chain',{})
    raw=response({**p,'id':'different'},'0x1')['body']
    with pytest.raises(ValueError,match='ID mismatch'):
        m.parse(raw,p,c,'chain',1800000000,{})
    saved=[]
    def persist(name,value):
        if len(saved)==2:raise OSError('invented storage failure')
        saved.append(name)
    with pytest.raises(OSError,match='invented storage'):
        m.capture(SPEC,invented,persist)
    assert saved==['ethereum-chain-receipt.json','ethereum-finalized-receipt.json']
