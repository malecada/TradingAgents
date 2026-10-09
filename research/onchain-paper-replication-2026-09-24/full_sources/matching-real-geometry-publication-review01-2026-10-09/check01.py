import os,resource,signal,sys,json,ast,types,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parent;P=R.parent/'matching-real-geometry-publication01-2026-10-09';G=R.parent/'matching-real-geometry-instrumentation01-2026-10-09';os.sched_setaffinity(0,{3});os.nice(10)
for k,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)):resource.setrlimit(k,(v,v))
signal.setitimer(signal.ITIMER_REAL,30);(R/'LIMITS01.json').write_text(json.dumps({'affinity':list(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'wall':signal.getitimer(signal.ITIMER_REAL)[0]})+'\n')
def module(path,ns):
 tree=ast.parse(path.read_bytes());tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and n.level)];exec(compile(tree,str(path),'exec'),ns);return types.SimpleNamespace(**ns)
g=module(G/'geometry_summary.py',{});pub=module(P/'geometry_publication.py',{k:getattr(g,k) for k in ('BINS','NAMES','LIMIT','raw','require')});trace=[]
t=ast.parse((G/'batched_numeric_reuse.py').read_bytes());cls=next(n for n in t.body if isinstance(n,ast.ClassDef));end=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='end_batch');ns={'require':g.require,'attest':lambda c:trace.append('attest')};exec(compile(ast.Module(body=[end],type_ignores=[]),'<accepted-end>','exec'),ns)
class Memo:
 def __init__(self,*a,geometry=False,max_geometry_summary_bytes=8192,**kw):
  self._geometry=g.Geometry(max_geometry_summary_bytes) if geometry else None;self.last_geometry_summary=None;self.counters={};self.occurrences=self.computed=self.reused=0;self.active=self.poisoned=self.closed=False;self.last_receipt=None
 def begin_batch(self):
  self.active=True;self._geometry_counts=(self.computed,self.reused)
  if self._geometry:self._geometry.begin(self.occurrences)
 def _current(self):trace.append('current')
 end_batch=ns['end_batch']
 def __call__(self,a,b,purpose):
  i=self.occurrences;reused=i==2;result=(.25,48,'temperature_complete');self.last_receipt={'schema_version':2,'kind':'engineering_numeric_occurrence','ordinal':i,'purpose_sha256':purpose,'mode':'reused' if reused else 'computed','origin_purpose_sha256':hashlib.sha256(b'0').hexdigest() if reused else purpose,'origin_ordinal':0 if reused else i,'score_f64_be':struct.pack('>d',.25).hex(),'iterations':48,'convergence':result[2],'cached':True,'checkpoint_attempt_delta':0,'checkpoint_reserved_byte_delta':0,'retained_cache_bytes':1024,'old_per_occurrence_execution_credit':False,'boundary_validated_batch_complete':False}
  if self._geometry:self._geometry.add(a,b,self.last_receipt)
  self.occurrences+=1;self.computed+=not reused;self.reused+=reused;return result
 def _poison(self):
  self.poisoned=True;self.active=False;self.last_geometry_summary=None
  if self._geometry:self._geometry.poison()
 def close(self):self.closed=True
namespace={'reuse':types.SimpleNamespace(NumericReuseExecutor=Memo),'geometry_publication':pub};n=module(P/'batched_numeric_execution.py',namespace)
a=types.SimpleNamespace(node_ids=range(2),edge_index=types.SimpleNamespace(shape=(2,2)));b=types.SimpleNamespace(node_ids=range(5),edge_index=types.SimpleNamespace(shape=(2,4)))
def create(name,cap=8192):
 root=R/name;root.mkdir();return root,n.NumericExecution(root,{},{},{},lambda *x:None,cells=3,batch_cells=3,max_origin_bytes=27,max_summary_bytes=cap,max_entries=4,max_retained_bytes=4096,max_key_bytes=2048,geometry=pub.POLICY)
root,e=create('healthy')
try:
 for i in range(3):e(a,b,hashlib.sha256(str(i).encode()).hexdigest())
 binding=e.finish();n.verify(root,binding);body=(root/'numeric-batches/000000000000.json').read_bytes();s=json.loads(body);assert s['geometry']['computed']==2 and s['geometry']['reused']==1 and trace==['current','attest'] and s['geometry']['metrics']['matrix_product']['sum']==30
finally:e.close()
for value in (True,{},dict(pub.POLICY,max_body_bytes=True),dict(pub.POLICY,max_body_bytes=8192)):
 try:pub.policy(value)
 except ValueError:pass
 else:raise AssertionError('invalid selected policy')
try:create('underreserved',8191)
except ValueError:assert list((R/'underreserved').iterdir())==[]
else:raise AssertionError('underreserved accepted')
root,e=create('write_failure');original=namespace['write_all'];primary=OSError('synthetic write failure')
def failed(*args):raise primary
try:
 namespace['write_all']=failed
 for i in range(2):e(a,b,hashlib.sha256(str(i).encode()).hexdigest())
 try:e(a,b,hashlib.sha256(b'2').hexdigest())
 except OSError as error:assert error is primary and e.poisoned and e.memo.poisoned and e.memo.last_geometry_summary is None and not list((root/'numeric-batches').iterdir())
 else:raise AssertionError('write failure credit')
finally:namespace['write_all']=original;e.close()
corrupt=dict(s['geometry']);corrupt['stop']=4
try:pub.check(corrupt,pub.POLICY,0,3,2,1)
except ValueError:pass
else:raise AssertionError('range corruption')
(R/'RESULT01.json').write_text(json.dumps({'metadata_connected_publication':True,'summary_bytes':len(body),'selected_body_cap':1536,'full_batch_reservation':8192,'range':[0,3],'computed':2,'reused':1,'actual_end_attestation_precedes_write':True,'original_consumer_roundtrip':True,'write_failure_primary_poison_no_summary_credit':True,'underreserved_before_files':True,'strict_policy_refusals':4,'range_corruption_refused':True,'qualification':'Actual publisher/consumer and accepted end_batch method; synthetic Memo/control only, no numerical engine/Owner.'},indent=2)+'\n')
