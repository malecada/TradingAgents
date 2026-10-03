import ast,hashlib,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).parent;O=P.parent/'neural-cold-feature-handoff-engineering-registration-preparation03-2026-10-03';C=P.parent/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03'
s=importlib.util.spec_from_file_location('g4',P/'generate04.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_inverse_whole_AST(self):
  pins=json.loads((P/'origins04.json').read_bytes());a=(P/'generate04.py').read_text().replace(pins['inventory_sha256'],pins['prior_inventory_sha256']);self.assertEqual(ast.dump(ast.parse(a)),ast.dump(ast.parse((O/'generate03.py').read_bytes())))
 def test_exact_inventory_and_frozen_contracts(self):
  self.assertEqual(m.PINNED_INVENTORY,hashlib.sha256((C/'source_inventory04.json').read_bytes()).hexdigest());self.assertEqual(m.RELEASE_SHA,'53c2294b7b38f340e9160e4484a6b7506942ce36e2dff12694a47f9b72206812')
  for n in ['CHARTER_MATERIALIZE02.md','CHARTER_COMPARE02.md','HISTORY02.md','request-materialize03.json','request-compare02.json']:self.assertEqual((P/n).read_bytes(),(O/n).read_bytes())
unittest.main(verbosity=2)
