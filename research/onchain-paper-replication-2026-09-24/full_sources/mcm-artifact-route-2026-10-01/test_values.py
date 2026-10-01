"""Tiny value validation and immutable buffer contract checks."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

def api():
    path=Path(__file__).with_name('route.py');spec=importlib.util.spec_from_file_location('mcm_value_route',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert hasattr(m,'immutable_matrix'),'immutable MCM conversion missing'
    return m

class Tests(unittest.TestCase):
    def test_values_bounds_and_independent_immutable_copy(self):
        m=api();source=np.linspace(0,1,35,dtype=np.float32).reshape(5,7);expected=source.copy()
        matrix=m.immutable_matrix(source,2);source[:]=0
        np.testing.assert_array_equal(matrix,expected)
        with self.assertRaises(ValueError):matrix.setflags(write=True)
        with self.assertRaises(ValueError):matrix.view().setflags(write=True)
        with self.assertRaises(ValueError):matrix.base.setflags(write=True)
        for value in (float('nan'),float('inf'),-0.01,1.01):
            bad=expected.copy();bad[-1,-1]=value
            with self.subTest(value=value),self.assertRaises(ValueError):m.immutable_matrix(bad,2)
    def test_record_and_storage_are_nonassignable_and_layout_lease_is_pinned(self):
        m=api();matrix=m.immutable_matrix(np.zeros((2,2),dtype=np.float32),1)
        result=m.Admitted(matrix,{'stage':'tiny'},lambda:None)
        with self.assertRaises(AttributeError):result.mcm=np.ones((2,2),dtype=np.float32)
        with self.assertRaises(AttributeError):result.record={}
        with self.assertRaises(AttributeError):result._mcm=np.ones((2,2),dtype=np.float32)
        matrix.strides=(0,4)
        with self.assertRaises(ValueError):result.lease()

if __name__=='__main__':unittest.main(verbosity=2)
