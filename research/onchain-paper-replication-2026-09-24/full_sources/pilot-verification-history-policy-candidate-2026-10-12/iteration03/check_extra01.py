from check01 import *
class Extra(unittest.TestCase):
 def test_baseline_red_selected_green_115(self):
  f=Fixture(115)
  try:
   f.env['claims'](f.root);f.env['claims'](f.root);self.assertEqual(sum(k=='verify' for k,v in f.events),232)
   f.events.clear();f.admit();f.admit();self.assertEqual(sum(k=='verify' for k,v in f.events),117)
   f.events.clear();f.env['_HISTORY'].clear();f.admit();self.assertEqual(sum(k=='verify' for k,v in f.events),116)
  finally:f.close()
 def test_separate_run_cannot_import_token_and_cleanup_fatal(self):
  a=Fixture();b=Fixture()
  try:
   a.admit();state,seal=a.env['_HISTORY'][a.run];b.env['_HISTORY'][b.run]=(state,seal)
   with self.assertRaisesRegex(ValueError,'authority'):b.admit()
   class Bad(dict):
    def pop(self,*args):raise SystemExit('cleanup')
   a.env['_HISTORY_BUSY']=Bad();fatal=KeyboardInterrupt('first');a.verify_error=fatal
   with self.assertRaises(KeyboardInterrupt) as caught:a.admit(True)
   self.assertIs(caught.exception,fatal)
   self.assertNotIn(a.run,a.env['_HISTORY'])
  finally:a.close();b.close()
 def test_cleanup_uncertainty_no_success(self):
  a=Fixture()
  try:
   class Bad(dict):
    def pop(self,*args):raise RuntimeError('cleanup')
   a.env['_HISTORY_BUSY']=Bad()
   with self.assertRaisesRegex(RuntimeError,'cleanup'):a.admit()
   self.assertNotIn(a.run,a.env['_HISTORY'])
  finally:a.close()
 def test_mutation_during_audit_and_expiry_only_history_git(self):
  f=Fixture()
  try:
   verify=f.env['verify_claim'];changed=[False]
   def mutate(path):
    result=verify(path)
    if not changed[0]:
     changed[0]=True;(f.root/'research_runs/old000/failed.json').write_text('changed')
    return result
   f.env['verify_claim']=mutate
   with self.assertRaisesRegex(ValueError,'frontier changed'):f.admit()
   f.env['verify_claim']=verify;f.admit();errors=[]
   # Model an old Git object mutation: warm checks do not inspect old Git.
   def old_git_error(path):
    if path.name.startswith('old'):raise ValueError('historical Git mutation')
    return verify(path)
   f.env['verify_claim']=old_git_error;f.admit()
   with self.assertRaisesRegex(ValueError,'historical Git'):f.admit(True)
  finally:f.close()
if __name__=='__main__':unittest.main(verbosity=2)
