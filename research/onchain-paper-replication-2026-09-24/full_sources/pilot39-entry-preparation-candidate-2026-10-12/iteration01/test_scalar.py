import importlib.util,copy,unittest,ast,json
from pathlib import Path
P=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('entry39candidate',P/'prepare_entry01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ScalarTests(unittest.TestCase):
 def test_same_caps(self):
  r=json.loads((P.parent/'real-data-pilot-full39-binding-preparation01-2026-10-12/public01/execution_job.json').read_bytes())['resources'];m.validate_limits(r)
  bad=copy.deepcopy(r);bad['memory_max_bytes']+=1
  with self.assertRaises(AssertionError):m.validate_limits(bad)
 def test_real_preflight_source_adaptation(self):
  p=P.parent/'real-data-pilot-full38-entry-preparation01-2026-10-12/preflight38_01.py';ref={'path':'actual39/PREPARED01.json','sha256':'0'*64,'bytes':123}
  out=m.adapt_control(p.read_text(),p.name,ref);ast.parse(out)
  self.assertIn("need('entry_qualification' not in mcm",out);self.assertIn("'whole_cells')==415968128",out);self.assertIn("memory_fit_proven') is False",out)
  self.assertIn("FROZEN_PREPARATION="+repr(ref),out);self.assertNotIn("==ENTRY_SELECTION",out)
 def test_root_io_alias_uses_new_preflight(self):
  p=P.parent/'real-data-pilot-full38-entry-preparation01-2026-10-12/root_io38_01.py';out=m.adapt_control(p.read_text(),p.name,{})
  ast.parse(out);self.assertIn('preflight39_01',out);self.assertNotIn('20261012-38',out)
 def test_storage_arithmetic_not_memory_proof(self):
  result={'growth':{'logical_file_bytes':100,'allocated_bytes':200,'entries':3},'storage_caps_and_floor_pass':True}
  terms={'directory_allocated_bytes':20,'other_writer_allocated_bytes':30};resources={'storage_budget':{'roots':['owned'],'shared_files':['lock']}}
  d=m.capacity_declaration('a'*40,resources,{}, {'at':'synthetic'},terms,result,{},True)
  self.assertEqual(d['decision'],'accepted');self.assertEqual(d['non_directory_new_allocated_growth_bytes'],150)
  self.assertFalse(d['physical_reservation']);self.assertFalse(d['full_training_memory_fit_proven']);self.assertFalse(d['full_pilot_capacity_admitted'])
  self.assertEqual(m.capacity_declaration('a'*40,resources,{}, {'at':'synthetic'},terms,result,{},False)['decision'],'DRAFT_NOT_RELEASED')
 def test_absent_prior_component_does_not_qualify(self):
  self.assertFalse(m.prior_component({'prior_outcome_review':None}))
 def test_candidate_ast_keeps_prior_gate_and_source_assertions(self):
  s=(P/'prepare_entry01.py').read_text();ast.parse(s)
  for needle in ["len(gate['experiments'])==15","len(experiment['source_files'])==1036","assert len(pins)==428","parent=None","sourcefiles[path]==digest","actual_new_recovery':None"]:self.assertIn(needle,s)
if __name__=='__main__':unittest.main()
