import runpy,unittest
from pathlib import Path
n=runpy.run_path(str(Path(__file__).with_name('check02.py')))
class Types(unittest.TestCase):
 def test_exact_integer_selected_cost_fields(self):
  c=n['Checks']()
  for which in ('spent','partial','manifest'):
   for value in (False,0.0,True,128653.0):
    d=c.fixture();mapping=d[0]['spent_counters'] if which=='spent' else d[0]['retained_partial_work'] if which=='partial' else d[1]['spent_counters'];mapping['checkpoint_attempts']=value
    with self.assertRaisesRegex(ValueError,'exact integer'):c.call(d)
if __name__=='__main__':unittest.main(verbosity=2)
