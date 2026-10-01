"""Pure small synthetic parity/refusal tests; no empirical inputs or owner mocks."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph
from tests.research.onchain_replication.test_neighborhoods import cfg
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods
from tradingagents.research.onchain_replication.provenance import canonical_bytes,thaw

HERE=Path(__file__).resolve().parent
def api():
    assert (HERE/'core.py').is_file(),'leased sampler core missing'
    spec=importlib.util.spec_from_file_location('sampler_core_candidate',HERE/'core.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def population():
    a=graph([[0],[1],[2],[3],[4]],[(0,1,1),(2,1,2),(3,4,3)])
    b=replace(a,start_utc='2024-01-08T00:00:00Z',end_utc='2024-01-15T00:00:00Z',available_at='2024-01-16T00:00:00Z',node_features=a.node_features+2)
    future=replace(a,start_utc='2024-03-01T00:00:00Z',end_utc='2024-03-08T00:00:00Z',available_at='2024-03-09T00:00:00Z')
    return [future,b,a]

POLICY={'schema_version':1,'max_centers':100,'max_direct_weight_bytes':1600,
    'neighborhood':{'schema_version':1,'mode':'array','max_buffer_bytes':1048576,
        'edge_chunk':2,'max_sample_array_bytes':1048576}}

class Tests(unittest.TestCase):
    def test_exact_maintained_sampler_parity_and_chained_draw_evidence(self):
        m=api()
        for seed in (11,23,37,51,71):
            with self.subTest(seed=seed):
                events=[];leases=[];graphs=population();settings=cfg()|{'sample_count':7}
                actual=m.sample(graphs,settings,seed,policy=POLICY,lease=lambda:leases.append(1),checkpoint=events.append)
                expected=sample_neighborhoods(graphs,settings,seed)
                self.assertEqual(actual.identity,expected.identity)
                self.assertEqual(canonical_bytes(actual.records),canonical_bytes(expected.records))
                self.assertEqual(canonical_bytes(actual.rng_state),canonical_bytes(expected.rng_state))
                self.assertEqual(actual.source_hashes,expected.source_hashes)
                for a,b in zip(actual.graphs,expected.graphs,strict=True):
                    self.assertEqual((a.node_ids,a.parent_hash,a.center_id),(b.node_ids,b.parent_hash,b.center_id))
                    for name in ('node_features','edge_index','edge_features'):
                        np.testing.assert_array_equal(getattr(a,name),getattr(b,name))
                self.assertEqual(len(events),7);self.assertGreaterEqual(len(leases),16)
                previous=None
                for i,event in enumerate(events):
                    value=thaw(event);sha=value.pop('sha256')
                    self.assertEqual(value['index'],i);self.assertEqual(value['previous_sha256'],previous)
                    self.assertEqual(sha,m.cache_key(value));previous=sha
                    self.assertEqual(canonical_bytes(value['record']),canonical_bytes(expected.records[i]))
                self.assertEqual(canonical_bytes(events[-1]['rng_after']),canonical_bytes(expected.rng_state))
    def test_weight_capacity_refuses_before_population_array_allocation(self):
        m=api()
        with patch.object(m.np,'ones',side_effect=AssertionError('early weight allocation')),self.assertRaises(ValueError):
            m.sample(population(),cfg(),11,policy=POLICY|{'max_direct_weight_bytes':1},lease=lambda:None,checkpoint=lambda x:None)
    def test_initial_lease_failure_precedes_weight_allocation(self):
        m=api()
        with patch.object(m.np,'ones',side_effect=AssertionError('early weight allocation')),self.assertRaisesRegex(ValueError,'expired'):
            m.sample(population(),cfg(),11,policy=POLICY,lease=lambda:(_ for _ in ()).throw(ValueError('expired')),checkpoint=lambda x:None)
    def test_checkpoint_failure_stops_after_one_draw_and_closes_index(self):
        m=api();indices=[];events=[];original=m.open_array_index
        def index(*args):
            value=original(*args);indices.append(value);return value
        def checkpoint(event):events.append(event);raise RuntimeError('publication failed')
        with patch.object(m,'open_array_index',side_effect=index),self.assertRaisesRegex(RuntimeError,'publication failed'):
            m.sample(population(),cfg(),11,policy=POLICY,lease=lambda:None,checkpoint=checkpoint)
        self.assertEqual(len(events),1);self.assertTrue(all(i.closed for i in indices))
    def test_changed_lease_after_first_checkpoint_refuses_more_draws(self):
        m=api();events=[]
        def lease():
            if events:raise ValueError('owner expired')
        with self.assertRaisesRegex(ValueError,'owner expired'):
            m.sample(population(),cfg(),11,policy=POLICY,lease=lease,checkpoint=events.append)
        self.assertEqual(len(events),1)
    def test_retained_cap_refuses_before_checkpoint_and_hub_is_not_truncated(self):
        m=api()
        for settings,policy in ((cfg(),POLICY|{'neighborhood':POLICY['neighborhood']|{'max_sample_array_bytes':1}}),
                                (cfg()|{'maximum_neighborhood_nodes':1},POLICY)):
            with self.subTest(settings=settings),self.assertRaises(ValueError):
                m.sample(population(),settings,11,policy=policy,lease=lambda:None,
                    checkpoint=lambda x:(_ for _ in ()).throw(AssertionError('invalid sample published')))
    def test_policy_and_callbacks_are_mandatory(self):
        m=api()
        for policy,lease,checkpoint in ((POLICY|{'max_centers':True},lambda:None,lambda x:None),
            (POLICY,None,lambda x:None),(POLICY,lambda:None,None)):
            with self.assertRaises(ValueError):m.sample(population(),cfg(),11,policy=policy,lease=lease,checkpoint=checkpoint)

if __name__=='__main__':unittest.main(verbosity=2)
