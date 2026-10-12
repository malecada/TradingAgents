"""Stdlib-only changed-seam controls; no NumPy import/execution."""
import ast,copy,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Amendment(unittest.TestCase):
 def tail(self):
  tree=ast.parse((P/'matching_immutable_session.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));ctor=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
  body=ctor.body[-2:];node=ast.FunctionDef(name='tail',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='self')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[])
  return ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
 def test_selector_fatal_releases_acquired_backend_and_preserves_first(self):
  for cleanup_fails in (False,True):
   calls=[]
   class Fatal(BaseException):
    def add_note(self,*args):raise AssertionError('overridden note must not execute')
   primary=Fatal('original')
   def selected(adapter):raise primary
   def cleanup():
    calls.append('cleanup')
    if cleanup_fails:raise KeyboardInterrupt('secondary')
   ns={'matching_numeric_policy':types.SimpleNamespace(cache_selected=selected)};exec(compile(self.tail(),'actual-tail','exec'),ns)
   obj=types.SimpleNamespace(_normalizer_cleanup=cleanup,_numeric_adapter=object())
   with self.assertRaises(Fatal) as caught:ns['tail'](obj)
   self.assertIs(caught.exception,primary);self.assertEqual(calls,['cleanup'])
 def test_miss_validation_before_initial_allocation_and_no_hit_row_gather(self):
  tree=ast.parse((P/'matching_numeric_policy.py').read_text());f={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
  domain=ast.unparse(f['_cache_domain'])
  for removed in ('np.isfinite','np.abs','left[il]','right[ir]'):self.assertNotIn(removed,domain)
  fill=ast.unparse(f['_cache_fill']);self.assertLess(fill.index('kernel.fill_agreement'),fill.index('weights = np.empty(total'))
  self.assertLess(fill.index('kernel.fill_agreement'),fill.index('adapter._cache_valid[locations] = True'))
  self.assertLess(fill.index('_feature_current(left'),fill.index('missing ='))
 def test_harness_production_shape_and_compile(self):
  for name in ('matching_numeric_policy.py','matching_immutable_session.py','numeric_harness.py','benchmark01.py'):compile((P/name).read_text(),name,'exec')
  text=(P/'numeric_harness.py').read_text();self.assertNotIn('engine.result(',text);self.assertIn('engine.score_only(',text)
  self.assertEqual(text.count('edge_cache_policy=dict(ann.ADAPTIVE_EDGE_POLICY)'),2)
  self.assertLess(text.index('start=time.perf_counter()'),text.index('state=engine.create('))
  self.assertLess(text.index('engine.close(state);state=None'),text.index('elapsed=time.perf_counter()-start'))
  self.assertIn('budget=1024',text);self.assertIn('default=1000000',(P/'benchmark01.py').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
