"""Reviewed synthetic inputs; actual admit/hash joins; no numerical execution."""
import ast,copy,dataclasses,json,os,time
from pathlib import Path
import pytest
from tests.research.test_lifecycle import registered,commit
from tradingagents.research.admission import admit
from tradingagents.research.onchain_replication import job,resources as guard,real_pilot_import_caller as caller,real_pilot_storage as storage
from tradingagents.research.onchain_replication.provenance import file_hash
G=1024**3

@pytest.fixture(params=[5*G//2,17*G//2])
def context(registered,request):
 root,spec,_=registered
 (root/'research_runs').mkdir();(root/'research_artifacts').mkdir()
 budget={'schema_version':2,'kind':storage.KIND,'authority_root':str(root),'experiment':storage.EXPERIMENT,'roots':[str(root/'research_artifacts'),str(root/'research_runs'/storage.EXPERIMENT)],'shared_files':[str(root/'research_runs/.lock')],'limits':dict(max_allocated_bytes=G,max_logical_bytes=G,max_entries=10000,max_depth=32,max_scan_seconds=5)}
 p=dict(memory_max_bytes=6*G,memory_high_bytes=5*G,reserve_bytes=5*G//2,start_reserve_bytes=request.param,disk_floor_bytes=10*G,disk_paths=[str(root)],wall_seconds=100,storage_budget=budget,native_unit_limits={'file_size_bytes':4096})
 hashes=[str(i)*64 for i in range(7)]
 plan=dict(schema_version=2,kind=caller.KIND,asset='ETH',seed=11,batch_size=16,lookback_days=28,cell_id='synthetic',graph_inputs=dict(zip(hashes,['g'+str(i) for i in range(7)])),indices=list(range(16)),decisions=[f'2000-01-{i+1:02}' for i in range(16)],graph_sequences=[hashes*4 for _ in range(16)],population_plan_input='population',model_input='model',training_input='training',model_execution=None,max_checkpoint_bytes=4096,outputs=dict(summary='s',ledger='l',binding='b',journal='j'),resource_policy=p)
 execution=dict(schema_version=1,kind='compact_resource',resources=p,environment_input='environment',payload={'representation_jobs':{'synthetic':{'real_pilot_input':'pilot'}}})
 exp=spec['experiments'].pop('example-a');spec['experiments'][storage.EXPERIMENT]=exp
 for name,value in [('execution_job',execution),('pilot',plan)]:
  path=root/(name+'.json');path.write_text(json.dumps(value));exp['inputs'][name]={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}
 source=commit(root,spec)
 ad=admit(root=root,registration='registration.json',experiment=storage.EXPERIMENT,source=source)
 return ad,execution

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


def test_exact_new_and_prior_policies(context):
 ad,e=context
 assert job.resource_policy(e['resources'],ad.root,pilot_context=context)==e['resources']
 caller._finite_resources(e['resources'])

def test_exact_new_and_prior_workers(context,live):
 assert check_live(context,live)==live[1]

@pytest.mark.parametrize('start',[5*G//2-1,3*G,17*G//2-1])
def test_unreviewed_tuple_refused(context,start):
 ad,e=context;e=copy.deepcopy(e);e['resources']['start_reserve_bytes']=start
 with pytest.raises(ValueError):job.resource_policy(e['resources'],ad.root,pilot_context=(ad,e))
 with pytest.raises(ValueError):caller._finite_resources(e['resources'])

@pytest.mark.parametrize('which',['execution_job','pilot'])
def test_changed_authentication_refused(context,which):
 ad,e=context;(ad.root/(which+'.json')).write_text('{}')
 with pytest.raises(ValueError):job.resource_policy(e['resources'],ad.root,pilot_context=context)

def test_missing_context_refused(context,live):
 ad,e=context
 with pytest.raises(ValueError):job.resource_policy(e['resources'],ad.root)
 with pytest.raises(RuntimeError):check_live(context,live,False)

def test_legacy_job_floor_preserved(tmp_path):
 p=dict(memory_max_bytes=6*G,memory_high_bytes=5*G,reserve_bytes=3*G,start_reserve_bytes=9*G,disk_floor_bytes=10*G,disk_paths=[str(tmp_path)],wall_seconds=28800)
 assert job.resource_policy(p,tmp_path)==p
 p['start_reserve_bytes']=3*G
 with pytest.raises(ValueError):job.resource_policy(p,tmp_path)

def test_legacy_worker_floor_preserved(tmp_path,monkeypatch):
 from tests.research.onchain_replication.test_resources import test_worker_rejects_different_or_unbounded_effective_cap
 test_worker_rejects_different_or_unbounded_effective_cap(tmp_path,monkeypatch)

@pytest.mark.parametrize('explicit',[True,False])
def test_explicit_floor_and_unchanged_default(tmp_path,monkeypatch,explicit):
 from tests.research.onchain_replication.test_resources import mock_unit
 startup=5*G//2 if explicit else 17*G//2
 receipt,calls=mock_unit(tmp_path,monkeypatch,memory=[startup]*10,completed=True)
 options={'start_reserve_bytes':startup} if explicit else {}
 result=guard.guarded_run(['true'],cwd=tmp_path,receipt_dir=receipt,reserve_bytes=5*G//2,disk_floor_bytes=10*G,**options)
 assert result['phase']=='complete' and result['start_reserve_bytes']==startup
 for p in ('MemoryMax=6442450944','MemoryHigh=5368709120','MemorySwapMax=0','CPUQuota=200%'):
  assert '--property='+p in calls[0]
 assert result['reserve_bytes']==5*G//2 and result['disk_floor_bytes']==10*G and len(result['cpus'])<=2

def test_explicit_below_runtime_reserve_refused_before_receipt(tmp_path):
 with pytest.raises(ValueError):guard.guarded_run(['true'],cwd=tmp_path,receipt_dir=tmp_path/'r',reserve_bytes=5*G//2,start_reserve_bytes=5*G//2-1)
 assert not (tmp_path/'r').exists()

@pytest.mark.parametrize('boundary',['entry','setup','runtime'])
def test_pressure_at_all_original_boundaries_still_refuses(tmp_path,monkeypatch,boundary):
 from tests.research.onchain_replication.test_resources import mock_unit
 reserve=5*G//2
 samples={'entry':[reserve-1],'setup':[reserve,reserve-1],'runtime':[reserve,reserve,reserve-1]}[boundary]
 receipt,calls=mock_unit(tmp_path,monkeypatch,memory=samples)
 # The generic fixture assumes a runtime observation before cleanup.
 # Setup refusal reaches stop one observation earlier; model its real effect.
 original_properties=guard._properties
 def properties(unit):
  if any('stop' in c for c in calls):return {'ControlGroup':'/user.slice/synthetic.service','ActiveState':'inactive','Result':'success'}
  return original_properties(unit)
 monkeypatch.setattr(guard,'_properties',properties)
 result=guard.guarded_run(['true'],cwd=tmp_path,receipt_dir=receipt,reserve_bytes=reserve,start_reserve_bytes=reserve,disk_floor_bytes=10*G,wait_seconds=0)
 assert result['phase']=='failed'
 expected={'entry':'host startup memory reserve unavailable','setup':'host reserve fell during cgroup setup','runtime':'host runtime memory reserve breached'}[boundary]
 assert expected in result['limit_reason']
 if boundary=='entry':assert not calls
 else:assert result['cleanup_verified'] and any('stop' in c for c in calls)
 assert (receipt/'release.json').exists()==(boundary=='runtime')
