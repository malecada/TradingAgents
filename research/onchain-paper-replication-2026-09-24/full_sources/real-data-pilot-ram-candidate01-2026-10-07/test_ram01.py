"""Reviewed synthetic inputs; actual admit/hash joins; no numerical execution."""
import ast,copy,dataclasses,json,os,time
from pathlib import Path
import pytest
from tests.research.test_lifecycle import registered,commit
from tradingagents.research.admission import admit
from tradingagents.research.onchain_replication import job,resources as guard,real_pilot_import_caller as caller,real_pilot_storage as storage
from tradingagents.research.onchain_replication.provenance import file_hash
G=1024**3

@pytest.fixture
def context(registered):
 root,spec,_=registered
 (root/'research_runs').mkdir();(root/'research_artifacts').mkdir()
 budget={'schema_version':2,'kind':storage.KIND,'authority_root':str(root),'experiment':storage.EXPERIMENT,'roots':[str(root/'research_artifacts'),str(root/'research_runs'/storage.EXPERIMENT)],'shared_files':[str(root/'research_runs/.lock')],'limits':dict(max_allocated_bytes=G,max_logical_bytes=G,max_entries=10000,max_depth=32,max_scan_seconds=5)}
 p=dict(memory_max_bytes=6*G,memory_high_bytes=5*G,reserve_bytes=5*G//2,start_reserve_bytes=17*G//2,disk_floor_bytes=10*G,disk_paths=[str(root)],wall_seconds=100,storage_budget=budget,native_unit_limits={'file_size_bytes':4096})
 hashes=[str(i)*64 for i in range(7)]
 plan=dict(schema_version=2,kind=caller.KIND,asset='ETH',seed=11,batch_size=16,lookback_days=28,cell_id='synthetic',graph_inputs=dict(zip(hashes,['g'+str(i) for i in range(7)])),indices=list(range(16)),decisions=[f'2000-01-{i+1:02}' for i in range(16)],graph_sequences=[hashes*4 for _ in range(16)],population_plan_input='population',model_input='model',training_input='training',model_execution=None,max_checkpoint_bytes=4096,outputs=dict(summary='s',ledger='l',binding='b',journal='j'),resource_policy=p)
 execution=dict(schema_version=1,kind='compact_resource',resources=p,environment_input='environment',payload={'representation_jobs':{'synthetic':{'real_pilot_input':'pilot'}}})
 exp=spec['experiments'].pop('example-a');spec['experiments'][storage.EXPERIMENT]=exp
 for name,value in [('execution_job',execution),('pilot',plan)]:
  path=root/(name+'.json');path.write_text(json.dumps(value));exp['inputs'][name]={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}
 source=commit(root,spec)
 ad=admit(root=root,registration='registration.json',experiment=storage.EXPERIMENT,source=source)
 return ad,execution

def test_authenticated_amendment(context):
 ad,e=context
 assert job.resource_policy(e['resources'],ad.root,pilot_context=context)==e['resources']
 caller._finite_resources(e['resources'])

@pytest.mark.parametrize('field,value',[('reserve_bytes',5*G//2-1),('start_reserve_bytes',17*G//2-1),('memory_max_bytes',5*G),('memory_high_bytes',4*G),('disk_floor_bytes',9*G)])
def test_no_other_relaxation(context,field,value):
 ad,e=context;e=copy.deepcopy(e);e['resources'][field]=value
 with pytest.raises(ValueError):job.resource_policy(e['resources'],ad.root,pilot_context=(ad,e))

def test_missing_context_and_legacy_refused(context):
 ad,e=context;p=copy.deepcopy(e['resources'])
 with pytest.raises(ValueError):job.resource_policy(p,ad.root)
 p.pop('storage_budget');p.pop('native_unit_limits')
 with pytest.raises(ValueError):job.resource_policy(p,ad.root,pilot_context=context)
 p.update(reserve_bytes=3*G,start_reserve_bytes=9*G)
 assert job.resource_policy(p,ad.root)==p

@pytest.mark.parametrize('change',['job_hash','plan_hash','plan_policy','not_ready','wrong_id','wrong_job_kind'])
def test_authentication_refusals(context,change):
 ad,e=context
 if change in ('job_hash','plan_hash'):
  (ad.root/ad.inputs['execution_job' if change=='job_hash' else 'pilot']['path']).write_text('{}')
 elif change=='plan_policy':
  plan=json.loads((ad.root/'pilot.json').read_text());plan['resource_policy']['reserve_bytes']=3*G;plan['resource_policy']['start_reserve_bytes']=9*G
  (ad.root/'pilot.json').write_text(json.dumps(plan));inputs=copy.deepcopy(ad.inputs);inputs['pilot']['sha256']=file_hash(ad.root/'pilot.json');ad=dataclasses.replace(ad,inputs=inputs)
 elif change=='not_ready':ad=dataclasses.replace(ad,ready=False)
 elif change=='wrong_id':ad=dataclasses.replace(ad,experiment_id='unrelated')
 else:e=copy.deepcopy(e);e['kind']='fit'
 with pytest.raises(ValueError):job.resource_policy(e['resources'],ad.root,pilot_context=(ad,e))

@pytest.fixture
def live(context,monkeypatch):
 ad,e=context;r=ad.root/'guard';r.mkdir();cg=ad.root/'cg';cg.mkdir()
 p=e['resources'];value={**copy.deepcopy(p),'command':['true'],'phase':'running','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'monotonic_seconds':time.monotonic(),'lease_seconds':15,'cgroup':str(cg),'cpus':list(os.sched_getaffinity(0)),'memory_swap_max_bytes':0,'owner_identity':{'experiment':ad.experiment_id,'source_commit':ad.source}}
 (r/'release.json').write_text('{"kernel_controls_verified":true}')
 monkeypatch.setattr(guard,'_own_cgroup',lambda:cg);monkeypatch.setattr(guard,'verify_cpu_tree',lambda *args:None)
 monkeypatch.setattr(guard,'_read_controls',lambda _:{'memory.max':str(6*G),'memory.high':str(5*G),'memory.swap.max':'0'})
 import resource
 monkeypatch.setattr(resource,'getrlimit',lambda _: (4096,4096))
 for k,v in guard._native_owned_env(ad.root,p['storage_budget']).items():monkeypatch.setenv(k,v)
 monkeypatch.chdir(ad.root)
 return r,value

def check_live(context,live,with_context=True):
 ad,e=context;r,value=live;(r/'live.json').write_text(json.dumps(value))
 return guard.assert_guarded_worker(r,['true'],required_paths=[ad.root],wall_seconds=100,disk_floor_bytes=10*G,**({'pilot_context':context} if with_context else {}))

def test_worker_amendment(context,live):assert check_live(context,live)==live[1]

def test_worker_default_refuses(context,live):
 with pytest.raises(RuntimeError):check_live(context,live,False)

@pytest.mark.parametrize('field,value',[('memory_swap_max_bytes',1),('start_reserve_bytes',17*G//2-1),('reserve_bytes',2*G),('disk_floor_bytes',9*G),('owner_identity',{'experiment':'other','source_commit':'0'*40})])
def test_worker_mismatch(context,live,field,value):
 live[1][field]=value
 with pytest.raises((RuntimeError,ValueError)):check_live(context,live)

def test_consumer_wiring():
 for module,function in [('job','worker'),('real_pilot_import_caller','execute'),('matching_owner','_guard')]:
  path=Path(__file__).parent/(module+'.py')
  if os.environ.get('RAM_BASELINE')=='1':path=path.parent/'baseline'/path.name
  tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function]
  calls=[n for f in nodes for n in ast.walk(f) if isinstance(n,ast.Call) and (getattr(n.func,'attr',None)=='assert_guarded_worker' or getattr(n.func,'id',None)=='assert_guarded_worker')]
  assert calls and all('pilot_context' in {k.arg for k in call.keywords} for call in calls),(module,function)


def test_amended_runtime_pressure_still_terminates(tmp_path,monkeypatch):
 from tests.research.onchain_replication.test_resources import mock_unit
 receipt,calls=mock_unit(tmp_path,monkeypatch,memory=[9*G,9*G,2*G])
 result=guard.guarded_run(['true'],cwd=tmp_path,receipt_dir=receipt,reserve_bytes=5*G//2,start_reserve_bytes=17*G//2,disk_floor_bytes=10*G)
 assert result['phase']=='failed' and 'host runtime memory reserve breached' in result['limit_reason']
 assert result['cleanup_verified'] and any('stop' in call for call in calls)
 assert '--property=MemoryMax=6442450944' in calls[0]
 assert '--property=MemoryHigh=5368709120' in calls[0]
 assert '--property=MemorySwapMax=0' in calls[0]

@pytest.mark.parametrize('available,accepted',[(17*G//2-1,False),(17*G//2,True)])
def test_amended_startup_boundary(tmp_path,monkeypatch,available,accepted):
 from tests.research.onchain_replication.test_resources import mock_unit
 receipt,calls=mock_unit(tmp_path,monkeypatch,memory=[available]*20,completed=True)
 result=guard.guarded_run(['true'],cwd=tmp_path,receipt_dir=receipt,reserve_bytes=5*G//2,start_reserve_bytes=17*G//2,disk_floor_bytes=10*G,wait_seconds=0)
 assert (result['phase']=='complete') is accepted
 if not accepted:
  assert not calls and 'startup memory reserve' in result['limit_reason']

def test_legacy_policy_does_not_import_pilot(tmp_path,monkeypatch):
 import builtins
 original=builtins.__import__
 def checked(name,*args,**kwargs):
  assert name!='real_pilot_import_caller','ordinary policy added pilot import'
  return original(name,*args,**kwargs)
 monkeypatch.setattr(builtins,'__import__',checked)
 p=dict(memory_max_bytes=6*G,memory_high_bytes=5*G,reserve_bytes=3*G,start_reserve_bytes=9*G,disk_floor_bytes=10*G,disk_paths=[str(tmp_path)],wall_seconds=100)
 assert job.resource_policy(p,tmp_path)==p
