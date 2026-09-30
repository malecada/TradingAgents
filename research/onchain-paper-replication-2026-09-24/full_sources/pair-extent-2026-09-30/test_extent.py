"""Tiny real pair publications, metadata/file-stat validation only."""
import hashlib
import os
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tradingagents.research.onchain_replication import matching_pair as pair
from tests.research.onchain_replication.test_matching_pair_checkpoints import POLICY, CONTEXT
from tests.research.onchain_replication.test_matching_reference import graph, config

HERE=Path(__file__).resolve().parent


def api():
    assert (HERE/'extent.py').is_file(), 'policy-bound extent verifier missing'
    spec=importlib.util.spec_from_file_location('pair_extent_candidate',HERE/'extent.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class Tests(unittest.TestCase):
    def setUp(self):
        self.m=api();self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.a=graph([[0.],[.3]],[(0,1,.2)]);self.b=graph([[0.],[.1]],[(0,1,.3)])
        self.c=config() | {'max_iterations':1};self.owner='a'*64
        self.identity=pair.identity(self.a,self.b,self.c,CONTEXT)
        self.session=pair.PairSession.create(self.root,'session',self.a,self.b,self.c,
            owner=self.owner,context=CONTEXT,policy=POLICY)
        self.addCleanup(self.session.close)

    def verify(self, ref, **changes):
        args={'root':self.root,'owner':self.owner,'identity':self.identity,'policy':POLICY,
              'parent':None,'declared_artifact_bytes':self.m.reservation_bytes(POLICY)}
        args.update(changes);return self.m.verify(ref,**args)

    @contextmanager
    def no_array_reads(self):
        original_open=os.open
        def opening(path,*args,**kwargs):
            if Path(path).suffix=='.npy':raise AssertionError('numerical body opened')
            return original_open(path,*args,**kwargs)
        original=Path.read_bytes
        def read(path):
            if path.suffix=='.npy':raise AssertionError('numerical body opened')
            return original(path)
        with patch.object(Path,'read_bytes',read),patch.object(os,'open',opening):
            yield

    def test_real_annealing_inventory_and_bytes_without_array_reads(self):
        ref=self.session.save()
        with self.no_array_reads(),patch.object(pair.engine.ann.np,'load',side_effect=AssertionError('array loaded')):
            report=self.verify(ref)
        paths=[p for p in Path(ref['path']).parent.rglob('*') if p.is_file()]
        self.assertEqual(report['publication_logical_bytes'],sum(p.stat().st_size for p in paths))
        self.assertEqual(report['array_files'],3)
        self.assertEqual(report['metadata_files'],3)
        self.assertLessEqual(report['publication_logical_bytes'],report['reserved_artifact_bytes'])
        self.assertEqual(report['owner_logical_bytes'],(self.session.directory/'owner.json').stat().st_size)

    def test_ranked_hardening_inventory(self):
        for _ in range(1000):
            pair.engine.advance(self.session.state,self.a,self.b,self.c,max_operations=2)
            if self.session.state['phase']=='hardening':break
        else:self.fail('hardening phase not reached')
        ref=self.session.save()
        with self.no_array_reads():report=self.verify(ref)
        self.assertEqual(report['array_files'],4)
        self.assertEqual(report['metadata_files'],4)

    def test_complete_publication_has_no_state(self):
        for _ in range(1000):
            if self.session.step(max_operations=2) is not None:break
        else:self.fail('pair not complete')
        ref=self.session.save()
        with self.no_array_reads():report=self.verify(ref)
        self.assertEqual(report['array_files'],0)
        self.assertEqual(report['metadata_files'],1)
        self.assertEqual(report['state_logical_bytes'],0)

    def test_under_reservation_refused_before_any_metadata_read(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('read before reservation check')):
            with self.assertRaisesRegex(ValueError,'reservation'):
                self.verify({'path':str(self.root/'missing/manifest.json'),'sha256':'b'*64},declared_artifact_bytes=1)

    def test_unexpected_file_missing_extent_and_wrong_size_refused(self):
        ref=self.session.save();base=Path(ref['path']).parent
        extra=base/'unregistered.bin';extra.write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'inventory'):self.verify(ref)
        extra.unlink();array=base/'state/annealing/V.npy';original=array.stat().st_size
        with array.open('ab') as f:f.write(b'x')
        with self.assertRaisesRegex(ValueError,'extent'):self.verify(ref)
        with array.open('r+b') as f:f.truncate(original)
        array.rename(array.with_suffix('.saved'))
        with self.assertRaises(ValueError):self.verify(ref)

    def test_symlink_and_hardlink_extents_refused(self):
        ref=self.session.save();base=Path(ref['path']).parent;array=base/'state/annealing/V.npy'
        outside=self.root/'outside.npy';array.rename(outside);array.symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'regular|symlink'):self.verify(ref)
        array.unlink();array.hardlink_to(outside)
        with self.assertRaisesRegex(ValueError,'link'):self.verify(ref)

    def test_exact_owner_policy_identity_parent_and_manifest_hash(self):
        ref=self.session.save()
        for changes in [{'owner':'b'*64},{'identity':self.identity | {'backend':{}}},
                        {'policy':POLICY | {'chunk_edges':1}},
                        {'parent':{'owner':'b'*64,'reference':ref}}]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.verify(ref,**changes)
        with self.assertRaises(ValueError):self.verify(ref | {'sha256':'b'*64})

    def test_changed_nested_metadata_rejected_without_array_read(self):
        ref=self.session.save();path=Path(ref['path']).parent/'state/annealing/manifest.json'
        value=json.loads(path.read_bytes());value['phase']='tampered';path.write_text(json.dumps(value))
        with self.no_array_reads(),self.assertRaisesRegex(ValueError,'hash'):self.verify(ref)

    def test_policy_values_cannot_be_boolean_or_nonpositive(self):
        for name in POLICY:
            for value in (True,0,-1):
                with self.subTest(name=name,value=value),self.assertRaises(ValueError):
                    self.m.reservation_bytes(POLICY | {name:value})

    def test_numerical_identity_primitive_types_are_exact(self):
        ref=self.session.save();path=Path(ref['path']);meta=json.loads(path.read_bytes())
        meta['identity']['backend']['version']=2.0
        path.write_bytes(pair.body(meta));ref['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'identity'):self.verify(ref)

    def journal(self):
        location=HERE.parent/'pair-journal-2026-09-30/journal.py'
        spec=importlib.util.spec_from_file_location('verified_extent_journal',location)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        return m.Journal(self.root,'journal','b'*64,'c'*64,
                        {'max_reserved_bytes':10000000,'max_reservations':10,'max_events':20})

    def test_policy_bound_reservation_and_verified_journal_publication(self):
        j=self.journal();root=self.root/'pairs';root.mkdir()
        record=self.m.reserve_pair(j,{'kind':'synthetic','direction':[0,1]},self.identity,POLICY)
        self.assertEqual(record['declared_artifact_bytes'],POLICY['max_checkpoint_bytes']+pair.LIMIT)
        session=pair.PairSession.create(root,record['artifact_owner'],self.a,self.b,self.c,
            owner=record['artifact_owner'],context=CONTEXT,policy=POLICY)
        try:
            ref=session.save()
            with self.no_array_reads():report=self.m.publish_pair(j,ref,identity=self.identity,policy=POLICY)
            self.assertEqual(j.latest(record['purpose']),ref)
            self.assertFalse(report['array_contents_verified'])
        finally:session.close()

    def test_unverified_or_under_reserved_artifact_never_publishes(self):
        j=self.journal();root=self.root/'pairs';root.mkdir();purpose={'kind':'synthetic'}
        target=j.target(purpose);j.reserve(purpose,target['path'],pair.digest(self.identity),1)
        session=pair.PairSession.create(root,target['artifact_owner'],self.a,self.b,self.c,
            owner=target['artifact_owner'],context=CONTEXT,policy=POLICY)
        try:
            ref=session.save()
            with self.assertRaisesRegex(ValueError,'reservation'):
                self.m.publish_pair(j,ref,identity=self.identity,policy=POLICY)
            self.assertIsNone(j.latest(purpose));self.assertIsNotNone(j.state['pending'])
            self.assertTrue(Path(ref['path']).exists())
        finally:session.close()

    def test_owner_metadata_cannot_escape_supplied_pair_root(self):
        for _ in range(1000):
            if self.session.step(max_operations=2) is not None:break
        ref=self.session.save();root=self.root/'nested';root.mkdir()
        (root/'manifest.json').write_bytes(Path(ref['path']).read_bytes())
        (self.root/'owner.json').write_bytes((self.session.directory/'owner.json').read_bytes())
        ref={'path':str(root/'manifest.json'),'sha256':ref['sha256']}
        with patch.object(os,'open',side_effect=AssertionError('metadata opened before root rejection')):
            with self.assertRaisesRegex(ValueError,'layout|containment'):
                self.verify(ref,root=root)


if __name__=='__main__':unittest.main()
