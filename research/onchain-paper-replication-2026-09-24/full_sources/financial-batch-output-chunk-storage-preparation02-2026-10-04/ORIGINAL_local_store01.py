"""Tiny engineering local sink/readback; no offload or live storage capability.

Caller supplies an existing empty private directory, exclusively owned. Partial
files and original errors remain; a failed instance is poisoned and never retries.
64MiB includes all retained files, not a permission to occupy the live 1GiB watch.
"""
import os,re,shutil,stat,time
from pathlib import Path
import codec01 as C
import recovery04 as R
from owned_io import _cleanup
LIMIT=64*1024**2
FLOOR=10*1024**3

def name(n):C.require(type(n)is str and re.fullmatch(r'(start|terminal)\.json|page-[0-9]{4}\.json|chunk-[0-9]{5}\.bin',n),'codec member name');return n
class LocalStore:
 def __init__(self,root):
  self.root=Path(root);self.fd=None;self.poisoned=False;self.closed=False;self.names=set();self.total=0;self.begin=time.monotonic()
  try:
   C.require(self.root.is_absolute() and self.root.resolve()==self.root,'canonical root')
   self.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
   s=os.fstat(self.fd);self.identity=(s.st_dev,s.st_ino,s.st_mode)
   C.require(stat.S_IMODE(s.st_mode)==0o700 and not os.listdir(self.fd),'fresh empty private root');self.check()
  except BaseException:
   self.close();raise
 def check(self):
  C.require(not self.closed and not self.poisoned,'terminal sink')
  s=self.root.lstat();f=os.fstat(self.fd)
  C.require(self.root.resolve()==self.root and (s.st_dev,s.st_ino,s.st_mode)==self.identity==(f.st_dev,f.st_ino,f.st_mode),'root changed')
  C.require(time.monotonic()-self.begin<=C.SECONDS and shutil.disk_usage(self.root).free>=FLOOR,'time/disk floor')
  C.require(set(os.listdir(self.fd))==self.names and len(self.names)<=C.MAX_CHUNKS+258,'whole local membership differs')
  allocated=f.st_blocks*512;logical=0
  for n in self.names:
   v=os.stat(n,dir_fd=self.fd,follow_symlinks=False)
   C.require(stat.S_ISREG(v.st_mode) and v.st_nlink==1 and stat.S_IMODE(v.st_mode)==0o600 and v.st_size<=C.FILE,'whole local file type/mode/size')
   allocated+=v.st_blocks*512;logical+=v.st_size
  C.require(allocated<=LIMIT and logical==self.total<=LIMIT,'whole sampled allocated/logical bound')
 def put(self,n,b):
  fd=None
  try:
   self.check();name(n);C.require(type(b)is bytes and 0<len(b)<=C.FILE and n not in self.names and self.total+len(b)<=LIMIT,'fresh bounded file/whole local limit')
   self.names.add(n) # Reservation is not refunded after failure.
   fd=os.open(n,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=self.fd)
   at=0
   while at<len(b):
    k=os.write(fd,memoryview(b)[at:at+65536]);C.require(k>0,'write progress');at+=k
   os.fsync(fd);s=os.fstat(fd);C.require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==len(b) and R.sig(s)==R.sig(os.stat(n,dir_fd=self.fd,follow_symlinks=False)),'file changed')
   os.fsync(self.fd);self.total+=len(b);self.check();C.require(R.read(self.root,n)==b,'file readback')
  except BaseException:self.poisoned=True;raise
  finally:
   try:_cleanup(() if fd is None else (lambda:os.close(fd),))
   except BaseException:self.poisoned=True;raise
 def verify(self,terminal_pin,descriptor,provisional=lambda b:None):
  self.check();result=C.verify_stream(lambda n:R.read(self.root,name(n)),terminal_pin,descriptor,provisional)
  C.require(set(result['members'])==self.names,'complete local member denominator');self.check();return result
 def close(self):
  if not self.closed:
   self.closed=True
   if self.fd is not None:_cleanup((lambda:os.close(self.fd),))
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
