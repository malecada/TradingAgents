import os,resource,signal,sys,json,ast,types,hashlib,struct
from pathlib import Path
R=Path(__file__).resolve().parent;P=R.parent/'pilot-binding-lease-timing-publication01-2026-10-09';G=R.parent/'matching-real-geometry-instrumentation01-2026-10-09';os.sched_setaffinity(0,{3});os.nice(10)
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

import contextlib,time
mt=ast.parse((P/'matching_owner.py').read_bytes());nodes=[]
for x in mt.body:
 if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and (t.id.startswith('_LEASE_TIMING_') or t.id=='BINDING_TIMING_POLICY') for t in x.targets):nodes.append(x)
 elif isinstance(x,ast.ClassDef) and x.name=='BindingLeaseTiming':nodes.append(x)
 elif isinstance(x,ast.FunctionDef) and x.name in ('binding_timing_policy','binding_timing_counters'):nodes.append(x)
 elif isinstance(x,ast.ClassDef) and x.name=='Binding':
  nodes.append(ast.ClassDef(name='Binding',bases=[],keywords=[],body=[z for z in x.body if isinstance(z,ast.FunctionDef) and z.name=='lease'],decorator_list=[]))
mn={'time':time,'contextmanager':contextlib.contextmanager,'require':g.require,'json':json,'Path':Path,'metadata':lambda *a:({},'pin')};exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<actual-timing>','exec'),mn);matching=types.SimpleNamespace(**mn)
journal=R/'journal';journal.mkdir();directory=journal/'one';directory.mkdir();bound=matching.Binding();bound._run=types.SimpleNamespace(_active=lambda:None,admission=types.SimpleNamespace(root=R));bound.record={'journal_directory':str(directory)};bound._ancestry_arguments=None;bound._snapshots={'sample':'pin'};bound._guard=lambda:None
# Metadata-only Owner substitute; actual select method and Binding.lease run, no real Owner authority.
ot=ast.parse((P/'compact_owner.py').read_bytes());oc=next(x for x in ot.body if isinstance(x,ast.ClassDef) and x.name=='Owner');select=next(x for x in oc.body if isinstance(x,ast.FunctionDef) and x.name=='select_binding_timing');on={'matching_owner':matching,'require':g.require};exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Owner',bases=[],keywords=[],body=[select],decorator_list=[])],type_ignores=[])),'<metadata-owner-shell>','exec'),on);Owner=on['Owner'];owner=Owner();owner.bound=bound;obs=owner.select_binding_timing(matching.BINDING_TIMING_POLICY)
def current(self):bound.lease(observer=obs);trace.append('current')
Memo._current=current
class Strip(ast.NodeTransformer):
 def visit_ImportFrom(self,n):return None if n.level else n
nt=Strip().visit(ast.parse((P/'batched_numeric_execution.py').read_bytes()));namespace={'reuse':types.SimpleNamespace(NumericReuseExecutor=Memo),'geometry_publication':pub,'matching_owner':matching,'compact_owner':types.SimpleNamespace(Owner=Owner)};exec(compile(nt,'<actual-publication>','exec'),namespace);N=namespace['NumericExecution'];root=R/'selected';root.mkdir();ex=N(root,{},{},{},lambda *x:None,cells=3,batch_cells=3,max_origin_bytes=27,max_summary_bytes=8192,max_entries=4,max_retained_bytes=4096,max_key_bytes=2048,geometry=pub.POLICY,binding_timing=matching.BINDING_TIMING_POLICY,binding_owner=owner)
a=types.SimpleNamespace(node_ids=range(2),edge_index=types.SimpleNamespace(shape=(2,2)));b=types.SimpleNamespace(node_ids=range(3),edge_index=types.SimpleNamespace(shape=(2,3)))
try:
 for i in range(3):ex(a,b,hashlib.sha256(str(i).encode()).hexdigest())
 frozen=ex._timing_snapshot;before=json.loads(frozen);bound.lease(observer=obs);binding=ex.finish();assert ex._timing_snapshot is frozen and binding['counters']['binding_first_guard_calls']==before['binding_first_guard_calls']==1 and obs.snapshot()['binding_first_guard_calls']==2
 namespace['verify'](root,binding);summary=json.loads((root/'numeric-batches/000000000000.json').read_bytes());assert summary['geometry']['computed']==2 and summary['geometry']['reused']==1 and len(frozen)<=640
finally:ex.close()
refusals=[]
for mode in ('forged','clock','counter'):
 fresh=matching.BindingLeaseTiming(bound)
 if mode=='forged':fresh=types.SimpleNamespace()
 elif mode=='clock':fresh.clock=lambda:0
 else:fresh._totals=(1,)*12
 try:bound.lease(observer=fresh)
 except (ValueError,AttributeError):refusals.append(mode)
 else:raise AssertionError(mode)
primary=RuntimeError('original guard failure');fresh=matching.BindingLeaseTiming(bound)
def fail():raise primary
bound._guard=fail
try:bound.lease(observer=fresh)
except RuntimeError as error:assert error is primary and fresh.snapshot()['binding_first_guard_failures']==1 and fresh.snapshot()['binding_journal_calls']==0
else:raise AssertionError('guard primary lost')
for invalid in (False,dict(matching.BINDING_TIMING_POLICY,max_body_bytes=641),dict(matching.BINDING_TIMING_POLICY,max_body_bytes=True)):
 try:matching.binding_timing_policy(invalid)
 except ValueError:pass
 else:raise AssertionError('policy widened')
(R/'RESULT01.json').write_text(json.dumps({'actual_selected_file_publication_consumer':True,'geometry_and_timing_body_bytes':(root/'numeric-batches/000000000000.json').stat().st_size,'frozen_timing_bytes':len(frozen),'frozen_first_guard_calls':before['binding_first_guard_calls'],'later_observer_calls':obs.snapshot()['binding_first_guard_calls'],'final_snapshot_samebytes':True,'guard_primary_identity_preserved':True,'no_later_phase_after_guardfailure':True,'refusals':refusals,'policy_refusals':3,'qualification':'Extracted actual Binding lease/observer, Owner selection and publisher; explicit metadata-only class shell, not real Owner/authority.'},indent=2)+'\n')
