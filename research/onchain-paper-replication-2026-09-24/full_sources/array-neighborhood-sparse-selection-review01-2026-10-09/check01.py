import os,resource,signal,sys,ast,json,hashlib,importlib.util
from pathlib import Path
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
R=Path(__file__).resolve().parent;ROOT=R.parents[3];C=R.parent/'array-neighborhood-sparse-selection01-2026-10-09';sys.path.insert(0,str(ROOT));h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((C/'MANIFEST01.json').read_bytes());oldpath=ROOT/m['baseline']['path'];assert h(oldpath)==m['baseline']['sha256'];assert h(C/'array_neighborhoods.py')==m['candidate']['sha256']
for p,v in m['files'].items():assert h(C/p)==v
from tradingagents.research.onchain_replication import array_neighborhoods as old
from tradingagents.research.onchain_replication.contracts import GraphSnapshot
from tradingagents.research.onchain_replication.matching_identity import graph_identity
import numpy as np
assert np.__version__=='2.3.0'
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._review_sparse',C/'array_neighborhoods.py');new=importlib.util.module_from_spec(spec);spec.loader.exec_module(new)
def tree(p):return ast.parse(p.read_bytes())
a=tree(oldpath);b=tree(C/'array_neighborhoods.py');ca=next(x for x in a.body if isinstance(x,ast.ClassDef));cb=next(x for x in b.body if isinstance(x,ast.ClassDef));changed={'_select','_induced_blocks','_neighborhood'}
assert {x.name for x in ca.body if isinstance(x,ast.FunctionDef)}=={x.name for x in cb.body if isinstance(x,ast.FunctionDef)}
for x,y in zip(ca.body,cb.body):
 if getattr(x,'name',None) not in changed:assert ast.dump(x)==ast.dump(y)
# Full source inverse by the retained exact unified patch, without editing source.
import difflib
assert ''.join(difflib.unified_diff(oldpath.read_text().splitlines(True),(C/'array_neighborhoods.py').read_text().splitlines(True),fromfile='tradingagents/research/onchain_replication/array_neighborhoods.py',tofile='candidate/array_neighborhoods.py'))==(C/'candidate.patch').read_text()
def graph(n,es,dtype):
 edges=np.array(es,dtype=np.int64).reshape(-1,2).T.copy();nf=np.arange(n*2,dtype=dtype).reshape(n,2)/8;nf[0,0]=-0.;ef=np.arange(len(es)*2,dtype=dtype).reshape(len(es),2)/16
 if len(es):ef[0,0]=-0.
 return GraphSnapshot('ETH','2022-01-01T00:00:00Z','2022-01-02T00:00:00Z','2022-01-03T00:00:00Z',('a'*64,),'b'*64,tuple('node'+str(i) for i in range(n)),nf,edges,ef,len(es),len(es),{})
def sig(out):return (out.node_ids,out.parent_hash,out.center_id,tuple((x.dtype.str,x.shape,x.tobytes()) for x in (out.node_features,out.edge_index,out.edge_features)),graph_identity(out))
cases=[]
for dtype in (np.float32,np.float64):
 es=[(5,3),(1,0),(3,1),(0,0),(2,1),(4,5),(1,2),(5,4)];g=graph(7,es,dtype)
 for center,hops in ((0,0),(3,1),(0,3),(6,4)):
  chosen={center};front={center}
  for _ in range(hops):
   reach={v for u,v in es if u in front}|{u for u,v in es if v in front};front=reach-chosen;chosen|=front
  ids=sorted(chosen);columns=[i for i,(u,v) in enumerate(es) if u in chosen and v in chosen];results=[]
  for module in (old,new):
   with module.ArrayNeighborhoodIndex(g,max_buffer_bytes=1000000,edge_chunk=1) as ix:
    cfg={'hop_depth':hops,'maximum_neighborhood_nodes':7};selected=ix.selected(center,cfg);assert selected.tolist()==ids;out=ix.neighborhood(center,cfg);assert out.node_ids==tuple(g.node_ids[i] for i in ids);assert out.edge_index.tolist()==[[ids.index(es[i][j]) for i in columns] for j in (0,1)];assert out.node_features.tobytes()==g.node_features[ids].tobytes() and out.edge_features.tobytes()==g.edge_features[columns].tobytes();assert not out.node_features.flags.writeable;results.append(sig(out));selected[:]=-1;assert ix.selected(center,cfg).tolist()==ids
  assert results[0]==results[1];cases.append((np.dtype(dtype).str,center,hops))
refusals=[]
for label,g,cfg,budget in [('duplicate',graph(3,[(1,0),(1,0)],np.float64),{'hop_depth':1,'maximum_neighborhood_nodes':3},1000000),('limit',graph(4,[(0,1),(2,0),(3,0)],np.float64),{'hop_depth':1,'maximum_neighborhood_nodes':2},1000000),('budget',graph(3,[],np.float64),{'hop_depth':0,'maximum_neighborhood_nodes':1},1)]:
 errors=[]
 for module in (old,new):
  try:
   with module.ArrayNeighborhoodIndex(g,max_buffer_bytes=budget,edge_chunk=1) as ix:ix.neighborhood(0,cfg)
  except ValueError as e:errors.append(str(e))
  else:raise AssertionError(label)
 assert errors[0]==errors[1];refusals.append((label,errors[0]))
doc=Path(np.__file__).parent/'_core/fromnumeric.py';assert "'quicksort'    1     O(n^2)            0" in doc.read_text()
r={'decision':'accepted_source_only','candidate_sha256':m['candidate']['sha256'],'baseline_sha256':m['baseline']['sha256'],'evidence':{str(p.relative_to(ROOT)):h(p) for p in (C/'MANIFEST01.json',C/'candidate.patch',C/'REPORT.md',oldpath)},'checks':{'changed_methods_only':sorted(changed),'additional_helper':'_merge_indices','independent_bfs_bitwise_hash_cases':cases,'refusals':refusals,'numpy_version':np.__version__},'scratch_proof':{'scope':'Numeric array storage, not RSS/Python allocator/validation/caller-held output','neighbor_merge_upper':'42N+26C <=44N+64C','difference_upper':'41N <=44N','selected_merge_upper':'34N+18C <=44N+64C','extraction':'selected8N+keep8E; bounded membership/remap/gathers within64C and existing width terms; outputs retain original2x charge','quicksort_assumption':'Pinned NumPy2.3.0 documents zero work-space quicksort; contiguous int64 in-place sort. Stack/internal allocator metadata excluded as in baseline.','unchanged_allowance':'retained16(E+N+1)+scratch16E+40(N+1)+4N+C(64+2node_width+2edge_width)'},'qualification':'Exact weak-hop selected IDs and original edge-column order/features/hash proven on tiny synthetic fixtures. Duplicate directed edges remain rejected by original graph validator. Lock/context/source validation methods unchanged; old author focused cases reused. Dense/growing sparse merges can regress. Allocation failure sites/timing differ; no universal hostile-runtime or total-memory proof, real graph, benchmark, speedup, source installation or empirical authority.'};(R/'SOURCE_REVIEW01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['checks']))
