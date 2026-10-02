"""Small real-filesystem checks; no study inputs or registered execution."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from tradingagents.research.onchain_replication import workflow_storage as m

class Checks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.limits={'max_allocated_bytes':1024**2,'max_logical_bytes':1024**2,
            'max_entries':100,'max_depth':8,'max_scan_seconds':1}
    def tearDown(self):self.temp.cleanup()
    def pair(self,a='a',b='b'):
        (self.root/a).write_bytes(b'payload');os.link(self.root/a,self.root/b)
    def watch(self):return m.StorageWatch(self.root,self.limits)
    def test_transient_link_requires_fresh_complete_single_link_scan(self):
        self.pair();watch=self.watch()
        with mock.patch.object(m.time,'sleep',side_effect=lambda _: (self.root/'b').unlink()):
            result=watch.check()
        self.assertEqual(result['scan_attempts'],2)
        self.assertEqual(result['regular_files'],1)
        self.assertEqual(result['logical_file_bytes'],7)
        self.assertEqual(len(result['hardlink_observations']),1)
        self.assertEqual(result['hardlink_observations'][0]['links'],2)
        self.assertEqual(result['aggregate_entry_visit_bound'],300)
    def test_two_transient_links_need_third_fresh_scan(self):
        self.pair();self.pair('c','d');watch=self.watch();remove=iter(('b','d'))
        with mock.patch.object(m.time,'sleep',side_effect=lambda _: (self.root/next(remove)).unlink()):
            result=watch.check()
        self.assertEqual(result['scan_attempts'],3)
        self.assertEqual(result['regular_files'],2)
        self.assertEqual(len(result['hardlink_observations']),2)
    def test_persistent_link_refused_with_exact_bounded_evidence(self):
        self.pair();watch=self.watch()
        with mock.patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(m.HardlinkObservation) as caught:watch.check()
        self.assertEqual(sleep.call_count,2)
        self.assertEqual(len(caught.exception.history),3)
        info=caught.exception.evidence;self.assertIn(info['relative_path'],('a','b'))
        self.assertEqual(info['inode'],(self.root/'a').stat().st_ino)
        self.assertEqual(info['links'],2)
        self.assertFalse(info['path_truncated'])
    def test_one_shared_deadline_includes_wait(self):
        self.pair();watch=self.watch();now=[0.0]
        def advance(_):now[0]=1.01
        with mock.patch.object(m.time,'monotonic',side_effect=lambda:now[0]),mock.patch.object(m.time,'sleep',side_effect=advance),mock.patch.object(watch,'_scan',wraps=watch._scan) as scan:
            with self.assertRaises(m.StorageLimit) as caught:watch.check()
        self.assertEqual(caught.exception.reason,'time');self.assertEqual(scan.call_count,1)
    def test_root_replacement_during_retry_refused(self):
        self.pair();watch=self.watch();moved=self.root.with_name(self.root.name+'-moved')
        def replace(_):self.root.rename(moved);self.root.mkdir()
        try:
            with mock.patch.object(m.time,'sleep',side_effect=replace):
                with self.assertRaisesRegex(ValueError,'root replaced'):watch.check()
        finally:
            if moved.exists():
                import shutil
                shutil.rmtree(moved)
    def test_symlink_never_retried(self):
        (self.root/'bad').symlink_to('/unopened')
        with mock.patch.object(m.time,'sleep') as sleep:
            with self.assertRaisesRegex(ValueError,'symbolic link refused'):self.watch().check()
        self.assertEqual(sleep.call_count,0)
    def test_sparse_logical_breach_never_retried(self):
        with (self.root/'sparse').open('wb') as f:f.truncate(2*1024**2)
        with mock.patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(m.StorageLimit) as caught:self.watch().check()
        self.assertEqual(caught.exception.reason,'logical');self.assertEqual(sleep.call_count,0)
    def test_entry_breach_never_retried(self):
        self.limits['max_entries']=1
        for name in ('a','b'):(self.root/name).write_bytes(b'x')
        with mock.patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(m.StorageLimit) as caught:self.watch().check()
        self.assertEqual(caught.exception.reason,'entries');self.assertEqual(sleep.call_count,0)
    def test_uncertain_close_refuses_retry_and_closes_real_descriptor(self):
        self.pair();watch=self.watch();real=m.os.close;raised=[False]
        def uncertain(fd):
            real(fd)
            if not raised[0]:raised[0]=True;raise OSError('injected close uncertainty')
        with mock.patch.object(m.os,'close',side_effect=uncertain),mock.patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(m.StorageCleanupFailure):watch.check()
        self.assertEqual(sleep.call_count,0)
    def test_first_fatal_retained_when_close_uncertain(self):
        watch=self.watch();fatal=MemoryError('original fatal');real=m.os.close
        def uncertain(fd):real(fd);raise OSError('later close')
        with mock.patch.object(m.os,'fstat',side_effect=fatal),mock.patch.object(m.os,'close',side_effect=uncertain),mock.patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(MemoryError) as caught:watch.check()
        self.assertIs(caught.exception,fatal);self.assertEqual(sleep.call_count,0)
    def test_single_link_normal_scan_unchanged_accounting(self):
        (self.root/'a').write_bytes(b'123')
        result=self.watch().check()
        self.assertEqual(result['scan_attempts'],1);self.assertEqual(result['hardlink_observations'],[])
        self.assertEqual(result['logical_file_bytes'],3);self.assertEqual(result['entries'],1)
        self.assertEqual(result['allocated_bytes'],self.root.stat().st_blocks*512+(self.root/'a').stat().st_blocks*512)
    def test_link_diagnostics_bounded_with_full_path_hash(self):
        import hashlib
        self.pair();path='z'*2000;error=m.HardlinkObservation(path,(self.root/'a').stat())
        self.assertEqual(len(error.evidence['relative_path']),512)
        self.assertTrue(error.evidence['path_truncated'])
        self.assertEqual(error.evidence['path_sha256'],hashlib.sha256(os.fsencode(path)).hexdigest())
    def test_deadline_checked_after_successful_descriptor_cleanup(self):
        (self.root/'a').write_bytes(b'x');watch=self.watch();now=[0.0];real=m.os.close
        def close(fd):real(fd);now[0]=1.01
        with mock.patch.object(m.time,'monotonic',side_effect=lambda:now[0]),mock.patch.object(m.os,'close',side_effect=close):
            with self.assertRaises(m.StorageLimit) as caught:watch.check()
        self.assertEqual(caught.exception.reason,'time')
    def test_first_close_fatal_preserved(self):
        watch=self.watch();fatal=MemoryError('first fatal at close');real=m.os.close
        def close(fd):real(fd);raise fatal
        with mock.patch.object(m.os,'close',side_effect=close):
            with self.assertRaises(MemoryError) as caught:watch.check()
        self.assertIs(caught.exception,fatal)
    def test_first_iterator_body_fatal_survives_iterator_close_error(self):
        (self.root/'a').write_bytes(b'x');watch=self.watch();fatal=KeyboardInterrupt('body fatal');real=m.os.scandir
        class Iterator:
            def __init__(self,fd):self.inner=real(fd)
            def __iter__(self):return self
            def __next__(self):return next(self.inner)
            def close(self):self.inner.close();raise OSError('later iterator close')
        with mock.patch.object(m.os,'scandir',side_effect=Iterator),mock.patch.object(m.os,'stat',side_effect=fatal):
            with self.assertRaises(KeyboardInterrupt) as caught:watch.check()
        self.assertIs(caught.exception,fatal)
    def test_persistent_history_and_partial_counts_guard_serializable(self):
        import json
        self.pair();watch=self.watch()
        with mock.patch.object(m.time,'sleep'):
            with self.assertRaises(m.HardlinkObservation) as caught:watch.check()
        obs=caught.exception.observation
        self.assertEqual(len(obs['hardlink_observations']),3)
        self.assertEqual(obs['directories'],1);self.assertGreater(obs['entries'],0)
        self.assertLess(len(json.dumps(obs)),8192)
    def test_prior_link_history_survives_next_root_failure(self):
        self.pair();watch=self.watch();moved=self.root.with_name(self.root.name+'-next')
        def replace(_):self.root.rename(moved);self.root.mkdir()
        try:
            with mock.patch.object(m.time,'sleep',side_effect=replace):
                with self.assertRaises(ValueError) as caught:watch.check()
            self.assertEqual(len(caught.exception.observation['hardlink_observations']),1)
        finally:
            if moved.exists():
                import shutil
                shutil.rmtree(moved)
    def test_wait_clamped_to_remaining_common_budget(self):
        self.pair();watch=self.watch();now=[0.0];real=watch._scan;waits=[]
        def scan(begin):
            try:return real(begin)
            except m.HardlinkObservation:
                if now[0]==0:now[0]=.999
                raise
        def wait(delay):waits.append(delay);now[0]+=delay
        with mock.patch.object(m.time,'monotonic',side_effect=lambda:now[0]),mock.patch.object(watch,'_scan',side_effect=scan),mock.patch.object(m.time,'sleep',side_effect=wait):
            with self.assertRaises(m.StorageLimit):watch.check()
        self.assertEqual(len(waits),1);self.assertLessEqual(waits[0],.001000001)
    def test_quota_before_link_is_not_retried(self):
        self.pair();watch=self.watch()
        partial={'entries':101}
        with mock.patch.object(watch,'_scan',side_effect=m.StorageLimit('entries',partial)),mock.patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(m.StorageLimit) as caught:watch.check()
        self.assertEqual(caught.exception.reason,'entries');self.assertEqual(sleep.call_count,0)
    def test_quota_after_link_retains_prior_link_history(self):
        self.pair();watch=self.watch();real=watch._scan
        with self.assertRaises(m.HardlinkObservation) as first:real(m.time.monotonic())
        sequence=[first.exception,m.StorageLimit('logical',{'logical_file_bytes':2*1024**2})]
        with mock.patch.object(watch,'_scan',side_effect=sequence),mock.patch.object(m.time,'sleep') as sleep:
            with self.assertRaises(m.StorageLimit) as caught:watch.check()
        self.assertEqual(caught.exception.reason,'logical');self.assertEqual(sleep.call_count,1)
        self.assertEqual(len(caught.exception.observation['hardlink_observations']),1)
    def test_backoff_fatal_preserves_prior_history_and_partial_counts(self):
        self.pair();watch=self.watch();fatal=KeyboardInterrupt('backoff interrupted')
        with mock.patch.object(m.time,'sleep',side_effect=fatal):
            with self.assertRaises(KeyboardInterrupt) as caught:watch.check()
        self.assertIs(caught.exception,fatal)
        obs=fatal.observation;self.assertEqual(obs['directories'],1)
        self.assertEqual(len(obs['hardlink_observations']),1)
        self.assertEqual(obs['hardlink_observations'][0]['partial_counts']['directories'],1)
    def test_later_first_real_fatal_promoted_after_ordinary_iterator_cleanup(self):
        watch=self.watch();fatal=MemoryError('first real fatal');scandir=m.os.scandir;close=m.os.close
        class Iterator:
            def __init__(self,fd):self.inner=scandir(fd)
            def __iter__(self):return self
            def __next__(self):return next(self.inner)
            def close(self):self.inner.close();raise OSError('ordinary iterator close')
        def fatal_close(fd):close(fd);raise fatal
        with mock.patch.object(m.os,'scandir',side_effect=Iterator),mock.patch.object(m.os,'close',side_effect=fatal_close):
            with self.assertRaises(MemoryError) as caught:watch.check()
        self.assertIs(caught.exception,fatal)
    def test_exact_guard_capture_persists_fatal_diagnostics_and_reraises(self):
        import ast
        import json
        resource_path=Path(m.__file__).parent/'resources.py'
        tree=ast.parse(resource_path.read_text())
        function=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='observe_storage')
        fatal=KeyboardInterrupt('original fatal');fatal.observation={'hardlink_observations':[{'relative_path':'a','links':2}]}
        class Watch:
            def check(self):raise fatal
        state={};namespace={'storage_watch':Watch(),'state':state}
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(resource_path),'exec'),namespace)
        with self.assertRaises(KeyboardInterrupt) as caught:namespace['observe_storage']()
        self.assertIs(caught.exception,fatal)
        self.assertEqual(json.loads(json.dumps(state['storage_breach'])),fatal.observation)
        self.assertIn('KeyboardInterrupt',state['storage_last_error'])

if __name__=='__main__':unittest.main()
