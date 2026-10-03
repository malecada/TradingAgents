"""Independent bounded stdlib controls. Does not invoke parent.launch or native controls."""
import ast,ctypes,hashlib,json,os,signal,stat,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent
C=H.parent/'financial-genuine-wrapper-parent-preparation02-2026-10-04'
sys.path.insert(0,str(C))
import supervisor01 as S
import descendants01 as D
import parent01 as P
import recovery04 as R
checks=[];cases=[]
def ok(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def subreaper():
 value=ctypes.c_int();lib=ctypes.CDLL(None,use_errno=True)
 assert lib.prctl(37,ctypes.byref(value),0,0,0)==0
 return value.value
initial=subreaper()
manifest_raw=(C/'MANIFEST01.json').read_bytes()
ok('candidate manifest exact',digest(manifest_raw)=='3f209f1794ace2c928d49fd83d5f51ce2330419971bdbf1dd4aea05857bf3270')
manifest=json.loads(manifest_raw)
ok('candidate 111 typed entries',len(manifest['entries'])==111)
for row in manifest['entries']:
 p=C/row['path'];s=p.lstat()
 ok('mode '+row['path'],stat.S_IMODE(s.st_mode)==row['mode'])
 if row['type']=='file':
  raw=p.read_bytes();ok('body '+row['path'],stat.S_ISREG(s.st_mode) and len(raw)==row['size'] and digest(raw)==row['sha256'])
 else:ok('directory '+row['path'],row['type']=='directory' and stat.S_ISDIR(s.st_mode))
pins=json.loads((C/'PROTOCOL_PINS01.json').read_bytes())
for name,pin in pins.items():
 original=C/('original-'+Path(name).name)
 ok('unchanged original '+name,digest(original.read_bytes())==pin==digest((P.CAP/name).read_bytes()))
def run(name,code,seconds=5,watch=None,spawn=None):
 d=H/name;d.mkdir(mode=0o700);saved={};result=None;error=None
 def on_spawn(p):
  saved['process']=p
  if spawn:spawn(p,d)
 try:result=S.supervise([sys.executable,'-B','-c',code],H,os.environ.copy(),d,seconds,(lambda:watch(d)) if watch else (lambda:None),on_spawn)
 except BaseException as e:error=e
 ok(name+' restores subreaper',subreaper()==initial)
 p=saved.get('process')
 if p:ok(name+' actual child reaped',p.poll() is not None and D.pin(p.pid) is None)
 receipt=d/'owned-tree-cleanup.json';cleanup=json.loads(receipt.read_bytes()) if receipt.exists() else None
 if cleanup:
  ok(name+' receipt empty original identities',cleanup['remaining_original_identities']==[])
  ok(name+' every retained identity absent',all((x:=D.pin(r['pid'])) is None or x['ticks']!=r['ticks'] for r in cleanup['owned_pid_start_records']))
 cases.append({'name':name,'result':result,'error_type':None if error is None else type(error).__name__,'primary_pid':None if p is None else p.pid,'cleanup':cleanup})
 return result,error,cleanup
r,e,c=run('exit7',"import sys;sys.stdout.buffer.write(b'opaque\\x00out');sys.stderr.buffer.write(b'opaque err');sys.exit(7)")
ok('actual exit7 remains failure',e is None and r['exit_code']==7)
ok('raw streams exact',(H/'exit7/stdout').read_bytes()==b'opaque\x00out' and (H/'exit7/stderr').read_bytes()==b'opaque err')
double="""import os,signal,time
if os.fork()==0:
 os.setsid()
 if os.fork()==0:
  signal.signal(signal.SIGTERM,signal.SIG_IGN)
  print('detached',os.getpid(),flush=True)
  time.sleep(12)
  os._exit(0)
 os._exit(0)
time.sleep(.15)
os._exit(7)
"""
r,e,c=run('doublefork-set-session-ignore-term',double)
ok('doublefork actual leader failure preserved',e is None and r['exit_code']==7)
ok('detached adopted identity reaped',len(c['owned_pid_start_records'])>=2 and len(c['reaped_descendants'])>=1)
ok('different child session authenticated',len({x['session'] for x in c['owned_pid_start_records']})>=2)
r,e,c=run('deadline',"import time;time.sleep(12)",seconds=.15)
ok('deadline refuses success',isinstance(e,ValueError) and r is None)
fatal=KeyboardInterrupt('opaque first fatal')
def raise_fatal(d):raise fatal
r,e,c=run('watch-fatal',"import time;time.sleep(12)",watch=raise_fatal)
ok('watch preserves same fatal',e is fatal)
spawnfatal=SystemExit(23)
def fail_spawn(p,d):raise spawnfatal
r,e,c=run('spawn-fatal',"import time;time.sleep(12)",spawn=fail_spawn)
ok('on-spawn preserves same fatal',e is spawnfatal)
original_close=D.OwnedTree.close
secondary=MemoryError('opaque later fatal')
def close_then_fail(self):original_close(self);raise secondary
D.OwnedTree.close=close_then_fail
try:r,e,c=run('primary-plus-close-fatal',"import time;time.sleep(12)",watch=raise_fatal)
finally:D.OwnedTree.close=original_close
ok('cleanup later fatal cannot replace original fatal',e is fatal)
ordinary=ValueError('opaque ordinary')
def raise_ordinary(d):raise ordinary
D.OwnedTree.close=close_then_fail
try:r,e,c=run('ordinary-plus-close-fatal',"import time;time.sleep(12)",watch=raise_ordinary)
finally:D.OwnedTree.close=original_close
ok('later fatal outranks ordinary primary',e is secondary)
def replace_log(d):
 p=d/'stdout';p.rename(d/'original-stdout');p.write_bytes(b'opaque replacement')
r,e,c=run('log-replaced',"import time;time.sleep(12)",watch=replace_log)
ok('log replacement refuses success and receipt',e is not None and r is None and c is None)
ok('replaced log evidence retained',(H/'log-replaced/original-stdout').is_file() and (H/'log-replaced/stdout').read_bytes()==b'opaque replacement')
prior=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(12)'])
try:
 d=H/'preexisting-child';d.mkdir(mode=0o700)
 try:S.supervise([sys.executable,'-B','-c','pass'],H,os.environ.copy(),d,1)
 except ValueError:ok('preexisting child refused without interference',prior.poll() is None and not list(d.iterdir()))
 else:raise AssertionError('unrelated child allowed')
finally:prior.terminate();prior.wait(timeout=2)
ok('preexisting child control restores state',subreaper()==initial)
# Reused identity is a minimal opaque metadata control: signal is intercepted.
tree=D.OwnedTree();real_pin=D.pin;real_kill=D.os.kill;calls=[]
D.pin=lambda pid:{'pid':pid,'ticks':'new'}
D.os.kill=lambda *args:calls.append(args)
try:
 try:tree.signal({123:{'pid':123,'ticks':'old'}},signal.SIGTERM)
 except ValueError:ok('PID ticks mismatch never signalled',calls==[])
 else:raise AssertionError('reused PID accepted')
finally:D.pin=real_pin;D.os.kill=real_kill
q=json.loads((C/'REQUEST_TEMPLATE01.json').read_bytes())
try:P.validate_release(q)
except ValueError:checks.append('actual draft refused before any proof reads')
else:raise AssertionError('draft accepted')
q['status']='RELEASED_ONE_USE_FINANCIAL_PARENT'
try:P.validate_release(q)
except ValueError:checks.append('status alone cannot release null contract')
else:raise AssertionError('null contract accepted')
# First-fatal reducer and native-control order use real exception objects only.
events=[];first=SystemExit(11);later=KeyboardInterrupt('later')
def callback(label,exc=None):
 events.append(label)
 if exc:raise exc
try:R._cleanup((lambda:callback('before',first),lambda:callback('stop',later),lambda:callback('after')))
except BaseException as e:ok('all native-control reducer callbacks and first fatal',e is first and events==['before','stop','after'])
else:raise AssertionError('fatal lost')
text=(C/'parent01.py').read_text();tree=ast.parse(text)
cleanup=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='child_cleanup')
segment=ast.get_source_segment(text,cleanup)
ok('actual native three controls are reducer actions',"('before',['show',unit" in segment and "('stop',['stop',unit])" in segment and "('after',['show',unit" in segment and 'R._cleanup(tuple(' in segment)
ok('unknown cgroup retains refusal',"require(not after.get('ControlGroup') and results['after']['exit_code']!=0,'unobserved original cgroup remains uncertain')" in segment)
ok('sample census not claimed full history',"'native_pid_census_is_complete_history':False" in segment)
original=(C/'original-resources.py').read_text();t=ast.parse(original);guard=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='guarded_run');s=ast.get_source_segment(original,guard)
ok('original predispatch live publication',"state['phase'] = 'verifying_cgroup'\n        publish()\n        args = ['systemd-run'" in s)
ok('guard does not delete live intent',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('unlink','remove','rmdir') for n in ast.walk(guard)))
ok('original atomic live publication',"_native_atomic(receipt/'live.json',state,native_io)" in s)
ok('numeric modules never loaded',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
ok('dedicated process ends with no children',not any(x['ppid']==os.getpid() for x in D.snapshot().values()))
out={'schema_version':1,'checks':checks,'count':len(checks),'cases':cases,'candidate_manifest_sha256':digest(manifest_raw),'actual_native_commands':False,'actual_research_claims':False,'numerical_imports':False,'release_accepted':False,'initial_subreaper':initial,'final_subreaper':subreaper()}
(H/'CHECKS01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(len(checks),'independent checks passed')
