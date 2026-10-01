"""Actual admitted dictionary to tiny required-graph MCM; guard mocked."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from tradingagents.research.onchain_replication.neighborhoods import NeighborhoodIndex,node_order_hash
from tradingagents.research.onchain_replication.matching_reference import match_reference

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('mcm_dictionary_fixture',HERE.parent/'dictionary-artifact-route-2026-10-01/test_route.py')
def api():
    assert (HERE/'driver.py').is_file(),'admitted-dictionary MCM driver missing'
    return load('mcm_dictionary_driver',HERE/'driver.py')

class Tests(unittest.TestCase):
    def fixture(self):
        self.m=api();m=self.m;f=base.Tests('test_current_dictionary_reuse_does_not_enter_numerical_workload');self.addCleanup(f.doCleanups)
        with patch.object(base,'api',return_value=m.artifacts),patch.object(m.artifacts,'SOURCES',m.SOURCES):owner=f.fixture()
        self.f=f;self.owner=owner;self.graph_hash=sorted(owner.workload.descriptor['required_graphs'])[0]
        return owner
    def run_driver(self,graph_hash=None):
        f=self.owner
        return self.m.compute(f.owned,f.journal,graph_hash=graph_hash or self.graph_hash,
            sampler_input='sampler_execution',artifact_input='artifact_read',output_input='dictionary_output',
            dictionary_proof_sha256=self.f.receipt['sha256'])
    def test_every_mcm_cell_matches_scalar_and_completed_pairs_are_reused(self):
        f=self.fixture();admitted=self.f.admit();dictionary=admitted.dictionary
        before=f.owned.journal.reservations;actual=self.run_driver();graph=f.workload._graphs[self.graph_hash]
        index=NeighborhoodIndex(graph);expected=np.empty((len(graph.node_ids),len(dictionary.representatives)),dtype=np.float32)
        for center in range(len(graph.node_ids)):
            local=index.neighborhood(center,dictionary.config)
            for motif,representative in enumerate(dictionary.representatives):expected[center,motif]=match_reference(local,representative,f.configs['matching']).score
        np.testing.assert_array_equal(actual['mcm'],expected)
        self.assertEqual(actual['mcm'].dtype,np.float32);self.assertEqual(actual['graph_hash'],self.graph_hash)
        self.assertEqual(actual['node_order_sha256'],node_order_hash(graph.node_ids))
        self.assertEqual(actual['dictionary_provenance']['dictionary_proof'],self.f.receipt)
        self.assertFalse(actual['empirical_admission_verified'])
        after=f.owned.journal.reservations;self.assertGreater(after,before);pair=self.m.serial.pair
        with patch.object(pair.PairSession,'create',side_effect=AssertionError('completed create')),patch.object(pair.PairSession,'resume',side_effect=AssertionError('completed resume')):
            again=self.run_driver()
        np.testing.assert_array_equal(again['mcm'],actual['mcm']);self.assertEqual(after,f.owned.journal.reservations)
    def test_foreign_graph_refuses_before_dictionary_loading(self):
        f=self.fixture();before=f.owned.journal.reservations
        with patch.object(self.m.artifacts,'admit',side_effect=AssertionError('dictionary loaded for foreign graph')),self.assertRaises(ValueError):self.run_driver('f'*64)
        self.assertEqual(before,f.owned.journal.reservations)
    def test_conflicting_dictionary_proof_refuses_before_pair_consumer(self):
        f=self.fixture();before=f.owned.journal.reservations
        (Path(self.f.receipt['path']).parent/'failed.json').write_text('{}')
        with patch.object(self.m.serial,'Serial',side_effect=AssertionError('consumer before proof')),self.assertRaises(ValueError):self.run_driver()
        self.assertEqual(before,f.owned.journal.reservations)
    def test_dictionary_drift_after_first_mcm_pair_stops_next_reservation(self):
        f=self.fixture();original=self.m.serial.Serial.__call__;calls=[]
        def changed(consumer,purpose,*args):
            result=original(consumer,purpose,*args)
            if purpose['kind']=='mcm':
                calls.append(f.owned.journal.reservations);path=f.directory/'checkpoint-000001/array-000000.npy'
                raw=bytearray(path.read_bytes());raw[-1]^=1;path.write_bytes(raw)
            return result
        with patch.object(self.m.serial.Serial,'__call__',new=changed),self.assertRaises(ValueError):self.run_driver()
        self.assertEqual(len(calls),1);self.assertEqual(f.owned.journal.reservations,calls[0])

if __name__=='__main__':unittest.main(verbosity=2)
