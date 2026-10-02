"""Tiny offline launcher contract tests; no resource job or numerical import."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH=Path(__file__).with_name('launcher02.py')
class Tests(unittest.TestCase):
    def api(self):
        self.assertTrue(PATH.exists(),'launcher02 missing')
        spec=importlib.util.spec_from_file_location('launcher02',PATH)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    def test_duplicate_reservation_preserves_original(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);api.reserve(root,{'identity':'first'})
            before=(root/'reservation.json').read_bytes()
            with self.assertRaises(FileExistsError):api.reserve(root,{'identity':'second'})
            self.assertEqual((root/'reservation.json').read_bytes(),before)
    def test_snapshot_mutation_refused(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'a.py').write_text('changed')
            with self.assertRaises(ValueError):api.verify_files(root,{'a.py':'0'*64})
    def test_symlink_and_unlisted_python_refused(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'a.py').write_text('a');sha=api.sha(root/'a.py')
            (root/'b.py').symlink_to(root/'a.py')
            with self.assertRaises(ValueError):api.verify_files(root,{'a.py':sha})
    def test_added_unit_limits_are_finite_and_environment_explicit(self):
        api=self.api();args=api.unit_arguments(['systemd-run','--user','--unit=x','/python','-B','child'],{'TMPDIR':'/owned/tmp'})
        self.assertIn('--property=LimitFSIZE=4194304',args)
        self.assertIn('--property=RuntimeMaxSec=1800s',args)
        self.assertIn('--setenv=TMPDIR=/owned/tmp',args)
        self.assertLess(args.index('--property=LimitFSIZE=4194304'),args.index('/python'))
    def test_conflicting_unit_property_refused(self):
        api=self.api()
        with self.assertRaises(ValueError):api.unit_arguments(['systemd-run','--property=LimitFSIZE=infinity','/python'],{})
    def test_infinite_or_soft_limit_mismatch_refused_before_release(self):
        api=self.api()
        good={'LimitFSIZE':'4194304','LimitFSIZESoft':'4194304','RuntimeMaxUSec':'30min'}
        api.verify_unit_properties(good)
        for key in good:
            with self.subTest(key=key),self.assertRaises(ValueError):api.verify_unit_properties({**good,key:'infinity'})
    def test_old_identity_spec_is_refused_without_namespace_reservation(self):
        api=self.api()
        old=Path(__file__).parent.parent/'owner-release-preparation01/prospective-release-spec02.json'
        spec=json.loads(old.read_bytes());spec['launcher_sha256']=api.sha(api.__file__)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'old-spec.json';path.write_text(json.dumps(spec))
            with self.assertRaises(ValueError):api.load_spec(path,api.sha(path))
            self.assertEqual({x.name for x in Path(d).iterdir()},{'old-spec.json'})
    def test_preparation_spec_cannot_launch(self):
        api=self.api()
        with self.assertRaises(ValueError):api.require_release({'status':'PREPARATION_ONLY_NOT_RELEASED'})
    def test_primary_fatal_survives_later_cleanup(self):
        api=self.api();fatal=MemoryError('first');later=KeyboardInterrupt('later')
        self.assertIs(api.retain(fatal,later),fatal)
        ordinary=ValueError('body');self.assertIs(api.retain(ordinary,later),later)
        self.assertIs(later.__cause__,ordinary)
if __name__=='__main__':unittest.main(verbosity=2)
