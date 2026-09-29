"""Synthetic preservation checks; no SSH and no research inputs."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import hashlib
import shutil
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('offload', HERE / 'offload.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Transport:
    def __init__(self, root, corrupt=False, fail_metadata=False):
        self.root = root
        self.corrupt = corrupt
        self.fail_metadata = fail_metadata

    def put(self, source, remote):
        if remote.endswith('.json') and self.fail_metadata:
            raise OSError('injected metadata upload failure')
        shutil.copyfile(source, self.root / Path(remote).name)

    def get(self, remote, destination):
        shutil.copyfile(self.root / Path(remote).name, destination)
        if self.corrupt:
            Path(destination).write_bytes(b'corrupt')


class Preservation(unittest.TestCase):
    def exercise(self, fault=None):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            here = root / 'receipts'; here.mkdir()
            remote = root / 'remote'; remote.mkdir()
            source = root / 'old.bin'; source.write_bytes(b'preserved historical failure')
            row = {'path':'old.bin', 'bytes':source.stat().st_size,
                   'sha256':module.sha(source), 'stat_identity':module.identity(source.stat())}
            transport = Transport(remote, corrupt=fault=='download', fail_metadata=fault=='metadata')
            if fault == 'source':
                source.write_bytes(b'changed source')
            if fault == 'receipt':
                (here / '00-verified.json').write_text('existing immutable receipt')
            if fault:
                with self.assertRaises((ValueError, OSError)):
                    module.offload_one(root, here, row, 0, 'new-remote', transport)
                self.assertTrue(source.is_file())
            else:
                result = module.offload_one(root, here, row, 0, 'new-remote', transport)
                self.assertFalse(source.exists())
                self.assertEqual(hashlib.sha256((remote/'00.bin').read_bytes()).hexdigest(), row['sha256'])
                self.assertEqual(json.loads((here/'00-verified.json').read_text()), result)
                self.assertEqual(json.loads((remote/'00-restore.json').read_text()), result)
                self.assertTrue((here/'00-evicted.json').is_file())
                self.assertTrue(source.with_name('old.bin.remote.json').is_file())
                self.assertFalse((here/'00-recovered.bin').exists())

    def test_success_preserves_remote_bytes_and_restore_receipts(self):self.exercise()
    def test_corrupt_download_keeps_source(self):self.exercise('download')
    def test_metadata_failure_keeps_source(self):self.exercise('metadata')
    def test_source_drift_keeps_source(self):self.exercise('source')
    def test_existing_receipt_keeps_source(self):self.exercise('receipt')

    def test_local_publication_failure_keeps_source(self):
        for failing_name in ('00-verified.json', 'old.bin.remote.json'):
            with self.subTest(failing_name=failing_name), tempfile.TemporaryDirectory() as name:
                root=Path(name);here=root/'receipts';here.mkdir();remote=root/'remote';remote.mkdir()
                source=root/'old.bin';source.write_bytes(b'preserve me')
                row={'path':'old.bin','bytes':source.stat().st_size,'sha256':module.sha(source),
                     'stat_identity':module.identity(source.stat())}
                publish=module.publish
                def failing_publish(path,value):
                    if Path(path).name==failing_name:raise OSError('injected publication failure')
                    publish(path,value)
                with patch.object(module,'publish',side_effect=failing_publish), self.assertRaises(OSError):
                    module.offload_one(root,here,row,0,'new-remote',Transport(remote))
                self.assertEqual(source.read_bytes(),b'preserve me')

    def test_completion_metadata_failure_has_no_complete_marker(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);here=root/'receipts';here.mkdir();remote=root/'remote';remote.mkdir()
            # Bodies may already be remote; terminal failure must not report full completion.
            (here/'00-evicted.json').write_text('{"body_preserved": true}')
            with self.assertRaises(OSError):
                module.finish(here,{'bytes_moved':123},'new-remote',Transport(remote,fail_metadata=True))
            self.assertFalse((here/'complete.json').exists())
            self.assertTrue((here/'completion-candidate.json').is_file())
            self.assertTrue((here/'00-evicted.json').is_file())

    def test_completion_success_waits_for_remote_roundtrip(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);here=root/'receipts';here.mkdir();remote=root/'remote';remote.mkdir()
            module.finish(here,{'bytes_moved':123},'new-remote',Transport(remote))
            self.assertEqual(json.loads((here/'complete.json').read_text()),{'bytes_moved':123})

    def test_bound_policy_is_checked_before_reduced_guard_contract(self):
        from tradingagents.research.onchain_replication import resources
        for valid in (False,True):
            with self.subTest(valid=valid),tempfile.TemporaryDirectory() as name:
                root=Path(name);here=root/'receipts';here.mkdir()
                policy=root/'policy.json';policy.write_text(json.dumps({'schema_version':1,'disk_floor_bytes':(10 if valid else 20)*1024**3}))
                manifest=here/'manifest.json';manifest.write_text(json.dumps({'disk_policy':'policy.json','disk_policy_sha256':module.sha(policy)}))
                (here/'bindings.json').write_text(json.dumps({'policy.json':module.sha(policy),'receipts/manifest.json':module.sha(manifest)}))
                with patch.object(module,'ROOT',root),patch.object(module,'HERE',here),patch.object(resources,'assert_guarded_worker',side_effect=RuntimeError('guard sentinel')) as guard:
                    if valid:
                        with self.assertRaisesRegex(RuntimeError,'guard sentinel'):module.worker()
                        self.assertEqual(guard.call_args.kwargs['disk_floor_bytes'],10*1024**3)
                    else:
                        with self.assertRaisesRegex(ValueError,'unexpected prospective disk policy'):module.worker()
                        guard.assert_not_called()


if __name__ == '__main__':unittest.main()
