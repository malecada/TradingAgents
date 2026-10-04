"""Audit the explicit sampled-boundary limit; no claim of an exhaustive race test."""
import json,os,struct
from pathlib import Path
import npy_bytes02 as N
root=Path(__file__).resolve().parent/'boundary01';root.mkdir();records=[]
b="{'descr': '<f4', 'fortran_order': False, 'shape': (4, 32), }";pad=64-(10+len(b)+1)%64;h=b'\x93NUMPY\x01\x00'+struct.pack('<H',len(b)+pad+1)+b.encode()+b' '*pad+b'\n';raw=b'opaque0123456789'*32
for i in range(12):
 d=root/str(i);d.mkdir();p=d/'array-000000.npy';p.write_bytes(h+raw)
 v={k:N.sha(k.encode()) for k in N.ROLES};v.update(member=p.name,rows=4,columns=32,dtype='<f4',order='C',file_bytes=len(h+raw),file_sha256=N.sha(h+raw),header_sha256=N.sha(h),payload_sha256=N.sha(raw))
 c=N.Cursor(p,N.canonical(v));c.read(0,512);original=os.close;seen=[];r={'case':i,'before':list(c.initial)}
 try:
  def hook(fd):
   original(fd);seen.append(fd)
   if len(seen)==2:
    with p.open('r+b') as f:f.seek(len(h));f.write(b'X');f.flush();os.fsync(f.fileno())
  os.close=hook
  try:c.finish();r['accepted']=True
  except BaseException as e:r['accepted']=False;r['error']=repr(e)
 finally:os.close=original
 r.update(after=list(N.fingerprint(p.stat())),current_sha256=N.sha(p.read_bytes()),expected_sha256=v['file_sha256']);records.append(r)
Path('SAMPLED_BOUNDARY01.json').write_bytes(N.canonical({'records':records,'accepted_after_injected_final_close':sum(r['accepted'] for r in records)}));print(json.dumps({'accepted':sum(r['accepted'] for r in records),'refused':sum(not r['accepted'] for r in records)}))
