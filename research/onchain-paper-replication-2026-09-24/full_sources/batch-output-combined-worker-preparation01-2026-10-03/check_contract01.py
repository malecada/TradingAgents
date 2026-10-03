import ast,json,hashlib,unittest,sys
from pathlib import Path
P=Path(__file__).parent;source=P/(sys.argv.pop(1) if len(sys.argv)>1 else 'held_score_consumer.py')
def load():
 names={'require','_transfer_closure','_combined_closure','_combined_budget','_combined_profile','_policy'};tree=ast.parse(source.read_bytes());ns=dict(Path=Path,json=json,hashlib=hashlib,KIND='original-import-held-score-readback-v1',TRANSFER_KIND='original-import-held-score-selected-transfer-v2',COMBINED_KIND='selected-combined-f64-f32-source-closure-v2',RAW_KIND='original-import-held-score-completed-f32-v3')
 exec(compile(ast.Module([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],[]),str(source),'exec'),ns);return ns
def closure(n=202):
 code={f'code/{i}.py':'a'*64 for i in range(n)};code['tradingagents/research/onchain_replication/completed_f32.py']=code.pop('code/0.py');package=dict(list(code.items())[:150]);package['tradingagents/research/onchain_replication/completed_f32.py']='a'*64;aux={f'aux/{i}.json':'b'*64 for i in range(5)}
 return dict(schema_version=2,kind='selected-combined-f64-f32-source-closure-v2',implementation_source_count=n,package_count=151,source_files=code,package_files=package,auxiliary_source_files=aux),code|aux,package
class Tests(unittest.TestCase):
 def test_combined_explicit_202(self):
  m=load();c,r,p=closure();self.assertEqual(m['_transfer_closure'](c,r,p),c['source_files'])
 def test_no_silent_201_widen(self):
  m=load();c,r,p=closure();c.update(schema_version=1,kind='selected-held-transfer-source-closure-v1')
  with self.assertRaises(ValueError):m['_transfer_closure'](c,r,p)
 def test_wrong_maps_types(self):
  m=load()
  for key,value in [('schema_version',True),('package_count',150),('implementation_source_count',201),('kind','unknown')]:
   c,r,p=closure();c[key]=value
   with self.assertRaises(ValueError):m['_transfer_closure'](c,r,p)
 def test_raw_policy_explicit(self):
  m=load();g=['a'*64,'b'*64];p=dict(schema_version=3,kind='original-import-held-score-completed-f32-v3',targets={g[0]:{'output':'a.json'},g[1]:{'output':'b.json'}},part_bytes=512,max_read_bytes=768,max_members=2,population_input='pop',network_release_input='release',source_closure_input='closure')
  self.assertEqual(m['_policy'](p,g,['a.json','b.json']),p)
  p['schema_version']=3.0
  with self.assertRaises(ValueError):m['_policy'](p,g,['a.json','b.json'])
if __name__=='__main__':unittest.main()
