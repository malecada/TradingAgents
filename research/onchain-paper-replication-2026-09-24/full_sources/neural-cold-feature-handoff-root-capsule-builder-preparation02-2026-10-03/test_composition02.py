import ast,hashlib,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).parent;ROOT=P.resolve().parents[3];O=P.parent/'neural-cold-feature-handoff-root-capsule-builder-preparation01-2026-10-03'
s=importlib.util.spec_from_file_location('b2',P/'builder02.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_inverse_whole_AST(self):
  text=(P/'builder02.py').read_text()
  for before,after in json.loads((P/'replacements02.json').read_bytes()).items():text=text.replace(after,before)
  self.assertEqual(ast.dump(ast.parse(text)),ast.dump(ast.parse((O/'builder01.py').read_bytes())))
 def test_exact_manifest_and_inventory_pins(self):
  for path,expected in m.PINS.items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),expected)
  self.assertEqual(hashlib.sha256((ROOT/m.CSC/'source_inventory04.json').read_bytes()).hexdigest(),m.INV)
  # Source-only load, no build/export/inventory/runtime verification invoked.
  gen=m.load(ROOT/m.GEN/'generate04.py','selected_generator_test');metadata=m.load(ROOT/m.CSC/'prepare_metadata_composed04.py','selected_metadata_test')
  self.assertEqual(gen.PINNED_INVENTORY,m.INV);inv=json.loads((ROOT/m.CSC/'source_inventory04.json').read_bytes());self.assertEqual(len(metadata.source_mapping(ROOT/m.CSC/'source-bodies',inv)),195)
 def test_templates_remain_unregistered(self):
  for n in ['request-export01.json','request-inputs01.json','request-materialize01.json','request-compare01.json']:self.assertEqual((P/n).read_bytes(),(O/n).read_bytes())
unittest.main(verbosity=2)
