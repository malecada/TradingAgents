import gc,hashlib,importlib.util,json,os,resource,sys,weakref
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;R=P.parents[3];sys.path.insert(0,str(R));os.nice(10);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(25,25))
import numpy as np
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,AttributedGraph
from tradingagents.research.onchain_replication.neighborhoods import graph_hash,node_order_hash
from tradingagents.research.onchain_replication.matching_identity import graph_identity

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
d=load('driver',P/'driver.py');jmod=load('journal',P.parent/'mcm-batched-execution03-2026-10-09/batch_journal.py')
g=GraphSnapshot('ETH','2022-01-03T00:00:00Z','2022-01-10T00:00:00Z','2022-01-10T00:00:00Z',('a'*64,),'b'*64,('a','b'),np.ones((2,4)),np.array([[0],[1]],dtype=np.int64),np.ones((1,2)),1,1,{})
motifs=tuple(AttributedGraph(('m',),np.ones((1,4)),np.empty((2,0),dtype=np.int64),np.empty((0,2)),'c'*64,'m') for _ in range(32));dictionary=SimpleNamespace(representatives=motifs,config={'hop_depth':1,'maximum_neighborhood_nodes':2})
descriptor={'rows':2,'cells':64,'motifs':32,'graph_hash':graph_hash(g),'node_order_hash':node_order_hash(g.node_ids),'workload_sha256':'d'*64,'purpose_schema_version':2};policy={'max_buffer_bytes':100000,'edge_chunk':2,'extraction_limit':3};actual=d.ArrayNeighborhoodIndex;indexes=[];locals_seen=[]
class Tracked(actual):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);indexes.append(self)
 def neighborhood(self,center,config):
  gc.collect();assert not locals_seen or locals_seen[-1]() is None
  assert config=={'hop_depth':1,'maximum_neighborhood_nodes':3};local=super().neighborhood(center,config);locals_seen.append(weakref.ref(local));return local
d.ArrayNeighborhoodIndex=Tracked;checks=[]
def one(label,fail=None):
 calls=[];chunks=[];j=jmod.BatchJournal(P/label,batch_cells=48,max_cells=64,max_bytes=200000,max_body_bytes=1024,boundary=lambda:None)
 def executor(local,m,key):
  ordinal=len(calls);center,motif=divmod(ordinal,32)
  purpose={'schema_version':2,'kind':'mcm','workload_sha256':'d'*64,'graph_hash':graph_hash(g),'center_index':center,'center_id':g.node_ids[center],'motif_index':motif,'typed_graphs':[graph_identity(local),graph_identity(m)],'ordinal':ordinal}
  assert key==hashlib.sha256(jmod.body(purpose)).hexdigest();calls.append(ordinal)
  if fail=='executor' and ordinal==5:raise RuntimeError('numeric fixture failed')
  return (-0.0 if ordinal==0 else ordinal/64.),2,'temperature_complete'
 def sink(ordinal,center,motif,payload):
  assert ordinal==center*32+motif and len(payload)<=16
  if fail=='sink' and ordinal==4:raise RuntimeError('consumer fixture failed')
  chunks.append((ordinal,payload))
 try:result=d.drive(g,dictionary,descriptor=descriptor,policy=policy,journal=j,executor=executor,consumer=sink,max_chunk_bytes=16)
 except RuntimeError as e:
  assert fail and 'incomplete' in e.__notes__[0];assert j.cells==(0 if fail=='executor' else 48);assert sum(len(b)//4 for _,b in chunks)==(0 if fail=='executor' else 4);checks.append(label+':original_error_and_partial_unavailable')
 else:
  assert not fail and result['completed_cells']==64 and result['completed_rows']==2 and result['representation_complete'] is False;assert calls==list(range(64));expected=np.array([-0.0]+[i/64. for i in range(1,64)],dtype=np.float32).tobytes();assert b''.join(b for _,b in chunks)==expected;checks.append('all_center_motif_purpose_f64_to_f32_order')
 assert j.closed and indexes[-1].closed;gc.collect();assert locals_seen[-1]() is None
one('success');one('executor_failure','executor');one('consumer_failure','sink')
# Changed stream failures use the actual03 journal. No numerical engine claim.
original_tasks=d._tasks
for mode in ['short','malformed','mutated_purpose','reader_tamper']:
 j=jmod.BatchJournal(P/mode,batch_cells=48,max_cells=64,max_bytes=200000,max_body_bytes=1024,boundary=lambda:None)
 held=[];sent=[]
 def tasks(*args):
  source=original_tasks(*args)
  try:
   for ordinal in range(64):
    if mode=='short' and ordinal==47:return
    task=next(source)
    if mode=='malformed' and ordinal==3:task=(task[0],task[1])
    if mode=='mutated_purpose':held.append(task[0])
    try:yield task
    finally:del task
  finally:source.close()
 d._tasks=tasks
 def exe(*args):
  if mode=='mutated_purpose' and len(held)>1:held[0]['center_id']='changed'
  return .25,1,'iteration_cap'
 if mode=='reader_tamper':
  actualrun=j.run_batch_stream
  def tamper(*args):
   result=actualrun(*args);path=j.root/'00000000.records.bin';raw=bytearray(path.read_bytes());raw[-1]=99;path.write_bytes(raw);return result
  j.run_batch_stream=tamper
 try:d.drive(g,dictionary,descriptor=descriptor,policy=policy,journal=j,executor=exe,consumer=lambda *x:sent.append(x),max_chunk_bytes=16)
 except (ValueError,RuntimeError) as e:assert not sent and j.closed and indexes[-1].closed;checks.append(mode+':refused_before_sink_and_closed')
 else:raise AssertionError(mode)
 d._tasks=original_tasks;gc.collect();assert locals_seen[-1]() is None
checks+=['one_local_across_48cell_batches','generator_index_journal_cleanup']
result={'status':'PASS_SYNTHETIC_STREAM_ROUTING_ONLY','checks':checks,'actual_affinity':sorted(os.sched_getaffinity(0)),'source_sha256':hashlib.sha256((P/'driver.py').read_bytes()).hexdigest(),'journal_sha256':hashlib.sha256((P.parent/'mcm-batched-execution03-2026-10-09/batch_journal.py').read_bytes()).hexdigest(),'numeric_executor':'deterministic tiny callback; not scientific equivalence or authority'};(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
