import ast,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Source(unittest.TestCase):
 def test_parser_has_distinct_phases(self):
  tree=ast.parse((P/'proof_raw01.py').read_text());names={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
  self.assertLessEqual({'materialization','comparison','authenticate','native','closure','proof_archives'},names)
 def test_real_one_use_controller(self):
  s=(P/'proof_outer01.py').read_text();self.assertIn("exist_ok=False",s);self.assertIn("job._command",s);self.assertIn("stop_native",s)
 def test_no_numeric_import_or_claim(self):
  for filename in ('proof_raw01.py','proof_outer01.py','proof_release01.py'):
   s=(P/filename).read_text();t=ast.parse(s)
   self.assertNotIn('ResearchRun.start(',s)
   for n in ast.walk(t):
    if isinstance(n,ast.Import):self.assertFalse({x.name.split('.')[0] for x in n.names}&{'numpy','torch','pandas','pyarrow'})
 def test_metadata_cap(self):self.assertIn('META=8192',(P/'proof_raw01.py').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
