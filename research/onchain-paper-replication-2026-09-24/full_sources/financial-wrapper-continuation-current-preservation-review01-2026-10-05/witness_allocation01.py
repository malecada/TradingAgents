"""Genuine owned FD allocation boundary, no live source entry."""
from pathlib import Path
import os,sys,json,importlib.util,hashlib
H=Path(__file__).resolve().parent;P=H.parent/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05';sys.path.insert(0,str(P));spec=importlib.util.spec_from_file_location('candidate',P/'bind02.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
root=H/'allocation-owned';root.mkdir(mode=0o700);(root/'body').write_bytes(b'opaque');op=os.open;cl=os.close;digest=hashlib.sha256;fds=[];closed=[];primary=MemoryError('digest allocation after successful actual child open')
def opening(path,*a,**kw):
 fd=op(path,*a,**kw)
 if path=='body':fds.append(fd)
 return fd
def closing(fd):closed.append(fd);return cl(fd)
def allocation(*a,**kw):
 if fds:raise primary
 return digest(*a,**kw)
os.open=opening;os.close=closing;hashlib.sha256=allocation
try:
 try:B.Census().tree(root,{'body':'file'},set());raise AssertionError('unexpected success')
 except BaseException as e:
  assert e is primary
  leaked=[]
  for fd in fds:
   try:os.fstat(fd);leaked.append(fd)
   except OSError:pass
finally:os.open=op;os.close=cl;hashlib.sha256=digest
for fd in leaked:cl(fd)
result={'candidate_sha256':digest((P/'bind02.py').read_bytes()).hexdigest(),'actual_original_fatal_preserved':True,'actual_child_fds':fds,'candidate_closed_fds':closed,'actual_child_fds_still_open_after_candidate_return':leaked,'reviewer_cleanup_closed_after_observation':leaked};assert len(leaked)==1
(H/'WITNESS_ALLOCATION01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result))
