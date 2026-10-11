import ast,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(20)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'matching-compiled-uncached-edge-chunk02-2026-10-11';O=F/'matching-compiled-uncached-edge-chunk01-2026-10-11';refs={};checks=[]
def read(p):
 assert not ({'.git','.venv','research_artifacts','research_runs','keys','apis'}&set(p.parts)) and p.suffix!='.so'
 b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(v,n):
 checks.append({'name':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
m=json.loads(read(D/'MANIFEST02.json'));ck(refs[str((D/'MANIFEST02.json').relative_to(R))]['sha256']=='2b566adc973e11d12d772c004ccb311eb084381afbe2f0975c5fd21a033f04ae','exact frozen02 manifest')
for name,row in m['files'].items():b=read(D/name).encode();ck(hashlib.sha256(b).hexdigest()==row['sha256'] and len(b)==row['bytes'],'frozen02 textual member '+name)
prior=json.loads(read(F/'pilot34-acceleration-candidates-source-review01-2026-10-11/REVIEW01.json'));ck(refs[str((F/'pilot34-acceleration-candidates-source-review01-2026-10-11/REVIEW01.json').relative_to(R))]['sha256']=='4f92784b82f2f55b4f6ba8bfe185ea0735b7ef7b5614adaa195cc9d1b61562d4','original independent refusal retained')
old=read(O/'matching_annealing.py');new=read(D/'matching_annealing.py')
inverse=new.replace('offset=0;native_progress=None','native_progress=None',1).replace('native_progress=[0]','native_progress=[None]',1).replace('if not native_used:\n                                    native_progress=None','if not native_used:',1)
ck(inverse==old and hashlib.sha256(new.encode()).hexdigest()=='86ccc3a471827bdce7784145914240d04416d2cc0023e8acb77fb26ae473df57','exact three-line inverse and candidate source')
for name in ('edge_chunk.c','adapter.py','fixture01.py','build01.py'):ck(read(D/name)==read(O/name),'unchanged original seam '+name)
tree=ast.parse(new);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_advance_checked')
branch=next(n for n in ast.walk(fn) if isinstance(n,ast.If) and any(isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='native_progress' for t in s.targets) for s in n.orelse))
probe=ast.parse('def probe():\n offset=77\n used=0\n').body[0];probe.body+=branch.orelse
class Matrix(dict):
 def __missing__(self,key):return 1.
class Edges:
 def __getitem__(self,key):return key[1],key[1]
rows=[]
for kind in ('prefill_fatal','eligibility','decline_then_error','partial_error'):
 error=KeyboardInterrupt('original fatal before progress') if kind=='prefill_fatal' else MemoryError('original current chunk failure')
 q=Matrix();graph=types.SimpleNamespace(edge_features=list(range(5)),edge_index=Edges());calls=[0]
 def agreement(a,b):
  calls[0]+=1
  if calls[0]==4:raise error
  return 2.
 def filler(w,af,bf,l,r,count,callback,progress):
  if kind=='decline_then_error':progress[0]=0;return False
  if kind=='partial_error':w[:3]=[1.,1.,1.];progress[0]=3
  raise error
 def guard():
  if kind=='eligibility':raise error
  return True
 env=dict(edge_chunk_fill=filler,reuse=False,cached=None,valid=None,count=5,start=0,total=5,weights=[0.]*5,left=list(range(5)),right=list(range(5)),a=graph,b=graph,_reuse_runtime=guard,_immutable_edges=lambda g:True,agreement=agreement,state={'Q':q,'M':Matrix(),'cursor':0},used=0)
 # Execute original branch in function scope; state prefix is externally observable.
 exec(compile(ast.fix_missing_locations(ast.Module(body=[probe],type_ignores=[])),'actual02-changed-branch','exec'),env)
 caught=None
 try:env['probe']()
 except BaseException as e:caught=e
 prefix=3 if kind in ('decline_then_error','partial_error') else 0
 ck(caught is error and env['state']['cursor']==prefix and len(q)==prefix,'original exception identity and prefix '+kind)
 rows.append({'case':kind,'primary_identity':caught is error,'type':type(caught).__name__,'prefix':prefix,'cursor':env['state']['cursor'],'q_destinations':len(q)})
out={'decision':'ACCEPT_EXACT02_PREFILL_EXCEPTION_SOURCE_REPAIR_ONLY','candidate_source_sha256':hashlib.sha256(new.encode()).hexdigest(),'checks':checks,'references':refs,'controls':rows,'limits':['Original candidate01 P2/refusal retained.','Unchanged C/adapter/fixture source review reused; no native/scientific imports or arrays.','Function-scope changed branch with stale prior offset77 and four independent controls only; no full annealing equivalence claim.','Root build02 and actual numerical fixture, public Session/loader/policy/currentness/Owner/caller release remain pending.','No live job, source installation, timing, capacity, financial or recovery claim.']}
with (P/'NATIVE_SOURCE_REVIEW01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'decision':out['decision'],'checks':len(checks),'sha256':hashlib.sha256((P/'NATIVE_SOURCE_REVIEW01.json').read_bytes()).hexdigest(),'controls':rows},sort_keys=True))
