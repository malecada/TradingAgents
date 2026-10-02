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
    def test_stricter_entry_tail_and_full_closure_arithmetic(self):
        old=(HERE/'baseline/neural_physical.py').read_text()
        candidate=(HERE/'candidate-neural_physical02.py').read_text()
        self.assertEqual(candidate.replace("self.policy['max_entries']-(0 if tail else 18)","self.policy['max_entries']-(0 if tail else 16)"),old)
        self.assertEqual((HERE/'source/tradingagents/research/onchain_replication/neural_physical.py').read_text(),candidate)
        active=128-18;publication_reserve=2
        self.assertEqual(active,110);self.assertGreater(active+publication_reserve,active)
        tail_names=['cell-'+str(i) for i in range(9)]+['failure-ledger','result','outputs/cell-ledger','outputs/resource-summary','outputs/artifact-index','terminal','observer','physical-final']
        self.assertEqual(len(tail_names),17)
        self.assertEqual(active+len(tail_names),127)
        self.assertLessEqual(active+len(tail_names)-1+publication_reserve,128)
    def test_exact_candidate03_overlays_and_phase_identity(self):
        import hashlib
        other=HERE.parent/'storage-publication-observation-2026-10-02'
        for a,b in [('candidate03.py','workflow_storage.py'),('candidate-resources03.py','resources.py')]:
            self.assertEqual((other/a).read_bytes(),(HERE/'source/tradingagents/research/onchain_replication'/b).read_bytes())
        phase=HERE.parent/'neural-phase-receipts-candidate-2026-10-02/candidate'
        for name in ('neural_resource.py','neural_phases.py'):
            self.assertEqual((phase/name).read_bytes(),(HERE/'source/tradingagents/research/onchain_replication'/name).read_bytes())
    def test_child_vector_timeout_and_output_envelope_statically(self):
        fixture=load('fixture02');child=HERE/'child_scope02.py'
        self.assertEqual(child.read_bytes(),(HERE/'source/child_scope.py').read_bytes())
        tree=ast.parse((HERE/'fixture02.py').read_text())
        bridge=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='child_bridge')
        runs=[n for n in ast.walk(bridge) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='run']
        self.assertEqual(len(runs),1)
        kw={k.arg:ast.literal_eval(k.value) for k in runs[0].keywords if k.arg in ('timeout','check')}
        self.assertEqual(kw,{'timeout':10,'check':False})
        self.assertNotIn('capture_output',ast.unparse(bridge))
        childtree=ast.parse(child.read_text())
        self.assertFalse(any('torch' in ast.unparse(n) or 'numpy' in ast.unparse(n) for n in ast.walk(childtree) if isinstance(n,(ast.Import,ast.ImportFrom))))
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
