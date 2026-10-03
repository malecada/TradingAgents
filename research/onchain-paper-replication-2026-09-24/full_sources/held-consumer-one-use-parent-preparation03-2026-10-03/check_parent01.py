"""Qualified pure/owned-IO controls; never a native/Run/Owner stand-in."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('parent_candidate', Path(__file__).with_name('launch_success01.py'))
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)

class Controls(unittest.TestCase):
    def test_flat_bootstrap_and_real_link_refusals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'source.py').write_bytes(b'opaque source')
            expected = hashlib.sha256(b'opaque source').hexdigest()
            self.assertEqual(parent.bootstrap(root, 'source.py', expected), b'opaque source')
            (root/'symlink.py').symlink_to('source.py')
            with self.assertRaises(ValueError): parent.bootstrap(root, 'symlink.py', expected)
            os.link(root/'source.py', root/'hard.py')
            with self.assertRaises(ValueError): parent.bootstrap(root, 'hard.py', expected)
            with self.assertRaises(ValueError): parent.bootstrap(root, '../source.py', expected)

    def test_bootstrap_first_fatal_and_two_actual_closes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'source.py').write_bytes(b'abc')
            actual_close = os.close; closed = []; original = MemoryError('original read')
            def close(fd):
                actual_close(fd); closed.append(fd)
                raise OSError('after real close')
            with patch.object(parent.os, 'read', side_effect=original), patch.object(parent.os, 'close', side_effect=close):
                with self.assertRaises(MemoryError) as observed:
                    parent.bootstrap(root, 'source.py', hashlib.sha256(b'abc').hexdigest())
            self.assertIs(observed.exception, original)
            self.assertEqual(len(closed), 2); self.assertEqual(len(set(closed)), 2)

    def test_bootstrap_growth_and_bad_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root/'source.py'; path.write_bytes(b'abc')
            original_read = os.read; grown = False
            def read(fd, extent):
                nonlocal grown
                if not grown:
                    grown = True
                    with path.open('ab') as stream: stream.write(b'd')
                return original_read(fd, extent)
            with patch.object(parent.os, 'read', side_effect=read):
                with self.assertRaises(ValueError): parent.bootstrap(root, 'source.py', '0'*64)
            with self.assertRaises(ValueError): parent.bootstrap(root, 'source.py', '0'*64)

    def test_duplicate_json_nonfinite_and_contract_extent(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'):
            with self.assertRaises(ValueError): parent.parse(raw)
        release = {'source': 'one', 'release_review_sha256':None,
                   'external_capsule_recovery_sha256':None, 'external_recovery_review_sha256':None}
        baseline = parent.contract(release)
        release['release_review_sha256'] = '0'*64
        self.assertEqual(parent.contract(release), baseline)
        release['source'] = 'two'
        self.assertNotEqual(parent.contract(release), baseline)

    def test_first_fatal_and_every_independent_action(self):
        original = MemoryError('first'); actions = []
        def action(number):
            actions.append(number)
            if number == 0: raise SystemExit('later')
            raise OSError('later close')
        with self.assertRaises(MemoryError) as caught:
            parent.cleanup([lambda:action(0), lambda:action(1), lambda:action(2)], original)
        self.assertIs(caught.exception, original); self.assertEqual(actions, [0,1,2])
        with self.assertRaises(KeyboardInterrupt):
            parent.cleanup([lambda:(_ for _ in ()).throw(KeyboardInterrupt())], ValueError())

    def test_actual_child_termination_and_reap(self):
        child = subprocess.Popen([sys.executable, '-B', '-c', 'import time; time.sleep(30)'],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
        tick = parent.ticks(child.pid)
        try:
            parent.reap_controller(child, tick)
            self.assertIsNotNone(child.returncode)
            self.assertFalse(Path('/proc', str(child.pid)).exists())
        finally:
            if child.poll() is None: child.kill(); child.wait(timeout=5)

    def test_poll_failure_does_not_skip_reap(self):
        calls = []
        class QualifiedProcess:
            pid = 0
            def poll(self): calls.append('poll'); raise MemoryError('poll original')
            def wait(self, timeout): calls.append('wait'); return 0
        with self.assertRaises(MemoryError): parent.reap_controller(QualifiedProcess(), None)
        self.assertEqual(calls, ['poll', 'wait'])

    def test_dangling_reserved_namespace_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/'cap'; root.mkdir()
            exterior = Path(directory)/'parent'; exterior.mkdir()
            (root/'research_runs').mkdir()
            (root/'research_runs'/parent.IDENTITY).symlink_to('missing')
            with self.assertRaises(ValueError): parent.dedup(root, exterior)

    def test_default_candidate_origin_cannot_release_or_reserve(self):
        with self.assertRaises(ValueError):
            parent.prepared(Path('/missing/request.json'), '0'*64)
        self.assertFalse(any(x in sys.modules for x in ('numpy','torch','scipy')))

if __name__ == '__main__':
    unittest.main()
