import ast,copy,hashlib,importlib.util,json,os,queue,stat,sys,threading,time
from pathlib import Path
P=Path(__file__).absolute().parent;A=P.parent/'financial-wrapper-operational-forensic-watch-correction04-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
new=load('review_watch04',P/'watch01.py');old=load('review_watch03',P/'watch.original03.py');checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n);(P/'PROGRESS01.json').write_text(json.dumps(checks,indent=2)+'\n')
def refuse(n,f):
 try:f()
 except (ValueError,OSError):ck(n,True)
 else:raise AssertionError('accepted '+n)
manifest=json.loads((A/'MANIFEST01.json').read_bytes());actual=[]
def walk(p):
 for q in p.iterdir():
  rel=q.relative_to(A).as_posix()
  if rel=='MANIFEST01.json':continue
  actual.append(rel)
  if stat.S_ISDIR(q.lstat().st_mode):walk(q)
walk(A);ck('whole frozen author membership',set(actual)=={r['path'] for r in manifest['members']})
for r in manifest['members']:
 q=A/r['path'];s=q.lstat();ck('mode:'+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
 if r['kind']=='file':ck('body:'+r['path'],stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(q.read_bytes())==r['sha256'])
 elif r['kind']=='directory':ck('directory:'+r['path'],stat.S_ISDIR(s.st_mode))
 elif r['kind']=='symlink':ck('literal:'+r['path'],os.readlink(q)==r['target'])
 else:ck('special-retained:'+r['path'],not stat.S_ISREG(s.st_mode) and not stat.S_ISDIR(s.st_mode))
inv=json.loads((A/'SOURCE_INVERSE01.json').read_bytes());nb=(P/'watch01.py').read_text();ob=(P/'watch.original03.py').read_text()
ck('source04pin',sha(nb.encode())=='bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18')
ck('original03pin',sha(ob.encode())=='cd2200b071cf14c8191c7b7e95ee660b6bc9a10c49a6de252e77f9832ede8673')
ck('exact single replacement inverse',nb.count(inv['new_segment'])==1 and nb.replace(inv['new_segment'],inv['old_segment'])==ob)
na=ast.parse(nb);oa=ast.parse(ob)
ck('all noncensus AST identical',ast.dump(ast.Module(body=[n for n in na.body if not isinstance(n,ast.FunctionDef) or n.name!='census'],type_ignores=[]))==ast.dump(ast.Module(body=[n for n in oa.body if not isinstance(n,ast.FunctionDef) or n.name!='census'],type_ignores=[])))
ck('allcaps unchanged',new.POLICY==old.POLICY=={'logical':67108864,'allocated':100663296,'members':32768,'depth':32,'file':4194304,'sample_seconds':5,'floor':10737418240,'samples':8192})
O=P/'owned01';O.mkdir(mode=0o700);publisher_results=[]
def publication(module,label):
 root=O/label;root.mkdir(mode=0o700);(root/'retained').write_bytes(b'opaque');requests=queue.Queue();done=queue.Queue();stop=threading.Event();started=time.monotonic();fail=[]
 def publisher():
  serial=0
  while not stop.is_set():
   try:requests.get(timeout=.01)
   except queue.Empty:continue
   try:
    path=root/('published-'+str(serial));path.mkdir(mode=0o700);(path/'body').write_bytes(b'opaque published body');serial+=1;done.put(True)
   except BaseException as e:fail.append(type(e).__name__);done.put(False)
 t=threading.Thread(target=publisher);t.start();original=Path.lstat;calls=0
 def endpoint(p,*args,**kw):
  nonlocal calls
  if p==root:
   calls+=1
   if calls%2==0 and time.monotonic()-started<.07:
    requests.put(True);assert done.get(timeout=1)
  return original(p,*args,**kw)
 Path.lstat=endpoint;result=None;error=None;begin=time.monotonic()
 try:result=module.census(root)
 except BaseException as e:error=type(e).__name__
 finally:Path.lstat=original;stop.set();t.join(timeout=2)
 ck('publisher-joined:'+label,not t.is_alive() and not fail)
 outcome={'label':label,'result':result,'error_type':error,'elapsed':time.monotonic()-begin,'actual_children':sorted(p.name for p in root.iterdir())};publisher_results.append(outcome);return outcome
for i in range(2):
 a=publication(old,'old'+str(i));b=publication(new,'new'+str(i))
 ck('oldactualRED:'+str(i),a['result'] is None and a['error_type']=='ValueError')
 ck('newactualGREEN:'+str(i),b['result'] is not None and b['result']['complete_attempts']==2 and b['result']['members']==4 and b['elapsed']>=.1)
# Control pure scheduling through exact real census function without fake authority.
scheduling=[]
class Clock:
 def __init__(self,step=0):self.now=0.;self.sleeps=[];self.step=step
 def monotonic(self):return self.now
 def sleep(self,n):self.sleeps.append(n);self.now+=n+self.step
orig_sample=new._sample;origtime=new.time
for name,failcount,start,overshoot in [('stable',0,0,0),('one',1,0,0),('two',2,0,0),('persistent',3,0,0),('no-room',1,4.95,0),('overshoot',1,0,5)]:
 clock=Clock(overshoot);count=[0]
 def sample(root):
  count[0]+=1
  if count[0]<=failcount:clock.now=max(clock.now,start);raise new.ChangingTree('owned control')
  return {'seconds':0}
 new._sample=sample;new.time=clock;result=None;err=None
 try:result=new.census(O)
 except ValueError as e:err=type(e).__name__
 finally:new._sample=orig_sample;new.time=origtime
 expectedwaits={'stable':0,'one':1,'two':2,'persistent':2,'no-room':0,'overshoot':1}[name]
 ck('waitceiling:'+name,len(clock.sleeps)==expectedwaits and all(x==.1 for x in clock.sleeps))
 ck('deadline-or-success:'+name,(result is not None)==(name in ('stable','one','two')))
 scheduling.append({'name':name,'calls':count[0],'sleeps':clock.sleeps,'error':err,'result':result})
for i,error in enumerate([KeyboardInterrupt(),MemoryError(),SystemExit(),PermissionError()]):
 clock=Clock();new.time=clock
 def failure(root,e=error):raise e
 new._sample=failure;caught=None
 try:new.census(O)
 except BaseException as e:caught=e
 finally:new.time=origtime;new._sample=orig_sample
 ck('fatalimmediate:'+str(i),caught is error and clock.sleeps==[])
# Real iterator cleanup path, actual fd closure before secondary exception.
root=O/'iteratorfatal';root.mkdir(mode=0o700);(root/'body').write_bytes(b'x')
original=new.os.scandir;primary=KeyboardInterrupt('primary');secondary=SystemExit('secondary');closed=[]
class Iterator:
 def __init__(self,p):self.actual=original(p)
 def __iter__(self):return self
 def __next__(self):raise primary
 def close(self):self.actual.close();closed.append(True);raise secondary
new.os.scandir=Iterator;caught=None
try:new.census(root)
except BaseException as e:caught=e
finally:new.os.scandir=original
ck('actualiterator-firstfatal',caught is primary and closed==[True])
# Existing closed-census resource/type refusals using owned ordinary files.
root=O/'resource';root.mkdir(mode=0o700);body=root/'body';body.write_bytes(b'opaque')
base=new.census(root);ck('actualstablefullnamespace',base['members']==2 and base['logical_bytes']==6)
for key,value in [('logical',5),('allocated',0),('file',5),('members',1),('depth',-1),('floor',2**100)]:
 original=new.POLICY;new.POLICY=dict(original,**{key:value})
 try:refuse('lowercap:'+key,lambda:new.census(root))
 finally:new.POLICY=original
link=O/'lexical';link.symlink_to(root,target_is_directory=True);refuse('realredirect',lambda:new.census(link))
hardroot=O/'hard';hardroot.mkdir(mode=0o700);os.link(body,hardroot/'body');refuse('realhardlink',lambda:new.census(hardroot))
ck('no numerical imports',not any(n.split('.')[0] in ('numpy','torch','scipy','pandas') for n in sys.modules))
(P/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'publication':publisher_results,'scheduling':scheduling,'source_only':True,'actual_remote_or_native_entry':False},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'status':'PASS_SOURCE_ONLY'}))
