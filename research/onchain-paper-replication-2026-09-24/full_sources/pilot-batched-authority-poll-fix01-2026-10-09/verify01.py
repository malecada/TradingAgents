"""Finite synthetic scheduling and actual tiny numeric tests; no authority objects."""
import os,sys,resource,signal,json,hashlib,importlib.util,copy,ast,struct
from pathlib import Path
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(60);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
H=Path(__file__).resolve().parent;ROOT=H.parents[3];S=ROOT/'tradingagents/research/onchain_replication';sys.path.insert(0,str(ROOT))
from tradingagents.research.onchain_replication import imported_authority_interval as interval,batched_journal as journal,batched_pair_executor as original,compact_policy
import tradingagents.research.onchain_replication as package
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
j=lambda p:json.loads(p.read_bytes())
gate=j(H.parent/'real-data-pilot-full26-entry01-2026-10-09/gate01.json');inputs=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261009-26']['inputs']
def metadata(role):
 p=ROOT/inputs[role]['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==inputs[role]['sha256'];return j(p)
lease_role=next(k for k in inputs if 'lease' in k);policy=metadata(lease_role)
# The registered document is directly the interval schema.
clock=[0.];counts={'full':0,'finger':0,'live':0}
def scheduler():
 clock[0]=0.;it=interval.Interval(policy,clock=lambda:clock[0])
 def call(boundary=False):
  def count(k):counts[k]+=1
  it.validate(lambda:count('full'),lambda:count('finger'),lambda:count('live'),boundary=boundary)
 call(True);return it,call
batch_results=[]
for selected in (False,True):
 it,poll=scheduler();root=H/('batch-green' if selected else 'batch-red');q=journal.BatchJournal(root,batch_cells=4096,max_cells=4096,max_bytes=1048576,max_body_bytes=8192,boundary=lambda:poll(True))
 def tasks():
  for i in range(4096):yield ({'ordinal':i},None,None)
 def execute(a,b,purpose):
  clock[0]+=.02
  if selected:poll()
  return .5,48,'temperature_complete'
 failure=None
 try:rows=q.run_batch_stream(4096,tasks(),execute,{'fixture':'clock-only'})
 except ValueError as e:failure=str(e)
 assert (failure=='import lease: stale interval cannot refresh' and q.cells==0 and not (root/'00000000.complete.json').exists()) if not selected else (failure is None and q.cells==4096 and len(rows)==4096)
 batch_results.append({'selected':selected,'failure':failure,'cells':q.cells,'clock':clock[0]});q.close()
def load(name):
 full='tradingagents.research.onchain_replication.'+name;spec=importlib.util.spec_from_file_location(full,H/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[full]=m;setattr(package,name,m);spec.loader.exec_module(m);return m
candidate=load('batched_pair_executor')
p=metadata('compact_policy')['stage_policy'];config=metadata('producer_plan')['producers']['original32']['descriptor']['configs']['matching'];config=compact_policy.effective_matching(config,p['pair']);limits=compact_policy.pair_policy(p['pair']);schedule=copy.deepcopy(p['schedule']);schedule['operations_per_call']=11
G=AttributedGraph(('x',),np.zeros((1,2)),np.empty((2,0),dtype=np.int64),np.empty((0,2)),'1'*64,'x')
cb=lambda *a:None
base=original.PairExecutor(config,limits,schedule,cb)(G,G,'2'*64)
legacy=candidate.PairExecutor(config,limits,schedule,cb)(G,G,'2'*64);assert base==legacy
it,poll=scheduler();poll_calls=[0]
def tick():clock[0]+=5.;poll_calls[0]+=1;poll()
x=candidate.PairExecutor(config,limits,schedule,cb,authority_poll=tick);value=x(G,G,'2'*64);assert value==base and struct.pack('>d',value[0])==struct.pack('>d',base[0]);poll(True)
assert x.checkpoints==0 and x.reserved_bytes==0 and poll_calls[0]>2
# Candidate propagation through actual memo and persistence wrapper; tiny two occurrences.
memo=load('batched_numeric_reuse');numeric=load('batched_numeric_execution');stream=H/'stream';stream.mkdir();calls=[0]
def lightpoll():calls[0]+=1
n=numeric.NumericExecution(stream,config,limits,schedule,cb,cells=2,batch_cells=2,max_origin_bytes=18,max_summary_bytes=8192,max_entries=2,max_retained_bytes=1048576,max_key_bytes=8192,authority_poll=lightpoll)
a=n(G,G,'3'*64);b=n(G,G,'4'*64);assert a==b==base and n.computed==n.reused==1;binding=n.finish();n.close();assert calls[0]>2
for label,callback in [('callback_error',lambda:(_ for _ in ()).throw(RuntimeError('poll failed')))]:
 x=candidate.PairExecutor(config,limits,schedule,cb,authority_poll=callback)
 try:x(G,G,'5'*64)
 except RuntimeError as e:assert str(e)=='poll failed' and x.poisoned
 else:raise AssertionError(label)
it,poll=scheduler();clock[0]=61
try:poll()
except ValueError as e:assert str(e)=='import lease: stale interval cannot refresh' and it.closed
else:raise AssertionError('true gap must remain fatal')
it,poll=scheduler();clock[0]=-1
try:poll()
except ValueError:assert it.closed
else:raise AssertionError('bad clock')
# Every unrelated source byte is recovered by literal inverses.
changes=j(H/'CHANGES01.json')
for name,record in changes.items():
 text=(H/name).read_text();ast.parse(text)
 for before,after in reversed(record['replacements']):assert text.count(after)==1;text=text.replace(after,before)
 assert text==(S/name).read_text()
result=dict(status='PASS_SYNTHETIC_ONLY',registered_interval=policy,batch_clock_cases=batch_results,numeric_equal=value,pair_poll_calls=poll_calls[0],wrapper_poll_calls=calls[0],true_gap_and_callback_and_clock_refusals=True,literal_inverses=True,limitations=['No genuine authority callbacks exercised.','Single uninterruptible construction/extraction/advance/score or authority callback longer than freshness budget remains fatal.'])
(H/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
