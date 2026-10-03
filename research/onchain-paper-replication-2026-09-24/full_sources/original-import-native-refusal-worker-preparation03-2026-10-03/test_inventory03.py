"""Typed finite source fixtures; no real raw arrays/claims/native jobs."""
import hashlib,importlib.util,json,pathlib,sys,unittest
D=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(D))
class Tests(unittest.TestCase):
 def module(self):
  p=D/'refusal_inventory03.py';self.assertTrue(p.exists(),'new complete inventory implementation required');s=importlib.util.spec_from_file_location('inventory_candidate03',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def index(self,count,wide=0):return {'schema_version':1,'root':'/source-only-fixture','root_allocated':4096,'tail_exclusion':'qualified source fixture','members':[{'path':str(i).zfill(5)+'x'*wide,'bytes':0,'allocated':0,'kind':'directory'} for i in range(count)]}
 def test_2311_rows_and_maximum_entries_all_retained(self):
  m=self.module()
  for count,width in ((2311,120),(32768,0)):
   with self.subTest(count=count):
    plan=m.prepare(self.index(count,width),'synthetic-case');self.assertTrue(all(len(m.encode(v))<=8192 for n,v in plan));self.assertEqual(plan[-1][1]['member_count'],count);self.assertEqual(sum(len(v['members']) for n,v in plan if v['kind']=='refusal-inventory-page-v1'),count)
 def test_near_four_mib_rows_require_second_index_level(self):
  m=self.module();v=self.index(1026);suffix='/'.join(['😀'*32]*10+['😀'*14])
  for i,row in enumerate(v['members']):row['path']=str(i).zfill(4)+'/'+suffix
  plan=m.prepare(v,'synthetic-case');self.assertEqual(plan[-1][1]['page_count'],1026);self.assertEqual(plan[-1][1]['level'],2);self.assertLessEqual(plan[-1][1]['encoded_row_bytes'],4*1024**2);self.assertTrue(all(len(m.encode(body))<=8192 for name,body in plan))
 def test_escaped_row_refuses_before_any_publication(self):
  m=self.module();v=self.index(1);v['members'][0]['path']='/'.join(['😀'*55]*16)
  with self.assertRaisesRegex(ValueError,'encoded inventory row'):m.prepare(v,'synthetic-case')
 def test_exact_serializer_not_compact_estimate(self):
  m=self.module();v=self.index(100,70);plan=m.prepare(v,'synthetic-case');self.assertTrue(all(m.encode(b)==(json.dumps(b,sort_keys=True,allow_nan=False)+'\n').encode() for n,b in plan));self.assertTrue(all(len(m.encode(b))<=8192 for n,b in plan))
if __name__=='__main__':unittest.main(verbosity=2)
