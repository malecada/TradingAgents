import ast,json,sys,types,os,math,hashlib,resource
assert resource.getrlimit(resource.RLIMIT_FSIZE)==(4194304,4194304)
assert resource.getrlimit(resource.RLIMIT_AS)==(268435456,268435456)
from pathlib import Path
P=Path(__file__).resolve().parent

def diagnostic(name):
 ns={'__name__':'synthetic_diagnostic'};exec(compile((P/name).read_text(),str(P/name),'exec'),ns);return ns
B=diagnostic('baseline_real_pilot_partial_progress.py');C=diagnostic('real_pilot_partial_progress.py')

def functions(name):
 tree=ast.parse((P/name).read_text());outer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
 nodes=[n for n in ast.walk(outer) if isinstance(n,ast.FunctionDef) and n.name in {'_lease_body','_lease_authority','_lease_start_metadata','_measured_lease_body','lease'}]
 return compile(ast.Module(body=nodes,type_ignores=[]),str(P/name),'exec')
BC=functions('baseline_compact_mcm.py');CC=functions('compact_mcm.py')
# Baseline None body and existing measure/_record are structurally unchanged.
def node(file,name):
 return next(n for n in ast.walk(ast.parse((P/file).read_text())) if isinstance(n,ast.FunctionDef) and n.name==name)
for method in ['measure','_record']:
 assert ast.dump(node('baseline_real_pilot_partial_progress.py',method))==ast.dump(node('real_pilot_partial_progress.py',method))
assert ast.dump(node('baseline_compact_mcm.py','_lease_body'))==ast.dump(node('compact_mcm.py','_lease_body'))
checks=[]
class MarkerFailure(Exception):pass
class Clock:
 def __init__(self):self.calls=0
 def __call__(self):self.calls+=1;return 100.+self.calls

def make_diag(ns,trace):
 d=ns['ScoringDiagnostic'].__new__(ns['ScoringDiagnostic']);d.policy={'schema_version':1,'max_completed_pairs':1024,'checkpoint_every_pairs':64,'checkpoint_relative':'scoring-diagnostic/progress.json'};d._policy=json.dumps(d.policy,sort_keys=True);d.timings={name:{'seconds':0.,'calls':0} for name in ns['DIAGNOSTIC_PHASES']};d.clock=Clock();d._refresh_count=0;d._refresh_at=0.;d._write=lambda:trace.append('write');return d

def run(ns,compiled,imported,present,enabled,failing=None):
 trace=[];failure=MarkerFailure(str(failing));d=make_diag(ns,trace) if enabled else None
 def step(name,result=None):
  trace.append(name)
  if name==failing:raise failure
  return result
 stage=types.SimpleNamespace(lease=lambda:step('stage'))
 dictionary=types.SimpleNamespace(execution=types.SimpleNamespace(_sampled_authority_lease=object()),lease=lambda:step('dictionary'))
 authority=types.ModuleType('synthetic_lease.imported_authority_lease');authority.target_lease=lambda value:step('target');sys.modules[authority.__name__]=authority
 io=types.SimpleNamespace(META_LIMIT=8192,_root=lambda *a:step('root'),_read=lambda *a:step('read',b'ok'),_json=lambda *a:step('json',b'bad' if failing=='mismatch' else b'ok'))
 def require(ok,why):
  if not ok:raise failure
 env={'__package__':'synthetic_lease','_imported':lambda _:imported,'dictionary':dictionary,'owner':types.SimpleNamespace(active=stage),'stage':stage,'require':require,'io':io,'root':'synthetic','fd':1,'start':{},'progress':types.SimpleNamespace(poll=lambda *a:step('poll')) if present else None,'log':None,'stream':None,'diagnostic':d}
 exec(compiled,env)
 try:result=env['lease']();error=None
 except BaseException as e:result=None;error=e
 assert error is None or error is failure
 return trace,result,error,d
for imported in [False,True]:
 for present in [False,True]:
  for enabled in [False,True]:
   failures=[None,('target' if imported else 'stage'),'root','read','json','mismatch']+(['dictionary'] if not imported else [])+(['poll'] if present else [])
   for fail in failures:
    old=run(B,BC,imported,present,enabled,fail);new=run(C,CC,imported,present,enabled,fail)
    assert old[0]==new[0],(imported,present,enabled,fail,old[0],new[0])
    assert old[1] is new[1] is None and (old[2] is None)==(new[2] is None)
    if enabled:
     assert new[0].count('write')==1 and new[0][-1]=='write'
     assert new[3]._refresh_count==1 and new[3].timings['lease']['calls']==1
     expected_extra=2 if fail in ('target','stage','dictionary') else 4 if fail in ('root','read','json','mismatch') or not present else 6
     assert new[3].clock.calls-old[3].clock.calls==expected_extra
     assert new[3].timings['lease_progress']['calls']==int(present and fail not in ('target','stage','dictionary','root','read','json','mismatch'))
    checks.append((imported,present,enabled,fail))
# Private method return forwarding, no refresh, finite labels and primary preservation.
trace=[];d=make_diag(C,trace);answer=object();assert d._measure_lease_subphase('lease_authority',lambda:answer) is answer and trace==[] and d._refresh_count==0
try:d._measure_lease_subphase('lease',lambda:None)
except ValueError:pass
else:raise AssertionError('invalid subphase accepted')
primary=MarkerFailure('original');clock_values=iter([10.,float('nan')]);d.clock=lambda:next(clock_values)
def fail():raise primary
try:d._measure_lease_subphase('lease_authority',fail)
except MarkerFailure as e:assert e is primary and len(e.__notes__)==1
else:raise AssertionError('lost primary')
# Extra clock validation can prevent a callback: explicitly retained limitation.
called=[];d.clock=lambda:float('nan')
try:d._measure_lease_subphase('lease_authority',lambda:called.append(True))
except ValueError:pass
else:raise AssertionError('invalid clock accepted')
assert called==[]
# Real bounded JSON publication with full28-phase startup stress, finite legal counters.
trace=[];d=make_diag(C,trace);d.clock=lambda:123456790.;d.began=0.;d.matching_began=1.;d.claim='a'*64;d.source='b'*64;d.graph='c'*64;d.completed=1024;d.graph_completed=1024;d.tail={'acknowledged_tail_cells':1024,'durable_tail_cells':1024,'completed_batch_cells':1024,'durability_poisoned':False};d.stopped=True;d.writes=9999
d.startup=[{'phase':phase,'graph_index':None,'state':'completed','entered_seconds':123456789.12345678,'elapsed_seconds':123456789.12345678} for phase in C['STARTUP_ONCE']]+[{'phase':phase,'graph_index':i,'state':'completed','entered_seconds':123456789.12345678,'elapsed_seconds':123456789.12345678} for i in range(7) for phase in C['STARTUP_GRAPHS']];d._startup_active=None;d.startup[-1].update(state='failed',failure_type='E'*64)
for v in d.timings.values():v.update(seconds=123456789.12345678,calls=2**63-1)
folder=P/'stress-checkpoint02';folder.mkdir(exist_ok=False);d.fd=os.open(folder,os.O_RDONLY|os.O_DIRECTORY)
try:C['ScoringDiagnostic']._write(d)
finally:os.close(d.fd)
size=(folder/'progress.json').stat().st_size;assert size<=8192
receipt={'status':'PASS','callback_cases':len(checks),'baseline_body_measure_record_unchanged':True,'same_body_order_primary_exception_and_single_outer_refresh':True,'private_return_forwarding':True,'invalid_clock_additional_failure_boundary_demonstrated':True,'extra_clock_reads_success':{'no_progress':4,'with_progress':6},'stress_bytes':size,'limit_bytes':8192,'numpy_imported':'numpy' in sys.modules,'nice':os.getpriority(os.PRIO_PROCESS,0),'affinity':sorted(os.sched_getaffinity(0)),'rlimit_fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'rlimit_as':resource.getrlimit(resource.RLIMIT_AS)}
assert not receipt['numpy_imported'];(P/'RESULT02.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
