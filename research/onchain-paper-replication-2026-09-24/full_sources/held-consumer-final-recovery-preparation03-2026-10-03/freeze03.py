"""Freeze honestly typed retained evidence; no production archive admission."""
import hashlib,json,os,stat
from pathlib import Path
p=Path(__file__).resolve().parent;rows=[]
for q in sorted(p.rglob('*')):
 if q==p/'MANIFEST03.json':continue
 s=q.lstat();r={'path':q.relative_to(p).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(q))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,nlink=s.st_nlink,sha256=hashlib.sha256(q.read_bytes()).hexdigest())
 elif stat.S_ISFIFO(s.st_mode):r.update(kind='fifo')
 else:raise RuntimeError(str(q))
 rows.append(r)
manifest={'schema_version':1,'scope':'Recovery03 preparation source and retained tiny synthetic evidence; not a production archive or external recovery','root_mode':stat.S_IMODE(p.stat().st_mode),'members':rows}
with (p/'MANIFEST03.json').open('x') as stream:stream.write(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
for name in ('recovery03.py','MANIFEST03.json','PROTOCOL03.md','INVERSE03.json'):print(name,hashlib.sha256((p/name).read_bytes()).hexdigest())
print('members',len(rows))
