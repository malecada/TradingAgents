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
        except BaseException:pass  # Expected refusal tests retain failure in assertion/log.


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
    assert all('--setenv='+key+'='+value in calls[0] for key,value in scope.environment().items())
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
              'max_allocated_bytes':160*1024**2,'max_logical_bytes':128*1024**2,'tail_reserve_bytes':32*1024**2}
    path=tmp_path/'execution.json';value=json.loads(path.read_bytes());value['resources']['physical_policy']=physical;path.write_text(json.dumps(value));run.admission.inputs['execution_job']['sha256']=file_hash(path)
    args=SimpleNamespace(root=tmp_path,experiment=run.admission.experiment_id,source=run.admission.source,registration=run.admission.registration)
    base=job._base(args);(tmp_path/'research_runs').mkdir(exist_ok=True);(tmp_path/n.PREFIX/'sources').mkdir(exist_ok=True)
    scope=n.Scope.create(tmp_path,args.experiment,args.source,physical,{'nonce':'synthetic','supervisor_pid':1})
    args.physical_anchor=scope.anchor_hash
    for env_key,env_value in scope.environment().items():monkeypatch.setenv(env_key,env_value)
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
    import tempfile
    monkeypatch.setattr(tempfile,'tempdir',tempfile.tempdir)
    job.worker(args)
    terminal=json.loads((run.directory/'complete.json').read_bytes())
    assert terminal['cell_count']==9 and terminal['unavailable_count']==0
    with lifecycle.metadata_scope(scope):
        scope.immutable(base/'observer.json',{'status':'complete'})
        result=scope.finish()
    paths=[p for root in scope.roots.values() for p in [root,*root.rglob('*')]]
    assert result['allocated_bytes']==sum(p.stat().st_blocks*512 for p in paths)
    assert result['logical_bytes']==sum(p.stat().st_size for p in paths if p.is_file())
    totals={}
    for role,root in scope.roots.items():
        members=[root,*root.rglob('*')]
        totals[role]={'allocated_bytes':sum(p.stat().st_blocks*512 for p in members),'logical_bytes':sum(p.stat().st_size for p in members if p.is_file()),'entries':len(members)}
    print('SYNTHETIC_PHYSICAL_TOTALS '+json.dumps({'limits':physical,'roles':totals,'total':result},sort_keys=True))
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
    assert scope.check()['files']==8


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
    assert snapshot['snapshot_before_receipt']['files']==6
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


def test_fresh_process_birth_binds_original_parent_state(tmp_path):
    import subprocess,sys
    scope,base=fresh(tmp_path)
    script="""import json,sys
from pathlib import Path
from tradingagents.research.onchain_replication.neural_physical import Scope
s=Scope.open(Path(sys.argv[1]),'invented','a'*40,json.loads(sys.argv[2]),original_anchor=sys.argv[3])
p=s.birth('lifecycle');s.immutable(p/'claim.json',{'experiment_id':'invented','source':'a'*40})
"""
    subprocess.run([sys.executable,'-B','-c',script,str(tmp_path),json.dumps(limits()),scope.anchor_hash],check=True,timeout=10)
    assert scope.check()['claim_sha256']==module()._hash(scope.roots['lifecycle']/'claim.json',limits()['max_json_bytes'])


def test_selected_launch_keeps_parent_authority_until_observer_closure(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from tradingagents.research import lifecycle
    from tradingagents.research.onchain_replication import job
    n=module();(tmp_path/'research_runs').mkdir();(tmp_path/n.PREFIX/'sources').mkdir(parents=True)
    args=SimpleNamespace(root=tmp_path,experiment='invented',source='a'*40,registration='synthetic')
    monkeypatch.setattr(job,'_admitted',lambda a:(None,{'resources':{'physical_policy':limits()}}))
    monkeypatch.setattr(job.signal,'signal',lambda *a:None)
    retained=[];events=[]
    class Monitor:
        def __init__(self,command,**kw):
            scope=lifecycle.current_metadata_scope();retained.append(scope)
            assert command[-6:-4]==['--physical-anchor',scope.anchor_hash]
        def wait(self):events.append('wait');retained[0].check();return 0
        def poll(self):return 0
    monkeypatch.setattr(job.subprocess,'Popen',Monitor)
    def reconcile(a):
        events.append('observer');retained[0].immutable(retained[0].base/'observer.json',{'status':'complete'});return {'status':'complete'}
    monkeypatch.setattr(job,'reconcile',reconcile)
    assert job.launch(args)==0 and events==['wait','observer']
    with pytest.raises(RuntimeError,match='authority'):retained[0].check()


def test_external_reconciliation_never_rebaselines_disk_anchor(tmp_path):
    from types import SimpleNamespace
    from tradingagents.research.onchain_replication import job
    scope,base=fresh(tmp_path)
    args=SimpleNamespace(root=tmp_path,experiment='invented',source='a'*40,registration='synthetic',physical_anchor=scope.anchor_hash)
    with pytest.raises(ValueError,match='original live parent'):job.reconcile(args)


def test_parent_transition_fatal_is_preserved_at_launcher_boundary(tmp_path,monkeypatch):
    scope,base=fresh(tmp_path);n=module();sentinel=SystemExit('original-birth-fatal');original=n._write
    def write(path,*a,**kw):
        if path.name=='physical-birth-lifecycle.json':raise sentinel
        return original(path,*a,**kw)
    monkeypatch.setattr(n,'_write',write)
    with pytest.raises(RuntimeError,match='authority'):scope.birth('lifecycle')
    with pytest.raises(SystemExit) as caught:scope.close_authority()
    assert caught.value is sentinel and scope.roots['lifecycle'].is_dir()


def test_terminal_entry_reserve_refuses_ordinary_publication_before_write(tmp_path):
    scope,base=fresh(tmp_path)
    for i in range(106):(base/f'empty-{i}').touch()
    with pytest.raises(ValueError,match='entry'):scope.immutable(base/'ordinary.json',{})
    assert not (base/'ordinary.json').exists()
    scope.immutable(base/'observer.json',{'status':'failed'})
    assert (base/'observer.json').exists()


def test_replaced_lock_fifo_refuses_without_waiting(tmp_path):
    import os
    scope,base=fresh(tmp_path);path=base/'physical.lock';path.rename(base/'preserved-lock');os.mkfifo(path)
    with pytest.raises(ValueError,match='lock'):scope.check()


def test_selected_scratch_mapping_is_propagated_and_cached_tempdir_reset(tmp_path,monkeypatch):
    import tempfile
    scope,base=fresh(tmp_path)
    expected={'TMPDIR':str(base/'scratch/tmp'),'TMP':str(base/'scratch/tmp'),'TEMP':str(base/'scratch/tmp'),
              'XDG_CACHE_HOME':str(base/'scratch/cache'),'TORCH_HOME':str(base/'scratch/torch')}
    assert scope.environment()==expected
    for key,value in expected.items():monkeypatch.setenv(key,value)
    monkeypatch.setattr(tempfile,'tempdir',str(tmp_path/'stale-cache'))
    scope.verify_environment()
    with tempfile.NamedTemporaryFile() as stream:
        assert Path(stream.name).parent==base/'scratch/tmp'
        stream.write(b'invented bytes');stream.flush();scope.check()
    monkeypatch.setenv('TORCH_HOME',str(tmp_path/'outside'))
    with pytest.raises(ValueError,match='scratch'):scope.verify_environment()


def test_parent_original_fatal_survives_real_socket_close_uncertainty(tmp_path,monkeypatch):
    scope,base=fresh(tmp_path);n=module();sentinel=SystemExit('owned-handler-primary');original=n._write
    def write(path,*a,**kw):
        if path.name=='physical-birth-lifecycle.json':raise sentinel
        return original(path,*a,**kw)
    monkeypatch.setattr(n,'_write',write)
    with pytest.raises(RuntimeError):scope.birth('lifecycle')
    server=scope._server;original_socket=server.socket;calls=[]
    class CloseUncertain:
        def __getattr__(self,name):return getattr(original_socket,name)
        def close(self):
            calls.append('close');original_socket.close();raise OSError('owned socket close uncertain')
    server.socket=CloseUncertain()
    with pytest.raises(SystemExit) as caught:scope.close_authority()
    assert caught.value is sentinel and calls==['close'] and original_socket.fileno()==-1
    assert any('close' in note for note in sentinel.__notes__)
    with pytest.raises(SystemExit):scope.close_authority()
    assert calls==['close']


def test_authority_constructor_closes_owned_socket_on_bind_failure(monkeypatch):
    from tradingagents.research.onchain_replication import neural_authority as a
    original=a.socket.socket;created=[];sentinel=RuntimeError('original bind failure')
    class FailingSocket(original):
        def __init__(self,*args,**kw):super().__init__(*args,**kw);self.closes=0;created.append(self)
        def bind(self,address):super().bind(address);raise sentinel
        def close(self):self.closes+=1;super().close()
    monkeypatch.setattr(a.socket,'socket',FailingSocket)
    with pytest.raises(RuntimeError) as caught:a.ParentAuthority(8192,lambda request:{})
    assert caught.value is sentinel and created[0].closes==1 and created[0].fileno()==-1


def test_client_primary_is_promoted_on_uncertain_owned_close(monkeypatch):
    from tradingagents.research.onchain_replication import neural_authority as a
    original=a.socket.socket;created=[]
    class FailingSocket(original):
        def __init__(self,*args,**kw):super().__init__(*args,**kw);self.closes=0;created.append(self)
        def connect(self,address):raise ValueError('original connect refusal')
        def close(self):self.closes+=1;super().close();raise OSError('uncertain actual client close')
    monkeypatch.setattr(a.socket,'socket',FailingSocket)
    identity={'pid':__import__('os').getpid(),'start_ticks':a.process_start(__import__('os').getpid()),'uid':__import__('os').getuid(),'address':'invented-no-server'}
    with pytest.raises(module().PhysicalCleanupFailure) as caught:a.request(identity,'a'*64,{'op':'get'},8192)
    assert isinstance(caught.value.__cause__,ValueError)
    assert created[0].closes==1 and created[0].fileno()==-1


from tests.research.test_lifecycle import registered


def test_selected_real_lifecycle_uses_parent_birth_and_preserves_default_registration(registered):
    from tradingagents.research import lifecycle
    root,spec,source=registered;n=module();base=root/n.PREFIX/'runs/example-a'
    base.mkdir(parents=True);(root/n.PREFIX/'sources').mkdir();(root/'research_runs').mkdir()
    scope=n.Scope.create(root,'example-a',source,limits(),{'nonce':'invented','supervisor_pid':1})
    with lifecycle.metadata_scope(scope):
        with lifecycle.ResearchRun.start(root=root,registration='registration.json',experiment='example-a',source=source) as run:
            run.write_json('summary.json',{'sum':5,'count':2})
            run.finish([{'id':'sum','status':'complete'},{'id':'count','status':'complete'}])
    assert scope.check()['claim_sha256']==run._claim_sha256
    assert json.loads((run.directory/'complete.json').read_bytes())['cell_count']==2


def test_parent_close_retains_inflight_fatal_after_join(monkeypatch):
    import threading
    from tradingagents.research.onchain_replication import neural_authority as a
    entered=threading.Event();release=threading.Event();sentinel=SystemExit('fatal-during-original-join')
    def handler(value):entered.set();assert release.wait(2);raise sentinel
    parent=a.ParentAuthority(8192,handler);failures=[]
    def client():
        try:a.request(parent.identity,'a'*64,{'op':'get'},8192)
        except BaseException as error:failures.append(error)
    caller=threading.Thread(target=client);caller.start();assert entered.wait(2)
    original_join=parent.thread.join
    def join(*args,**kwargs):release.set();return original_join(*args,**kwargs)
    monkeypatch.setattr(parent.thread,'join',join)
    try:
        with pytest.raises(SystemExit) as caught:parent.close()
        assert caught.value is sentinel
    finally:release.set();caller.join(3)
    assert failures and not caller.is_alive()


def test_scope_create_promotes_uncertain_cleanup_over_ordinary_primary(tmp_path,monkeypatch):
    from tradingagents.research.onchain_replication import neural_authority as a
    n=module();base=tmp_path/n.PREFIX/'runs/invented';base.mkdir(parents=True)
    (tmp_path/'research_runs').mkdir();(tmp_path/n.PREFIX/'sources').mkdir()
    original=n._write;primary=ValueError('anchor-write-primary');fatal=n.PhysicalCleanupFailure('authority-close-uncertain')
    def write(path,*args,**kwargs):
        if path.name=='physical-anchor.json':raise primary
        return original(path,*args,**kwargs)
    close=a.ParentAuthority.close
    def uncertain(self):close(self);raise fatal
    monkeypatch.setattr(n,'_write',write);monkeypatch.setattr(a.ParentAuthority,'close',uncertain)
    with pytest.raises(n.PhysicalCleanupFailure) as caught:n.Scope.create(tmp_path,'invented','a'*40,limits(),{})
    assert caught.value is fatal and fatal.__cause__ is primary


@pytest.mark.parametrize('fail_final_live',[False,True])
def test_selected_guard_rethrows_local_fatal_after_stop_and_receipts(tmp_path,monkeypatch,fail_final_live):
    from tests.research.onchain_replication.test_resources import mock_unit
    from tradingagents.research.onchain_replication import resources
    from tradingagents.research import lifecycle
    scope,base=fresh(tmp_path);receipt,calls=mock_unit(base,monkeypatch,completed=True)
    sentinel=module().PhysicalCleanupFailure('local physical client close uncertain');original=resources._atomic;once=[]
    def atomic(path,value):
        if value.get('phase')=='running' and not once:once.append(True);raise sentinel
        if fail_final_live and value.get('phase')=='failed':raise OSError('independent final live failure')
        return original(path,value)
    run=resources.subprocess.run
    def dispatch(args,**kwargs):
        result=run(args,**kwargs)
        if args[0]=='systemd-run':
            path=receipt/'cpu_ready.json';v=json.loads(path.read_bytes());v['file_size_limit']=[65536,65536];path.write_text(json.dumps(v))
        return result
    monkeypatch.setattr(resources,'_atomic',atomic);monkeypatch.setattr(resources.subprocess,'run',dispatch)
    with lifecycle.metadata_scope(scope):
        with pytest.raises(module().PhysicalCleanupFailure) as caught:
            resources.guarded_run(['true'],cwd=tmp_path,receipt_dir=receipt,disk_paths=[tmp_path],disk_floor_bytes=1,
                physical_policy=limits(),owner_identity={'experiment':'invented','source_commit':'a'*40})
    assert caught.value is sentinel and any('stop' in call for call in calls)
    assert json.loads((receipt/'final.json').read_bytes())['phase']=='failed'


def test_selected_launcher_reports_nonzero_monitor_even_after_complete_reconciliation(tmp_path,monkeypatch,capsys):
    from types import SimpleNamespace
    from tradingagents.research import lifecycle
    from tradingagents.research.onchain_replication import job
    n=module();(tmp_path/'research_runs').mkdir();(tmp_path/n.PREFIX/'sources').mkdir(parents=True)
    args=SimpleNamespace(root=tmp_path,experiment='invented',source='a'*40,registration='synthetic')
    monkeypatch.setattr(job,'_admitted',lambda a:(None,{'resources':{'physical_policy':limits()}}))
    monkeypatch.setattr(job.signal,'signal',lambda *a:None);retained=[]
    class Monitor:
        def __init__(self,*a,**kw):retained.append(lifecycle.current_metadata_scope())
        def wait(self):return 23
        def poll(self):return 23
    monkeypatch.setattr(job.subprocess,'Popen',Monitor)
    def reconcile(a):
        scope=retained[0];scope.immutable(scope.base/'observer.json',{'status':'complete'});return {'status':'complete'}
    monkeypatch.setattr(job,'reconcile',reconcile)
    assert job.launch(args)==1
    result=json.loads(capsys.readouterr().out)
    assert result['status']=='monitor_failed' and result['monitor_exit_code']==23 and result['reconciled_disposition']['status']=='complete'
    assert json.loads((retained[0].base/'observer.json').read_bytes())['status']=='complete'
    assert json.loads((retained[0].base/'monitor-failed.json').read_bytes())==result
    assert not (retained[0].base/'physical-final.json').exists()
    with pytest.raises(RuntimeError,match='authority'):retained[0].check()


def test_selected_guard_final_directory_close_uncertainty_is_fatal(tmp_path,monkeypatch):
    import os
    from tests.research.onchain_replication.test_resources import mock_unit
    from tradingagents.research.onchain_replication import resources
    from tradingagents.research import lifecycle
    scope,base=fresh(tmp_path);n=module();receipt,calls=mock_unit(base,monkeypatch,completed=True)
    original=resources.subprocess.run;close=n._close;uncertain=[]
    def dispatch(args,**kwargs):
        result=original(args,**kwargs)
        if args[0]=='systemd-run':
            path=receipt/'cpu_ready.json';value=json.loads(path.read_bytes());value['file_size_limit']=[65536,65536];path.write_text(json.dumps(value))
        return result
    # Fault after a real close of the final publication's owned directory fd.
    original_os_close=os.close
    def close_os(fd):
        target=os.readlink('/proc/self/fd/'+str(fd))
        original_os_close(fd)
        if target==str(receipt) and (receipt/'final.json').exists() and not uncertain:
            uncertain.append(fd);raise OSError('actual owned final directory close uncertain')
    monkeypatch.setattr(resources.subprocess,'run',dispatch);monkeypatch.setattr(os,'close',close_os)
    with lifecycle.metadata_scope(scope):
        with pytest.raises(n.PhysicalCleanupFailure):
            resources.guarded_run(['true'],cwd=tmp_path,receipt_dir=receipt,disk_paths=[tmp_path],disk_floor_bytes=1,
                physical_policy=limits(),owner_identity={'experiment':'invented','source_commit':'a'*40})
    assert len(uncertain)==1 and (receipt/'final.json').exists() and any('stop' in call for call in calls)


@pytest.mark.parametrize('cleanup_uncertain',[False,True])
@pytest.mark.parametrize('primary_type',[ValueError,MemoryError])
def test_selected_guard_ordinary_primary_survives_late_cleanup_promotion(tmp_path,monkeypatch,cleanup_uncertain,primary_type):
    import os
    from tests.research.onchain_replication.test_resources import mock_unit
    from tradingagents.research.onchain_replication import resources
    from tradingagents.research import lifecycle
    scope,base=fresh(tmp_path);receipt,calls=mock_unit(base,monkeypatch,completed=True)
    primary=primary_type('original ordinary guard body');atomic=resources._atomic;once=[];closed=[]
    def write(path,value):
        if value.get('phase')=='running' and not once:once.append(True);raise primary
        return atomic(path,value)
    dispatch=resources.subprocess.run
    def run(args,**kwargs):
        result=dispatch(args,**kwargs)
        if args[0]=='systemd-run':
            p=receipt/'cpu_ready.json';v=json.loads(p.read_bytes());v['file_size_limit']=[65536,65536];p.write_text(json.dumps(v))
        return result
    original_close=os.close
    def close(fd):
        path=os.readlink('/proc/self/fd/'+str(fd));original_close(fd)
        if cleanup_uncertain and path==str(receipt) and (receipt/'final.json').exists() and not closed:
            closed.append(fd);raise OSError('one-shot actual owned directory close uncertainty')
    monkeypatch.setattr(resources,'_atomic',write);monkeypatch.setattr(resources.subprocess,'run',run);monkeypatch.setattr(os,'close',close)
    kwargs={'cwd':tmp_path,'receipt_dir':receipt,'disk_paths':[tmp_path],'disk_floor_bytes':1,
            'physical_policy':limits(),'owner_identity':{'experiment':'invented','source_commit':'a'*40}}
    with lifecycle.metadata_scope(scope):
        if primary_type is MemoryError:
            with pytest.raises(MemoryError) as caught:resources.guarded_run(['true'],**kwargs)
            assert caught.value is primary
            if cleanup_uncertain:assert len(closed)==1 and primary.__notes__
        elif cleanup_uncertain:
            with pytest.raises(module().PhysicalCleanupFailure) as caught:resources.guarded_run(['true'],**kwargs)
            assert caught.value.__cause__ is primary and len(closed)==1
        else:
            result=resources.guarded_run(['true'],**kwargs)
            assert result['phase']=='failed' and 'original ordinary guard body' in result['limit_reason']
    assert any('stop' in call for call in calls) and (receipt/'final.json').exists()
