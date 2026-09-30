"""Three existing synthetic subprocess contracts against the isolated candidate."""
import importlib.util
from pathlib import Path
import sys
import unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_guard',HERE/'resource_guard.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class LiveGuardContracts(unittest.TestCase):
    def test_affinity_and_address_space_policy(self):
        result=m.run_guard([sys.executable,'-c','import os,resource; assert len(os.sched_getaffinity(0))<=2; assert resource.getrlimit(resource.RLIMIT_AS)[0]==resource.RLIM_INFINITY'],wall_seconds=10)
        self.assertEqual(result['child_exit_code'],0);self.assertIsNone(result['limit_reason'])

    def test_memory_and_wall_refusals(self):
        result=m.run_guard([sys.executable,'-c','import time; data=bytearray(80*1024**2); time.sleep(5)'],rss_limit_bytes=32*1024**2,wall_seconds=10)
        self.assertEqual(result['limit_reason'],'sampled aggregate RSS limit exceeded')
        result=m.run_guard([sys.executable,'-c','import time; time.sleep(5)'],wall_seconds=.1)
        self.assertEqual(result['limit_reason'],'wall-clock limit exceeded')

    def test_launch_failure_remains_explicit_unknown(self):
        result=m.run_guard(['/nonexistent/research-synthetic-executable'])
        self.assertIsNone(result['child_exit_code']);self.assertIsNone(result['peak_sampled_tree_rss_bytes'])
        self.assertTrue(result['limit_reason'].startswith('launch/setup failed:'))
        self.assertFalse(result['retry'])

if __name__=='__main__':unittest.main(verbosity=2)
