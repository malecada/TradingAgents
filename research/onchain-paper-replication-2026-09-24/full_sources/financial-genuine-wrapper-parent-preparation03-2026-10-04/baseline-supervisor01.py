"""Bounded real child supervisor, exact raw logs, first-fatal cleanup."""
import os,stat,selectors,signal,subprocess,time
from pathlib import Path
import recovery04 as R
from descendants01 import OwnedTree

def supervise(argv,cwd,env,directory,seconds,watch=lambda:None,on_spawn=lambda process:None):
 R.require(0<seconds<=1840,'outer finite deadline');directory=Path(directory);process=None;poll=None;fds=[];primary=None;result=None;tree=OwnedTree();cleanup_result=None;directory_fd=None;directory_pin=None;log_pins=[]
 try:
  tree.begin()
  R.require(directory.is_absolute() and directory.resolve()==directory,'canonical supervisor namespace')
  directory_fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  ds=os.fstat(directory_fd);directory_pin=(ds.st_dev,ds.st_ino,ds.st_mode,ds.st_uid)
  def joined():
   ds=os.fstat(directory_fd);actual=directory.lstat()
   R.require(directory.resolve()==directory and directory_pin==(ds.st_dev,ds.st_ino,ds.st_mode,ds.st_uid)==(actual.st_dev,actual.st_ino,actual.st_mode,actual.st_uid),'supervisor directory replaced')
   for fd,name,original in log_pins:
    fs=os.fstat(fd);visible=os.stat(name,dir_fd=directory_fd,follow_symlinks=False)
    R.require((fs.st_dev,fs.st_ino,fs.st_mode)==original and fs.st_nlink==1 and R.sig(fs)==R.sig(visible),'supervisor log replaced')
  joined()
  for name in ('stdout','stderr'):
   fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory_fd);fds.append(fd);fs=os.fstat(fd);log_pins.append((fd,name,(fs.st_dev,fs.st_ino,fs.st_mode)));joined()
  process=subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  tree.scan();on_spawn(process)
  poll=selectors.DefaultSelector();counts=[0,0]
  for i,pipe in enumerate((process.stdout,process.stderr)):os.set_blocking(pipe.fileno(),False);poll.register(pipe,selectors.EVENT_READ,i)
  started=time.monotonic();deadline=started+seconds
  while poll.get_map():
   R.require(time.monotonic()<deadline,'outer active deadline');joined();watch();tree.scan()
   if process.poll() is not None:cleanup_result=tree.drain(process)
   for key,_ in poll.select(.1):
    b=os.read(key.fileobj.fileno(),65536)
    if not b:poll.unregister(key.fileobj);continue
    i=key.data;counts[i]+=len(b);R.require(counts[i]<=R.FILE,'outer raw stream exceeds4MiB')
    off=0
    while off<len(b):n=os.write(fds[i],b[off:]);R.require(n>0,'short log write');off+=n
  code=process.wait(timeout=max(.01,deadline-time.monotonic()));result={'pid':process.pid,'exit_code':code,'elapsed_seconds':time.monotonic()-started,'stdout_bytes':counts[0],'stderr_bytes':counts[1]}
 except BaseException as error:primary=error
 finally:
  def stop():
   nonlocal cleanup_result
   if tree.previous is not None:cleanup_result=tree.drain(process)
  def receipt():
   if cleanup_result is None or directory_fd is None:return
   joined();raw=R.encode(cleanup_result);R.require(len(raw)<=R.FILE,'cleanup record extent');record_fd=None
   try:
    record_fd=os.open('owned-tree-cleanup.json',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory_fd)
    offset=0
    while offset<len(raw):n=os.write(record_fd,raw[offset:]);R.require(n>0,'cleanup record short write');offset+=n
    os.fsync(record_fd);os.lseek(record_fd,0,os.SEEK_SET);R.require(os.read(record_fd,len(raw)+1)==raw,'cleanup record readback');joined();os.fsync(directory_fd)
   finally:R._cleanup(() if record_fd is None else (lambda:os.close(record_fd),))
  actions=[stop,receipt,tree.close]
  if directory_fd is not None:actions.append(joined)
  if poll is not None:actions.append(poll.close)
  if process is not None:
   actions.extend([process.stdout.close,process.stderr.close])
  for fd in fds:actions.extend([lambda fd=fd:os.fsync(fd),lambda fd=fd:os.close(fd)])
  if directory_fd is not None:actions.extend((lambda:os.fsync(directory_fd),lambda:os.close(directory_fd)))
  R._cleanup(tuple(actions),primary=primary)
 if primary is not None:raise primary
 return result
