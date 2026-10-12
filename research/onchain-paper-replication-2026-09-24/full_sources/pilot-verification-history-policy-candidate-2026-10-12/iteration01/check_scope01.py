from check01 import *
class Scope(unittest.TestCase):
 def test_unclosed_history_preserved_changes_force(self):
  f=Fixture()
  try:
   f.add('unrelated-unfinished',terminal=False);f.admit();f.events.clear();f.admit()
   self.assertEqual(sum(k=='verify' for k,v in f.events),1)
   (f.root/'research_runs/unrelated-unfinished/failed.json').write_text('{}');f.events.clear();f.admit()
   self.assertEqual(sum(k=='verify' for k,v in f.events),7)
   self.assertFalse((f.root/'research_runs/unrelated-unfinished/complete.json').exists())
  finally:f.close()
 def test_metadata_only_helper_creates_no_run_state(self):
  f=Fixture()
  try:
   previous=None;fulls=[]
   for force in (False,False,False,False,True):
    previous,prior,full=f.env['_history_scan'](f.root,1,previous,force=force);fulls.append(full)
   self.assertEqual(fulls,[True,False,False,False,True]);self.assertEqual(len(f.env['_HISTORY']),0)
   self.assertEqual(len(f.env['_HISTORY_BUSY']),0)
  finally:f.close()
if __name__=='__main__':unittest.main(verbosity=2)
