import ast,ctypes,errno,fcntl,hashlib,importlib.util,json,mmap,os,stat,struct,sys,threading
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'replay'));import npy_bytes03 as N
checks=[]; events=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(fn,n,kind=Exception):
 try:fn()
 except kind as e:checks.append(n+':'+type(e).__name__);return e
 raise AssertionError(n)
libc=ctypes.CDLL(None,use_errno=True);libc.memfd_create.argtypes=[ctypes.c_char_p,ctypes.c_uint];libc.memfd_create.restype=ctypes.c_int
raw=bytes(range(128))*2
def hdr(v=(1,0)):
 b=b"{'descr': '<f4', 'fortran_order': False, 'shape': (2, 32), }";k=2 if v==(1,0) else 4;p=64-((8+k+len(b)+1)%64);return b'\x93NUMPY'+bytes(v)+(len(b)+p+1).to_bytes(k,'little')+b+b' '*p+b'\n'
def meta(h):
 d={k:N.sha(k.encode()) for k in N.ROLES};d.update(member='array-000000.npy',rows=2,columns=32,dtype='<f4',order='C',file_bytes=len(h+raw),file_sha256=N.sha(h+raw),header_sha256=N.sha(h),payload_sha256=N.sha(raw));return N.canonical(d)
def make(data,seals=15):
 f=libc.memfd_create(b'independent-opaque',3)
 if f<0:raise OSError(ctypes.get_errno(),'memfd')
 os.write(f,data)
 if seals:fcntl.fcntl(f,1033,seals)
 return f
for v in [(1,0),(2,0),(3,0)]:
 h=hdr(v);m=meta(h);f=make(h+raw);alias=os.dup(f)
 try:
  with N.sealed_cursor(f,m,H) as c:
   ok(c.fd!=f and not os.get_inheritable(c.fd),'owned duplicate cloexec')
   os.lseek(alias,0,0)
   ok(c.read(0,128)+c.read(128,128)==raw,'pread ignores external alias offset')
   p=c.finish();q=json.loads(p);ok(q['file_sha256']==N.sha(h+raw) and q['payload_sha256']==N.sha(raw),'full opaque hash')
   ok(q['production_authority'] is False and q['original_component_path_current'] is False,'no scientific provenance')
   for name,fn in [('write',lambda:os.write(alias,b'X')),('pwrite',lambda:os.pwrite(alias,b'X',len(h))),('truncate',lambda:os.ftruncate(alias,1)),('grow',lambda:os.ftruncate(alias,1000)),('mmap',lambda:mmap.mmap(alias,0,access=mmap.ACCESS_WRITE))]:
    e=refuse(fn,name);ok(isinstance(e,OSError) and e.errno in (errno.EPERM,errno.EACCES),'kernel errno '+name)
   alt=os.open('/proc/self/fd/'+str(f),os.O_RDWR)
   try:refuse(lambda:os.pwrite(alt,b'X',len(h)),'reopened write')
   finally:os.close(alt)
   ok(c.consume(lambda b:b)==p,'live proof access')
  ok(c.fd is None and c.state=='RELEASED','context release')
  refuse(lambda:c.consume(lambda x:x),'escaped cursor unavailable')
  ok(os.pread(alias,len(h+raw),0)==h+raw,'inode unchanged after all attempts')
 finally:os.close(alias);os.close(f)
h=hdr();m=meta(h)
# Ordinary route refuses before it can observe any body; original failed cases are never replayed.
for path in [H/'absent.npy',H/'replay/npy_bytes03.py']:
 refuse(lambda:N.Cursor(path,m),'ordinary path failclosed',PermissionError)
for bit in (1,2,4,8):
 f=make(h+raw,15^bit)
 try:refuse(lambda:N.SealedCursor(f,m,H),'missing seal '+str(bit))
 finally:os.close(f)
f=make(h+raw,0);mapped=mmap.mmap(f,0,access=mmap.ACCESS_WRITE)
try:
 e=refuse(lambda:fcntl.fcntl(f,1033,15),'existing writer prevents seal');ok(e.errno==errno.EBUSY,'real EBUSY')
finally:mapped.close();os.close(f)
# Copy-on-write private mapping can change its own view only.
f=make(h+raw)
try:
 mapped=mmap.mmap(f,0,access=mmap.ACCESS_COPY);mapped[len(h):len(h)+1]=b'Y';ok(os.pread(f,len(h+raw),0)==h+raw,'private map cannot mutate inode');mapped.close()
finally:os.close(f)
for change in ('metadata','proof','thread','deadline','partial','offset','boolsize'):
 f=make(h+raw);c=N.SealedCursor(f,m,H)
 try:
  if change=='metadata':c.spec['rows']=True;refuse(lambda:c.read(0,4),'metadata changed')
  elif change=='proof':c.read(0,256);c.finish();c._proof=b'{}';refuse(lambda:c.consume(lambda p:p),'proof mutated')
  elif change=='thread':
   seen=[]
   def run():
    try:c.read(0,4)
    except BaseException as e:seen.append(type(e).__name__)
   t=threading.Thread(target=run);t.start();t.join();ok(seen==['ValueError'],'thread refused')
  elif change=='deadline':c.deadline=0;refuse(lambda:c.read(0,4),'deadline')
  elif change=='partial':c.read(0,4);refuse(c.finish,'partial footer')
  elif change=='offset':refuse(lambda:c.read(4,4),'offset')
  else:refuse(lambda:c.read(0,True),'boolsize')
  ok(c.fd is None and c.state=='FAILED','failure closes duplicate '+change)
 finally:os.close(f)
# Callback raises and its owned descriptor really closes before secondary fatal.
for primary in (KeyboardInterrupt('first'),MemoryError('first'),SystemExit(2)):
 for secondary in (OSError('close'),MemoryError('close'),KeyboardInterrupt('close')):
  f=make(h+raw);real=os.close;slot={};calls=[]
  def close(fd):
   real(fd)
   if fd==slot.get('fd'):calls.append(slot['c'].state);raise secondary
  try:
   try:
    with N.sealed_cursor(f,m,H) as c:
     slot.update(fd=c.fd,c=c);c.read(0,256);c.finish();os.close=close;raise primary
   except BaseException as e:ok(e is primary,'first fatal identity')
   ok(calls==['RELEASED'] and c.fd is None,'revoked before real close')
   refuse(lambda:os.fstat(slot['fd']),'actual duplicate closed',OSError)
  finally:os.close=real;os.close(f)
old=(H/'replay/npy_bytes02.original.py').read_text();new=(H/'replay/npy_bytes03.py').read_text();prefix,tail=new.split('\n# Explicit separate engineering domain.',1)
guard="        raise PermissionError('UNAVAILABLE: ordinary-path inode writer exclusion is not enforced; stat fingerprints and repeated hashes are insufficient')\n"
inverse=prefix.replace(guard,'').rstrip()+'\n';ok(prefix.count(guard)==1 and inverse==old,'full literal inverse');ok(ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)),'full AST inverse')
# The production module performs no memfd construction, seal setting, copy or write.
a=ast.parse(new);calls=[n.func for n in ast.walk(a) if isinstance(n,ast.Call)];ok(not any(isinstance(f,ast.Attribute) and f.attr in ('write','pwrite','memfd_create','ftruncate','CDLL') for f in calls),'reader does not create/copy/seal/write')
ok(all(x not in sys.modules for x in ('numpy','torch','pandas','scipy')),'no numerical imports')
(H/'CHECKS01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'domain':'actual kernel-sealed anonymous opaque inode only','scientific_authority':False},indent=2)+'\n');print(json.dumps({'checks':len(checks),'passed':True}))
