"""Synthetic independent set oracle; no empirical bodies."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('hub_edges',HERE/'hub_edges.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class HubTests(unittest.TestCase):
    def oracle(self,edges,n,center):
        nodes={center}
        for u,v in edges.T:
            if u==center:nodes.add(int(v))
            if v==center:nodes.add(int(u))
        return len(nodes),sum(int(u) in nodes and int(v) in nodes for u,v in edges.T)

    def test_directed_reciprocal_duplicate_loop_and_isolate(self):
        edges=np.array([[0,1,0,1,2,1,3,3],[1,0,1,1,1,2,4,3]],dtype=np.int64)
        wanted={i:self.oracle(edges,6,i)[0] for i in range(6)}
        for chunk in (1,3,100):
            rows=module.measure(edges,6,wanted,max_buffer_bytes=1024**2,edge_chunk=chunk)
            self.assertEqual([(r['center'],r['nodes'],r['directed_edges']) for r in rows],[(i,*self.oracle(edges,6,i)) for i in wanted])

    def test_empty_and_large_full_hub_without_truncation(self):
        empty=np.empty((2,0),dtype=np.int64)
        self.assertEqual(module.measure(empty,4,{2:1},max_buffer_bytes=1024**2)[0]['directed_edges'],0)
        n=10002;edges=np.stack([np.zeros(n-1,dtype=np.int64),np.arange(1,n,dtype=np.int64)])
        row=module.measure(edges,n,{0:n},max_buffer_bytes=1024**2,edge_chunk=64)[0]
        self.assertEqual((row['nodes'],row['directed_edges']),(n,n-1))

    def test_fixed_random_set_oracle(self):
        rng=np.random.default_rng(909)
        for n in (1,2,17):
            edges=rng.integers(0,n,size=(2,3*n),dtype=np.int64)
            wanted={i:self.oracle(edges,n,i)[0] for i in range(n)}
            rows=module.measure(edges,n,wanted,max_buffer_bytes=1024**2,edge_chunk=5)
            self.assertEqual([(r['nodes'],r['directed_edges']) for r in rows],[self.oracle(edges,n,i) for i in wanted])

    def test_invalid_and_budget_refusal_before_work(self):
        edges=np.array([[0],[1]],dtype=np.int64)
        for wanted in ({0:1},{2:1},{True:2},{0:3}):
            with self.assertRaises(ValueError):module.measure(edges,2,wanted,max_buffer_bytes=1024**2)
        with patch.object(module.np,'zeros',side_effect=AssertionError('allocation before bound')):
            with self.assertRaisesRegex(ValueError,'numeric allowance'):
                module.measure(edges,2,{0:2},max_buffer_bytes=1)
        with self.assertRaises(ValueError):module.measure(np.array([[0],[-1]]),2,{0:2},max_buffer_bytes=1024**2)

    def test_callback_per_completed_center_and_failure_propagates(self):
        edges=np.array([[0,1],[1,2]],dtype=np.int64);saved=[]
        def checkpoint(row):
            saved.append(row.copy())
            if len(saved)==2:raise RuntimeError('checkpoint unavailable')
        with self.assertRaisesRegex(RuntimeError,'checkpoint unavailable'):
            module.measure(edges,3,{0:2,1:3,2:2},max_buffer_bytes=1024**2,checkpoint=checkpoint)
        self.assertEqual([r['center'] for r in saved],[0,1])

if __name__=='__main__':unittest.main(verbosity=2)
