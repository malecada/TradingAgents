"""Qualified stdlib metadata refusal checks; no genuine authority stand-ins."""
import importlib.util,json,tempfile,unittest,sys
from pathlib import Path
P=Path(__file__).parent
s=importlib.util.spec_from_file_location('draft_generator',P/'generate01.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class Refusals(unittest.TestCase):
 def test_exact_policy_and_wrong_types(self):
  root=Path('/unexecuted-capsule');v={'memory_max_bytes':3*g.GIB,'memory_high_bytes':3*g.GIB,'reserve_bytes':3*g.GIB,'start_reserve_bytes':6*g.GIB,'wall_seconds':1800,'disk_floor_bytes':10*g.GIB,'disk_paths':[str(root)],'native_unit_limits':{'file_size_bytes':g.MAX},'storage_budget':{'root':str(root),'limits':{'max_allocated_bytes':g.GIB,'max_logical_bytes':g.GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}}
  self.assertEqual(g.resources(root,v),v)
  for k in ('memory_max_bytes','reserve_bytes','wall_seconds'):
   for bad in (True,None,0):
    with self.subTest(key=k,bad=bad),self.assertRaises(ValueError):g.resources(root,{**v,k:bad})
  with self.assertRaises(ValueError):g.resources(root,{**v,'storage_budget':{**v['storage_budget'],'root':'/elsewhere'}})
  with self.assertRaises(ValueError):g.resources(root,{**v,'physical_policy':{}})
 def test_compare_always_fail_closed_before_authority_access(self):
  for r in ({'phase':'compare'},{'phase':'compare','accepted':True,'source':'a'*40,'inputs':{}},{'phase':'compare','materialization':{'status':'complete','inputs':{'x':1}}}):
   with self.assertRaisesRegex(ValueError,'COMPARISON_UNREGISTRABLE'):g.validate(Path('/nonexistent'),r)
 def test_missing_and_placeholder_request(self):
  for request in ({},{'phase':'unknown'},{'phase':'materialize'},{'phase':True}):
   with self.assertRaises(ValueError):g.validate(Path('/nonexistent'),request)
  self.assertFalse(g.sha('0'*64));self.assertFalse(g.sha(None));self.assertFalse(g.sha(True))
 def test_actual_file_reference_integrity(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'tiny.json';p.write_bytes(b'{"a":1}\n');r={'path':p.name,'sha256':g.digest(p.read_bytes())}
   self.assertEqual(g.document(root,r),{'a':1})
   p.write_bytes(b'{"a":2}\n')
   with self.assertRaises(ValueError):g.document(root,r)
   (root/'alias.json').symlink_to(p)
   with self.assertRaises(ValueError):g.body(root,'alias.json')
   for name in ('../outside','.env','keys/example'):
    with self.assertRaises(ValueError):g.body(root,name)
 def test_no_numerical_modules(self):self.assertFalse(any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules))
if __name__=='__main__':unittest.main()
