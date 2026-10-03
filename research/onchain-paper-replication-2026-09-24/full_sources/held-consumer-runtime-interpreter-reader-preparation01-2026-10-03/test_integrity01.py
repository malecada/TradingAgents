import ast,hashlib,os,pathlib,runpy,tempfile,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).parent;ROOT=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-05/source');B=runpy.run_path(str(P/'capsule_builder01.py'))
class Tests(unittest.TestCase):
 def fixture(self):
  t=tempfile.TemporaryDirectory(dir=P,prefix='owned-integrity-');self.addCleanup(t.cleanup);base=pathlib.Path(t.name);parent=base/'parent';parent.mkdir();p=parent/'python';p.write_bytes(b'abc');return base,p
 def test_parent_rename_symlink_refused(self):
  base,p=self.fixture();real=os.read;once=True
  def read(fd,size):
   nonlocal once
   if once and os.readlink('/proc/self/fd/'+str(fd))==str(p):
    once=False;p.parent.rename(base/'moved');p.parent.symlink_to('moved')
   return real(fd,size)
  with patch.object(os,'read',side_effect=read),self.assertRaisesRegex(ValueError,'changed'):B['_held_interpreter'](ROOT,p,hashlib.sha256(b'abc').hexdigest(),3)
 def test_same_body_replacement_and_hardlink_refuse(self):
  base,p=self.fixture();real=os.read;once=True
  def read(fd,size):
   nonlocal once
   if once and os.readlink('/proc/self/fd/'+str(fd))==str(p):
    once=False;p.rename(p.parent/'old');p.write_bytes(b'abc')
   return real(fd,size)
  with patch.object(os,'read',side_effect=read),self.assertRaises(ValueError):B['_held_interpreter'](ROOT,p,hashlib.sha256(b'abc').hexdigest(),3)
  os.link(p,p.parent/'alias')
  with self.assertRaises(ValueError):B['_held_interpreter'](ROOT,p,hashlib.sha256(b'abc').hexdigest(),3)
 def test_full_inverse_source_caps_and_existing_runtime_body(self):
  old=(P/'capsule_builder01.py.baseline05.txt').read_text();new=(P/'capsule_builder01.py').read_text();node=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='_held_interpreter');ls=new.splitlines(True);del ls[node.lineno-1:node.end_lineno+1];restored=''.join(ls)
  restored=restored.replace("    _held_interpreter(root,executable,expected['executable_sha256'],expected['executable_bytes'])","    read(executable.parent,executable.name,expected['executable_sha256'],executable.stat().st_size)",1)
  self.assertEqual(restored,old);self.assertEqual(ast.dump(ast.parse(restored)),ast.dump(ast.parse(old)))
  self.assertEqual(B['MAX_FILE'],4194304)
  base,p=self.fixture();os.truncate(p,4194305)
  with self.assertRaisesRegex(ValueError,'source type/link/extent'):B['read'](p.parent,p.name,'0'*64,4194305)
if __name__=='__main__':unittest.main(verbosity=2)
