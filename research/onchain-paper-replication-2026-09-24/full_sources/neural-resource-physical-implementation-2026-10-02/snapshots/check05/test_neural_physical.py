"""Fresh invented owners and bounded bytes; no real guard/unit launch."""
import importlib
import json
from pathlib import Path
import pytest


def module():
    try:return importlib.import_module('tradingagents.research.onchain_replication.neural_physical')
    except ModuleNotFoundError:pytest.fail('selected physical route missing')


def limits():
    return {'schema_version':1,'max_file_bytes':65536,'max_json_bytes':8192,'max_allocated_bytes':2*1024**2,
            'max_logical_bytes':1024**2,'max_entries':128,'tail_reserve_bytes':131072}


def fresh(tmp_path):
    n=module();base=tmp_path/n.PREFIX/'runs'/'invented';base.mkdir(parents=True)
    return n.Scope.create(tmp_path,'invented','a'*40,limits(),{'nonce':'invented','supervisor_pid':1}),base


def test_no_precreated_claim_or_producer_roots(tmp_path):
    n=module();base=tmp_path/n.PREFIX/'runs'/'invented';base.mkdir(parents=True)
    (tmp_path/'research_runs/invented').mkdir(parents=True)
    with pytest.raises(ValueError,match='fresh'):n.Scope.create(tmp_path,'invented','a'*40,limits(),{})
    assert not (base/'physical-anchor.json').exists()


def test_three_root_birth_claim_and_terminal_accounting(tmp_path):
    scope,base=fresh(tmp_path);n=module()
    life=tmp_path/'research_runs/invented';life.mkdir(parents=True);(life/'outputs').mkdir()
    scope.immutable(life/'claim.json',{'experiment_id':'invented','source':'a'*40})
    producer=tmp_path/n.PREFIX/'sources/invented';producer.mkdir(parents=True)
    scope.immutable(producer/'intent.json',{'claim_sha256':scope.check()['claim_sha256']})
    scope.immutable(life/'failed.json',{'status':'failed'})
    scope.immutable(base/'observer.json',{'status':'failed'})
    receipt=scope.finish()
    assert receipt['roles']==['control','lifecycle','producer']
    assert receipt['claim_sha256'] and receipt['files']>=6
    assert receipt['terminal_tail_included'] is True
    assert json.loads((base/'physical-final.json').read_bytes())['status']=='accounted'


def test_metadata_limit_refuses_before_creating_file_and_keeps_history(tmp_path):
    scope,base=fresh(tmp_path)
    scope.immutable(base/'small.json',{'value':'kept'})
    before=(base/'small.json').read_bytes()
    with pytest.raises(ValueError,match='JSON'):scope.immutable(base/'large.json',{'value':'x'*10000})
    assert not (base/'large.json').exists() and (base/'small.json').read_bytes()==before
    with pytest.raises(FileExistsError):scope.immutable(base/'small.json',{})


def test_root_replacement_symlink_and_foreign_claim_refused(tmp_path):
    scope,base=fresh(tmp_path)
    life=tmp_path/'research_runs/invented';life.mkdir(parents=True)
    with pytest.raises(ValueError,match='claim'):scope.immutable(life/'claim.json',{'experiment_id':'foreign','source':'a'*40})
    assert not (life/'claim.json').exists()


def test_exact_file_limit_readback_is_required():
    n=module()
    n.verify_file_limit(65536,(65536,65536))
    for value in ((65536,-1),(32768,65536),(65536,131072)):
        with pytest.raises(ValueError,match='file limit'):n.verify_file_limit(65536,value)


def test_selected_metadata_context_bounds_real_lifecycle_writer_and_restores(tmp_path):
    scope,base=fresh(tmp_path)
    from tradingagents.research import lifecycle
    assert hasattr(lifecycle,'metadata_scope'),'opt-in lifecycle publication scope missing'
    with lifecycle.metadata_scope(scope):
        lifecycle._immutable(base/'inside.json',{'safe':True})
        with lifecycle.metadata_scope(scope):
            with pytest.raises(ValueError,match='JSON'):lifecycle._immutable(base/'large.json',{'x':'a'*10000})
    outside=tmp_path/'outside.json';lifecycle._immutable(outside,{'x':'a'*10000})
    assert outside.exists() and not (base/'large.json').exists()


def test_selected_metadata_scope_refuses_nested_foreign_authority(tmp_path):
    first,base=fresh(tmp_path);other=tmp_path/'other';other.mkdir();second,_=fresh(other)
    from tradingagents.research import lifecycle
    assert hasattr(lifecycle,'metadata_scope'),'opt-in lifecycle publication scope missing'
    with lifecycle.metadata_scope(first):
        with pytest.raises(ValueError,match='authority'):
            with lifecycle.metadata_scope(second):pass
        lifecycle._immutable(base/'kept.json',{'identity':'first'})
    assert (base/'kept.json').exists()


def test_real_kernel_file_limit_stops_child_writes_and_preserves_partial_bytes(tmp_path):
    # Tiny isolated subprocess only; no OS guard/unit, empirical arrays or parent rlimit changes.
    import subprocess,sys
    path=tmp_path/'child.log'
    script="""import os,resource,signal,sys
resource.setrlimit(resource.RLIMIT_FSIZE,(4096,4096))
signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
assert resource.getrlimit(resource.RLIMIT_FSIZE)==(4096,4096)
fd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
try:
 while True:os.write(fd,b'x'*1024)
except OSError as e:
 assert e.errno==27
finally:os.close(fd)
"""
    subprocess.run([sys.executable,'-B','-c',script,str(path)],check=True)
    assert path.stat().st_size==4096 and path.read_bytes()==b'x'*4096


def test_new_policy_is_explicit_and_neural_only(tmp_path):
    from tradingagents.research.onchain_replication import job
    resource={'memory_max_bytes':6*1024**3,'memory_high_bytes':5*1024**3,'reserve_bytes':3*1024**3,
              'start_reserve_bytes':9*1024**3,'disk_floor_bytes':10*1024**3,'disk_paths':[str(tmp_path)],'wall_seconds':60,'physical_policy':limits()}
    assert job.resource_policy(resource,tmp_path)==resource
    spec={'schema_version':1,'kind':'neural_resource','resources':resource,'payload':{'plan_input':'plan'},'environment_input':'env'}
    job.job_schema(spec)
    with pytest.raises(ValueError,match='neural'):job.job_schema({**spec,'kind':'fit'})


def test_guard_atomic_uses_selected_bound_and_old_route_unchanged(tmp_path):
    from tradingagents.research import lifecycle
    from tradingagents.research.onchain_replication import resources
    scope,base=fresh(tmp_path);guard=base/'guard';guard.mkdir()
    with lifecycle.metadata_scope(scope):
        resources._atomic(guard/'live.json',{'phase':'running'})
        before=(guard/'live.json').read_bytes()
        with pytest.raises(ValueError,match='JSON'):resources._atomic(guard/'live.json',{'oversize':'x'*10000})
        assert (guard/'live.json').read_bytes()==before
    resources._atomic(tmp_path/'old-route.json',{'oversize':'x'*10000})
    assert (tmp_path/'old-route.json').exists()


def test_lifecycle_output_requires_original_claim_birth(tmp_path):
    scope,base=fresh(tmp_path)
    output=tmp_path/'research_runs/invented/outputs/summary.json';output.parent.mkdir(parents=True)
    with pytest.raises(ValueError,match='claim'):scope.immutable(output,{'not_admitted':True})
    assert not output.exists()


def test_fresh_role_ancestor_cannot_redirect_before_birth(tmp_path):
    n=module();base=tmp_path/n.PREFIX/'runs'/'invented';base.mkdir(parents=True)
    external=tmp_path/'redirect';external.mkdir();(tmp_path/'research_runs').symlink_to(external,target_is_directory=True)
    with pytest.raises(ValueError,match='ancestor|redirect'):n.Scope.create(tmp_path,'invented','a'*40,limits(),{})
    assert not (base/'physical-anchor.json').exists()


def test_guard_requires_file_limit_readback_before_release(tmp_path,monkeypatch):
    import subprocess
    from tests.research.onchain_replication.test_resources import mock_unit
    from tradingagents.research.onchain_replication import resources
    from tradingagents.research import lifecycle
    scope,base=fresh(tmp_path)
    receipt,calls=mock_unit(base,monkeypatch,completed=True)
    original=resources.subprocess.run
    def run(args,**kw):
        result=original(args,**kw)
        if args[0]=='systemd-run':
            path=receipt/'cpu_ready.json';value=json.loads(path.read_bytes());value['file_size_limit']=[65536,65536];path.write_text(json.dumps(value))
        return result
    monkeypatch.setattr(resources.subprocess,'run',run)
    with lifecycle.metadata_scope(scope):
        result=resources.guarded_run(['true'],cwd=tmp_path,receipt_dir=receipt,
            disk_paths=[tmp_path],disk_floor_bytes=1,physical_policy=limits(),
            owner_identity={'experiment':'invented','source_commit':'a'*40})
    assert result['phase']=='complete'
    assert '--property=LimitFSIZE=65536' in calls[0] and '--physical' in calls[0]
    assert json.loads((receipt/'release.json').read_bytes())['kernel_controls_verified'] is True


def test_selected_worker_counts_real_model_outputs_and_lifecycle_tail(tmp_path,monkeypatch):
    from contextlib import contextmanager
    from types import SimpleNamespace
    from tests.research.onchain_replication.test_neural_resource import synthetic_run
    from tradingagents.research.onchain_replication import job,resources
    from tradingagents.research.onchain_replication.provenance import file_hash
    from tradingagents.research import lifecycle
    n=module();run,plan=synthetic_run(tmp_path,monkeypatch)
    physical={**limits(),'max_file_bytes':8*1024**2,'max_json_bytes':256*1024,
              'max_allocated_bytes':128*1024**2,'max_logical_bytes':96*1024**2,'tail_reserve_bytes':16*1024**2}
    path=tmp_path/'execution.json';value=json.loads(path.read_bytes());value['resources']['physical_policy']=physical;path.write_text(json.dumps(value));run.admission.inputs['execution_job']['sha256']=file_hash(path)
    args=SimpleNamespace(root=tmp_path,experiment=run.admission.experiment_id,source=run.admission.source,registration=run.admission.registration)
    base=job._base(args);scope=n.Scope.create(tmp_path,args.experiment,args.source,physical,{'nonce':'synthetic','supervisor_pid':1})
    scope.immutable(base/'launch.json',{'nonce':'synthetic','supervisor_pid':1})
    run.directory.mkdir(parents=True);(run.directory/'outputs').mkdir()
    scope.immutable(run.directory/'claim.json',{'experiment_id':args.experiment,'source':args.source})
    run._claim_sha256=file_hash(run.directory/'claim.json');run.admission.registration_sha256='a'*64
    owner=json.loads((base/'owner.json').read_bytes())
    monkeypatch.setattr(resources,'assert_guarded_worker',lambda *a,**kw:{**value['resources'],'owner_identity':owner})
    monkeypatch.setattr(job,'_admitted',lambda a:(run.admission,value))
    monkeypatch.setattr(job.signal,'signal',lambda *a:None)
    @contextmanager
    def start(**kw):yield run
    monkeypatch.setattr(job.ResearchRun,'start',start)
    job.worker(args)
    terminal=json.loads((run.directory/'complete.json').read_bytes())
    assert terminal['cell_count']==9 and terminal['unavailable_count']==0
    with lifecycle.metadata_scope(scope):
        scope.immutable(base/'observer.json',{'status':'complete'})
        result=scope.finish()
    paths=[p for root in scope.roots.values() for p in [root,*root.rglob('*')]]
    assert result['allocated_bytes']==sum(p.stat().st_blocks*512 for p in paths)
    assert result['logical_bytes']==sum(p.stat().st_size for p in paths if p.is_file())
    assert (run.directory/'outputs/resource-summary.json').exists()
    assert len(list(scope.roots['producer'].glob('cell-*/checkpoint.pt')))==9


def test_failure_tail_can_publish_after_active_budget_is_exhausted(tmp_path):
    scope,base=fresh(tmp_path)
    for i in range(14):(base/f'data-{i}').write_bytes(b'x'*60000)
    with pytest.raises(ValueError,match='budget'):scope.immutable(base/'ordinary.json',{'body':'no remaining active space'})
    scope.immutable(base/'observer.json',{'status':'failed'})
    assert (base/'observer.json').exists()


def test_cross_process_scope_writers_share_original_lock_and_accounting(tmp_path):
    import subprocess,sys
    scope,base=fresh(tmp_path)
    script="""import json,sys
from pathlib import Path
from tradingagents.research.onchain_replication.neural_physical import Scope
root=Path(sys.argv[1]);policy=json.loads(sys.argv[2]);scope=Scope.open(root,'invented','a'*40,policy)
for i in range(3):scope.immutable(scope.base/(sys.argv[3]+str(i)+'.json'),{'writer':sys.argv[3],'i':i})
"""
    children=[subprocess.Popen([sys.executable,'-B','-c',script,str(tmp_path),json.dumps(limits()),prefix]) for prefix in ('a','b')]
    assert [p.wait(timeout=10) for p in children]==[0,0]
    assert len(list(base.glob('a?.json')))==len(list(base.glob('b?.json')))==3
    assert scope.check()['files']>=9
