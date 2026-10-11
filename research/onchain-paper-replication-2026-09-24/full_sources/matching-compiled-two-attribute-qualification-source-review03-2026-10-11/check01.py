import ast,copy,difflib,hashlib,json,os,resource,signal,traceback,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'matching-compiled-two-attribute-qualification03-2026-10-11';O=F/'matching-compiled-two-attribute-qualification02-2026-10-11';Q=F/'pilot34-native-owner-qualification01-2026-10-11';checks=[];refs={}
def read(p):
 assert p.suffix!='.so';b=p.read_bytes();refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(v,n):checks.append({'name':n,'pass':bool(v)});assert v,n
manifest=json.loads(read(D/'MANIFEST03.json'));ck(refs[str((D/'MANIFEST03.json').relative_to(R))]['sha256'].startswith('dd140c1f'),'exact supplied fixture03 manifest prefix')
for name,row in manifest['files'].items():read(D/name);ck(refs[str((D/name).relative_to(R))]==row,'frozen fixture03 '+name)
new=read(D/'fixture03.py');old=read(O/'fixture02.py');ck(hashlib.sha256(new.encode()).hexdigest()=='2647223d8501ab5273ddc3015fbc71e993384731e5453f24c821bd017f4f84b5','exact fixture03 body')
for a,b,n in ((old,new,'FORWARD.patch'),(new,old,'INVERSE.patch')):ck(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='fixture.py',tofile='fixture.py'))==read(D/n),'literal '+n)
start='    filler=make_filler(native,np,agreement)';end="    checks.append({'function_and_global_mutation_refused':True})";ck(new[new.index(start):new.index(end)+len(end)]==old[old.index(start):old.index(end)+len(end)],'numerical body unchanged')
ck(new[:new.index('start=time.monotonic()')]==old[:old.index('start=time.monotonic()')],'reservation and original references unchanged')
tree=ast.parse(new);template=next(n for n in tree.body if isinstance(n,ast.Try))
class BadString(Exception):
 def __str__(self):raise MemoryError('synthetic formatting failure')
class Target:
 def __init__(self,broken):self.broken=broken
 def __truediv__(self,name):return self
 def open(self,*a,**kw):
  if self.broken:raise OSError('synthetic traceback storage failure')
  return self
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def write(self,text):return len(text)
outcomes=[]
for label,primary,broken,writefail in [('ordinary',ValueError('original'),False,False),('traceback',ValueError('original'),True,False),('format',BadString(),False,False),('both_storage',KeyboardInterrupt('original'),True,True),('success',None,False,False),('success_storage',None,False,True)]:
 trial=copy.deepcopy(template);trial.body=[ast.Raise(exc=ast.Name(id='original',ctx=ast.Load()),cause=None)] if primary is not None else [ast.Pass()]
 rows=[];storage=OSError('synthetic result storage failure')
 def write_result(path,row):
  if writefail:raise storage
  rows.append(row)
 env={'original':primary,'ATTEMPT':Target(broken),'traceback':traceback,'failure':None,'failed':False,'primary':None,'secondary':[],'checks':[],'start':0,'time':types.SimpleNamespace(monotonic=lambda:0),'write_result':write_result};escaped=None
 try:exec(compile(ast.fix_missing_locations(ast.Module(body=[trial],type_ignores=[])),'actual-fixture03-reporting','exec'),env)
 except BaseException as error:escaped=error
 ck(escaped is (primary if primary is not None else storage if writefail else None),'primary disposition '+label)
 ck(not rows or rows[0]['status']==('FAILED' if primary is not None else 'PASS_FINITE_SYNTHETIC'),'result disposition '+label)
 outcomes.append({'case':label,'status':rows[0]['status'] if rows else 'UNPUBLISHED','primary_identity_preserved':escaped is primary if primary else None})
command=json.loads(read(Q/'COMMAND01.json'));policy=json.loads(read(Q/'POLICY_ROLE01.json'));qmanifest=json.loads(read(Q/'MANIFEST01.json'))
ck(refs[str((Q/'COMMAND01.json').relative_to(R))]['sha256']=='85aa4d791634c0d7547634f567cac420367de0982e8d34406e53f15f5234c03f','exact command')
ck(refs[str((Q/'POLICY_ROLE01.json').relative_to(R))]['sha256']=='46bfd555cb4eee027164ecbf0dd9fe91198023d6a174bbd8d6f9b4f8158271eb','exact policy')
for name,row in qmanifest['files'].items():read(Q/name);ck(all(refs[str((Q/name).relative_to(R))][k]==row[k] for k in ('sha256','bytes')),'queued owner manifest member '+name)
argv=command['argv'];ck(argv[:2]==[str(R/'.venv/bin/python'),'-B'] and argv[2]==str(Q/'qualify01.py') and command['cwd']==str(R) and command['outer_timeout_seconds']==60 and command['maximum_attempts']==1,'fixed interpreter cwd one-use outer bound')
options=dict(zip(argv[3::2],argv[4::2]))
for role in ('owner','kernel','policy'):
 read(Path(options['--'+role]));ck(refs[str(Path(options['--'+role]).relative_to(R))]['sha256']==options['--'+role+'-sha256'],'actual argv pin '+role)
read(R/'tradingagents/research/onchain_replication/matching_annealing.py');ck(refs['tradingagents/research/onchain_replication/matching_annealing.py']['sha256']==options['--baseline-sha256'],'actual installed baseline pin')
for role,row in command['role_references'].items():
 ck(policy[role+'_path']==row['path'] and policy[role+'_sha256']==row['sha256'],'policy exact '+role+' join')
 if role!='library':read(Path(row['path']));ck(refs[str(Path(row['path']).relative_to(R))]=={k:row[k] for k in ('sha256','bytes')},'public '+role+' body pin')
 else:ck(row['bytes']==17072,'native size metadata only; no binary read')
harness=read(Q/'qualify01.py');ck('resource.RLIMIT_CPU, (50, 55)' in harness and 'resource.RLIMIT_AS, (1536*1024**2, 1536*1024**2)' in harness and 'resource.RLIMIT_FSIZE, (4*1024**2, 4*1024**2)' in harness and 'os.sched_setaffinity(0, {0, 1})' in harness,'exact internal resource source bounds')
ck(harness.index('not UNIT.exists()')<harness.index('out.mkdir')<harness.index('import numpy') and "exist_ok=False" in harness and "result_path.open('xb')" in harness,'owner one-use and inactive-job source guard')
# Narrow newly identified analogue in old owner harness: formatting failure before assignment.
main=next(n for n in ast.parse(harness).body if isinstance(n,ast.FunctionDef) and n.name=='main');trial=copy.deepcopy(next(n for n in main.body if isinstance(n,ast.Try)));trial.body=[ast.Raise(exc=ast.Name(id='original',ctx=ast.Load()),cause=None)]
class Capture(Target):
 def __init__(self):self.parts=[]
 def open(self,*a,**kw):return self
 def write(self,body):self.parts.append(body)
 def flush(self):pass
 def fileno(self):return 0
capture=Capture();original=BadString();env={'original':original,'failure':None,'lease':None,'owner':None,'checks':[],'phases':[],'started':0,'time':types.SimpleNamespace(monotonic=lambda:0),'resource':types.SimpleNamespace(RUSAGE_SELF=0,getrusage=lambda x:types.SimpleNamespace(ru_maxrss=0)),'os':types.SimpleNamespace(fsync=lambda x:None),'result_path':capture,'encoded':lambda row:json.dumps(row).encode()};escaped=None
try:exec(compile(ast.fix_missing_locations(ast.Module(body=[trial],type_ignores=[])),'actual-owner-harness-reporting','exec'),env)
except BaseException as error:escaped=error
owner_result=json.loads(b''.join(capture.parts));ck(isinstance(escaped,MemoryError) and owner_result['status']=='PASS_FINITE_SYNTHETIC' and owner_result['failure'] is None,'confirmed owner harness false PASS after error formatting failure')
out={'fixture_decision':'ACCEPTED_FAILURE_LATCH_SOURCE_ONLY','owner_command_decision':'WITHHELD_EXISTING_HARNESS_FAILURE_REPORTING','checks':checks,'references':refs,'fixture_outcomes':outcomes,'owner_counterexample':owner_result,'real_native_science_fixture_or_authority_execution':False}
with (P/'RESULT01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'fixture_decision':out['fixture_decision'],'owner_command_decision':out['owner_command_decision'],'checks':len(checks)}))
