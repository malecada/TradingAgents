"""Counterexample executes the actual frozen01 main's terminal tail only."""
import ast,pathlib,types,unittest
HERE=pathlib.Path(__file__).resolve().parent
class Legacy(unittest.TestCase):
 def test_actual_legacy_worker_terminal_tail_preserves_body_fatal(self):
  tree=ast.parse((HERE/'oracle01.py').read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Try) and ast.unparse(n.body[0])=='phases.close()')
  wrapper=ast.parse('def legacy(primary,phases,args,root,result):\n pass\n').body[0];wrapper.body=main.body[start:]
  ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),'<actual-legacy-terminal>','exec'),ns)
  original=MemoryError('body');later=SystemExit(17)
  def fail():raise later
  phases=types.SimpleNamespace(close=lambda:None,report=fail)
  args=types.SimpleNamespace(mode='correctness',run_id='synthetic',source_commit='a'*40,manifest_sha256='b'*64)
  try:ns['legacy'](original,phases,args,None,None)
  except BaseException as caught:self.assertIs(caught,original,'actual prior fatal was replaced during terminal assembly')
  else:self.fail('fatal did not escape')
if __name__=='__main__':unittest.main(verbosity=2)
