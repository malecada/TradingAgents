from pathlib import Path
import importlib.util,json,os,types,stat
O=Path(__file__).resolve().parent;sp=importlib.util.spec_from_file_location('cohort04',O/'restore01.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);results=[]
for kind in ['prerequisite-byte','prerequisite-mode','root-mode','iterator-late','membership']:
 d=O/('cohort-'+kind);d.mkdir(mode=0o700);sel=d/'selected';sel.mkdir(mode=0o700);early=sel/'earlier';late=sel/'later';early.write_bytes(b'first');late.write_bytes(b'last');early.chmod(0o600);late.chmod(0o600);receipt=d/'receipt.opaque';receipt.write_bytes(b'opaque prerequisite not a provenance receipt');receipt.chmod(0o600);c=M.VerifiedCohort();c.read(d,'receipt.opaque');c.tree(sel,{'earlier','later'});c.read(sel,'earlier');c.read(sel,'later');c.check();changed=[False]
 if kind=='iterator-late':
  real=M.os;proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)})
  class It:
   def __init__(self,p):self.it=os.scandir(p)
   def __iter__(self):return self
   def __next__(self):return next(self.it)
   def close(self):
    self.it.close()
    if not changed[0]:changed[0]=True;receipt.write_bytes(b'changed prerequisite')
  proxy.scandir=lambda p:It(p);M.os=proxy
 else:
  changed[0]=True
  if kind=='prerequisite-byte':receipt.write_bytes(b'changed')
  elif kind=='prerequisite-mode':receipt.chmod(0o644)
  elif kind=='root-mode':d.chmod(0o755)
  else:(sel/'foreign').write_bytes(b'extra')
 error=None
 try:c.check()
 except BaseException as e:error=e
 finally:
  if kind=='iterator-late':M.os=real
 assert changed[0] and isinstance(error,ValueError);results.append({'case':kind,'refused':True,'error_type':type(error).__name__,'opaque_only_no_remote_record':True})
# A same-file cleanup mutation is rejected before it could become a new baseline.
d=O/'same-read04';d.mkdir(mode=0o700);p=d/'opaque';p.write_bytes(b'initial');pin=(p.stat().st_dev,p.stat().st_ino);real=M.R.os;proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});fired=[False]
def close(fd):
 s=os.fstat(fd);os.close(fd)
 if not fired[0] and (s.st_dev,s.st_ino)==pin:fired[0]=True;p.write_bytes(b'changed-larger')
proxy.close=close;M.R.os=proxy
try:
 try:M.VerifiedCohort().read(d,'opaque')
 except ValueError:results.append({'case':'same_read_cleanup_newbaseline_refused','refused':True})
 else:raise AssertionError('same read corruption accepted')
finally:M.R.os=real
assert fired[0]
(O/'COHORT04.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS',len(results),'cross-prerequisite/iterator/private-root/currentness controls')
