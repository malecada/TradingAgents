"""PF2: real tiny child progresses before the caller learns its Popen handle."""
import ast,hashlib,json,os,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'financial-genuine-wrapper-parent-preparation02-2026-10-04'
sys.path.insert(0,str(C))
import supervisor01 as S
import descendants01 as D
d=H/'early-census-failure';d.mkdir(mode=0o700)
progress=d/'child-progress.json';fatal=KeyboardInterrupt('opaque first census failure');calls=[];observed=None
old=D.OwnedTree.scan;first=True
def first_scan(self):
 global first
 if first:
  first=False
  deadline=time.monotonic()+1
  while not progress.exists() and time.monotonic()<deadline:time.sleep(.01)
  assert progress.exists(),'tiny child made no progress'
  raise fatal
 return old(self)
D.OwnedTree.scan=first_scan
code="import json,os,time;from pathlib import Path;Path("+repr(str(progress))+").write_text(json.dumps({'pid':os.getpid(),'opaque_progress':True}));time.sleep(5)"
try:
 try:S.supervise([sys.executable,'-B','-c',code],H,os.environ.copy(),d,2,on_spawn=lambda p:calls.append(p.pid))
 except BaseException as e:observed=e
finally:D.OwnedTree.scan=old
child=json.loads(progress.read_bytes());cleanup=json.loads((d/'owned-tree-cleanup.json').read_bytes())
checks=[]
def ok(name,v):
 if not v:raise AssertionError(name)
 checks.append(name)
ok('actual child progressed before failed census',child['opaque_progress'] is True)
ok('parent callback never receives process',calls==[])
ok('original census fatal preserved',observed is fatal)
ok('ordinary child still drained',D.pin(child['pid']) is None and cleanup['remaining_original_identities']==[])
ok('ordinary child PID retained in separate supervisor receipt',any(row['pid']==child['pid'] for row in cleanup['owned_pid_start_records']))
raw=(C/'parent01.py').read_text();t=ast.parse(raw);launch=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='launch')
spawn=next(n for n in launch.body if isinstance(n,ast.FunctionDef) and n.name=='spawned')
retainer=next(n for n in ast.walk(launch) if isinstance(n,ast.FunctionDef) and n.name=='retain_cleanup')
ok('actual parent sets handle only in callback',"child['process']=process" in ast.get_source_segment(raw,spawn))
ok('actual parent native cleanup requires callback handle',"if child['process'] is not None:cleanup_result=child_cleanup(q,args,child['process'],directory)" in ast.get_source_segment(raw,retainer))
sup=(C/'supervisor01.py').read_text()
ok('actual supervisor orders failing census before callback','tree.scan();on_spawn(process)' in sup)
out={'id':'PF2','checks':checks,'count':len(checks),'candidate_parent_sha256':hashlib.sha256(raw.encode()).hexdigest(),'candidate_supervisor_sha256':hashlib.sha256(sup.encode()).hexdigest(),'primary_exception_type':type(observed).__name__,'callback_pids':calls,'actual_tiny_child':child,'ordinary_cleanup':cleanup,'parent_cleanup_skipped_by_exact_source_condition':True,'actual_native_commands':False,'native_unit_created':False,'native_escape_demonstrated':False,'impact':'If real child dispatch has occurred before this census failure, ordinary subreaper drainage does not establish native cgroup absence, and parent skips its native cleanup. Actual native dispatch was not executed in this control.'}
(H/'PF2_WITNESS01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(len(checks),'PF2 checks passed; native cleanup scheduling gap reproduced')
