"""Synthetic receipt fields exercise actual parser; never native/Owner evidence."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

D=Path(__file__).resolve().parent
OLD=D.parent/'original-import-fixture-native-preparation02-2026-10-03'
sys.path.insert(0,str(OLD))
from test_raw01 import fixture
spec=importlib.util.spec_from_file_location('positive_parser_under_test',D/'raw_receipts01.py')
parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)

def complete_fake(root,case):
    release,base,run,write=fixture(root,case)
    limits=release['cases'][case]['job_resources']
    limits.update(wall_seconds=1800,reserve_bytes=3*parser.GIB,disk_floor_bytes=10*parser.GIB,
        storage_budget={'root':str(root),'limits':{'max_allocated_bytes':parser.GIB,
            'max_logical_bytes':parser.GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}})
    info=root.stat();observation={'root':str(root),'root_device':info.st_dev,'root_inode':info.st_ino,
        'allocated_bytes':4096,'logical_file_bytes':128,'regular_files':2,'directories':1,'entries':2,'elapsed_seconds':.01}
    snapshot={'memory_current_bytes':123,'memory_events':{'oom':0,'oom_kill':0}}
    guard=parser.metadata(root,base+'/guard/final.json')
    guard.update(limits);guard.update(terminal_memory_snapshot=snapshot,memory_current_bytes=123,
        memory_events=snapshot['memory_events'],initial_memory_events={'oom':0,'oom_kill':0},
        peak_sampled_memory_current_bytes=128,elapsed_seconds=2.,host_mem_available_bytes=4*parser.GIB,
        disk_free_bytes={str(root):11*parser.GIB},storage_observation=observation,
        storage_peak_allocated_bytes=8192,storage_peak_logical_file_bytes=256,storage_peak_entries=4)
    child=parser.metadata(root,base+'/guard/child_exit.json')
    child.update(reason='workload exited',terminal_memory_snapshot=snapshot,snapshot_error=None)
    write(base+'/guard/final.json',guard);write(base+'/guard/child_exit.json',child)
    return release,base,run,write,guard,child,observation

class PositiveObservations(unittest.TestCase):
    def test_both_fixed_lifecycle_dispositions_accept_complete_fake_observations(self):
        for case in ('success','second_target_publication_failure'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);release,*_=complete_fake(root,case)
                proof=parser.authenticate(root,case,release)
                self.assertEqual(proof['lifecycle_status'],'complete' if case=='success' else 'failed')
                self.assertEqual(proof['native_observations']['sampled_memory_peak_bytes'],128)

    def test_missing_breached_or_wrong_positive_evidence_is_refused(self):
        variants=[('guard','storage_observation',None),('guard','storage_peak_allocated_bytes',0),
            ('guard','elapsed_seconds',True),('guard','host_mem_available_bytes',1),
            ('guard','disk_free_bytes',{}),('guard','initial_memory_events',{}),
            ('guard','terminal_memory_snapshot',{}),('child','snapshot_error','failed'),
            ('child','terminal_memory_snapshot',None),('guard','peak_sampled_memory_current_bytes',True)]
        for role,key,value in variants:
            with self.subTest(role=role,key=key),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);release,base,_,write,guard,child,_=complete_fake(root,'success')
                record=guard if role=='guard' else child;record[key]=value
                write(base+'/guard/'+('final.json' if role=='guard' else 'child_exit.json'),record)
                with self.assertRaises((ValueError,KeyError)):parser.authenticate(root,'success',release)

    def test_native_late_failure_marker_overrides_earlier_complete_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);release,base,_,write,*_=complete_fake(root,'success')
            write(base+'/guard/native-finalization-failed.json',{'status':'failed'})
            with self.assertRaises(ValueError):parser.authenticate(root,'success',release)

    def test_missing_child_snapshot_error_field_is_not_assumed_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);release,base,_,write,guard,child,_=complete_fake(root,'success')
            del child['snapshot_error'];write(base+'/guard/child_exit.json',child)
            with self.assertRaises(ValueError):parser.authenticate(root,'success',release)

    def test_final_tail_is_joined_and_late_failure_remains_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);release,base,run,write,guard,child,observation=complete_fake(root,'success')
            identity=release['cases']['success']['identity'];prefix='fixture_outer/'+identity
            write(prefix+'/post-tail-storage.json',{'observation':observation,'disk_free_bytes':11*parser.GIB,
                'disk_floor_bytes':10*parser.GIB,'excludes_own_file':True,'remaining_final_file_allowance':65536})
            self.assertEqual(parser.authenticate_post_tail(root,identity,release['cases']['success']['job_resources'])['disk_free_bytes'],11*parser.GIB)
            write(prefix+'/post-terminal-failure.json',{'status':'failed'})
            with self.assertRaises(ValueError):parser.authenticate_post_tail(root,identity,release['cases']['success']['job_resources'])

if __name__=='__main__':unittest.main()
