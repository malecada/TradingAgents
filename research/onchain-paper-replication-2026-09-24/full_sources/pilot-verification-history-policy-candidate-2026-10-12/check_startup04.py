from check01 import Fixture,unittest
class Startup(unittest.TestCase):
 def test_selected_startup_bound_and_no_seed(self):
  f=Fixture(2)
  try:
   def startup():return f.env['_history_prior'](None,f.root,'gate','own','source','source',f.raw,f.policy,False)
   f.env['_HISTORY_MAX_RUNS']=1
   with self.assertRaisesRegex(ValueError,'bounded history roster exceeded'):startup()
   self.assertEqual(sum(k=='verify' for k,v in f.events),0)
   f.env['_HISTORY_MAX_RUNS']=512
   self.assertEqual(len(startup()),3);self.assertEqual(len(startup()),3)
   self.assertEqual(sum(k=='verify' for k,v in f.events),6)
   self.assertEqual(len(f.env['_HISTORY']),0);self.assertEqual(len(f.env['_HISTORY_BUSY']),0)
  finally:f.close()
if __name__=='__main__':unittest.main(verbosity=2)
