import ast,copy,hashlib,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).parent;OLD=P.parent/'neural-cold-feature-handoff-proof-source-composition03-2026-10-03'
s=importlib.util.spec_from_file_location('metadata04',P/'prepare_metadata_composed04.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
I=json.loads((P/'source_inventory04.json').read_bytes())
class Tests(unittest.TestCase):
 def test_exact_mapping(self):
  value=m.source_mapping(P/'source-bodies',I);self.assertEqual(len(value),195);self.assertEqual(sum(x.startswith('tradingagents/') for x in value),147)
 def test_one_body_change_only(self):
  old=json.loads((OLD/'source_inventory03.json').read_bytes());a={r['target']:r['sha256'] for r in old['source_inventory']};b={r['target']:r['sha256'] for r in I['source_inventory']};self.assertEqual(a.keys(),b.keys());self.assertEqual([k for k in a if a[k]!=b[k]],['tradingagents/research/verify.py'])
  for r in I['source_inventory']:
   data=(P/'source-bodies'/r['target']).read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256']);self.assertEqual(len(data),r['bytes'])
 def test_tampered_inventory_refuses(self):
  for name in ['status','path','order','sha','denominator']:
   v=copy.deepcopy(I)
   if name=='status':v['status']='accepted'
   if name=='path':v['source_inventory'][0]['target']='../escape'
   if name=='order':v['source_inventory'].reverse()
   if name=='sha':v['source_inventory'][0]['sha256']='0'*64
   if name=='denominator':v['source_inventory'].pop()
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,'frozen exact'):m.source_mapping(P/'source-bodies',v)
 def test_helper_inverse_AST_and_configs(self):
  s=(P/'prepare_metadata_composed04.py').read_text();pins=json.loads((P/'origins04.json').read_bytes());s=s.replace(pins['canonical_inventory_sha256'],'aff7a877446e94a10c75d73f093c643e3e1f90296d86337352cd0f8dfac69379').replace('source-only-verify-batch04-unreviewed','source-only-outer03-unreviewed')
  self.assertEqual(ast.dump(ast.parse(s)),ast.dump(ast.parse((OLD/'prepare_metadata_composed03.py').read_bytes())))
  for n in ['recipe01.json','configs01.json','model01.json','training01.json']:self.assertEqual((P/n).read_bytes(),(OLD/n).read_bytes())
unittest.main(verbosity=2)
