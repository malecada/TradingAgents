"""Power-loss simulation in disposable synthetic Git roots only."""
import importlib.util
import json
from pathlib import Path
import subprocess
import pytest
from tradingagents.research.verify import verify_run
from tradingagents.research.admission import claims
HERE=Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15'
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('tested_zero_output_recovery',HERE/'f1_restart_recovery.py')
old=module('synthetic_original_lifecycle_fixtures',Path(__file__).with_name('test_lifecycle.py'))


@pytest.fixture
def interrupted(tmp_path):
    registered=old.registered.__wrapped__(tmp_path)
    run=old.start(registered)  # deliberately no context exit, representing lost process
    raw=(run.directory/'claim.json').read_bytes();claim=json.loads(raw)
    config={'experiment':claim['experiment_id'],'original_claim_sha256':m.sha(raw),
            'original_source':claim['source'],'registration':claim['registration'],'original_started_at':claim['started_at']}
    return tmp_path,config,raw


def test_recovery_finishes_original_claim_without_spending_another_trial(interrupted):
    root,c,raw=interrupted;run=m.restore(root,c);factory=m.factory(run)
    args={'root':root,'registration':c['registration'],'experiment':c['experiment'],'source':c['original_source']}
    with factory.start(**args) as active:
        assert active.read_input('sample')==b'[2, 3]'
        old.complete(active)
    assert (run.directory/'claim.json').read_bytes()==raw
    assert verify_run(run.directory)['status']=='complete'
    assert len(claims(root))==1
    with pytest.raises(ValueError,match='attaches once'):factory.start(**args)


@pytest.mark.parametrize('name',['history.json','.pending-interrupted'])
def test_nonempty_or_pending_outputs_forbid_replay(interrupted,name):
    root,c,raw=interrupted;d=root/'research_runs'/c['experiment']
    (d/'outputs'/name).write_bytes(b'invented prior bytes')
    with pytest.raises(ValueError,match='zero-output'):m.restore(root,c)
    assert (d/'claim.json').read_bytes()==raw


def test_changed_input_or_claim_cannot_be_hidden_by_recovery(interrupted):
    root,c,raw=interrupted;(root/'sample.json').write_text('[99]')
    with pytest.raises(ValueError,match='input hash differs'):m.restore(root,c)
    d=root/'research_runs'/c['experiment'];(d/'claim.json').write_bytes(raw+b' ')
    with pytest.raises(ValueError,match='claim hash changed'):m.restore(root,c)


def test_terminal_claim_cannot_attach(interrupted):
    root,c,raw=interrupted;d=root/'research_runs'/c['experiment']
    (d/'failed.json').write_text('{}')
    with pytest.raises(ValueError,match='only original claim'):m.restore(root,c)


def test_shared_root_lock_prevents_concurrent_attachments(interrupted):
    root,c,_=interrupted
    with m.exclusive_owner(root,c['experiment']):
        with pytest.raises(BlockingIOError):
            with m.exclusive_owner(root,c['experiment']):pass
    with m.exclusive_owner(root,c['experiment']):pass


def test_durable_attachment_survives_adapter_checkout_change(interrupted,tmp_path):
    root,c,_=interrupted
    first={'adapter_root':str(tmp_path/'adapter-a'),'original_claim_sha256':c['original_claim_sha256']}
    with m.exclusive_owner(root,c['experiment']):marker=m.reserve_attachment(root,c,first)
    second={**first,'adapter_root':str(tmp_path/'adapter-b')}
    with m.exclusive_owner(root,c['experiment']):
        with pytest.raises(FileExistsError):m.reserve_attachment(root,c,second)
    assert json.loads(marker.read_bytes())==first


def test_additional_recovery_source_guard_remains_active(interrupted):
    root,c,_=interrupted;changed=False
    def guard():
        if changed:raise ValueError('invented recovery source change')
    run=m.restore(root,c,guard);changed=True
    with pytest.raises(ValueError,match='recovery source change'):run.write_json('summary.json',{'sum':5})
    assert not list((run.directory/'outputs').iterdir())


def test_committed_adapter_entry_preserves_claim_and_records_both_sources(tmp_path,monkeypatch):
    root=tmp_path/'original';root.mkdir();registered=old.registered.__wrapped__(root)
    engine='''from pathlib import Path
import argparse,json
from tradingagents.research import ResearchRun
ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--source');a=p.parse_args()
    with ResearchRun.start(root=ROOT,registration='registration.json',experiment='example-a',source=a.source) as run:
        values=json.loads(run.read_input('sample'))
        run.write_json('summary.json',{'sum':sum(values)})
        run.finish([{'id':'sum','status':'complete'},{'id':'count','status':'complete'}])
'''
    (root/'engine.py').write_text(engine);spec=registered[1]
    spec['experiments']['example-a']['source_files']['engine.py']=m.sha(engine.encode())
    source=old.commit(root,spec);run=old.start((root,spec,source))
    claim_raw=(run.directory/'claim.json').read_bytes();claim=json.loads(claim_raw)
    recovery=tmp_path/'recovery';recovery.mkdir();old.git(recovery,'init','-q')
    adapter=Path(m.__file__).read_bytes();(recovery/'adapter.py').write_bytes(adapter)
    config={'recovery_id':'invented-recovery','experiment':'example-a','execution_root':str(root),
        'original_source':source,'original_claim_sha256':m.sha(claim_raw),'original_started_at':claim['started_at'],
        'registration':'registration.json','original_runner':'engine.py','source_files':{'adapter.py':m.sha(adapter)}}
    (recovery/'config.json').write_text(json.dumps(config))
    old.git(recovery,'add','adapter.py','config.json')
    old.git(recovery,'-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','synthetic recovery')
    recovery_source=old.git(recovery,'rev-parse','HEAD')
    monkeypatch.setattr(m,'ROOT',recovery);monkeypatch.setattr(m,'CONFIG','config.json')
    monkeypatch.setattr(m.sys,'argv',['adapter','--recovery-source',recovery_source])
    real_run=m.subprocess.run
    def execute(args,**kwargs):
        if args==['pgrep','-f','[f]1_source.py']:return subprocess.CompletedProcess(args,1,b'',b'')
        return real_run(args,**kwargs)
    monkeypatch.setattr(m.subprocess,'run',execute)
    m.main()
    assert (run.directory/'claim.json').read_bytes()==claim_raw
    assert verify_run(run.directory)['status']=='complete' and len(claims(root))==1
    event=json.loads((recovery/'research_recoveries/invented-recovery/started.json').read_bytes())
    assert event['original_source']==source and event['recovery_source']==recovery_source
    assert event['new_empirical_claim'] is False
    assert (root/'research_runs/.example-a-recovery-attachment.json').exists()
