"""Exact Eq1 reference score from sparse injective assignments, synthetic only."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph,config
from tradingagents.research.onchain_replication.matching_reference import score_assignment

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sparse_objective',HERE/'sparse_objective.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class SparseScoreTests(unittest.TestCase):
    def compare(self,left,right,pairs):
        pairs=np.array(pairs,dtype=np.int64).reshape(-1,2)
        assignment=np.zeros((len(left.node_ids),len(right.node_ids)),dtype=np.int8)
        for u,i in pairs:assignment[u,i]=1
        expected=score_assignment(left,right,assignment,config())
        for chunk in (1,3,100):
            self.assertEqual(module.score_indices(left,right,pairs,config(),max_buffer_bytes=1024**2,chunk_edges=chunk),expected)

    def test_directed_reciprocal_loops_and_incomplete_assignment(self):
        a=graph([[0],[.7],[1.2]],[(0,1,.4),(1,0,.2),(1,1,.8),(2,0,.5)])
        b=graph([[.1],[.8],[1.1],[2.]],[(0,1,.3),(1,0,.1),(1,1,.6),(2,0,.2)])
        for pairs in ([],[(1,1)],[(2,0),(0,2),(1,1)]):self.compare(a,b,pairs)

    def test_zero_edge_singleton_and_negative_attributes(self):
        self.compare(graph([[0]],[]),graph([[0]],[]),[(0,0)])
        self.compare(graph([[-2],[3]],[]),graph([[4],[-3],[1]],[(0,1,-2)]),[(1,0),(0,1)])

    def test_fixed_random_full_and_partial_assignments(self):
        rng=np.random.default_rng(313)
        for n,m in ((2,5),(5,2),(7,7)):
            a=graph(rng.normal(size=(n,2)).tolist(),[(u,v,float(rng.normal())) for u in range(n) for v in range(n) if rng.random()<.4])
            b=graph(rng.normal(size=(m,2)).tolist(),[(u,v,float(rng.normal())) for u in range(m) for v in range(m) if rng.random()<.4])
            for count in (0,1,min(n,m)):
                self.compare(a,b,list(zip(rng.permutation(n)[:count],rng.permutation(m)[:count])))

    def test_unrepresentable_agreement_domain_is_explicitly_refused(self):
        a=graph([[0.],[1e200]],[]);pairs=np.array([[0,0],[1,1]],dtype=np.int64)
        with self.assertRaises(OverflowError):score_assignment(a,a,np.eye(2,dtype=np.int8),config())
        with self.assertRaisesRegex(ValueError,'agreement arithmetic domain'):
            module.score_indices(a,a,pairs,config(),max_buffer_bytes=1024,chunk_edges=2)

    def test_edge_and_summed_square_envelopes_are_explicit(self):
        pairs=np.array([[0,0],[1,1]],dtype=np.int64)
        a=graph([[0.],[0.]],[(0,1,0.),(1,0,1e200)])
        with self.assertRaisesRegex(ValueError,'agreement arithmetic domain'):
            module.score_indices(a,a,pairs,config(),max_buffer_bytes=1024)
        b=graph([[0.,0.],[1e154,1e154]],[])
        with self.assertRaisesRegex(ValueError,'agreement arithmetic domain'):
            module.score_indices(b,b,pairs,config(),max_buffer_bytes=1024)
        # Empty edge cross-product does not evaluate any edge agreements.
        self.compare(a,graph([[0.],[0.]],[]),pairs)

    def test_invalid_assignment_and_capacity_are_not_bypassed(self):
        a=graph([[0],[1]],[])
        for pairs in (np.array([[0,0],[0,1]]),np.array([[0,0],[1,0]]),np.array([[-1,0]]),np.array([[2,0]]),np.array([[0.,0.]]),np.array([0,0])):
            with self.assertRaises(ValueError):module.score_indices(a,a,pairs,config(),max_buffer_bytes=1024,chunk_edges=2)
        with self.assertRaisesRegex(ValueError,'capacity'):
            module.score_indices(a,a,np.array([[0,0]]),config()|{'max_pair_entries':1},max_buffer_bytes=1024,chunk_edges=2)
        with self.assertRaisesRegex(ValueError,'allowance'):
            module.score_indices(a,a,np.array([[0,0]]),config(),max_buffer_bytes=1,chunk_edges=2)

if __name__=='__main__':unittest.main(verbosity=2)
