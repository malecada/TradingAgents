"""Offline controls over retained genuine metadata; no lifecycle/array imports."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'tradingagents/research/onchain_replication/graph_legacy_coverage.py'
spec = importlib.util.spec_from_file_location('legacy_coverage_under_test', SOURCE)
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


class LegacyCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bodies = {name: (ROOT / ref['path']).read_bytes() for name, ref in legacy.EVIDENCE.items()}
        cls.manifest = json.loads(cls.bodies['graph_manifest'])

    def setUp(self):
        self.graph = SimpleNamespace(**copy.deepcopy(self.manifest['metadata']))
        self.proof = {'schema_version': 2, 'kind': legacy.KIND,
                      'roles': {name: name for name in legacy.EVIDENCE}}

    def verify(self, bodies=None):
        source = self.bodies if bodies is None else bodies
        return legacy.verify_legacy_coverage(self.proof, self.graph,
                                            legacy.EVIDENCE['graph_manifest']['sha256'], source.__getitem__)

    def test_genuine_failed_parent_complete_component(self):
        reads = []
        def read(name):
            reads.append(name)
            return self.bodies[name]
        result = legacy.verify_legacy_coverage(self.proof, self.graph,
                                              legacy.EVIDENCE['graph_manifest']['sha256'], read)
        self.assertEqual(result['parent_status'], 'failed')
        self.assertEqual(result['graph_cell_status'], 'complete')
        self.assertEqual(result['member_count'], 7)
        self.assertEqual(set(reads), set(legacy.EVIDENCE))
        self.assertEqual(len(reads), 19)
        self.assertNotIn('plan_sha256', result)

    def test_every_registered_body_is_immutable(self):
        for name in self.bodies:
            with self.subTest(role=name):
                bodies = dict(self.bodies); bodies[name] += b' '
                with self.assertRaisesRegex(ValueError, 'body differs'):
                    self.verify(bodies)

    def test_genuine_schema_mutations_refused(self):
        mutations = {
            'terminal': lambda v: v.update(status='complete'),
            'cell': lambda v: v.update(worker_exit_code=1),
            'claim': lambda v: v.update(source='0' * 40),
            'source_index': lambda v: v['weeks']['2022-06-13']['members'][0].update(end_utc='2022-06-15T00:00:00Z'),
            'result': lambda v: v['details'].update(rows=7581092),
            'artifact_index': lambda v: v.clear(),
            'cell_ledger': lambda v: v.clear(),
            'intent': lambda v: v['bindings'].clear(),
            'graph_manifest': lambda v: v['metadata'].update(graph_config_hash='0' * 64),
        }
        for name, change in mutations.items():
            with self.subTest(role=name):
                v = json.loads(self.bodies[name]); change(v)
                bodies = dict(self.bodies); bodies[name] = json.dumps(v).encode()
                with self.assertRaises(ValueError): self.verify(bodies)

    def test_graph_and_manifest_joins_refused(self):
        for field, bad in [('raw_count', 0), ('asset', 'BTC'), ('start_utc', '2022-06-06T00:00:00Z'),
                           ('end_utc', '2022-06-19T00:00:00Z'), ('source_hashes', []),
                           ('graph_config_hash', '0' * 64), ('exclusion_counts', {})]:
            with self.subTest(field=field):
                self.setUp(); setattr(self.graph, field, bad)
                with self.assertRaises(ValueError): self.verify()
        with self.assertRaises(ValueError):
            legacy.verify_legacy_coverage(self.proof, self.graph, '0' * 64, self.bodies.__getitem__)

    def test_role_and_schema_mismatch(self):
        for change in [lambda p: p.update(schema_version=1), lambda p: p.update(extra=True),
                       lambda p: p['roles'].pop('terminal'),
                       lambda p: p['roles'].update(terminal='claim'),
                       lambda p: p['roles'].update(extra='extra')]:
            self.setUp(); change(self.proof)
            with self.assertRaises(ValueError): self.verify()


if __name__ == '__main__':
    unittest.main()
