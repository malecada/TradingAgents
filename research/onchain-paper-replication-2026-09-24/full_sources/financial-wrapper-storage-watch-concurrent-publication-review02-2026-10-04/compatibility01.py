import ast,hashlib,importlib.util,json,os,stat,sys,threading,uuid
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent
A=H.parent/'financial-wrapper-storage-watch-concurrent-publication-correction01-2026-10-04'
S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
rows=[]; checks=0

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(v,label):
 global checks
 checks+=1
 if not v:raise AssertionError(label)
def record(name,**kw):
 rows.append({'case':name,**kw});(H/'PROGRESS01.json').write_text(json.dumps(rows,indent=2)+'\n')
def load(name):
 directory=H.parent/'financial-wrapper-storage-watch-concurrent-publication-correction02-2026-10-04' if name=='workflow_storage' else A
 spec=importlib.util.spec_from_file_location(name,directory/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.os=SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});return m
ck(sys.version_info[:3]==(3,13,13),'pinned runtime')
ck(sha(A/'MANIFEST01.json')=='ffbcc1efc6e56d1bf5b19830dd46a279e79f0a2b242e0e3a8ca182da421aaafb','manifest anchor')
manifest=json.loads((A/'MANIFEST01.json').read_text()); listed=set()
for r in manifest['members']:
 p=A/r['path'];listed.add(r['path']);s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'mode '+r['path'])
 if r['kind']=='file':
  ck(stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p)==r['sha256'],'body '+r['path']);ck(s.st_nlink==r['links'],'links')
 elif r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'directory')
 else:ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r.get('target',r.get('link_target')),'symlink')
actual={str(p.relative_to(A)) for p in A.rglob('*')};ck(actual==listed|{'MANIFEST01.json'},'complete author census')
for group in manifest['literal_retained_hardlink_groups']:ck(len({(A/x).stat().st_ino for x in group})==1,'hardlink group')
for r in json.loads((A/'SOURCE_REFERENCES01.json').read_text()):ck(sha(Path(r['path']))==r['sha256'],'actual source reference')
readback=json.loads((A/'SOURCE194_READBACK01.json').read_text())
for r in readback['bodies']:
 p=S/r['path'];ck(sha(p)==r['sha256'] and p.stat().st_size==r['bytes'] and stat.S_IMODE(p.stat().st_mode)==r['mode'],'source closure body')
ck(len(readback['bodies'])==194,'194 denominator')
inv=json.loads((A/'FINAL_INVERSE08.json').read_text());new=(A/'workflow_storage.py').read_text();old=(A/'original_workflow_storage.py').read_text();rebuilt=new
for op in reversed(inv['operations']):
 ck(rebuilt[op['new_start']:op['new_end']]==op['new_literal'],'inverse literal');rebuilt=rebuilt[:op['new_start']]+op['old_literal']+rebuilt[op['new_end']:]
ck(rebuilt==old and hashlib.sha256(new.encode()).hexdigest()==inv['new_sha256'] and hashlib.sha256(old.encode()).hexdigest()==inv['old_sha256'],'full inverse')
def strip(body):
 t=ast.parse(body);t.body=[n for n in t.body if getattr(n,'name',None) not in ('StorageMutationObservation','_signature','_cleanup')]
 for n in t.body:
  if isinstance(n,ast.ClassDef) and n.name=='StorageWatch':n.body=[x for x in n.body if getattr(x,'name',None) not in ('_check','_scan')]
 return ast.dump(t,include_attributes=False)
ck(strip(old)==strip(new),'only declared AST domain')
record('full-authentication',author_members=len(listed),actual_source_bodies=194,full_inverse=True)
L=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
def root(name):p=H/'controls01'/name;p.mkdir(parents=True);return p
# Extract only the actual publication helper and its stdlib-only dependencies.
t=ast.parse((S/'tradingagents/research/lifecycle.py').read_text());pubenv={'os':os,'json':json,'uuid':uuid,'Path':Path,'current_metadata_scope':lambda:None}
exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('_encode','_fsync_dir','_immutable')],type_ignores=[]),'actual-lifecycle-subset','exec'),pubenv)
fd0=len(os.listdir('/proc/self/fd'))
for modname in ('original_workflow_storage','workflow_storage'):
 m=load(modname);p=root('publication-'+modname);ready=threading.Event();finish=threading.Event();errors=[]
 class PubOS:
  def __getattr__(self,k):return getattr(os,k)
  def link(self,a,b):ready.set();ck(finish.wait(3),'release publisher');return os.link(a,b)
 env=dict(pubenv);env['os']=PubOS();exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('_encode','_fsync_dir','_immutable')],type_ignores=[]),'actual-lifecycle-subset','exec'),env)
 def publish():
  try:env['_immutable'](p/'published',{'opaque':'owned'})
  except BaseException as e:errors.append(repr(e))
 thread=threading.Thread(target=publish);thread.start();ck(ready.wait(3),'publisher waiting at actual link')
 original=m.os.stat;fired=[False]
 def race(path,*a,**kw):
  if str(path).startswith('.pending-') and not fired[0]:fired[0]=True;finish.set();thread.join(3);ck(not thread.is_alive(),'publisher completed')
  return original(path,*a,**kw)
 m.os.stat=race
 try:r=m.StorageWatch(p,L).check();result={'accepted':True,'logical':r['logical_file_bytes'],'attempts':r['scan_attempts']}
 except BaseException as e:result={'accepted':False,'type':type(e).__name__}
 finally:finish.set();thread.join(3)
 ck(not errors and fired[0],'genuine publication completed')
 ck(result.get('type')=='FileNotFoundError' if modname.startswith('original') else result.get('logical')==(p/'published').stat().st_size and result['attempts']==2,'actual publication RED GREEN')
 record('genuine-publication-'+modname,**result)
# Ordinary census and observed refusals use actual filesystem objects.
for case in ('baseline','pending','logical','allocated','entries','depth','symlink','hardlink','sparse'):
 m=load('workflow_storage');p=root(case);limits=dict(L);(p/'a').write_bytes(b'abc')
 if case=='pending':(p/'.pending-live').write_bytes(b'opaque')
 if case=='logical':limits['max_logical_bytes']=2
 if case=='allocated':limits['max_allocated_bytes']=1
 if case=='entries':limits['max_entries']=1;(p/'b').write_bytes(b'x')
 if case=='depth':limits['max_depth']=1;(p/'d'/'e').mkdir(parents=True)
 if case=='symlink':(p/'b').symlink_to('a')
 if case=='hardlink':os.link(p/'a',p/'b')
 if case=='sparse':
  with (p/'sparse').open('wb') as f:f.truncate((1<<20)+1)
 try:r=m.StorageWatch(p,limits).check();ck(case in ('baseline','pending'),'must refuse '+case);ck(r['logical_file_bytes']==(9 if case=='pending' else 3),'full accounting');record(case,accepted=True,observation=r)
 except (ValueError,RuntimeError) as e:ck(case not in ('baseline','pending'),'must accept');record(case,accepted=False,type=type(e).__name__,reason=getattr(e,'reason',None),observation=getattr(e,'observation',{}))
# Late namespace cleanup must precede all metadata counts.
for case in ('late-growth','late-extra','disappear','replace','churn','cleanup-limit'):
 m=load('workflow_storage');p=root(case);(p/'a').write_bytes(b'x');(p/'z').mkdir();(p/'z'/'q').write_bytes(b'y');w=m.StorageWatch(p,{**L,'max_logical_bytes':3} if case=='cleanup-limit' else L);done=[False];scans=[0]
 original=m.os.scandir
 class Iterator:
  def __init__(self,path):self.path=path;self.it=original(path)
  def __iter__(self):return self
  def __next__(self):return next(self.it)
  def close(self):
   self.it.close()
   if self.path==p/'z' and (not done[0] or case=='churn'):
    done[0]=True;scans[0]+=1
    if case=='late-extra':(p/'extra').write_bytes(b'new')
    elif case=='disappear':os.rename(p/'a',p.parent/(case+'-retained'))
    elif case=='replace':os.rename(p/'a',p.parent/(case+'-retained'));(p/'a').write_bytes(b'new')
    else:
     with (p/'a').open('ab') as f:f.write(b'zz')
 m.os.scandir=Iterator
 try:r=w.check();ck(case not in ('churn','cleanup-limit'),'must fail mutation control');actual=sum(x.stat().st_size for x in p.rglob('*') if x.is_file());record('mutation-before-assert', scenario=case, actual=actual, observation=r);ck((case=='late-extra' and r['logical_file_bytes'] in (2,actual)) or (r['logical_file_bytes']==actual and r['scan_attempts']==2),'full changed rejoin');record(case,accepted=True,logical=actual,attempts=r['scan_attempts'])
 except (m.StorageMutationObservation,m.StorageLimit) as e:ck(case in ('churn','cleanup-limit'),'unexpected refusal');record(case,accepted=False,type=type(e).__name__,observation=e.observation)
# The deadline is one shared clock. No blocked-syscall preemption claim.
m=load('workflow_storage');p=root('deadline');w=m.StorageWatch(p,L);m.time=SimpleNamespace(monotonic=lambda:6,sleep=lambda x:None)
try:w._check(0,[])
except m.StorageLimit as e:ck(e.reason=='time','deadline');record('deadline',reason=e.reason)
else:raise AssertionError('deadline allowed')
m=load('workflow_storage');p=root('root-replaced');w=m.StorageWatch(p,L);p.rename(p.parent/'old-root-retained');p.mkdir()
try:w.check()
except ValueError as e:ck(str(e)=='owned storage root replaced','root fatal');record('root-replaced',refused=True)
else:raise AssertionError('root accepted')
# Actual nested descriptor unwind: the first fatal must remain selected and every close error retained.
m=load('workflow_storage');p=root('nested-cleanup');(p/'d').mkdir();(p/'d'/'f').write_bytes(b'x');first=KeyboardInterrupt('first fatal');seen=[];savedstat=m.os.stat;savedclose=m.os.close
class CloseError(RuntimeError):pass
def failstat(path,*a,**kw):
 if path=='f':raise first
 return savedstat(path,*a,**kw)
def failclose(fd):
 savedclose(fd);e=CloseError('descriptor '+str(fd));seen.append(e);raise e
m.os.stat=failstat;m.os.close=failclose
try:m.StorageWatch(p,L).check()
except BaseException as e:
 ck(e is first and len(seen)==2,'genuine first fatal and two actual closes')
 retained=list(getattr(e,'storage_cleanup_errors',()))
 record('nested-cleanup-successor',first_fatal_preserved=e is first,actual_closed_descriptor_errors=len(seen),retained_errors=len(retained),lost_earlier_error=seen[0] not in retained,selected_type=type(e).__name__)
 ck(len(retained)==2 and retained==seen,'both cleanup errors required')
else:raise AssertionError('fatal swallowed')
record('fd-inspection', baseline=fd0, fds={x:os.readlink('/proc/self/fd/'+x) for x in os.listdir('/proc/self/fd') if os.path.exists('/proc/self/fd/'+x)})
record('descriptor-count',before=fd0,after=len(os.listdir('/proc/self/fd')))
(H/'RAW_CONTROLS01.json').write_text(json.dumps({'checks':checks,'cases':rows},indent=2)+'\n')
print(json.dumps({'checks':checks,'case_count':len(rows),'result':'both nested cleanup objects retained'}))
