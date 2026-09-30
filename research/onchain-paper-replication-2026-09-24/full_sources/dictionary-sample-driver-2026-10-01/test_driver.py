"""Real tiny owner/sample/pair composition; no empirical execution or real guard."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from tradingagents.research.onchain_replication.dictionary import fit_dictionary
from tradingagents.research.onchain_replication.matching_identity import graph_identity

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('driver_sample_fixture',HERE.parent/'sample-artifact-route-2026-10-01/test_route.py')
def api():
    assert (HERE/'driver.py').is_file(),'published-sample dictionary driver missing'
    return load('dictionary_sample_driver_candidate',HERE/'driver.py')

class Tests(unittest.TestCase):
    def fixture(self,omit=False):
        self.m=api();m=self.m
        f=base.Tests('test_exact_published_samples_join_current_owner_and_consumer_scope')
        self.addCleanup(f.doCleanups)
        # The actual fixture admits these exact source bytes before ResearchRun.
        # No numerical result or ownership object is substituted.
        sources=m.artifacts.SOURCES if omit else tuple(sorted(set(m.artifacts.SOURCES)|set(m.SOURCES)))
        with patch.object(base,'api',return_value=m.artifacts),patch.object(m.artifacts,'SOURCES',sources):
            f.fixture()
        self.f=f;return f.f
    def run_driver(self):
        return self.m.fit(self.f.f.owned,self.f.f.journal,artifact_input='artifact_read',
            event_index=0,event_sha256=base.file_hash(self.f.event))
    def test_full_dictionary_scalar_parity_and_completed_pair_reuse(self):
        f=self.fixture();actual=self.run_driver()
        from tradingagents.research.onchain_replication import dictionary as scalar
        matrices=[];cluster=scalar.cluster_medoids
        def capture(matrix,k):matrices.append(matrix.copy());return cluster(matrix,k)
        with patch.object(scalar,'cluster_medoids',side_effect=capture):
            expected=fit_dictionary(self.f.samples,f.configs['matching'],dict(f.workload.settings))
        self.assertEqual(len(matrices),len(actual['matrices']))
        for expected_matrix,block in zip(matrices,actual['matrices'],strict=True):
            np.testing.assert_array_equal(block['matrix'],expected_matrix)
        d=actual['dictionary']
        self.assertEqual(d.memberships,expected.memberships)
        self.assertEqual(d.hierarchy,expected.hierarchy)
        self.assertEqual([graph_identity(g) for g in d.representatives],
            [graph_identity(g) for g in expected.representatives])
        self.assertEqual(actual['workload_sha256'],f.workload.sample_scope(self.f.samples))
        self.assertFalse(actual['empirical_admission_verified'])
        reservations=f.owned.journal.reservations
        self.assertGreater(reservations,0)
        pair=self.m.artifacts.consumer.serial.pair
        with patch.object(pair.PairSession,'create',side_effect=AssertionError('completed create')),\
             patch.object(pair.PairSession,'resume',side_effect=AssertionError('completed resume')):
            replay=self.run_driver()
        self.assertEqual(f.owned.journal.reservations,reservations)
        self.assertEqual(d.identity,replay['dictionary'].identity)
        for a,b in zip(actual['matrices'],replay['matrices'],strict=True):
            np.testing.assert_array_equal(a['matrix'],b['matrix'])
    def test_changed_sample_after_first_pair_refuses_next_reservation(self):
        f=self.fixture();original=self.m.artifacts.consumer.dictionary_consumer;calls=[]
        def instrument(*args,**kwargs):
            consumer=original(*args,**kwargs)
            def score(*values):
                result=consumer(*values);calls.append(f.owned.journal.reservations)
                member=f.directory/'checkpoint-000000'/'array-000000.npy'
                raw=bytearray(member.read_bytes());raw[-1]^=1;member.write_bytes(raw)
                return result
            return score
        with patch.object(self.m.artifacts.consumer,'dictionary_consumer',side_effect=instrument),self.assertRaises(ValueError):
            self.run_driver()
        self.assertEqual(len(calls),1)
        self.assertEqual(f.owned.journal.reservations,calls[0])
    def test_unregistered_driver_refuses_before_pair_reservation(self):
        f=self.fixture(omit=True)
        with self.assertRaises(ValueError):self.run_driver()
        self.assertEqual(f.owned.journal.reservations,0)
    def test_invalid_sample_event_refuses_before_dictionary_workload(self):
        f=self.fixture();self.f.event.write_text('{}')
        with patch.object(self.m.workload,'fit',side_effect=AssertionError('workload before admission')),self.assertRaises(ValueError):
            self.run_driver()
        self.assertEqual(f.owned.journal.reservations,0)

if __name__=='__main__':unittest.main(verbosity=2)
