"""Actual pure-metadata admission and exact closed lineage tests; no claim/array."""
import ast,dataclasses,importlib.util,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;CAP=HERE/'capsule03';SOURCE=HERE/'resource_fixture.py'
if len(sys.argv)>1 and sys.argv[1]=='--source':SOURCE=Path(sys.argv.pop(2));sys.argv.pop(1)
sys.path.insert(0,str(CAP))
from tradingagents.research.admission import admit
class Parent(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  draft=json.loads((HERE/'release-draft01.json').read_bytes())
  cls.ad=admit(root=CAP,registration='fixture-registration.json',experiment='original-import-native-success-20261003-03',source=draft['capsule_commit'])
  cls.job=json.loads((CAP/cls.ad.inputs['execution_job']['path']).read_bytes())
  spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.resource_fixture',SOURCE);cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)
  assert not {'numpy','torch','scipy'}&set(sys.modules)
 def test_actual_fresh03_admission_and_selected_fixture_agree(self):
  self.assertTrue(self.ad.ready);self.assertEqual(self.ad.effective_attempt_budget,4);self.module.admitted(self.ad,self.job)
 def test_parent_missing_wrong_or_terminal_identity_is_refused(self):
  for parent in [None,'unrelated-parent','original-import-native-success-20261003-01']:
   with self.assertRaises(ValueError):self.module.admitted(dataclasses.replace(self.ad,experiment=self.ad.experiment|{'parent':parent}),self.job)
 def test_old_ceiling_or_missing_and_changed_review_is_refused(self):
  with self.assertRaises(ValueError):self.module.admitted(dataclasses.replace(self.ad,effective_attempt_budget=3),self.job)
  for ref in [None,{'extension':{'path':'fixture_budget/cumulative-extension01.json','sha256':'0'*64},'review':{'path':'fixture_budget/cumulative-extension-review02.json','sha256':'0'*64}}]:
   with self.assertRaises(ValueError):self.module.admitted(dataclasses.replace(self.ad,experiment=self.ad.experiment|{'cumulative_budget_extension':ref}),self.job)
 def test_legacy_none_and_unknown_parent_routes_are_preserved(self):
  self.assertTrue(self.module._engineering_parent(SimpleNamespace(experiment_id='legacy-route',experiment={'parent':None})))
  self.assertFalse(self.module._engineering_parent(SimpleNamespace(experiment_id='legacy-route',experiment={'parent':'unrelated'})))
 def test_only_fixed03_lineage_nodes_are_added(self):
  base=ast.parse((HERE/'resource_fixture.baseline04.py').read_bytes());after=ast.parse(SOURCE.read_bytes())
  fn=next(n for n in after.body if isinstance(n,ast.FunctionDef) and n.name=='_engineering_parent')
  fn.body=[n for n in fn.body if not (isinstance(n,ast.If) and any(isinstance(c,ast.Constant) and c.value=='original-import-native-success-20261003-03' for c in ast.walk(n)))]
  after.body=[n for n in after.body if not (isinstance(n,ast.FunctionDef) and n.name=='_engineering_parent03')]
  self.assertEqual(ast.dump(base),ast.dump(after))
if __name__=='__main__':unittest.main(verbosity=2)
