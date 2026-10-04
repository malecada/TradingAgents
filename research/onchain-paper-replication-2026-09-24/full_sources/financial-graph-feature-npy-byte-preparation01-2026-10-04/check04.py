import json,os,struct,time
from pathlib import Path
import npy_bytes02 as N
ROOT=Path(__file__).resolve().parent; CASE=ROOT/'cases04';CASE.mkdir(); checks=[]
b="{'descr': '<f4', 'fortran_order': False, 'shape': (4, 32), }";pad=64-(10+len(b)+1)%64;h=b'\x93NUMPY\x01\x00'+struct.pack('<H',len(b)+pad+1)+b.encode()+b' '*pad+b'\n';raw=b'opaque0123456789'*32
v={k:N.sha(k.encode()) for k in N.ROLES};v.update(member='array-000000.npy',rows=4,columns=32,dtype='<f4',order='C',file_bytes=len(h+raw),file_sha256=N.sha(h+raw),header_sha256=N.sha(h),payload_sha256=N.sha(raw))
def fixture(name,override=None):
 d=CASE/name;d.mkdir();p=d/v['member'];p.write_bytes(h+raw);p.chmod(0o600);m=dict(v);m.update(override or {});return p,N.canonical(m)
def reject(call,name,kind=ValueError):
 try:call()
 except kind as e:checks.append({'case':name,'error':repr(e)});return
 raise AssertionError('accepted '+name)
for field in ('file_sha256','header_sha256','payload_sha256'):
 p,m=fixture(field,{field:'0'*64})
 def go():
  c=N.Cursor(p,m);c.read(0,512);c.finish()
 reject(go,field)
p,m=fixture('deadline');c=N.Cursor(p,m);c.deadline=0;reject(lambda:c.read(0,4),'sampled deadline');assert c.fd is None
p,m=fixture('floor');realstat=os.statvfs
class Low:
 f_bavail=0;f_frsize=4096
try:
 os.statvfs=lambda p:Low()
 reject(lambda:N.Cursor(p,m),'floor')
finally:os.statvfs=realstat
p,m=fixture('header-short');realread=os.read
try:
 os.read=lambda fd,n:realread(fd,n-1)
 reject(lambda:N.Cursor(p,m),'constructor short read')
finally:os.read=realread
p,m=fixture('link');link=p.parent.parent/'array-000000.npy';link.symlink_to(p);reject(lambda:N.Cursor(link,m),'literal symlink')
p,m=fixture('hardlink');os.link(p,p.parent/'other');reject(lambda:N.Cursor(p,m),'hardlink')
p,m=fixture('mode-change');c=N.Cursor(p,m);p.chmod(0o640);reject(lambda:c.read(0,4),'mode change')
p,m=fixture('body-extra');c=N.Cursor(p,m)
with p.open('ab') as f:f.write(b'X')
reject(lambda:c.read(0,4),'body added after open')
# Actual final verifier cleanup mutation; ensure its ctime has an observable
# advance. This is explicitly sampled fingerprint evidence, not all possible
# sub-tick mutations.
p,m=fixture('verify-close-mutation');c=N.Cursor(p,m);c.read(0,512);close=os.close;seen=[];old=p.stat().st_mtime_ns
try:
 def hook(fd):
  close(fd);seen.append(fd)
  if len(seen)==2:
   with p.open('r+b') as f:f.seek(len(h));f.write(b'X');f.flush();os.fsync(f.fileno())
   os.utime(p,ns=(p.stat().st_atime_ns,old+1_000_000_000))
 os.close=hook
 reject(c.finish,'final verifier cleanup mutation with changed fingerprint')
finally:os.close=close
assert len(seen)==2 and c.state=='FAILED' and c.fd is None
# Real EOF and verifier read failures, and final close failure retain no proof.
for stage in ('eof','final-read','final-close'):
 p,m=fixture(stage);c=N.Cursor(p,m);c.read(0,512);realread=os.read;realclose=os.close;calls=[]
 try:
  if stage in ('eof','final-read'):
   def read(fd,n):
    calls.append(n)
    if (stage=='eof' and len(calls)==1):return b'X'
    if (stage=='final-read' and len(calls)==2):return realread(fd,n-1)
    return realread(fd,n)
   os.read=read
   reject(c.finish,stage)
  else:
   def close(fd):
    realclose(fd);calls.append(fd)
    if len(calls)==2:raise OSError('actual verifier close uncertain')
   os.close=close;reject(c.finish,stage,N.IO.CleanupFailure)
 finally:os.read=realread;os.close=realclose
 assert c.state=='FAILED' and c.fd is None
# Pure metadata extent refuses overlarge shape without materializing payload.
body="{'descr': '<f4', 'fortran_order': False, 'shape': (9999999999, 32), }";pd=64-(10+len(body)+1)%64
reject(lambda:N.parse_header(b'\x93NUMPY\x01\x00'+struct.pack('<H',len(body)+pd+1)+body.encode()+b' '*pd+b'\n'),'projected payload ceiling')
(ROOT/'CHECKS04.json').write_bytes(N.canonical({'count':len(checks),'checks':checks}));print(json.dumps({'status':'PASS','checks':len(checks)}))
