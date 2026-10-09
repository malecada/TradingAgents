import os,time,json,hashlib,importlib.util,sys,resource,platform
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(R));start=time.perf_counter()
import numpy as np
from tradingagents.research.onchain_replication import array_neighborhoods as baseline
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,AttributedGraph
candidate_path=D.parent/'array-neighborhood-sparse-selection01-2026-10-09/array_neighborhoods.py';assert hashlib.sha256(candidate_path.read_bytes()).hexdigest()=='e3b4bf6ff403f3e942af536ae83bdbd1e773723961edb3d1851881df3ec8d855'
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._benchmark_sparse',candidate_path);candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
assert np.__version__=='2.3.0';assert resource.getrlimit(resource.RLIMIT_AS)[0]==256*1024**2
out={'status':'RUNNING','runtime':{'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),'affinity':sorted(os.sched_getaffinity(0)),'address_space_limit':resource.getrlimit(resource.RLIMIT_AS),'file_limit':resource.getrlimit(resource.RLIMIT_FSIZE),'threads':{x:os.environ.get(x) for x in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}},'pins':{'baseline':hashlib.sha256(Path(baseline.__file__).read_bytes()).hexdigest(),'candidate':hashlib.sha256(candidate_path.read_bytes()).hexdigest()},'definitions':{'warmups':1,'repetitions':4,'order_even':['baseline','candidate'],'order_odd':['candidate','baseline'],'edge_chunk':256,'max_buffer_bytes':64*1024**2,'hop_depth':1,'setup_timed_separately':True,'output_digest_outside_extraction_timing':True},'cases':[]}
def digest(g):
 assert type(g) is AttributedGraph
 h=hashlib.sha256(repr((g.node_ids,g.parent_hash,g.center_id)).encode())
 for a in (g.node_features,g.edge_index,g.edge_features):h.update(str((a.shape,a.dtype.str)).encode());h.update(a.tobytes())
 return h.hexdigest()
def save():
 out['elapsed_seconds']=time.perf_counter()-start;out['max_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;(D/'RAW01.json').write_text(json.dumps(out,indent=2)+'\n')
try:
 for name,n,centers in [('bidirectional_chain',10000,[0,100,5000,9999]),('hub_and_leaves',4000,[0,1,2000,3999]),('dense_center',160,[0,79])]:
  t=time.perf_counter()
  if name=='bidirectional_chain':a=np.arange(n-1,dtype=np.int64);edge=np.stack([np.concatenate([a,a+1]),np.concatenate([a+1,a])])
  elif name=='hub_and_leaves':a=np.arange(1,n,dtype=np.int64);edge=np.stack([np.concatenate([np.zeros(n-1,dtype=np.int64),a]),np.concatenate([a,np.zeros(n-1,dtype=np.int64)])])
  else:a=np.arange(n,dtype=np.int64);edge=np.stack([np.repeat(a,n),np.tile(a,n)])
  g=GraphSnapshot('ETH','2022-01-01T00:00:00Z','2022-01-02T00:00:00Z','2022-01-03T00:00:00Z',('a'*64,),'b'*64,tuple('n'+str(i) for i in range(n)),np.arange(n*2,dtype=np.float64).reshape(n,2)*.125,edge,np.arange(edge.shape[1]*2,dtype=np.float64).reshape(-1,2)*-.25,edge.shape[1],edge.shape[1],{})
  case={'name':name,'nodes':n,'edges':edge.shape[1],'centers':centers,'fixture_seconds':time.perf_counter()-t,'initialization_seconds':{},'warmup':[],'timings':[]};out['cases'].append(case);indices={}
  for k,m in [('baseline',baseline),('candidate',candidate)]:
   t=time.perf_counter();indices[k]=m.ArrayNeighborhoodIndex(g,max_buffer_bytes=64*1024**2,edge_chunk=256);case['initialization_seconds'][k]=time.perf_counter()-t
  case['graph_hash']=indices['baseline'].identity;assert indices['baseline'].identity==indices['candidate'].identity
  config={'hop_depth':1,'maximum_neighborhood_nodes':n};hashes={}
  for center in centers:
   reference=None
   for k in ('baseline','candidate'):
    t=time.perf_counter();local=indices[k].neighborhood(center,config);dt=time.perf_counter()-t;h=digest(local);case['warmup'].append({'center':center,'implementation':k,'seconds':dt,'output_nodes':len(local.node_ids),'output_edges':local.edge_index.shape[1],'hash':h})
    if reference is None:reference=h
    else:assert reference==h
    del local
   hashes[center]=reference
  for rep in range(4):
   order=('baseline','candidate') if rep%2==0 else ('candidate','baseline')
   for center in centers:
    for k in order:
     t=time.perf_counter();local=indices[k].neighborhood(center,config);dt=time.perf_counter()-t;assert digest(local)==hashes[center];del local
     case['timings'].append({'repetition':rep,'center':center,'implementation':k,'seconds':dt})
  for ix in indices.values():ix.close()
  del indices,g,edge,a;save()
 out['status']='PASS';save();print(json.dumps({'status':'PASS','elapsed_seconds':out['elapsed_seconds'],'max_rss_kib':out['max_rss_kib']}))
except BaseException as error:
 out['status']='REFUSED';out['error']={'type':type(error).__name__,'message':str(error)};save();raise
