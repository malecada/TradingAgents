import os,resource,signal,json,sys,time,hashlib,importlib.util,ast,struct
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];sys.path.insert(0,str(R))
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(r,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'wall':signal.getitimer(signal.ITIMER_REAL),'threads':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}}
assert limits['affinity']==[3] and limits['nice']==10
(D/'LIMITER01.json').write_text(json.dumps(limits,indent=2)+'\n');started=time.perf_counter()
import numpy as np
from tradingagents.research.onchain_replication import batched_numeric_reuse as old,compact_policy
from tradingagents.research.onchain_replication.contracts import AttributedGraph
prefix='tradingagents.research.onchain_replication.'
def load(name,file):
 spec=importlib.util.spec_from_file_location(prefix+name,D/file);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
g=load('geometry_summary','geometry_summary.py');new=load('geometry_candidate','batched_numeric_reuse.py')
src=(D/'batched_numeric_reuse.py').read_text()
for a,b in reversed(json.loads((D/'CHANGES01.json').read_text())):assert src.count(b)==1;src=src.replace(b,a)
assert src==Path(old.__file__).read_text();assert ast.dump(ast.parse(src))==ast.dump(ast.parse(Path(old.__file__).read_text()))
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text());stage=json.loads((D.parent/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json').read_text())['stage_policy'];p=compact_policy.pair_policy(stage['pair']);c=compact_policy.effective_matching(c,stage['pair']);s=stage['schedule']
def graph(n):
 e=np.array([(i,(i+1)%n) for i in range(n)],dtype=np.int64).T.copy()
 return AttributedGraph(tuple(str(i) for i in range(n)),np.arange(n*2,dtype=np.float64).reshape(n,2)*.01,e,np.ones((n,2),dtype=np.float64),'a'*64,'0')
a,b=graph(3),graph(4);purposes=[hashlib.sha256(str(i).encode()).hexdigest() for i in range(4)]
def checkpoint(*args):raise AssertionError('unexpected checkpoint')
def make(module,trace,**kw):return module.NumericReuseExecutor(c,p,s,checkpoint,max_entries=8,max_retained_bytes=65536,max_key_bytes=32768,authority_poll=lambda:trace.append('poll'),**kw)
rows=[];reference=None
for flag in ['baseline',None,False,True]:
 trace=[];m=make(old if flag=='baseline' else new,trace,**({} if flag=='baseline' else {'geometry':flag}));results=[];receipts=[]
 try:
  m.begin_batch();t=time.perf_counter_ns()
  for purpose in purposes:
   v=m(a,b,purpose);results.append((struct.pack('>d',v[0]).hex(),*v[1:]));receipts.append(m.last_receipt.copy())
  elapsed=time.perf_counter_ns()-t
  if flag is True:assert m.last_geometry_summary is None
  m.end_batch()
  if flag is True:
   summary=json.loads(m.last_geometry_summary);assert summary['computed']==1 and summary['reused']==3 and summary['stop']==4 and summary['end_batch_attested'];assert summary['metrics']['matrix_product']['sum']==48 and summary['metrics']['edge_product']['sum']==48;assert summary['static_shape_only']=={'batched02_two_pair_scratch':4,'compiled04_matrix_shape':4}
  elif flag!='baseline':assert m.last_geometry_summary is None
  if reference is None:reference=(results,receipts,trace)
  else:assert (results,receipts,trace)==reference
  rows.append({'geometry':flag,'four_calls_ns':elapsed,'poll_count':len(trace)})
 finally:m.close()
# Original end attestation must pass; no credited summary upon failure.
trace=[];m=make(new,trace,geometry=True);m.begin_batch();m(a,b,purposes[0]);attest=new.attest;primary=RuntimeError('attestation failure')
def fail(counters):raise primary
new.attest=fail
try:
 try:m.end_batch()
 except RuntimeError as error:assert error is primary
 else:raise AssertionError('missing guard refusal')
 assert m.poisoned and m.last_geometry_summary is None and m._geometry.data is None
finally:new.attest=attest;m.close()
# Byte cap refuses without credit; completed result remains provisional.
m=make(new,[],geometry=True,max_geometry_summary_bytes=1);m.begin_batch();m(a,b,purposes[0])
try:
 try:m.end_batch()
 except ValueError:pass
 else:raise AssertionError('missing summary cap')
 assert m.poisoned and m.last_geometry_summary is None
finally:m.close()
# Geometry only: finite count, exact ordinals, overflowing products refuse.
from types import SimpleNamespace as NS
for aa,bb,receipt in [(a,b,{'ordinal':1,'mode':'computed'}),(NS(node_ids=range(2**32),edge_index=NS(shape=(2,1))),NS(node_ids=range(2**32),edge_index=NS(shape=(2,1))),{'ordinal':0,'mode':'computed'})]:
 z=g.Geometry(8192);z.begin(0)
 try:z.add(aa,bb,receipt)
 except ValueError:pass
 else:raise AssertionError('missing bounds refusal')
z=g.Geometry(8192);z.begin(0)
for i in range(4096):z.add(a,b,{'ordinal':i,'mode':'computed'})
try:z.add(a,b,{'ordinal':4096,'mode':'computed'})
except ValueError:pass
else:raise AssertionError('missing cardinality refusal')
# Conservative serialized maximum: all integer fields at int63 and hist counts4096.
for metric in z.data['metrics'].values():metric.update(sum=g.LIMIT,max=g.LIMIT,histogram=[4096]*len(g.BINS))
z.data.update(start=g.LIMIT,stop=g.LIMIT,computed=4096,reused=4096);z.data['static_shape_only']={k:4096 for k in z.data['static_shape_only']};upper=len(g.raw(z.data));assert upper+1027<8192
# Isolated new metadata overhead, one bounded4096-cell fixture, no second numerical pass.
z=g.Geometry(8192);z.begin(0);t=time.perf_counter_ns()
for i in range(4096):z.add(a,b,{'ordinal':i,'mode':'computed'})
body=z.finish(4096,4096,0);overhead=time.perf_counter_ns()-t
out={'status':'PASS_SYNTHETIC_NO_AUTHORITY','literal_inverse':True,'exact_results_receipts_callback_trace':True,'routes':rows,'geometry_only_4096_adds_and_finish_ns':overhead,'geometry_summary_bytes':len(body),'conservative_summary_upper_bytes':upper,'combined_with_prior_numeric_upper_1027':upper+1027,'limits':limits,'elapsed_seconds':time.perf_counter()-started,'tests':['None/False inverse','computed/reused exact receipts and result bits','original attestation refusal poisons no summary','serialization cap refusal','ordinal/product/cardinality refusals','finite fixed histogram','actual scalar tiny route'],'qualification':'Single ordered route timings include ordinary noise, not speed comparison; isolated metadata timing excludes original numeric/authority work.'}
(D/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
