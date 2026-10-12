"""Stdlib-only extracted entry/dispatch controls; no numerical imports."""
import ast,unittest
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent
TREE=ast.parse((P/'serial_advance.py').read_text())
def extract(*names,namespace):
 body=[n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name in names]
 exec(compile(ast.Module(body=body,type_ignores=[]),'<extracted>','exec'),namespace)
 return namespace
class Checks(unittest.TestCase):
 def test_fallback_once_no_write_original_arguments(self):
  state={'untouched':object()};before=state.copy();calls=[]
  ns=extract('advance_checked',namespace={'try_advance_checked':lambda *a,**kw:None,'ORIGINAL':lambda *a,**kw:calls.append((a,kw)) or 17})
  self.assertEqual(ns['advance_checked'](state,'a','b','c',max_operations=18,normalizer='n',edge_chunk_fill='e'),17)
  self.assertEqual(state,before);self.assertEqual(len(calls),1)
  self.assertEqual(calls[0][1],dict(max_operations=18,edge_cache_policy=None,normalizer='n',edge_chunk_fill='e'))
 def test_selected_zero_is_not_fallback(self):
  ns=extract('advance_checked',namespace={'try_advance_checked':lambda *a,**kw:0,'ORIGINAL':lambda *a,**kw:(_ for _ in ()).throw(AssertionError())})
  self.assertEqual(ns['advance_checked']({},1,2,3,max_operations=1),0)
 def test_fresh_public_check_and_fatal(self):
  order=[];ns=extract('advance',namespace={'ann':SimpleNamespace(check=lambda *a:order.append('check')),'advance_checked':lambda *a,**kw:order.append('advance') or 1})
  for _ in range(2):ns['advance']({},1,2,3,max_operations=1)
  self.assertEqual(order,['check','advance']*2)
  with self.assertRaises(ValueError):ns['advance']({},1,2,3,max_operations=True)
  fatal=KeyboardInterrupt('original')
  def reject(*a):raise fatal
  ns['ann'].check=reject
  with self.assertRaises(KeyboardInterrupt) as cm:ns['advance']({},1,2,3,max_operations=1)
  self.assertIs(cm.exception,fatal)
 def test_scratch_bound_and_prewrite_sentinel(self):
  ns=extract('scratch_bound',namespace={});self.assertEqual(ns['scratch_bound'](16,16,1024),251904)
  function=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='try_advance_checked')
  self.assertIsInstance(function.body[2],ast.If)
  self.assertIsInstance(function.body[2].body[0],ast.Return)
  self.assertEqual(function.body[2].body[0].value.value,None)
 def test_source_normalization_order_and_no_engine_handoff(self):
  source=(P/'serial_advance.py').read_text()
  self.assertLess(source.index('axis=1,keepdims=True'),source.index('axis=0,keepdims=True'))
  self.assertNotIn('engine.advance',source)
  self.assertNotIn('hard.create',source)
  self.assertIn('if max_operations>needed:',source)
if __name__=='__main__':unittest.main()
