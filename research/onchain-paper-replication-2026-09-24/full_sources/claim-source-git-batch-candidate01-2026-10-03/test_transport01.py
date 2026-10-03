import importlib.util,pathlib,subprocess,sys,unittest,os
from unittest.mock import patch
P=pathlib.Path(__file__).parent
s=importlib.util.spec_from_file_location('candidate',P/'candidate01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def child(self,script,expected=None,limit=None):
  real=subprocess.Popen;made=[]
  def spawn(command,**kw):
   p=real([sys.executable,'-B','-c',script],**kw);made.append(p);return p
  old=m._GIT_SECONDS
  if limit is not None:m._GIT_SECONDS=limit
  try:
   with patch.object(m.subprocess,'Popen',side_effect=spawn):
    if expected:
     with self.assertRaises(expected):m._git_transport(P,b'x\n')
    else:self.assertEqual(m._git_transport(P,b'x\n'),b'ok')
  finally:m._GIT_SECONDS=old
  self.assertEqual(len(made),1);p=made[0];self.assertIsNotNone(p.poll())
  for f in [p.stdin,p.stdout,p.stderr]:self.assertTrue(f.closed)
 def test_success_reaped_closed(self):self.child('import sys;sys.stdin.buffer.read();sys.stdout.buffer.write(b"ok")')
 def test_dead_child(self):self.child('raise SystemExit(3)',ValueError)
 def test_timeout_killed_reaped(self):self.child('import time;time.sleep(5)',subprocess.TimeoutExpired,.05)
 def test_stderr_ceiling(self):self.child('import sys;sys.stderr.buffer.write(b"x"*100000);sys.stderr.flush()',ValueError)
 def test_stdout_ceiling(self):
  with patch.object(m,'_GIT_BODY',1024):self.child('import sys;sys.stdout.buffer.write(b"x"*100000);sys.stdout.flush()',ValueError)
 def test_first_fatal_during_actual_read(self):
  for fatal in [MemoryError('sentinel'),KeyboardInterrupt('sentinel'),SystemExit(17)]:
   real=subprocess.Popen;made=[];read=os.read
   def spawn(command,**kw):
    p=real([sys.executable,'-B','-c','import sys,time;sys.stdout.buffer.write(b"ok");sys.stdout.flush();time.sleep(5)'],**kw);made.append(p);return p
   def fail(fd,n):
    if made and fd==made[0].stdout.fileno():raise fatal
    return read(fd,n)
   with patch.object(m.subprocess,'Popen',side_effect=spawn),patch.object(os,'read',side_effect=fail):
    with self.assertRaises(type(fatal)) as out:m._git_transport(P,b'')
   self.assertIs(out.exception,fatal);self.assertIsNotNone(made[0].poll())
   for f in [made[0].stdin,made[0].stdout,made[0].stderr]:self.assertTrue(f.closed)
 def test_request_validation(self):
  for p in ['/absolute','../x','keys/x','.env','dir/.env.a','apis/a','hf_token.txt','null\0']:
   with self.assertRaises(ValueError):m._source_request('1'*40,p)
  for c in ['main','1'*39,None]:
   with self.assertRaises(ValueError):m._source_request(c,'a')
 def test_fresh_order_group_count(self):
  rows={str(i):m.hashlib.sha256(str(i).encode()).hexdigest() for i in range(163)};seen=[]
  def transport(root,req,expression=None):
   seen.append(req);out=b''
   for line in req.splitlines():
    b=line.split(b':',1)[1];out+=b'1'*40+b' blob '+str(len(b)).encode()+b'\n'+b+b'\n'
   return out
  with patch.object(m,'_git_transport',side_effect=transport):
   m._verify_sources(P,rows,{'1'*40});m._verify_sources(P,rows,{'1'*40})
  self.assertEqual([len(x.splitlines()) for x in seen],[128,35,128,35])
 def test_first_hash_before_later_bad_row(self):
  def frame(b):return b'1'*40+b' blob '+str(len(b)).encode()+b'\n'+b+b'\n'
  with self.assertRaisesRegex(ValueError,'hash mismatch'):
   m._verify_batch(frame(b'x')+b'bad missing\n',[('a','1'*40,'0'*64),('bad','1'*40,'0'*64)])
unittest.main()
