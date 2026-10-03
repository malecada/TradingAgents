"""Bounded stdlib/source metadata tests; no constructed research authority."""
import ast,copy,hashlib,importlib.util,json,sys,types,unittest
from pathlib import Path
P=Path(__file__).parent
s=importlib.util.spec_from_file_location('selected_builder',P/'capsule_builder01.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
s=importlib.util.spec_from_file_location('selected_generator',P/'generate_inputs01.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
# Module aliases are qualified source-only stand-ins, not a real capsule origin.
package=types.ModuleType('fixture_tools');package.capsule_builder01=b;sys.modules['fixture_tools']=package
q=json.loads((P/'ROOT_TEMPLATE01.json').read_bytes());mode=q['closure_mode'];rows=q['rows']
def plan():
 source,package=b.full_rows(rows,mode)
 return {'schema_version':1,'kind':'full202-resource-source-metadata-v1','closure_mode':mode,'source_count':202,'package_count':151,'source_files':source,'package_files':package,'source':'a'*40,'anchor':'b'*40,'root':'/synthetic-only','execution_admitted':False}
class Checks(unittest.TestCase):
 def test_complete_cardinality(self):
  a,c=b.full_rows(rows,mode);self.assertEqual(len(a),202);self.assertEqual(len(c),151)
 def test_mode_refusals(self):
  for value in (None,True,{},dict(mode,unknown=1),dict(mode,schema_version=True),dict(mode,kind='other'),dict(mode,helper_source_files={})):
   with self.assertRaises(ValueError):b.full_mode(value)
 def test_source_rows_refuse(self):
  for mutate in ('missing','extra','hash','order','boolsize','duplicate'):
   x=copy.deepcopy(rows)
   if mutate=='missing':x.pop()
   elif mutate=='extra':x.append(dict(x[0],path='unknown.py'))
   elif mutate=='hash':x[0]['sha256']='0'*64
   elif mutate=='order':x.reverse()
   elif mutate=='boolsize':x[0]['bytes']=True
   else:x[-1]=x[0]
   with self.assertRaises(ValueError):b.full_rows(x,mode)
 def test_input_plan_explicit_partial_metadata(self):
  p=g.held_input_plan({},plan(),closure_mode=mode);self.assertEqual(p['source_count'],202);self.assertEqual(p['package_count'],151);self.assertEqual(p['remaining_roles'],list(g.HELD_ROLES));self.assertFalse(p['execution_admitted']);self.assertIn('201/206',p['route_blocker'])
 def test_none_refuses_full_population(self):
  with self.assertRaises(ValueError):g.held_input_plan({},plan())
 def test_selected_refuses_old_population(self):
  x=plan();x['source_count']=199
  with self.assertRaises(ValueError):g.held_input_plan({},x,closure_mode=mode)
 def test_legacy_none_same_behavior(self):
  x={'source_count':199,'package_count':148,'execution_admitted':False,'source_files':{str(i):'a'*64 for i in range(199)},'package_files':{str(i):'a'*64 for i in range(148)},'source':'c'*40,'anchor':'d'*40,'root':'/synthetic-only'}
  self.assertEqual(g.held_input_plan({},x),g._legacy_held_input_plan({},x))
 def test_declared_auxiliary207_and_collisions(self):
  p=plan();roles={'case_contract':{'document':{'kind':'root-selected-imported-held-resource-v1','program_id':'unregistered-synthetic','experiment_id':'unregistered-synthetic'}}}
  for i,name in enumerate(g.AUXILIARY_ROLES):roles[name]={'reference':{'path':'metadata/'+name+('.md' if name=='charter' else '.json'),'bytes':10,'sha256':str(i)*64},'document':{}}
  d=g.render_held_auxiliary_declaration(roles,p,closure_mode=mode);self.assertEqual(d['implementation_source_count'],202);self.assertEqual(d['package_count'],151);self.assertEqual(d['entry_count'],4)
  roles['charter']['reference']['path']=roles['budget_review']['reference']['path']
  with self.assertRaises(ValueError):g.render_held_auxiliary_declaration(roles,p,closure_mode=mode)
 def test_no_invented_anchor_or_origin(self):
  with self.assertRaisesRegex(ValueError,'origin'):b.full_source_plan(P.resolve(),'a'*40,'b'*40,rows,mode,design_source='a'*40)
 def test_original_prefix_bytes(self):
  for name in ('capsule_builder01.py','generate_inputs01.py','build_release_draft01.py'):
   old=(P/(name+'.baseline.txt')).read_bytes();new=(P/name).read_bytes();self.assertTrue(new.startswith(old));ast.parse(new)
if __name__=='__main__':unittest.main()
