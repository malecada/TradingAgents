"""Invented seeds and process outputs only; no empirical source reads."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

HERE=Path(__file__).resolve().parents[2]/'research/onchain-graph-2026-09-16/fullpanel_resume'
SPEC=importlib.util.spec_from_file_location('resume_runner_test',HERE/'run.py')
runner=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(runner)


class Run:
    def __init__(self,root):
        self.directory=root/'research_runs'/runner.EXPERIMENT
        (self.directory/'outputs').mkdir(parents=True)
        self.publications=[]

    def write_json(self,name,value):
        runner.storage.atomic_json(self.directory/'outputs'/name,value)
        self.publications.append(name)

    def read(self,name):return json.loads((self.directory/'outputs'/name).read_bytes())


def fixture(root,monkeypatch,*,duplicate=False,failure=None,wrong_digest=False,unexpected=False):
    (root/runner.BASE).mkdir(parents=True)
    (root/runner.RESUME_BASE).mkdir(parents=True)
    dates=['2022-01-01','2022-01-02','2022-01-03','2022-01-04']
    limits=dict(min_free_bytes=0,max_scratch_bytes=2**20,max_derived_bytes=10*2**20,max_hash_bytes=2**20)
    numerical=dict(dates=dates,expected_rows={d:1 for d in dates},expected_total_rows=4,
        expected_hash_bytes=128,expected_graph_unavailable=[dates[0],dates[-1]],limits=limits)
    runner.storage.atomic_json(root/runner.BASE/'plan.json',numerical)
    oldroot=root/'oldhash';oldroot.mkdir()
    monkeypatch.setattr(runner.hash_audit,'FREE_FLOOR_BYTES',0)
    plan=dict(numerical_plan=dict(path=runner.BASE+'plan.json',sha256=runner.sha(root/runner.BASE/'plan.json')),
        dates=dates,seed_count=2,seed_dates=dates[:2],remaining_dates=dates[2:],prior_run_id='prior',
        archive_root=runner.RESUME_BASE+'preserved',seed_files={},limits=limits,
        hash_roots=[dict(path=str(oldroot),day_indices=[0,1]),dict(path=str(root/'newhash'),day_indices=[2,3])])
    def seed(relative,raw):
        path=root/plan['archive_root']/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        plan['seed_files'][relative]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    def serialized(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    def phase(date,hashes=None):
        edge=date in numerical['expected_graph_unavailable'] or (unexpected and date==dates[2])
        return dict(date=date,source=dict(date=date,status='complete',integrity={'rows':1},
            activity=dict(events=1,nodes=2,directed_pairs=1),transaction_hashes=hashes or [],prefix=[]),
            count=dict(status='unavailable' if edge else 'complete',reason='boundary' if edge else None,
                features=dict(local40_sums=[0]*40,overlap_node_count=2,nonzero_nodes=0)))
    for index,date in enumerate(dates[:2]):
        appended=runner.hash_audit.append_day(oldroot,[(index+1).to_bytes(32,'big')],index)
        report=dict(passed=True,source_rows=1,source_hash_digest=appended['stream_sha256'],count_verified=index!=0)
        value=dict(phase(date),independent=report,hash_append=appended)
        seed(f'research_runs/prior/outputs/day-{date}.json',serialized(value))
        seed(runner.BASE+f'artifacts/checks/{date}.json',serialized(report))
        seed(runner.BASE+f'artifacts/cleanup/{date}.json',serialized({'released':True}))
        seed(runner.BASE+f'artifacts/prefixes/{date}/prefix-0000.zst',b'synthetic preserved prefix')
        for suffix in ['.json','.intent.json']:
            name=f'day-{index:04d}{suffix}'
            seed(runner.BASE+'artifacts/hash-receipts/'+name,(oldroot/name).read_bytes())
    calls=[];run=Run(root)
    def command(command,check,cwd):
        assert check and cwd==root
        args={command[i]:command[i+1] for i in range(3,len(command),2)}
        assert args['--plan']==runner.BASE+'plan.json'
        if command[2].endswith('/day.py'):
            date=args['--date'];calls.append(('extract',date))
            assert date in dates[2:]
            previous=root/args['--previous']
            assert previous==run.directory/'outputs'/('day-'+dates[dates.index(date)-1]+'.json')
            assert runner.sha(previous)==args['--previous-sha256']
            if date==failure:raise subprocess.CalledProcessError(1,command)
            value=(1 if duplicate else dates.index(date)+1).to_bytes(32,'big')
            target=root/args['--phase'];target.parent.mkdir(parents=True)
            meta=runner.storage.write_blob(target.parent/'hashes.zst',value)
            meta.update(path=str((target.parent/'hashes.zst').relative_to(root)),hashes=1)
            runner.storage.atomic_json(target,phase(date,[meta]))
        else:
            target=root/args['--phase'];value=json.loads(target.read_bytes());date=value['date']
            calls.append(('check',date))
            meta=value['source']['transaction_hashes'][0]
            raw=runner.storage.read_blob(root/meta['path'],meta)
            report=dict(date=date,passed=True,phase_sha256=runner.sha(target),source_rows=1,
                count_verified=value['count']['status']=='complete',
                source_hash_digest='0'*64 if wrong_digest else hashlib.sha256(raw).hexdigest())
            runner.storage.atomic_json(Path(args['--report']),report)
    monkeypatch.setattr(runner.subprocess,'run',command)
    return plan,run,calls


def snapshot(root):return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_seed_republication_and_continuation_are_exact(tmp_path,monkeypatch):
    plan,run,calls=fixture(tmp_path,monkeypatch)
    oldroot=Path(plan['hash_roots'][0]['path']);before=snapshot(oldroot)
    archived=snapshot(tmp_path/plan['archive_root'])
    original_cleanup=runner.cleanup_day
    def durable(root,scratch,manifest):
        value=run.read('day-'+scratch.name+'.json')
        index=plan['dates'].index(scratch.name)
        assert value['independent']['passed']
        assert (root/runner.BASE/f'artifacts/hash-receipts/day-{index:04d}.json').exists()
        original_cleanup(root,scratch,manifest)
    monkeypatch.setattr(runner,'cleanup_day',durable)
    cells=runner.execute(tmp_path,plan,run)
    assert calls==[(stage,date) for date in plan['remaining_dates'] for stage in ['extract','check']]
    assert len(cells)==9 and len(run.publications)==7 and len(set(run.publications))==7
    assert run.read('hash-audit.json')['rows']==4 and run.read('hash-audit.json')['admitted']
    assert run.read('summary.json')['expected_boundary_only']
    assert run.read('summary.json')['source_days']==4 and run.read('summary.json')['graph_days']==2
    for date in plan['seed_dates']:
        relative=f'research_runs/prior/outputs/day-{date}.json'
        assert runner.sha(run.directory/'outputs'/Path(relative).name)==plan['seed_files'][relative]['sha256']
    assert before==snapshot(oldroot) and archived==snapshot(tmp_path/plan['archive_root'])
    assert not (tmp_path/'newhash/day-0000.json').exists()
    assert (tmp_path/'newhash/day-0002.json').exists()
    assert not list((tmp_path/runner.BASE/'artifacts/scratch').iterdir())


def test_remaining_failure_keeps_seed_and_full_denominator(tmp_path,monkeypatch):
    plan,run,calls=fixture(tmp_path,monkeypatch,failure='2022-01-03')
    cells=runner.execute(tmp_path,plan,run)
    assert len(cells)==9 and calls==[('extract','2022-01-03')]
    assert run.read('hash-audit.json')['checked_days']==2
    assert run.read('day-2022-01-04.json')['source']['status']=='unavailable'
    assert run.read('day-2022-01-01.json')['source']['status']=='complete'
    assert all(not row['source_admitted'] for row in run.read('panel.json')['days'])


def test_cross_namespace_duplicate_blocks_every_panel_row(tmp_path,monkeypatch):
    plan,run,_=fixture(tmp_path,monkeypatch,duplicate=True)
    runner.execute(tmp_path,plan,run)
    audit=run.read('hash-audit.json')
    assert audit['rows']==4 and audit['unique']==2 and audit['duplicate_excess']==2
    assert not audit['admitted']
    assert all(not row['source_admitted'] and not row['graph_admitted'] for row in run.read('panel.json')['days'])


@pytest.mark.parametrize('bad',['seed_bytes','missing_seed','orphan','existing_artifacts','existing_hashroot','plan_hash','calendar','old_receipt'])
def test_startup_fails_closed_without_old_hash_mutation(tmp_path,monkeypatch,bad):
    plan,run,calls=fixture(tmp_path,monkeypatch)
    oldroot=Path(plan['hash_roots'][0]['path']);before=snapshot(oldroot)
    if bad=='seed_bytes':
        (tmp_path/plan['archive_root']/next(iter(plan['seed_files']))).write_bytes(b'changed')
    elif bad=='missing_seed':del plan['seed_files']['research_runs/prior/outputs/day-2022-01-01.json']
    elif bad=='orphan':
        relative=runner.BASE+'artifacts/prefixes/2022-01-03/orphan.zst'
        path=tmp_path/plan['archive_root']/relative;path.parent.mkdir(parents=True);path.write_bytes(b'orphan')
        plan['seed_files'][relative]=dict(bytes=6,sha256=runner.sha(path))
    elif bad=='existing_artifacts':(tmp_path/runner.BASE/'artifacts').mkdir()
    elif bad=='existing_hashroot':(tmp_path/'newhash').mkdir()
    elif bad=='plan_hash':plan['numerical_plan']['sha256']='0'*64
    elif bad=='calendar':plan['remaining_dates'].reverse()
    else:
        path=oldroot/'day-0000.intent.json'
        value=json.loads(path.read_bytes());value['new_field']='mismatched original metadata'
        path.write_text(json.dumps(value))
        before=snapshot(oldroot)
    with pytest.raises((ValueError,FileExistsError)):
        runner.execute(tmp_path,plan,run)
    assert not calls and snapshot(oldroot)==before


def test_wrong_stream_stops_and_preserves_new_attempt(tmp_path,monkeypatch):
    plan,run,calls=fixture(tmp_path,monkeypatch,wrong_digest=True)
    runner.execute(tmp_path,plan,run)
    assert len(calls)==2
    assert 'appended stream' in run.read('summary.json')['stopped']
    assert (tmp_path/'newhash/day-0002.json').exists()
    assert (tmp_path/runner.BASE/'artifacts/scratch/2022-01-03/phase.json').exists()


def test_combined_chunk_limit_includes_seed_and_prior_chunks(monkeypatch):
    monkeypatch.setattr(runner.hash_union,'MAX_BUCKET_BYTES',96)
    chunks=runner.bounded_hashes([b'\0'*32,b'\0'*32],[64]+[0]*255)
    assert next(chunks)==b'\0'*32
    with pytest.raises(ValueError,match='combined bucket'):next(chunks)


def test_unexpected_graph_stops_after_durable_output(tmp_path,monkeypatch):
    plan,run,calls=fixture(tmp_path,monkeypatch,unexpected=True)
    runner.execute(tmp_path,plan,run)
    assert len(calls)==2
    assert run.read('day-2022-01-03.json')['source']['status']=='complete'
    assert 'unexpected graph' in run.read('summary.json')['stopped']
    assert (tmp_path/runner.BASE/'artifacts/scratch/2022-01-03/phase.json').exists()


def test_resource_metadata_counts_toward_retained_cap(tmp_path,monkeypatch):
    plan,run,_=fixture(tmp_path,monkeypatch)
    artifacts=tmp_path/runner.BASE/'artifacts';artifacts.mkdir()
    used=runner.allocated(tmp_path/runner.RESUME_BASE)+runner.allocated(run.directory)
    plan['limits']['max_derived_bytes']=used
    runner.preflight(tmp_path,plan,artifacts)
    (tmp_path/runner.RESUME_BASE/'resource.json').write_bytes(b'x'*8192)
    with pytest.raises(OSError,match='retained derived'):runner.preflight(tmp_path,plan,artifacts)


@pytest.mark.parametrize('guarded',[False,True])
def test_main_proves_guard_before_claim(tmp_path,monkeypatch,guarded):
    events=[]
    source='a'*40
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(runner.sys,'argv',['run.py','--source',source])
    monkeypatch.setattr(runner.sys,'addaudithook',lambda hook:events.append('offline'))
    def admit(root,revision):
        assert root==tmp_path and revision==source
        events.append('admitted')
    def guard(root,revision):
        assert root==tmp_path and revision==source
        events.append('guard')
        if not guarded:raise ValueError('guard proof absent')
    def module(name,path):
        if path.name=='admission.py':return SimpleNamespace(EXPERIMENT=runner.EXPERIMENT,admit_resume=admit)
        assert path.name=='memory_guard.py'
        return SimpleNamespace(assert_guarded_worker=guard)
    monkeypatch.setattr(runner,'load',module)
    class Context:
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read_input(self,name):
            assert name=='plan'
            return b'{}'
        def finish(self,cells):
            assert cells==['synthetic']
            events.append('finished')
    def start(**kwargs):
        assert kwargs==dict(root=tmp_path,registration=runner.RESUME_BASE+'gates.json',experiment=runner.EXPERIMENT,source=source)
        events.append('claimed')
        return Context()
    monkeypatch.setattr(runner,'ResearchRun',SimpleNamespace(start=start))
    monkeypatch.setattr(runner,'execute',lambda root,plan,run:['synthetic'])
    if guarded:
        runner.main()
        assert events==['admitted','guard','offline','claimed','finished']
    else:
        with pytest.raises(ValueError,match='guard proof'):runner.main()
        assert events==['admitted','guard']
