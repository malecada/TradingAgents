"""Float32 model outputs must reproduce metrics from saved scalar probabilities."""
import unittest
import math
import numpy as np
from tradingagents.research.onchain_replication.metrics import classification_metrics
from tradingagents.research.onchain_replication.verification import independent_classification,compare_summary

class Tests(unittest.TestCase):
    def test_float32_probabilities_match_saved_scalar_metric_arithmetic(self):
        p=np.array([.6,.3,.99,.01],dtype=np.float32);y=[1,0,0,1]
        a=classification_metrics(y,p);expected=independent_classification(y,p.tolist())
        self.assertTrue(compare_summary(a,expected)['passed'])
        self.assertEqual(a,classification_metrics(y,p.tolist()))
    def test_float32_endpoints_use_finite_frozen_clipping(self):
        p=np.array([0.,1.,1.,0.],dtype=np.float32);y=[0,1,0,1]
        with np.errstate(all='raise'):a=classification_metrics(y,p)
        expected=-sum(math.log(min(max(float(v),1e-15),1-1e-15)) if label else math.log1p(-min(max(float(v),1e-15),1-1e-15)) for label,v in zip(y,p))/4
        self.assertAlmostEqual(a['log_loss'],expected,places=13)
        self.assertTrue(compare_summary(a,independent_classification(y,p.tolist()))['passed'])
    def test_float32_labels_and_probabilities_preserve_brier_precision(self):
        p=np.array([.1,.7,.5],dtype=np.float32);y=np.array([0,1,1],dtype=np.float32)
        expected=sum((float(a)-float(b))**2 for a,b in zip(p,y))/len(y)
        actual=classification_metrics(y,p)
        self.assertAlmostEqual(actual['brier'],expected,places=14)
        self.assertTrue(compare_summary(actual,independent_classification(y.tolist(),p.tolist()))['passed'])

if __name__=='__main__':unittest.main(verbosity=2)
