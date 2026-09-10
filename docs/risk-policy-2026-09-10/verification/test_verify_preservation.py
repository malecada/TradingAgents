"""Synthetic preservation failures; no market data or strategy execution."""
import importlib.util
import copy
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).with_name('verify_preservation.py')


def implementation():
    if not MODULE.exists():
        raise AssertionError('risk-policy preservation verifier is not implemented')
    spec = importlib.util.spec_from_file_location('risk_policy_preservation_test', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreservationTests(unittest.TestCase):
    def nested_fixture(self):
        m = implementation()
        cells = [{'id': f'config{i//4}|A{i%4}', 'configuration': {'name': f'config{i//4}'},
                  'arm': f'A{i%4}', 'sizing': 'saved', 'reentry': 'immediate'} for i in range(72)]
        gate = {'cells': cells, 'expected_identities': 72,
                'variants': ['primary', 'zero_execution', 'double_execution', 'zero_funding'],
                'coins': ['bitcoin', 'ethereum']}
        def item(): return {'status': 'complete'}
        rows = [{'experiment': m.KEY, 'cell': c['id'],
                 'config': {k: c[k] for k in ('configuration','arm','sizing','reentry')},
                 'metrics': {'status': 'complete', 'variants': {
                     v: {'status': 'complete', 'sleeves': {coin:item() for coin in gate['coins']},
                         'index': item()} for v in gate['variants']}, 'log_shadow': item()}}
                for c in cells]
        return m, gate, rows

    def test_exact_ordered_nested_ledger_denominators(self):
        m, gate, rows = self.nested_fixture()
        report = m.check_ledger_cells(rows, gate)
        self.assertEqual(report['identities'], 72)
        self.assertEqual(report['index_statuses'], {'complete': 288, 'unavailable': 0})
        self.assertEqual(report['sleeve_statuses'], {'complete': 576, 'unavailable': 0})
        self.assertEqual(report['shadow_statuses'], {'complete': 72, 'unavailable': 0})

    def test_wrong_cell_order_config_or_experiment_rejected(self):
        m, gate, rows = self.nested_fixture()
        for mutation in ('order','duplicate','config','experiment'):
            bad = copy.deepcopy(rows)
            if mutation == 'order': bad[0], bad[1] = bad[1], bad[0]
            if mutation == 'duplicate': bad[1] = bad[0]
            if mutation == 'config': bad[0]['config']['sizing'] = 'unknown'
            if mutation == 'experiment': bad[0]['experiment'] = 'wrong'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                m.check_ledger_cells(bad, gate)

    def test_missing_variant_sleeve_index_shadow_and_unknown_status_rejected(self):
        m, gate, rows = self.nested_fixture()
        for mutation in ('variant','coin','index','shadow','status','extra'):
            bad = copy.deepcopy(rows); metrics = bad[0]['metrics']
            if mutation == 'variant': del metrics['variants']['primary']
            if mutation == 'coin': del metrics['variants']['primary']['sleeves']['ethereum']
            if mutation == 'index': del metrics['variants']['primary']['index']
            if mutation == 'shadow': del metrics['log_shadow']
            if mutation == 'status': metrics['status'] = 'pending'
            if mutation == 'extra': metrics['variants']['surprise'] = {}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                m.check_ledger_cells(bad, gate)

    def test_unavailable_requires_reason_and_cannot_be_promoted_by_parent(self):
        m, gate, rows = self.nested_fixture()
        rows[0]['metrics']['variants']['primary']['sleeves']['bitcoin'] = {
            'status': 'unavailable', 'reason': 'synthetic missing data'}
        with self.assertRaises(ValueError): m.check_ledger_cells(rows, gate)
        rows[0]['metrics']['status'] = 'unavailable'; rows[0]['metrics']['reason'] = 'missing sleeve'
        rows[0]['metrics']['variants']['primary']['status'] = 'unavailable'
        rows[0]['metrics']['variants']['primary']['reason'] = 'missing sleeve'
        rows[0]['metrics']['variants']['primary']['index'] = {
            'status': 'unavailable', 'reason': 'missing sleeve'}
        self.assertEqual(m.check_ledger_cells(rows, gate)['cell_statuses']['unavailable'], 1)
        rows[0]['metrics']['variants']['primary']['sleeves']['bitcoin'].pop('reason')
        with self.assertRaises(ValueError): m.check_ledger_cells(rows, gate)

    def test_only_exact_single_gate_addition_allowed(self):
        m = implementation(); old = {'old': {'n': 4}}; new = {'n': 72}
        m.gate_additions(old, old | {m.KEY: new}, new)
        for after in ({'old': {'n': 3}, m.KEY: new}, old | {'extra': {}},
                      old, old | {m.KEY: {'n': 71}}):
            with self.assertRaises(ValueError): m.gate_additions(old, after, new)

    def test_append_only_means_exact_bytes(self):
        m = implementation()
        self.assertEqual(m.append_suffix(b'old\n', b'old\nnew\n', 'notes'), b'new\n')
        with self.assertRaisesRegex(ValueError, 'prefix'):
            m.append_suffix(b'old\n', b'OLD\nnew\n', 'notes')

    def test_engine_original_archive_required_even_when_live_engine_changes(self):
        m = implementation()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); engine = root/m.ENGINE; archive = root/m.ENGINE_ARCHIVE
            engine.parent.mkdir(parents=True); archive.parent.mkdir(parents=True)
            engine.write_bytes(b'old source'); archive.write_bytes(b'old source')
            original = b'old source'
            report = m.check_engine(root, original)
            self.assertFalse(report['changed'])
            engine.write_bytes(b'authorized hook')
            self.assertTrue(m.check_engine(root, original)['changed'])
            archive.write_bytes(b'new source masquerading as old')
            with self.assertRaisesRegex(ValueError, 'archive'):
                m.check_engine(root, original)
            archive.unlink()
            with self.assertRaises(FileNotFoundError): m.check_engine(root, original)

    def test_other_original_source_and_evidence_cannot_change_or_disappear(self):
        m = implementation()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); p = root/'source.py'; p.write_bytes(b'original')
            expected = {'source.py': m.inspect_file(p)}
            m.check_tree(root, expected, set())
            p.write_bytes(b'changed')
            with self.assertRaises(ValueError): m.check_tree(root, expected, set())
            p.unlink()
            with self.assertRaises(FileNotFoundError): m.check_tree(root, expected, set())

    def test_local_paths_reject_escapes_secrets_and_symlinks(self):
        m = implementation()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'real').write_bytes(b'bytes')
            (root/'alias').symlink_to(root/'real')
            for name in ('../escape', '/absolute', 'keys/secret', '.env', 'alias'):
                with self.assertRaises(ValueError): m.safe_local(root, name)

    def test_baseline_phase_requires_unchanged_financial_ledger(self):
        m = implementation(); before = b'{"old":1}\n'
        report = m.ledger_prefix(before, before, phase='baseline')
        self.assertEqual(report['new_rows'], 0)
        for after in (b'{"old":2}\n', before+b'{}\n'):
            with self.assertRaises(ValueError): m.ledger_prefix(before, after, phase='baseline')

    def test_final_phase_preserves_prefix_and_requires_exact_72_rows(self):
        m = implementation(); before = b'{"old":1}\n'
        suffix = b''.join(json.dumps({'cell': str(i)}).encode()+b'\n' for i in range(72))
        report = m.ledger_prefix(before, before+suffix, phase='final')
        self.assertEqual(report['new_rows'], 72)
        for after in (before, before+suffix+b'{}\n', before+suffix.splitlines(keepends=True)[0], b'changed\n'+suffix):
            with self.assertRaises(ValueError): m.ledger_prefix(before, after, phase='final')

    def test_external_receipt_union_never_accepts_conflicting_identity(self):
        m = implementation()
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            m.merge_receipts([{'path':'/a','sha256':'one'}], {'/a':'two'})

    def test_new_reports_cannot_overwrite_previous_report(self):
        m = implementation()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'report.json'
            m.write_new(path, {'first': True}); before = path.read_bytes()
            with self.assertRaises(FileExistsError): m.write_new(path, {'second': True})
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__': unittest.main()
