import importlib.util,pathlib,unittest
P=pathlib.Path(__file__).with_name('tail_population.py')
class Budget(unittest.TestCase):
 def module(self):
  self.assertTrue(P.exists(),'separate score-tail population adapter missing')
  spec=importlib.util.spec_from_file_location('tail_population',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def test_whole_population_rounded_two_graphs(self):
  m=self.module();got=m.population([{'graph':'a'*64,'rows':2048},{'graph':'b'*64,'rows':1}],chunk_cells=65536,reads=1)
  raw=(65536+32)*80;rounded=(5242880//32768+1)*32768+32768
  self.assertEqual(got['chunks'],2);self.assertEqual(got['remote_payload_bytes'],raw)
  self.assertEqual(got['rounded_transfer_bytes'],raw+2*rounded)
  self.assertEqual(got['commands'],8)
 def test_duplicate_graph_unknown_field_bounds(self):
  m=self.module()
  for targets in ([{'graph':'a'*64,'rows':1}]*2,[{'graph':'a'*64,'rows':True}],[{'graph':'a'*64,'rows':1,'events':1}]):
   with self.assertRaises(ValueError):m.population(targets,chunk_cells=65536,reads=1)
  with self.assertRaises(ValueError):m.population([{'graph':'a'*64,'rows':1}],chunk_cells=65537,reads=1)
if __name__=='__main__':unittest.main(verbosity=2)
