import ast,copy,difflib,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'pilot34-native-owner-qualification02-2026-10-11';O=F/'pilot34-native-owner-qualification01-2026-10-11';checks=[];refs={}
def read(p):
 b=p.read_bytes();refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(v,n):checks.append({'name':n,'pass':bool(v)});assert v,n
m=json.loads(read(D/'MANIFEST02.json'));ck(refs[str((D/'MANIFEST02.json').relative_to(R))]['sha256']=='1cb930ae25e2db95099b6b484fbf821f89859a216d93b8466dd557072fa108f3','exact owner02 manifest')
for name,row in m['bodies'].items():read(D/name);ck(refs[str((D/name).relative_to(R))]=={k:row[k] for k in ('sha256','bytes')},'frozen owner02 '+name)
new=read(D/'qualify02.py');old=read(O/'qualify01.py')
for a,b,n,x,y in ((old,new,'LITERAL_PATCH01.diff','qualify01.py','qualify02.py'),(new,old,'LITERAL_INVERSE01.diff','qualify02.py','qualify01.py')):ck(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=x,tofile=y))==read(D/n),'exact '+n)
def main(text):return next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='main')
newmain=main(new);oldmain=main(old);trial=next(n for n in newmain.body if isinstance(n,ast.Try));oldtry=next(n for n in oldmain.body if isinstance(n,ast.Try))
ck(ast.dump(ast.Module(body=trial.body,type_ignores=[]))==ast.dump(ast.Module(body=oldtry.body,type_ignores=[])),'entire numeric try body AST unchanged')
command=json.loads(read(D/'COMMAND02.json'));prior=json.loads(read(O/'COMMAND01.json'))
expected=copy.deepcopy(prior);expected['argv'][2]=str(D/'qualify02.py');expected['script']=command['script'];expected['predecessor_command']=command['predecessor_command']
ck(command==expected,'only selected script/reference metadata command changes; all roles and bounds retained')
ck(command['script']['sha256']==hashlib.sha256(new.encode()).hexdigest() and command['script']['bytes']==len(new.encode()) and command['script']['path']==command['argv'][2],'actual command/source join')
class BadString(Exception):
 def __str__(self):raise MemoryError('synthetic formatting error')
class Capture:
 def __init__(self,error=None):self.error=error;self.parts=[]
 def open(self,*args):
  if self.error:raise self.error
  return self
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def write(self,data):self.parts.append(data)
 def flush(self):pass
 def fileno(self):return 0
outcomes=[]
for label,original,cleanup,output,encoding in [('primary_badstr',BadString(),None,False,False),('primary_cleanup',ValueError('original'),BadString(),False,False),('primary_output',KeyboardInterrupt('original'),None,True,False),('primary_encode',ValueError('original'),None,False,True),('cleanup_first',None,BadString(),False,False),('output_first',None,None,True,False),('success',None,None,False,False)]:
 t=copy.deepcopy(trial);t.body=[ast.Raise(exc=ast.Name(id='original',ctx=ast.Load()),cause=None)] if original is not None else [ast.Pass()]
 storage=OSError('synthetic output error');encode_error=MemoryError('synthetic encoding error');capture=Capture(storage if output else None);calls=[]
 def close():
  calls.append('close')
  if cleanup is not None:raise cleanup
 def encode(row):
  if encoding:raise encode_error
  return json.dumps(row).encode()
 env={'original':original,'failed':False,'primary':None,'secondary':[],'failure':None,'lease':types.SimpleNamespace(close=close),'owner':None,'checks':[],'phases':[],'started':0,'time':types.SimpleNamespace(monotonic=lambda:0),'resource':types.SimpleNamespace(RUSAGE_SELF=0,getrusage=lambda x:types.SimpleNamespace(ru_maxrss=0)),'os':types.SimpleNamespace(fsync=lambda x:None),'result_path':capture,'encoded':encode};escaped=None
 try:exec(compile(ast.fix_missing_locations(ast.Module(body=[t],type_ignores=[])),'actual-owner02-handler-only','exec'),env)
 except BaseException as error:escaped=error
 expected_error=original if original is not None else cleanup if cleanup is not None else storage if output else encode_error if encoding else None
 ck(escaped is expected_error and calls==['close'],'original/cleanup/publication primary identity '+label)
 result=json.loads(b''.join(capture.parts)) if capture.parts else None
 ck(result is None or result['status']==('FAILED' if original is not None or cleanup is not None else 'PASS_FINITE_SYNTHETIC'),'result status '+label)
 outcomes.append({'case':label,'result_status':result['status'] if result else 'UNPUBLISHED','primary_identity_preserved':True})
out={'decision':'ACCEPTED_OWNER02_SOURCE_AND_CONDITIONAL_ENTRY','checks':checks,'references':refs,'outcomes':outcomes,'actual_native_science_or_harness_execution':False,'required_actual_postconditions':['pilot34 terminal/cleanup and independent acceptance','full failed34 external recovery and independent acceptance','fresh code/runtime/storage/process and single-launch eligibility','exact COMMAND02 under declared 60-second outer timeout with raw exit retention'],'not_established':['genuine Owner/Binding admission','actual Session/checkpoint/upper chain','real native/ABI/FD lifetime','real numerical equality or speed']}
with (P/'OWNER02_RESULT01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':out['decision'],'checks':len(checks)}))
