"""Actual terminal boundary extracted through AST; only stdlib stand-in IO."""
import ast,pathlib,types,unittest
HERE=pathlib.Path(__file__).resolve().parent
class Terminal(unittest.TestCase):
 def helper(self):
  path=HERE/'oracle02.py';self.assertTrue(path.exists(),'corrected terminal boundary missing')
  tree=ast.parse(path.read_bytes());names={'terminal_boundary','preserve','safe_note','close_once'}
  nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
  self.assertEqual({n.name for n in nodes},names,'actual terminal boundary helpers missing')
  ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);return ns
 def test_first_body_fatal_survives_every_later_assembly_failure(self):
  ns=self.helper()
  for first in (MemoryError('body'),SystemExit(7)):
   for later in (ValueError('assembly'),MemoryError('assembly'),SystemExit(9)):
    calls=[]
    def assemble(primary):calls.append('assemble');raise later
    with self.assertRaises(type(first)) as caught:ns['terminal_boundary'](first,lambda:calls.append('close'),assemble,lambda v:calls.append('publish'))
    self.assertIs(caught.exception,first);self.assertEqual(calls,['close','assemble'])
 def test_phase_close_and_publication_each_attempted_once(self):
  ns=self.helper();first=MemoryError('body');calls=[]
  def close():calls.append('close');raise SystemExit(12)
  def assembly(primary):calls.append('assemble');self.assertIs(primary,first);return {'status':'failed'}
  def publish(value):calls.append('publish');self.assertEqual(value['status'],'failed');raise MemoryError('publication')
  with self.assertRaises(MemoryError) as caught:ns['terminal_boundary'](first,close,assembly,publish)
  self.assertIs(caught.exception,first);self.assertEqual(calls,['close','assemble','publish'])
 def test_actual_fatal_promoted_over_ordinary_body(self):
  ns=self.helper();first=ValueError('body');fatal=SystemExit(4)
  def assembly(primary):raise fatal
  with self.assertRaises(SystemExit) as caught:ns['terminal_boundary'](first,None,assembly,lambda v:None)
  self.assertIs(caught.exception,fatal);self.assertIs(fatal.__cause__,first)
 def test_error_format_failure_cannot_replace_original(self):
  ns=self.helper()
  class BadFatal(MemoryError):
   def __str__(self):raise SystemExit(8)
   def __repr__(self):raise KeyboardInterrupt('repr')
  first=BadFatal()
  with self.assertRaises(BadFatal) as caught:ns['terminal_boundary'](first,None,lambda p:{'message':str(p)},lambda v:None)
  self.assertIs(caught.exception,first)
  self.assertIs(ns['preserve'](first,BadFatal()),first)
 def test_success_and_publication_failure_never_fabricate_pass(self):
  ns=self.helper();calls=[]
  self.assertEqual(ns['terminal_boundary'](None,lambda:calls.append('close'),lambda p:{'status':'passed'},lambda v:calls.append(v)),0)
  self.assertEqual(calls,['close',{'status':'passed'}])
  error=OSError('disk')
  def fail(v):raise error
  with self.assertRaises(OSError) as caught:ns['terminal_boundary'](None,None,lambda p:{'status':'passed'},fail)
  self.assertIs(caught.exception,error)
 def test_actual_worker_and_coordinator_route_assembly_inside_boundary(self):
  self.helper()
  for name in ('oracle02.py','coordinator02.py'):
   tree=ast.parse((HERE/name).read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
   text=ast.unparse(main);self.assertIn('terminal_boundary(',text);self.assertIn('assemble',text)
   self.assertIn('source-manifest02.json',(HERE/name).read_text());self.assertNotIn('source-manifest01.json',(HERE/name).read_text())
if __name__=='__main__':unittest.main(verbosity=2)
