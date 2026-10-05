"""One real owned FD allocation regression, original RED and corrected GREEN."""
import hashlib,importlib.util,json,os,sys
from pathlib import Path
H=Path(__file__).resolve().parent;O=H.parent/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05'
sys.path.insert(0,str(H))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
original=load('original',O/'bind02.py');corrected=load('corrected',H/'bind03.py')
results=[]
for label,module in [('original',original),('corrected',corrected)]:
 root=H/(label+'-owned');root.mkdir(mode=0o700);(root/'body').write_bytes(b'opaque allocation witness')
 op,cl,digest=os.open,os.close,hashlib.sha256;opened=[];closed=[];child=[];primary=MemoryError('real digest allocation failure')
 def opening(path,*a,**kw):
  fd=op(path,*a,**kw);opened.append(fd)
  if path=='body':child.append(fd)
  return fd
 def closing(fd):closed.append(fd);return cl(fd)
 def allocation(*a,**kw):raise primary
 os.open,os.close,hashlib.sha256=opening,closing,allocation
 try:
  try:module.Census().tree(root,{'body':'file'},set())
  except BaseException as error:assert error is primary
  else:raise AssertionError('allocation failure not propagated')
  leaked=[]
  for fd in opened:
   try:os.fstat(fd);leaked.append(fd)
   except OSError:pass
 finally:os.open,os.close,hashlib.sha256=op,cl,digest
 for fd in leaked:cl(fd)
 assert (len(leaked)==1 and leaked==child) if label=='original' else (leaked==[] and child==[])
 results.append({'source':label,'source_sha256':digest(Path(module.__file__).read_bytes()).hexdigest(),'same_primary':True,'opened_fds':opened,'child_fds':child,'closed_fds':closed,'still_open_after_return':leaked,'harness_closed_after_observation':leaked})
 # Ordinary real read verifies allocation movement retains successful bytes.
 c=corrected.Census();tree=c.tree(root,{'body':'file'},{'body'});c.finish();assert c.saved[(str(root),'body')]==b'opaque allocation witness'
print(json.dumps({'regression_pairs':1,'ordinary_read_controls':2,'results':results},sort_keys=True))
