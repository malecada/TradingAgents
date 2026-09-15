"""Invented ownership and terminal fixtures; no real source/calculation runs."""
import base64
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest

HERE=Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15'
spec=importlib.util.spec_from_file_location('tested_f1_context',HERE/'f1_context.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def first_owner():
    day={'date':'2025-10-01','timestamp':1759276800,'candidate_block':123}
    def proof(key,method,params):
        rid=day['date']+'-'+key
        return {'id':rid,'attempted':False,'url':'https://mainnet.base.org',
                'request':{'jsonrpc':'2.0','id':rid,'method':method,'params':params}}
    item={'suppressed_header_intent':proof('header-left','eth_getBlockByNumber',['0x7b',False]),
          'suppressed_price_intent':proof('oracle-prices','eth_call',[
              {'to':m.F2.ORACLE,'data':m.F2.encode_prices(['WST','ETH','USDC'])},None])}
    packet={'prior_request_keys':[],'days':{day['date']:item}}
    design={'days':[day],'prior_request_keys':[], 'price_field_history':m.O.price_fields([]),
            'ownership':{day['date']:{'header':'new','prices':'new'}}}
    return packet,design,item


def test_legitimate_unsent_requests_qualify_without_inventing_data():
    packet,design,_=first_owner()
    assert m.verify_packet(packet,design)=={'2025-10-01':{}}


@pytest.mark.parametrize('proof_name', ['suppressed_header_intent','suppressed_price_intent'])
@pytest.mark.parametrize('mutation', ['url','method','id','params','attempted','rpc'])
def test_false_first_owner_proofs_rejected(proof_name,mutation):
    packet,design,item=first_owner();p=item[proof_name]
    if mutation=='url':p['url']='https://unrelated.invalid'
    elif mutation=='attempted':p['attempted']=True
    else:p['request'][{'rpc':'jsonrpc'}.get(mutation,mutation)]=[] if mutation=='params' else 'different'
    with pytest.raises(ValueError,match='first-acquisition proof'):m.verify_packet(packet,design)


@pytest.mark.parametrize('body',[b'[]',b'7',b'{"jsonrpc":"2.0","id":"wrong","error":{"code":-1}}'])
def test_terminal_audit_preserves_malformed_failed_provider_response(tmp_path,body):
    run=tmp_path/'research_runs/defi-depth-f2-20260915';out=run/'outputs';out.mkdir(parents=True)
    intent={'id':'invented','attempted':True,'url':'https://mainnet.base.org','request_utc':'2026-09-15',
            'request':{'jsonrpc':'2.0','id':'invented','method':'eth_getBlockByNumber','params':['0x7b',False]}}
    receipt={**intent,'body_base64':base64.b64encode(body).decode(),'body_sha256':m.sha(body),
             'body_bytes':len(body),'http_status':503}
    objects={'invented-attempt.json':intent,'invented-receipt.json':receipt,
             'source-summary.json':{'rpc_requests':1,'raw_bytes':len(body),'price_rows':[],
                                    'status':'unavailable','reason':'invented provider response'}}
    def put(path,value):
        raw=json.dumps(value).encode();path.write_bytes(raw);return m.sha(raw)
    hashes={name:put(out/name,obj) for name,obj in objects.items()}
    claim={'experiment_id':'invented','source':'invented','started_at':'invented',
           'experiment':{'cells':['invented'],'outputs':list(objects)}}
    claim_hash=put(run/'claim.json',claim)
    put(run/'complete.json',{'claim_sha256':claim_hash,'output_sha256':hashes,'status':'complete',
        'cells':[{'id':'invented','status':'unavailable'}],'ended_at':'invented'})
    result=m.A.audit(tmp_path)
    assert result['counts']['invalid_rpc_envelopes']==1
    assert result['counts']['actual_source_requests']==1
    assert result['counts']['qualified_price_dates']==0
    assert result['counts']['retained_raw_bytes']==len(body)


def test_registered_evidence_does_not_trust_embedded_proof():
    proof={'attempted':False};raw=json.dumps(proof).encode();ref={'path':'original-intent','sha256':m.sha(raw)}
    claim={'claim':'invented'};claim_raw=json.dumps(claim).encode();claim_ref={'path':'claim','sha256':m.sha(claim_raw)}
    terminal={'claim_sha256':claim_ref['sha256']};terminal_raw=json.dumps(terminal).encode()
    terminal_ref={'path':'terminal','sha256':m.sha(terminal_raw)}
    packet={'evidence_refs':[ref,claim_ref,terminal_ref],
      'days':{'date':{'suppressed_header_intent':proof,'header_intent_ref':ref}},
      'f2_claim_ref':claim_ref,'f2_terminal_ref':terminal_ref,
      'f2_audit':{'claim_sha256':claim_ref['sha256'],'terminal_sha256':terminal_ref['sha256']}}
    raws=[raw,claim_raw,terminal_raw]
    read=lambda name:raws[int(name.rsplit('_',1)[1])]
    m.verify_registered_evidence(packet,read)
    changed=deepcopy(packet);changed['days']['date']['suppressed_header_intent']['attempted']=True
    with pytest.raises(ValueError,match='embedded ownership evidence'):m.verify_registered_evidence(changed,read)
    raws[0]=b'{}'
    with pytest.raises(ValueError,match='hash differs'):m.verify_registered_evidence(packet,read)
