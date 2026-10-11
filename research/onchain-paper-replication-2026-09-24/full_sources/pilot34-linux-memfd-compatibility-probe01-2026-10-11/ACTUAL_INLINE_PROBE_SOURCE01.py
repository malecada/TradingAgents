import ctypes,errno,fcntl,hashlib,json,os,sys,time
from pathlib import Path
D=Path('research/onchain-paper-replication-2026-09-24/full_sources/pilot34-linux-memfd-compatibility-probe01-2026-10-11')
assert not (D/'PROBE01.json').exists()
assert sys.platform=='linux';start=time.monotonic();fd=None;error=None;out={}
try:
 libc=ctypes.CDLL(None,use_errno=True);create=libc.memfd_create
 create.argtypes=[ctypes.c_char_p,ctypes.c_uint];create.restype=ctypes.c_int
 fd=create(b'bounded-compatibility-probe',3)
 if fd<0:
  code=ctypes.get_errno();raise OSError(code,os.strerror(code))
 body=b'one finite engineering kernel-seal proof\n';assert os.write(fd,body)==len(body)
 fcntl.fcntl(fd,1033,15);seals=fcntl.fcntl(fd,1034)
 assert seals==15 and os.pread(fd,len(body)+1,0)==body
 refused=[]
 for title,call in [('write',lambda:os.write(fd,b'x')),('grow',lambda:os.ftruncate(fd,len(body)+1)),('shrink',lambda:os.ftruncate(fd,0))]:
  try:call()
  except OSError as e:assert e.errno==errno.EPERM;refused.append(title)
  else:raise AssertionError(title+' not sealed')
 out={'status':'PASS_ACTUAL_LINUX_KERNEL_SEALS','libc_memfd_create_lookup':'CDLL(None)','flags':3,'F_ADD_SEALS':1033,'F_GET_SEALS':1034,'seal_mask':15,'actual_kernel_seals':seals,'refusals':refused,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'no_scientific_import':True}
except BaseException as e:
 error=e;out={'status':'FAILED','type':type(e).__name__,'message':str(e),'no_scientific_import':True}
finally:
 if fd is not None and fd>=0:os.close(fd)
 out['fd_closed']=fd is not None and fd>=0;out['elapsed_seconds']=time.monotonic()-start
 with (D/'PROBE01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
 print(json.dumps(out))
if error:raise error
