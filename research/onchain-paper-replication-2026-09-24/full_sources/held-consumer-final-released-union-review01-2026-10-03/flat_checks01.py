"""Read-only independent flat output check; invoke only after actual receipt handoff."""
from pathlib import Path
import gzip,hashlib,io,json,os,stat,tarfile
H=lambda b:hashlib.sha256(b).hexdigest()
def read(path):
 path=Path(path);s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304 and path.resolve()==path
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 def sig(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 try:
  assert sig(s)==sig(os.fstat(fd));parts=[];n=0
  while True:
   b=os.read(fd,min(65536,s.st_size-n+1))
   if not b:break
   n+=len(b);assert n<=s.st_size;parts.append(b)
  assert n==s.st_size and sig(s)==sig(os.fstat(fd))==sig(path.lstat());return b''.join(parts)
 finally:os.close(fd)
def check(flat,bundle,request):
 flat=Path(flat);bundle=Path(bundle);assert flat.resolve()==flat and stat.S_IMODE(flat.lstat().st_mode)==0o700
 recovery=json.loads(read(flat/'recovery.json'));assert recovery['status']=='fresh-flat-archival-recovery-not-origin-proof'
 for k in ('instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority'):assert recovery[k] is False
 capture=read(bundle/'capture.json');assert recovery['capture_sha256']==H(capture);cap=json.loads(capture)
 names={'recovery.json'};results={}
 for role in ('capsule','external'):
  meta_name=role+'-metadata.json';names.add(meta_name);meta_raw=read(flat/meta_name);meta=json.loads(meta_raw);m=request[role+'_manifest'];assert meta['manifest']==m and meta['archive']==cap['archives'][role]
  result=recovery['results'][role];assert result['metadata_file']==meta_name and result['metadata_sha256']==H(meta_raw) and result['manifest_sha256']==request[role+'_manifest_sha256'];assert result['root_mode']==m['root_mode']
  mapping=meta['flat_members'];expected={r['path'] for r in m['members'] if r['kind']=='file'};assert set(mapping)==expected and len(set(mapping.values()))==len(mapping)
  out=io.BytesIO();gz=gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0);tar=tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT);logical=0;index=0
  for row in m['members']:
   t=tarfile.TarInfo(row['path']);t.mode=row['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
   if row['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
   else:
    leaf=mapping[row['path']];assert leaf==role+'-'+str(index).zfill(5)+'.body';index+=1;assert leaf not in names;names.add(leaf);b=read(flat/leaf);assert len(b)==row['bytes'] and H(b)==row['sha256'];logical+=len(b);t.size=len(b);tar.addfile(t,io.BytesIO(b))
  tar.close();gz.close();raw=read(bundle/(role+'.tar.gz'));assert raw==out.getvalue() and H(raw)==result['archive_sha256']==cap['archives'][role]['sha256'];assert len(raw)==cap['archives'][role]['bytes']
  assert result['members']==len(m['members']) and result['regular_bodies']==len(mapping)
  results[role]={'members':len(m['members']),'regular_bodies':len(mapping),'logical_bytes':logical,'canonical_compressed_sha256':H(raw),'manifest_sha256':result['manifest_sha256'],'root_mode_metadata':m['root_mode']}
 assert {p.name for p in flat.iterdir()}==names
 for p in flat.iterdir():assert stat.S_ISREG(p.lstat().st_mode) and stat.S_IMODE(p.lstat().st_mode)==0o600
 return {'flat_files':len(names),'roles':results,'qualifications':'Exact flat bytes plus logical names/types/modes; no original POSIX tree or Git reconstructed by reviewer.'}
