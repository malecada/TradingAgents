import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('oracle',Path(__file__).with_name('oracle.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_identity_reversal_rotation(self):
  self.assertEqual(m.chain_score([[i,i] for i in range(4)],4,1),(3,.75))
  self.assertEqual(m.chain_score([[i,3-i] for i in range(4)],4,1),(0,.5))
  hits,score=m.chain_score([[i,(i+1)%4] for i in range(4)],4,1);self.assertEqual(hits,2);self.assertAlmostEqual(score,2/3)
 def test_nonbijective_refused(self):
  for pairs in ([[0,0],[1,0]],[[0,1]],[[0,0],[1,2]]):
   with self.assertRaises(ValueError):m.chain_score(pairs,2,1)
if __name__=='__main__':unittest.main(verbosity=2)
