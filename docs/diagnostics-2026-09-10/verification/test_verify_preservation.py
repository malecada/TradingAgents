"""Synthetic rejection tests for the bounded diagnostics preservation fence."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).with_name('verify_preservation.py')


def implementation():
    if not MODULE.exists():
        raise AssertionError('diagnostic preservation verifier is not implemented')
    spec = importlib.util.spec_from_file_location('diagnostic_preservation_tests', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreservationTests(unittest.TestCase):
    def test_old_gate_edit_rejected(self):
        m = implementation()
        with self.assertRaisesRegex(ValueError, 'prior gate'):
            m.gate_additions({'old': {'n': 4}}, {'old': {'n': 3}})

    def test_only_two_declared_additions_allowed(self):
        m = implementation()
        after = {'old': {}, **{key: {'n': i} for i, key in enumerate(m.KEYS)}}
        m.gate_additions({'old': {}}, after, {key: after[key] for key in m.KEYS})
        with self.assertRaisesRegex(ValueError, 'gate keys'):
            m.gate_additions({'old': {}}, {**after, 'extra': {}})

    def test_missing_or_changed_registered_gate_rejected(self):
        m = implementation()
        expected = {key: {'n': 1} for key in m.KEYS}
        for after in ({'old': {}}, {'old': {}, **{key: {'n': 2} for key in m.KEYS}}):
            with self.assertRaisesRegex(ValueError, 'registered gate'):
                m.gate_additions({'old': {}}, after, expected)

    def test_prefix_preservation_is_not_semantic_rewrite(self):
        m = implementation()
        self.assertEqual(m.append_suffix(b'old\n', b'old\nnew\n', 'notes'), b'new\n')
        with self.assertRaisesRegex(ValueError, 'prefix'):
            m.append_suffix(b'old\n', b'OLD\nnew\n', 'notes')

    def test_any_financial_ledger_append_rejected(self):
        m = implementation()
        before = b'{"trial_id":"old"}\n'
        with self.assertRaisesRegex(ValueError, 'financial ledger'):
            m.require_ledger(before + b'{"trial_id":"new"}\n', before)
        self.assertEqual(m.require_ledger(before, before)['rows'], 1)

    def test_receipt_union_rejects_conflicting_identity(self):
        m = implementation()
        first = [{'path': '/a', 'sha256': 'one', 'bytes': 1}]
        self.assertEqual(len(m.merge_receipts(first, {'/b': 'two'})), 2)
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            m.merge_receipts(first, {'/a': 'two'})

    def test_input_escape_and_symlink_rejected(self):
        m = implementation()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'real').write_bytes(b'abc')
            (root / 'alias').symlink_to(root / 'real')
            for name in ('../escape', '/absolute', 'alias', 'keys/secret'):
                with self.assertRaises(ValueError):
                    m.safe_local(root, name)

    def test_original_file_mutation_and_deletion_rejected(self):
        m = implementation()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'original').write_bytes(b'abc')
            expected = {'original': m.inspect_file(root / 'original')}
            m.check_tree(root, expected, set())
            (root / 'original').write_bytes(b'abd')
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                m.check_tree(root, expected, set())
            (root / 'original').unlink()
            with self.assertRaises(FileNotFoundError):
                m.check_tree(root, expected, set())

    def test_manifest_write_is_exclusive(self):
        m = implementation()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            m.write_new(path, {'original': True})
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                m.write_new(path, {'original': False})
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
