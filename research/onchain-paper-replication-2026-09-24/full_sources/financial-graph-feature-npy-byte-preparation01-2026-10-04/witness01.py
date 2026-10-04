from pathlib import Path
import json,os,struct
import npy_bytes01 as N
root=Path(__file__).resolve().parent/'witness01';root.mkdir()
b="{'descr': '<f4', 'fortran_order': False, 'shape': (4, 32), }";pad=64-(10+len(b)+1)%64;h=b'\x93NUMPY\x01\x00'+struct.pack('<H',len(b)+pad+1)+b.encode()+b' '*pad+b'\n';raw=b'opaque0123456789'*32;p=root/'array-000000.npy';p.write_bytes(h+raw)
v={k:N.sha(k.encode()) for k in N.ROLES};v.update(member=p.name,rows=4,columns=32,dtype='<f4',order='C',file_bytes=len(h+raw),file_sha256=N.sha(h+raw),header_sha256=N.sha(h),payload_sha256=N.sha(raw))
c=N.Cursor(p,N.canonical(v));c.read(0,512);fd=c.fd;close=os.close;records={'before':list(c.initial)}
def hook(i):
 close(i)
 if i==fd:
  with p.open('r+b') as f:f.seek(len(h));f.write(b'X');f.flush();os.fsync(f.fileno())
  records['after_hook']=list(N.fingerprint(p.stat()))
os.close=hook
try:
 try: records['proof']=json.loads(c.finish());records['accepted']=True
 except BaseException as e: records['error']=repr(e);records['accepted']=False
finally:os.close=close
records['current_hash']=N.sha(p.read_bytes());records['expected_hash']=v['file_sha256']
Path('WITNESS01.json').write_bytes(N.canonical(records));print(json.dumps(records))
