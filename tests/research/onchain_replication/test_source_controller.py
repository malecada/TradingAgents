import importlib.util
from pathlib import Path
import json
import pytest
from tradingagents.research.onchain_replication.provenance import file_hash

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/metadata-01'

def load(name):
    spec=importlib.util.spec_from_file_location('metadata_'+name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_controller_ownership_and_worker_receipt_agree_and_cannot_touch_pilot():
    owner,monitor,worker=map(load,('launch','monitor','worker'))
    assert owner.ROOT==monitor.ROOT==worker.ROOT==ROOT
    assert owner.receipt==monitor.receipt==worker.GUARD
    assert owner.ownership==monitor.ownership
    assert owner.receipt.name=='source-metadata-01-guard'
    assert owner.ownership.name=='source-metadata-01-supervisor'
    assert owner.receipt!=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-01-guard'


def test_metadata_observer_refuses_other_owner_and_is_idempotent(tmp_path,monkeypatch):
    observer=load('reconcile');monkeypatch.setattr(observer,'ROOT',tmp_path)
    receipt=tmp_path/'receipt';receipt.mkdir();artifacts=tmp_path/'sources'
    identity={'monitor_pid':123,'nonce':'synthetic','monitor_start_ticks':'1'}
    (receipt/'live.json').write_text(json.dumps({'owner_identity':identity,'monitor_pid':123,'cgroup':None}))
    with pytest.raises(ValueError,match='ownership'):observer.reconcile(receipt,artifacts,'a'*40,{**identity,'nonce':'other'})
    assert not (receipt/'observer.json').exists()
    result=observer.reconcile(receipt,artifacts,'a'*40,identity)
    before=file_hash(receipt/'observer.json')
    assert observer.reconcile(receipt,artifacts,'a'*40,identity)==result
    assert file_hash(receipt/'observer.json')==before
    assert result['status']=='not_admitted'


@pytest.mark.parametrize('partial',[False,True])
def test_interrupted_metadata_observer_retains_all_slots_and_partial_artifacts(tmp_path,monkeypatch,partial):
    observer=load('reconcile');monkeypatch.setattr(observer,'ROOT',tmp_path)
    receipt=tmp_path/'receipt';receipt.mkdir();cgroup=tmp_path/'synthetic-cgroup';cgroup.mkdir()
    (cgroup/'cgroup.events').write_text('populated 0\n')
    identity={'monitor_pid':123,'nonce':'synthetic'}
    (receipt/'live.json').write_text(json.dumps({'cgroup':str(cgroup),'owner_identity':identity,'monitor_pid':123}))
    artifacts=tmp_path/'sources';artifacts.mkdir()
    (artifacts/'partial-response.bin').write_bytes(b'synthetic interrupted bytes')
    if partial:(artifacts/'postmortem').mkdir()
    directory=tmp_path/'research_runs'/observer.EXPERIMENT;directory.mkdir(parents=True);(directory/'outputs').mkdir()
    gate=json.loads((HERE/'gate-v3.json').read_bytes());cells=gate['experiments'][observer.EXPERIMENT]['cells']
    (directory/'claim.json').write_text(json.dumps({'source':'a'*40,'registration_sha256':file_hash(HERE/'gate-v3.json'),'experiment':{'cells':cells}}))
    result=observer.reconcile(receipt,artifacts,'a'*40,identity)
    assert result['status']=='failed' and (directory/'failed.json').exists()
    ledger=json.loads((artifacts/'postmortem/cell-ledger.json').read_bytes())
    assert len(ledger)==72 and [c['id'] for c in ledger]==cells
    index=json.loads((artifacts/'postmortem/artifact-index.json').read_bytes())
    assert index[str(artifacts/'partial-response.bin')]['sha256']==file_hash(artifacts/'partial-response.bin')
    assert observer.reconcile(receipt,artifacts,'a'*40,identity)==result
