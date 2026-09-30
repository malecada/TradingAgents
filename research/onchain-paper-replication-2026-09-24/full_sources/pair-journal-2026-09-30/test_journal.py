"""Tiny metadata fixtures only; no registered or numerical workload."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def api():
    assert (HERE/'journal.py').is_file(), 'durable pair journal implementation missing'
    spec = importlib.util.spec_from_file_location('pair_journal_candidate', HERE/'journal.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Tests(unittest.TestCase):
    def setUp(self):
        self.m = api()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = {'max_reserved_bytes': 10000000, 'max_reservations': 4, 'max_events': 20}
        self.owner = 'a'*64
        self.workflow = 'b'*64
        self.purpose = {'kind': 'dictionary', 'sample_hash': 'c'*64, 'indices': [0, 1], 'direction': [1, 0]}
        self.ident = 'd'*64

    def create(self, name='one', **kwargs):
        return self.m.Journal(self.root, name, self.owner, self.workflow, self.policy, **kwargs)

    def reserve(self, journal, purpose=None):
        purpose = self.purpose if purpose is None else purpose
        return journal.reserve(purpose, journal.target(purpose)['path'], self.ident, 1024)

    def artifact(self, reservation, kind='complete', **changes):
        path = Path(reservation['path']);path.parent.mkdir(parents=True)
        value = {'kind': kind, 'owner': reservation['artifact_owner'], 'identity': {'synthetic': True},
                 'parent': reservation.get('session_parent')}
        value.update(changes);path.write_bytes(self.m.encode(value))
        return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def compatible_reserve(self, journal, purpose=None):
        self.ident = self.m.digest({'synthetic': True})
        return self.reserve(journal, purpose)

    def test_completed_pair_is_reused_from_exact_failed_ancestry(self):
        j = self.create();r = self.compatible_reserve(j);ref = self.artifact(r);j.publish(ref)
        terminal = j.seal('failed')
        before = {str(p):p.read_bytes() for p in j.directory.rglob('*') if p.is_file()}
        child = self.create('child', parent=terminal)
        self.assertEqual(child.latest(self.purpose), ref)
        with self.assertRaisesRegex(ValueError, 'completed'):
            self.reserve(child)
        self.assertEqual(before, {str(p):p.read_bytes() for p in j.directory.rglob('*') if p.is_file()})

    def test_ancestor_reservations_and_owner_overhead_are_not_reset(self):
        self.policy['max_reservations'] = 1
        j = self.create();r = self.compatible_reserve(j);j.publish(self.artifact(r));parent = j.seal('failed')
        child = self.create('child', parent=parent)
        self.assertEqual(child.reservations, 1)
        self.assertGreater(child.reserved_bytes, j.reserved_bytes)
        with self.assertRaisesRegex(ValueError, 'quota'):
            self.reserve(child, self.purpose | {'direction': [0, 1]})
        self.assertEqual(len(list(child.directory.glob('event-*.json'))), 0)

    def test_unpublished_reservation_blocks_recovery_even_without_artifact(self):
        j = self.create();self.compatible_reserve(j);parent = j.seal('failed')
        with self.assertRaisesRegex(ValueError, 'reconciliation'):
            self.create('child', parent=parent)
        self.assertFalse((self.root/'child').exists())

    def test_complete_orphan_requires_reconciliation_not_rerun(self):
        j = self.create();r = self.compatible_reserve(j);ref = self.artifact(r)
        with patch.object(self.m, 'write', side_effect=OSError('journal disk failure')):
            with self.assertRaises(OSError):j.publish(ref)
        self.assertTrue(Path(ref['path']).exists())
        with self.assertRaisesRegex(ValueError, 'poisoned'):j.latest(self.purpose)
        # The unsealed journal is retained for an external death/recovery checker.
        self.assertTrue((j.directory/'event-000000.json').exists())
        self.assertFalse((j.directory/'event-000001.json').exists())

    def test_only_current_pending_reference_can_publish(self):
        j = self.create();r = self.compatible_reserve(j);ref = self.artifact(r)
        for wrong in (ref | {'sha256': 'f'*64}, ref | {'path': str(self.root/'elsewhere/manifest.json')}):
            with self.assertRaises(ValueError):j.publish(wrong)
        j.publish(ref)
        with self.assertRaises(ValueError):j.publish(ref)
        self.assertEqual(j.latest(self.purpose), ref)

    def test_progress_predecessor_chain_retains_latest_direction(self):
        j = self.create();r = self.compatible_reserve(j);first = self.artifact(r, kind='progress');j.publish(first)
        r2 = self.reserve(j);self.assertEqual(r2['predecessor'], first)
        second = self.artifact(r2);j.publish(second)
        child = self.create('child', parent=j.seal('failed'))
        self.assertEqual(child.latest(self.purpose), second)
        self.assertIsNone(child.latest(self.purpose | {'direction': [0, 1]}))

    def test_foreign_owner_or_identity_manifest_refused(self):
        for change in ({'owner': 'f'*64}, {'identity': {'foreign': True}}):
            with self.subTest(change=change):
                j = self.create('x'+str(len(list(self.root.iterdir()))));r = self.compatible_reserve(j)
                with self.assertRaisesRegex(ValueError, 'identity'):
                    j.publish(self.artifact(r, **change))

    def test_parent_tampering_tail_omission_and_symlink_refused(self):
        j = self.create();r = self.compatible_reserve(j);j.publish(self.artifact(r));parent=j.seal('failed')
        event = j.directory/'event-000001.json';old=event.read_bytes();event.write_text('{}')
        with self.assertRaises(ValueError):self.create('bad', parent=parent)
        event.write_bytes(old)
        extra = j.directory/'event-000002.json';extra.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'inventory'):self.create('bad2', parent=parent)
        extra.unlink()
        link=self.root/'linked';link.symlink_to(j.directory, target_is_directory=True)
        with self.assertRaises(ValueError):self.m.Journal(link, 'bad3', self.owner, self.workflow, self.policy)

    def test_complete_parent_foreign_workflow_policy_and_duplicate_owner_refused(self):
        j=self.create()
        with self.assertRaises(FileExistsError):self.create()
        parent=j.seal('complete')
        with self.assertRaisesRegex(ValueError, 'failed'):self.create('child', parent=parent)
        k=self.create('two');parent=k.seal('failed')
        self.workflow='e'*64
        with self.assertRaises(ValueError):self.create('foreign', parent=parent)
        self.workflow='b'*64;self.policy['max_events']=21
        with self.assertRaises(ValueError):self.create('changed', parent=parent)

    def test_reservation_keeps_room_for_publication_before_numerical_work(self):
        self.policy['max_events'] = 1
        j = self.create()
        with self.assertRaisesRegex(ValueError, 'quota'):
            self.compatible_reserve(j)
        self.assertEqual(j.reservations, 0)
        self.assertEqual(list(j.directory.glob('event-*.json')), [])

    def test_reservation_cannot_claim_an_existing_artifact_path(self):
        j = self.create();path=Path(j.target(self.purpose)['path'])
        path.parent.mkdir(parents=True);path.write_text('retained evidence')
        with self.assertRaisesRegex(ValueError, 'existing'):
            j.reserve(self.purpose, path, self.ident, 1024)
        self.assertEqual(path.read_text(), 'retained evidence')
        self.assertEqual(j.reservations, 0)

    def test_actual_pair_multiple_checkpoints_and_child_resume(self):
        from tradingagents.research.onchain_replication import matching_pair as pair
        from tests.research.onchain_replication.test_matching_pair_checkpoints import POLICY, CONTEXT
        from tests.research.onchain_replication.test_matching_reference import graph, config
        a=graph([[0.], [.3]], [(0, 1, .2)])
        b=graph([[0.], [.1]], [(0, 1, .3)])
        c=config() | {'max_iterations': 1}
        ident=pair.identity(a,b,c,CONTEXT)
        self.ident=pair.digest(ident)
        self.policy['max_reserved_bytes']=100000000
        self.policy['max_reservations']=10
        root=self.root/'pairs';root.mkdir()
        j=self.create();target=j.target(self.purpose)
        j.reserve(self.purpose,target['path'],self.ident,1024**2)
        session=pair.PairSession.create(root,target['artifact_owner'],a,b,c,
            owner=target['artifact_owner'],context=CONTEXT,policy=POLICY)
        try:
            session.step(max_operations=2);first=session.save();j.publish(first)
            next_target=j.target(self.purpose)
            self.assertEqual(next_target['artifact_owner'],target['artifact_owner'])
            self.assertNotEqual(next_target['path'],first['path'])
            j.reserve(self.purpose,next_target['path'],self.ident,1024**2)
            session.step(max_operations=2);second=session.save();j.publish(second)
        finally:session.close()
        child=self.create('child',parent=j.seal('failed'));t=child.target(self.purpose)
        child.reserve(self.purpose,t['path'],self.ident,1024**2)
        resumed=pair.PairSession.resume(root,t['artifact_owner'],a,b,c,child.latest(self.purpose),
            owner=t['artifact_owner'],expected_owner=target['artifact_owner'],context=CONTEXT,policy=POLICY)
        try:
            resumed.step(max_operations=2)
            child_progress=resumed.save();child.publish(child_progress)
            t2=child.target(self.purpose)
            self.assertEqual(t2['session_parent'],t['session_parent'])
            child.reserve(self.purpose,t2['path'],self.ident,1024**2)
            for _ in range(1000):
                if resumed.step(max_operations=2) is not None:break
            else:self.fail('pair did not finish')
            final=resumed.save();child.publish(final)
            self.assertEqual(child.latest(self.purpose),final)
        finally:resumed.close()
        with self.assertRaisesRegex(ValueError,'completed'):self.reserve(child)

    def test_child_artifact_cannot_restart_instead_of_resuming_latest_pair(self):
        j=self.create();r=self.compatible_reserve(j);prior=self.artifact(r,kind='progress');j.publish(prior)
        child=self.create('child',parent=j.seal('failed'));reservation=self.reserve(child)
        with self.assertRaisesRegex(ValueError,'parent'):
            child.publish(self.artifact(reservation,kind='progress',parent=None))

    def test_real_child_create_manifest_cannot_impersonate_resume(self):
        from tradingagents.research.onchain_replication import matching_pair as pair
        from tests.research.onchain_replication.test_matching_pair_checkpoints import POLICY, CONTEXT
        from tests.research.onchain_replication.test_matching_reference import graph, config
        a=graph([[0.], [.3]], [(0, 1, .2)]);c=config() | {'max_iterations': 1}
        self.ident=pair.digest(pair.identity(a,a,c,CONTEXT))
        root=self.root/'pairs';root.mkdir();j=self.create();t=j.target(self.purpose)
        j.reserve(self.purpose,t['path'],self.ident,1024**2)
        session=pair.PairSession.create(root,t['artifact_owner'],a,a,c,
            owner=t['artifact_owner'],context=CONTEXT,policy=POLICY)
        try:j.publish(session.save())
        finally:session.close()
        child=self.create('child',parent=j.seal('failed'));t=child.target(self.purpose)
        child.reserve(self.purpose,t['path'],self.ident,1024**2)
        restarted=pair.PairSession.create(root,t['artifact_owner'],a,a,c,
            owner=t['artifact_owner'],context=CONTEXT,policy=POLICY)
        try:
            wrong=restarted.save()
            with self.assertRaisesRegex(ValueError,'parent'):child.publish(wrong)
            self.assertTrue(Path(wrong['path']).exists())
        finally:restarted.close()


if __name__ == '__main__':
    unittest.main()
