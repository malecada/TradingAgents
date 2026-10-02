"""Small offline admission tests. No guard, unit, fixture or numerical imports."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

PATH=Path(__file__).with_name('launcher01.py')

class AdmissionTests(unittest.TestCase):
    def api(self):
        self.assertTrue(PATH.is_file(),'launcher implementation missing')
        spec=importlib.util.spec_from_file_location('owner_launcher01',PATH)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_host_partition_cannot_be_mistaken_for_dedicated_cap(self):
        api=self.api()
        with self.assertRaises(ValueError):
            api.validate_volume(capacity=100*1024**3,source_allocated=24662016,
                device=9,parent_device=9,filesystem='ext4',mount_exact=False)

    def test_tmpfs_rejected_even_when_small(self):
        api=self.api()
        with self.assertRaises(ValueError):
            api.validate_volume(capacity=512*1024**2,source_allocated=24662016,
                device=9,parent_device=8,filesystem='tmpfs',mount_exact=True)

    def test_aggregate_includes_source_and_control_reserve(self):
        api=self.api()
        with self.assertRaises(ValueError):
            api.validate_volume(capacity=1024**3,source_allocated=24662016,
                device=9,parent_device=8,filesystem='ext4',mount_exact=True)
        result=api.validate_volume(capacity=900*1024**2,source_allocated=24662016,
                device=9,parent_device=8,filesystem='ext4',mount_exact=True)
        self.assertLessEqual(result['aggregate_upper_bound_bytes'],1024**3)

    def test_one_shot_marker_preserved_and_duplicate_refused(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            api.reserve(root,'archive-outer-owner-20261002-01')
            original=(root/'reservation.json').read_bytes()
            with self.assertRaises(FileExistsError):api.reserve(root,'archive-outer-owner-20261002-01')
            self.assertEqual((root/'reservation.json').read_bytes(),original)

    def test_log_ceiling_never_appends_overflow(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'log'
            with api.BoundedLog(path,maximum=5) as log:
                log.write(b'abcd')
                with self.assertRaises(api.LogLimit):log.write(b'efg')
            self.assertEqual(path.read_bytes(),b'abcde')

if __name__=='__main__':unittest.main(verbosity=2)
