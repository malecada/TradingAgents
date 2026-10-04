from pathlib import Path
import importlib.util,os,types,json,stat,hashlib
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-compatibility-composed-recovery-preparation01-2026-10-04';s=importlib.util.spec_from_file_location('source_checker',A/'verify01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M);rows=[];checks=[]
assert hashlib.sha256((A/'verify01.py').read_bytes()).hexdigest()=='14145d47b0df54c4234c4c029a1108ce8b3e7a9d4638f92b9475d99eb3f7c52f'
p=H/'opaque-body';p.write_bytes(b'opaque');p.chmod(0o600)
for secondary in [MemoryError('later close fatal'),SystemExit('later close fatal')]:
 primary=ValueError('original read ordinary');proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});fds=[];real=M.os
 def read(fd,n):fds.append((fd,os.fstat(fd).st_ino));raise primary
 def close(fd):os.close(fd);raise secondary
 proxy.read=read;proxy.close=close;M.os=proxy
 try:
  try:M.Reader().read(p)
  except BaseException as actual:
   assert actual is primary and actual.secondary_close_failure is secondary
   rows.append({'id':'CR1','primary':type(primary).__name__,'later_close':type(secondary).__name__,'escaped':type(actual).__name__,'first_actual_fatal_escaped':False,'secondary_object_retained_as_attribute':True})
  else:raise AssertionError('no failure')
 finally:M.os=real
 for fd,ino in fds:
  try:os.fstat(fd)
  except OSError:checks.append('real descriptor closed after '+type(secondary).__name__)
  else:raise AssertionError('descriptor still open')
# A real scandir is explicitly closed, then its close callback raises during an active fatal.
for ptype,stype in [(KeyboardInterrupt,SystemExit),(MemoryError,ValueError)]:
 primary=ptype('original iteration fatal');secondary=stype('later iterator close');state=[];real=M.os;proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)})
 class Iterator:
  def __init__(self,path):self.it=os.scandir(path)
  def __enter__(self):return self
  def __iter__(self):return self
  def __next__(self):next(self.it);raise primary
  def __exit__(self,*args):self.it.close();state.append('actual iterator closed');raise secondary
 proxy.scandir=Iterator;M.os=proxy
 try:
  try:M.Reader().tree(H)
  except BaseException as actual:
   assert actual is secondary and state==['actual iterator closed']
   rows.append({'id':'CR2','primary':ptype.__name__,'later_close':stype.__name__,'escaped':type(actual).__name__,'original_fatal_identity_preserved':False,'original_in_context':actual.__context__ is primary,'real_iterator_closed':True})
  else:raise AssertionError('no failure')
 finally:M.os=real
r={'decision':'WITHHELD_CR1_CR2','source_sha256':hashlib.sha256((A/'verify01.py').read_bytes()).hexdigest(),'actual_source_invoked':['Reader.read','Reader.tree'],'no_run_entry_or_proof':True,'checks':checks,'witnesses':rows}
(H/'WITNESS01.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r))
