import datetime,hashlib,io,json,os,stat,tarfile
from pathlib import Path
R=Path.cwd();D=Path(__file__).resolve().parent

ALIAS_MEMBERS = {'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-normalization-connected-review01-2026-10-10/reference-body.bin': {'bytes': 14, 'device': 66310, 'inode': 7865445, 'mode': '0664', 'nlink': 2, 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-normalization-connected-review01-2026-10-10/reference-body.bin', 'sha256': '881ae31e592d550b22be2352b13010241c0598cf2b8fffec8bfd9da0cb6a806e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-normalization-connected-review01-2026-10-10/reference-hardlink': {'bytes': 14, 'device': 66310, 'inode': 7865445, 'mode': '0664', 'nlink': 2, 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-normalization-connected-review01-2026-10-10/reference-hardlink', 'sha256': '881ae31e592d550b22be2352b13010241c0598cf2b8fffec8bfd9da0cb6a806e'}}

def alias_signature(info):
    return (info.st_dev,info.st_ino,info.st_nlink,info.st_size,stat.S_IMODE(info.st_mode),stat.S_ISREG(info.st_mode))

def authenticate_alias_pair(root):
    # Exact historical fixture only; no general hardlink admission.
    before={}
    for name,metadata in ALIAS_MEMBERS.items():
        path=root/name
        assert path.parent.resolve(strict=True)==path.parent, name
        before[name]=path.lstat()
        assert alias_signature(before[name])==(66310,7865445,2,14,0o664,True), name
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
        try:
            assert alias_signature(os.fstat(fd))==alias_signature(before[name]), name
            body=os.read(fd,15)
            assert len(body)==14 and hashlib.sha256(body).hexdigest()==metadata['sha256'], name
            assert all(getattr(before[name],k)==getattr(os.fstat(fd),k) for k in ('st_dev','st_ino','st_nlink','st_mode','st_size','st_mtime_ns','st_ctime_ns')), name
        finally:os.close(fd)
    for name,info in before.items():
        after=(root/name).lstat()
        assert all(getattr(info,k)==getattr(after,k) for k in ('st_dev','st_ino','st_nlink','st_mode','st_size','st_mtime_ns','st_ctime_ns')), name
    return ALIAS_MEMBERS

S=D/'SELECTION16.json'
sel=json.loads(S.read_bytes());p=D/'failed-outcome-increment16.tar';assert not p.exists()
assert sel['original_alias_members']==authenticate_alias_pair(R)
assert {row['path'] for row in sel['rows'] if row['path'] in ALIAS_MEMBERS}==set(ALIAS_MEMBERS)
rows=sorted(sel['rows']+sel['directories'],key=lambda r:r['path'])
with tarfile.open(p,'x',format=tarfile.PAX_FORMAT) as t:
 for r in rows:
  q=R/r['path'];before=q.lstat();assert stat.S_IMODE(before.st_mode)==int(r['mode'],8)
  x=tarfile.TarInfo(r['path']);x.mode=int(r['mode'],8);x.uid=x.gid=x.mtime=0
  if r['type']=='directory':assert stat.S_ISDIR(before.st_mode);x.type=tarfile.DIRTYPE;t.addfile(x)
  elif r['type']=='symlink':
   assert stat.S_ISLNK(before.st_mode) and os.readlink(q)==r['linkname'];x.type=tarfile.SYMTYPE;x.linkname=r['linkname'];t.addfile(x)
  else:
   assert stat.S_ISREG(before.st_mode) and (before.st_nlink==1 or (r['path'] in ALIAS_MEMBERS and r.get('original_alias')==ALIAS_MEMBERS[r['path']] and alias_signature(before)==(66310,7865445,2,14,0o664,True)));raw=q.read_bytes();after=q.lstat();assert all(getattr(before,k)==getattr(after,k) for k in ('st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink'))
   assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'];x.size=len(raw);t.addfile(x,io.BytesIO(raw))
authenticate_alias_pair(R)
with tarfile.open(p,'r') as t:
 members=t.getmembers();assert len(members)==len(rows) and len({m.name for m in members})==len(rows)
 for m,r in zip(members,rows,strict=True):
  assert m.name==r['path'] and m.mode==int(r['mode'],8)
  if r['type']=='directory':assert m.isdir()
  elif r['type']=='symlink':assert m.issym() and m.linkname==r['linkname']
  else:assert m.isfile() and m.size==r['bytes'] and hashlib.sha256(t.extractfile(m).read()).hexdigest()==r['sha256']
raw=p.read_bytes();v={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection':{'path':str(S.relative_to(R)),'sha256':hashlib.sha256(S.read_bytes()).hexdigest()},'archive':{'path':str(p.relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},'files':sel['files'],'directories':len(sel['directories']),'regular_bytes':sel['body_bytes'],'actual_local_readback':True,'excluded_synthetic_git_subtrees':sel['excluded_synthetic_git_subtrees'],'original_alias_members':ALIAS_MEMBERS,'alias_qualification':'Two archived regular bodies with original alias metadata only; no hardlink/POSIX reconstruction or recovery/deletion claim for excluded synthetic .git internals','qualification':'Complete declared public full29 failed outcome and functional source increment including original names/types/modes and opaque regular bodies. Private runtime, unchanged historical stores and scientific inputs excluded. Local capture does not establish external recovery, POSIX reconstruction, installed runtime or deletion authority.'}
(D/'CAPTURE16.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps(v))
