"""Actual tiny registered dictionary publication; kernel guard mocked."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tradingagents.research.onchain_replication.provenance import file_hash,thaw
from tradingagents.research.onchain_replication.serialization import dictionary_from_record
from tradingagents.research.onchain_replication.dictionary import fit_dictionary
from tradingagents.research.onchain_replication.matching_identity import graph_identity

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('dictionary_publication_fixture',HERE.parent/'dictionary-proof-driver-2026-10-01/test_driver.py')
def api():
    assert (HERE/'publication.py').is_file(),'dictionary publication missing'
    return load('dictionary_publication',HERE/'publication.py')

class Tests(unittest.TestCase):
    def fixture(self,mode=None):
        self.m=api();m=self.m
        f=base.Tests('test_actual_dictionary_parity_provenance_and_completed_pair_reuse');self.addCleanup(f.doCleanups)
        owner=base.base.base.base.first.OwnershipTests;original=owner.input
        policy={'schema_version':1,'max_metadata_bytes':262144,'max_manifest_bytes':1048576,
            'max_artifact_bytes':10485760,'max_attempt_bytes':20_000_000,'max_sample_matrix_array_bytes':10_000_000}
        if mode=='artifact_cap':policy['max_artifact_bytes']=1
        if mode=='reservation_cap':policy['max_attempt_bytes']=1
        if mode=='array_cap':policy['max_sample_matrix_array_bytes']=1
        def configured(instance,name,value):
            if name=='artifact_read' and mode=='event_cap':value=value|{'max_journal_events':1}
            if name=='plan':
                original(instance,'dictionary_output',policy)
                value['producers']['p']['dictionary_output_input']='dictionary_output'
            if name=='execution_job':value['payload']['representation_jobs']['r']['dictionary_output_input']='wrong' if mode=='route' else 'dictionary_output'
            return original(instance,name,value)
        with patch.object(base,'api',return_value=m.driver),patch.object(m.driver,'SOURCES',m.SOURCES),patch.object(owner,'input',new=configured):f.fixture()
        self.f=f;return f.f.f.f
    def run_publication(self):
        f=self.f.f.f.f
        return self.m.produce(f.owned,f.journal,sampler_input='sampler_execution',artifact_input='artifact_read',
            proof_sha256=file_hash(self.f.f.proof),output_input='dictionary_output')
    def attempt(self):return self.m.attempt_directory(self.f.f.f.f.owned)
    def test_actual_dictionary_publication_has_exact_provenance_sizes_and_scalar_parity(self):
        f=self.fixture();result=self.run_publication();proof=json.loads(Path(result['path']).read_bytes())
        self.assertEqual(result['sha256'],file_hash(Path(result['path'])))
        self.assertEqual(proof['status'],'complete');self.assertFalse(proof['resumable'])
        event_path=f.directory/'event-000001.json';event=json.loads(event_path.read_bytes())
        self.assertEqual(event['stage'],'dictionary_complete')
        self.assertEqual(event['context']['sample_provenance']['sampler_proof'],{'path':str(self.f.f.proof),'sha256':file_hash(self.f.f.proof)})
        path=f.directory/event['path'];reader=self.m.producer.artifacts.reader
        payload=reader.read_component(path,event['sha256'],event['binding'],root=f.root,
            max_manifest_bytes=1048576,max_artifact_bytes=10485760,max_array_bytes=10_000_000,lease=f.owned.lease)
        actual=dictionary_from_record(payload)
        expected=fit_dictionary(self.f.f.result['admitted'].samples,f.configs['matching'],dict(f.workload.settings))
        self.assertEqual(actual.memberships,expected.memberships);self.assertEqual(actual.hierarchy,expected.hierarchy)
        self.assertEqual([graph_identity(g) for g in actual.representatives],[graph_identity(g) for g in expected.representatives])
        self.assertEqual(actual.identity,proof['dictionary_identity'])
        self.assertEqual(proof['encoded_artifact_bytes'],sum(p.stat().st_size for p in path.parent.iterdir()))
        self.assertEqual(proof['encoded_event_bytes'],event_path.stat().st_size)
        self.assertEqual(proof['event'],{'path':str(event_path),'sha256':file_hash(event_path)})
        self.assertEqual(proof['component'],{'path':str(path),'sha256':file_hash(path)})
        start=json.loads(Path(proof['start']['path']).read_bytes())
        self.assertEqual(start['reserved_encoded_bytes'],4*262144+10485760)
        before=f.owned.journal.reservations
        with patch.object(self.m.driver,'fit',side_effect=AssertionError('completed refit')),self.assertRaises((ValueError,FileExistsError)):self.run_publication()
        self.assertEqual(before,f.owned.journal.reservations)
    def test_bad_route_and_reservation_or_array_budget_refuse_before_fitting(self):
        for mode in ('route','reservation_cap','array_cap'):
            with self.subTest(mode=mode):
                self.fixture(mode)
                with patch.object(self.m.driver,'fit',side_effect=AssertionError('fit before admission')),self.assertRaises(ValueError):self.run_publication()
                self.assertFalse(self.attempt().exists())
    def test_artifact_cap_preserves_failed_attempt_before_feature_write(self):
        f=self.fixture('artifact_cap')
        with self.assertRaises(ValueError):self.run_publication()
        self.assertTrue((self.attempt()/'start.json').exists());self.assertTrue((self.attempt()/'failed.json').exists())
        self.assertEqual(len(f.journal.records),1);self.assertFalse((f.directory/'checkpoint-000001').exists())
        with patch.object(self.m.driver,'fit',side_effect=AssertionError('failed refit')),self.assertRaises((ValueError,FileExistsError)):self.run_publication()
    def test_partial_attempt_is_never_refitted(self):
        self.fixture();self.attempt().mkdir(parents=True);(self.attempt()/'start.json').write_text('{}')
        with patch.object(self.m.driver,'fit',side_effect=AssertionError('partial refit')),self.assertRaises((ValueError,FileExistsError)):self.run_publication()
        self.assertEqual((self.attempt()/'start.json').read_text(),'{}')
    def test_registered_one_event_cap_refuses_before_fit_or_reservation(self):
        f=self.fixture('event_cap')
        with patch.object(self.m.driver,'fit',side_effect=AssertionError('fit despite registered event cap')),self.assertRaises(ValueError):self.run_publication()
        self.assertFalse(self.attempt().exists());self.assertEqual(len(f.journal.records),1)
    def test_dictionary_component_drift_during_completion_refuses_success(self):
        for kind in ('array','manifest','foreign'):
            with self.subTest(kind=kind):
                f=self.fixture();sync=self.m.sync_directory;hit=[]
                def changed(path):
                    sync(path)
                    if (self.attempt()/'complete.json').exists() and not hit:
                        hit.append(True);component=f.directory/'checkpoint-000001'
                        if kind=='array':
                            target=component/'array-000000.npy';raw=bytearray(target.read_bytes());raw[-1]^=1;target.write_bytes(raw)
                        elif kind=='manifest':
                            target=component/'manifest.json';target.write_bytes(target.read_bytes()+b' ')
                        else:(component/'foreign').write_text('unexpected')
                with patch.object(self.m,'sync_directory',side_effect=changed),self.assertRaises(ValueError):self.run_publication()
                self.assertEqual(hit,[True]);self.assertTrue((self.attempt()/'failed.json').exists())
    def test_sampler_drift_after_fit_refuses_dictionary_write(self):
        f=self.fixture();original=self.m.driver.fit
        def changed(*args,**kwargs):
            result=original(*args,**kwargs);(self.f.f.proof.parent/'failed.json').write_text('{}');return result
        with patch.object(self.m.driver,'fit',side_effect=changed),self.assertRaises(ValueError):self.run_publication()
        self.assertEqual(len(f.journal.records),1);self.assertTrue((self.attempt()/'failed.json').exists())
    def test_completion_lease_failure_preserves_conflicting_markers(self):
        f=self.fixture();sync=self.m.sync_directory
        def changed(path):
            sync(path)
            if (self.attempt()/'complete.json').exists():f.journal.directory=f.root/'foreign'
        with patch.object(self.m,'sync_directory',side_effect=changed),self.assertRaises(ValueError):self.run_publication()
        self.assertTrue((self.attempt()/'complete.json').exists());self.assertTrue((self.attempt()/'failed.json').exists())

if __name__=='__main__':unittest.main(verbosity=2)
