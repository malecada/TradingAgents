import ast,errno,fcntl,hashlib,importlib.util,json,mmap,os,stat,struct,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import npy_bytes03 as N
spec=importlib.util.spec_from_file_location('old_npy',H/'npy_bytes02.original.py');O=importlib.util.module_from_spec(spec);sys.modules[spec.name]=O;spec.loader.exec_module(O)
checks=[];results=[];root=H/'opaque';root.mkdir(mode=0o700)
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(fn,n):
 try:fn()
 except BaseException as e:checks.append(n+':'+type(e).__name__);return e
 raise AssertionError(n)
def header(version=(1,0),rows=4):
 b="{'descr': '<f4', 'fortran_order': False, 'shape': (%d, 32), }"%rows
 code='<H' if version==(1,0) else '<I';pad=64-((8+struct.calcsize(code)+len(b)+1)%64)
 return b'\x93NUMPY'+bytes(version)+struct.pack(code,len(b)+pad+1)+b.encode()+b' '*pad+b'\n'
def metadata(h,raw,rows=4):
 v={k:N.sha(('opaque-'+k).encode()) for k in N.ROLES};v.update(member='array-000000.npy',rows=rows,columns=32,dtype='<f4',order='C',file_bytes=len(h+raw),file_sha256=N.sha(h+raw),header_sha256=N.sha(h),payload_sha256=N.sha(raw));return N.canonical(v)
def mem(body,seals=N.REQUIRED_SEALS):
 fd=os.memfd_create('owned-opaque-npy',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING);os.write(fd,body)
 if seals:fcntl.fcntl(fd,fcntl.F_ADD_SEALS,seals)
 return fd
raw=b'opaque0123456789'*32;h=header();m=metadata(h,raw)
# Old route still constructs a reader on ordinary files; new route refuses the
# unenforceable premise BEFORE any payload read or returned proof.
p=root/'array-000000.npy';p.write_bytes(h+raw)
c=O.Cursor(p,m);ok(c.read(0,len(raw))==raw,'original ordinary-file reader available');c.abort()
refuse(lambda:N.Cursor(p,m),'successor ordinary-path unavailable')
fd=os.open(p,os.O_RDONLY)
try:refuse(lambda:N.SealedCursor(fd,m,root),'ordinary disk inode never becomes anonymous sealed authority')
finally:os.close(fd)
for version in ((1,0),(2,0),(3,0)):
 h=header(version);m=metadata(h,raw);fd=mem(h+raw);alias=os.dup(fd)
 try:
  c=N.SealedCursor(fd,m,root);parts=[]
  for off in range(0,len(raw),4):parts.append(c.read(off,4))
  proof=json.loads(c.finish());ok(b''.join(parts)==raw and proof['file_sha256']==N.sha(h+raw),'exact sealed opaque bytes '+str(version))
  ok(proof['header_hex']==h.hex() and proof['header_sha256']==N.sha(h) and proof['payload_sha256']==N.sha(raw),'literal header/raw/full hashes '+str(version))
  ok(c.fd is not None and c.state=='PROVEN','finish retains inode resource '+str(version))
  for name,fn in [('write',lambda:os.write(alias,b'X')),('pwrite',lambda:os.pwrite(alias,b'X',len(h))),('shrink',lambda:os.ftruncate(alias,1)),('grow',lambda:os.ftruncate(alias,len(h+raw)+1)),('shared-write-map',lambda:mmap.mmap(alias,0,access=mmap.ACCESS_WRITE)),('seal-change',lambda:fcntl.fcntl(alias,fcntl.F_ADD_SEALS,0))]:
   e=refuse(fn,'kernel all alias denial '+name+str(version));ok(isinstance(e,OSError) and e.errno in (errno.EPERM,errno.EACCES),'actual kernel errno '+name+str(version))
  reopened=os.open('/proc/self/fd/'+str(alias),os.O_RDWR)
  try:refuse(lambda:os.pwrite(reopened,b'X',len(h)),'reopened alias kernel denial '+str(version))
  finally:os.close(reopened)
  def consume(proof):
   refuse(lambda:os.pwrite(alias,b'X',len(h)),'callback write denied '+str(version))
   return json.loads(proof)['file_sha256']
  ok(c.consume(consume)==N.sha(h+raw),'consumption inside actual exclusion '+str(version))
  owned=c.fd;real=os.close;observed=[]
  def closehook(f):
   if f==owned:
    observed.append(c.state);refuse(lambda:c.consume(lambda x:x),'proof revoked before release close '+str(version));refuse(lambda:os.pwrite(alias,b'X',len(h)),'release-close alias write denied '+str(version))
   return real(f)
  try:os.close=closehook;c.release()
  finally:os.close=real
  ok(observed==['RELEASED'] and c.fd is None,'release ordering '+str(version));refuse(lambda:c.consume(lambda p:p),'no post-release current proof '+str(version))
  ok(os.pread(fd,len(h+raw),0)==h+raw,'all aliases original inode unchanged '+str(version))
 finally:os.close(alias);os.close(fd)
# Every missing mandatory seal refuses. Existing writable shared mapping prevents
# kernel exclusion from being installed; no fake token substitutes for it.
h=header();m=metadata(h,raw)
for missing in (fcntl.F_SEAL_WRITE,fcntl.F_SEAL_GROW,fcntl.F_SEAL_SHRINK,fcntl.F_SEAL_SEAL):
 fd=mem(h+raw,N.REQUIRED_SEALS&~missing)
 try:refuse(lambda:N.SealedCursor(fd,m,root),'missing exact kernel seal '+str(missing))
 finally:os.close(fd)
fd=mem(h+raw,0);mapping=mmap.mmap(fd,0,access=mmap.ACCESS_WRITE)
try:
 e=refuse(lambda:fcntl.fcntl(fd,fcntl.F_ADD_SEALS,N.REQUIRED_SEALS),'existing writable mapping prevents seal');ok(isinstance(e,OSError) and e.errno==errno.EBUSY,'actual existing-writer exclusion errno')
 refuse(lambda:N.SealedCursor(fd,m,root),'unexcluded mapped writer refused')
finally:mapping.close();os.close(fd)
# Read-only alias lifetime is independent of caller closing its original handle.
fd=mem(h+raw);c=N.SealedCursor(fd,m,root);os.close(fd);c.read(0,len(raw));proof=c.finish();ok(c.consume(lambda x:x)==proof,'owned duplicate retains original inode through consumption');c.release()
for name,data in [('truncated',h+raw[:-1]),('extra',h+raw+b'X'),('corrupt',h+raw[:-1]+b'X')]:
 fd=mem(data)
 try:
  if name=='corrupt':
   c=N.SealedCursor(fd,m,root);c.read(0,len(raw));refuse(c.finish,'immutable corruption hash refused');ok(c.fd is None and c.state=='FAILED','hash failure closed')
  else:refuse(lambda:N.SealedCursor(fd,m,root),name+' sealed extent refusal')
 finally:os.close(fd)
# Exact full-file ceiling: sparse anonymous negative, never a produced artifact.
fd=os.memfd_create('opaque-oversize',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING);os.ftruncate(fd,N.FILE_LIMIT+1);fcntl.fcntl(fd,fcntl.F_ADD_SEALS,N.REQUIRED_SEALS)
try:refuse(lambda:N.SealedCursor(fd,m,root),'kernel inode actual4MiB+1 cap refusal')
finally:os.close(fd)
for offset,size in [(1,4),(0,3),(False,4),(0,N.READ_LIMIT+4),(0,len(raw)+4)]:
 fd=mem(h+raw)
 try:c=N.SealedCursor(fd,m,root);refuse(lambda:c.read(offset,size),'same finite read rules '+str((offset,size)));ok(c.fd is None,'invalid read closes ownfd')
 finally:os.close(fd)
# Original reducer first-fatal ordering with real close followed by injected error.
for i,primary in enumerate((KeyboardInterrupt(),MemoryError(),SystemExit(8))):
 for j,later in enumerate((KeyboardInterrupt(),MemoryError(),ValueError('close'))):
  fd=mem(h+raw);c=N.SealedCursor(fd,m,root);c.read(0,len(raw));c.finish();owned=c.fd;real=os.close;seen=[]
  def closehook(f):
   real(f)
   if f==owned:seen.append(f);raise later
  def fail(proof):raise primary
  try:os.close=closehook;e=refuse(lambda:c.consume(fail),'fatal callback close pair '+str((i,j)))
  finally:os.close=real
  ok(e is primary and seen==[owned] and c.fd is None and c.state=='FAILED','first primary and actual owned close '+str((i,j)));os.close(fd)
# Floor and time remain sampled bounds, no change to values.
for kind in ('deadline','floor'):
 fd=mem(h+raw);c=N.SealedCursor(fd,m,root);original=N.os.statvfs
 try:
  if kind=='deadline':c.deadline=0
  else:
   class V:f_bavail=0;f_frsize=1
   N.os.statvfs=lambda p:V()
  refuse(lambda:c.read(0,4),kind+' refuses');ok(c.fd is None,kind+' cleanup')
 finally:N.os.statvfs=original;os.close(fd)
# Full inverse: legacy path guard + appended sealed-domain implementation only.
old=(H/'npy_bytes02.original.py').read_text();new=(H/'npy_bytes03.py').read_text();marker='\n# Explicit separate engineering domain.';prefix,addition=new.split(marker,1)
guard="        raise PermissionError('UNAVAILABLE: ordinary-path inode writer exclusion is not enforced; stat fingerprints and repeated hashes are insufficient')\n"
assert prefix.count(guard)==1
inverse=prefix.replace(guard,'').rstrip()+'\n';ok(inverse==old,'literal full inverse');ok(ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False),'AST full inverse')
for name in ('parse_header','expected','fingerprint','production','Envelope'):
 a=next(n for n in ast.parse(old).body if getattr(n,'name',None)==name);b=next(n for n in ast.parse(new).body if getattr(n,'name',None)==name);ok(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'unchanged original '+name)
ok(all(x not in sys.modules for x in ('numpy','torch','scipy','pandas')),'no numerical imports')
(H/'CHECKS01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'source_sha256':N.sha(new.encode()),'kernel_seals':N.REQUIRED_SEALS,'production_available':False},indent=2,sort_keys=True)+'\n');(H/'INVERSE01.json').write_text(json.dumps({'guard':guard,'append_marker':marker,'full_literal_inverse':True,'full_AST_inverse':True,'appended_sha256':N.sha((marker+addition).encode())},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks),'status':'PASS'}))
