"""Qualified deterministic render; no real source anchor, registration or claims."""
import ast,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
import mutation_inputs as mutate
import refusal_cases as cases
import resource_policy05 as policy
D=Path(__file__).resolve().parent;F=D.parent
spec=importlib.util.spec_from_file_location('generator',F/'original-import-fixture-native-preparation02-2026-10-03/generate_inputs01.py');generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
def render():
 index=json.loads((F/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json').read_text());evidence=json.loads((F/'original-dictionary-bridge-investigation-2026-10-02/evidence01.json').read_text());matching=json.loads((F.parent/'config/matching-stable.json').read_text());inv=json.loads((F/'original-import-native-refusal-candidate04-2026-10-03/source_inventory04.json').read_text())
 sources={r['target']:r['sha256'] for r in inv['source_inventory']};package={k:v for k,v in sources.items() if k.startswith('tradingagents/')};assert len(package)==144
 base=generator.inputs(case='success',capsule='/qualified-unregistered-synthetic',source_anchor='a'*40,source_files=dict(list(package.items())[:142]),original_index=index,evidence=evidence,matching=matching,environment={'qualified_not_admitted':True})
 return base,{v:mutate.render(base,v,package) for v in cases.NAMES},sources,inv
class Checks(unittest.TestCase):
 def test_all27_rendered_policies_and_original_semantics(self):
  base,items,_,_=render();oldm=json.loads(base['files'][base['inputs']['mcm_policy']['path']]);self.assertEqual(oldm['numeric']['edge_chunk'],65536)
  for variant,item in items.items():
   m=json.loads(item['files'][item['inputs']['mcm_policy']['path']]);self.assertEqual(m['numeric'],policy.NUMERIC)
   expected=json.loads(json.dumps(oldm));expected['numeric']['edge_chunk']=4096;self.assertEqual(m,expected)
   for name in ('original_import','original_import_stage'):
    self.assertEqual(item['files'][item['inputs'][name]['path']],base['files'][base['inputs'][name]['path']])
   for info in item['inputs'].values():
    if info['path'] in item['files']:self.assertEqual(hashlib.sha256(item['files'][info['path']]).hexdigest(),info['sha256'])
   self.assertEqual(item['targets'],base['targets']);self.assertEqual(item['identity'],cases.identity(variant))
 def test_source_pin_and_strict_numeric_types(self):
  for key in policy.NUMERIC:
   val=dict(policy.NUMERIC);val[key]=True
   with self.assertRaises(ValueError):policy.validate(val,2,2,32,16)
  for vals in ((4,4,32,16),(2,2,4,2),(True,2,32,16)):
   with self.assertRaises(ValueError):policy.validate(dict(policy.NUMERIC),*vals)
  base,_,sources,_=render();package={k:v for k,v in sources.items() if k.startswith('tradingagents/')};package[policy.CONSTRUCTOR_PATH]='0'*64
  with self.assertRaisesRegex(ValueError,'constructor source'):mutate.render(base,'wrong-ack',package)
 def test_separate_program_and_exact27_23_gate(self):
  base,items,sources,inv=render();primary,_=generator.registration(rendered={'success':base,'second_target_publication_failure':base},source_files=sources,runtime_hashes={'qualified_only':'a'*64})
  row=next(r for r in inv['source_inventory'] if r['target']=='tradingagents/research/onchain_replication/imported_mcm_identity.py');root=D.parents[3]
  gate,_=mutate.draft_gate(primary,items,sources,{'qualified_only':'a'*64},imported_identity_source=(root/row['origin']).read_bytes())
  self.assertEqual(gate['program_id'],'original-import-refusal-engineering-20261003');self.assertEqual(len(gate['experiments']),27);self.assertEqual(gate['families']['import-refusal-engineering']['attempt_budget'],23);self.assertEqual(len(cases.PRECLAIM),4)
 def test_helper_formula_actual_constructor_ast(self):
  source=F/'original-import-fixture-io-candidate02-2026-10-02/array_neighborhoods.py';self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),policy.CONSTRUCTOR_SHA256)
  original=next(n.value for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='buffer_allowance' for t in n.targets))
  selected=next(n.value for n in ast.walk(ast.parse((D/'resource_policy05.py').read_text())) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='allowance' for t in n.targets));self.assertEqual(ast.dump(original),ast.dump(selected))
if __name__=='__main__':
 result=unittest.main(exit=False);assert not any(n.split('.')[0] in ('numpy','scipy','torch','tradingagents') for n in sys.modules);sys.exit(not result.result.wasSuccessful())
