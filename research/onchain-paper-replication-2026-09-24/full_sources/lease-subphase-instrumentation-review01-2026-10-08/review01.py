import ast,hashlib,json,os,resource,tempfile,types
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'lease-subphase-instrumentation01-2026-10-08';os.sched_setaffinity(0,{2});os.nice(10);resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
def require(x,m):
 if not x:raise ValueError(m)
phases={'lease_authority','lease_start_metadata','lease_progress'}
class Inverse(ast.NodeTransformer):
 def visit_FunctionDef(self,n):
  if n.name in {'_lease_authority','_lease_start_metadata','_measured_lease_body','_measure_lease_subphase','_record_lease_subphase'}:return None
  return self.generic_visit(n)
 def visit_Name(self,n):
  if n.id=='_measured_lease_body':n.id='_lease_body'
  return n
 def visit_Assign(self,n):
  if any(isinstance(x,ast.Name) and x.id=='DIAGNOSTIC_PHASES' for x in n.targets):n.value.elts=[x for x in n.value.elts if x.value not in phases]
  return self.generic_visit(n)
pins={'compact_mcm.py':'64ea0371c65b097cbebc56ac666e7bc3bb6600651799f3cc6bc4491b8644c530','real_pilot_partial_progress.py':'d424e92edba6e0d7ae3537649f3ebda228b3d9c1498fbe878530d31b519d64f7'}
for name,pin in pins.items():
 raw=(C/name).read_bytes();ck('pin_'+name,hashlib.sha256(raw).hexdigest()==pin);ck('full_AST_inverse_'+name,ast.dump(Inverse().visit(ast.parse(raw)))==ast.dump(ast.parse((C/('baseline_'+name)).read_bytes())))
ns={};exec(compile((C/'real_pilot_partial_progress.py').read_bytes(),'actual_stdlib_diagnostic','exec'),ns)
tree=ast.parse((C/'compact_mcm.py').read_text());names={'_lease_body','_lease_authority','_lease_start_metadata','_measured_lease_body','lease'}
# Select direct nested producer closures only; no Produced.lease method.
body=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and any(isinstance(x,ast.FunctionDef) and x.name=='_lease_body' for x in n.body))
funcs=[n for n in body.body if isinstance(n,ast.FunctionDef) and n.name in names]
class Strip(ast.NodeTransformer):
 def visit_ImportFrom(self,n):return None
policy={'schema_version':1,'max_completed_pairs':1024,'checkpoint_every_pairs':64,'checkpoint_relative':'scoring-diagnostic/progress.json'}
for imported in (False,True):
 for progress_present in (False,True):
  with tempfile.TemporaryDirectory(dir=H) as tmp:
   now=[0.];clockcalls=[0]
   def clock():clockcalls[0]+=1;return now[0]
   diagnostic=ns['ScoringDiagnostic'](policy,Path(tmp),claim_sha256='a'*64,source='b'*40,clock=clock)
   try:
    for fail_at in (None,'authority','metadata','progress'):
     if fail_at=='progress' and not progress_present:continue
     events=[];error=RuntimeError('synthetic '+str(fail_at));writes=[]
     def hit(name):
      events.append(name)
      if name==fail_at:raise error
     stage=types.SimpleNamespace(lease=lambda:hit('authority'));dictionary=types.SimpleNamespace(execution=types.SimpleNamespace(_sampled_authority_lease=object()),lease=lambda:hit('dictionary'))
     io=types.SimpleNamespace(_root=lambda *a:hit('metadata'),_read=lambda *a:b'x',_json=lambda x:b'x',META_LIMIT=8192)
     g=dict(_imported=lambda d:imported,dictionary=dictionary,owner=types.SimpleNamespace(active=stage),stage=stage,target_lease=lambda d:hit('authority'),require=require,io=io,root=None,fd=None,start={},progress=types.SimpleNamespace(poll=lambda *a:hit('progress')) if progress_present else None,log=object(),stream=object(),diagnostic=diagnostic)
     exec(compile(ast.fix_missing_locations(Strip().visit(ast.Module(funcs,type_ignores=[]))),'actual_lease_closures','exec'),g)
     # None path remains original and establishes callback trace for this case.
     g['diagnostic']=None
     try:g['lease']()
     except RuntimeError as e:ck('none_original_error_'+str((imported,progress_present,fail_at)),e is error)
     original=list(events);events.clear();g['diagnostic']=diagnostic;now[0]+=60;before=clockcalls[0];original_write=diagnostic._write
     def write():writes.append(list(events));original_write()
     diagnostic._write=write
     try:g['lease']()
     except RuntimeError as e:ck('same_primary_'+str((imported,progress_present,fail_at)),e is error)
     else:ck('healthy_return_'+str((imported,progress_present,fail_at)),fail_at is None)
     diagnostic._write=original_write
     ck('same_order_no_later_spans_'+str((imported,progress_present,fail_at)),events==original)
     ck('one_outer_refresh_'+str((imported,progress_present,fail_at)),writes==[events])
     if fail_at is None:ck('extra_clock_reads_'+str((imported,progress_present)),clockcalls[0]-before==(9 if progress_present else 7)) # outer2 + sub6/4 + publication summary1
   finally:diagnostic.close()
# Invalid-clock behavior is explicitly changed by extra reads, not universally equivalent.
with tempfile.TemporaryDirectory(dir=H) as tmp:
 d=ns['ScoringDiagnostic'](policy,Path(tmp),claim_sha256='a'*64,source='b'*64,clock=lambda:0.)
 try:
  primary=ValueError('original callback')
  def failure():d.clock=lambda:float('nan');raise primary
  try:d._measure_lease_subphase('lease_authority',failure)
  except ValueError as e:ck('primary_over_invalid_record_clock',e is primary and bool(e.__notes__))
  else:raise AssertionError('missing primary')
 finally:d.close()
x={'decision':'accepted-source-only','source_hashes':pins,'checks':checks,'qualification':'Exact whole-module AST inverse preserves original body/measure/_record/numerical logic. Isolated real producer closures and stdlib diagnostic show healthy order/results, same primary callback error and no later body span, one outer publication only. Extra4/6clock reads can add diagnostic failures on invalid clocks/aggregate overflow; no universal failure-trace equivalence or runtime-saving claim. No scientific imports/arrays/Owner/admission/native/network/Main edits. Existing finite stress receipt reused separately.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'checks':len(checks),'sha256':hashlib.sha256((H/'SOURCE_REVIEW01.json').read_bytes()).hexdigest()}))
