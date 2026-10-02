"""Bounded stdlib close-order sentinels; extracts the exact candidate function."""
import ast
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('candidate03.py')
if len(sys.argv) > 1 and sys.argv[1].startswith('--source='):
    SOURCE = Path(sys.argv.pop(1).split('=', 1)[1]).resolve()

class CleanupFailure(BaseException):
    pass

class CustomFatal(BaseException):
    pass

class CloseOrder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodes = [node for node in ast.parse(SOURCE.read_text()).body
                 if isinstance(node, ast.FunctionDef) and node.name == '_close_owned']
        assert len(nodes) == 1
        namespace = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), namespace)
        cls.close_owned = staticmethod(namespace['_close_owned'])

    def invoke(self, primary, errors):
        calls = []
        def close(fd):
            calls.append(fd)
            error = errors.get(fd)
            if error is not None:
                raise error
        def run():
            if primary is None:
                self.close_owned((101, 102), SimpleNamespace(CleanupFailure=CleanupFailure))
            else:
                try:
                    raise primary
                finally:
                    self.close_owned((101, 102), SimpleNamespace(CleanupFailure=CleanupFailure))
        escaped = None
        with patch.object(os, 'close', close):
            try:
                run()
            except BaseException as error:
                escaped = error
        self.assertEqual(calls, [101, 102])
        return escaped

    def test_ordinary_child_then_first_parent_fatal_identity_and_cause(self):
        for fatal in (MemoryError('parent'), SystemExit('parent'), CustomFatal('parent')):
            ordinary = OSError('child')
            error = self.invoke(None, {101: ordinary, 102: fatal})
            self.assertIs(error, fatal)
            self.assertIs(error.__cause__, ordinary)

    def test_body_and_child_ordinary_then_parent_fatal_preserves_both_prior_objects(self):
        for fatal in (MemoryError('parent'), SystemExit('parent'), CustomFatal('parent')):
            body = ValueError('body')
            child = OSError('child')
            error = self.invoke(body, {101: child, 102: fatal})
            self.assertIs(error, fatal)
            self.assertIsInstance(error.__cause__, ExceptionGroup)
            self.assertEqual(error.__cause__.exceptions, (body, child))

    def test_first_true_child_fatal_survives_later_fatal(self):
        first = SystemExit('first')
        later = MemoryError('later')
        self.assertIs(self.invoke(None, {101: first, 102: later}), first)

    def test_body_fatal_survives_all_closes(self):
        body = MemoryError('body')
        error = self.invoke(body, {101: OSError('child'), 102: SystemExit('parent')})
        self.assertIs(error, body)
        self.assertEqual(len(error.__notes__), 2)

    def test_ordinary_only_uncertainty_is_terminal_wrapper_with_all_evidence(self):
        body = ValueError('body')
        child = OSError('child')
        parent = OSError('parent')
        error = self.invoke(body, {101: child, 102: parent})
        self.assertIs(type(error), CleanupFailure)
        self.assertIsInstance(error.__cause__, ExceptionGroup)
        self.assertEqual(error.__cause__.exceptions, (body, child, parent))

    def test_existing_fatal_cause_survives_new_prior_evidence(self):
        fatal = SystemExit('parent')
        existing = ValueError('existing causal evidence')
        fatal.__cause__ = existing
        child = OSError('child')
        error = self.invoke(None, {101: child, 102: fatal})
        self.assertIs(error, fatal)
        self.assertIsInstance(error.__cause__, BaseExceptionGroup)
        self.assertEqual(error.__cause__.exceptions, (child, existing))

    def test_no_cleanup_error_preserves_body_or_success(self):
        body = ValueError('body')
        self.assertIs(self.invoke(body, {}), body)
        self.assertIsNone(self.invoke(None, {}))

if __name__ == '__main__':
    unittest.main()
