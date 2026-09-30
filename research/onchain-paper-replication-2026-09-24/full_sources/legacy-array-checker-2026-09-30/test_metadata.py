"""Compact retained-receipt joins only; no array/body reads or empirical work."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREP = HERE.parent/'legacy-graph-array-preparation-2026-09-30/inputs.json'
CONFIG = ROOT/'research/onchain-paper-replication-2026-09-24/config/graph.json'


class Tests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((HERE/'metadata.py').is_file(), 'metadata adapter missing')
        spec = importlib.util.spec_from_file_location('legacy_metadata', HERE/'metadata.py')
        self.m = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.m)
        self.prep = json.loads(PREP.read_bytes())
        self.raw = {n:(ROOT/n).read_bytes() for n in self.prep['files']}
        self.config = CONFIG.read_bytes()
    def check(self):
        return self.m.validate(self.prep, self.raw, self.config, str(ROOT))
    def change(self, suffix, mutate):
        name, = [n for n in self.raw if n.endswith(suffix)]
        value = json.loads(self.raw[name]); mutate(value)
        self.raw[name] = json.dumps(value,sort_keys=True,separators=(',',':')).encode()
        self.prep['files'][name].update(bytes=len(self.raw[name]),sha256=hashlib.sha256(self.raw[name]).hexdigest())
    def test_original_failed_claim_and_two_complete_phases(self):
        value=self.check()
        self.assertEqual(value['historical_dispositions'],{'complete':7,'unavailable':102})
        self.assertEqual([g['week'] for g in value['graphs']],['2022-01-03','2022-06-13'])
        self.assertEqual(value['array_bytes_declared'],1037092456)
        self.assertFalse(value['arrays_read'])
    def test_unbound_compact_bytes_rejected(self):
        n=next(iter(self.raw));self.raw[n]+=b' '
        with self.assertRaises(ValueError):self.check()
    def test_original_terminal_cannot_be_promoted(self):
        self.change('/failed.json',lambda v:v.update(status='complete'))
        with self.assertRaises(ValueError):self.check()
    def test_full_historical_denominator_required(self):
        self.change('/cell-ledger.json',lambda v:v.pop())
        name, = [n for n in self.raw if n.endswith('/cell-ledger.json')]
        h=self.prep['files'][name]['sha256']
        self.change('/closure.json',lambda v:v.update(cell_ledger_sha256=h))
        self.change('/observer.json',lambda v:v.update(observer_ledger_sha256=h))
        with self.assertRaisesRegex(ValueError,'complete historical denominator'):self.check()
    def test_complete_phase_required(self):
        self.change('2022-01-03/decode_graph/result.json',lambda v:v.update(status='unavailable'))
        with self.assertRaises(ValueError):self.check()
    def test_source_identity_required(self):
        self.change('2022-01-03/decode_graph/intent.json',lambda v:v.update(source_commit='a'*40))
        with self.assertRaises(ValueError):self.check()
    def test_coverage_order_required(self):
        self.change('2022-01-03-coverage.json',lambda v:v['members'].reverse())
        graph=self.prep['graphs'][0]
        graph['coverage']=copy.deepcopy(self.prep['files'][graph['coverage']['path']])
        with self.assertRaisesRegex(ValueError,'daily continuity'):self.check()
    def test_graph_configuration_raw_binding_required(self):
        self.config += b' '
        with self.assertRaises(ValueError):self.check()
    def test_array_declared_path_exact(self):
        self.prep['graphs'][0]['arrays'][0]['path']='../../outside.npy'
        with self.assertRaises(ValueError):self.check()
    def test_declared_total_exact(self):
        self.prep['array_bytes_declared']+=1
        with self.assertRaises(ValueError):self.check()


if __name__=='__main__':unittest.main(verbosity=2)
