from check01 import Fixture,ResearchRun,unittest
class Identity(unittest.TestCase):
 def test_same_fields_distinct_run_transplant_refuses(self):
  f=Fixture()
  try:
   f.admit();original=f.run;saved=f.env['_HISTORY'][original]
   clone=ResearchRun();clone.__dict__.update(original.__dict__)
   self.assertIsNot(clone,original);self.assertEqual(clone.__dict__,original.__dict__)
   f.env['_HISTORY'][clone]=saved;f.run=clone;f.events.clear()
   with self.assertRaisesRegex(ValueError,'history snapshot authority/thread differs'):f.admit()
   self.assertEqual(sum(k=='verify' for k,v in f.events),0)
   self.assertNotIn(clone,f.env['_HISTORY']);self.assertIs(f.env['_HISTORY'][original],saved)
  finally:f.close()
if __name__=='__main__':unittest.main(verbosity=2)
