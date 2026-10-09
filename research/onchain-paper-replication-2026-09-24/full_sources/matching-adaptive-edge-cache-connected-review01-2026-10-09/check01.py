import os,resource,signal,sys,types,importlib,json,hashlib,copy,struct,ast
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];C=D.parent/'matching-adaptive-edge-cache-connected01-2026-10-09';S=R/'tradingagents/research/onchain_replication'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(k,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'wall':signal.getitimer(signal.ITIMER_REAL),'threads':{k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}}
(D/'LIMITER01.json').write_text(json.dumps(limits,indent=2)+'\n');sys.path.insert(0,str(R))
import numpy as np
from tradingagents.research.onchain_replication import compact_policy
from tradingagents.research.onchain_replication.contracts import AttributedGraph
base='tradingagents.research.onchain_replication';name=base+'.independent_connected';pkg=types.ModuleType(name);pkg.__path__=[str(C),str(S)];sys.modules[name]=pkg
for k in ('contracts','checkpoint_chunks','matching_identity','matching_hardening','matching_sparse'):sys.modules[name+'.'+k]=importlib.import_module(base+'.'+k)
bne=importlib.import_module(name+'.batched_numeric_execution');helper=importlib.import_module(name+'.adaptive_edge_policy');ann=bne.reuse.engine.ann
policy=dict(ann.ADAPTIVE_EDGE_POLICY)
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text());st=json.loads((D.parent/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json').read_text())['stage_policy'];c=compact_policy.effective_matching(c,st['pair']);p=compact_policy.pair_policy(st['pair']);schedule=st['schedule'];assert schedule['operations_per_call']==1000000

def graph(n,e):return AttributedGraph(tuple(str(k) for k in range(n)),np.arange(n,dtype=np.float64).reshape(-1,1)*.015,np.array([(i,j) for i in range(n) for j in range(n)][:e],dtype=np.int64).T.copy(),np.arange(e,dtype=np.float64).reshape(-1,1)*.001,'b'*64,'0')
a,b=graph(9,70),graph(10,72);assert ann._reuse_runtime() and ann._immutable_edges(a) and ann._immutable_edges(b)
def checkpoint(*a):raise AssertionError('unexpected checkpoint callback')
def make(label,option,trace):
 root=D/label;root.mkdir()
 return root,bne.NumericExecution(root,c,p,schedule,checkpoint,cells=2,batch_cells=2,max_origin_bytes=18,max_summary_bytes=8192,max_entries=4,max_retained_bytes=262144,max_key_bytes=131072,authority_poll=lambda:trace.append('poll'),edge_cache_policy=option)
results={};traces={};bindings={}
for label,option in [('default',None),('selected',dict(policy))]:
 trace=[];root,ex=make(label,option,trace)
 try:
  if option is not None:option['chunk_entries']=512;assert dict(ex._edge_cache_policy)==policy
  values=[]
  for k in range(2):
   value=ex(a,b,hashlib.sha256(('purpose'+str(k)).encode()).hexdigest());values.append([struct.pack('>d',value[0]).hex(),value[1],value[2]])
  binding=ex.finish();bne.verify(root,binding);assert (binding['computed'],binding['reused'])==(1,1)
  results[label]=values;traces[label]=trace;bindings[label]=binding
  if label=='selected':
   assert binding['edge_cache_policy']==policy
   altered=copy.deepcopy(binding);altered['edge_cache_policy']=None
   try:bne.verify(root,altered)
   except ValueError as e:assert 'adaptive policy differs' in str(e)
   else:raise AssertionError('selected binding downgrade accepted')
 finally:ex.close()
assert results['default']==results['selected'] and traces['default']==traces['selected']
# Constructor rejection must precede even numeric directory/origin creation.
root=D/'invalid';root.mkdir()
try:bne.NumericExecution(root,c,p,schedule,checkpoint,cells=2,batch_cells=2,max_origin_bytes=18,max_summary_bytes=8192,max_entries=4,max_retained_bytes=262144,max_key_bytes=131072,edge_cache_policy=dict(policy,max_scratch_bytes=262145))
except ValueError:assert not list(root.iterdir())
else:raise AssertionError('invalid policy accepted')
# Selection drift on an actual reused occurrence cannot inherit a valid old cache result.
root,ex=make('drift',dict(policy),[])
try:
 ex(a,b,hashlib.sha256(b'first').hexdigest());assert ex.memo.computed==1
 ex.memo.executor._edge_cache_policy=None
 try:ex(a,b,hashlib.sha256(b'second').hexdigest())
 except ValueError:pass
 else:raise AssertionError('mutated child cache hit accepted')
 assert ex.poisoned and not list((root/'numeric-batches').iterdir()) and (root/'numeric-origins.bin').stat().st_size==0
finally:ex.close()
# Source-only adapter validator/forwarding and inverses remain separately inspected.
out={'status':'PASS_CONNECTED_SYNTHETIC','edge_products':5040,'runtime_guard_unmodified_true':True,'results':results,'callback_counts':{k:len(v) for k,v in traces.items()},'callback_order_equal':True,'computed_reused':[1,1],'selected_summary_bytes':bindings['selected']['summary_bytes'],'invalid_constructor_precedes_files':True,'actual_reuse_drift_poison_before_summary':True,'binding_downgrade_refused':True,'caller_alias_copied':True,'limits':limits,'scope':'No genuine Owner/Run; normal alternate relative-import package with only unchanged dependencies aliased; no primitive or source-pin override.'}
(D/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
