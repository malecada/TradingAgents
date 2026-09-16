"""Invented terminal provenance and F1-to-F3 source reuse; no real run reads."""
import base64
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15'
spec=importlib.util.spec_from_file_location('tested_f3_context',HERE/'f3_context.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    d='2025-10-01';day={'date':d,'timestamp':1759276800,'candidate_block':123}
    raw_header={'number':'0x7b','timestamp':hex(day['timestamp']),'hash':'0x'+'a'*64,
                'parentHash':'0x'+'b'*64,'baseFeePerGas':'0x1'}
    header=m.S.P.actual_clock_header(raw_header,day,1780000000)
    def request(rid,method,params):return {'jsonrpc':'2.0','id':rid,'method':method,'params':params}
    def proof(key,method,params):
        rid=d+'-'+key;return {'id':rid,'attempted':False,'url':'https://mainnet.base.org','request':request(rid,method,params)}
    oldpacket={'prior_request_keys':[],'days':{d:{
        'suppressed_header_intent':proof('header-left','eth_getBlockByNumber',['0x7b',False]),
        'suppressed_price_intent':proof('oracle-prices','eth_call',[{'to':m.S.F2.ORACLE,'data':m.S.F2.encode_prices(['WST','ETH','USDC'])},None])}}}
    olddesign={'days':[day],'prior_request_keys':[],'price_field_history':m.S.O.price_fields([]),
               'ownership':{d:{'header':'new','prices':'new'}}}
    objects={'old-design.json':olddesign,'old-context.json':oldpacket}
    def add(logical,method,params,result):
        for slot in (1,2,3):
            rid=f'{logical}-try{slot}';req=request(rid,method,params)
            intent={'id':rid,'logical_id':logical,'logical_key':m.S.P.Q.request_key(method,params),
                    'attempted':slot==1,'url':'https://mainnet.base.org','request':req}
            objects[m.PREFIX+'outputs/'+rid+'-attempt.json']=intent
            if slot==1:
                body=json.dumps({'jsonrpc':'2.0','id':rid,'result':result}).encode()
                objects[m.PREFIX+'outputs/'+rid+'-receipt.json']={**intent,'body_base64':base64.b64encode(body).decode(),
                    'body_bytes':len(body),'body_sha256':m.sha(body),'http_status':200,'body_complete':True,
                    'error':None,'retrieval_utc':'2026-09-16T00:00:00+00:00'}
    add(d+'-header','eth_getBlockByNumber',['0x7b',False],raw_header)
    price_data='0x'+''.join(format(v,'064x') for v in (32,2,2000*10**8,10**8))
    add(d+'-oracle-prices','eth_call',[{'to':m.S.F2.ORACLE,'data':m.S.F2.encode_prices(['ETH','USDC'])},
                                    {'blockHash':header['hash'],'requireCanonical':True}],price_data)
    objects[m.PREFIX+'outputs/'+d+'-source.json']={'cells':[
        {'id':d+'-actual-clock','status':'complete','value':header,'successful_physical_slot':1},
        {'id':d+'-oracle-prices','status':'complete','value':{'ETH':2000*10**8,'USDC':10**8},'successful_physical_slot':1}]}
    raw_bytes=sum(o['body_bytes'] for path,o in objects.items() if path.endswith('-receipt.json'))
    objects[m.PREFIX+'outputs/source-summary.json']={'endpoint_stop':None,'physical_requests':2,'raw_bytes':raw_bytes}
    raws={p:json.dumps(o).encode() for p,o in objects.items()}
    claim={'inputs':{'design':{'path':'old-design.json','sha256':m.sha(raws['old-design.json'])},
                     'source_context':{'path':'old-context.json','sha256':m.sha(raws['old-context.json'])}},
           'experiment':{'outputs':[p.removeprefix(m.PREFIX+'outputs/') for p in raws if p.startswith(m.PREFIX)]}}
    claimraw=json.dumps(claim).encode()
    terminal={'status':'complete','claim_sha256':m.sha(claimraw),
              'output_sha256':{p.removeprefix(m.PREFIX+'outputs/'):m.sha(v) for p,v in raws.items() if p.startswith(m.PREFIX)}}
    terminalraw=json.dumps(terminal).encode()
    packet={'f1_claim_sha256':m.sha(claimraw),'f1_terminal_sha256':m.sha(terminalraw),
            'f1_audit':{'claim_sha256':m.sha(claimraw),'terminal_sha256':m.sha(terminalraw),
                        'counts':{'actual_physical_requests':2,'retained_raw_bytes':raw_bytes}},
            'evidence_base64':{p:base64.b64encode(v).decode() for p,v in raws.items()}}
    return packet,claimraw,terminalraw


def test_raw_shared_header_prices_and_spent_keys_reconstructed():
    p,c,t=fixture();context,owners,prior,design=m.reconstruct(p,c,t,[],[])
    assert context['2025-10-01']['prices']['prices_atoms_1e8']=={'ETH':2000*10**8,'USDC':10**8}
    assert owners['2025-10-01']=={'header':'retained','prices':'retained','fields':{}}
    assert len(prior)==2 and len(design['days'])==1


def test_missing_suppressed_intent_cannot_hide_source_denominator():
    p,c,t=fixture();del p['evidence_base64'][m.PREFIX+'outputs/2025-10-01-header-try3-attempt.json']
    with pytest.raises(KeyError):m.reconstruct(p,c,t,[],[])


def test_altered_raw_or_terminal_provenance_rejected():
    p,c,t=fixture();p['evidence_base64']['old-context.json']=base64.b64encode(b'{}').decode()
    with pytest.raises(ValueError,match='not bound'):m.reconstruct(p,c,t,[],[])
    p,c,t=fixture();p['f1_audit']['terminal_sha256']='0'*64
    with pytest.raises(ValueError,match='audit provenance'):m.reconstruct(p,c,t,[],[])


def test_new_lp_alias_cannot_repeat_f1_observation():
    p,c,t=fixture();action={'key':'lp-alias','method':'eth_call','to':m.S.F2.ORACLE,'data':m.S.F2.encode_prices(['ETH','USDC'])}
    with pytest.raises(ValueError,match='overlaps prior'):m.reconstruct(p,c,t,[action],[])


def test_bundle_cannot_underreport_parent_source_resource_usage():
    p,c,t=fixture();p['f1_audit']['counts']['actual_physical_requests']=1
    with pytest.raises(ValueError,match='resource totals differ'):m.reconstruct(p,c,t,[],[])
