import ast
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent

def function(name):
    p=HERE/'resource_binding.py'
    if not p.exists():raise AssertionError('resource admission absent')
    t=ast.parse(p.read_text());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('require',name)]
    ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns);return ns[name]

class Contract(unittest.TestCase):
    def test_resource_kind_and_payload_no_fake_fit(self):
        f=function('validate_job');v={'schema_version':1,'kind':'compact_resource','resources':{},'environment_input':'env','payload':{'representation_jobs':{'r':{}}}}
        f(v)
        for x in ({**v,'kind':'fit'},{**v,'schema_version':True},{**v,'payload':{}},{**v,'payload':{'representation_jobs':{},'batch_plan_input':'fake'}}):
            with self.subTest(x=x),self.assertRaises(ValueError):f(x)
    def test_reserved_import_stage_policy(self):
        f=function('import_policy');v={'schema_version':1,'max_numeric_bytes':65536,'max_stage_bytes':131072}
        self.assertEqual(f(v),v)
        for x in ({**v,'max_numeric_bytes':True},{**v,'max_stage_bytes':1},{**v,'other':1}):
            with self.subTest(x=x),self.assertRaises(ValueError):f(x)
    def test_no_fresh_matching_receipt_for_import(self):
        p=HERE/'original_import_stage.py'
        self.assertTrue(p.exists(),'real stage implementation required')
        tree=ast.parse(p.read_text());names={n.name for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
        self.assertTrue({'ImportStage','complete_import','attach'}<=names)
        self.assertNotIn('PairSession',p.read_text())
        self.assertNotIn('begin_dictionary(',p.read_text())

if __name__=='__main__':unittest.main()
