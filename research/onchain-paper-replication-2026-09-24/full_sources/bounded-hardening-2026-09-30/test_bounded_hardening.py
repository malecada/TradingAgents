"""Synthetic exact hardening oracle; no empirical inputs or capacity changes."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from tradingagents.research.onchain_replication.matching_reference import harden

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('bounded_hardening',HERE/'bounded_hardening.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class HardeningTests(unittest.TestCase):
    def check(self,matrix,chunk=3):
        before=matrix.copy();expected=harden(matrix)
        pairs=module.harden_indices(matrix,max_buffer_bytes=1024**2,chunk_entries=chunk)
        actual=np.zeros(matrix.shape,dtype=np.int8)
        for row,column in pairs:actual[row,column]=1
        np.testing.assert_array_equal(actual,expected);np.testing.assert_array_equal(matrix,before)
        self.assertEqual(pairs.dtype,np.int64);self.assertEqual(pairs.shape,(min(matrix.shape),2))
        return pairs

    def test_rectangular_ties_negative_and_zero(self):
        for shape in ((1,1),(2,5),(5,2),(7,7),(0,7),(7,0)):
            for value in (0.,-3.,1.):
                pairs=self.check(np.full(shape,value))
                np.testing.assert_array_equal(pairs,np.array([(i,i) for i in range(min(shape))],dtype=np.int64).reshape(-1,2))
        self.check(np.array([[0,-2,8],[8,5,1],[1,8,2]],dtype=float))

    def test_random_dtype_stride_and_chunk_parity(self):
        rng=np.random.default_rng(729)
        for dtype in (np.float64,np.float32,np.int64):
            matrix=rng.integers(-5,6,size=(13,17)).astype(dtype)
            for value in (matrix,matrix.T,matrix[::-1,::2],matrix[:,::-1]):
                for chunk in (1,11,1000):self.check(value,chunk)

    def test_input_finite_and_budget_rejections_before_output(self):
        for matrix in (np.array([[np.nan]]),np.array([[np.inf]]),np.array([[-np.inf]]),np.ones(3),np.array([['x']])):
            with self.assertRaises(ValueError):module.harden_indices(matrix,max_buffer_bytes=1024,chunk_entries=3)
        for kw in ({'max_buffer_bytes':1,'chunk_entries':3},{'max_buffer_bytes':True,'chunk_entries':3},{'max_buffer_bytes':1024,'chunk_entries':True}):
            with self.assertRaises(ValueError):module.harden_indices(np.ones((2,3)),**kw)

    def test_mapped_input_and_above_former_pair_limit_without_dense_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'matrix.npy'
            matrix=np.lib.format.open_memmap(path,mode='w+',shape=(2,2_000_001),dtype=np.float64)
            matrix[:]=0;matrix[0,-1]=1;matrix[1,0]=1
            try:
                pairs=module.harden_indices(matrix,max_buffer_bytes=65536,chunk_entries=256)
                np.testing.assert_array_equal(pairs,[[0,2_000_000],[1,0]])
            finally:matrix._mmap.close()

    def test_float64_rounding_ties_and_signed_zero(self):
        self.check(np.array([[2**63,2**63+1],[2**63+4096,2**63]],dtype=np.uint64),1)
        self.check(np.array([[2**62+1,2**62],[2**62-1,2**62+1024]],dtype=np.int64),1)
        self.check(np.array([[-0.,0.,-0.],[0.,-0.,0.]]),1)

    def test_literal_greedy_selection_order(self):
        pairs=self.check(np.array([[.2,.5],[.8,.1]]),1)
        np.testing.assert_array_equal(pairs,[[1,0],[0,1]])

    def test_exact_numeric_allowance_and_preallocation_refusal(self):
        matrix=np.arange(10,dtype=float).reshape(2,5)
        allowance=48*2+64*3
        with patch.object(module.np,'empty',side_effect=AssertionError('allocated before refusal')):
            with self.assertRaisesRegex(ValueError,'allowance'):
                module.harden_indices(matrix,max_buffer_bytes=allowance-1,chunk_entries=3)
        actual=module.harden_indices(matrix,max_buffer_bytes=allowance,chunk_entries=3)
        np.testing.assert_array_equal(actual,[[1,4],[0,3]])

    def test_no_full_matrix_copy_or_dense_assignment(self):
        matrix=np.arange(63,dtype=float).reshape(7,9);expected=harden(matrix)
        original_empty=np.empty;original_zeros=np.zeros
        def bounded(factory,shape,*a,**k):
            if isinstance(shape,tuple):
                self.assertNotEqual(shape,matrix.shape)
            return factory(shape,*a,**k)
        with patch.object(module.np,'empty',side_effect=lambda shape,*a,**k:bounded(original_empty,shape,*a,**k)),patch.object(module.np,'zeros',side_effect=lambda shape,*a,**k:bounded(original_zeros,shape,*a,**k)):
            pairs=module.harden_indices(matrix,max_buffer_bytes=1024**2,chunk_entries=5)
        actual=np.zeros(matrix.shape,dtype=np.int8)
        for a,b in pairs:actual[a,b]=1
        np.testing.assert_array_equal(actual,expected)

if __name__=='__main__':unittest.main(verbosity=2)
