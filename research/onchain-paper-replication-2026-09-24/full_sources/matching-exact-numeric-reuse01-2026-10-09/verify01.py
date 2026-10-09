import copy,hashlib,importlib.util,json,os,resource,signal,sys,weakref,gc
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[3]));spec=importlib.util.spec_from_file_location('numeric_reuse',P/'numeric_reuse.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication.matching_reference import match_reference
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal');policy=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576);schedule=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=3,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
def graph(names=('a','b'),parent='a',features=None,edges=None,ef=None):return AttributedGraph(names,np.array([[0.],[1.]]) if features is None else features,np.array([[0,1],[1,0]],dtype=np.int64) if edges is None else edges,np.array([[.2],[.3]]) if ef is None else ef,parent*64,names[0])
def executor(**kwargs):return m.NumericReuseExecutor(c,policy,schedule,lambda *a:None,max_entries=kwargs.get('entries',2),max_retained_bytes=kwargs.get('memory',16384),max_key_bytes=kwargs.get('key',4096))
checks=[];receipts=[]
def ck(n,v):assert v,n;checks.append(n)
a=graph();b=graph();ex=executor();first=ex(a,b,'1'*64);receipts.append(dict(ex.last_receipt));same=graph(('x','y'),'b');second=ex(same,b,'2'*64);receipts.append(dict(ex.last_receipt));ck('identity_only_reuse_exact',first==second and ex.last_receipt['mode']=='reused' and ex.last_receipt['origin_purpose_sha256']=='1'*64 and ex.last_receipt['purpose_sha256']=='2'*64 and ex.last_receipt['checkpoint_attempt_delta']==0);ck('reference_tolerance',abs(first[0]-match_reference(a,b,c).score)<=1e-12)
for label,g in [('node',graph(features=np.array([[.1],[1.]]))),('edgefeature',graph(ef=np.array([[.21],[.3]]))),('edgeorder',graph(edges=np.array([[1,0],[0,1]],dtype=np.int64),ef=np.array([[.3],[.2]]))),('dtype',graph(features=np.array([[0.],[1.]],dtype=np.float32))),('signedzero',graph(features=np.array([[-0.],[1.]])))]:
 ex(g,b,hashlib.sha256(label.encode()).hexdigest());ck('miss_'+label,ex.last_receipt['mode']=='computed' and ex.retained_bytes<=ex.max_retained_bytes and len(ex._cache)<=2)
ck('lru_eviction',len(ex._cache)==2)
old=weakref.ref(g);del g;gc.collect();ck('no_graph_retention',old() is None)
small=executor(memory=1024,key=1);small(a,b,'3'*64);small(a,b,'4'*64);ck('oversize_not_cached',small.computed==2 and small.reused==0 and small.retained_bytes<=1024)
mutable=graph();object.__setattr__(mutable,'node_features',mutable.node_features.copy());u=executor();u(mutable,b,'5'*64);u(mutable,b,'6'*64);ck('mutable_not_reused',u.computed==2)
x=executor();x(a,b,'7'*64);x.executor.config['alpha']=.9
try:x(a,b,'8'*64)
except ValueError:ck('configuration_refuses_poisoned',x.poisoned and not x._cache)
else:raise AssertionError('config mutation accepted')
x=executor();x(a,b,'9'*64);original=m.reference.agreement;m.reference.agreement=lambda *a:0.
try:
 try:x(a,b,'a'*64)
 except ValueError:ck('runtime_replacement_refuses',x.poisoned and not x._cache)
 else:raise AssertionError('runtime changed accepted')
finally:m.reference.agreement=original
primary=RuntimeError('checkpoint failure');x=m.NumericReuseExecutor(c,policy,schedule,lambda *args:(_ for _ in ()).throw(primary),max_entries=2,max_retained_bytes=16384,max_key_bytes=4096)
try:x(a,b,'b'*64)
except RuntimeError as e:ck('unfinished_never_cached',e is primary and x.poisoned and x.executor.poisoned and not x._cache and x.last_receipt is None)
else:raise AssertionError('failure missing')
ex.close();ck('close_clears',ex.closed and not ex._cache and ex.last_receipt is None)
try:ex(a,b,'c'*64)
except ValueError:checks.append('closed_refuses')
else:raise AssertionError('closed executed')
r={'status':'PASS_ENGINEERING_ONLY','checks':checks,'example_occurrence_receipts':receipts,'reference_tolerance':1e-12,'affinity':sorted(os.sched_getaffinity(0)),'no_benchmark':True};(P/'RESULT01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
