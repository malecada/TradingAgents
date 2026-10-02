"""Finite scheduling checks with injected time/RAM; no actual workload or sleep."""
import argparse
from importlib import util
import json
from pathlib import Path
import unittest

parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--policy',type=Path,required=True);args=parser.parse_args()
spec=util.spec_from_file_location('readiness_candidate_test',args.source)
module=util.module_from_spec(spec);spec.loader.exec_module(module)
policy=json.loads(args.policy.read_bytes())


class Readiness(unittest.TestCase):
    def observe(self,available):
        now=[0.0]
        def advance(seconds):now[0]+=seconds
        return module.observe(policy,mem_available=lambda:available,clock=lambda:now[0],sleep=advance),now[0]

    def test_native_startup_minimum_passes_complete_window(self):
        report,now=self.observe(7247757312)
        self.assertEqual(report['status'],'ready')
        self.assertEqual(len(report['observations']),16)
        self.assertEqual(report['elapsed_seconds'],30.0)
        self.assertTrue(module.fresh(report,policy,now))
        self.assertFalse(module.fresh(report,policy,now+1.01))

    def test_below_existing_hard_minimum_refuses(self):
        report,_=self.observe(7247757311)
        self.assertEqual(report['status'],'deferred')
        self.assertEqual(len(report['observations']),1)
        self.assertFalse(policy['failed_observation_reserves_namespace'])
        self.assertFalse(policy['automatic_launch_retry'])

    def test_host_reserve_window_and_policy_cannot_change(self):
        self.assertEqual(policy['hard_guard_reserve_bytes_unchanged'],3221225472)
        self.assertEqual(policy['hard_guard_start_reserve_bytes_unchanged'],7247757312)
        self.assertEqual(policy['observation_count'],16)
        self.assertEqual(policy['observation_interval_seconds'],2)
        for key,value in [('minimum_available_bytes',True),('hard_guard_reserve_bytes_unchanged',3221225471),('observation_count',1)]:
            with self.assertRaises(ValueError):module.validate({**policy,key:value})


if __name__=='__main__':unittest.main(argv=['test_readiness04'],verbosity=2)
