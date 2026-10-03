"""Stdlib source-only boundaries; never imports the numerical worker."""
import ast
from pathlib import Path
import unittest
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_concrete_worker(self):
  t=ast.parse((P/'compact_cold_proof.py').read_text())
  names={n.name for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  self.assertLessEqual({'selected','execute','observe','_trajectory','_release','materialize'},names)
 def test_genuine_factory_observation(self):
  s=(P/'compact_cold_features.py').read_text()
  self.assertLess(s.index('compact_terminal.finish(published'),s.index('compact_cold_proof.observe('))
  self.assertLess(s.index('compact_native_features.prepare(terminal'),s.index('compact_cold_proof.observe('))
 def test_no_numerical_top_import(self):
  t=ast.parse((P/'compact_cold_proof.py').read_text())
  for n in t.body:
   if isinstance(n,ast.Import):self.assertFalse({x.name.split('.')[0] for x in n.names}&{'numpy','torch','pandas','pyarrow'})
 def test_real_weakref_slots(self):
  for n in ('compact_terminal','compact_publication','compact_closure'):
   self.assertIn("'__weakref__'",(P/(n+'.py')).read_text())
 def test_no_fake_lifecycle(self):
  s=(P/'compact_cold_proof.py').read_text()
  for forbidden in ('mock','monkeypatch','object.__new__','ResearchRun.start','Receipt(','Published('):self.assertNotIn(forbidden,s)
 def test_dispatch_before_default(self):
  s=(P/'job_payload.py').read_text();self.assertLess(s.index('compact_cold_proof.execute('),s.index('routes={'))
if __name__=='__main__':unittest.main(verbosity=2)
