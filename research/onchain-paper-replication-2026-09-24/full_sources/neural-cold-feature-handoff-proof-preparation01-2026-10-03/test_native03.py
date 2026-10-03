"""Actual-source stdlib policy and unselected-control AST checks only."""
import ast,copy,hashlib,json,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_native_policy_refusals(self):
  env={'__builtins__':__builtins__}
  tree=ast.parse((P/'compact_cold_proof_native.py').read_text())
  nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.Assign)) and (not isinstance(n,ast.FunctionDef) or n.name in ('require','selected','schema'))]
  exec(compile(ast.Module(nodes,type_ignores=[]),'actual-native-policy','exec'),env)
  r={'memory_high_bytes':3*1024**3,'memory_max_bytes':3*1024**3,'reserve_bytes':3*1024**3,'start_reserve_bytes':6*1024**3,'disk_floor_bytes':10*1024**3,'wall_seconds':1800,'native_unit_limits':{'file_size_bytes':4194304}}
  j={'kind':'fit','resources':r,'payload':{'cold_proof_input':'cold_proof','representation_jobs':{}}};self.assertTrue(env['selected'](j));env['schema'](j)
  for key in ('memory_high_bytes','memory_max_bytes','reserve_bytes','start_reserve_bytes','disk_floor_bytes','wall_seconds'):
   bad=copy.deepcopy(j);bad['resources'][key]+=1
   with self.assertRaises(ValueError):env['schema'](bad)
  for change in ('missing_cap','wrong_cap','physical','extra_payload','boolean_input'):
   bad=copy.deepcopy(j)
   if change=='missing_cap':bad['resources'].pop('native_unit_limits')
   if change=='wrong_cap':bad['resources']['native_unit_limits']['file_size_bytes']=1
   if change=='physical':bad['resources']['physical_policy']={}
   if change=='extra_payload':bad['payload']['fallback']=True
   if change=='boolean_input':bad['payload']['cold_proof_input']=True
   with self.assertRaises(ValueError):env['schema'](bad)
  self.assertFalse(env['selected']({'kind':'fit','payload':{'representation_jobs':{}}}))
 def test_frozen_config_pins(self):
  tree=ast.parse((P/'compact_cold_proof.py').read_text())
  pins=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='CONFIG_PINS' for x in n.targets)))
  for role,name in [('recipe','recipe01.json'),('configs','configs01.json'),('model','model01.json'),('training','training01.json')]:
   b=json.dumps(json.loads((P/name).read_bytes()),sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode();self.assertEqual(hashlib.sha256(b).hexdigest(),pins[role])
 def test_native_job_unselected_whole_ast_parity(self):
  a=ast.parse((P/'job.py.baseline-native02').read_text());b=ast.parse((P/'job.py').read_text())
  class Strip(ast.NodeTransformer):
   def visit_FunctionDef(self,n):
    if n.name=='_cold_native':return None
    return self.generic_visit(n)
   def visit_If(self,n):
    # The proof-specific imports/calls reduce to absent on legacy input.
    if isinstance(n.test,ast.Call) and isinstance(n.test.func,ast.Name) and n.test.func.id=='_cold_native':return [self.visit(x) for x in n.orelse]
    return self.generic_visit(n)
   def visit_BoolOp(self,n):
    n=self.generic_visit(n)
    if isinstance(n.op,ast.And):n.values=[v for v in n.values if not (isinstance(v,ast.UnaryOp) and isinstance(v.op,ast.Not) and isinstance(v.operand,ast.Call) and isinstance(v.operand.func,ast.Name) and v.operand.func.id=='_cold_native')]
    if isinstance(n.op,ast.Or):n.values=[v for v in n.values if not (isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='_cold_native')]
    return n.values[0] if len(n.values)==1 else n
  b=Strip().visit(b)
  self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
 def test_only_declared_synthetic_dictionary_override(self):
  root=P.parents[1]/'config';cfg=json.loads((P/'configs01.json').read_bytes());original=json.loads((root/'dictionary.json').read_bytes())
  self.assertEqual(cfg['dictionary'],original|{'sample_count':32})
  for n,source in [('matching','matching-stable'),('graph','graph'),('baselines','baselines')]:self.assertEqual(cfg[n],json.loads((root/(source+'.json')).read_bytes()))
  for n in ('model','training'):self.assertEqual((P/(n+'01.json')).read_bytes(),(root/(n+'.json')).read_bytes())
 def test_no_numeric_import_in_preclaim_module(self):
  tree=ast.parse((P/'compact_cold_proof_native.py').read_text())
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):self.assertFalse({a.name.split('.')[0] for a in n.names}&{'numpy','torch','pandas','pyarrow'})
   if isinstance(n,ast.ImportFrom):self.assertNotIn((n.module or '').split('.')[0],{'numpy','torch','pandas','pyarrow'})
if __name__=='__main__':unittest.main(verbosity=2)
