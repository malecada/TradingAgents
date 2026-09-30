"""Synthetic byte-parity and interrupted-step checks for isolated normalization."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from scipy.special import logsumexp
spec=importlib.util.spec_from_file_location('normalization',Path(__file__).with_name('normalization.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class NormalizationTests(unittest.TestCase):
    def test_reference_bytes_at_every_chunk_boundary(self):
        for n,k in ((1,1),(1,7),(7,1),(17,6),(257,17)):
            rng=np.random.default_rng(23)
            for q in (np.abs(rng.standard_normal((n,k))),np.zeros((n,k)),np.round(np.abs(rng.standard_normal((n,k))))):
                for beta in (1.,1000.):
                    expected=beta*q
                    expected-=logsumexp(expected,axis=1,keepdims=True)
                    expected-=logsumexp(expected,axis=0,keepdims=True)
                    expected=np.exp(expected)
                    for entries in (max(k,2*n),max(k,2*n)*3):
                        state=m.create(q,beta,max_chunk_entries=entries,max_state_bytes=8*n*k)
                        phases=set()
                        while state['phase']!='done':
                            phases.add(state['phase'])
                            self.assertEqual(m.advance(state,max_blocks=1),1)
                            self.assertTrue(state['safe'])
                        self.assertEqual(state['matrix'].tobytes(),expected.tobytes())
                        self.assertEqual(phases,{'scale','rows','columns','exp'})
    def test_layout_and_capacity_rejected_before_output_allocation(self):
        q=np.ones((7,3))
        with patch.object(m.np,'zeros',side_effect=AssertionError('premature allocation')):
            for kwargs in ({'max_state_bytes':1,'max_chunk_entries':100}, {'max_state_bytes':1000,'max_chunk_entries':2}):
                with self.assertRaises(ValueError):m.create(q,1.,**kwargs)
            with self.assertRaises(ValueError):m.create(np.asfortranarray(q),1.,max_state_bytes=1000,max_chunk_entries=100)
    def test_interrupted_write_poisons_scratch(self):
        state=m.create(np.ones((7,3)),1.,max_chunk_entries=14,max_state_bytes=1000)
        original=m.np.multiply
        def interrupted(*args,**kwargs):
            original(*args,**kwargs)
            raise KeyboardInterrupt('after mutation')
        with patch.object(m.np,'multiply',side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):m.advance(state,max_blocks=1)
        self.assertFalse(state['safe'])
        with self.assertRaises(ValueError):m.advance(state,max_blocks=1)
    def test_inputs_remain_unchanged(self):
        q=np.arange(21,dtype=np.float64).reshape(7,3);before=q.tobytes()
        state=m.create(q,2.,max_chunk_entries=14,max_state_bytes=1000)
        while state['phase']!='done':m.advance(state,max_blocks=3)
        self.assertEqual(q.tobytes(),before)

if __name__=='__main__':unittest.main()
