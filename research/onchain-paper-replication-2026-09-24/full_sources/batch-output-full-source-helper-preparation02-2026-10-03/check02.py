"""Source/metadata-only checks; no Git/Owner/runtime authority is simulated."""
import ast,copy,hashlib,importlib.util,json,sys,types,unittest
from pathlib import Path
P=Path(__file__).parent
def load(n,path):
 s=importlib.util.spec_from_file_location(n,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('builder_successor',P/'capsule_builder01.py');g=load('generator_successor',P/'generate_inputs01.py');v=json.loads((P/'SOURCE_INVENTORY02.json').read_bytes());q=json.loads((P/'ROOT_TEMPLATE02.json').read_bytes())
class Checks(unittest.TestCase):
 def test_full_inverse_two_values_only(self):
  a=(P/'capsule_builder01.py').read_bytes();z=(P/'capsule_builder01.py.baseline.txt').read_bytes()
  for new,old in [('8c66189bd61a715c5f06b33b5fa9195a7185237c571529135d46f8ee1d7710ae','ec49b3a90b598595985ec650dc610e5f21ed6782d54677b17dd9c045bc10adbf'),('4bcef0f71fc228e7ae7379aac2ea3a49ef24dc379f86a67719682e4192db9587','a5bcd68dceb2b6c5e5e9f720c64eb588226a0ede7fb6493808ec0a698ce82df3')]:self.assertEqual(a.count(new.encode()),1);a=a.replace(new.encode(),old.encode())
  self.assertEqual(a,z);self.assertEqual(ast.dump(ast.parse(a)),ast.dump(ast.parse(z)))
  for n in ('generate_inputs01.py','build_release_draft01.py'):self.assertEqual((P/n).read_bytes(),(P/(n+'.baseline.txt')).read_bytes())
 def test_every_source_actual_body(self):
  total=0
  for row in v['entries']:
   path=Path(row['origin']);reader=b.Reader(path.parent);raw=reader.body(path.name);reader.recheck();self.assertEqual(len(raw),row['bytes']);self.assertEqual(b.sha(raw),row['sha256']);total+=len(raw)
  self.assertEqual(len(v['entries']),202);self.assertEqual(total,v['implementation_bytes']);self.assertEqual(total,3543144)
 def test_external_helper_pins_and_shape(self):
  code,package=b.full_rows(q['rows'],q['closure_mode']);self.assertEqual(len(code),202);self.assertEqual(len(package),151)
  for path,digest in q['closure_mode']['helper_source_files'].items():self.assertEqual(b.sha((P/Path(path).name).read_bytes()),digest)
  self.assertEqual({r['target']:r['sha256'] for r in v['entries']},code)
 def test_mode_refusals(self):
  for value in [None,{},dict(q['closure_mode'],schema_version=True),dict(q['closure_mode'],kind='unknown'),dict(q['closure_mode'],helper_source_files={})]:
   with self.assertRaises(ValueError):b.full_mode(value)
 def test_rows_refusals(self):
  for change in range(6):
   rows=copy.deepcopy(q['rows'])
   if change==0:rows.pop()
   if change==1:rows.reverse()
   if change==2:rows[0]['sha256']='0'*64
   if change==3:rows[0]['bytes']=True
   if change==4:rows[0]['bytes']=4*1024**2+1
   if change==5:rows[0]['path']='unknown.py'
   with self.assertRaises(ValueError):b.full_rows(rows,q['closure_mode'])
 def test_real_metadata_missing_roles_stays_unregistered(self):
  code,package=b.full_rows(q['rows'],q['closure_mode']);plan={'kind':'full202-resource-source-metadata-v1','closure_mode':q['closure_mode'],'source_count':202,'package_count':151,'source_files':code,'package_files':package,'execution_admitted':False,'source':None,'anchor':None,'root':None}
  pkg=types.ModuleType('fixture_tools');pkg.capsule_builder01=b;before=sys.modules.get('fixture_tools');sys.modules['fixture_tools']=pkg
  try:out=g.held_input_plan({},plan,closure_mode=q['closure_mode'])
  finally:
   if before is None:del sys.modules['fixture_tools']
   else:sys.modules['fixture_tools']=before
  self.assertEqual(out['source_count'],202);self.assertEqual(out['package_count'],151);self.assertIs(out['execution_admitted'],False)
  with self.assertRaises(ValueError):g.full_render_held_auxiliary_declaration({},plan)
 def test_original_default_delegation_unchanged(self):
  for name in ('capsule_builder01.py','generate_inputs01.py','build_release_draft01.py'):
   def funcs(path):return {n.name:ast.dump(n) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
   self.assertEqual(funcs(P/name),funcs(P/(name+'.baseline.txt')))
 def test_no_current_design_anchor_authority(self):
  for key in ('current_source','design_source','genuine151_anchor','native_release','registration','role_references'):self.assertIsNone(q[key])
  with self.assertRaises(ValueError):b.full_source_plan(P,None,None,q['rows'],q['closure_mode'],design_source=None)
if __name__=='__main__':unittest.main()
