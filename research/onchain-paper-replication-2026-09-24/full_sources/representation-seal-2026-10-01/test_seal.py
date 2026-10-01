"""Synthetic registered publication-to-seal handoff; no financial fitting."""
import importlib.util
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash
from tests.research.onchain_replication import test_matching_owner as first

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('seal_publication_fixture',HERE.parent/'representation-publication-2026-10-01/test_publication.py')
def api():
    assert (HERE/'seal.py').exists(),'representation seal handoff missing'
    return load('representation_seal_candidate',HERE/'seal.py')

class Tests(unittest.TestCase):
    def fixture(self):
        self.m=m=api();f=base.Tests('test_complete_event_proof_and_predecessor_handoff_refuse_relaunch');self.addCleanup(f.doCleanups)
        original=first.OwnershipTests.input
        def configured(instance,name,value):
            if name=='plan':
                original(instance,'seal_policy',{'schema_version':1,'max_metadata_bytes':2097152,'max_attempt_bytes':14000000,
                    'max_snapshot_entries':2000,'max_journal_events':10,'max_pair_events':1000})
                value['producers']['p']['representation_seal_input']='seal_policy'
            if name=='execution_job':
                value['payload']['representation_jobs']['r'].update(representation_seal_input='seal_policy',
                    binding_output='binding.json',journal_output='journal.json')
            return original(instance,name,value)
        with patch.object(base,'api',return_value=m.publication),patch.object(m.publication,'SOURCES',m.SOURCES),patch.object(first.OwnershipTests,'input',new=configured):owner=f.fixture()
        self.f=f;self.owner=owner;return owner
    def finish(self):
        f=self.owner
        return self.m.finish(f.owned,f.journal,examples=f.examples,fold=f.fold,denominator_input='denominator',
            dictionary_ticket=self.f.f.ticket,closure_input='closure',output_input='representation_output',seal_input='seal_policy')
    def test_own_record_bytes_are_prebound_before_sync(self):
        m=api()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta=m.producer.Metadata(root);original=m.writer.sync_directory
            def corrupt(directory):
                original(directory);(directory/'start.json').write_bytes(canonical_bytes({'status':'tampered'}))
            with patch.object(m.writer,'sync_directory',side_effect=corrupt),self.assertRaises(ValueError):
                m.write_metadata(meta,root,'start.json',{'status':'reserved'},1024)
    def test_archive_enumeration_refuses_before_collecting_foreign_inventory(self):
        m=api()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for i in range(5):(root/str(i)).touch()
            with self.assertRaisesRegex(ValueError,'entry allowance'):m.bounded_children(root,2)
            self.assertEqual(set(m.bounded_children(root,5)),set(root.iterdir()))
    def test_examples_drift_after_publication_refuses_before_sealing(self):
        f=self.fixture();m=self.m;original=m.publication.produce
        def mutate(*args,**kwargs):
            result=original(*args,**kwargs);object.__setattr__(f.examples,'train_hash','0'*64);return result
        with patch.object(m.publication,'produce',side_effect=mutate),self.assertRaises(ValueError):self.finish()
        self.assertFalse(f.journal.sealed);self.assertFalse(f.owned.journal.sealed)
        self.assertTrue((m.attempt_directory(f.owned)/'failed.json').exists())
    def test_output_routes_require_exact_distinct_registered_names(self):
        m=api();item={'binding_output':'binding.json','journal_output':'journal.json'};allowed=list(item.values())
        self.assertEqual(m.outputs(item,item,allowed),('binding.json','journal.json'))
        for selected in ({},dict(item,binding_output='journal.json'),dict(item,journal_output='../journal.json')):
            with self.assertRaises(ValueError):m.outputs(item,selected,allowed)
        with self.assertRaises(ValueError):m.outputs(item,item,['binding.json'])
    def test_unadmitted_owner_refuses(self):
        with self.assertRaises(ValueError):api().finish(object(),None,examples=None,fold=None,denominator_input='x',
            dictionary_ticket=None,closure_input='x',output_input='x',seal_input='x')
    def test_seals_publishes_receipt_and_old_leases_refuse(self):
        f=self.fixture();m=self.m
        marker=f.owned.journal.directory/'failed.json';marker.symlink_to('missing-failure-target')
        with patch.object(m.publication,'produce',side_effect=AssertionError('terminal conflict entered producer')):
            with self.assertRaises(ValueError):self.finish()
        marker.unlink()  # This deliberately injected synthetic broken link was never a terminal run.
        original=f.owned.journal.state['pending'];f.owned.journal.state['pending']={'unresolved':True}
        with patch.object(m.publication,'produce',side_effect=AssertionError('pending state entered producer')):
            with self.assertRaises(ValueError):self.finish()
        f.owned.journal.state['pending']=original
        r=self.finish();r.lease()
        self.assertTrue(f.journal.sealed);self.assertTrue(f.owned.journal.sealed)
        for path in (f.directory/'complete.json',f.owned.journal.directory/'complete.json',m.attempt_directory(f.owned)/'complete.json'):
            self.assertTrue(path.is_file())
        run=f.owned.workload.bound._run;run._active()
        self.assertEqual(set(run._published_outputs),{'binding.json','journal.json'})
        binding=json.loads((run.directory/'outputs/binding.json').read_bytes())
        reference=json.loads((run.directory/'outputs/journal.json').read_bytes())
        self.assertEqual(binding['schema_version'],3);self.assertEqual(reference['sha256'],file_hash(f.directory/'complete.json'))
        with self.assertRaises(ValueError):f.owned.lease()
        with patch.object(m.publication,'produce',side_effect=AssertionError('closed producer repeated')):
            with self.assertRaises(ValueError):self.finish()
        with self.assertRaises(AttributeError):r._record={}
        pin=m.saved._issued[self.f.f.ticket]['record'];manifest=Path(pin['component']['path']);a=next(iter(json.loads(manifest.read_bytes())['arrays']))
        target=manifest.parent/a;raw=bytearray(target.read_bytes());raw[-1]^=1;target.write_bytes(raw)
        with self.assertRaises(ValueError):r.lease()
    def test_late_drift_during_feature_seal_preserves_terminal_evidence(self):
        f=self.fixture();m=self.m;original=type(f.journal).seal
        def corrupt(j,status,**kwargs):
            result=original(j,status,**kwargs)
            target=f.directory/f"checkpoint-{len(j.records)-1:06d}/manifest.json"
            value=json.loads(target.read_bytes());value['tree']['items'][0][1]['value']=4;target.write_bytes(canonical_bytes(value))
            return result
        with patch.object(type(f.journal),'seal',new=corrupt),self.assertRaises(ValueError):self.finish()
        self.assertTrue((m.attempt_directory(f.owned)/'failed.json').exists())
        self.assertTrue((f.directory/'complete.json').exists());self.assertTrue((f.owned.journal.directory/'complete.json').exists())
        self.assertFalse(f.owned.workload.bound._run._published_outputs)
    def test_second_output_failure_preserves_first_and_no_producer_retry(self):
        f=self.fixture();m=self.m;run=f.owned.workload.bound._run;original=run.write_json
        def write(name,value):
            if name=='journal.json':raise OSError('synthetic second-output interruption')
            return original(name,value)
        with patch.object(run,'write_json',side_effect=write),self.assertRaisesRegex(OSError,'second-output'):self.finish()
        self.assertEqual(set(run._published_outputs),{'binding.json'})
        self.assertTrue((f.directory/'complete.json').exists());self.assertTrue((m.attempt_directory(f.owned)/'failed.json').exists())
        with patch.object(m.publication,'produce',side_effect=AssertionError('closed producer repeated')):
            with self.assertRaises(ValueError):self.finish()

if __name__=='__main__':unittest.main(verbosity=2)
