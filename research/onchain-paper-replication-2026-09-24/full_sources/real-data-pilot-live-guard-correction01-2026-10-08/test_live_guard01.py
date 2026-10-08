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



from types import SimpleNamespace

def extract_guard():
 source=Path(os.environ['OWNER_SOURCE']);tree=ast.parse(source.read_text())
 node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_guard')
 from tradingagents.research.onchain_replication.provenance import canonical_bytes
 def require(condition,message):
  if not condition:raise ValueError(message)
 ns=dict(__name__='tradingagents.research.onchain_replication.matching_owner',__package__='tradingagents.research.onchain_replication',json=json,SimpleNamespace=SimpleNamespace,resources=guard,job=job,Path=Path,require=require,equal=lambda a,b:canonical_bytes(a)==canonical_bytes(b))
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
 return ns['_guard']

@pytest.fixture
def guard_call(context,live):
 ad,e=context;r,value=live
 def forbidden_read(name):
  raise AssertionError('live guard invoked ResearchRun.read_input/full admission validation')
 run=SimpleNamespace(admission=ad,read_input=forbidden_read)
 ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]
 owner=dict(experiment=ad.experiment_id,source_commit=ad.source,monitor_pid=os.getpid(),monitor_start_ticks=ticks)
 value.update(owner_identity=owner,monitor_pid=owner['monitor_pid'],command=job._command(SimpleNamespace(root=ad.root,registration=ad.registration,experiment=ad.experiment_id,source=ad.source),'worker'))
 (r/'live.json').write_text(json.dumps(value))
 def call(**kwargs):return extract_guard()(run,e['resources'],owner,ad.root,**kwargs)
 return call

def test_fallback_uses_bounded_fresh_hash_read(guard_call):
 guard_call()

@pytest.mark.parametrize('mutation',['bytes','missing_input','wrong_hash','missing_file','oversize'])
def test_fallback_refuses_invalid_registered_bytes(context,guard_call,mutation):
 ad,e=context;path=ad.root/'execution_job.json'
 if mutation=='bytes':path.write_text('{}')
 elif mutation=='missing_input':del ad.inputs['execution_job']
 elif mutation=='wrong_hash':ad.inputs['execution_job']['sha256']='0'*64
 elif mutation=='missing_file':path.unlink()
 else:path.write_bytes(b' '* (caller.FILE_MAX+1))
 with pytest.raises((ValueError,KeyError,FileNotFoundError)):guard_call()

def test_explicit_context_remains_authenticated(context,guard_call):
 ad,e=context;guard_call(execution=e)
 (ad.root/'execution_job.json').write_text('{}')
 with pytest.raises(ValueError):guard_call(execution=e)

def test_legacy_three_gib_does_not_read_pilot(context,live,guard_call):
 ad,e=context;r,value=live;e['resources'].update(reserve_bytes=3*G,start_reserve_bytes=9*G)
 value.update(e['resources']);(r/'live.json').write_text(json.dumps(value))
 (ad.root/'execution_job.json').unlink()
 guard_call()
