"""Current producer-proof admission with actual tiny artifacts and mocked guard."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('proof_fixture',HERE.parent/'sampler-producer-2026-10-01/test_producer.py')
def api():
    assert (HERE/'route.py').is_file(),'sampler proof admission missing'
    return load('sampler_proof_admission',HERE/'route.py')

class Tests(unittest.TestCase):
    def fixture(self,limits=None):
        self.m=api();m=self.m;f=base.Tests('test_actual_production_publishes_typed_samples_and_exact_completion_proof')
        self.addCleanup(f.doCleanups)
        owner=base.base.first.OwnershipTests;original_input=owner.input
        def configured(instance,name,value):
            if name=='sampler_execution' and limits is not None:value=value|{'limits':limits}
            return original_input(instance,name,value)
        with patch.object(base,'api',return_value=m.producer),patch.object(m.producer,'SOURCES',m.SOURCES),patch.object(owner,'input',new=configured):f.fixture()
        self.f=f
        if limits is None:self.result=f.produce()
        else:
            # Fault injection: produce valid samples while violating declared
            # sampler limits; the independent proof route must catch it.
            real=m.producer.core.sample
            safe={'schema_version':1,'max_centers':10000,'max_direct_weight_bytes':160000,
                'neighborhood':{'schema_version':1,'mode':'array','max_buffer_bytes':1048576,'edge_chunk':2,'max_sample_array_bytes':1048576}}
            with patch.object(m.producer.core,'sample',side_effect=lambda *a,**kw:real(*a,**(kw|{'policy':safe}))):self.result=f.produce()
        self.proof=Path(self.result['proof']['path']);return f.f
    def admit(self):return self.m.admit(self.f.f.owned,self.f.f.journal,sampler_input='sampler_execution',artifact_input='artifact_read',proof_sha256=file_hash(self.proof))
    def forbidden_arrays(self):return patch.object(self.m.producer.artifacts,'admit_samples',side_effect=AssertionError('sample materialization before proof admission'))
    def test_current_completion_proof_is_admitted_without_redrawing(self):
        f=self.fixture()
        with patch.object(self.m.producer.core,'sample',side_effect=AssertionError('redraw')):
            result=self.admit();result.lease()
        self.assertEqual(result.samples.identity,self.result['admitted'].samples.identity)
        self.assertEqual(result.scope,self.result['admitted'].scope)
        self.assertEqual(result.record['sampler_proof']['sha256'],file_hash(self.proof))
        self.assertEqual(f.owned.journal.reservations,0)
    def test_conflicting_terminal_marker_refuses_before_array_loading(self):
        self.fixture();(self.proof.parent/'failed.json').symlink_to('absent')
        with self.forbidden_arrays(),self.assertRaises(ValueError):self.admit()
    def test_foreign_owner_refuses_even_with_new_expected_proof_hash(self):
        self.fixture();value=json.loads(self.proof.read_bytes());value['owner']['experiment']='foreign'
        self.proof.write_bytes(canonical_bytes(value))
        with self.forbidden_arrays(),self.assertRaises(ValueError):self.admit()
    def test_rehashed_incorrect_rng_draw_refuses_before_array_loading(self):
        self.fixture();value=json.loads(self.proof.read_bytes());path=Path(value['draws'][0]['path'])
        draw=json.loads(path.read_bytes());draw['rng_after']['state']['state']^=1
        draw['sha256']=self.m.producer.core.cache_key({k:v for k,v in draw.items() if k!='sha256'})
        path.write_bytes(canonical_bytes(draw));value['draws'][0]['sha256']=file_hash(path)
        self.proof.write_bytes(canonical_bytes(value))
        with self.forbidden_arrays(),self.assertRaises(ValueError):self.admit()
    def rehash_draws(self,field,value):
        proof=json.loads(self.proof.read_bytes());previous=None
        for i,ref in enumerate(proof['draws']):
            path=Path(ref['path']);draw=json.loads(path.read_bytes())
            if i==0:draw[field]=value(draw[field])
            draw['previous_sha256']=previous
            draw['sha256']=self.m.producer.core.cache_key({k:v for k,v in draw.items() if k!='sha256'})
            path.write_bytes(canonical_bytes(draw));ref['sha256']=file_hash(path);previous=draw['sha256']
        proof['last_draw_sha256']=previous;self.proof.write_bytes(canonical_bytes(proof))
    def test_rehashed_selected_neighborhood_digest_is_checked(self):
        self.fixture();self.rehash_draws('selected_indices_sha256',lambda old:'f'*64)
        with self.assertRaises(ValueError):self.admit()
    def test_rehashed_intermediate_retained_count_is_checked(self):
        self.fixture();self.rehash_draws('retained_array_bytes',lambda old:old+1)
        with self.assertRaises(ValueError):self.admit()
    def test_actual_samples_cannot_bypass_registered_sampler_limits(self):
        safe={'schema_version':1,'max_centers':10000,'max_direct_weight_bytes':160000,
            'neighborhood':{'schema_version':1,'mode':'array','max_buffer_bytes':1048576,'edge_chunk':2,'max_sample_array_bytes':1048576}}
        for limits in (safe|{'max_direct_weight_bytes':1},safe|{'neighborhood':safe['neighborhood']|{'max_sample_array_bytes':1}}):
            with self.subTest(limits=limits):
                self.fixture(limits)
                with self.assertRaises(ValueError):self.admit()
    def test_later_proof_drift_invalidates_receipt(self):
        self.fixture();result=self.admit();path=self.proof.parent/'draw-000000.json';path.write_text('{}')
        with self.assertRaises(ValueError):result.lease()
    def test_proof_drift_after_artifact_loading_refuses_return(self):
        self.fixture();original=self.m.producer.artifacts.admit_samples
        def drift(*args,**kwargs):
            result=original(*args,**kwargs);(self.proof.parent/'failed.json').write_text('{}');return result
        with patch.object(self.m.producer.artifacts,'admit_samples',side_effect=drift),self.assertRaises(ValueError):self.admit()
    def test_proof_drift_during_final_artifact_lease_refuses_return(self):
        self.fixture();original=self.m.producer.artifacts.admit_samples;hit=[]
        def wrapped(*args,**kwargs):
            result=original(*args,**kwargs);check=result.lease
            def drift():
                check();hit.append(True);(self.proof.parent/'failed.json').write_text('{}')
            result.lease=drift
            return result
        with patch.object(self.m.producer.artifacts,'admit_samples',side_effect=wrapped),self.assertRaises(ValueError):self.admit()
        self.assertEqual(hit,[True])

if __name__=='__main__':unittest.main(verbosity=2)
