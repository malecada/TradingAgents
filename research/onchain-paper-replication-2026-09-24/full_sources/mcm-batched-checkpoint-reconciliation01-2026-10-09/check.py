"""Source control-flow doubles and exact finite checkpoint metadata arithmetic."""
import ast,copy,hashlib,json,math,os,types
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication';gate=P.parent/'real-data-pilot-final23-2026-10-09/gate03.json';g=json.loads(gate.read_text());key=list(g['experiments'])[-1];e=g['experiments'][key];pins={str(gate):hashlib.sha256(gate.read_bytes()).hexdigest()}
policies={}
for role in ('compact_policy','pair_policy'):
 ref=e['inputs'][role];path=R/ref['path'];h=hashlib.sha256(path.read_bytes()).hexdigest();assert h==ref['sha256'];pins[str(path)]=h;policies[role]=json.loads(path.read_text())
p=policies['pair_policy']['limits'];s=policies['compact_policy']['stage_policy']['schedule'];assert policies['compact_policy']['stage_policy']['pair']==p
assert (s['max_checkpoints'],p['max_publications'],s['calls_per_checkpoint'],s['operations_per_call'])==(1,1,10000,1000000)
assert (p['max_checkpoint_bytes'],p['checkpoint_layout']['chunk_entries'],s['max_total_checkpoints'],s['max_total_checkpoint_bytes'])==(269097984,262144,160,43058298880)
source=S/'batched_pair_executor.py';tree=ast.parse(source.read_text());code=ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef)],type_ignores=[]);checks=[]
for case in ('done','stop','callback_failure','cleanup_failure'):
 trace=[];primary=RuntimeError('checkpoint write failure');cleanup=OSError('session cleanup failure')
 def create(*args,**kwargs):trace.append('create');return {'phase':'done' if case=='done' else 'annealing'}
 def close(state):trace.append('engine_close')
 class Session:
  def __init__(self,*args,**kwargs):trace.append('session')
  def advance(self,state,*,max_operations):assert max_operations==1000000;trace.append('advance')
  def close(self):
   trace.append('session_close')
   if case=='cleanup_failure':raise cleanup
 def checkpoint(*args):
  trace.append('checkpoint')
  if case=='callback_failure':raise primary
 ns={'copy':copy,'engine':types.SimpleNamespace(create=create,close=close,score_only=lambda *args,**kwargs:types.SimpleNamespace(score=.5,iterations=1,convergence='iteration_cap')),'pair':types.SimpleNamespace(hash_string=lambda s:None,policy_check=lambda *args,**kwargs:None,ENGINE_FIELDS=(),LIMIT=8192),'annealing':object(),'ImmutablePairSession':Session}
 exec(compile(code,str(source),'exec'),ns);x=ns['PairExecutor']({},p,s,checkpoint);observed=None
 try:
  for _ in range(2):x(None,None,'a'*64)
 except BaseException as error:observed=error
 if case=='done':assert observed is None and trace.count('create')==2 and trace.count('checkpoint')==0
 else:
  assert trace.count('create')==1 and trace.count('advance')==10000 and trace.count('checkpoint')==1 and trace.count('session_close')==trace.count('engine_close')==1 and x.poisoned
  if case=='callback_failure':assert observed is primary
  else:assert isinstance(observed,ns['CheckpointStop'])
  if case=='cleanup_failure':assert observed.__notes__
  try:x(None,None,'b'*64)
  except ValueError:pass
  else:raise AssertionError('poisoned executor reused')
 checks.append({'case':case,'creates':trace.count('create'),'advances':trace.count('advance'),'callbacks':trace.count('checkpoint'),'session_closes':trace.count('session_close'),'engine_closes':trace.count('engine_close'),'observed':None if observed is None else type(observed).__name__})
# Actual describe/layout arithmetic extracted without NumPy or any numerical arrays.
t=ast.parse((S/'checkpoint_chunks.py').read_text());ns={'math':math,'FORMAT':'sharded-npy-v1','MAX_ENTRIES':262144,'MAX_CHUNKS':256}
exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('need','layout','describe','io_scratch_bytes')],type_ignores=[]),str(S/'checkpoint_chunks.py'),'exec'),ns)
N=p['max_pair_entries_override'];layout=p['checkpoint_layout'];desc=ns['describe']([N],'<f8',layout,'M');A=desc['bytes'];K=len(desc['chunks']);maximum=p['max_checkpoint_bytes'];L=65536;block=4096
assert 4*A+3*L==maximum
nextdesc=ns['describe']([N+1],'<f8',layout,'M');assert 4*nextdesc['bytes']+3*L>maximum
roundup=lambda n:((n+block-1)//block)*block
allocated_arrays=4*sum(roundup(v['bytes']) for v in desc['chunks']);files=4*K+3+1
bound={'max_pair_entries':N,'chunks_per_array':K,'chunk_max_file_bytes':8*layout['chunk_entries']+128,'array_with_headers_bytes':A,'snapshot_body_bound':4*A+3*L,'callback_sidecar_bound':8192,'snapshot_plus_sidecar_bound':maximum+8192,'snapshot_files_including_sidecar':files,'snapshot_directories':3,'parent_checkpoint_directory_count_separate':7,'conditional4096B_allocated_snapshot_files':allocated_arrays+3*roundup(L)+roundup(8192),'conditional4096B_snapshot_files_plus3dirs':allocated_arrays+3*roundup(L)+roundup(8192)+3*block,'additional_producer_failed_json_bound':8192,'original_pair_logical_total_checkpoint_bytes':p['total_checkpoint_bytes'],'original_global_cumulative_checkpoint_bytes':s['max_total_checkpoint_bytes'],'original_global_max_checkpoints':s['max_total_checkpoints'],'callback_reservation_per_attempt':maximum+2*8192,'io_scratch_memory_only_bytes':ns['io_scratch_bytes'](layout),'training_checkpoint_separate_body_bytes':4*1024**2,'checkpoint_plus_training_conservative_allocation':allocated_arrays+3*roundup(L)+roundup(8192)+3*block+8192+4*1024**2,'snapshot_disk_staging_extra_bytes':0,'partial_failure_bound':'prefix of the same exclusive files; no second snapshot after first callback or callback failure'}
for name in ('batched_pair_executor.py','batched_numeric_reuse.py','batched_numeric_execution.py','batched_journal.py','batched_driver.py','compact_mcm_batched.py','real_pilot_import_caller.py','matching_checkpoint.py','checkpoint_chunks.py','matching_annealing.py','matching_hardening.py','real_pilot_training.py'):
 pins[str(S/name)]=hashlib.sha256((S/name).read_bytes()).hexdigest()
assert 'numpy' not in __import__('sys').modules
result={'status':'PASS_SOURCE_CONDITIONAL_ONE_ATTEMPT_BOUND','gate_experiment':key,'schedule':s,'checks':checks,'bounds':bound,'affinity':sorted(os.sched_getaffinity(0)),'no_numerical_arrays_or_authority':True,'source_pins':pins}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':checks,'bounds':bound}))
