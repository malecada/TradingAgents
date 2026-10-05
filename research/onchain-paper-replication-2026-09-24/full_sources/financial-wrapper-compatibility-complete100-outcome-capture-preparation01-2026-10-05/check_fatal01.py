from pathlib import Path
import sys,time,os,json
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import capture01 as C
path=D/'retained-fatal.body';original_write=os.write;original_close=os.close;primary=MemoryError('actual opaque primary');closed=[];fds=[]
def write(fd,raw):fds.append(fd);raise primary
def close(fd):
 original_close(fd);closed.append(fd)
 if fd in fds:raise OSError('after real file close')
os.write=write;os.close=close
try:
 try:C.write(path,b'opaque',time.monotonic())
 except BaseException as error:assert error is primary
 else:raise AssertionError('primary lost')
finally:os.write=original_write;os.close=original_close
assert fds and all(fd in closed for fd in fds)
for fd in fds:
 try:os.fstat(fd)
 except OSError:pass
 else:raise AssertionError('file descriptor leaked')
assert path.exists() and path.stat().st_size==0
(D/'FATAL_CHECK01.json').write_text(json.dumps({'same_primary':True,'actual_file_fd_closed':True,'partial_retained':True,'cleanup_error_retained_as_cause':primary.__cause__ is not None,'Root_execution':False},indent=2)+'\n');print('actual primary/secondary FD cleanup passed')
