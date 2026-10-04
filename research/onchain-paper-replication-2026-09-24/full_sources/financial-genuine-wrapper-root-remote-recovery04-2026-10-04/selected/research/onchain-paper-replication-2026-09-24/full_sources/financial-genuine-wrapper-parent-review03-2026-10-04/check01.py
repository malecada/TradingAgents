"""Independent exact Parent03 inverse and original PF1/PF2 RED/GREEN controls."""
import ast,ctypes,hashlib,importlib.util,json,os,signal,stat,sys,time
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;B=H.parent/'financial-genuine-wrapper-parent-preparation02-2026-10-04';C=H.parent/'financial-genuine-wrapper-parent-preparation03-2026-10-04';V=H.parent/'financial-genuine-wrapper-parent-review02-2026-10-04'
sys.path.insert(0,str(C))
import supervisor01 as new
import descendants01 as D
import recovery04 as R
import parent01 as P
spec=importlib.util.spec_from_file_location('baseline_supervisor',B/'supervisor01.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
checks=[];matrix=[];outcomes=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ok('candidate parent pin',sha(C/'parent01.py')=='3546fadac261bf1853b0139466c296c351e568b3842658d2984ac0aa5bdb8843')
ok('candidate supervisor pin',sha(C/'supervisor01.py')=='551850d2af69baf48bc582f8fc7da7e7eba931c2b58abec4987a09e9ec270db0')
ok('candidate manifest pin',sha(C/'MANIFEST01.json')=='3c6c8ef58e93de1a314a105b77e0b452267494487c971c73f925f98615ad78de')
ok('previous review immutable',sha(V/'MANIFEST01.json')=='d5111dae5d8d7d896779306b24b5ab3621c831aa0c24b2e88cf9b9b356fb4ec3')
ok('previous candidate immutable',sha(B/'MANIFEST01.json')=='3f209f1794ace2c928d49fd83d5f51ce2330419971bdbf1dd4aea05857bf3270')
rows=json.loads((C/'MANIFEST01.json').read_bytes())['entries']
ok('exact61 typed members',len(rows)==61 and len({r['path'] for r in rows})==61)
ok('full candidate inventory exact',{p.relative_to(C).as_posix() for p in C.rglob('*')}=={r['path'] for r in rows}|{'MANIFEST01.json'})
for r in rows:
 p=C/r['path'];s=p.lstat();ok('candidate mode '+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
 if r['type']=='file':ok('candidate body '+r['path'],stat.S_ISREG(s.st_mode) and s.st_size==r['size'] and sha(p)==r['sha256'])
 else:ok('candidate directory '+r['path'],r['type']=='directory' and stat.S_ISDIR(s.st_mode))
changes={'parent01.py':(b' finally:os.close(fd)',b' finally:R._cleanup((lambda:os.close(fd),))'),'supervisor01.py':(b'  tree.scan();on_spawn(process)',b'  on_spawn(process);tree.scan()')}
for name,(before,after) in changes.items():
 a=(B/name).read_bytes();b=(C/name).read_bytes()
 ok('one exact substitution '+name,a.count(before)==1 and b.count(after)==1 and a.replace(before,after)==b)
 inverse=b.replace(after,before)
 ok('whole byte inverse '+name,inverse==a)
 ok('whole AST inverse '+name,ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False))
unchanged=('descendants01.py','recovery04.py','owned_io.py','bounded_git01.py','PROTOCOL_PINS01.json','REQUEST_TEMPLATE01.json','original-job.py','original-resources.py')
for name in unchanged:ok('unchanged inherited '+name,(C/name).read_bytes()==(B/name).read_bytes())
for r in json.loads((C/'ORIGINS01.json').read_bytes()):
 p=Path(r['path']);ok('actual origin '+r['target'],sha(p)==r['sha256'] and p.resolve()==(B/r['target']).resolve())
for name,pin in json.loads((C/'PROTOCOL_PINS01.json').read_bytes()).items():ok('actual original source unchanged '+name,sha(P.CAP/name)==pin==sha(C/('original-'+Path(name).name)))
def seam(directory):
 raw=(directory/'parent01.py').read_text();t=ast.parse(raw);fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='launch')
 return next(n for n in fn.body if isinstance(n,ast.Try) and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and c.func.attr=='fsync' for c in ast.walk(n)))
def fsync_case(node,primary,secondary):
 fd=os.open(H,os.O_RDONLY|os.O_DIRECTORY);events=[];error=None
 def fsync(n):
  os.fsync(n);events.append('fsync')
  if primary is not None:raise primary
 def close(n):
  os.close(n);events.append('close')
  if secondary is not None:raise secondary
 try:exec(compile(ast.Module(body=[node],type_ignores=[]),'exact-parent-seam','exec'),{'fd':fd,'os':SimpleNamespace(fsync=fsync,close=close),'R':R})
 except BaseException as e:error=e
 ok('close called once '+str(len(matrix)),events==['fsync','close'])
 try:os.fstat(fd)
 except OSError:pass
 else:raise AssertionError('descriptor not closed')
 return error
fatal=KeyboardInterrupt('original PF1');secondary=OSError('later PF1');red=fsync_case(seam(B),fatal,secondary)
ok('PF1 baseline RED exact witness',red is secondary and red.__context__ is fatal)
green=fsync_case(seam(C),fatal,secondary);ok('PF1 successor GREEN same original fatal',green is fatal)
kinds=[None,ValueError,MemoryError,KeyboardInterrupt,SystemExit]
for a in kinds:
 for b in kinds:
  p=None if a is None else a('opaque primary');q=None if b is None else b('opaque cleanup');observed=fsync_case(seam(C),p,q)
  fatalp=isinstance(p,(MemoryError,KeyboardInterrupt,SystemExit));fatalq=isinstance(q,(MemoryError,KeyboardInterrupt,SystemExit))
  if fatalp:valid=observed is p
  elif fatalq:valid=observed is q
  elif q is None:valid=observed is p
  else:valid=type(observed).__name__=='CleanupFailure' and observed.failures==tuple(x for x in (p,q) if x is not None)
  ok('independent fatal precedence '+str(a)+' / '+str(b),valid)
  matrix.append({'primary':None if p is None else type(p).__name__,'cleanup':None if q is None else type(q).__name__,'observed':None if observed is None else type(observed).__name__,'primary_object_preserved':observed is p if p is not None else None,'cleanup_object_selected':observed is q if q is not None else None})
def state():
 value=ctypes.c_int();assert ctypes.CDLL(None).prctl(37,ctypes.byref(value),0,0,0)==0;return value.value
initial=state()
def census_case(label,module):
 d=H/label;d.mkdir(mode=0o700);progress=d/'progress.json';handle={};first=True;fatal=KeyboardInterrupt('opaque census');error=None;scan=D.OwnedTree.scan
 def census(self):
  nonlocal first
  if first:
   first=False;until=time.monotonic()+1
   while not progress.exists() and time.monotonic()<until:time.sleep(.01)
   assert progress.exists();raise fatal
  return scan(self)
 D.OwnedTree.scan=census
 code="import json,os,time;from pathlib import Path;Path("+repr(str(progress))+").write_text(json.dumps({'pid':os.getpid(),'opaque_progress':True}));time.sleep(5)"
 try:
  try:module.supervise([sys.executable,'-B','-c',code],H,os.environ.copy(),d,2,on_spawn=lambda p:handle.update(process=p))
  except BaseException as e:error=e
 finally:D.OwnedTree.scan=scan
 child=json.loads(progress.read_bytes());cleanup=json.loads((d/'owned-tree-cleanup.json').read_bytes())
 ok(label+' same first fatal',error is fatal)
 ok(label+' actual progressed child absent',child['opaque_progress'] is True and D.pin(child['pid']) is None)
 ok(label+' cleanup empty',cleanup['remaining_original_identities']==[])
 ok(label+' subreaper restored',state()==initial)
 retained=handle.get('process');outcomes.append({'name':label,'actual_child_pid':child['pid'],'callback_pid':None if retained is None else retained.pid,'callback_process_exit':None if retained is None else retained.returncode,'error_type':type(error).__name__,'cleanup':cleanup})
 return retained
ok('PF2 baseline RED callback missed',census_case('PF2-red',old) is None)
retained=census_case('PF2-green',new);ok('PF2 GREEN retains actual reaped handle',retained is not None and retained.returncode is not None)
# Actual parent source proves assignment is callback's first statement and
# native-cleanup retainer consumes this exact handle; no native API is executed.
t=ast.parse((C/'parent01.py').read_text());launch=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='launch');spawn=next(n for n in launch.body if isinstance(n,ast.FunctionDef) and n.name=='spawned')
ok('callback stores real handle before metadata',ast.dump(spawn.body[0],include_attributes=False)==ast.dump(ast.parse("child['process']=process").body[0],include_attributes=False))
retainer=next(n for n in ast.walk(launch) if isinstance(n,ast.FunctionDef) and n.name=='retain_cleanup')
ok('retainer source unchanged',ast.dump(retainer,include_attributes=False)==ast.dump(next(n for n in ast.walk(ast.parse((B/'parent01.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name=='retain_cleanup'),include_attributes=False))
# Fresh descendant control retains actual failure status and orphan ancestry.
d=H/'detached-descendant';d.mkdir(mode=0o700)
code="""import os,signal,time
if os.fork()==0:
 os.setsid()
 if os.fork()==0:
  signal.signal(signal.SIGTERM,signal.SIG_IGN)
  print('opaque descendant',os.getpid(),flush=True)
  time.sleep(8)
  os._exit(0)
 os._exit(0)
time.sleep(.15)
os._exit(7)
"""
result=new.supervise([sys.executable,'-B','-c',code],H,os.environ.copy(),d,5)
cleanup=json.loads((d/'owned-tree-cleanup.json').read_bytes())
ok('fresh detached actual exit7 retained',result['exit_code']==7)
ok('fresh detached descendant adopted and reaped',len(cleanup['owned_pid_start_records'])>=2 and len(cleanup['reaped_descendants'])>=1)
ok('fresh detached setsid differs',len({r['session'] for r in cleanup['owned_pid_start_records']})>=2)
ok('fresh detached all original identities absent',all((x:=D.pin(r['pid'])) is None or x['ticks']!=r['ticks'] for r in cleanup['owned_pid_start_records']))
ok('fresh detached subreaper restored',state()==initial)
outcomes.append({'name':'detached-descendant','result':result,'cleanup':cleanup})
# Early callback-publication failure still retains the actual handle.
d=H/'callback-publication-failure';d.mkdir(mode=0o700);handle={};failure=MemoryError('opaque publication failure');observed=None
def callback(p):handle['process']=p;raise failure
try:new.supervise([sys.executable,'-B','-c','import time;time.sleep(5)'],H,os.environ.copy(),d,2,on_spawn=callback)
except BaseException as e:observed=e
ok('publication failure same fatal',observed is failure)
ok('publication failure retains reaped handle',handle['process'].returncode is not None and D.pin(handle['process'].pid) is None)
ok('publication failure subreaper restored',state()==initial)
outcomes.append({'name':'callback-publication-failure','actual_child_pid':handle['process'].pid,'exit_code':handle['process'].returncode,'error_type':type(observed).__name__,'cleanup':json.loads((d/'owned-tree-cleanup.json').read_bytes())})
q=json.loads((C/'REQUEST_TEMPLATE01.json').read_bytes())
try:P.validate_release(q)
except ValueError:checks.append('exact null draft refused')
else:raise AssertionError('draft accepted')
ok('no numerical modules',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
ok('no remaining owned direct children',not any(r['ppid']==os.getpid() for r in D.snapshot().values()))
out={'schema_version':1,'checks':checks,'count':len(checks),'PF1_matrix':matrix,'PF1_baseline_red':True,'PF1_successor_green':True,'PF2_baseline_red':True,'PF2_successor_green':True,'process_outcomes':outcomes,'actual_native_execution':False,'actual_financial_claims':False,'actual_native_cleanup_tested':False,'numeric_imports':False,'author_checks_used_as_oracle':False,'candidate_manifest_sha256':sha(C/'MANIFEST01.json'),'inherited_review_manifest_sha256':sha(V/'MANIFEST01.json')}
(H/'CHECKS01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(len(checks),'independent Parent03 checks passed')
