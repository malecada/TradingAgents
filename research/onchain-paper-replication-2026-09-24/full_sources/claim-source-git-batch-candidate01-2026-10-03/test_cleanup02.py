import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).parent;s=importlib.util.spec_from_file_location('c',p/'candidate01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_first_actual_fatal_outranks_uncertainty_wrapper(self):
  first=MemoryError('real');seen=[]
  def fail():seen.append(1);raise first
  with self.assertRaises(MemoryError) as got:m._git_cleanup((fail,lambda:seen.append(2)),m._GitCleanupFailure('uncertain'))
  self.assertIs(got.exception,first);self.assertEqual(seen,[1,2])
unittest.main()
