"""Actual read-only admission plus selected fixture source; never a claim."""
import ast,dataclasses,importlib.util,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;FULL=HERE.parent
SOURCE=HERE/'resource_fixture.py'
if len(sys.argv)>1 and sys.argv[1]=='--source':SOURCE=Path(sys.argv.pop(2));sys.argv.pop(1)
CAP=FULL/'original-import-native-successor-preparation02-2026-10-03/capsule02'
sys.path.insert(0,str(CAP))
from tradingagents.research.admission import admit
class Parent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        draft=json.loads((CAP.parent/'release-draft01.json').read_bytes())
        cls.ad=admit(root=CAP,registration='fixture-registration.json',experiment='original-import-native-success-20261003-02',source=draft['capsule_commit'])
        cls.job=json.loads((CAP/cls.ad.inputs['execution_job']['path']).read_bytes())
        spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.resource_fixture',SOURCE)
        cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)
        assert not {'numpy','torch','scipy'}&set(sys.modules)
    def test_actual_successor_read_only_admission_and_selected_fixture_agree(self):
        self.assertTrue(self.ad.ready);self.assertEqual(self.ad.effective_attempt_budget,3)
        self.module.admitted(self.ad,self.job)
    def test_selected_parent_missing_or_wrong_is_refused(self):
        for parent in [None,'unrelated-parent']:
            ad=dataclasses.replace(self.ad,experiment=self.ad.experiment|{'parent':parent})
            with self.assertRaisesRegex(ValueError,'successor parent/ceiling'):self.module.admitted(ad,self.job)
    def test_selected_ceiling_and_extension_reference_must_match_exact_review(self):
        with self.assertRaisesRegex(ValueError,'successor parent/ceiling'):
            self.module.admitted(dataclasses.replace(self.ad,effective_attempt_budget=2),self.job)
        ad=dataclasses.replace(self.ad,experiment=self.ad.experiment|{'cumulative_budget_extension':None})
        with self.assertRaisesRegex(ValueError,'successor extension'):self.module.admitted(ad,self.job)
    def test_legacy_parent_none_is_unchanged_and_unknown_parent_refused(self):
        self.assertTrue(self.module._engineering_parent(SimpleNamespace(experiment_id='legacy-source-sentinel',experiment={'parent':None})))
        self.assertFalse(self.module._engineering_parent(SimpleNamespace(experiment_id='legacy-source-sentinel',experiment={'parent':'other'})))
    def test_other_fixture_module_nodes_are_unchanged(self):
        before=ast.parse((HERE/'resource_fixture.baseline.py').read_bytes());after=ast.parse(SOURCE.read_bytes())
        mapping={n.name:n for n in after.body if isinstance(n,ast.FunctionDef)}
        for node in before.body:
            if isinstance(node,ast.FunctionDef) and node.name!='admitted':self.assertEqual(ast.dump(node),ast.dump(mapping[node.name]),node.name)
        original=next(n for n in before.body if isinstance(n,ast.FunctionDef) and n.name=='admitted')
        changed=mapping['admitted']
        class StripParent(ast.NodeTransformer):
            def visit_Call(self,node):
                if isinstance(node.func,ast.Name) and node.func.id=='_engineering_parent':
                    return ast.parse("ad.experiment.get('parent') is None",mode='eval').body
                return self.generic_visit(node)
        self.assertEqual(ast.dump(original),ast.dump(StripParent().visit(changed)))
if __name__=='__main__':unittest.main(verbosity=2)
