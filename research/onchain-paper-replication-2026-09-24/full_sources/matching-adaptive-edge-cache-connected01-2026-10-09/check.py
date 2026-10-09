import os,resource,signal,sys,time,json,ast,types,importlib,hashlib,struct,copy
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];S=R/'tradingagents/research/onchain_replication';sys.path.insert(0,str(R))
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(r,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'wall':signal.getitimer(signal.ITIMER_REAL),'threads':{k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}}
assert limits['affinity']==[3] and limits['nice']==10
(D/'LIMITER01.json').write_text(json.dumps(limits,indent=2)+'\n');started=time.perf_counter()
import numpy as np
from tradingagents.research.onchain_replication import batched_numeric_execution as original,compact_policy,matching_pair
from tradingagents.research.onchain_replication.contracts import AttributedGraph
base='tradingagents.research.onchain_replication';package=base+'.adaptive_connected_fixture';pkg=types.ModuleType(package);pkg.__path__=[str(D),str(S)];sys.modules[package]=pkg
for name in ('contracts','checkpoint_chunks','matching_identity','matching_hardening','matching_sparse'):sys.modules[package+'.'+name]=importlib.import_module(base+'.'+name)
new=importlib.import_module(package+'.batched_numeric_execution');helper=importlib.import_module(package+'.adaptive_edge_policy');engine=new.reuse.engine;ann=engine.ann
selection=dict(ann.ADAPTIVE_EDGE_POLICY)
for name,changes in json.loads((D/'CHANGES01.json').read_text()).items():
 text=(D/name).read_text()
 for a,b in reversed(changes):assert text.count(b)==1;text=text.replace(b,a)
 assert text==(S/name).read_text();assert ast.dump(ast.parse(text))==ast.dump(ast.parse((S/name).read_text()))
assert (D/'matching_annealing.py').read_bytes()==(D.parent/'matching-adaptive-edge-cache01-2026-10-09/matching_annealing.py').read_bytes()
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text());stage=json.loads((D.parent/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json').read_text())['stage_policy'];c=compact_policy.effective_matching(c,stage['pair']);p=compact_policy.pair_policy(stage['pair']);schedule=stage['schedule'];assert schedule['operations_per_call']==1000000

def graph(n,edges):
 e=np.array([(i,j) for i in range(n) for j in range(n)][:edges],dtype=np.int64).T.copy();return AttributedGraph(tuple(str(i) for i in range(n)),np.arange(n,dtype=np.float64).reshape(-1,1)*.01,e,np.arange(edges,dtype=np.float64).reshape(-1,1)*.002,'a'*64,'0')
a,b=graph(8,64),graph(16,128);assert ann._immutable_edges(a) and ann._immutable_edges(b) and ann._reuse_runtime()
checks=['all six changed modules literal/AST inverse and byte-identical reviewed annealing dependency'];results={};traces={};bindings={}
def checkpoint(*args):raise AssertionError('unexpected full-budget checkpoint')
for name,module,option in [('original',original,'omit'),('none',new,None),('false',new,False),('selected',new,selection)]:
 root=D/name;root.mkdir();trace=[];options={} if option=='omit' else {'edge_cache_policy':option}
 ex=module.NumericExecution(root,c,p,schedule,checkpoint,cells=2,batch_cells=2,max_origin_bytes=18,max_summary_bytes=8192,max_entries=8,max_retained_bytes=262144,max_key_bytes=131072,authority_poll=lambda:trace.append('poll'),**options)
 try:
  if name=='selected':
   # Caller alias mutation cannot alter any retained selection.
   option['chunk_entries']=1
   assert dict(ex._edge_cache_policy)['chunk_entries']==256 and ex._edge_cache_policy==ex.memo._edge_cache_policy==ex.memo.executor._edge_cache_policy
  out=[]
  for i in range(2):
   result=ex(a,b,hashlib.sha256(str(i).encode()).hexdigest());out.append((struct.pack('>d',result[0]).hex(),result[1],result[2]))
  binding=ex.finish();module.verify(root,binding);original.verify(root,binding);bindings[name]=binding;results[name]=out;traces[name]=trace
  assert ex.memo.computed==1 and ex.memo.reused==1
  if name=='selected':assert dict(ex._edge_cache_policy)==binding['edge_cache_policy'] and json.loads((root/'numeric-batches/000000000000.json').read_text())['edge_cache_policy']==binding['edge_cache_policy']
  else:assert 'edge_cache_policy' not in binding and 'edge_cache_policy' not in json.loads((root/'numeric-batches/000000000000.json').read_text())
 finally:ex.close()
assert len({repr(v) for v in results.values()})==1 and len({repr(v) for v in traces.values()})==1
checks.append('actual NumericExecution→memo→PairExecutor→session→engine→annealing >4096 route,1M budget, computed/reused scorebits and authority callback trace/default schema equal')
selection=dict(ann.ADAPTIVE_EDGE_POLICY)
# Actual selected session state and original composite checkpoint compatibility.
Session=new.reuse.immutable_session.ImmutablePairSession;state=engine.create(a,b,c,**{k:p[k] for k in matching_pair.ENGINE_FIELDS});session=Session(a,b,c,engine=engine,annealing=ann,edge_cache_policy=selection)
try:
 used=session.advance(state,max_operations=1000000);assert used==393584 and state['phase']=='hardening'
 path=D/'checkpoint';pin=engine.save(state,path,a,b,c,max_checkpoint_bytes=p['max_checkpoint_bytes'],checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':262144})
 old_engine=original.reuse.engine;restored=old_engine.load(path,a,b,c,expected_sha256=pin,**{k:p[k] for k in matching_pair.ENGINE_FIELDS},checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':262144})
 try:
  assert restored['phase']==state['phase']
  for key in ('V','M','Q'):assert restored['annealing'][key].tobytes()==state['annealing'][key].tobytes()
 finally:old_engine.close(restored)
 session._edge_cache_policy=None
 try:session.advance(state,max_operations=1000000)
 except ValueError as error:assert 'selection changed' in str(error)
 else:raise AssertionError('session mutation accepted')
finally:session.close();engine.close(state)
checks.append('selected original hardening checkpoint saved/loaded and session policy replacement refusal')
# Concrete adapter schema AST, no genuine Owner fabricated.
t=ast.parse((D/'compact_mcm_batched.py').read_text());ns={'require':lambda ok,m:None if ok else (_ for _ in ()).throw(ValueError(m)),'adaptive_edge_policy':helper,'FORMAT':'ordered-mcm-batch-closure-v2'};exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in ('selected','validate')],type_ignores=[]),'actual_adapter_validator','exec'),ns)
bounds={'format':ns['FORMAT'],'authority_boundaries':'entry-batch-checkpoint-final','batch_cells':2,'max_journal_bytes':10000,'max_body_bytes':1024,'max_closure_token_bytes':336,'max_checkpoint_bytes':1,'retention':'local-v2','max_spool_bytes':16,'max_offload_metadata_bytes':1,'max_offload_entries':1,'max_offload_anchor_bytes':0,'execution':{'route':'immutable-input-session+exact-byte-reuse-v1','max_entries':8,'max_retained_bytes':262144,'max_key_bytes':131072,'max_origin_bytes':36,'max_summary_bytes':8192,'edge_cache_policy':selection}}
policy={'schema_version':5,'max_entries':1,'max_workflow_metadata_bytes':1,'numeric':{},'batched':bounds};assert ns['validate'](policy,4) is bounds
for bad in (False,True,dict(selection,chunk_entries=512)):
 q=copy.deepcopy(policy);q['batched']['execution']['edge_cache_policy']=bad
 try:ns['validate'](q,4)
 except ValueError:pass
 else:raise AssertionError('bad selected policy admitted')
checks.append('actual compact selected policy schema validates exact fixed policy and rejects altered/default-valued explicit selection')
# Refuse policy drift at top/memo/PairExecutor chain before new numerical work.
for level in ('top','memo','executor'):
 root=D/('mutation_'+level);root.mkdir();ex=new.NumericExecution(root,c,p,schedule,checkpoint,cells=1,batch_cells=1,max_origin_bytes=9,max_summary_bytes=8192,max_entries=8,max_retained_bytes=262144,max_key_bytes=131072,edge_cache_policy=selection)
 try:
  obj={'top':ex,'memo':ex.memo,'executor':ex.memo.executor}[level];obj._edge_cache_policy=None
  try:ex(a,b,hashlib.sha256(b'mutation').hexdigest())
  except ValueError:pass
  else:raise AssertionError('policy drift accepted')
  assert ex.poisoned and not list((root/'numeric-batches').iterdir())
 finally:ex.close()
checks.append('top/memo/executor policy identity mutation poisons without summary credit')
(D/'RESULT01.json').write_text(json.dumps({'status':'PASS_SYNTHETIC_CONNECTED_NO_AUTHORITY','checks':checks,'scores':results,'callback_counts':{k:len(v) for k,v in traces.items()},'checkpoint_sha256':pin,'selected_summary_bytes':bindings['selected']['summary_bytes'],'limits':limits,'elapsed_seconds':time.perf_counter()-started,'qualification':'Temporary normal relative-import package with unchanged dependency module aliases. No installed/global production function monkeypatch. No Owner or empirical authority.'},indent=2)+'\n');print('PASS',len(checks),time.perf_counter()-started)
