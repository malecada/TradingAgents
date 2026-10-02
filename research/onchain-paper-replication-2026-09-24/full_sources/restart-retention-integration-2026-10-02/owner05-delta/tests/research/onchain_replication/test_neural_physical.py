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


@pytest.fixture(autouse=True)
def close_test_authorities(monkeypatch):
    n=module();original=n.Scope.create;created=[]
    def create(cls,*args,**kwargs):
        result=original(*args,**kwargs);created.append(result);return result
    monkeypatch.setattr(n.Scope,'create',classmethod(create))
    yield
    for scope in created:
        try:scope.close_authority()
        except RuntimeError:pass  # Expected refusal tests retain failure in assertion/log.


def fresh(tmp_path):
    n=module();base=tmp_path/n.PREFIX/'runs'/'invented';base.mkdir(parents=True)
    (tmp_path/'research_runs').mkdir();(tmp_path/n.PREFIX/'sources').mkdir()
    return n.Scope.create(tmp_path,'invented','a'*40,limits(),{'nonce':'invented','supervisor_pid':1}),base


def test_no_precreated_claim_or_producer_roots(tmp_path):
    n=module();base=tmp_path/n.PREFIX/'runs'/'invented';base.mkdir(parents=True)
    (tmp_path/'research_runs/invented').mkdir(parents=True)
    with pytest.raises(ValueError,match='fresh'):n.Scope.create(tmp_path,'invented','a'*40,limits(),{})
    assert not (base/'physical-anchor.json').exists()


def test_three_root_birth_claim_and_terminal_accounting(tmp_path):
    scope,base=fresh(tmp_path);n=module()
    life=scope.birth('lifecycle');(life/'outputs').mkdir()
    scope.immutable(life/'claim.json',{'experiment_id':'invented','source':'a'*40})
    producer=scope.birth('producer')
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
    life=scope.birth('lifecycle')
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
    output=scope.birth('lifecycle')/'outputs/summary.json';output.parent.mkdir()
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
    base=job._base(args);(tmp_path/'research_runs').mkdir(exist_ok=True);(tmp_path/n.PREFIX/'sources').mkdir(exist_ok=True)
    scope=n.Scope.create(tmp_path,args.experiment,args.source,physical,{'nonce':'synthetic','supervisor_pid':1})
    args.physical_anchor=scope.anchor_hash
    scope.immutable(base/'launch.json',{'nonce':'synthetic','supervisor_pid':1})
    scope.birth('lifecycle');(run.directory/'outputs').mkdir()
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
    for i in range(15):(base/f'data-{i}').write_bytes(b'x'*61000)
    with pytest.raises(ValueError,match='budget'):scope.immutable(base/'ordinary.json',{'body':'no remaining active space'})
    scope.immutable(base/'observer.json',{'status':'failed'})
    assert (base/'observer.json').exists()


def test_cross_process_scope_writers_share_original_lock_and_accounting(tmp_path):
    import subprocess,sys
    scope,base=fresh(tmp_path)
    script="""import json,sys
from pathlib import Path
from tradingagents.research.onchain_replication.neural_physical import Scope
root=Path(sys.argv[1]);policy=json.loads(sys.argv[2]);scope=Scope.open(root,'invented','a'*40,policy,original_anchor=sys.argv[4])
for i in range(3):scope.immutable(scope.base/(sys.argv[3]+str(i)+'.json'),{'writer':sys.argv[3],'i':i})
"""
    children=[subprocess.Popen([sys.executable,'-B','-c',script,str(tmp_path),json.dumps(limits()),prefix,scope.anchor_hash]) for prefix in ('a','b')]
    assert [p.wait(timeout=10) for p in children]==[0,0]
    assert len(list(base.glob('a?.json')))==len(list(base.glob('b?.json')))==3
    assert scope.check()['files']>=9


def test_monitor_final_accounting_includes_observer_after_guard_returns(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from tradingagents.research import lifecycle
    from tradingagents.research.onchain_replication import job,resources
    scope,base=fresh(tmp_path)
    args=SimpleNamespace(root=tmp_path,experiment='invented',source='a'*40,registration='synthetic',owner_pid=1,nonce='invented',physical_anchor=scope.anchor_hash)
    launch={'experiment':'invented','source_commit':'a'*40,'supervisor_pid':1,'nonce':'invented'}
    scope.immutable(base/'launch.json',launch)
    spec={'resources':{'physical_policy':limits()}}
    monkeypatch.setattr(job,'_admitted',lambda a:(None,spec));monkeypatch.setattr(resources,'bind_parent_death',lambda p:None)
    monkeypatch.setattr(job.signal,'signal',lambda *a:None)
    def guarded(*a,**kw):
        directory=base/'guard';directory.mkdir()
        lifecycle._immutable(directory/'final.json',{'phase':'complete','cleanup_verified':True})
        return {'phase':'complete'}
    def reconcile(a):
        lifecycle._immutable(base/'observer.json',{'status':'complete','after_guard':True})
        return {'status':'complete'}
    monkeypatch.setattr(resources,'guarded_run',guarded);monkeypatch.setattr(job,'reconcile',reconcile)
    assert job.monitor(args)==0
    snapshot=json.loads((base/'physical-final.json').read_bytes())
    assert snapshot['snapshot_before_receipt']['files']>=7
    assert (base/'observer.json').exists()


def test_bounded_json_rejects_deep_values_without_recursion_failure(tmp_path):
    scope,base=fresh(tmp_path);value={}
    for _ in range(100):value={'nested':value}
    with pytest.raises(ValueError,match='depth'):scope.immutable(base/'deep.json',value)
    assert not (base/'deep.json').exists()


def test_authority_missing_claim_cannot_be_acknowledged(tmp_path):
    scope,base=fresh(tmp_path);life=scope.birth('lifecycle')
    scope.immutable(life/'claim.json',{'experiment_id':'invented','source':'a'*40})
    (life/'claim.json').rename(life/'retained-claim.json')
    with pytest.raises(ValueError,match='claim'):scope.check()


def test_authority_mutable_state_cannot_reset_root_birth(tmp_path):
    scope,base=fresh(tmp_path);life=scope.birth('lifecycle')
    scope.immutable(life/'claim.json',{'experiment_id':'invented','source':'a'*40})
    life.rename(life.with_name('preserved-first'));life.mkdir()
    (life/'claim.json').write_text(json.dumps({'experiment_id':'invented','source':'a'*40,'rewritten':True}))
    (base/'physical-state.json').write_text(json.dumps({'identities':{'control':scope.anchor['control_identity']},'claim_sha256':None}))
    with pytest.raises(ValueError,match='original|birth'):scope.check()


def test_authority_dangling_role_entry_is_not_absent(tmp_path):
    scope,base=fresh(tmp_path);life=scope.roots['lifecycle']
    life.symlink_to(tmp_path/'never-created',target_is_directory=True)
    with pytest.raises(ValueError,match='root|entry|redirect'):scope.check()


def test_authority_root_replacement_during_descriptor_scan_refuses(tmp_path,monkeypatch):
    import os
    scope,base=fresh(tmp_path);life=scope.birth('lifecycle')
    scope.immutable(life/'claim.json',{'experiment_id':'invented','source':'a'*40})
    original=os.scandir;replaced=False
    def swap(path):
        nonlocal replaced
        if isinstance(path,int) and os.fstat(path).st_ino==life.stat().st_ino and not replaced:
            replaced=True;life.rename(life.with_name('preserved-during-scan'));life.mkdir()
        return original(path)
    monkeypatch.setattr(os,'scandir',swap)
    with pytest.raises(ValueError,match='changed|replaced'):scope.check()
    assert replaced


def test_bounded_control_read_refuses_oversized_anchor_before_decode(tmp_path,monkeypatch):
    scope,base=fresh(tmp_path);n=module();(base/'physical-anchor.json').write_bytes(b'x'*10000)
    def decoded(*a,**kw):pytest.fail('oversized control file decoded before admission')
    monkeypatch.setattr(n.json,'loads',decoded)
    with pytest.raises(ValueError,match='extent|limit'):n.Scope.open(tmp_path,'invented','a'*40,limits())


def test_bounded_control_read_actual_fifo_refuses_without_blocking(tmp_path):
    import os,subprocess,sys
    scope,base=fresh(tmp_path);path=base/'physical-anchor.json';path.rename(base/'preserved-anchor.json');os.mkfifo(path)
    script="""import json,sys
from pathlib import Path
from tradingagents.research.onchain_replication.neural_physical import Scope
try:Scope.open(Path(sys.argv[1]),'invented','a'*40,json.loads(sys.argv[2]))
except ValueError as e:
 assert 'regular' in str(e) or 'type' in str(e)
else:raise AssertionError('FIFO accepted')
"""
    process=subprocess.Popen([sys.executable,'-B','-c',script,str(tmp_path),json.dumps(limits())])
    try:assert process.wait(timeout=2)==0
    except subprocess.TimeoutExpired:
        process.kill();process.wait();pytest.fail('control FIFO blocked before regular-file admission')


def test_reopen_requires_original_anchor_and_rejects_coherent_control_replacement(tmp_path):
    scope,base=fresh(tmp_path);n=module();original=scope.anchor_hash
    with pytest.raises(ValueError,match='original'):n.Scope.open(tmp_path,'invented','a'*40,limits())
    n.Scope.open(tmp_path,'invented','a'*40,limits(),original_anchor=original).check()
    preserved=base.with_name('preserved-control');base.rename(preserved)
    import shutil
    shutil.copytree(preserved,base)
    anchor=json.loads((base/'physical-anchor.json').read_bytes());anchor['control_identity']=[base.stat().st_dev,base.stat().st_ino]
    (base/'physical-anchor.json').write_text(json.dumps(anchor,sort_keys=True,indent=2)+'\n')
    with pytest.raises(ValueError,match='original'):n.Scope.open(tmp_path,'invented','a'*40,limits(),original_anchor=original)


def test_public_authority_fields_cannot_be_coherently_rebound(tmp_path):
    scope,base=fresh(tmp_path)
    replacement={**scope.anchor,'policy':{**scope.policy,'max_file_bytes':65537}}
    with pytest.raises((AttributeError,ValueError)):
        scope.anchor=replacement;scope.policy=replacement['policy']
        import hashlib
        scope.anchor_hash=hashlib.sha256(module()._encode(replacement)).hexdigest()
        (base/'physical-anchor.json').write_bytes(module()._encode(replacement))
        scope.check()


def test_original_parent_owns_birth_and_coherent_saved_record_replacement_refuses(tmp_path):
    scope,base=fresh(tmp_path);n=module()
    life=scope.birth('lifecycle');scope.immutable(life/'claim.json',{'experiment_id':'invented','source':'a'*40})
    original=scope.anchor_hash
    life.rename(life.with_name('preserved-original'));life.mkdir()
    (life/'claim.json').write_text(json.dumps({'experiment_id':'invented','source':'a'*40,'changed':True}))
    for path in base.glob('physical-birth-*.json'):
        value=json.loads(path.read_bytes());value['identity']=[life.stat().st_dev,life.stat().st_ino];path.write_text(json.dumps(value))
    (base/'physical-state.json').write_text(json.dumps({'identities':{'control':scope.anchor['control_identity'],'lifecycle':[life.stat().st_dev,life.stat().st_ino]},'claim_sha256':None}))
    with pytest.raises(ValueError,match='original|birth'):
        n.Scope.open(tmp_path,'invented','a'*40,limits(),original_anchor=original).check()


def test_parent_loss_prevents_reopen_and_scoped_mutation(tmp_path):
    scope,base=fresh(tmp_path);n=module();scope.close_authority()
    with pytest.raises((ValueError,RuntimeError),match='authority|parent'):
        n.Scope.open(tmp_path,'invented','a'*40,limits(),original_anchor=scope.anchor_hash)
    with pytest.raises((ValueError,RuntimeError),match='authority|parent'):scope.immutable(base/'after-parent.json',{})
    assert not (base/'after-parent.json').exists()
