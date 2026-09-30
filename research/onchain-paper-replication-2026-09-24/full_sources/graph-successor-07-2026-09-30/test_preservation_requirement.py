"""Synthetic failure-boundary checks; no remote or research artifact reads."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import shutil
import unittest

spec = importlib.util.spec_from_file_location('preservation_requirement', Path(__file__).with_name('preservation_requirement.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RequirementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.storage = self.root / m.STORAGE
        self.storage.mkdir(parents=True)
        self.row = {'path': 'ledger.sqlite', 'bytes': 12, 'sha256': 'a'*64}
        self.record = {**self.row, 'body_roundtrip_verified': True,
                       'remote_object': 'remote/00.bin', 'remote_restore': 'remote/00-restore.json'}
        self.write('manifest.json', {'files':[self.row], 'total_bytes':12, 'remote':'remote'})
        self.write('guard01/final.json', {'phase':'complete', 'child_exit_code':0,
                   'cleanup_verified':True, 'cgroup':str(self.root/'absent-cgroup'), 'monitor_pid':2147483647})
        self.write('complete.json', {'files':[self.record], 'bytes_moved':12})
        for name in ('completion-candidate.json', 'recovered-complete.json'):
            (self.storage/name).write_bytes((self.storage/'complete.json').read_bytes())
        for name in ('00-verified.json','00-evicted.json','00-restore.json','00-recovered-restore.json'):
            self.write(name,self.record)
        (self.root/'ledger.sqlite.remote.json').write_text(json.dumps(self.record))
        self.write('CLOSURE_REVIEW.md', 'Independent synthetic review')
        self.review = {'decision':'accepted','scope':'closed-ledger-preservation-terminal',
                       'evidence':{}}
        self.refresh()
    def write(self,name,data):
        p=self.storage/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(data))
    def refresh(self):
        self.review['evidence']={name:hashlib.sha256((self.storage/name).read_bytes()).hexdigest() for name in m.REQUIRED}
        self.write('closure-review.json',self.review)
    def check(self):
        return m.verify(self.root)
    def test_accepts_complete_reviewed_preservation(self):
        self.assertEqual(self.check()['bytes_preserved'],12)
    def test_rejects_unreviewed_or_drifted_evidence(self):
        self.review['decision']='pending';self.refresh()
        with self.assertRaises(ValueError):self.check()
        self.review['decision']='accepted';self.refresh()
        self.write('00-verified.json',{})
        with self.assertRaises(ValueError):self.check()
    def test_rejects_live_owner_or_failed_terminal(self):
        final=json.loads((self.storage/'guard01/final.json').read_bytes())
        final['cgroup']=str(self.root);self.write('guard01/final.json',final);self.refresh()
        with self.assertRaises(ValueError):self.check()
        final['cgroup']=str(self.root/'absent');final['phase']='failed'
        self.write('guard01/final.json',final);self.refresh()
        with self.assertRaises(ValueError):self.check()
    def test_rejects_retained_source_or_sidecar_disagreement(self):
        (self.root/'ledger.sqlite').write_bytes(b'x')
        with self.assertRaises(ValueError):self.check()
        (self.root/'ledger.sqlite').unlink()
        (self.root/'ledger.sqlite.remote.json').write_text('{}')
        with self.assertRaises(ValueError):self.check()
    def test_rejects_incomplete_roundtrip_or_wrong_remote(self):
        self.record['body_roundtrip_verified']=False
        for name in ('00-verified.json','00-evicted.json','00-restore.json','00-recovered-restore.json'):
            self.write(name,self.record)
        self.refresh()
        with self.assertRaises(ValueError):self.check()

    def test_chain_requires_all_three_exact_preservation_identities(self):
        paths = [m.STORAGE.with_name('closed-ledger-offload-2026-09-30-'+suffix)
                 for suffix in ('01','02','03')]
        for p in paths[1:]:
            shutil.copytree(self.storage, self.root/p)
        result = m.verify_chain(self.root)
        self.assertEqual([x['path'] for x in result['preservations']], [str(p) for p in paths])
        self.assertEqual(result['total_bytes_preserved'], 36)
        (self.root/paths[-1]/'closure-review.json').unlink()
        with self.assertRaises(ValueError):
            m.verify_chain(self.root)
    def test_chain_refuses_failed_middle_preservation(self):
        paths = [m.STORAGE.with_name('closed-ledger-offload-2026-09-30-'+suffix)
                 for suffix in ('02','03')]
        for p in paths:
            shutil.copytree(self.storage, self.root/p)
        review_path = self.root/paths[0]/'closure-review.json'
        review = json.loads(review_path.read_bytes())
        review['decision'] = 'rejected'
        review_path.write_text(json.dumps(review))
        with self.assertRaises(ValueError):
            m.verify_chain(self.root)

if __name__=='__main__':unittest.main()
