"""Bounded real child supervisor, exact raw logs, first-fatal cleanup."""
import os,selectors,signal,subprocess,time
from pathlib import Path
import recovery04 as R

def supervise(argv,cwd,env,directory,seconds,watch=lambda:None,on_spawn=lambda process:None):
 R.require(0<seconds<=1840,'outer finite deadline');directory=Path(directory);process=None;poll=None;fds=[];primary=None;result=None
 try:
  for name in ('stdout','stderr'):
   fd=os.open(directory/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);fds.append(fd)
  process=subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
  on_spawn(process)
  poll=selectors.DefaultSelector();counts=[0,0]
  for i,pipe in enumerate((process.stdout,process.stderr)):os.set_blocking(pipe.fileno(),False);poll.register(pipe,selectors.EVENT_READ,i)
  started=time.monotonic();deadline=started+seconds
  while poll.get_map():
   R.require(time.monotonic()<deadline,'outer active deadline');watch()
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
   if process is None:return
   # Created session owns this group; never signal any externally supplied PID.
   if process.poll() is None:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)
   else:process.wait(timeout=1)
  actions=[stop]
  if poll is not None:actions.append(poll.close)
  if process is not None:
   actions.extend([process.stdout.close,process.stderr.close])
  for fd in fds:actions.extend([lambda fd=fd:os.fsync(fd),lambda fd=fd:os.close(fd)])
  R._cleanup(tuple(actions),primary=primary)
 if primary is not None:raise primary
 return result
