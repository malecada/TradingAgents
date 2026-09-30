"""Exercise actual guard boundary with tiny synthetic kernel/receipt surfaces."""
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import release
from tradingagents.research.onchain_replication import resources


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.receipt=self.root/'verification01'
        (self.receipt/'guard').mkdir(parents=True)
        self.cg=self.root/'cgroup';self.cg.mkdir()
        for name,value in {'memory.max':3*1024**3,'memory.high':2*1024**3,'memory.swap.max':0,'cgroup.procs':os.getpid()}.items():
            (self.cg/name).write_text(str(value))
        self.source='a'*40;self.binding='b'*64;self.boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        ticks=Path('/proc/self/stat').read_text().rpartition(')')[2].split()[19]
        self.reservation={'source_commit':self.source,'bindings_sha256':self.binding,
                          'pid':os.getpid(),'start_ticks':ticks,'boot_id':self.boot}
        self.live={'phase':'running','owner_identity':{'kind':release.KIND,'source_commit':self.source,'bindings_sha256':self.binding},
            'monotonic_seconds':time.monotonic(),'lease_seconds':15,'boot_id':self.boot,'monitor_pid':os.getpid(),
            'cgroup':str(self.cg),'memory_max_bytes':3*1024**3,'memory_high_bytes':2*1024**3,'memory_swap_max_bytes':0,
            'disk_floor_bytes':10*1024**3,'disk_paths':[str(self.root)],'wall_seconds':1800,'reserve_bytes':3*1024**3,
            'start_reserve_bytes':6*1024**3,'cpus':[0,1],
            'command':[str(self.root/'.venv/bin/python'),'-B',str(self.root/'verify_saved.py'),'--source',self.source]}
        for obj,name,value in ((release,'ROOT',self.root),(release,'HERE',self.root),(release,'RECEIPT',self.receipt),
                               (resources,'_own_cgroup',lambda:self.cg),(resources.os,'sched_getaffinity',lambda _: {0,1})):
            p=patch.object(obj,name,value);p.start();self.addCleanup(p.stop)
        # Old boundary reads its own /proc path directly; expose the same tiny
        # cgroup surface so refusal tests reach the missing checks before fix.
        own=self.root/'own-cgroup.txt';own.write_text('0::/cgroup\n')
        def path_surface(*args):
            if args==('/proc/self/cgroup',):return own
            if args==('/sys/fs/cgroup',):return self.root
            return Path(*args)
        p=patch.object(release,'Path',path_surface);p.start();self.addCleanup(p.stop)
        (self.receipt/'guard/release.json').write_text('{"kernel_controls_verified":true}')
        self.save()
    def save(self):
        (self.receipt/'guard/live.json').write_text(json.dumps(self.live))
        (self.receipt/'reservation.json').write_text(json.dumps(self.reservation))
    def check(self):return release.live_guard(self.source,self.binding)
    def test_correct_real_boundary(self):
        self.assertEqual(self.check()['monitor_pid'],os.getpid())
    def test_monitor_start_tick_mismatch_refused(self):
        self.reservation['start_ticks']='0';self.save()
        with self.assertRaises((ValueError,RuntimeError)):self.check()
    def test_reservation_source_mismatch_refused(self):
        self.reservation['source_commit']='f'*40;self.save()
        with self.assertRaises((ValueError,RuntimeError)):self.check()
    def test_wrong_child_command_refused(self):
        self.live['command'][-1]='f'*40;self.save()
        with self.assertRaises((ValueError,RuntimeError)):self.check()
    def test_kernel_limit_mismatch_refused(self):
        (self.cg/'memory.max').write_text(str(4*1024**3))
        with self.assertRaises((ValueError,RuntimeError)):self.check()
    def test_unreleased_worker_refused(self):
        (self.receipt/'guard/release.json').write_text('{"kernel_controls_verified":false}')
        with self.assertRaises((ValueError,RuntimeError)):self.check()
    def test_matching_one_cpu_affinity_refused(self):
        self.live['cpus']=[0];self.save()
        with patch.object(resources.os,'sched_getaffinity',return_value={0}):
            with self.assertRaisesRegex(RuntimeError,'exactly two CPU IDs required'):self.check()
    def test_resource_limits_refused(self):
        for key,value in (('wall_seconds',1801),('reserve_bytes',0),('start_reserve_bytes',0),('disk_paths',[]),('cpus',[0])):
            with self.subTest(key=key):
                before=self.live[key];self.live[key]=value;self.save()
                try:
                    with self.assertRaises((ValueError,RuntimeError)):self.check()
                finally:self.live[key]=before;self.save()


if __name__=='__main__':unittest.main(verbosity=2)
