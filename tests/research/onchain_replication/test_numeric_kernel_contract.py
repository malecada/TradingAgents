"""Bounded synthetic numeric helper contract; no graph/Owner/Run imports."""
import math
import unittest
import numpy as np
from tradingagents.research.onchain_replication.matching_numeric_kernel import fill_agreement


def frozen(value, dtype=np.float64):
    a = np.asarray(value, dtype=dtype)
    return np.frombuffer(a.tobytes(), dtype=dtype).reshape(a.shape)


def scalar(a, b):
    return math.exp(-math.fsum((float(x)-float(y))**2 for x, y in zip(a, b, strict=True))/len(a))


class NumericKernelContract(unittest.TestCase):
    def fixture(self):
        return (frozen([[0., 0.], [1., 2.], [-1., -2.]]),
                frozen([[0., 0.], [-1., -2.], [1., 2.]]),
                frozen([0, 1, 2, 1], np.int64), frozen([0, 0, 2, 1], np.int64))

    def test_literal_and_slice(self):
        a,b,i,j=self.fixture();out=np.full(6, -7.)
        self.assertTrue(fill_agreement(a,b,i,j,out,0,4))
        np.testing.assert_allclose(out[:4], [1.,0.0820849986238988,0.00004539992976248485,0.00004539992976248485],rtol=1e-6,atol=1e-8)
        np.testing.assert_array_equal(out[4:], [-7.,-7.])
        out[:]=-7;self.assertTrue(fill_agreement(a,b,i,j,out,1,3))
        np.testing.assert_array_equal(out[[0,3,4,5]], [-7.]*4)

    def test_widths_directions_ties_extremes(self):
        for width in (2,4):
            a=frozen([[256.]*width,[-256.]*width,[1e-100]*width,[0.]*width,[1.,-1.]*(width//2)])
            b=frozen([[0.]*width,[256.]*width,[-256.]*width,[1e-100]*width,[1.,-1.]*(width//2)])
            i=frozen([0,0,1,2,3,4],np.int64);j=frozen([1,2,1,3,0,4],np.int64);out=np.zeros(6);reverse=np.zeros(6)
            self.assertTrue(fill_agreement(a,b,i,j,out,0,6));self.assertTrue(fill_agreement(b,a,j,i,reverse,0,6))
            np.testing.assert_allclose(out,[scalar(a[x],b[y]) for x,y in zip(i,j)],atol=1e-8,rtol=1e-6)
            np.testing.assert_array_equal(out,reverse);self.assertEqual(out[1],0.);self.assertEqual(out[4],1.)

    def test_nondyadic_reference(self):
        a=frozen([[0.1, -0.3, 1.1, 1e-9], [3.14159, -2.71828, 0.123456789, -0.00001]])
        b=frozen([[0.2, 0.7, -1.7, 1e-7], [3.14158, -2.71829, 0.123456788, -0.00002]])
        i=frozen([0,1,0,1],np.int64);j=frozen([0,1,1,0],np.int64);out=np.zeros(4)
        self.assertTrue(fill_agreement(a,b,i,j,out,0,4))
        np.testing.assert_allclose(out,[scalar(a[x],b[y]) for x,y in zip(i,j)],atol=1e-8,rtol=1e-6)

    def test_refusals_do_not_write(self):
        a,b,i,j=self.fixture()
        bad_cases=[(a.copy(),b,i,j,0,4),(a,b,i.copy(),j,0,4),(frozen([[257.,0.]]*3),b,i,j,0,4),
                   (frozen([[float('nan'),0.]]*3),b,i,j,0,4),(a,b,frozen([0,3,0,0],np.int64),j,0,4),
                   (a,b,i,j,-1,2),(a,b,i,j,0,5),(a,b,i,j,True,2),
                   (frozen([[0.,0.,0.]]*3),frozen([[0.,0.,0.]]*3),i,j,0,4)]
        for args in bad_cases:
            out=np.full(6,-9.);self.assertFalse(fill_agreement(*args[:4],out,*args[4:]));np.testing.assert_array_equal(out,[-9.]*6)

    def test_capacity(self):
        a,b,_,_=self.fixture();i=frozen([0]*1025,np.int64);out=np.full(1025,-3.)
        self.assertFalse(fill_agreement(a,b,i,i,out,0,1025));self.assertTrue(np.all(out==-3))
        self.assertTrue(fill_agreement(a,b,i,i,out,0,1024));self.assertEqual(out[-1],-3.)
        self.assertTrue(fill_agreement(a,b,i,i,out,1024,1024))

    def test_alias_and_readonly_output(self):
        a,b,i,j=self.fixture();out=a.reshape(-1)
        self.assertFalse(fill_agreement(a,b,i,j,out,0,4))
        backing=np.zeros((3,2));view=backing.view();view.flags.writeable=False
        self.assertFalse(fill_agreement(view,b,i,j,backing.reshape(-1),0,4))
        np.testing.assert_array_equal(backing,np.zeros((3,2)))

    def test_inputs_immutable_and_fresh(self):
        a,b,i,j=self.fixture();before=[x.tobytes() for x in (a,b,i,j)];out=np.zeros(4)
        self.assertTrue(fill_agreement(a,b,i,j,out,0,4))
        self.assertEqual(before,[x.tobytes() for x in (a,b,i,j)])
        with self.assertRaises(ValueError):a.flags.writeable=True
        changed=frozen([[0.,0.],[2.,2.],[-1.,-2.]])
        self.assertTrue(fill_agreement(changed,b,i,j,out,0,4));self.assertAlmostEqual(out[1],math.exp(-4))

    def test_nondefault_error_policy(self):
        a,b,i,j=self.fixture();out=np.full(4,-1.)
        with np.errstate(under='raise'):
            self.assertFalse(fill_agreement(a,b,i,j,out,0,4))
        np.testing.assert_array_equal(out,[-1.]*4)

if __name__=='__main__':unittest.main()
