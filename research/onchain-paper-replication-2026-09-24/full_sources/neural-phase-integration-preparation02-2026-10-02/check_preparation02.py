"""Pure controls/fixture-shape checks only; no guard, socket, claim or trial."""
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
HERE=Path(__file__).resolve().parent

def load(name):
    spec=importlib.util.spec_from_file_location('prepared_'+name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class Checks(unittest.TestCase):
    def test_distinct_identity_cases(self):
        launcher=load('launcher02')
        self.assertEqual(launcher.IDENTITY,'neural-phase-integration-20261002-01')
        self.assertEqual(launcher.CASES,['success','fatal','publication_refusal','near_cap','entry_cap'])
    def test_prepared_not_released(self):
        launcher=load('launcher02')
        with self.assertRaises(ValueError):launcher.require_release({'status':'PREPARATION_ONLY_NOT_RELEASED'})
    def test_real_control_vector_and_refusal(self):
        launcher=load('launcher02')
        args=launcher.unit_arguments(['systemd-run','--unit=invented','true'],{})
        self.assertIn('--property=LimitFSIZE=4194304',args);self.assertIn('--property=RuntimeMaxSec=1800s',args)
        with self.assertRaises(ValueError):launcher.unit_arguments(['systemd-run','--property=LimitFSIZE=1'],{})
        with self.assertRaises(ValueError):launcher.verify_unit_properties({'LimitFSIZE':'1'})
    def test_first_fatal_is_retained(self):
        launcher=load('launcher02');first=MemoryError('first');later=SystemExit('later')
        self.assertIs(launcher.retain(first,later),first)
        ordinary=ValueError('ordinary');self.assertIs(launcher.retain(ordinary,later),later)
    def test_exact_source_membership(self):
        launcher=load('launcher02')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'a').write_text('a');files={'a':launcher.sha(root/'a')}
            launcher.verify_files(root,files);(root/'extra').write_text('x')
            with self.assertRaises(ValueError):launcher.verify_files(root,files)
    def test_fixture_policy_near_cap_and_no_numerical_imports(self):
        fixture=load('fixture02');p=fixture.POLICY
        target=p['max_logical_bytes']-p['tail_reserve_bytes']-128*1024
        self.assertLess(target,p['max_logical_bytes']-p['tail_reserve_bytes'])
        self.assertGreater(target+p['max_json_bytes']+8192,p['max_logical_bytes']-p['tail_reserve_bytes'])
        self.assertEqual(p['max_entries'],128);self.assertEqual(p['max_file_bytes'],4*1024**2)
        tree=ast.parse((HERE/'fixture02.py').read_text())
        imports=[x for x in ast.walk(tree) if isinstance(x,(ast.Import,ast.ImportFrom))]
        self.assertFalse(any('torch' in ast.unparse(x) or 'numpy' in ast.unparse(x) for x in imports))
        self.assertFalse(any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='start' for x in ast.walk(tree)))

if __name__=='__main__':unittest.main(verbosity=2)
