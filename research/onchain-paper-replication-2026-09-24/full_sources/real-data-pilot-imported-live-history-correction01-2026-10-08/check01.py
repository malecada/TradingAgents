"""Focused source routing fixtures; no numerical or genuine authority claim."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / 'tradingagents/research/onchain_replication'


def live(path):
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Lease')
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_live')
    env = {'__package__': 'fixture_package', 'require': lambda ok, why: None if ok else fail(why)}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), env)
    return env['_live']


def fail(why):
    raise ValueError(why)


class Checks(unittest.TestCase):
    def test_exact_single_keyword_inverse(self):
        change = json.loads((HERE / 'SOURCE_DELTA01.json').read_text())
        original = (SOURCE / 'imported_authority_lease.py').read_text()
        candidate = (HERE / 'imported_authority_lease.py').read_text()
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), change['baseline']['sha256'])
        self.assertEqual(candidate.replace(change['exact_inverse']['from'], change['exact_inverse']['to']), original)

    def test_identity_and_owner_or_stage_lease_still_precede_current_check(self):
        for active in (False, True):
            calls = []
            class Stage:
                def lease(self): calls.append('stage')
            owner = types.SimpleNamespace(active=Stage() if active else None, lease=lambda: calls.append('owner'))
            compact = types.ModuleType('fixture_package.compact_owner')
            compact.Stage = Stage
            compact.verify_current = lambda selected, **kw: calls.append(('current', selected is owner, kw))
            package = types.ModuleType('fixture_package'); package.compact_owner = compact
            obj = types.SimpleNamespace(owner=owner, _identity=lambda: calls.append('identity'))
            with patch.dict(sys.modules, {'fixture_package': package, 'fixture_package.compact_owner': compact}):
                live(HERE / 'imported_authority_lease.py')(obj)
            self.assertEqual(calls, ['identity', 'stage' if active else 'owner', ('current', True, {'sampled_archive_evidence': True})])

    def test_foreign_stage_refused_before_current_check(self):
        calls = []
        compact = types.ModuleType('fixture_package.compact_owner'); compact.Stage = type('Stage', (), {})
        compact.verify_current = lambda *a, **k: calls.append('current')
        package = types.ModuleType('fixture_package'); package.compact_owner = compact
        obj = types.SimpleNamespace(owner=types.SimpleNamespace(active=object()), _identity=lambda: None)
        with patch.dict(sys.modules, {'fixture_package': package, 'fixture_package.compact_owner': compact}):
            with self.assertRaisesRegex(ValueError, 'actual active MCM stage'):
                live(HERE / 'imported_authority_lease.py')(obj)
        self.assertEqual(calls, [])

    def test_full_boundary_default_owner_evidence_unchanged(self):
        tree = ast.parse((HERE / 'imported_authority_lease.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Lease')
        full = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_full')
        self.assertTrue(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'check' for n in ast.walk(full)))
        original = ast.parse((SOURCE / 'original_import_stage.py').read_text())
        execution = next(n for n in original.body if isinstance(n, ast.ClassDef) and n.name == 'ImportedExecution')
        check = next(n for n in execution.body if isinstance(n, ast.FunctionDef) and n.name == 'check')
        calls = [n for n in ast.walk(check) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'verify_current']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].keywords, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
