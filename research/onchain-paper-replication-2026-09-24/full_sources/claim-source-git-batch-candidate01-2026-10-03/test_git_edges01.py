import hashlib,importlib.util,pathlib,subprocess,tempfile,unittest
P=pathlib.Path(__file__).parent;s=importlib.util.spec_from_file_location('c',P/'candidate01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Test(unittest.TestCase):
 def test_surrogate_empty_body_two_commits_tree_and_secret(self):
  with tempfile.TemporaryDirectory() as d:
   def g(*a):return subprocess.check_output(['git',*a],cwd=d,stderr=subprocess.PIPE)
   g('init','-q');name=b'raw-\xff'.decode('utf8','surrogateescape');pathlib.Path(d,name).write_bytes(b'');pathlib.Path(d,'dir').mkdir();pathlib.Path(d,'dir/x').write_bytes(b'a')
   g('add','.');g('-c','user.name=offline','-c','user.email=offline@example.invalid','commit','-qm','one');one=g('rev-parse','HEAD').decode().strip()
   pathlib.Path(d,'dir/x').write_bytes(b'b');g('add','.');g('-c','user.name=offline','-c','user.email=offline@example.invalid','commit','-qm','two');two=g('rev-parse','HEAD').decode().strip()
   m._verify_sources(d,{name:hashlib.sha256(b'').hexdigest()},{one,two})
   with self.assertRaisesRegex(ValueError,'hash mismatch'):m._verify_sources(d,{'dir/x':hashlib.sha256(b'a').hexdigest()},{one,two})
   with self.assertRaisesRegex(ValueError,'non-blob'):m._verify_sources(d,{'dir':'0'*64},{one})
   with self.assertRaisesRegex(ValueError,'secret'):m._verify_sources(d,{'keys/never-read':'0'*64},{one})
unittest.main()
