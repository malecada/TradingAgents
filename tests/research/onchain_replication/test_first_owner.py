"""Fresh journal allocation and incomplete-construction preservation checks."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests.research.onchain_replication import test_matching_owner as first
from tests.research.test_lifecycle import commit
from tradingagents.research.lifecycle import ResearchRun,_immutable
from tradingagents.research.onchain_replication import matching_owner as owner,feature_journal,job,resources
from tradingagents.research.onchain_replication.cache import cache_key

class Tests(unittest.TestCase):
    def fixture(self,mutate=None):
        f=first.OwnershipTests('test_actual_claim_owner_and_old_numerical_anchor_are_distinct')
        self.addCleanup(f.doCleanups)
        def prepare(f):
            if mutate is not None:mutate(f)
            f.input('plan',f.plan);f.input('execution_job',f.execution)
            f.source=commit(f.root,f.spec)
            f.run=ResearchRun.start(root=f.root,registration='registration.json',experiment='example-a',source=f.source)
            self.addCleanup(lambda:f.run.fail('synthetic first-owner fixture closed'))
            f.directory=f.root/'research_artifacts/onchain_representations'/cache_key(f.descriptor)/'example-a'
            f.base=f.root/job.PREFIX/'runs/example-a';f.base.mkdir(parents=True)
            launch={'experiment':'example-a','source_commit':f.source,'supervisor_pid':os.getpid(),'nonce':'synthetic-first'}
            guard={**launch,'monitor_pid':os.getpid(),'monitor_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]}
            _immutable(f.base/'launch.json',launch);_immutable(f.base/'owner.json',guard)
            mock=patch.object(resources,'assert_guarded_worker',return_value={**f.resources,'owner_identity':guard,'monitor_pid':os.getpid()})
            mock.start();self.addCleanup(mock.stop)
        with patch.object(first.OwnershipTests,'prepare',new=prepare):f.setUp()
        return f
    def open(self,f):
        return owner.open_first(f.run,representation='r',plan_input='plan',producer='p',policy_input='pair_policy')
    def test_first_owner_creates_once_and_refuses_existing_residue(self):
        f=self.fixture();journal,bound=self.open(f);bound.lease()
        self.assertEqual(journal.required,['a'*64])
        with self.assertRaisesRegex(ValueError,'already reserved'):self.open(f)
        self.assertFalse(journal.sealed)
    def test_redirected_ancestor_refuses_without_external_residue(self):
        f=self.fixture();external=f.root/'external';external.mkdir()
        parent=f.root/'research_artifacts/onchain_representations';parent.parent.mkdir(exist_ok=True);parent.symlink_to(external,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'redirected'):self.open(f)
        self.assertEqual(list(external.iterdir()),[])
    def test_noncanonical_required_graphs_refuse_before_namespace(self):
        f=self.fixture(lambda f:f.descriptor.update(required_graphs=['b'*64,'a'*64]))
        with self.assertRaisesRegex(ValueError,'canonical'):self.open(f)
        self.assertFalse(f.directory.parent.exists())
    def test_owner_start_claim_write_failures_preserve_residue(self):
        for filename in ('owner.json','start.json','claim.json'):
            with self.subTest(filename=filename):
                f=self.fixture();module=owner if filename=='claim.json' else feature_journal
                original=module._immutable
                def fail(path,value):
                    if Path(path).name==filename:raise OSError('injected publication failure')
                    return original(path,value)
                with patch.object(module,'_immutable',side_effect=fail),self.assertRaises(owner.JournalConstructionError):self.open(f)
                self.assertTrue(f.directory.is_dir())
                note=job._incomplete_representation(f.directory,f.root)
                self.assertIn(filename,note['missing_metadata']);self.assertFalse(note['owner_verified'])
                self.assertFalse(note['automatic_reuse_allowed'])
                before={p.name:p.read_bytes() for p in f.directory.iterdir()}
                with self.assertRaisesRegex(ValueError,'already reserved'):self.open(f)
                self.assertEqual(before,{p.name:p.read_bytes() for p in f.directory.iterdir()})
    def test_guard_failure_precedes_namespace_creation(self):
        f=self.fixture()
        with patch.object(resources,'assert_guarded_worker',side_effect=RuntimeError('guard stopped')),self.assertRaisesRegex(RuntimeError,'guard stopped'):self.open(f)
        self.assertFalse(f.directory.parent.exists())
    def test_incomplete_observer_refuses_symlink_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();directory=root/'journal';directory.mkdir()
            (directory/'owner.json').symlink_to(root/'missing')
            with self.assertRaisesRegex(ValueError,'metadata'):job._incomplete_representation(directory,root)

if __name__=='__main__':unittest.main(verbosity=2)
