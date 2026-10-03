import unittest
import test_dispatch02 as prior
class Tests(prior.Tests):
 def test_plan_only_selector(self):
  del self.s['held_score_consumer_input'];self.outputs=self.outputs[:4]
  with self.assertRaises(ValueError):self.check()
 def test_plan_only_reserved_typo(self):
  self.item['held_score_typo']='not-authority'
  with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main(verbosity=2)
