"""Focused scalar/header controls; synthetic observations grant no authority."""
import copy,json,sys,unittest
from pathlib import Path
from capacity import project,graph_growth,header_bounds,LIMITS
D=Path(__file__).resolve().parent
class CapacityTests(unittest.TestCase):
 def setUp(self):
  self.m=json.loads((D/'WHOLE_METADATA01.json').read_text());self.o=json.loads((D/'DATED_OBSERVATION01.json').read_text());self.t=json.loads((D/'CONDITIONAL_TERMS01.json').read_text())
 def final_fixture(self):
  self.o.update(kind='final-post38-whole39-writable-union',post38_closed_and_recovered=True,source_and_scope_current=True,free_inodes=2000000,filesystem_block_bytes=4096,filesystem_identity='synthetic-only',observation_sha256='synthetic-only')
  self.t.update(review_status='root-current-full-growth',observation_sha256='synthetic-only')
 def test_whole_counts_and_independent_group_formula(self):
  rows=graph_growth(self.m)
  self.assertEqual((sum(v['cells'] for v in rows),sum(v['batches'] for v in rows),sum(v['groups'] for v in rows)),(415968128,101559,6352))
  # One full16-batch archive: two4096 control files and one217180-byte
  # score journal per batch,512 headers and10240 tar record rounding.
  per_member=lambda n:512+((n+511)//512)*512
  full=((16*(2*per_member(4096)+per_member(92+53*4096))+1024+10239)//10240)*10240
  self.assertEqual(full,3645440)
  self.assertEqual(sum(v['prefix_bytes'] for v in rows),415985664)
 def test_header_exact_and_interval(self):
  self.assertEqual(header_bounds(100,0),[100,100]);self.assertEqual(header_bounds(1024+128,1024),[128,128]);self.assertEqual(header_bounds(16*500+128),[10,8128])
  for args in [(100,101),(100,99),(100000,1),(True,None)]:
   with self.subTest(args=args):
    with self.assertRaises(ValueError):header_bounds(*args)
 def test_dated_baseline_cannot_pass(self):
  with self.assertRaises(ValueError):project(self.m,self.o,self.t)
  r=project(self.m,self.o,self.t,conditional=True);self.assertFalse(r['storage_caps_and_floor_pass']);self.assertIn('free_inodes',r['missing_terms'])
 def test_final_synthetic_arithmetic_only(self):
  self.final_fixture();r=project(self.m,self.o,self.t)
  self.assertTrue(r['storage_caps_and_floor_pass']);self.assertFalse(r['memory_fit_proven']);self.assertFalse(r['physical_reservation'])
  self.assertEqual(r['continuation_addition'],{'logical_file_bytes':416083968,'allocated_bytes':416083968,'entries':101559})
  self.assertEqual(sum(r['persistent_subterms_logical'].values()),9086624428)
 def test_residual_domains_rebased_without_double_charge(self):
  self.final_fixture();a=project(self.m,self.o,self.t)
  domain=self.o['storage_observation']['residual_domains']['training_and_lifecycle'];domain['logical_file_bytes']+=100;domain['allocated_bytes']+=4096
  self.o['storage_observation']['logical_file_bytes']+=100;self.o['storage_observation']['allocated_bytes']+=4096
  b=project(self.m,self.o,self.t);self.assertEqual(a['projection'],b['projection'])
 def test_missing_terms_refused(self):
  self.final_fixture()
  for k in ('directory_allocated_bytes','other_writer_entries','additional_headers_edges_logical_bytes','other_new_allocated_bytes'):
   t=copy.deepcopy(self.t);del t[k]
   with self.subTest(k=k):
    with self.assertRaises(ValueError):project(self.m,self.o,t)
  self.t['directory_allocated_bytes']=None
  with self.assertRaises(ValueError):project(self.m,self.o,self.t)
 def test_source_route_counts_and_limits_refused(self):
  self.final_fixture()
  for k,val in [('storage_writer_sources_unchanged',False),('original_input_manifest_pins_unchanged',False),('continuation_manifest_input','old-parent'),('batch_cells',8192)]:
   m=copy.deepcopy(self.m);m[k]=val
   with self.subTest(k=k):
    with self.assertRaises(ValueError):project(m,self.o,self.t)
  self.t['limits']['memory_max_bytes']+=1
  with self.assertRaises(ValueError):project(self.m,self.o,self.t)
 def test_cap_floor_inode_and_header_extra_cost(self):
  self.final_fixture();self.t['additional_headers_edges_logical_bytes']=1000;self.t['additional_headers_edges_allocated_bytes']=4096;self.t['additional_headers_edges_entries']=1
  a=project(self.m,self.o,self.t);self.assertEqual(a['components']['additional_headers_edges']['allocated_bytes'],4096)
  self.o['free_inodes']=1;self.o['disk_free_bytes']=LIMITS['disk_floor_bytes']
  r=project(self.m,self.o,self.t);self.assertFalse(r['storage_caps_and_floor_pass']);self.assertLess(r['margins']['inodes_after_growth'],0);self.assertLess(r['margins']['filesystem_free_after_growth_and_floor'],0)
 def test_unbound_current_terms_refused(self):
  self.final_fixture();self.t['observation_sha256']='stale'
  with self.assertRaises(ValueError):project(self.m,self.o,self.t)
 def test_no_numerical_imports(self):self.assertFalse({'numpy','torch','tensorflow','jax'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
