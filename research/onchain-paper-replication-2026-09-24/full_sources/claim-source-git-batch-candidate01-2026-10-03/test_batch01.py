import ast, hashlib, importlib.util, pathlib, subprocess, sys, tempfile, unittest
from unittest.mock import patch
P=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('candidate',sys.argv.pop(1));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def check(root,pins,commits):
    if hasattr(m,'_verify_sources'):return m._verify_sources(root,pins,commits)
    for path,expected in pins.items():
        for commit in commits:
            if hashlib.sha256(m._blob(root,commit,path)).hexdigest()!=expected:raise ValueError('registered source/charter/selection hash mismatch')
def sha(b):return hashlib.sha256(b).hexdigest()
class Tests(unittest.TestCase):
 def test_real_git_fresh_order_names_and_process_count(self):
  with tempfile.TemporaryDirectory() as d:
   def git(*args):return subprocess.check_output(['git',*args],cwd=d,stderr=subprocess.PIPE)
   git('init','-q');names=['a','space name','line\nname','trailing\r','unicodé']
   for name in names:pathlib.Path(d,name).write_bytes(name.encode())
   git('add','.');git('-c','user.name=synthetic','-c','user.email=offline@example.invalid','commit','-qm','tiny')
   c=git('rev-parse','HEAD').decode().strip();pins={n:sha(n.encode()) for n in names}
   real=subprocess.Popen
   with patch.object(m.subprocess,'Popen',wraps=real) as p:
    check(d,pins,{c});first=p.call_count;check(d,pins,{c});self.assertEqual(p.call_count,2*first)
   self.assertLess(first,len(names),'source bodies still spawn one process each')
   with self.assertRaisesRegex(ValueError,'hash mismatch'):check(d,{'a':'0'*64,'../bad':'0'*64},{c})
   with self.assertRaises(ValueError):check(d,{'missing':'0'*64},{c})
   with self.assertRaises(ValueError):check(d,{'a':'0'*64},{c})
 def test_parser_negative_and_order(self):
  if not hasattr(m,'_verify_batch'):self.fail('bounded framing validator absent')
  rows=[('a','1'*40,sha(b'x'))];head=b'2'*40+b' blob 1\n'
  m._verify_batch(head+b'x\n',rows)
  for raw in [b'',b'a missing\n',b'2'*40+b' tree 1\nx\n',head+b'x',head+b'x\njunk',b'2'*40+b' blob 999999999\n',head+b'y\n']:
   with self.assertRaises(ValueError):m._verify_batch(raw,rows)
 def test_cleanup_first_fatal(self):
  if not hasattr(m,'_git_cleanup'):self.fail('owned cleanup reducer absent')
  for fatal in (MemoryError('first'),KeyboardInterrupt(),SystemExit(9)):
   called=[]
   def later():called.append(1);raise OSError('close')
   m._git_cleanup((later,lambda:called.append(2)),fatal)
   self.assertEqual(called,[1,2])
   with self.assertRaises(type(fatal)) as out:m._git_cleanup((lambda:(_ for _ in ()).throw(fatal),lambda:called.append(3)),ValueError())
   self.assertIs(out.exception,fatal);self.assertEqual(called[-1],3)
unittest.main()
