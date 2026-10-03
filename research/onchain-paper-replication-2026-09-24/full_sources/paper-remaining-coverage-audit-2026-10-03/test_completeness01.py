import copy,importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('completeness_report01.py');s=importlib.util.spec_from_file_location('metadata_report',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def test_actual_documentary_denominators(self):
  r=m.summarize(m.read_inputs());self.assertEqual(r['fits']['unique'],1420);self.assertEqual(r['resource']['remaining'],32);self.assertEqual(r['fits']['distinct_table_patterns'],40)
 def test_corrupted_counts_and_history_refuse(self):
  d=m.read_inputs()
  for mutate in (lambda x:x['coverage']['requirements'].pop(),lambda x:x['coverage']['requirements'][0].update(original_status='failed'),lambda x:x['allocation']['batches'][0]['cells'].pop(),lambda x:x['tables']['cell_dispositions'][0].update(status='complete'),lambda x:x['tables']['cell_dispositions'][0]['attempts'].append('invented'),lambda x:x['tables']['rows'][0].update(complete=True)):
   v=copy.deepcopy(d);mutate(v)
   with self.assertRaises(AssertionError):m.summarize(v)
if __name__=='__main__':unittest.main(verbosity=2)
