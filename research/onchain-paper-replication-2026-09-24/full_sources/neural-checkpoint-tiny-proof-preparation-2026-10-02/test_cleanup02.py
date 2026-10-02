import ast,pathlib,unittest
P=pathlib.Path(__file__).with_name('oracle01.py')
class Cleanup(unittest.TestCase):
 def test_later_actual_fatal_is_not_swallowed_by_ordinary_primary(self):
  node=next(n for n in ast.parse(P.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='close_once')
  ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(P),'exec'),ns)
  primary=ValueError('original');fatal=MemoryError('cleanup')
  def fail():raise fatal
  with self.assertRaises(MemoryError) as caught:ns['close_once']((fail,),primary)
  self.assertIs(caught.exception,fatal);self.assertIs(fatal.__cause__,primary)
if __name__=='__main__':unittest.main(verbosity=2)
