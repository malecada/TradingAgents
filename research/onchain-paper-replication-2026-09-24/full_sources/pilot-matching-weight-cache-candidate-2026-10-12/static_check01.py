"""Stdlib-only controls; no NumPy import or execution."""
from pathlib import Path
import ast,types,unittest
P=Path(__file__).resolve().parent
class Checks(unittest.TestCase):
 def test_compile_and_kernel_untouched(self):
  for name in ('matching_numeric_policy.py','matching_immutable_session.py','phase_timing.py'):compile((P/name).read_text(),name,'exec')
  self.assertFalse((P/'matching_numeric_kernel.py').exists())
 def test_v1_literal_ast_restore(self):
  a=ast.parse((P/'BASELINE_matching_numeric_policy.py').read_text());b=ast.parse((P/'matching_numeric_policy.py').read_text())
  allowed={n.name for n in a.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};new={n.name:n for n in b.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  for n in a.body:
   if not isinstance(n,(ast.FunctionDef,ast.ClassDef)):continue
   candidate=new[n.name]
   if n.name=='freeze':candidate.body=candidate.body[1:]
   elif isinstance(n,ast.ClassDef):
    for method in candidate.body:
     if isinstance(method,ast.FunctionDef):
      if method.name=='__init__':method.body=method.body[:-1]
      elif method.name=='current':method.body=method.body[:1]+method.body[2:]
      elif method.name=='fill':method.body=method.body[1:]
   self.assertEqual(ast.dump(n),ast.dump(candidate),n.name)
 def test_default_session_close_and_timers_unchanged(self):
  for name in ('matching_immutable_session.py','phase_timing.py'):
   a=ast.parse((P/('BASELINE_'+name)).read_text());b=ast.parse((P/name).read_text())
   if name=='phase_timing.py':
    a.body=[n for n in a.body if not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NUMERIC_COUNTS' for t in n.targets))]
    b.body=[n for n in b.body if not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NUMERIC_COUNTS' for t in n.targets))]
   else:
    cls=next(n for n in b.body if isinstance(n,ast.ClassDef));ctor=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__');ctor.body=ctor.body[:-2]
   self.assertEqual(ast.dump(a),ast.dump(b),name)
 def test_release_exact_refs_idempotent_and_failure(self):
  node=next(n for n in ast.parse((P/'matching_numeric_policy.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_cache_release')
  calls=[];ns={'phase_timing':types.SimpleNamespace(add_count=lambda k,v:calls.append((k,v)))}
  exec(compile(ast.Module(body=[node],type_ignores=[]),'release','exec'),ns)
  a=types.SimpleNamespace(_counts={'cache_reserved_bytes':123,'cache_weight_bytes':100,'cache_validity_bytes':23,'cache_released_bytes':0})
  ns['_cache_release'](a);ns['_cache_release'](a)
  self.assertIsNone(a._cache_weights);self.assertIsNone(a._cache_pair);self.assertEqual(calls,[('cache_released_bytes',123)])
  def fail(*args):raise KeyboardInterrupt('telemetry')
  ns['phase_timing'].add_count=fail;a._counts['cache_reserved_bytes']=123
  with self.assertRaises(KeyboardInterrupt):ns['_cache_release'](a)
  self.assertIsNone(a._cache_storage_pins);self.assertEqual(a._counts['cache_reserved_bytes'],0)
if __name__=='__main__':unittest.main(verbosity=2)
