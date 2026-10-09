"""Actual publisher and consumer source; metadata-only memo/authority doubles."""
import os,resource,signal,json,sys,time,ast,types,hashlib,struct,copy
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];S=R/'tradingagents/research/onchain_replication';G=D.parent/'matching-real-geometry-instrumentation01-2026-10-09'
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(r,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
limits={'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'as':resource.getrlimit(resource.RLIMIT_AS),'fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'cpu':resource.getrlimit(resource.RLIMIT_CPU),'wall_timer':signal.getitimer(signal.ITIMER_REAL),'threads':{k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}}
assert limits['affinity']==[3] and limits['nice']==10 and limits['as']==(536870912,)*2 and limits['fsize']==(4194304,)*2
(D/'LIMITER02.json').write_text(json.dumps(limits,indent=2)+'\n');started=time.perf_counter();W=D/'fixtures02';W.mkdir()
checks=[]
changes=json.loads((D/'CHANGES01.json').read_text())
for name,edits in changes.items():
 text=(D/name).read_text()
 for a,b in reversed(edits):assert text.count(b)==1;text=text.replace(b,a)
 assert text==(S/name).read_text();assert ast.dump(ast.parse(text))==ast.dump(ast.parse((S/name).read_text()))
checks.append('both candidate modules literal and AST inverse')
geom=types.ModuleType('geometry');exec(compile((G/'geometry_summary.py').read_text(),str(G/'geometry_summary.py'),'exec'),geom.__dict__)
pub=types.ModuleType('publication');pub.__dict__.update({k:getattr(geom,k) for k in ('BINS','NAMES','LIMIT','raw','require')});tree=ast.parse((D/'geometry_publication.py').read_text());tree.body=[n for n in tree.body if not isinstance(n,ast.ImportFrom)];exec(compile(tree,'actual_geometry_publication','exec'),pub.__dict__)
# Actual frozen end_batch source, with explicit metadata-only authority doubles.
ct=ast.parse((G/'batched_numeric_reuse.py').read_text());cl=next(n for n in ct.body if isinstance(n,ast.ClassDef));end=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='end_batch');ns={'require':geom.require,'attest':lambda counters:trace.append('attest')};exec(compile(ast.Module(body=[end],type_ignores=[]),'actual_end_batch','exec'),ns)
trace=[];failure=None
class Memo:
 def __init__(self,*args,geometry=False,max_geometry_summary_bytes=8192,**kw):
  self._geometry=geom.Geometry(max_geometry_summary_bytes) if geometry else None;self.last_geometry_summary=None;self.counters={'source_guard_calls':0};self.occurrences=self.computed=self.reused=0;self.active=self.poisoned=self.closed=False;self.last_receipt=None
 def _current(self):
  trace.append('current')
  if failure=='attest':raise ValueError('fixture currentness refusal')
 def begin_batch(self):
  self.active=True
  if self._geometry:self._geometry_counts=(self.computed,self.reused);self.last_geometry_summary=None;self._geometry.begin(self.occurrences)
 end_batch=ns['end_batch']
 def __call__(self,a,b,purpose):
  i=self.occurrences;mode='computed' if i==0 else 'reused';v=(.5,48,'temperature_complete')
  self.last_receipt={'schema_version':2,'kind':'engineering_numeric_occurrence','ordinal':i,'purpose_sha256':purpose,'mode':mode,'origin_purpose_sha256':purpose if i==0 else hashlib.sha256(b'0').hexdigest(),'origin_ordinal':0,'score_f64_be':struct.pack('>d',.5).hex(),'iterations':48,'convergence':v[2],'cached':True,'checkpoint_attempt_delta':0,'checkpoint_reserved_byte_delta':0,'retained_cache_bytes':1024,'old_per_occurrence_execution_credit':False,'boundary_validated_batch_complete':False}
  if self._geometry:self._geometry.add(a,b,self.last_receipt)
  self.occurrences+=1;self.computed+=i==0;self.reused+=i!=0;return v
 def _poison(self):
  self.poisoned=True;self.active=False;self.last_geometry_summary=None
  if self._geometry:self._geometry.poison()
 def close(self):self.closed=True

def module(path):
 t=ast.parse(path.read_text());t.body=[n for n in t.body if not (isinstance(n,ast.ImportFrom) and n.level)]
 n={'reuse':types.SimpleNamespace(NumericReuseExecutor=Memo),'geometry_publication':pub};exec(compile(t,str(path),'exec'),n);n['time']=types.SimpleNamespace(perf_counter=lambda:1.0);return types.SimpleNamespace(**n)
old=module(S/'batched_numeric_execution.py');new=module(D/'batched_numeric_execution.py')
a=types.SimpleNamespace(node_ids=('a','b','c'),edge_index=types.SimpleNamespace(shape=(2,3)));b=types.SimpleNamespace(node_ids=('a','b','c','d'),edge_index=types.SimpleNamespace(shape=(2,4)))
def create(name,mod,geometry='omit',allowance=16384):
 root=W/name;root.mkdir();kw={} if geometry=='omit' else {'geometry':geometry}
 return root,mod.NumericExecution(root,{}, {}, {},lambda *x:None,cells=4,batch_cells=2,max_origin_bytes=36,max_summary_bytes=allowance,max_entries=8,max_retained_bytes=65536,max_key_bytes=32768,**kw)
outputs={}
for name,mod,selection in [('baseline',old,'omit'),('none',new,None),('false',new,False),('selected',new,pub.POLICY)]:
 root,ex=create(name,mod,selection)
 try:
  for i in range(4):ex(a,b,hashlib.sha256(str(i).encode()).hexdigest())
  binding=ex.finish();verified=mod.verify(root,binding);assert verified==old.verify(root,binding)
  summaries=[(root/'numeric-batches'/f'{i:012d}.json').read_bytes() for i in range(2)];outputs[name]=summaries
  if name=='selected':
   assert binding['geometry']==pub.POLICY
   for i,body in enumerate(summaries):
    value=json.loads(body);assert value['geometry']['start']==2*i and value['geometry']['stop']==2*i+2 and value['geometry']['end_batch_attested'] is True
   (D/'SELECTED_BINDING02.json').write_text(json.dumps(binding,indent=2)+'\n')
  else:assert 'geometry' not in binding
 finally:ex.close()
assert outputs['baseline']==outputs['none']==outputs['false'];checks.append('actual publisher None/False identical summary bytes; original consumer accepts selected bodies and exact hash closure')
assert trace==['current','attest']*8;checks.append('actual frozen end_batch checks precede each publication')
# Exact selected policy path validation from adapter, no Owner fabricated/imported.
t=ast.parse((D/'compact_mcm_batched.py').read_text());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('selected','validate')];vns={'require':geom.require,'geometry_publication':pub,'FORMAT':'ordered-mcm-batch-closure-v2'};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_adapter_validate','exec'),vns)
# Use public actual policy metadata as shape, not an authority object.
paths=list((D.parent/'real-data-pilot-full28-input-drafts01-2026-10-09').glob('**/mcm*.json')) if (D.parent/'real-data-pilot-full28-input-drafts01-2026-10-09').exists() else []
bounds={'format':vns['FORMAT'],'authority_boundaries':'entry-batch-checkpoint-final','batch_cells':2,'max_journal_bytes':10000,'max_body_bytes':1024,'max_closure_token_bytes':336,'max_checkpoint_bytes':1,'retention':'local-v2','max_spool_bytes':16,'max_offload_metadata_bytes':1,'max_offload_entries':1,'max_offload_anchor_bytes':0,'execution':{'route':'immutable-input-session+exact-byte-reuse-v1','max_entries':8,'max_retained_bytes':65536,'max_key_bytes':32768,'max_origin_bytes':36,'max_summary_bytes':16384,'geometry':dict(pub.POLICY)}}
policy={'schema_version':5,'max_entries':1,'max_workflow_metadata_bytes':1,'numeric':{},'batched':bounds};assert vns['validate'](policy,4) is bounds
for bad in [False,{'format':pub.FORMAT,'max_body_bytes':True},{'format':pub.FORMAT,'max_body_bytes':1537}]:
 q=copy.deepcopy(policy);q['batched']['execution']['geometry']=bad
 try:vns['validate'](q,4)
 except ValueError:pass
 else:raise AssertionError('policy accepted')
checks.append('actual adapter explicit policy validation and typed cap refusals')
# Declared total bound rejected before any numeric file creation.
root=W/'underreserved';root.mkdir()
try:new.NumericExecution(root,{}, {}, {},lambda *x:None,cells=4,batch_cells=2,max_origin_bytes=36,max_summary_bytes=16383,max_entries=8,max_retained_bytes=65536,max_key_bytes=32768,geometry=pub.POLICY)
except ValueError:pass
else:raise AssertionError('reservation accepted')
assert not list(root.iterdir());checks.append('total summary reservation refusal before file allocation')
root,ex=create('guard_refusal',new,pub.POLICY);failure='attest'
try:
 ex(a,b,hashlib.sha256(b'0').hexdigest())
 try:ex(a,b,hashlib.sha256(b'1').hexdigest())
 except ValueError:pass
 else:raise AssertionError('guard accepted')
 assert ex.poisoned and not list((root/'numeric-batches').iterdir()) and (root/'numeric-origins.bin').stat().st_size==0
finally:failure=None;ex.close()
checks.append('actual end_batch refusal before any origin/summary publication')
value=json.loads(outputs['selected'][0])['geometry'];bad=copy.deepcopy(value);bad['computed']=0
try:pub.check(bad,pub.POLICY,0,2,1,1)
except ValueError:pass
else:raise AssertionError('geometry mode mismatch accepted')
# Original storage consumer must reject on-disk extra byte / currentness drift.
root=W/'selected';binding=json.loads((D/'SELECTED_BINDING02.json').read_text());path=root/'numeric-batches/000000000000.json';original=path.read_bytes();path.write_bytes(original+b' ')
for mod in (old,new):
 try:mod.verify(root,binding)
 except ValueError:pass
 else:raise AssertionError('corrupt summary accepted')
checks.append('new semantic mismatch and original/new on-disk mutation refusals; corrupted fixture retained')
result={'status':'PASS_METADATA_ONLY_NO_AUTHORITY','checks':checks,'selected_body_bytes':[len(x) for x in outputs['selected']],'legacy_body_bytes':[len(x) for x in outputs['baseline']],'per_batch_reserved_total':8192,'whole_101559_batch_reserved_total':101559*8192,'no_extra_files_per_batch':True,'limits':limits,'elapsed_seconds':time.perf_counter()-started,'fixture_qualification':'Actual publisher/verifier and frozen memo end method; metadata-only Memo/_current/attest doubles, no actual numerical matching or genuine Owner/Binding authority.'}
(D/'RESULT02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
