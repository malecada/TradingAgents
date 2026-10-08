import ast,hashlib,json,os,resource,signal,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3]
os.nice(10);os.sched_setaffinity(0,{2});resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
old=P.parent/'real-data-pilot-xsect-owned-transport02-2026-10-08/owned_transport02.py';new=P/'owned_transport03.py'
a=ast.parse(old.read_bytes());b=ast.parse(new.read_bytes())
for x,y in zip(a.body,b.body):
 if isinstance(x,ast.FunctionDef) and x.name=='install':
  def strip(f):return [n for n in f.body if not (isinstance(n,ast.FunctionDef) and n.name=='run') and not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='run_number' for t in n.targets))]
  assert ast.dump(ast.Module(body=strip(x),type_ignores=[]))==ast.dump(ast.Module(body=strip(y),type_ignores=[]))
 else:assert ast.dump(x)==ast.dump(y)
ns={'__name__':'fixture','__file__':str(new)};exec(compile(new.read_bytes(),str(new),'exec'),ns)
class Transport:pass
def immutable(p,v):
 with p.open('x') as f:json.dump(v,f)
scope={'Transport':Transport,'_immutable':immutable,'HERE':P};T=ns['install'](scope);obj=T();checks=[]
try:obj.run([sys.executable,'-c',"import sys; print('out',end=''); sys.stderr.write('ssh fixture error'); raise SystemExit(7)"])
except subprocess.CalledProcessError as e:assert e.returncode==7 and e.stderr==b'ssh fixture error'
else:raise AssertionError('expected failure')
r=json.loads((P/'transport-run-0001.json').read_text());assert r['returncode']==7 and r['stderr_tail']=='ssh fixture error' and r['error_type']=='CalledProcessError';assert r['owned_cleanup']['direct_child_reaped'] and r['owned_cleanup']['owned_group_absent'];assert r['stdout_bytes']==3 and r['stdout_sha256']==hashlib.sha256(b'out').hexdigest();checks.append('nonzero_stderr_returncode_stdout_identity_cleanup_persisted')
def alarm(s,f):raise TimeoutError('fixture outer alarm')
prior=signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,.15)
try:
 try:obj.run([sys.executable,'-c','import time; time.sleep(20)'])
 except TimeoutError:pass
 else:raise AssertionError('missing alarm')
finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,prior)
r=json.loads((P/'transport-run-0002.json').read_text());assert r['error_type']=='TimeoutError' and r['returncode']==-9 and r['owned_cleanup']['owned_group_absent'];checks.append('outer_alarm_cleanup_and_actual_returncode_persisted')
assert obj.run([sys.executable,'-c',"print('ok',end='')"]).stdout==b'ok';assert json.loads((P/'transport-run-0003.json').read_text())['status']=='complete';checks.append('normal_success_persisted_incremental_name')
def broken(p,v):raise OSError('receipt unavailable')
scope['_immutable']=broken;T=ns['install'](scope)
try:T().run([sys.executable,'-c','raise SystemExit(8)'])
except subprocess.CalledProcessError as e:assert e.returncode==8 and any('receipt unavailable' in n for n in e.__notes__)
else:raise AssertionError('primary lost')
try:T().run([sys.executable,'-c','pass'])
except OSError as e:assert str(e)=='receipt unavailable'
else:raise AssertionError('publication failure swallowed')
checks+=['publication_failure_preserves_primary','publication_failure_on_success_propagates','all_other_ast_unchanged']
result={'status':'PASS','checks':checks,'source_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'inherited13check_result_sha256':hashlib.sha256((old.parent/'RESULT01.json').read_bytes()).hexdigest(),'no_network_original_data_numerical_imports':True};(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
