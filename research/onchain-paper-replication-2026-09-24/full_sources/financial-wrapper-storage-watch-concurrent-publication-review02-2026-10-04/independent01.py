import ast,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-wrapper-storage-watch-concurrent-publication-correction02-2026-10-04';old=B/'financial-wrapper-storage-watch-concurrent-publication-correction01-2026-10-04';prior=B/'financial-wrapper-storage-watch-concurrent-publication-review01-2026-10-04';checks=0;rows=[]
def ck(x,label):
 global checks
 checks+=1
 if not x:raise AssertionError(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(case,**kw):rows.append({'case':case,**kw});(H/'INDEPENDENT_PROGRESS01.json').write_text(json.dumps(rows,indent=2)+'\n')
def authenticate(root,pin):
 ck(sha(root/'MANIFEST01.json')==pin,'manifest anchor');v=json.loads((root/'MANIFEST01.json').read_text());listed=set()
 for r in v['members']:
  p=root/r['path'];listed.add(r['path']);s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'mode')
  if r['kind']=='file':ck(stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p)==r['sha256'] and s.st_nlink==r['links'],'body')
  elif r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'directory')
  else:ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'link')
 ck({str(p.relative_to(root)) for p in root.rglob('*')}==listed|{'MANIFEST01.json'}|set(v.get('excluded_execution_streams',[])),'complete census')
 for g in v.get('literal_retained_hardlink_groups',[]):ck(len({(root/x).stat().st_ino for x in g})==1,'literal hardlinks')
 return len(listed)
counts=[authenticate(A,'7010c22de559e838a7815260caf612f3ebcb9fad3a2bfa3a39509c63b5ce413b'),authenticate(old,'ffbcc1efc6e56d1bf5b19830dd46a279e79f0a2b242e0e3a8ca182da421aaafb'),authenticate(prior,'da3279ce476d772db5b5f1950cdd529bb673e2074b03e2c0a716b4dc0e569300')]
inv=json.loads((A/'INVERSE01.json').read_text());n=(A/'workflow_storage.py').read_text();o=(old/'workflow_storage.py').read_text();ck(n.count(inv['new_literal'])==1 and n.replace(inv['new_literal'],inv['old_literal'])==o,'full single inverse');ck(sha(A/'workflow_storage.py')=='21e21dddc5b5008c3dc016839fc5b05c60dfbd345d224e91b8a9c3fb551c62cf','new source pin')
def stripped(s):
 t=ast.parse(s);t.body=[n for n in t.body if not (isinstance(n,ast.FunctionDef) and n.name=='_cleanup')];return ast.dump(t,include_attributes=False)
ck(stripped(n)==stripped(o),'only cleanup AST changed');record('authentication',scope_members=counts,full_literal_inverse=True,only_cleanup_ast_changed=True)
def load(path):
 s=importlib.util.spec_from_file_location('subject',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.os=SimpleNamespace(**vars(os));return m
def dictionary(e):return BaseException.__dict__['__dict__'].__get__(e)
def graph(e):
 q=[e];found=[]
 while q:
  x=q.pop()
  if any(x is y for y in found):continue
  found.append(x)
  for name in ('__cause__','__context__'):
   y=BaseException.__dict__[name].__get__(x)
   if y is not None:q.append(y)
  a=dict.get(dictionary(x),'storage_cleanup_errors',())
  q.extend(y for y in (a if type(a)is tuple else (a,)) if isinstance(y,BaseException))
  if isinstance(x,BaseExceptionGroup):q.extend(x.exceptions)
 return found
L=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
before=len(os.listdir('/proc/self/fd'))
# Vary first fatal, number of real recursive opens and secondary fatal type.
for label,directory in [('old',old),('new',A)]:
 for primarytype in (KeyboardInterrupt,MemoryError,SystemExit):
  for secondarytype in (RuntimeError,MemoryError,KeyboardInterrupt,SystemExit):
   m=load(directory/'workflow_storage.py');p=H/'nested'/label/primarytype.__name__/secondarytype.__name__; (p/'d'/'e').mkdir(parents=True);(p/'d'/'e'/'f').write_bytes(b'x');first=primarytype('first');seen=[];fds=[]
   def st(path,*a,**kw):
    if path=='f':raise first
    return os.stat(path,*a,**kw)
   def close(fd):
    os.close(fd);fds.append(fd);e=secondarytype('secondary');seen.append(e);raise e
   m.os.stat=st;m.os.close=close
   try:m.StorageWatch(p,L).check()
   except BaseException as e:
    present=[any(x is y for y in graph(e)) for x in seen];ck(e is first and len(seen)==3 and len(set(fds))==3,'first fatal/all real closes')
    ck(present==([False,False,True] if label=='old' else [True]*3),'old RED new GREEN')
    for fd in fds:
     try:os.fstat(fd)
     except OSError:pass
     else:raise AssertionError('descriptor open')
    record('real-three-level-unwind',source=label,primary=primarytype.__name__,secondary=secondarytype.__name__,first_fatal=True,all_error_presence=present,closed_once=len(fds))
   else:raise AssertionError('fatal accepted')
# Cleanup itself must not execute arbitrary subclass hooks.
m=load(A/'workflow_storage.py');p=H/'hostile';p.mkdir();called=[]
class Hostile(KeyboardInterrupt):
 @property
 def __dict__(self):called.append('dict');raise SystemExit('unsafe dict')
 @property
 def storage_cleanup_errors(self):called.append('property');raise SystemExit('unsafe errors')
 def __getattribute__(self,name):
  if name in ('storage_cleanup_errors','__dict__'):called.append('getattribute');raise SystemExit('unsafe access')
  return super().__getattribute__(name)
 def __setattr__(self,name,value):called.append('setattr');raise SystemExit('unsafe set')
 def __str__(self):called.append('str');raise SystemExit('unsafe str')
 def __repr__(self):called.append('repr');raise SystemExit('unsafe repr')
 def add_note(self,x):called.append('note');raise SystemExit('unsafe note')
first=Hostile();earlier=OSError('existing');dictionary(first)['storage_cleanup_errors']=(earlier,);seen=[]
for cls in (RuntimeError,KeyboardInterrupt,MemoryError,SystemExit):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY);e=cls('close');seen.append(e)
 def action():os.close(fd);raise e
 try:m._cleanup(action,first)
 except BaseException as selected:ck(selected is first,'hostile first fatal')
 else:raise AssertionError('hostile accepted')
ck(not called and dictionary(first)['storage_cleanup_errors']==(earlier,*seen),'bypass all hooks retain originals');record('cleanup-descriptor-overrides',hooks_called=called,retained_originals=5)
# Full StorageWatch check with the same hostile get/set hooks retains first fatal.
m=load(A/'workflow_storage.py');p=H/'hostile-full';(p/'d').mkdir(parents=True);(p/'d'/'f').write_bytes(b'x');first=Hostile();seen=[];called.clear()
def st(path,*a,**kw):
 if path=='f':raise first
 return os.stat(path,*a,**kw)
def close(fd):os.close(fd);e=RuntimeError('close');seen.append(e);raise e
m.os.stat=st;m.os.close=close
try:m.StorageWatch(p,L).check()
except BaseException as e:ck(e is first and all(any(x is y for y in graph(e)) for x in seen),'full hostile first fatal');record('full-watch-hostile-diagnostics',first_fatal=True,errors_retained=len(seen),diagnostic_hooks=called[:])
else:raise AssertionError('fatal accepted')
# A more adversarial inherited diagnostic boundary is measured separately.
class CauseHostile(KeyboardInterrupt):
 @property
 def __cause__(self):raise SystemExit('cause-property-diagnostic')
m=load(A/'workflow_storage.py');p=H/'cause-hostile';p.mkdir();(p/'f').write_bytes(b'x');first=CauseHostile()
def st(path,*a,**kw):
 if path=='f':raise first
 return os.stat(path,*a,**kw)
m.os.stat=st
try:m.StorageWatch(p,L).check()
except BaseException as e:record('inherited-cause-property-boundary',first_fatal=e is first,selected_type=type(e).__name__,original_in_graph=any(first is x for x in graph(e)))
else:raise AssertionError('fatal accepted')
ck(len(os.listdir('/proc/self/fd'))==before,'no owned fd leak');record('descriptor-count',before=before,after=len(os.listdir('/proc/self/fd')))
(H/'INDEPENDENT01.json').write_text(json.dumps({'checks':checks,'rows':rows},indent=2)+'\n');print(json.dumps({'checks':checks,'rows':len(rows)}))
