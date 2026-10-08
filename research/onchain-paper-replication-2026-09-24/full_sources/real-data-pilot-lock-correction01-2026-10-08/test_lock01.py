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


import multiprocessing,sys
from types import SimpleNamespace
from tradingagents.research.lifecycle import ResearchRun,_lock
H=Path(__file__).resolve().parent

def extracted():
 # Compile the exact actual function plus both actual calls in bind's lock.
 # The numeric module imports are omitted, never stubbed or executed.
 source=Path(os.environ['OWNER_SOURCE'])
 tree=ast.parse(source.read_text(),filename=str(source))
 guard=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_guard')
 bind=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bind')
 locked=next(n for n in ast.walk(bind) if isinstance(n,ast.With) and isinstance(n.items[0].context_expr,ast.Call) and getattr(n.items[0].context_expr.func,'id',None)=='_lock')
 calls=[n for n in locked.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id',None)=='_guard']
 assert len(calls)==2
 wrapper=ast.parse('def locked_checks(run,policy_resources,guard_owner,base,execution):\n with _lock(run.admission.root):\n  pass\n').body[0]
 wrapper.body[0].body=calls
 from tradingagents.research.onchain_replication.provenance import canonical_bytes
 def require(condition,message):
  if not condition:raise ValueError(message)
 ns=dict(json=json,SimpleNamespace=SimpleNamespace,resources=globals()['guard'],job=job,Path=Path,_lock=_lock,require=require,equal=lambda a,b:canonical_bytes(a)==canonical_bytes(b))
 exec(compile(ast.fix_missing_locations(ast.Module(body=[guard,wrapper],type_ignores=[])),str(source),'exec'),ns)
 return ns

def setup_run(context,live):
 ad,e=context;r,value=live
 run=ResearchRun.start(root=ad.root,registration=ad.registration,experiment=ad.experiment_id,source=ad.source)
 execution=json.loads(run.read_input('execution_job'))
 ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]
 owner=dict(experiment=ad.experiment_id,source_commit=ad.source,monitor_pid=os.getpid(),monitor_start_ticks=ticks)
 value['owner_identity']=owner;value['monitor_pid']=owner['monitor_pid']
 value['command']=job._command(SimpleNamespace(root=ad.root,registration=ad.registration,experiment=ad.experiment_id,source=ad.source),'worker')
 (r/'live.json').write_text(json.dumps(value))
 return run,execution,owner

def test_both_locked_checks_finish(context,live):
 run,e,owner=setup_run(context,live);ns=extracted()
 def child():
  print('enter exact two guard calls under real lifecycle flock',flush=True)
  ns['locked_checks'](run,e['resources'],owner,run.admission.root,e)
  print('both authenticated guard checks returned',flush=True)
 process=multiprocessing.get_context('fork').Process(target=child);process.start();process.join(2)
 if process.is_alive():
  proc=Path('/proc')/str(process.pid)
  print('DEADLOCK wchan='+ (proc/'wchan').read_text(),flush=True)
  for p in (proc/'fdinfo').iterdir():
   text=p.read_text()
   if 'lock:' in text:print(text,flush=True)
  process.terminate();process.join(2)
  assert not process.is_alive()
  pytest.fail('bounded synthetic subprocess did not return: lifecycle self-deadlock')
 assert process.exitcode==0

def test_default_low_reserve_context_remains_authenticated(context,live):
 run,e,owner=setup_run(context,live)
 extracted()['_guard'](run,e['resources'],owner,run.admission.root)

@pytest.mark.parametrize('mutation',['missing','mismatch','changed_hash','not_ready'])
def test_authentication_refusals(context,live,mutation):
 run,e,owner=setup_run(context,live);ns=extracted()
 if mutation=='missing':
  with pytest.raises(ValueError):job.resource_policy(e['resources'],run.admission.root)
  return
 if mutation=='mismatch':e=copy.deepcopy(e);e['kind']='fit'
 elif mutation=='changed_hash':(run.admission.root/'execution_job.json').write_text('{}')
 else:run.admission=dataclasses.replace(run.admission,ready=False)
 with _lock(run.admission.root),pytest.raises(ValueError):
  ns['_guard'](run,e['resources'],owner,run.admission.root,execution=e)

def test_legacy_three_gib_never_reads_execution(context,live):
 run,e,owner=setup_run(context,live);p=copy.deepcopy(e['resources']);p.update(reserve_bytes=3*G,start_reserve_bytes=9*G)
 r,value=live;value.update(p);(r/'live.json').write_text(json.dumps(value))
 with _lock(run.admission.root):extracted()['_guard'](run,p,owner,run.admission.root)
