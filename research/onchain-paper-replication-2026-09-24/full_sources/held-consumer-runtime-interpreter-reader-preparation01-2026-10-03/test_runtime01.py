"""Stdlib actual interpreter/RECORD metadata; no numerical packages imported."""
import ast,hashlib,json,os,pathlib,runpy,sys,tempfile,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).parent;ROOT=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-05/source')
OLD='--baseline' in sys.argv;sys.argv=[x for x in sys.argv if x!='--baseline']
B=runpy.run_path(str(ROOT/'fixture_tools/capsule_builder01.py' if OLD else P/'capsule_builder01.py'))
EXPECTED=json.loads((P.parent/'held-consumer-original-git-runtime-role-investigation01-2026-10-03/RUNTIME_ROLE_BODY01.json').read_bytes())
class Tests(unittest.TestCase):
 def test_actual_locked_interpreter_and_251_records(self):
  before=set(sys.modules);result=B['held_runtime_metadata'](ROOT,EXPECTED)
  self.assertEqual(result['record_count'],251);self.assertFalse(result['native_controls_verified']);self.assertFalse(result['execution_admitted'])
  self.assertFalse(any(n.split('.')[0] in ('numpy','torch','scipy') for n in set(sys.modules)-before))
  (P/('ACTUAL_RUNTIME_RED_READBACK.json' if OLD else 'ACTUAL_RUNTIME_READBACK01.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 def test_real_executable_bound_and_streamed_extent(self):
  path=pathlib.Path(EXPECTED['resolved_executable']);real=os.read;reads=[]
  def read(fd,size):reads.append(size);return real(fd,size)
  with patch.object(os,'read',side_effect=read):result=B['_held_interpreter'](ROOT,path,EXPECTED['executable_sha256'],EXPECTED['executable_bytes'])
  self.assertEqual(result,{'bytes':31510904,'sha256':EXPECTED['executable_sha256']});self.assertLessEqual(max(reads),65536)
 def tiny(self,body=b'abc'):
  t=tempfile.TemporaryDirectory(dir=P,prefix='owned-runtime-');self.addCleanup(t.cleanup);path=pathlib.Path(t.name)/'python';path.write_bytes(body);return path
 def test_type_hash_and_extent_refusals(self):
  p=self.tiny();sha=hashlib.sha256(b'abc').hexdigest()
  for size,digest in [(True,sha),(0,sha),(64*1024**2+1,sha),(4,sha),(3,'f'*64)]:
   with self.subTest(size=size,digest=digest),self.assertRaises(ValueError):B['_held_interpreter'](ROOT,p,digest,size)
  link=p.parent/'redirect';link.symlink_to('python')
  with self.assertRaises(ValueError):B['_held_interpreter'](ROOT,link,sha,3)
 def test_grow_and_same_size_mutation(self):
  for body in [b'abcdef',b'xyz']:
   p=self.tiny();real=os.read;once=True
   def read(fd,size):
    nonlocal once
    if once:once=False;p.write_bytes(body)
    return real(fd,size)
   # Bootstrap canonical cleanup loader runs before interpreter read. Patch only
   # interpreter descriptors so source-bootstrap IO is not mistaken for target IO.
   def selected(fd,size):
    if os.readlink('/proc/self/fd/'+str(fd))==str(p):return read(fd,size)
    return real(fd,size)
   with patch.object(os,'read',side_effect=selected),self.assertRaises(ValueError):B['_held_interpreter'](ROOT,p,hashlib.sha256(b'abc').hexdigest(),3)
 def test_fatal_survives_both_closes_once(self):
  p=self.tiny();fatal=MemoryError('original interpreter read');rd=os.read;cl=os.close;calls=[]
  def read(fd,size):
   if os.readlink('/proc/self/fd/'+str(fd))==str(p):raise fatal
   return rd(fd,size)
  def close(fd):
   target=os.readlink('/proc/self/fd/'+str(fd));cl(fd)
   if target in (str(p),str(p.parent)):calls.append((fd,target));raise OSError('closed then uncertainty')
  with patch.object(os,'read',side_effect=read),patch.object(os,'close',side_effect=close),self.assertRaises(MemoryError) as got:B['_held_interpreter'](ROOT,p,hashlib.sha256(b'abc').hexdigest(),3)
  self.assertIs(got.exception,fatal);self.assertEqual(len(calls),2);self.assertEqual(len(set(fd for fd,_ in calls)),2)
if __name__=='__main__':unittest.main(verbosity=2)
