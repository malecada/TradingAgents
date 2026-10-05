"""Actual guarded_run startup/finalization, synthetic disk samples; never dispatch."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('disk_telemetry_candidate', HERE/'resources.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class DiskMinimumTests(unittest.TestCase):
    def test_rebound_retains_each_path_minimum_in_live_and_final(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            root = Path(td); other = root/'other'; other.mkdir(); receipt = root/'receipt'
            snapshots = []; atomic = guard._atomic
            def capture(path, state):
                snapshots.append(json.loads(json.dumps(state)))
                atomic(path, state)
            with patch.object(guard.shutil, 'disk_usage', side_effect=[SimpleNamespace(free=n) for n in [100,200,60,170,90,150]]), \
                 patch.object(guard, 'mem_available', side_effect=[0,0,RuntimeError('synthetic stop after rebound')]), \
                 patch.object(guard.time, 'sleep'), \
                 patch.object(guard.subprocess, 'run', side_effect=AssertionError('native dispatch forbidden')), \
                 patch.object(guard, '_atomic', side_effect=capture):
                result = guard.guarded_run(['never-dispatch'], cwd=root, receipt_dir=receipt,
                                           disk_paths=[root,other], disk_floor_bytes=50, wait_seconds=100)
            expected = {str(root):60, str(other):150}
            self.assertEqual(result['minimum_sampled_disk_free_bytes'], expected)
            self.assertEqual(result['disk_free_bytes'], {str(root):90,str(other):150})
            self.assertEqual(snapshots[0]['minimum_sampled_disk_free_bytes'], {str(root):100,str(other):200})
            for name in ['live.json','final.json']:
                state = json.loads((receipt/name).read_bytes())
                self.assertEqual(state['minimum_sampled_disk_free_bytes'], expected)
                self.assertEqual(state['phase'], 'failed')
            self.assertFalse((receipt/'release.json').exists())

    def test_floor_breach_sample_is_retained_before_refusal(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            root=Path(td)
            with patch.object(guard.shutil, 'disk_usage', return_value=SimpleNamespace(free=40)), \
                 patch.object(guard.subprocess, 'run', side_effect=AssertionError('native dispatch forbidden')):
                result=guard.guarded_run(['never-dispatch'],cwd=root,receipt_dir=root/'r',disk_paths=[root],disk_floor_bytes=50)
            self.assertEqual(result['minimum_sampled_disk_free_bytes'],{str(root):40})
            self.assertIn('disk floor breached',result['limit_reason'])

    def test_unobserved_paths_are_empty_not_zero(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            root=Path(td)
            with patch.object(guard,'mem_available',return_value=0), \
                 patch.object(guard.subprocess,'run',side_effect=AssertionError('native dispatch forbidden')):
                result=guard.guarded_run(['never-dispatch'],cwd=root,receipt_dir=root/'r',wait_seconds=0)
            self.assertEqual(result['minimum_sampled_disk_free_bytes'],{})


if __name__=='__main__':unittest.main()
