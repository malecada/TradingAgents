"""Actual owned FD/iterator and exact handler controls; no public run/proof/restore."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,types
D=Path(__file__).resolve().parent;A=D.parent/'financial-wrapper-compatibility-composed-recovery-preparation01-2026-10-04';O=D/'owned-matrix02';O.mkdir(mode=0o700);p=O/'opaque';p.write_bytes(b'opaque');p.chmod(0o600);rows=[]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=module('old',A/'verify01.py');new=module('new',D/'verify02.py')
assert new.OWNED_IO_BYTES==(D/'owned_io.py').read_bytes() and hashlib.sha256(new.OWNED_IO_BYTES).hexdigest()=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'
def fatal(e):return e is not None and (isinstance(e,MemoryError) or not isinstance(e,Exception))
def contains(root,target):
 todo=[root];seen=set()
 while todo:
  e=todo.pop()
  if e is target:return True
  if id(e) in seen:continue
  seen.add(id(e))
  if isinstance(e,BaseException):
   todo.extend(BaseException.__dict__['__dict__'].__get__(e).values())
   for key in ['__cause__','__context__']:
    value=BaseException.__dict__[key].__get__(e)
    if value is not None:todo.append(value)
   if isinstance(e,BaseExceptionGroup):todo.extend(BaseExceptionGroup.__dict__['exceptions'].__get__(e))
  elif isinstance(e,(list,tuple)):todo.extend(e)
 return False

def readcase(m,primary,secondary):
 proxy=types.SimpleNamespace(**vars(os));fds=[];closed=[];real=m.os
 def open(*a,**k):fd=os.open(*a,**k);fds.append(fd);return fd
 def read(fd,n):
  if primary is not None:raise primary
  return os.read(fd,n)
 def close(fd):
  os.close(fd);closed.append(fd)
  if secondary is not None:raise secondary
 proxy.open=open;proxy.read=read;proxy.close=close;m.os=proxy;escaped=None;r=m.Reader()
 try:
  try:r.read(p)
  except BaseException as e:escaped=e
 finally:m.os=real
 assert len(fds)==1 and closed==fds
 for fd in fds:
  try:os.fstat(fd)
  except OSError:pass
  else:raise AssertionError('FD open')
 if primary is not None or secondary is not None:assert not r.cache
 return escaped

def scancase(m,primary,secondary):
 proxy=types.SimpleNamespace(**vars(os));real=m.os;opened=[];closed=[]
 class Iterator:
  def __init__(self,path):self.it=os.scandir(path);opened.append(self)
  def __enter__(self):return self
  def __iter__(self):return self
  def __next__(self):
   e=next(self.it)
   if primary is not None:raise primary
   return e
  def close(self):
   self.it.close();closed.append(self)
   if secondary is not None:raise secondary
  def __exit__(self,*args):self.close()
 proxy.scandir=Iterator;m.os=proxy;escaped=None;r=m.Reader()
 try:
  try:r.tree(O)
  except BaseException as e:escaped=e
 finally:m.os=real
 assert len(opened)==1 and closed==opened
 assert list(opened[0].it)==[]
 if primary is not None or secondary is not None:assert not r.trees
 return escaped

def expected(primary,secondary,actual):
 if fatal(primary):assert actual is primary
 elif fatal(secondary):assert actual is secondary
 elif secondary is not None:assert isinstance(actual,new.IO.CleanupFailure)
 elif primary is not None:assert actual is primary
 else:assert actual is None
 for e in (primary,secondary):
  if e is not None:assert contains(actual,e)

for which,fn,combos in [('CR1',readcase,[(ValueError,MemoryError),(ValueError,SystemExit)]),('CR2',scancase,[(KeyboardInterrupt,SystemExit),(MemoryError,ValueError)])]:
 for first,last in combos:
  a=first('primary');b=last('secondary');red=fn(old,a,b);wrong=(red is a if which=='CR1' else red is b);assert wrong
  a=first('primary');b=last('secondary');green=fn(new,a,b);expected(a,b,green)
  rows.append({'case':which,'primary':first.__name__,'secondary':last.__name__,'old_wrong_escape':type(red).__name__,'new_escape':type(green).__name__,'actual_cleanup_once':True,'all_actual_objects_reachable':True})
for which,fn in [('read',readcase),('scan',scancase)]:
 for ptype in [None,ValueError,MemoryError,KeyboardInterrupt,SystemExit]:
  for stype in [None,OSError,MemoryError,KeyboardInterrupt,SystemExit]:
   a=None if ptype is None else ptype('primary');b=None if stype is None else stype('secondary');escaped=fn(new,a,b);expected(a,b,escaped);rows.append({'case':which+' cleanup matrix','primary':None if ptype is None else ptype.__name__,'secondary':None if stype is None else stype.__name__,'escape':None if escaped is None else type(escaped).__name__,'actual_resource_closed_once':True,'cache_or_tree_not_accepted_on_failure':True})
# Exact public handler AST only; run(), parser and success output are never invoked.
def handler(path):
 t=ast.parse(path.read_bytes());main=next(n for n in t.body if isinstance(n,ast.If));tr=next(n for n in main.body if isinstance(n,ast.Try));return compile(ast.Module(body=tr.handlers[0].body,type_ignores=[]),'exact public handler only','exec')
oldhandler=handler(A/'verify01.py');newhandler=handler(D/'verify02.py')
def diagnostic(code,ptype,stype,stage):
 secondary=stype('diagnostic') if stype is not None else None
 class Hostile(ptype):
  def __str__(self):
   if stage=='str' and secondary is not None:raise secondary
   return 'opaque'
 primary=Hostile('body');outputs=[]
 def dumps(*a,**k):
  if stage=='json' and secondary is not None:raise secondary
  return json.dumps(*a,**k)
 def output(*a,**k):
  if stage=='print' and secondary is not None:raise secondary
  outputs.append(a)
 ns={'json':types.SimpleNamespace(dumps=dumps),'print':output,'_finish':new._finish};escaped=None
 try:
  try:raise primary
  except BaseException as error:ns['error']=error;exec(code,ns)
 except BaseException as e:escaped=e
 return primary,secondary,escaped
for ptype,stype,stage in [(KeyboardInterrupt,SystemExit,'str'),(MemoryError,OSError,'print')]:
 a,b,red=diagnostic(oldhandler,ptype,stype,stage);assert red is b
 a,b,green=diagnostic(newhandler,ptype,stype,stage);expected(a,b,green);rows.append({'case':'CR3','stage':stage,'old_wrong_escape':type(red).__name__,'new_original_fatal_preserved':green is a,'all_objects_reachable':contains(green,b)})
for stage in ['str','json','print']:
 for ptype in [ValueError,MemoryError,KeyboardInterrupt,SystemExit]:
  for stype in [None,OSError,MemoryError,KeyboardInterrupt,SystemExit]:
   a,b,e=diagnostic(newhandler,ptype,stype,stage);expected(a,b,e);rows.append({'case':'diagnostic matrix','stage':stage,'primary':ptype.__name__,'secondary':None if stype is None else stype.__name__,'escape':type(e).__name__,'actual_objects_retained':True})
# Nested actual two-FD cleanup: every close once, earliest fatal retained across levels.
fds=[os.open(p,os.O_RDONLY),os.open(p,os.O_RDONLY)];first=MemoryError('first close fatal');last=SystemExit('later outer close fatal');body=ValueError('ordinary body');closed=[]
def close(fd,error):os.close(fd);closed.append(fd);raise error
def nested():
 try:raise body
 finally:new._finish((lambda:close(fds[0],first),),body)
try:new._finish((nested,lambda:close(fds[1],last)),None)
except BaseException as e:assert e is first and contains(e,body) and contains(e,last)
else:raise AssertionError('missing nested fatal')
assert closed==fds
for fd in fds:
 try:os.fstat(fd)
 except OSError:pass
 else:raise AssertionError('nested FD leak')
rows.append({'case':'nested actual twoFD firstfatal','all_actual_objects_reachable':True,'actual_descriptors_closed_once':2})
# Hostile diagnostic/cause access cannot replace a preselected fatal.
class HostileFatal(KeyboardInterrupt):
 def __getattribute__(self,n):
  if n in ('__cause__','__context__','__dict__'):raise SystemExit('hostile getter')
  return super().__getattribute__(n)
 def __setattr__(self,n,v):raise SystemExit('hostile setter')
fatalobj=HostileFatal('primary');secondary=OSError('cleanup')
try:
 try:raise fatalobj
 finally:new._finish((lambda:(_ for _ in ()).throw(secondary),),fatalobj)
except BaseException as e:assert e is fatalobj and contains(e,secondary)
rows.append({'case':'hostile fatal descriptors actualobject retained','passed':True})
(D/'CONTROLS02.json').write_text(json.dumps({'schema_version':1,'no_public_run_or_proof':True,'source_sha256':hashlib.sha256((D/'verify02.py').read_bytes()).hexdigest(),'rows':rows},indent=2)+'\n');print(len(rows))
