"""Synthetic storage accounting; no study arrays, fits or historical replay."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tradingagents.research.onchain_replication.workflow_storage import StorageWatch,StorageLimit

class Tests(unittest.TestCase):
    def fixture(self,**changes):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)/'outputs';root.mkdir()
        limits={'max_allocated_bytes':1024*1024,'max_logical_bytes':1024*1024,'max_entries':100,'max_depth':8,'max_scan_seconds':5}
        limits.update(changes);return root,limits
    def test_allocated_bytes_include_directory_blocks_and_repeat_growth(self):
        root,limits=self.fixture();sub=root/'nested';sub.mkdir();file=sub/'data';file.write_bytes(b'a'*4097)
        watcher=StorageWatch(root,limits);r=watcher.check()
        self.assertEqual(r['allocated_bytes'],sum(p.stat().st_blocks*512 for p in (root,sub,file)))
        self.assertEqual((r['logical_file_bytes'],r['regular_files'],r['directories'],r['entries']),(4097,1,2,2))
        file.write_bytes(b'b'*9000);self.assertEqual(watcher.check()['logical_file_bytes'],9000)
    def test_sparse_logical_cap_is_independent_of_allocated_cap(self):
        root,limits=self.fixture(max_logical_bytes=8192)
        with (root/'sparse').open('wb') as f:f.truncate(100000)
        with self.assertRaisesRegex(StorageLimit,'logical'):StorageWatch(root,limits).check()
    def test_allocated_limit_includes_empty_directory(self):
        root,limits=self.fixture(max_allocated_bytes=1)
        with self.assertRaisesRegex(StorageLimit,'allocated'):StorageWatch(root,limits).check()
    def test_redirect_and_special_file_refusal(self):
        for kind in ('symlink','hardlink','fifo'):
            with self.subTest(kind=kind):
                root,limits=self.fixture();source=root/'original';source.write_bytes(b'x')
                target=root/'foreign'
                if kind=='symlink':target.symlink_to('missing')
                elif kind=='hardlink':os.link(source,target)
                else:os.mkfifo(target)
                with self.assertRaisesRegex(ValueError,'regular|link|special'):StorageWatch(root,limits).check()
    def test_entry_and_depth_limits(self):
        root,limits=self.fixture(max_entries=1);(root/'a').touch();(root/'b').touch()
        with self.assertRaisesRegex(StorageLimit,'entries'):StorageWatch(root,limits).check()
        root,limits=self.fixture(max_depth=1);(root/'a/b').mkdir(parents=True)
        with self.assertRaisesRegex(StorageLimit,'depth'):StorageWatch(root,limits).check()
    def test_owned_root_replacement_refused(self):
        root,limits=self.fixture();watcher=StorageWatch(root,limits);root.rename(root.with_name('old'));root.mkdir()
        with self.assertRaisesRegex(ValueError,'root'):watcher.check()
    def test_bounded_time_and_descriptor_cleanup(self):
        root,limits=self.fixture();(root/'a').touch();watcher=StorageWatch(root,limits)
        before=len(list(Path('/proc/self/fd').iterdir()))
        with patch('tradingagents.research.onchain_replication.workflow_storage.time.monotonic',side_effect=[0,100]):
            with self.assertRaisesRegex(StorageLimit,'time'):watcher.check()
        self.assertEqual(before,len(list(Path('/proc/self/fd').iterdir())))
    def test_strict_limits(self):
        for key,value in (('max_entries',True),('max_depth',1000),('max_scan_seconds',0),('foreign',1)):
            root,limits=self.fixture();limits[key]=value
            with self.assertRaises(ValueError):StorageWatch(root,limits)
if __name__=='__main__':unittest.main(verbosity=2)
