import ast,ctypes,errno,fcntl,hashlib,json,os,struct,sys,difflib
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import npy_bytes03 as N
checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(fn,n):
 try:fn()
 except BaseException as e:checks.append(n+':'+type(e).__name__);return e
 raise AssertionError(n)
b="{'descr': '<f4', 'fortran_order': False, 'shape': (1, 32), }";pad=64-(10+len(b)+1)%64;h=b'\x93NUMPY\x01\x00'+struct.pack('<H',len(b)+pad+1)+b.encode()+b' '*pad+b'\n';raw=b'x'*128
v={k:N.sha(k.encode()) for k in N.ROLES};v.update(member='array-000000.npy',rows=1,columns=32,dtype='<f4',order='C',file_bytes=len(h+raw),file_sha256=N.sha(h+raw),header_sha256=N.sha(h),payload_sha256=N.sha(raw));m=N.canonical(v)
libc=ctypes.CDLL(None,use_errno=True);libc.memfd_create.argtypes=(ctypes.c_char_p,ctypes.c_uint);libc.memfd_create.restype=ctypes.c_int
def fd():
 x=libc.memfd_create(b'opaque-context',3)
 if x<0:raise OSError(ctypes.get_errno(),'memfd_create')
 os.write(x,h+raw);fcntl.fcntl(x,N.F_ADD_SEALS,N.REQUIRED_SEALS);return x
for i,primary in enumerate((KeyboardInterrupt(),MemoryError(),SystemExit(1),ValueError('body'))):
 for j,later in enumerate((MemoryError(),ValueError('close'))):
  f=fd();close=os.close;events=[];slot={}
  def closehook(x):
   close(x)
   if x==slot.get('owned'):events.append((x,slot['cursor'].state));raise later
  def run():
   with N.sealed_cursor(f,m,H) as c:
    slot.update(cursor=c,owned=c.fd);c.read(0,128);c.finish();raise primary
  try:os.close=closehook;e=refuse(run,'structured body/close pair '+str((i,j)))
  finally:os.close=close;os.close(f)
  expected=primary if isinstance(primary,MemoryError) or not isinstance(primary,Exception) else (later if isinstance(later,MemoryError) else None)
  if expected is None:ok(isinstance(e,N.IO.CleanupFailure),'ordinary errors retained wrapper')
  else:ok(e is expected,'original first fatal identity '+str((i,j)))
  ok(len(events)==1 and events[0][1]=='RELEASED' and slot['cursor'].fd is None,'revocation precedes real close '+str((i,j)))
  refuse(lambda:slot['cursor'].consume(lambda p:p),'escaped cursor cannot reuse '+str((i,j)))
f=fd()
try:
 with N.sealed_cursor(f,m,H) as c:
  c.read(0,128);proof=c.finish();ok(c.consume(lambda p:p)==proof,'structured live proof')
 ok(c.state=='RELEASED' and c.fd is None,'structured normal close');refuse(lambda:c.consume(lambda p:p),'structured normal proof revoked')
finally:os.close(f)
# Malformed proof metadata remains caller assertion, not mutable authority.
f=fd()
try:
 c=N.SealedCursor(f,m,H);c.spec['graph_sha256']='0'*64;refuse(lambda:c.read(0,4),'mutable expected fields refused');ok(c.fd is None,'metadata mutation failure closed')
finally:os.close(f)
# Direct explicit finalizers also preserve an already active first fatal.
for method in ('release','abort'):
 f=fd();c=N.SealedCursor(f,m,H);owned=c.fd;close=os.close;primary=KeyboardInterrupt('body');later=MemoryError('close');events=[]
 def closehook(x):
  close(x)
  if x==owned:events.append(x);raise later
 try:
  os.close=closehook
  try:
   try:raise primary
   finally:getattr(c,method)()
  except BaseException as e:ok(e is primary,'direct '+method+' active firstfatal preserved')
 finally:os.close=close;os.close(f)
 ok(events==[owned] and c.fd is None,'direct '+method+' actual closed once')
# Final complete inverse and predecessor reader/parser/class function preservation.
old=(H/'npy_bytes02.original.py').read_text();new=(H/'npy_bytes03.py').read_text();marker='\n# Explicit separate engineering domain.';prefix,addition=new.split(marker,1);guard="        raise PermissionError('UNAVAILABLE: ordinary-path inode writer exclusion is not enforced; stat fingerprints and repeated hashes are insufficient')\n";inverse=prefix.replace(guard,'').rstrip()+'\n'
ok(prefix.count(guard)==1 and inverse==old,'final whole literal inverse');ok(ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False),'final whole AST inverse')
previous=(H/'npy_bytes03.draft03.py').read_text();prefix,tail=new.split('class SealedCursor(Cursor):',1);oldprefix,oldtail=previous.split('class SealedCursor(Cursor):',1);ok(prefix==oldprefix and tail.replace('self._close(sys.exception())','self._close()')==oldtail,'exact two direct active-exception cleanup substitutions')
(H/'SOURCE_FINAL05.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original_npy_bytes02',tofile='successor_npy_bytes03')))
(H/'INVERSE_FINAL05.json').write_text(json.dumps({'guard':guard,'appended_marker':marker,'appended_bytes':len((marker+addition).encode()),'appended_sha256':N.sha((marker+addition).encode()),'full_literal_inverse':True,'full_AST_inverse':True},indent=2,sort_keys=True)+'\n');(H/'CHECKS05.json').write_text(json.dumps({'checks':len(checks),'names':checks,'source_sha256':N.sha(new.encode()),'numeric_imports':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks),'status':'PASS'}))
