"""Pure request/closure refusal checks, no capsule or subprocess execution."""
import importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).with_name('builder01.py')
s=importlib.util.spec_from_file_location('builder',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_paths(self):
  for p in ('../escape','/absolute','keys/x','.env','x//y','x/./y'):
   with self.assertRaises(ValueError):m.relative(p)
  self.assertEqual(m.relative('proof_tools/a.py'),'proof_tools/a.py')
 def test_refs(self):
  for v in ({},{'path':'a','sha256':'x'},{'path':'../a','sha256':'a'*64},{'path':'a','sha256':True}):
   with self.assertRaises(ValueError):m.reference_shape(v)
  m.reference_shape({'path':'a','sha256':'ab'*32})
 def test_order_denominator(self):
  rows=[{'target':'x%03d'%i,'bytes':1,'sha256':'ab'*32} for i in range(195)]
  for bad in (rows[::-1],rows[:-1],rows[:-1]+[rows[0]]):
   with self.assertRaises(ValueError):m.ordered_rows(bad)
  self.assertEqual(m.ordered_rows(rows),rows)
 def test_runtime_cardinality(self):
  v={'distribution_records':[{'name':str(i),'record':'/x/'+str(i),'record_sha256':'ab'*32} for i in range(251)]}
  m.runtime_shape(v)
  for bad in (dict(v,distribution_records=v['distribution_records'][:-1]),dict(v,distribution_records=v['distribution_records']+[v['distribution_records'][0]])):
   with self.assertRaises(ValueError):m.runtime_shape(bad)
 def test_actual_ref_hash_mismatch(self):
  from unittest.mock import patch
  with patch.object(m,'bounded',return_value=b'changed'):
   with self.assertRaisesRegex(ValueError,'reference mismatch'):m.ref(Path('/unused'),{'path':'a','sha256':'ab'*32})
 def test_manifest_tamper_precedes_source_copy(self):
  from unittest.mock import patch
  with patch.object(m,'git',return_value=('a'*40+'\n').encode()),patch.object(m,'bounded',return_value=b'{}'):
   with self.assertRaisesRegex(ValueError,'accepted manifest/Git differs'):m.verify_preparation(Path('/unused'),'a'*40)
 def test_actual_selected_resource_schema(self):
  repo=Path(__file__).resolve().parents[4]
  # Load only accepted generator stdlib, no capsule/claims/numerical imports.
  gen=m.load(repo/m.GEN/'generate03.py','test_source_generator')
  root=Path('/unused-capsule')
  p={'memory_max_bytes':3*m.GIB,'memory_high_bytes':3*m.GIB,'reserve_bytes':3*m.GIB,'start_reserve_bytes':6*m.GIB,'wall_seconds':1800,'disk_floor_bytes':10*m.GIB,'disk_paths':[str(root)],'native_unit_limits':{'file_size_bytes':m.MAX},'storage_budget':{'root':str(root),'limits':{'max_allocated_bytes':m.GIB,'max_logical_bytes':m.GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}}
  gen.resources(root,p)
  for key in ('memory_max_bytes','memory_high_bytes','reserve_bytes','start_reserve_bytes','wall_seconds','disk_floor_bytes'):
   with self.assertRaises(ValueError):gen.resources(root,dict(p,**{key:True}))
  with self.assertRaises(ValueError):gen.resources(root,dict(p,physical_policy={}))
 def test_no_automatic_mutation_or_launch(self):
  import ast
  t=ast.parse(P.read_text());calls=[n for n in ast.walk(t) if isinstance(n,ast.Call)]
  for n in calls:
   if isinstance(n.func,ast.Attribute):self.assertNotIn(n.func.attr,('guarded_run','start','fit','admit','commit','Popen'))
 def test_stage_fields(self):
  for v in ({'stage':'launch'},{'stage':'export','capsule':'/x','authority':True}):
   with self.assertRaises(ValueError):m.request_shape(v)
if __name__=='__main__':unittest.main(verbosity=2)
