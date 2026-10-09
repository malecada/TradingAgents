import os,resource,signal,sys,time,json,ast,importlib.util,hashlib,struct,statistics
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(R))
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(r,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'wall':signal.getitimer(signal.ITIMER_REAL),'threads':{k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}}
assert limits['affinity']==[3] and limits['nice']==10 and limits['as']==(536870912,)*2 and limits['fsize']==(4194304,)*2
(D/'LIMITER01.json').write_text(json.dumps(limits,indent=2)+'\n');started=time.perf_counter()
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as old
from tradingagents.research.onchain_replication.contracts import AttributedGraph
source=(D/'matching_annealing.py').read_text();inverse=source
for a,b in reversed(json.loads((D/'CHANGES01.json').read_text())):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
assert inverse==Path(old.__file__).read_text();assert ast.dump(ast.parse(inverse))==ast.dump(ast.parse(Path(old.__file__).read_text()))
def load(name,path):
 spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.'+name,path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
new=load('adaptive_candidate',D/'matching_annealing.py');policy=dict(new.ADAPTIVE_EDGE_POLICY)
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text())
def graph(n,edges,fail=False):
 e=np.array([(i,j) for i in range(n) for j in range(n)][:edges],dtype=np.int64).T.copy();f=np.arange(edges,dtype=np.float64).reshape(-1,1)*.002
 if fail:f[3]=1e308
 return AttributedGraph(tuple(str(i) for i in range(n)),np.arange(n,dtype=np.float64).reshape(-1,1)*.01,e,f,'a'*64,'0')
a,b=graph(8,64),graph(16,128)
def create(module,aa=a,bb=b):return module.create(aa,bb,c,max_state_bytes=1024**2,max_chunk_entries=256)
def eq(x,y):
 assert x.keys()==y.keys()
 for k in x:
  if isinstance(x[k],np.ndarray):assert x[k].dtype==y[k].dtype and x[k].shape==y[k].shape and x[k].tobytes()==y[k].tobytes(),k
  else:assert x[k]==y[k],k
checks=['literal/AST inverse'];timings=[];reference=None
for rep in range(2):
 row={};states={}
 for label,mod in ([('original',old),('selected',new)] if rep==0 else [('selected',new),('original',old)]):
  st=create(mod);begin=time.perf_counter_ns();used=mod.advance(st,a,b,c,max_operations=1000000,**({'edge_cache_policy':policy} if label=='selected' else {}));row[label]=time.perf_counter_ns()-begin;states[label]=st;row[label+'_used']=used
 eq(states['original'],states['selected']);assert row['original_used']==row['selected_used'];assert states['selected']['iterations']==48 and states['selected']['phase']=='done'
 xr=old.result(states['original'],a,b,c);yr=new.result(states['selected'],a,b,c);assert xr.assignment.tobytes()==yr.assignment.tobytes() and struct.pack('>d',xr.score)==struct.pack('>d',yr.score) and xr.iterations==yr.iterations
 timings.append(row);reference=states['selected']
checks.append('two alternating real8192-edge-product full advances: full state/used/48iterations/assignment/score bits equal')
path=D/'checkpoint';pin=new.save(reference,path,a,b,c,max_checkpoint_bytes=1024**2,checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':256});restored=old.load(path,a,b,c,expected_sha256=pin,max_state_bytes=1024**2,max_chunk_entries=256,checkpoint_layout={'format':'sharded-npy-v1','chunk_entries':256});eq(reference,restored);checks.append('actual unchanged original checkpoint load of selected completed state')
# Test-local counter insertion into exact call sites; no primitive monkeypatch,
# profiler or runtime-guard change. Counts measured separately from timing.
class Count(ast.NodeTransformer):
 def visit_Assign(self,node):
  self.generic_visit(node)
  if isinstance(node.value,ast.BinOp) and isinstance(node.value.op,ast.Mult) and isinstance(node.value.right,ast.Call) and isinstance(node.value.right.func,ast.Name) and node.value.right.func.id=='agreement':
   return [ast.parse('_edge_calls[0]+=1').body[0],node]
  return node
 def visit_AugAssign(self,node):
  self.generic_visit(node)
  if any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='agreement' for x in ast.walk(node)):
   return [ast.parse('_edge_calls[0]+=1').body[0],node]
  return node
counts={}
for label,text in [('original',inverse),('selected',source)]:
 tree=Count().visit(ast.parse(text));tree.body.insert(0,ast.parse('_edge_calls=[0]').body[0]);ast.fix_missing_locations(tree);path=D/('count_'+label+'.py');path.write_text(ast.unparse(tree)+'\n');mod=load('count_'+label,path);state=create(mod);mod.advance(state,a,b,c,max_operations=1000000,**({'edge_cache_policy':policy} if label=='selected' else {}));eq(state,reference);counts[label]=mod._edge_calls[0]
assert counts=={'original':8192*48,'selected':8192};checks.append('actual test-local edge agreement counter reduction393216→8192; primitive/runtime guards unchanged')
# Failure at original ordered position384 crosses selected256 chunk boundary.
af=graph(8,64,True);failed=[]
for mod,kw in [(old,{}),(new,{'edge_cache_policy':policy})]:
 state=create(mod,af,b)
 try:mod.advance(state,af,b,c,max_operations=1000000,**kw)
 except OverflowError as error:failed.append((state,type(error).__name__,str(error)))
 else:raise AssertionError('missing agreement overflow')
eq(failed[0][0],failed[1][0]);assert failed[0][1:]==failed[1][1:] and failed[0][0]['cursor']==384 and failed[0][0]['safe'] is False;checks.append('ordered agreement failureprefix across256 boundary exact cursor384/Q/primary type-message')
# Nonstandard mode disables selected extended cache/chunks; same short original path.
with np.errstate(under='raise'):
 x=create(old);y=create(new);u=old.advance(x,a,b,c,max_operations=200);v=new.advance(y,a,b,c,max_operations=200,edge_cache_policy=policy);eq(x,y);assert u==v
checks.append('nonstandard runtime original fallback partial state/used equality')
# Conservative explicit overlap charge incl allocator-independent ndarray headers.
charge=9*16384+256*256+16384;assert charge==229376 and charge<=262144
out={'status':'PASS_SYNTHETIC_NO_AUTHORITY','checks':checks,'shape':[8,16],'edges':[64,128],'edge_products':8192,'policy':policy,'maximum_explicit_charge':charge,'timings_ns':timings,'edge_agreement_calls':counts,'checkpoint_sha256':pin,'limits':limits,'elapsed_seconds':time.perf_counter()-started,'counter_qualification':'Separate retained test-local AST counter at exact agreement sites. Production modules/primitives unchanged; no profiler. Timings use uninstrumented candidate.'}
(D/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
