"""Synthetic namespace/guard integration around the immutable prior pipeline."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'research/onchain-graph-2026-09-16/fullpanel_resume2'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


runner=load('resume2_test_runner',HERE/'run.py')
fixtures=load('resume2_prior_synthetic_fixtures',ROOT/'tests/research/test_onchain_fullpanel_resume_run.py')


@pytest.mark.parametrize('duplicate',[False,True])
def test_successor_uses_new_namespace_and_same_exact_pipeline(tmp_path,monkeypatch,duplicate):
    monkeypatch.setattr(fixtures,'runner',runner.pipeline)
    plan,run,calls=fixtures.fixture(tmp_path,monkeypatch,duplicate=duplicate)
    assert runner.execute is runner.pipeline.execute
    assert runner.pipeline.EXPERIMENT==runner.EXPERIMENT
    assert runner.pipeline.RESUME_BASE==runner.BASE
    before=fixtures.snapshot(Path(plan['hash_roots'][0]['path']))
    cells=runner.execute(tmp_path,plan,run)
    assert len(cells)==9
    assert run.directory==tmp_path/'research_runs'/runner.EXPERIMENT
    assert len(calls)==4 and all(day in plan['remaining_dates'] for _,day in calls)
    assert (tmp_path/runner.BASE/'hash-owner.json').exists()
    assert not (tmp_path/'research/onchain-graph-2026-09-16/fullpanel_resume/hash-owner.json').exists()
    assert fixtures.snapshot(Path(plan['hash_roots'][0]['path']))==before
    assert run.read('hash-audit.json')['admitted'] is not duplicate
    for date in plan['seed_dates']:
        path=f'research_runs/prior/outputs/day-{date}.json'
        assert runner.pipeline.sha(run.directory/'outputs'/Path(path).name)==plan['seed_files'][path]['sha256']


def test_remaining_failure_is_retained_in_successor(tmp_path,monkeypatch):
    monkeypatch.setattr(fixtures,'runner',runner.pipeline)
    plan,run,calls=fixtures.fixture(tmp_path,monkeypatch,failure='2022-01-03')
    assert len(runner.execute(tmp_path,plan,run))==9
    assert calls==[('extract','2022-01-03')]
    assert run.read('hash-audit.json')['checked_days']==2
    assert run.read('day-2022-01-04.json')['source']['status']=='unavailable'


@pytest.mark.parametrize('relative',list(runner.FROZEN_FILES))
def test_frozen_pipeline_and_hash_implementation_cannot_drift(tmp_path,relative):
    for name in runner.FROZEN_FILES:
        target=tmp_path/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((HERE.parent/name).read_bytes())
    runner.verify_frozen(tmp_path)
    (tmp_path/relative).write_bytes(b'changed implementation')
    with pytest.raises(ValueError,match='frozen continuation source'):
        runner.verify_frozen(tmp_path)


@pytest.mark.parametrize('guarded',[False,True])
def test_successor_main_requires_own_admission_and_guard_before_claim(tmp_path,monkeypatch,guarded):
    events=[];source='b'*40
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(runner.sys,'argv',['run.py','--source',source])
    monkeypatch.setattr(runner.sys,'addaudithook',lambda hook:events.append('offline'))
    def admitted(root,revision):
        assert root==tmp_path and revision==source
        events.append('admitted')
    def guarded_worker(root,revision):
        assert root==tmp_path and revision==source
        events.append('guard')
        if not guarded:raise ValueError('guard absent')
    def module(name,path):
        assert path.parent==HERE
        if path.name=='admission.py':return SimpleNamespace(EXPERIMENT=runner.EXPERIMENT,admit_resume=admitted)
        assert path.name=='memory_guard.py'
        return SimpleNamespace(assert_guarded_worker=guarded_worker)
    monkeypatch.setattr(runner,'load',module)
    class Context:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read_input(self,name):
            assert name=='plan'
            return json.dumps({'synthetic':True}).encode()
        def finish(self,cells):
            assert cells==['synthetic']
            events.append('finished')
    def start(**kwargs):
        assert kwargs==dict(root=tmp_path,registration=runner.BASE+'gates.json',experiment=runner.EXPERIMENT,source=source)
        events.append('claimed');return Context()
    monkeypatch.setattr(runner,'ResearchRun',SimpleNamespace(start=start))
    monkeypatch.setattr(runner,'execute',lambda root,plan,run:['synthetic'])
    if guarded:
        runner.main();assert events==['admitted','guard','offline','claimed','finished']
    else:
        with pytest.raises(ValueError,match='guard absent'):runner.main()
        assert events==['admitted','guard']
