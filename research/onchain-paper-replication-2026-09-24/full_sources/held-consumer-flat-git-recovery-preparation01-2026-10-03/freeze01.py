"""Typed evidence freeze, including retained adversarial links; no archive admission."""
import hashlib,json,os,stat
from pathlib import Path
p=Path(__file__).resolve().parent;rows=[]
for q in sorted(p.rglob('*')):
 if q==p/'MANIFEST01.json':continue
 s=q.lstat();r={'path':q.relative_to(p).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(q))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,nlink=s.st_nlink,sha256=hashlib.sha256(q.read_bytes()).hexdigest())
 else:raise RuntimeError('unselected evidence type '+str(q))
 rows.append(r)
manifest={'schema_version':1,'scope':'Flat Git source preparation and tiny real Git utility fixtures only; no actual capsule or origin recovery','root_mode':stat.S_IMODE(p.stat().st_mode),'members':rows}
with (p/'MANIFEST01.json').open('x') as stream:stream.write(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
for name in ('git_recovery01.py','bounded_git_fd01.py','MANIFEST01.json','PROTOCOL01.md','SOURCE_PINS01.json'):print(name,hashlib.sha256((p/name).read_bytes()).hexdigest())
print('members',len(rows),'regular_logical_bytes',sum(r.get('bytes',0) for r in rows))
