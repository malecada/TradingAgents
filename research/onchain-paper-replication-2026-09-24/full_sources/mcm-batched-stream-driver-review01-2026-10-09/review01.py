import gc,hashlib,importlib.util,json,os,resource,signal,sys,weakref
from pathlib import Path
from types import SimpleNamespace
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;sys.path.insert(0,str(R))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
jp=F/'mcm-batched-execution03-2026-10-09/batch_journal.py';dp=F/'mcm-batched-driver02-2026-10-09/driver.py';assert sha(jp)=='16d8c368195a166df0fbdf6f24b7ab0449b1cc06c122746dc132babbe97af06b';assert sha(dp)=='74d1105b595c65932b23dd0ac4232e5c07e55215b0c3375f3bd351bbc6b22478';jmod=load('journal03',jp);d=load('driver02',dp)
import numpy as np
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,AttributedGraph
from tradingagents.research.onchain_replication.neighborhoods import graph_hash,node_order_hash
from tradingagents.research.onchain_replication.matching_identity import graph_identity
g=GraphSnapshot('ETH','2022-01-03T00:00:00Z','2022-01-10T00:00:00Z','2022-01-10T00:00:00Z',('a'*64,),'b'*64,('a','b'),np.ones((2,4)),np.array([[0],[1]],dtype=np.int64),np.ones((1,2)),1,1,{})
motifs=tuple(AttributedGraph(('m',),np.ones((1,4)),np.empty((2,0),dtype=np.int64),np.empty((0,2)),'c'*64,'m') for _ in range(32));dictionary=SimpleNamespace(representatives=motifs,config={'hop_depth':1,'maximum_neighborhood_nodes':2});descriptor={'rows':2,'cells':64,'motifs':32,'graph_hash':graph_hash(g),'node_order_hash':node_order_hash(g.node_ids),'workload_sha256':'d'*64,'purpose_schema_version':2};policy={'max_buffer_bytes':100000,'edge_chunk':2,'extraction_limit':3}
base=d.ArrayNeighborhoodIndex;indexes=[];locals=[]
class Index(base):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);indexes.append(self)
 def neighborhood(self,center,cfg):
  gc.collect();assert not locals or locals[-1]() is None
  v=super().neighborhood(center,cfg);locals.append(weakref.ref(v));return v
d.ArrayNeighborhoodIndex=Index;results=[]
for mode in ['healthy','final_payload_mutation','final_root_replacement','sink_throw']:
 root=H/mode;j=jmod.BatchJournal(root,batch_cells=48,max_cells=64,max_bytes=200000,max_body_bytes=1024,boundary=lambda:None);calls=[];chunks=[];primary=RuntimeError('synthetic-sink-failure')
 def execute(local,m,key):
  ordinal=len(calls);center,motif=divmod(ordinal,32);purpose={'schema_version':2,'kind':'mcm','workload_sha256':'d'*64,'graph_hash':graph_hash(g),'center_index':center,'center_id':g.node_ids[center],'motif_index':motif,'typed_graphs':[graph_identity(local),graph_identity(m)],'ordinal':ordinal};assert key==hashlib.sha256(jmod.body(purpose)).hexdigest();calls.append(ordinal);return ordinal/64.,1,'iteration_cap'
 def sink(ordinal,center,motif,payload):
  assert len(payload)<=16 and ordinal==32*center+motif
  if mode=='sink_throw' and ordinal==4:raise primary
  chunks.append(payload)
  if ordinal==60:
   if mode=='final_payload_mutation':(root/'00000001.records.bin').write_bytes(b'bad')
   elif mode=='final_root_replacement':root.rename(H/'moved-root');root.mkdir()
 try:answer=d.drive(g,dictionary,descriptor=descriptor,policy=policy,journal=j,executor=execute,consumer=sink,max_chunk_bytes=16)
 except RuntimeError as e:
  assert mode=='sink_throw' and e is primary;record={'case':mode,'refused':True,'notes':e.__notes__,'confirmed_delivered':sum(map(len,chunks))//4}
 else:
  assert calls==list(range(64)) and answer['completed_cells']==64
  record={'case':mode,'returned_success':True,'result':answer,'declared_root_valid_payload':(root/'00000001.records.bin').exists() and (root/'00000001.records.bin').stat().st_size==92+16*53}
  if mode!='healthy':assert not record['declared_root_valid_payload']
 assert j.closed and indexes[-1].closed;gc.collect();assert locals[-1]() is None;record['cleanup_verified']=True;results.append(record)
(H/'RESULT01.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'source03':sha(jp),'driver02':sha(dp),'results':results}))
