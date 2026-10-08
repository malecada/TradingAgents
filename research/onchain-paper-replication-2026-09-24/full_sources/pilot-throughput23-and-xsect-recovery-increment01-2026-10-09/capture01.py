import datetime,hashlib,io,json,stat,tarfile
from pathlib import Path
R=Path.cwd();D=Path(__file__).resolve().parent
S=D/'SELECTION01.json'
sel=json.loads(S.read_bytes());p=D/'increment01.tar';assert not p.exists()
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path'])
with tarfile.open(p,'x',format=tarfile.PAX_FORMAT) as t:
 for r in rows:
  q=R/r['path'];before=q.lstat();assert not q.is_symlink() and stat.S_IMODE(before.st_mode)==int(r['mode'],8)
  x=tarfile.TarInfo(r['path']);x.mode=int(r['mode'],8);x.uid=x.gid=x.mtime=0
  if r['type']=='directory':assert stat.S_ISDIR(before.st_mode);x.type=tarfile.DIRTYPE;t.addfile(x)
  else:
   assert stat.S_ISREG(before.st_mode) and before.st_nlink==1;raw=q.read_bytes();after=q.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink'))
   assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'];x.size=len(raw);t.addfile(x,io.BytesIO(raw))
with tarfile.open(p,'r') as t:
 members=t.getmembers();assert len(members)==len(rows) and len({m.name for m in members})==len(rows)
 for m,r in zip(members,rows,strict=True):
  assert m.name==r['path'] and m.mode==int(r['mode'],8)
  if r['type']=='directory':assert m.isdir()
  else:assert m.isfile() and m.size==r['bytes'] and hashlib.sha256(t.extractfile(m).read()).hexdigest()==r['sha256']
raw=p.read_bytes();v={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':{'path':str(S.relative_to(R)),'sha256':hashlib.sha256(S.read_bytes()).hexdigest()},'archive':{'path':str(p.relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'files':sel['files'],'directories':len(sel['directories']),'regular_bytes':sel['body_bytes'],'actual_local_readback':True,'qualification':'Complete declared public throughput23 entry and actual xsect recovery metadata increment including original names/types/modes and opaque regular bodies. Private runtime, unchanged historical stores and scientific inputs excluded. Local capture does not establish external recovery, POSIX reconstruction, installed runtime or deletion authority.'}
(D/'CAPTURE01.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps(v))
