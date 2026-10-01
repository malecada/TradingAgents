"""Actual temporary owner and durable sampler attempt, with kernel guard mocked."""
import importlib.util
from pathlib import Path
import shutil
import json
import unittest
from unittest.mock import patch
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods
from tradingagents.research.onchain_replication.provenance import file_hash,canonical_bytes

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('sampler_owner_fixture',HERE.parent/'pair-owner-route-2026-09-30/test_ownership.py')
def api():
    assert (HERE/'producer.py').is_file(),'registered sampler producer missing'
    return load('sampler_producer_candidate',HERE/'producer.py')

class Tests(unittest.TestCase):
    def fixture(self,mode=None):
        self.m=api();m=self.m
        class Selected(base.Parent):
            bridge=m.artifacts.consumer.ownership;close_pair=False
            def prepare(self):
                for name in m.SOURCES:
                    target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(ROOT/name,target);self.exp['source_files'][name]=file_hash(target)
                    base.first.git(self.root,'add','--',name)
                policy={'schema_version':1,'kernel':'resident-leased-v1','max_metadata_bytes':65536,'max_attempt_bytes':20_000_000,
                    'limits':{'schema_version':1,'max_centers':10000,'max_direct_weight_bytes':160000,
                        'neighborhood':{'schema_version':1,'mode':'array','max_buffer_bytes':1048576,'edge_chunk':2,'max_sample_array_bytes':1048576}}}
                artifact={'schema_version':1,'max_manifest_bytes':1048576,'max_artifact_bytes':10485760,'max_array_bytes':2097152,'max_journal_events':10}
                if mode=='write_cap':artifact['max_artifact_bytes']=1
                if mode=='reservation_cap':policy['max_attempt_bytes']=1
                if mode=='event_reservation':policy['max_attempt_bytes']=6*policy['max_metadata_bytes']+artifact['max_artifact_bytes']
                self.input('sampler_execution',policy);self.input('artifact_read',artifact)
                self.item.update(sampler_input='sampler_execution',sample_artifact_input='artifact_read')
                self.execution['payload']['representation_jobs']['r'].update(sampler_input='wrong' if mode=='route' else 'sampler_execution',sample_artifact_input='artifact_read')
                super().prepare()
        f=Selected('test_actual_claim_owner_and_old_numerical_anchor_are_distinct')
        self.addCleanup(f.doCleanups);f.setUp();self.f=f;return f
    def produce(self):return self.m.produce(self.f.owned,self.f.journal,sampler_input='sampler_execution',artifact_input='artifact_read')
    def attempt(self):return self.m.attempt_directory(self.f.owned)
    def test_actual_production_publishes_typed_samples_and_exact_completion_proof(self):
        f=self.fixture();result=self.produce();proof=json.loads(Path(result['proof']['path']).read_bytes())
        expected=sample_neighborhoods(f.graphs,dict(f.workload.settings),11)
        self.assertEqual(result['admitted'].samples.identity,expected.identity)
        self.assertEqual(canonical_bytes(result['admitted'].samples.records),canonical_bytes(expected.records))
        self.assertEqual(proof['event']['sha256'],file_hash(f.directory/'event-000000.json'))
        self.assertEqual(proof['component'],dict(result['admitted'].record['component']))
        self.assertEqual(proof['rng_final'],dict(expected.rng_state))
        self.assertEqual(proof['owner']['claim_sha256'],f.run._claim_sha256)
        self.assertEqual(proof['status'],'complete');self.assertEqual(len(proof['draws']),3)
        component=Path(proof['component']['path'])
        actual_bytes=sum(path.stat().st_size for path in component.parent.iterdir())
        self.assertEqual(proof['encoded_artifact_bytes'],actual_bytes)
        self.assertEqual(proof['encoded_event_bytes'],(f.directory/'event-000000.json').stat().st_size)
        self.assertEqual(result['proof']['sha256'],file_hash(Path(result['proof']['path'])))
        self.assertFalse((self.attempt()/'failed.json').exists())
        self.assertEqual(f.owned.journal.reservations,0)
        with patch.object(self.m.core,'sample',side_effect=AssertionError('completed redraw')),self.assertRaises((ValueError,FileExistsError)):self.produce()
    def test_original_sample_arrays_are_released_before_artifact_reload(self):
        import weakref
        self.fixture();refs=[];sample=self.m.core.sample;admit=self.m.artifacts.admit_samples
        def sampled(*args,**kwargs):
            result=sample(*args,**kwargs)
            refs.extend(weakref.ref(getattr(g,name)) for g in result.graphs for name in ('node_features','edge_index','edge_features'))
            return result
        def reload(*args,**kwargs):
            self.assertTrue(refs and all(ref() is None for ref in refs),'original sample arrays still retained during reload')
            return admit(*args,**kwargs)
        with patch.object(self.m.core,'sample',side_effect=sampled),patch.object(self.m.artifacts,'admit_samples',side_effect=reload):self.produce()
    def test_completion_publication_drift_refuses_success(self):
        f=self.fixture();sync=self.m.sync_directory
        def drift(path):
            sync(path)
            if (self.attempt()/'complete.json').exists():f.journal.directory=f.root/'foreign'
        with patch.object(self.m,'sync_directory',side_effect=drift),self.assertRaises(ValueError):self.produce()
        self.assertTrue((self.attempt()/'complete.json').exists());self.assertTrue((self.attempt()/'failed.json').exists())
    def test_guard_loss_during_parent_hash_refuses_attempt_creation(self):
        f=self.fixture();original=self.m.neighborhoods.graph_hash;hit=[]
        def expired(graph):
            result=original(graph);hit.append(1);f.journal.directory=f.root/'foreign';return result
        with patch.object(self.m.neighborhoods,'graph_hash',side_effect=expired),self.assertRaises(ValueError):self.produce()
        self.assertTrue(hit);self.assertFalse(self.attempt().exists())
    def test_partial_attempt_is_never_redrawn(self):
        self.fixture();path=self.attempt();path.mkdir(parents=True);(path/'start.json').write_text('{}')
        before=(path/'start.json').read_bytes()
        with patch.object(self.m.core,'sample',side_effect=AssertionError('partial redraw')),self.assertRaises((ValueError,FileExistsError)):self.produce()
        self.assertEqual((path/'start.json').read_bytes(),before)
    def test_draw_failure_is_retained_and_cannot_be_relaunched(self):
        f=self.fixture()
        with patch.object(self.m.core,'sample',side_effect=RuntimeError('synthetic draw failure')),self.assertRaisesRegex(RuntimeError,'draw failure'):self.produce()
        self.assertTrue((self.attempt()/'start.json').exists());self.assertTrue((self.attempt()/'failed.json').exists())
        self.assertEqual(f.journal.records,[])
        with patch.object(self.m.core,'sample',side_effect=AssertionError('failed redraw')),self.assertRaises((ValueError,FileExistsError)):self.produce()
    def test_write_budget_refuses_before_feature_component_creation(self):
        f=self.fixture('write_cap')
        with self.assertRaises(ValueError):self.produce()
        self.assertFalse((f.directory/'checkpoint-000000').exists())
        self.assertTrue((self.attempt()/'failed.json').exists())
        self.assertEqual(len(list(self.attempt().glob('draw-*.json'))),3)
    def test_registered_route_and_reservation_cap_refuse_before_draw(self):
        for mode in ('route','reservation_cap'):
            with self.subTest(mode=mode):
                self.fixture(mode)
                with patch.object(self.m.core,'sample',side_effect=AssertionError('early draw')),self.assertRaises(ValueError):self.produce()
                self.assertFalse(self.attempt().exists())
    def test_event_publication_allowance_is_reserved_before_draw(self):
        self.fixture('event_reservation')
        with patch.object(self.m.core,'sample',side_effect=AssertionError('event bytes not reserved')),self.assertRaises(ValueError):self.produce()
        self.assertFalse(self.attempt().exists())
    def test_lease_loss_after_first_draw_preserves_checkpoint_and_failure(self):
        f=self.fixture();original=self.m.core.sample
        def wrapped(*args,**kwargs):
            callback=kwargs['checkpoint']
            def lose(event):callback(event);f.journal.directory=f.root/'foreign'
            return original(*args,**(kwargs|{'checkpoint':lose}))
        with patch.object(self.m.core,'sample',side_effect=wrapped),self.assertRaises(ValueError):self.produce()
        self.assertEqual(len(list(self.attempt().glob('draw-*.json'))),1)
        self.assertTrue((self.attempt()/'failed.json').exists());self.assertEqual(f.journal.records,[])

if __name__=='__main__':unittest.main(verbosity=2)
