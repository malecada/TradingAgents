"""Complete owned preparation-tree manifest; excludes one exact root file only."""
import hashlib,json,os,stat
from pathlib import Path

def collect(root,manifest_name='MANIFEST02.json'):
 root=Path(root);assert root.is_absolute() and root.resolve()==root
 excluded=root/manifest_name;assert excluded.parent==root
 rows=[]
 for p in sorted(root.rglob('*')):
  if p==excluded:continue
  s=p.lstat();assert not p.is_symlink() and (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode))
  row={'path':p.relative_to(root).as_posix(),'type':'directory' if stat.S_ISDIR(s.st_mode) else 'file','mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISREG(s.st_mode):
   assert s.st_nlink==1 and s.st_size<=4*1024**2
   fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
   try:
    b=os.read(fd,4*1024**2+1);after=os.fstat(fd);assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) and len(b)==s.st_size
   finally:os.close(fd)
   row.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  rows.append(row)
 assert len(rows)==len(list(root.rglob('*')))-int(excluded.exists())
 return rows
if __name__=='__main__':
 root=Path(__file__).resolve().parent
 target=root/'MANIFEST02.json';assert not target.exists()
 rows=collect(root)
 with target.open('xb') as f:f.write((json.dumps({'schema_version':1,'status':'DRAFT_NOT_RELEASED','entries':rows,'excluded_exact_path':'MANIFEST02.json','implementation_count':199,'package_count':148,'changed_bodies':1,'paper_credit':0},indent=2,sort_keys=True)+'\n').encode());f.flush();os.fsync(f.fileno())
