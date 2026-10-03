"""Independent finite inventory/source checks. No native or numerical execution."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[3];CAND=HERE.parent/'original-import-native-refusal-worker-preparation03-2026-10-03';OLD=HERE.parent/'original-import-native-refusal-worker-preparation02-2026-10-03'
def digest(b):return hashlib.sha256(b).hexdigest()
m=json.loads((CAND/'MANIFEST03.json').read_bytes())
for row in m['files']+m['dependencies']:
 raw=(ROOT/row['path']).read_bytes();assert len(raw)==row['bytes'] and digest(raw)==row['sha256'],row['path']
new=json.loads((CAND/'source_inventory03.json').read_bytes());old=json.loads((OLD/'source_inventory02.json').read_bytes());n={r['target']:r for r in new['source_inventory']};o={r['target']:r for r in old['source_inventory']}
assert len(n)==170 and len(o)==169 and len([x for x in n if x.startswith('tradingagents/')])==144
assert set(n)-set(o)=={'fixture_tools/refusal_inventory03.py'}
assert {x for x in o if o[x]['sha256']!=n[x]['sha256']}=={'fixture_tools/refusal_outer01.py','fixture_tools/templates01.py'}
for row in n.values():assert digest((ROOT/row['origin']).read_bytes())==row['sha256']
proto=json.loads((CAND/'PROTOCOL03.json').read_bytes());assert (proto['variants'],proto['classes'],proto['max_claims'],proto['max_owners'],proto['max_journals'],proto['max_oracle_pairs'],proto['max_scored_pairs'])==(27,16,23,17,19,1088,129)
assert len(proto['preclaim'])==4 and len(proto['case_order'])==27 and proto['whole_outer_deadline_enforced'] is False and proto['per_case_closure_seconds'] is None and proto['entire_suite_wall_bound_seconds'] is None
sys.path.insert(0,str(CAND));import refusal_inventory03 as inv
# This imports only retained-source test setup that extracts the old scanner and
# loads the exact stdlib raw body reader. No test creates authority objects.
from test_reader03 import env

def tree(root):
 outer=root/'fixture_outer'/'independent';outer.mkdir(parents=True);(root/'a.txt').write_bytes(b'A');(root/'b.txt').write_bytes(b'B');return outer

def save_at(outer):
 def save(name,value):
  b=inv.encode(value);assert len(b)<=8192
  with (outer/name).open('xb') as f:f.write(b)
 return save
class Review(unittest.TestCase):
 def test_serializer_71refs_and_typed_layers(self):
  rows=[{'path':'data/'+str(i).zfill(5)+'.json','bytes':1,'allocated':4096,'kind':'file','sha256':'0'*64} for i in range(2311)]
  plan=inv.prepare({'schema_version':1,'root':'/synthetic','root_allocated':4096,'tail_exclusion':'fixture','members':rows},'independent')
  self.assertEqual(plan[-1][1]['member_count'],2311);self.assertGreater(plan[-1][1]['level'],0);self.assertTrue(all(len(inv.encode(v))<=8192 for _,v in plan))
  for _,v in plan:self.assertEqual(inv.encode(v),(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode())
 def test_resealed_omission_refuses_actual_tree(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);outer=tree(root);index=env['inventory'](root);index['members']=[r for r in index['members'] if r['path']!='a.txt']
   with self.assertRaisesRegex(ValueError,'member set differs'):inv.publish(root,outer,index,'independent',save_at(outer))
 def test_resealed_size_hash_change_refuses_original_body(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);outer=tree(root);index=env['inventory'](root)
   next(r for r in index['members'] if r['path']=='a.txt')['sha256']=digest(b'changed')
   with self.assertRaisesRegex(ValueError,'original raw file changed'):inv.publish(root,outer,index,'independent',save_at(outer))
 def test_actual_child_reference_count_and_encoding_refusal(self):
  for change in ('count','duplicate_key'):
   with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);outer=tree(root);ref=inv.publish(root,outer,env['inventory'](root),'independent',save_at(outer));page=outer/'inventory-page-0000.json';record=json.loads(page.read_bytes())
    if change=='count':
     index=json.loads((outer/'inventory.json').read_bytes());index['children'][0]['members']+=1;(outer/'inventory.json').write_bytes(inv.encode(index))
    else:
     original=page.read_bytes();page.write_bytes(original.replace(b'{',b'{"schema_version": 1, ',1));index=json.loads((outer/'inventory.json').read_bytes());index['children'][0].update(sha256=digest(page.read_bytes()),bytes=page.stat().st_size);(outer/'inventory.json').write_bytes(inv.encode(index))
    # Even coherently updating the root ref cannot rescue malformed semantics.
    ref.update(sha256=digest((outer/'inventory.json').read_bytes()),bytes=(outer/'inventory.json').stat().st_size)
    with self.assertRaises(ValueError):inv.authenticate(root,outer,'independent',ref)
 def test_no_numeric_package(self):self.assertFalse(any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules))
if __name__=='__main__':
 print(json.dumps({'manifest_files':len(m['files']),'sources':len(n),'unchanged':167,'package':144,'source_only':True}));unittest.main(verbosity=2)
