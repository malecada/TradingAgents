"""Actual batch body with explicit stub OS/process/selector; no subprocess run."""
import ast,hashlib,os,subprocess,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).parent
OWNED=HERE.parent/'original-import-fixture-io-candidate04-2026-10-02/owned_io.py'
ns={};exec(compile(ast.parse(OWNED.read_bytes()),str(OWNED),'exec'),ns)
def require(ok,msg):
 if not ok:raise ValueError(msg)
class Tests(unittest.TestCase):
 def run_case(self,mode='ok'):
  calls=[];fatal=MemoryError('first fatal');wire=b'a'*40+b' blob 1\nx\n';chunks={12:[wire,b''],13:[b'']};clock=[0];proc=types.SimpleNamespace(returncode=None)
  if mode=='oversize':chunks[12]=[b'x'*(4*1024**2+128*26+1)]
  if mode=='stderr':chunks[13]=[b'x'*65537]
  class Stream:
   def __init__(self,fd):self.fd=fd
   def fileno(self):return self.fd
   def close(self):
    calls.append(('close',self.fd))
    if mode=='fatal_and_close' and self.fd==12:raise OSError('close uncertainty')
  proc.stdin=Stream(11);proc.stdout=Stream(12);proc.stderr=Stream(13)
  def poll():calls.append(('poll',));return proc.returncode
  def kill():calls.append(('kill',));proc.returncode=-9
  def wait(timeout):calls.append(('wait',timeout));proc.returncode=1 if mode=='nonzero' else (proc.returncode if proc.returncode is not None else 0);return proc.returncode
  proc.poll=poll;proc.kill=kill;proc.wait=wait
  def popen(cmd,**kw):calls.append(('spawn',tuple(cmd)));self.assertEqual(kw['env']['GIT_NO_LAZY_FETCH'],'1');return proc
  class Selector:
   def __init__(self):self.map={}
   def register(self,s,event,label):self.map[s.fd]=types.SimpleNamespace(fileobj=s,data=label)
   def unregister(self,s):del self.map[s.fd]
   def get_map(self):return self.map
   def select(self,timeout):
    if mode=='timeout':clock[0]+=11;return []
    return [(k,0) for k in tuple(self.map.values())]
   def close(self):calls.append(('selector_close',))
  def read(fd,n):
   if mode=='fatal_and_close':raise fatal
   if mode=='partial' and fd==12:return b''
   return chunks[fd].pop(0)
  def write(fd,b):calls.append(('write',len(b)));return min(len(b),3)
  env={'require':require,'subprocess':types.SimpleNamespace(Popen=popen,PIPE=-1,TimeoutExpired=subprocess.TimeoutExpired),'os':types.SimpleNamespace(environ={},set_blocking=lambda *a:None,write=write,read=read),'selectors':types.SimpleNamespace(DefaultSelector=Selector,EVENT_READ=1,EVENT_WRITE=2),'time':types.SimpleNamespace(monotonic=lambda:clock[0]),'_cleanup':ns['_cleanup']}
  fn=next(n for n in ast.parse((HERE/'candidate01.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='_original_git_batch');fn.body=[n for n in fn.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual helper qualified import bindings','exec'),env)
  result=None;error=None
  try:result=env['_original_git_batch']('/unused',b'abc\ndef\n')
  except BaseException as e:error=e
  self.assertEqual(len([x for x in calls if x[0]=='spawn']),1)
  self.assertEqual([x for x in calls if x[0]=='close'],[('close',11),('close',12),('close',13)])
  self.assertEqual(len([x for x in calls if x[0]=='selector_close']),1)
  if mode=='fatal_and_close':self.assertIs(error,fatal)
  return result,error,calls
 def test_success_one_fresh_process_every_call(self):
  for _ in range(2):self.assertEqual(self.run_case()[0],b'a'*40+b' blob 1\nx\n')
 def test_fail_closed_stream_caps_exit_timeout(self):
  for mode in ('oversize','stderr','nonzero','timeout'):
   with self.subTest(mode=mode):self.assertIsNotNone(self.run_case(mode)[1])
 def test_partial_output_rejected_by_actual_parser(self):
  result,error,_=self.run_case('partial');self.assertIsNone(error)
  env={'require':require,'hashlib':hashlib};fn=next(n for n in ast.parse((HERE/'candidate01.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='_original_batch_rows');exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual parser','exec'),env)
  with self.assertRaises(ValueError):env['_original_batch_rows'](result,[('p',hashlib.sha256(b'x').hexdigest())])
 def test_first_fatal_survives_uncertain_close_all_closed(self):self.run_case('fatal_and_close')
if __name__=='__main__':unittest.main(verbosity=2)
