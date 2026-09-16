"""Invented retry receipts; structural Git verifier is separately tested."""
import base64
import importlib.util
import json
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('tested_protocol_audit',Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/protocol_closure_audit.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
EID='defi-depth-f1-20260915'


def fixture(tmp_path,monkeypatch):
    run=tmp_path/'research_runs'/EID;out=run/'outputs';out.mkdir(parents=True)
    (run/'complete.json').write_text(json.dumps({'ended_at':'invented'}))
    monkeypatch.setattr(m,'verify_run',lambda r:{'status':'complete'})
    total=0
    for slot in (1,2,3):
        rid=f'invented-try{slot}';request={'jsonrpc':'2.0','id':rid,'method':'eth_call','params':[{'to':'invented','data':'0x'},'invented']}
        key=json.dumps([request['method'],request['params']],sort_keys=True,separators=(',',':'))
        intent={'id':rid,'logical_id':'invented','logical_key':key,'physical_slot':slot,'attempted':slot<3,
                'request':request,'url':'https://mainnet.base.org','request_utc':'invented','max_response_bytes':16384}
        body=(b'invented outage' if slot==1 else b'{"invented":"result"}') if slot<3 else b''
        total+=len(body)
        receipt={**intent,'body_base64':base64.b64encode(body).decode(),'body_sha256':m.sha(body),'body_bytes':len(body),
                 'http_status':503 if slot==1 else 200 if slot==2 else None}
        for kind,obj in [('attempt',intent),('receipt',receipt)]:
            (out/f'{rid}-{kind}.json').write_text(json.dumps(obj))
    summary={'physical_requests':2,'raw_bytes':total,'rows':[],'status':'unavailable','endpoint_stop':None}
    (out/'source-summary.json').write_text(json.dumps(summary))
    (run/'claim.json').write_text(json.dumps({'source':'invented','started_at':'invented',
        'experiment':{'cells':['invented'],'outputs':[p.name for p in out.iterdir()]}}))
    return out


def test_two_physical_tries_one_spent_logical_key(tmp_path,monkeypatch):
    fixture(tmp_path,monkeypatch);r=m.audit(tmp_path,EID)
    assert r['counts']['actual_physical_requests']==2
    assert r['counts']['actual_unique_logical_keys']==1
    assert r['counts']['suppressed_physical_slots']==1
    assert r['http_status_counts']=={'503':1,'200':1}


def test_corrupt_retained_body_is_not_provider_unavailability(tmp_path,monkeypatch):
    out=fixture(tmp_path,monkeypatch);p=out/'invented-try1-receipt.json';r=json.loads(p.read_text())
    r['body_base64']=base64.b64encode(b'altered').decode();p.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='body hash/length'):m.audit(tmp_path,EID)


def test_complete_missing_retry_slot_rejected(tmp_path,monkeypatch):
    out=fixture(tmp_path,monkeypatch)
    for kind in ('attempt','receipt'):(out/f'invented-try3-{kind}.json').unlink()
    with pytest.raises(ValueError,match='missing physical slots'):m.audit(tmp_path,EID)


def test_uncertain_intent_stays_spent_in_failed_run(tmp_path,monkeypatch):
    out=fixture(tmp_path,monkeypatch);run=out.parent
    (run/'complete.json').rename(run/'failed.json');(out/'source-summary.json').unlink()
    (out/'invented-try2-receipt.json').unlink()
    monkeypatch.setattr(m,'verify_run',lambda r:{'status':'failed'})
    r=m.audit(tmp_path,EID)
    assert r['counts']['uncertain_actual_requests']==1
    assert r['counts']['actual_physical_requests']==1
    assert r['counts']['actual_or_uncertain_physical_requests']==2
    assert len(r['actual_or_uncertain_request_keys'])==1
    assert r['counts']['registered_cells']==1 and r['counts']['unpublished_outputs']==2


def test_unpaired_intent_cannot_hide_duplicate_logical_request(tmp_path,monkeypatch):
    out=fixture(tmp_path,monkeypatch);run=out.parent
    (run/'complete.json').rename(run/'failed.json');(out/'source-summary.json').unlink()
    old=json.loads((out/'invented-try1-attempt.json').read_text())
    old.update(id='second-try1',logical_id='second');old['request']['id']='second-try1'
    (out/'second-try1-attempt.json').write_text(json.dumps(old))
    monkeypatch.setattr(m,'verify_run',lambda r:{'status':'failed'})
    with pytest.raises(ValueError,match='another logical ID'):m.audit(tmp_path,EID)
