"""Deterministic synthetic procfs transitions, no empirical jobs."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_guard',HERE/'resource_guard.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ExitRaceTests(unittest.TestCase):
    def sample(self,statuses):
        values=iter(statuses)
        def read(path,*args,**kwargs):
            if str(path).endswith('/children'):return ''
            value=next(values)
            if isinstance(value,Exception):raise value
            return value
        with patch.object(m.Path,'read_text',read):return m.tree_rss(123)

    def test_exit_becomes_zombie_after_status_without_rss(self):
        self.assertEqual(self.sample(['State:\tR (running)\n','State:\tZ (zombie)\n']),0)

    def test_exit_disappears_after_status_without_rss(self):
        self.assertEqual(self.sample(['State:\tR (running)\n',FileNotFoundError()]),0)

    def test_dead_state_without_rss_is_terminal(self):
        self.assertEqual(self.sample(['State:\tX (dead)\n']),0)

    def test_second_status_has_real_rss(self):
        self.assertEqual(self.sample(['State:\tR (running)\n','State:\tR (running)\nVmRSS:\t123 kB\n']),123*1024)

    def test_persistent_live_missing_rss_still_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,'live process has no VmRSS'):
            self.sample(['State:\tR (running)\n','State:\tR (running)\n'])

    def test_unknown_state_and_malformed_rss_are_not_zero(self):
        with self.assertRaises(RuntimeError):self.sample(['State:\t?\n','State:\t?\n'])
        with self.assertRaises(ValueError):self.sample(['State:\tR\nVmRSS:\tbad kB\n'])

if __name__=='__main__':unittest.main(verbosity=2)
