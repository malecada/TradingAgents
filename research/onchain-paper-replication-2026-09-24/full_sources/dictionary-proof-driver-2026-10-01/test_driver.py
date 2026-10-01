"""Actual tiny producer proof to dictionary, with guard observations mocked."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from tradingagents.research.onchain_replication.dictionary import fit_dictionary
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.provenance import file_hash,thaw

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('dictionary_proof_fixture',HERE.parent/'sampler-proof-route-2026-10-01/test_route.py')
def api():
    assert (HERE/'driver.py').is_file(),'proof-enforcing dictionary driver missing'
    return load('dictionary_proof_driver',HERE/'driver.py')

class Tests(unittest.TestCase):
    def fixture(self,omit=False):
        self.m=api();m=self.m;f=base.Tests('test_current_completion_proof_is_admitted_without_redrawing')
        self.addCleanup(f.doCleanups)
        admitted=m.proof.SOURCES if omit else m.SOURCES
        with patch.object(base,'api',return_value=m.proof),patch.object(m.proof,'SOURCES',admitted):f.fixture()
        self.f=f;return f.f.f
    def run_driver(self):
        owner=self.f.f.f
        return self.m.fit(owner.owned,owner.journal,sampler_input='sampler_execution',
            artifact_input='artifact_read',proof_sha256=file_hash(self.f.proof))
    def test_actual_dictionary_parity_provenance_and_completed_pair_reuse(self):
        f=self.fixture();actual=self.run_driver()
        from tradingagents.research.onchain_replication import dictionary as scalar
        matrices=[];cluster=scalar.cluster_medoids
        def capture(matrix,k):matrices.append(matrix.copy());return cluster(matrix,k)
        with patch.object(scalar,'cluster_medoids',side_effect=capture):
            expected=fit_dictionary(self.f.result['admitted'].samples,f.configs['matching'],dict(f.workload.settings))
        self.assertEqual(len(matrices),len(actual['matrices']))
        for matrix,block in zip(matrices,actual['matrices'],strict=True):np.testing.assert_array_equal(matrix,block['matrix'])
        d=actual['dictionary'];self.assertEqual(d.memberships,expected.memberships);self.assertEqual(d.hierarchy,expected.hierarchy)
        self.assertEqual([graph_identity(g) for g in d.representatives],[graph_identity(g) for g in expected.representatives])
        proof=actual['sample_provenance']['sampler_proof']
        self.assertEqual(proof,{'path':str(self.f.proof),'sha256':file_hash(self.f.proof)})
        self.assertEqual(actual['sample_provenance']['sample_artifact'],thaw(self.f.result['admitted'].record))
        self.assertFalse(actual['empirical_admission_verified'])
        reservations=f.owned.journal.reservations;self.assertGreater(reservations,0)
        pair=self.m.artifacts.consumer.serial.pair
        with patch.object(pair.PairSession,'create',side_effect=AssertionError('completed create')),patch.object(pair.PairSession,'resume',side_effect=AssertionError('completed resume')):
            replay=self.run_driver()
        self.assertEqual(reservations,f.owned.journal.reservations)
        self.assertEqual(d.identity,replay['dictionary'].identity)
        self.assertEqual(actual['sample_provenance'],replay['sample_provenance'])
    def test_conflicting_proof_refuses_before_workload_or_pair_reservation(self):
        f=self.fixture();(self.f.proof.parent/'failed.json').write_text('{}')
        with patch.object(self.m.workload,'fit',side_effect=AssertionError('workload before proof')),self.assertRaises(ValueError):self.run_driver()
        self.assertEqual(f.owned.journal.reservations,0)
    def test_partial_proof_refuses_before_workload_or_pair_reservation(self):
        f=self.fixture();(self.f.proof.parent/'draw-000000.json').unlink()
        with patch.object(self.m.workload,'fit',side_effect=AssertionError('workload before proof')),self.assertRaises(ValueError):self.run_driver()
        self.assertEqual(f.owned.journal.reservations,0)
    def test_proof_drift_after_first_pair_refuses_further_work(self):
        f=self.fixture();original=self.m.artifacts.consumer.dictionary_consumer;calls=[]
        def wrapped(*args,**kwargs):
            consumer=original(*args,**kwargs)
            def score(*values):
                result=consumer(*values);calls.append(f.owned.journal.reservations)
                (self.f.proof.parent/'failed.json').write_text('{}');return result
            return score
        with patch.object(self.m.artifacts.consumer,'dictionary_consumer',side_effect=wrapped),self.assertRaises(ValueError):self.run_driver()
        self.assertEqual(len(calls),1);self.assertEqual(f.owned.journal.reservations,calls[0])
    def test_unregistered_driver_refuses_before_reservation(self):
        f=self.fixture(omit=True)
        with self.assertRaises(ValueError):self.run_driver()
        self.assertEqual(f.owned.journal.reservations,0)

if __name__=='__main__':unittest.main(verbosity=2)
