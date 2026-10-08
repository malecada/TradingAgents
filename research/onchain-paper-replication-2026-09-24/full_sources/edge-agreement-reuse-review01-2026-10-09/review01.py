import os,resource,signal,sys,hashlib,json,ast,copy,importlib.util
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(60)
R=Path.cwd();sys.path.insert(0,str(R));H=Path(__file__).resolve().parent;P=H.parent/'edge-agreement-reuse-candidate01-2026-10-09';checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ck('candidate_exact',sha(P/'matching_annealing.py')=='1c9e48fa537839ce54236d24e82b35108aaff3c7f36995236e819d5e877f24b4')
ck('baseline_exact',sha(P/'baseline.py')=='63555980e79fc10fc1a5093b75c21ec3015c79f3cf6d39c4bc90c1f27125ce2a')
# Apply the supplied inverse as text in memory only.
lines=(P/'matching_annealing.py').read_text().splitlines(True);out=[];pos=0
for block in (P/'inverse.patch').read_text().split('@@ ')[1:]:
 if not block[0].isdigit() and not block.startswith('-'):continue
 header,body=block.split(' @@',1);start=int(header.split()[0][1:].split(',')[0])-1
 out+=lines[pos:start];pos=start
 for line in body.splitlines(True)[1:]:
  if line.startswith(' '):assert lines[pos]==line[1:];out.append(line[1:]);pos+=1
  elif line.startswith('-'):assert lines[pos]==line[1:];pos+=1
  elif line.startswith('+'):out.append(line[1:])
out+=lines[pos:];ck('full_text_inverse',''.join(out)==(P/'baseline.py').read_text())
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
mods=[]
for file,name in [('baseline.py','review_edge_baseline'),('matching_annealing.py','review_edge_candidate')]:
 spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.'+name,P/file);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);mods.append(m)
B,C=mods
cfg=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=4,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
def graph(n,bad=False):
 edges=[(u,v) for u in range(n) for v in range(n) if u!=v];e=np.array([[i/17,-0.] for i in range(len(edges))]);
 if bad:e[-1,0]=1e308
 return AttributedGraph(tuple(map(str,range(n))),np.zeros((n,2)),np.asarray(edges,dtype=np.int64).T,e,'a'*64,'0')
def equal(x,y):return x.keys()==y.keys() and all(x[k].tobytes()==y[k].tobytes() if isinstance(x[k],np.ndarray) else x[k]==y[k] for k in x)
a,b=graph(4),graph(3);ck('eligible',C._immutable_edges(a) and C._reuse_runtime())
for budget in [1,9,74,100000]:
 x=B.create(a,b,cfg,max_state_bytes=65536,max_chunk_entries=32);y=copy.deepcopy(x)
 while x['phase']!='done':
  ck('operations_and_bits_'+str(budget),B.advance(x,a,b,cfg,max_operations=budget)==C.advance(y,a,b,cfg,max_operations=budget) and equal(x,y))
# Original late agreement failure retains class/message and all partial state.
a=graph(4,True);states=[];errors=[]
for m in mods:
 s=m.create(a,b,cfg,max_state_bytes=65536,max_chunk_entries=32)
 try:m.advance(s,a,b,cfg,max_operations=100000)
 except OverflowError as e:errors.append((type(e).__name__,str(e)))
 states.append(s)
ck('lazy_late_error_prefix',len(errors)==2 and errors[0]==errors[1] and equal(*states))
# Cache is local only; checkpoint routines and all other existing functions AST unchanged.
bt=ast.parse((P/'baseline.py').read_text());ct=ast.parse((P/'matching_annealing.py').read_text());bf={n.name:ast.dump(n) for n in bt.body if isinstance(n,ast.FunctionDef)};cf={n.name:ast.dump(n) for n in ct.body if isinstance(n,ast.FunctionDef)}
ck('other_functions_including_checkpoints_exact',all(v==cf[k] for k,v in bf.items() if k!='_advance_checked'))
# Concrete maximum chunk arrays, including view base containers and transient guards.
a=graph(9);b=graph(8);count=1024;positions=np.arange(count,dtype=np.int64);left,right=np.divmod(positions,56);u,v=a.edge_index[:,left];i,j=b.edge_index[:,right];old=np.ones(count);weights=np.empty(count);cached=np.empty(4096);valid=np.zeros(4096,dtype=np.bool_)
seen=set()
def size(x):
 if id(x) in seen:return 0
 seen.add(id(x));return sys.getsizeof(x)+(size(x.base) if isinstance(x,np.ndarray) and x.base is not None else 0)
containers=(positions,left,right,u,v,i,j,old,weights,cached,valid)
actual=sum(size(x) for x in containers)+sys.getsizeof(containers)+sys.getsizeof((a.edge_features,b.edge_features))
# At next chunk assignment, previous arrays remain until rebound; conservative extra copy of all chunk payload/headers and guard temporaries.
conservative=actual+sum(sys.getsizeof(np.empty(count,dtype=np.float64)) for _ in range(10))+sys.getsizeof(np.empty(count,dtype=np.bool_))+4096
ck('combined_scratch_headers_and_overlap',conservative<262144)
x={'decision':'accepted-source-only','candidate_sha256':sha(P/'matching_annealing.py'),'baseline_sha256':sha(P/'baseline.py'),'checks':checks,'check_count':len(checks),'scratch_bytes':{'simultaneous_concrete_arrays_and_containers':actual,'conservative_chunk_overlap_guard_and_fixed_allowance':conservative,'reservation':262144},'resources':{'affinity':sorted(os.sched_getaffinity(0)),'nice':10,'AS':256*1024**2,'FSIZE':4*1024**2,'seconds':60},'qualification':'Synthetic exact-state/order/operation/error checks only. Local per-advance cache has no persistent checkpoint state. Frozen original callable/runtime, immutable bytes-backed exact graphs, exclusive state ownership, no concurrent mutation/callback or fenv changes required. Allocation failures can differ. Bound covers edge scratch plus cache, excludes retained state and existing normalization/validation/library allocations; not process RSS or universal hostile-runtime safety. No performance, empirical, source installation or launch admission claim.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'checks':len(checks),'scratch':x['scratch_bytes'],'sha256':sha(H/'SOURCE_REVIEW01.json')}))
