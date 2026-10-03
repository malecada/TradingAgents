"""PF2 exact supervisor RED/GREEN, real progressed children, no native claims."""
import ast,importlib.util,json,os,sys,time
from pathlib import Path
import descendants01 as D
H=Path(__file__).resolve().parent;checks=[];outcomes=[]
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def load(name):
 spec=importlib.util.spec_from_file_location('tiny_'+name.replace('-','_'),H/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
for name,label in [('baseline-supervisor01.py','red'),('supervisor01.py','green')]:
 S=load(name);d=H/('first-census-'+label);d.mkdir(mode=0o700);progress=d/'progress.json';fatal=KeyboardInterrupt('first owned scan');old=D.OwnedTree.scan;calls=[];state={'first':True};observed=None
 def scan(self):
  if state['first']:
   state['first']=False;deadline=time.monotonic()+2
   while not progress.exists() and time.monotonic()<deadline:time.sleep(.01)
   check(label+' real child progressed',progress.exists());raise fatal
  return old(self)
 D.OwnedTree.scan=scan
 code='import os,json,time;from pathlib import Path;Path('+repr(str(progress))+').write_text(json.dumps({"pid":os.getpid()}));time.sleep(8)'
 try:
  try:S.supervise([sys.executable,'-B','-c',code],H,os.environ.copy(),d,4,on_spawn=lambda p:calls.append(p))
  except BaseException as error:observed=error
 finally:D.OwnedTree.scan=old
 pid=json.loads(progress.read_bytes())['pid'];cleanup=json.loads((d/'owned-tree-cleanup.json').read_bytes())
 check(label+' first actual fatal preserved',observed is fatal);check(label+' actual child absent',D.pin(pid) is None and cleanup['remaining_original_identities']==[])
 check(label+' handle disposition',calls==[] if label=='red' else len(calls)==1 and calls[0].pid==pid and calls[0].returncode is not None)
 outcomes.append({'label':label,'actual_pid':pid,'parent_handles':[p.pid for p in calls],'actual_child_exits':[p.returncode for p in calls],'fatal_identity_preserved':observed is fatal,'cleanup':cleanup,'actual_native_commands':False})
# A failing callback metadata publication must still leave the actual handle stored.
t=ast.parse((H/'parent01.py').read_bytes());launch=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='launch');spawn=next(n for n in launch.body if isinstance(n,ast.FunctionDef) and n.name=='spawned')
check('genuine parent first callback statement stores handle',isinstance(spawn.body[0],ast.Assign) and ast.unparse(spawn.body[0])=="child['process'] = process")
retainer=next(n for n in ast.walk(launch) if isinstance(n,ast.FunctionDef) and n.name=='retain_cleanup')
check('unchanged genuine parent schedules native cleanup whenever handle exists',"if child['process'] is not None:\n        cleanup_result = child_cleanup(q, args, child['process'], directory)" in ast.unparse(retainer))
# Exercise source-exact callback assignment before a failing opaque diagnostic,
# with the real completed Popen object; no synthetic receipt is published.
child={'process':None};actual=calls[0];env={'child':child,'process':actual};exec(compile(ast.fix_missing_locations(ast.Module(body=[spawn.body[0]],type_ignores=[])),'<actual-handle-assignment>','exec'),env)
check('actual returned handle retained before diagnostic failure',child['process'] is actual)
(H/'CHECKS02.json').write_text(json.dumps({'checks':checks,'count':len(checks),'outcomes':outcomes,'native_dispatch_tested':False,'scope':'real ordinary children only; genuine native cleanup route retained and source-joined'},indent=2)+'\n');print(len(checks),'PF2 checks passed')
