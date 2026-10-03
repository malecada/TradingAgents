"""Finite immutable byte snapshots; no numeric decoding or remote transfer."""
import hashlib,json,os,stat,time
from pathlib import Path
import owned_io as io
MAX=4194304;GIB=1024**3
require=io._require

def direct(p):
 p=Path(p);require(p.is_absolute() and p.resolve()==p,'absolute direct root required')
 for x in (p,*p.parents):require(not x.is_symlink(),'redirected ancestry')
 return p

def relative(s):
 require(type(s)is str and s and len(s)<=2048,'bounded path required');p=Path(s)
 require(not p.is_absolute() and str(p)==s and s!='.' and '..' not in p.parts,'unsafe member path')
 require(not any(x in {'keys','apis','.env','hf_token.txt'} or x.startswith('.env.') for x in p.parts),'secret path forbidden');return p

def sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def fsync_dir(p):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:io._release(lambda:os.close(fd))

def census(root,limit,deadline):
 root=direct(root);base=root.stat();require(stat.S_ISDIR(base.st_mode),'directory root required');rows=[];total=base.st_size;allocated=base.st_blocks*512
 for p in root.rglob('*'):
  require(time.monotonic()<deadline and len(rows)<32768,'tree count/time bound');name=str(p.relative_to(root));relative(name);require(len(Path(name).parts)<=32,'tree depth bound');s=p.lstat();require(p.resolve()==p and s.st_dev==base.st_dev,'tree redirected/cross-device member')
  row={'path':name,'mode':stat.S_IMODE(s.st_mode),'signature':sig(s)}
  if stat.S_ISDIR(s.st_mode):row['kind']='directory';total+=s.st_size;allocated+=s.st_blocks*512
  else:
   require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=MAX,'single-link regular bounded member required');row.update(kind='file',bytes=s.st_size);total+=s.st_size;allocated+=s.st_blocks*512
  require(total<=limit and allocated<=limit,'tree extent exceeds bound')
  rows.append(row)
 require(sig(root.stat())==sig(base),'root identity changed during census');rows.sort(key=lambda x:x['path']);return rows

def copy_file(source,target,expected,deadline):
 before=source.lstat();require(sig(before)==tuple(expected['signature']),'source changed before open');fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK);dest=None
 try:
  require(sig(os.fstat(fd))==sig(before),'source open identity differs');dest=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,expected['mode']);h=hashlib.sha256();total=0
  while True:
   require(time.monotonic()<deadline,'copy deadline');data=os.read(fd,65536)
   if not data:break
   total+=len(data);require(total<=MAX and total<=expected['bytes'],'source expanded');h.update(data);off=0
   while off<len(data):
    n=os.write(dest,data[off:]);require(n>0,'copy short write');off+=n
  require(total==expected['bytes'] and sig(os.fstat(fd))==sig(source.lstat())==sig(before),'source changed during copy');os.fchmod(dest,expected['mode']);os.fsync(dest)
  return h.hexdigest()
 finally:io._cleanup((lambda:os.close(fd),)+( () if dest is None else (lambda:os.close(dest),)))

def hash_file(path,expected,deadline):
 s=path.lstat();fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==expected['bytes'] and stat.S_IMODE(s.st_mode)==expected['mode'] and sig(os.fstat(fd))==sig(s),'recovered file identity/type/extent differs');h=hashlib.sha256();total=0
  while True:
   require(time.monotonic()<deadline,'hash deadline');b=os.read(fd,65536)
   if not b:break
   total+=len(b);require(total<=MAX and total<=expected['bytes'],'hash extent');h.update(b)
  require(total==expected['bytes'] and sig(s)==sig(os.fstat(fd))==sig(path.lstat()),'file changed during hash');return h.hexdigest()
 finally:io._release(lambda:os.close(fd))

def snapshot(source,destination,*,limit=GIB,seconds=120):
 source=direct(source);destination=direct(destination);require(not destination.is_relative_to(source) and not source.is_relative_to(destination),'independent snapshot root required');deadline=time.monotonic()+seconds;root_pin=sig(source.stat());before=census(source,limit,deadline);destination.mkdir(exist_ok=False);fsync_dir(destination.parent);result=[]
 for row in before:
  name=row['path'];p=destination/name
  if row['kind']=='directory':p.mkdir(mode=0o700)
  else:row=dict(row,sha256=copy_file(source/name,p,row,deadline))
  result.append({k:v for k,v in row.items() if k!='signature'})
 require(before==census(source,limit,deadline) and sig(source.stat())==root_pin,'source membership/signature changed during snapshot')
 for row in reversed(before):
  if row['kind']=='directory':os.chmod(destination/row['path'],row['mode']);fsync_dir(destination/row['path'])
 os.chmod(destination,stat.S_IMODE(source.stat().st_mode));fsync_dir(destination);return result

def verify_tree(root,rows,*,limit=GIB,seconds=120):
 root=direct(root);deadline=time.monotonic()+seconds;actual=census(root,limit,deadline)
 require([r['path'] for r in rows]==sorted(set(r['path'] for r in rows)),'sorted complete retained members required');require([r['path'] for r in actual]==[r['path'] for r in rows],'recovered membership differs')
 for got,want in zip(actual,rows):
  require(got['kind']==want['kind'] and got['mode']==want['mode'],'recovered type/mode differs')
  if want['kind']=='file':require(hash_file(root/want['path'],want,deadline)==want['sha256'],'recovered byte hash differs')
 require(actual==census(root,limit,deadline),'recovered tree changed');return {'members':len(rows),'logical_bytes':sum(r.get('bytes',0) for r in rows),'full_membership':True,'numerical_decoding':False}

def read(path,limit=MAX):
 path=direct(path)
 with io._opened(path,'rb') as f:
  s=os.fstat(f.fileno());require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=limit,'bounded metadata required');data=f.read(limit+1);require(len(data)<=limit and sig(s)==sig(os.fstat(f.fileno()))==sig(path.lstat()),'metadata changed');return data

def write(directory,name,value):
 data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();require(len(data)<=MAX,'metadata ceiling')
 with io._opened(directory/relative(name),'xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 fsync_dir(directory)
 return {'path':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}

def pages(directory,rows):
 directory.mkdir(exist_ok=False);refs=[];group=[]
 for row in rows:
  if len(json.dumps(group+[row],sort_keys=True).encode())>7800:
   require(group,'single metadata member exceeds compact page');refs.append(write(directory,f'page-{len(refs):05d}.json',group));group=[]
  group.append(row)
 if group:refs.append(write(directory,f'page-{len(refs):05d}.json',group))
 return refs
