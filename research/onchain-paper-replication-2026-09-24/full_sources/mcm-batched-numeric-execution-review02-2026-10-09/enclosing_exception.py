"""Local cleanup-only failure under an unrelated enclosing handled exception."""
import ast,json,os,resource,signal,types,hashlib
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;C=H.parent/'mcm-batched-numeric-execution02-2026-10-09/numeric_execution.py';tree=ast.parse(C.read_text());tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and any(x.name=='batched_numeric_reuse' for x in n.names))];ns={};exec(compile(tree,str(C),'exec'),ns)
root=H/'enclosing-fixture';root.mkdir();fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY);child=os.open('body',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600,dir_fd=fd);os.write(child,b'valid');os.close(child)
outer=ValueError('unrelated already handled caller error');cleanup=OSError('actual close succeeded; synthetic cleanup-only failure')
def close(d):os.close(d);raise cleanup
proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.close=close;ns['os']=proxy
try:
 try:raise outer
 except ValueError:
  returned=ns['read_file'](fd,'body',10)
finally:os.close(fd)
assert returned[0]==b'valid' and 'numeric read cleanup' in outer.__notes__[0]
out={'cleanup_only_failure_silently_suppressed':True,'read_returned_success':True,'unrelated_outer_error_notes':outer.__notes__,'source_sha256':hashlib.sha256(C.read_bytes()).hexdigest(),'arrays_or_authority_objects':False}
(H/'ENCLOSING_RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
