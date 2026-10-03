"""Bounded byte-only baseline capture/restore. No network or research authority."""
import argparse,gzip,hashlib,io,json,os,stat,tarfile,time,shutil
from contextlib import contextmanager
from pathlib import Path,PurePosixPath
from owned_io import _cleanup
from bounded_git01 import git
FILE=4*1024**2;BASE=128*1024**2;TOTAL=1024**3;FLOOR=10*1024**3
SOURCE='d443208795f59292c156c5b81b687594efacea4d'
CAP='/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source'
def require(v,msg):
 if not v:raise ValueError(msg)
def digest(b):return hashlib.sha256(b).hexdigest()
def encode(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def path_name(n):
 require(type(n) is str and n and n!='.' and str(PurePosixPath(n))==n and not n.startswith('/') and '\\' not in n and '\0' not in n and '..' not in n.split('/') and len(n.encode())<=2048 and len(n.split('/'))<=32,'unsafe member path')
 require(not any(x.lower() in ('keys','apis','.env','.ssh','hf_token.txt') or x.lower().endswith(('.pem','.key')) for x in n.split('/')),'protected path refused before IO');return n
def sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(root,name,limit=FILE):
 root=Path(root);path_name(str(root).lstrip('/'));path_name(name);fds=[];parents=[]
 try:
  require(root.is_absolute() and root.resolve()==root,'root redirected');p=root;fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);fds.append(fd);parents.append((p,fd,sig(os.fstat(fd))))
  for part in name.split('/')[:-1]:
   fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);fds.append(fd);p=p/part;parents.append((p,fd,sig(os.fstat(fd))))
  leaf=name.split('/')[-1];before=os.stat(leaf,dir_fd=fd,follow_symlinks=False);pin=sig(before)
  require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit,'file type/link/extent')
  child=os.open(leaf,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd);fds.append(child);require(sig(os.fstat(child))==pin,'file replaced before open');chunks=[];count=0
  while True:
   block=os.read(child,min(65536,before.st_size-count+1))
   if not block:break
   count+=len(block);require(count<=before.st_size,'file grew');chunks.append(block)
  require(count==before.st_size and sig(os.fstat(child))==pin==sig(os.stat(leaf,dir_fd=fd,follow_symlinks=False))==sig((root/name).lstat()) and (root/name).resolve()==root/name,'file changed')
  for p,f,pin in parents:require(p.resolve()==p and sig(p.lstat())==pin==sig(os.fstat(f)),'parent changed')
  return b''.join(chunks)
 finally:_cleanup(tuple(lambda f=f:os.close(f) for f in reversed(fds)))
def scan(root):
 root=Path(root);path_name(str(root).lstrip('/'));require(root.is_absolute() and root.resolve()==root,'canonical scan root');rows=[];logical=allocated=0;deadline=time.monotonic()+120
 def visit(p,relative):
  nonlocal logical,allocated
  require(time.monotonic()<deadline and len(rows)<32768,'finite scan bound');fd=None;it=None
  try:
   fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);pin=sig(os.fstat(fd));allocated+=os.fstat(fd).st_blocks*512;it=os.scandir(fd);names=[]
   for e in it:
    require(len(names)+len(rows)<32768,'entry count');names.append(e.name)
   for name in sorted(names):
    rel=name if not relative else relative+'/'+name;path_name(rel);q=root/rel;s=q.lstat();require(q.resolve()==q and s.st_dev==root.stat().st_dev,'redirect/device');row={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
    if stat.S_ISDIR(s.st_mode):row['kind']='directory';rows.append(row);visit(q,rel)
    else:
     raw=read(root,rel);require(sig(q.lstat())==sig(s),'file changed during inventory');logical+=len(raw);allocated+=s.st_blocks*512;row.update(kind='file',bytes=len(raw),sha256=digest(raw));rows.append(row)
    require(logical<=BASE and allocated<=BASE,'128MiB initial baseline bound')
   require(sig(p.lstat())==pin==sig(os.fstat(fd)) and p.resolve()==p,'directory changed during scan')
  finally:_cleanup((() if it is None else (it.close,))+(() if fd is None else (lambda:os.close(fd),)))
 visit(root,'');return {'schema_version':1,'root_mode':stat.S_IMODE(root.lstat().st_mode),'members':sorted(rows,key=lambda r:r['path'])}
def validate(m):
 require(type(m) is dict and set(m)=={'schema_version','root_mode','members'} and type(m['schema_version']) is int and m['schema_version']==1,'manifest schema');require(type(m['root_mode']) is int and 0<=m['root_mode']<=0o7777,'root mode');require(type(m['members']) is list and len(m['members'])<=32768,'membership count');seen=set();total=0
 for r in m['members']:
  require(type(r) is dict and r.get('kind') in ('file','directory'),'typed member');fields={'path','kind','mode'}|({'bytes','sha256'} if r['kind']=='file' else set());require(set(r)==fields,'typed fields');name=path_name(r['path']);require(name not in seen,'duplicate member');parent=str(PurePosixPath(name).parent);require(parent=='.' or any(x['path']==parent and x['kind']=='directory' for x in m['members']),'missing parent');seen.add(name);require(type(r['mode']) is int and 0<=r['mode']<=0o7777,'mode')
  if r['kind']=='file':require(type(r['bytes']) is int and 0<=r['bytes']<=FILE and type(r['sha256']) is str and len(r['sha256'])==64 and all(c in '0123456789abcdef' for c in r['sha256']),'file extent/hash');total+=r['bytes']
 require(total<=BASE and [r['path'] for r in m['members']]==sorted(seen),'total/order')
def same(root,m):validate(m);require(scan(root)==m,'whole tree differs')
class Sink:
 def __init__(self,fd=None):self.fd=fd;self.count=0;self.hash=hashlib.sha256()
 def write(self,b):
  require(self.count+len(b)<=FILE,'archive exceeds4MiB; retain failed attempt');self.count+=len(b);self.hash.update(b)
  if self.fd is not None:
   offset=0
   while offset<len(b):n=os.write(self.fd,b[offset:]);require(n>0,'short write');offset+=n
  return len(b)
 def flush(self):pass
 def tell(self):return self.count
def tar_stream(root,m,sink):
 gz=None;tar=None
 try:
  gz=gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0);tar=tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT)
  for r in m['members']:
   t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
   if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
   else:
    b=read(root,r['path']);require(len(b)==r['bytes'] and digest(b)==r['sha256'],'archive source body differs');t.size=len(b);tar.addfile(t,io.BytesIO(b))
 finally:_cleanup((() if tar is None else (tar.close,))+(() if gz is None else (gz.close,)))
@contextmanager
def new_file(path):
 path=Path(path);path_name(str(path).lstrip('/'));parent=None;fd=None
 try:
  require(path.parent.is_absolute() and path.parent.resolve()==path.parent,'output parent redirected');parent=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);pin=os.fstat(parent);require((pin.st_dev,pin.st_ino)==(path.parent.stat().st_dev,path.parent.stat().st_ino),'output parent changed')
  fd=os.open(path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
  yield fd
  actual=os.fstat(fd);require(sig(actual)==sig(os.stat(path.name,dir_fd=parent,follow_symlinks=False))==sig(path.lstat()) and actual.st_nlink==1 and path.resolve()==path,'output file changed');current=path.parent.lstat();require((current.st_dev,current.st_ino,current.st_mode)==(pin.st_dev,pin.st_ino,pin.st_mode) and path.parent.resolve()==path.parent,'output parent changed');os.fsync(parent)
 finally:_cleanup((() if fd is None else (lambda:os.close(fd),))+(() if parent is None else (lambda:os.close(parent),)))
def pack(root,m,destination):
 root=Path(root);destination=Path(destination);same(root,m);require(destination.parent.resolve()==destination.parent and not destination.is_relative_to(root),'archive output must be outside baseline');sink=None
 with new_file(destination) as fd:
  sink=Sink(fd);tar_stream(root,m,sink);os.fsync(fd);same(root,m)
 return {'bytes':sink.count,'sha256':sink.hash.hexdigest(),'manifest_sha256':digest(encode(m))}
def restore(archive,info,m,dest):
 archive=Path(archive);dest=Path(dest);validate(m);raw=read(archive.parent,archive.name);require(set(info)=={'bytes','sha256','manifest_sha256'} and len(raw)==info['bytes'] and digest(raw)==info['sha256'] and digest(encode(m))==info['manifest_sha256'],'archive binding differs');require(dest.parent.resolve()==dest.parent and not os.path.lexists(dest),'fresh destination required');dest.mkdir(mode=0o700);expected={r['path']:r for r in m['members']};seen=set();tar=None
 try:
  tar=tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz')
  for t in tar:
   name=path_name(t.name);require(name in expected and name not in seen,'extra/repeated tar member');r=expected[name];require(t.mode==r['mode'] and not t.issym() and not t.islnk(),'archive mode/link');q=dest/name;require(q.parent.resolve()==q.parent and q.parent.is_dir(),'restore parent missing/redirected')
   if r['kind']=='directory':require(t.isdir() and t.size==0,'directory extent/type');q.mkdir(mode=0o700)
   else:
    require(t.isfile() and t.size==r['bytes']<=FILE,'file extent/type');stream=None
    try:
     stream=tar.extractfile(t);require(stream is not None,'missing body');b=stream.read(FILE+1);require(len(b)==r['bytes'] and digest(b)==r['sha256'],'archive body mismatch')
     with new_file(q) as fd:
      offset=0
      while offset<len(b):n=os.write(fd,b[offset:]);require(n>0,'restore short write');offset+=n
      os.fchmod(fd,r['mode']);os.fsync(fd)
    finally:_cleanup(() if stream is None else (stream.close,))
   seen.add(name)
 finally:_cleanup(() if tar is None else (tar.close,))
 require(seen==set(expected),'missing tar member')
 for r in reversed(m['members']):
  if r['kind']=='directory':os.chmod(dest/r['path'],r['mode'])
 os.chmod(dest,m['root_mode']);same(dest,m);sink=Sink();tar_stream(dest,m,sink);require(sink.count==len(raw) and sink.hash.hexdigest()==digest(raw),'noncanonical/trailing archive framing');return {'status':'byte-restored-no-authority','archive_sha256':digest(raw),'members':len(seen),'root_mode':m['root_mode']}
def put(path,value):
 raw=encode(value);require(len(raw)<=FILE,'receipt extent')
 with new_file(path) as fd:
  offset=0
  while offset<len(raw):n=os.write(fd,raw[offset:]);require(n>0,'receipt short write');offset+=n
  os.fsync(fd)
def request(value):
 require(set(value)=={'schema_version','capsule_root','source','external_root','external_members','capsule_manifest','capsule_manifest_sha256','external_manifest','external_manifest_sha256','output_root','registration','registration_sha256'},'request fields');require(type(value['schema_version']) is int and value['schema_version']==1 and value['capsule_root']==CAP and value['source']==SOURCE,'fixed source/root');require(type(value['external_members']) is dict and value['external_members'],'explicit external members required')
 for role in ('capsule','external'):
  validate(value[role+'_manifest']);require(digest(encode(value[role+'_manifest']))==value[role+'_manifest_sha256'],'manifest pin')
 m=value['external_manifest'];require({r['path']:r['sha256'] for r in m['members'] if r['kind']=='file'}==value['external_members'],'external full file membership differs')
 require(sum(r.get('bytes',0) for role in ('capsule','external') for r in value[role+'_manifest']['members'])<=BASE,'combined initial logical baseline exceeds128MiB')
 roots=[Path(value[k]) for k in ('capsule_root','external_root','output_root')];require(all(p.is_absolute() and p.resolve()==p for p in roots),'canonical roots');require(all(not a.is_relative_to(b) for i,a in enumerate(roots) for j,b in enumerate(roots) if i!=j),'separate nonrecursive scopes');return roots
def authenticate_source(cap,q):
 require(not os.path.lexists(cap/'.git/objects/info/alternates') and not os.path.lexists(cap/'.git/info/grafts') and not os.path.lexists(cap/'.git/refs/replace'),'foreign Git ancestry')
 require(git(cap,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'current source HEAD differs')
 raw=read(cap,path_name(q['registration']));require(digest(raw)==q['registration_sha256'],'registration changed');reg=json.loads(raw);exp=reg['experiments']['original-import-held-success-20261003-01'];refs=dict(exp['source_files']);require(len(refs)==204 and len(exp['inputs'])==33,'LOCAL6 source/input cardinality');refs[q['registration']]=q['registration_sha256']
 names=sorted(refs);require(all('\n' not in n and '\r' not in n for n in names),'batch path framing');bodies={n:read(cap,path_name(n)) for n in names};require(all(digest(bodies[n])==refs[n] for n in names),'source body hash differs')
 result=git(cap,['cat-file','--batch'],''.join(SOURCE+':'+n+'\n' for n in names).encode());offset=0
 for n in names:
  end=result.index(b'\n',offset);head=result[offset:end].split();require(len(head)==3 and head[1]==b'blob' and head[2].isdigit(),'source blob missing/type');size=int(head[2]);start=end+1;require(size<=FILE and result[start:start+size]==bodies[n] and result[start+size:start+size+1]==b'\n','committed source differs');offset=start+size+1
 require(offset==len(result),'trailing Git framing')
 for ref in exp['inputs'].values():require(digest(read(cap,path_name(ref['path'])))==ref['sha256'],'registered input changed')
 tracked=git(cap,['ls-tree','-r','--name-only','-z',SOURCE],cap=1024**2).split(b'\0');require(tracked[-1]==b'' and len(tracked)-1==246,'tracked246 count differs')
 require(sum(not (r['path']=='.git' or r['path'].startswith('.git/')) and r['kind']=='file' for r in q['capsule_manifest']['members'])==288,'whole nonGit288 files differs')
 return {'source':SOURCE,'committed_source_registration_bodies':205,'registered_inputs':33,'tracked_files':246,'nonGit_files':288}

def capture(q):
 cap,external,out=request(q);require(not os.path.lexists(out),'capture identity already reserved');require(shutil.disk_usage(out.parent).free>=FLOOR,'10GiB disk floor');same(cap,q['capsule_manifest']);same(external,q['external_manifest']);authenticate_source(cap,q);require(sum(root.lstat().st_blocks*512+sum((root/r['path']).lstat().st_blocks*512 for r in q[role+'_manifest']['members']) for role,root in [('capsule',cap),('external',external)])<=BASE,'combined allocated initial baseline exceeds128MiB');out.mkdir(mode=0o700)
 records={}
 for role,root in [('capsule',cap),('external',external)]:
  records[role]=pack(root,q[role+'_manifest'],out/(role+'.tar.gz'));put(out/(role+'-manifest.json'),q[role+'_manifest'])
  require(shutil.disk_usage(out).free>=FLOOR,'capture floor')
 same(cap,q['capsule_manifest']);same(external,q['external_manifest']);put(out/'capture.json',{'schema_version':1,'request_sha256':digest(encode(q)),'source':SOURCE,'archives':records,'scope':'complete supplied byte baselines; no external recovery or admission'});return records

def recover(bundle,capture_sha256,request_value,request_sha256,destination):
 """Fresh LOCAL byte verification after Root independently fetches a bundle.
 Origin branch/commit/fetch receipts remain separately required for external proof.
 """
 bundle=Path(bundle);destination=Path(destination);request(request_value)
 require(digest(encode(request_value))==request_sha256,'request expected hash differs')
 raw=read(bundle,'capture.json');require(digest(raw)==capture_sha256,'capture expected hash differs');receipt=json.loads(raw)
 require(receipt['schema_version']==1 and receipt['source']==SOURCE and receipt['request_sha256']==request_sha256 and set(receipt['archives'])=={'capsule','external'},'capture request/source join')
 require(destination.parent.resolve()==destination.parent and not os.path.lexists(destination),'fresh restore bundle required');require(shutil.disk_usage(destination.parent).free>=FLOOR,'recovery10GiBfloor');destination.mkdir(mode=0o700);results={}
 for role in ('capsule','external'):
  manifest_raw=read(bundle,role+'-manifest.json');require(digest(manifest_raw)==request_value[role+'_manifest_sha256'] and json.loads(manifest_raw)==request_value[role+'_manifest'],'recovered manifest hash differs')
  results[role]=restore(bundle/(role+'.tar.gz'),receipt['archives'][role],request_value[role+'_manifest'],destination/role)
  require(shutil.disk_usage(destination).free>=FLOOR,'recovery disk floor')
 results['source']=authenticate_source(destination/'capsule',request_value)
 put(destination/'recovery.json',{'schema_version':1,'status':'fresh-local-byte-recovery-not-origin-proof','capture_sha256':capture_sha256,'request_sha256':request_sha256,'results':results,'runtime_package_bodies_recovered':False,'research_authority':False});return results

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--request',type=Path,required=True);parser.add_argument('--request-sha256',required=True);parser.add_argument('--mode',choices=('capture','recover'),required=True);parser.add_argument('--bundle',type=Path);parser.add_argument('--capture-sha256');parser.add_argument('--destination',type=Path);args=parser.parse_args();raw=read(args.request.parent.resolve(),args.request.name);require(digest(raw)==args.request_sha256,'explicit request bytes differ');q=json.loads(raw);require(encode(q)==raw,'canonical request required')
 if args.mode=='capture':capture(q)
 else:
  require(args.bundle is not None and args.capture_sha256 is not None and args.destination is not None,'explicit recovered bundle/hash/destination required');recover(args.bundle,args.capture_sha256,q,args.request_sha256,args.destination)
