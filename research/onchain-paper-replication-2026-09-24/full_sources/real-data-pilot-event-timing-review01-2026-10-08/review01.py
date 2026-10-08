import ast,hashlib,json,tempfile,types
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'real-data-pilot-event-timing01-2026-10-08';checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
manifest=json.loads((C/'CANDIDATE01.json').read_text())
changes={'compact_matcher.py':[("self._timed('event_publication',self.log.progress,result)","self.log.progress(result)"),("self._timed('event_publication',self.log.begin,cache_key(purpose),pair.digest(identity))","self.log.begin(cache_key(purpose), pair.digest(identity))"),("self._timed('event_publication',self.log.complete,float(result.score),result.convergence,result.iterations)","self.log.complete(float(result.score), result.convergence, result.iterations)")],'stage_retention.py':[("self.matcher._timed('event_publication',self.matcher.log.progress,artifact)","self.matcher.log.progress(artifact)")],'real_pilot_partial_progress.py':[("'retention_live', 'event_publication')","'retention_live')")]}
for name,edits in changes.items():
 s=(C/name).read_text();ck('pin_'+name,hashlib.sha256(s.encode()).hexdigest()==manifest['files'][name]['candidate']['sha256']);inverse=s
 for new,old in edits:ck('unique_'+new,inverse.count(new)==1);inverse=inverse.replace(new,old,1)
 ck('inverse_'+name,inverse==(C/('baseline_'+name)).read_text())
t=ast.parse((C/'compact_matcher.py').read_text());timed=next(n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='_timed');ns={};exec(compile(ast.Module([timed],type_ignores=[]),'actual_timed','exec'),ns)
diag={};exec(compile((C/'real_pilot_partial_progress.py').read_bytes(),str(C/'real_pilot_partial_progress.py'),'exec'),diag)
policy={'schema_version':1,'max_completed_pairs':1024,'checkpoint_every_pairs':1,'checkpoint_relative':'scoring-diagnostic/progress.json'}
class Clock:
 value=0.
 def __call__(self):self.value+=0.12345678901234567;return self.value
with tempfile.TemporaryDirectory(dir=H) as tmp:
 d=diag['ScoringDiagnostic'](policy,Path(tmp),claim_sha256='a'*64,source='b'*40,clock=Clock())
 try:
  for diagnostic in (None,d):
   holder=types.SimpleNamespace(_diagnostic=diagnostic);seen=[];sentinel=object()
   def callback(*args,**kwargs):seen.append((args,kwargs));return sentinel
   ck('return_'+str(diagnostic is None),ns['_timed'](holder,'event_publication',callback,1,2,x=3) is sentinel)
   ck('arguments_'+str(diagnostic is None),seen==[((1,2),{'x':3})])
   error=RuntimeError('synthetic engineering callback failure')
   def fail():raise error
   try:ns['_timed'](holder,'event_publication',fail)
   except RuntimeError as e:ck('exception_identity_'+str(diagnostic is None),e is error)
   else:raise AssertionError('exception lost')
  ck('both_success_failure_counted',d.timings['event_publication']['calls']==2)
  for phase in diag['STARTUP_ONCE']:d.startup_enter(phase);d.startup_complete()
  for index in range(7):
   for phase in diag['STARTUP_GRAPHS']:d.startup_enter(phase,index);d.startup_complete()
  ck('all28_startup',len(d.startup)==28)
  # Metadata capacity stress only; counters not a scientific observation.
  for item in d.startup:item.update(entered_seconds=12345.678901234567,elapsed_seconds=12345.678901234567)
  for item in d.timings.values():item.update(seconds=12345.678901234567,calls=2**63-1)
  d.graph='c'*64;d.completed=d.graph_completed=1024;d.writes=2**63-1;d.matching_began=0.12345678901234567
  d.tail={'acknowledged_tail_cells':1024,'durable_tail_cells':1024,'completed_batch_cells':1024,'durability_poisoned':False}
  d._write();raw=(d.directory/'progress.json').read_bytes();size=len(raw);ck('checkpoint_fits8192',size<=8192)
 finally:d.close()
# Four exact public event call ASTs retain function and argument expressions.
count=0
for name in ('compact_matcher.py','stage_retention.py'):
 tree=ast.parse((C/name).read_text())
 for call in [n for n in ast.walk(tree) if isinstance(n,ast.Call) and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='event_publication']:
  count+=1;ck('bound_method_'+str(count),ast.unparse(call.args[1]) in ('self.log.begin','self.log.progress','self.log.complete','self.matcher.log.progress'))
ck('exactly_four_sites',count==4)
result={'decision':'accepted-source-only','files':manifest['files'],'checks':checks,'checkpoint_stress_bytes':size,'scope':'Exact full inverses preserve numeric/counter/stop logic and unchanged _timed/measure. Actual stdlib diagnostic exercised successful and failed callbacks,28startup records,long float formatting and signed63bit counters. Synthetic hashes/counters only; no authority, empirical data, scientific imports or subprocess.','qualification':'Inclusive public event validation/append/readback/conditional chunk transport; separate barriers and argument construction excluded. Overlapping timing phases cannot be added or called pure IO. No measured speedup or fresh entry release.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'checkpoint_bytes':size,'sha256':hashlib.sha256((H/'SOURCE_REVIEW01.json').read_bytes()).hexdigest()}))
