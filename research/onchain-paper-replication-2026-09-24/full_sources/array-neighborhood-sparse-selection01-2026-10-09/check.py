import hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(R))
from tradingagents.research.onchain_replication import array_neighborhoods as old
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,AttributedGraph
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._sparse_candidate',D/'array_neighborhoods.py');new=importlib.util.module_from_spec(spec);spec.loader.exec_module(new)
def graph(n,edges,dtype=np.float64):
 e=np.array(edges,dtype=np.int64).reshape(-1,2).T.copy();nf=(np.arange(n*3).reshape(n,3)*.125).astype(dtype);nf[0,0]=-0.0;ef=(np.arange(len(edges)*2).reshape(len(edges),2)*-.25).astype(dtype)
 return GraphSnapshot('ETH','2022-01-01T00:00:00Z','2022-01-02T00:00:00Z','2022-01-03T00:00:00Z',('a'*64,),'b'*64,tuple(f'n{i}' for i in range(n)),nf,e,ef,len(edges),len(edges),{})
def snap(g):
 assert type(g) is AttributedGraph
 arrays=[g.node_features,g.edge_index,g.edge_features]
 assert all(not a.flags.writeable for a in arrays)
 return (g.node_ids,g.parent_hash,g.center_id,tuple((a.dtype.str,a.shape,a.tobytes()) for a in arrays))
cases=[]
def compare(name,g,center,hops,limit,chunk=2,allowance=1000000):
 results=[]
 for module in (old,new):
  try:
   with module.ArrayNeighborhoodIndex(g,max_buffer_bytes=allowance,edge_chunk=chunk) as ix:
    selected=ix.selected(center,{'hop_depth':hops,'maximum_neighborhood_nodes':limit});out=ix.neighborhood(center,{'hop_depth':hops,'maximum_neighborhood_nodes':limit});results.append(('ok',selected.dtype.str,selected.tobytes(),snap(out),ix.identity,ix.buffer_allowance))
   try:ix.selected(center,{'hop_depth':0,'maximum_neighborhood_nodes':1})
   except ValueError as e:assert str(e)=='neighborhood index is closed'
   else:raise AssertionError('closed accepted')
  except Exception as e:results.append(('refused',type(e).__name__,str(e)))
 assert results[0]==results[1],(name,results)
 cases.append({'name':name,'status':results[0][0],'result_sha256':hashlib.sha256(repr(results[0]).encode()).hexdigest()})
g=graph(8,[(4,1),(1,0),(0,2),(2,0),(2,3),(3,3),(6,4),(4,0)])
for hops in (0,1,2):compare('weighted_directed_overlap_hop'+str(hops),g,0,hops,8)
compare('isolated',g,7,2,1)
compare('self_loop',g,3,1,8,1)
compare('capacity_whole_level',g,0,2,3)
compare('empty_edges',graph(3,[]),1,2,1)
compare('float32',graph(5,[(4,0),(0,1),(1,2)],np.float32),0,2,5,1)
compare('repeated_directed_edges_refused',graph(3,[(0,1),(0,1)]),0,1,3)
compare('invalid_center',g,-1,1,8)
compare('invalid_hops',g,0,-1,8)
# Same constructor allowance and output refusal without changing reservation formula.
with old.ArrayNeighborhoodIndex(g,max_buffer_bytes=1000000,edge_chunk=2) as ix:allow=ix.buffer_allowance
compare('output_buffer_refused',g,0,1,8,allowance=allow)
compare('constructor_buffer_refused',g,0,1,8,allowance=allow-1)
# Lock semantics and independent selected return.
for module in (old,new):
 with module.ArrayNeighborhoodIndex(g,max_buffer_bytes=1000000,edge_chunk=1) as ix:
  a=ix.selected(0,{'hop_depth':1,'maximum_neighborhood_nodes':8});a[:]=-1;assert (ix.selected(0,{'hop_depth':1,'maximum_neighborhood_nodes':8})>=0).all()
  ix._lock.acquire()
  try:
   for call in (lambda:ix.selected(0,{}),lambda:ix.neighborhood(0,{}),ix.close):
    try:call()
    except ValueError as e:assert str(e)=='neighborhood index is busy'
    else:raise AssertionError('busy accepted')
  finally:ix._lock.release()
print(json.dumps({'status':'PASS','cases':cases,'case_count':len(cases),'context_lock_and_independent_output':True,'numpy_version':np.__version__,'affinity':sorted(__import__('os').sched_getaffinity(0))},indent=2))
