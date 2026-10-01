"""Tiny exact numerical and allocation-failure checks; no empirical admission."""
import importlib.util
from pathlib import Path
from dataclasses import replace
import unittest
from unittest.mock import patch
import weakref
import numpy as np
from tradingagents.research.onchain_replication.dictionary import dictionary_hash,reorder_dictionary

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('array_mcm_oracle_fixture',HERE.parent/'pair-workload-2026-09-30/test_workload.py')
POLICY={'schema_version':1,'max_buffer_bytes':100000,'edge_chunk':2,'max_output_bytes':56,'max_numeric_bytes':100056}
def api():
    assert (HERE/'kernel.py').is_file(),'bounded MCM kernel missing'
    return load('array_mcm_kernel',HERE/'kernel.py')

class Tests(unittest.TestCase):
    def setUp(self):
        self.m=api();self.f=base.Tests();self.f.setUp()
        self.d=self.f.fit(base.Scores(self.f.match))['dictionary']
        self.leases=0
    def lease(self):self.leases+=1
    def run_kernel(self,callback=None,policy=None,lease=None,dictionary=None):
        return self.m.mcm(self.f.g,dictionary or self.d,self.f.match,**self.f.kw,
            score_pair=callback or base.Scores(self.f.match),policy=POLICY if policy is None else policy,
            lease=self.lease if lease is None else lease)
    def test_every_cell_purpose_and_order_matches_existing_scalar_workload(self):
        for d in (self.d,reorder_dictionary(self.d,[1,0])):
            with self.subTest(dictionary=d.identity):
                expected_scores=base.Scores(self.f.match);actual_scores=base.Scores(self.f.match)
                expected=self.f.m.mcm(self.f.g,d,self.f.match,**self.f.kw,score_pair=expected_scores)
                actual=self.run_kernel(actual_scores,dictionary=d)
                np.testing.assert_array_equal(actual['mcm'],expected)
                self.assertEqual(actual['mcm'].dtype,np.float32)
                self.assertEqual(actual_scores.asked,expected_scores.asked)
                self.assertEqual(actual['completed_rows'],7);self.assertEqual(actual['completed_cells'],14)
                self.assertEqual(actual['output_bytes'],56)
                self.assertEqual(actual['workload_sha256'],expected_scores.asked[0]['workload_sha256'])
                self.assertGreaterEqual(self.leases,2*14+2*7+2)
    def test_caps_and_missing_lease_refuse_before_index_or_output_allocation(self):
        bad=[POLICY|{'max_output_bytes':55},POLICY|{'max_numeric_bytes':100055},
             POLICY|{'max_buffer_bytes':True},POLICY|{'edge_chunk':0},POLICY|{'extra':1}]
        with patch.object(self.m,'ArrayNeighborhoodIndex',side_effect=AssertionError('index before preflight')):
            for policy in bad:
                with self.subTest(policy=policy),self.assertRaises(ValueError):self.run_kernel(policy=policy)
            with self.assertRaises(ValueError):self.run_kernel(lease=False)
    def test_full_neighborhood_capacity_refuses_without_truncation_and_closes_index(self):
        d=replace(self.d,config=dict(self.d.config)|{'maximum_neighborhood_nodes':1},identity='')
        d=replace(d,identity=dictionary_hash(d));instances=[];original=self.m.ArrayNeighborhoodIndex
        def track(*a,**kw):
            obj=original(*a,**kw);instances.append(obj);return obj
        with patch.object(self.m,'ArrayNeighborhoodIndex',side_effect=track),self.assertRaisesRegex(ValueError,'no truncation'):
            self.run_kernel(lambda *a:self.fail('pair after capacity failure'),dictionary=d)
        self.assertTrue(instances[0].closed);self.assertEqual(instances[0].orders,[])
    def test_partial_row_failure_closes_and_zero_replay_has_no_missing_cells(self):
        scores=base.Scores(self.f.match,fail=1,zero=True);instances=[];original=self.m.ArrayNeighborhoodIndex
        def track(*a,**kw):
            obj=original(*a,**kw);instances.append(obj);return obj
        with patch.object(self.m,'ArrayNeighborhoodIndex',side_effect=track),self.assertRaises(RuntimeError):self.run_kernel(scores)
        self.assertTrue(instances[0].closed);self.assertEqual(len(scores.saved),1)
        scores.fail=None;scores.asked=[];out=self.run_kernel(scores)
        np.testing.assert_array_equal(out['mcm'],np.zeros((7,2),dtype=np.float32))
        self.assertEqual(out['completed_cells'],14);self.assertEqual(len(scores.computed),14)
    def test_post_pair_lease_failure_stops_before_next_pair_and_closes(self):
        scores=base.Scores(self.f.match);instances=[];original=self.m.ArrayNeighborhoodIndex
        def track(*a,**kw):
            obj=original(*a,**kw);instances.append(obj);return obj
        def lease():
            if scores.computed:raise ValueError('revoked lease')
        with patch.object(self.m,'ArrayNeighborhoodIndex',side_effect=track),self.assertRaisesRegex(ValueError,'revoked'):
            self.run_kernel(scores,lease=lease)
        self.assertEqual(len(scores.computed),1);self.assertTrue(instances[0].closed)
    def test_previous_local_is_released_before_next_neighborhood(self):
        original=self.m.ArrayNeighborhoodIndex.neighborhood;refs=[]
        def track(index,*a,**kw):
            self.assertTrue(all(ref() is None for ref in refs))
            g=original(index,*a,**kw);refs.append(weakref.ref(g));return g
        with patch.object(self.m.ArrayNeighborhoodIndex,'neighborhood',new=track):self.run_kernel()
        self.assertEqual(len(refs),7);self.assertTrue(all(ref() is None for ref in refs))
    def test_invalid_score_or_purpose_never_returns_partial_output(self):
        for value in (-1.,1.1,float('nan'),True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.run_kernel(lambda p,a,b:{'purpose_sha256':base.cache_key(p),'score':value})
        with self.assertRaises(ValueError):self.run_kernel(lambda p,a,b:{'purpose_sha256':'f'*64,'score':.2})

if __name__=='__main__':unittest.main(verbosity=2)
