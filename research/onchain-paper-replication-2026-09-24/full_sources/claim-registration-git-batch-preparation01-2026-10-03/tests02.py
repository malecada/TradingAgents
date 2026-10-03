"""Synthetic source tests only; no real research claims or package imports."""
import hashlib,json,os,runpy,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
NS=runpy.run_path(str(HERE/os.environ.get('CANDIDATE','verify.candidate01.py')))
NS=NS['_blob'].__globals__
H='1'*40
frame=lambda b:(b'2'*40+b' blob '+str(len(b)).encode()+b'\n'+b+b'\n')
class Tests(unittest.TestCase):
 def pair(self,root,source,design,path):return NS['_registration_pair'](root,{'source':source,'design_source':design,'registration':path})
 def test_pair_one_transport_duplicate_requests(self):
  calls=[]
  def transport(root,req,expression=None):calls.append((req,expression));return frame(b'a')+frame(b'b')
  with patch.dict(NS,{'_git_transport':transport}):self.assertEqual(list(self.pair('.',H,H,'x')), [b'a',b'b'])
  self.assertEqual(calls, [(((H+':x\n')*2).encode(),None)])
 def test_first_body_before_second_parse(self):
  with patch.dict(NS,{'_git_transport':lambda *a:frame(b'a')+b'bad\n'}):
   p=self.pair('.',H,H,'x');self.assertEqual(next(p),b'a')
   with self.assertRaises(ValueError):next(p)
 def test_first_comparison_before_invalid_second_ref(self):
  with patch.dict(NS,{'_git_transport':lambda *a:b'a'}):
   p=self.pair('.',H,'invalid','x');self.assertEqual(next(p),b'a')
   with self.assertRaises(ValueError):next(p)
 def test_malformed_frames(self):
  for raw in (b'',frame(b'a'),frame(b'a')+frame(b'b')+b'extra',frame(b'a')+b'2'*40+b' tree 0\n\n',frame(b'a')+b'2'*40+b' blob 01\nx\n',frame(b'a')+b'2'*40+b' blob 8388609\n'):
   with self.subTest(raw=raw[:60]),patch.dict(NS,{'_git_transport':lambda *a:raw}):
    with self.assertRaises(ValueError):list(self.pair('.',H,H,'x'))
 def test_fallback_and_fresh_invocations(self):
  calls=[]
  def transport(root,req,expression=None):calls.append((req,expression));return str(len(calls)).encode()
  with patch.dict(NS,{'_git_transport':transport}):
   self.assertEqual(list(self.pair('.',H,H,'a\nb')),[b'1',b'2']);self.assertEqual(list(self.pair('.',H,H,'a\nb')),[b'3',b'4'])
  self.assertTrue(all(x[0]==b'' and x[1]==H+':a\nb' for x in calls))
 def test_typed_secret_null_refusals(self):
  for path in (None,12,'../x','/x','keys/x','.env','x\0y'):
   with self.subTest(path=path):
    with self.assertRaises((ValueError,TypeError)):list(self.pair('.',H,H,path))
 def test_first_fatal_cleanup(self):
  fatal=MemoryError('first');seen=[]
  def fail():seen.append(1);raise OSError('close')
  NS['_git_cleanup']((fail,lambda:seen.append(2)),fatal)
  self.assertEqual(seen,[1,2])
  with self.assertRaises(NS['_GitCleanupFailure']):NS['_git_cleanup']((fail,),None)
 def test_real_tiny_git(self):
  with tempfile.TemporaryDirectory(prefix='tiny-git-',dir=HERE) as d:
   root=Path(d);env={**os.environ,'GIT_AUTHOR_NAME':'Synthetic','GIT_AUTHOR_EMAIL':'synthetic@example.invalid','GIT_COMMITTER_NAME':'Synthetic','GIT_COMMITTER_EMAIL':'synthetic@example.invalid','GIT_NO_LAZY_FETCH':'1','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
   def git(*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=root,env=env,stderr=subprocess.PIPE).decode().strip()
   git('init','-q');(root/'r.json').write_bytes(b'{"version":1}\n');(root/'a\nb').write_bytes(b'line\n');git('add','.');git('commit','-qm','synthetic one');a=git('rev-parse','HEAD')
   (root/'r.json').write_bytes(b'{"version":2}\n');git('add','.');git('commit','-qm','synthetic two');b=git('rev-parse','HEAD')
   self.assertEqual(list(self.pair(root,a,b,'r.json')),[b'{"version":1}\n',b'{"version":2}\n'])
   self.assertEqual(list(self.pair(root,a,a,'a\nb')),[b'line\n']*2)
   with self.assertRaises(ValueError):list(self.pair(root,a,b,'missing'))
 def test_actual_verifier_first_hash_before_missing_design(self):
  with tempfile.TemporaryDirectory(prefix='schema-fixture-',dir=HERE) as d:
   directory=Path(d)/'research_runs'/'synthetic';directory.mkdir(parents=True)
   (directory/'claim.json').write_text(json.dumps({'experiment_id':'synthetic','source':H,'registration':'x','registration_sha256':'wrong'}))
   with patch.dict(NS,{'_git_transport':lambda *a:b'{}'}):
    with self.assertRaisesRegex(ValueError,'registration hash differs'):NS['verify_claim'](directory)
 def test_actual_verifier_program_before_second_frame(self):
  raw=b'{"program_id":"real"}'
  with tempfile.TemporaryDirectory(prefix='schema-fixture-',dir=HERE) as d:
   directory=Path(d)/'research_runs'/'synthetic';directory.mkdir(parents=True)
   (directory/'claim.json').write_text(json.dumps({'experiment_id':'synthetic','source':H,'design_source':H,'registration':'x','registration_sha256':hashlib.sha256(raw).hexdigest(),'program_id':'wrong'}))
   with patch.dict(NS,{'_git_transport':lambda *a:frame(raw)+b'bad\n'}):
    with self.assertRaisesRegex(ValueError,'claim program differs'):NS['verify_claim'](directory)
 def test_transport_timeout(self):
  with patch.dict(NS,{'_GIT_SECONDS':-1}):
   with self.assertRaises(subprocess.TimeoutExpired):NS['_git_transport'](HERE,b'')
 def test_inverse_bytes(self):
  c=(HERE/'verify.candidate01.py').read_text();b=(HERE/'verify.baseline01.py').read_text()
  helper=c[c.index('def _registration_pair('):c.index('def verify_claim(')]
  restored=c.replace(helper,'').replace('    registration_pair = _registration_pair(root, claim)\n    registration = next(registration_pair)','    registration = _blob(root, claim["source"], claim["registration"])').replace('if next(registration_pair) != registration:', 'if _blob(root, claim["design_source"], claim["registration"]) != registration:')
  self.assertEqual(restored,b)
if __name__=='__main__':unittest.main(verbosity=2)
