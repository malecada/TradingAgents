"""AST-only authority boundary checks; no genuine Owner or numerical imports."""
import ast, pathlib, types, unittest
P=pathlib.Path(__file__).with_name('held_tail_adapter.py')
class Held(unittest.TestCase):
 def helper(self):
  self.assertTrue(P.exists(),'typed held tail adapter is missing')
  tree=ast.parse(P.read_text());f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_joins')
  def require(test,message):
   if not test:raise ValueError(message)
  ns={'require':require};exec(compile(ast.Module(body=[f],type_ignores=[]),str(P),'exec'),ns);return ns['_joins']
 def test_exact_stage_token_and_denominator_rejoined(self):
  check=self.helper();owner=types.SimpleNamespace(identity='o',active=None,stages={},_binding_sha256='b')
  stage=types.SimpleNamespace(owner=owner,name='mcm-g',intent_sha256='s',kind='mcm',closed=False,pairs=64,scope={'workflow':'w'})
  owner.active=stage;owner.stages[stage.name]=stage
  c={'owner':'o','stage':'mcm-g','stage_intent_sha256':'s','binding_sha256':'b','rows':2,'scope':{'workflow':'w'}}
  check(owner,stage,c)
  for key,value in [('pairs',63),('closed',True),('intent_sha256','changed')]:
   before=getattr(stage,key);setattr(stage,key,value)
   with self.assertRaises(ValueError):check(owner,stage,c)
   setattr(stage,key,before)
  owner.active=object()
  with self.assertRaises(ValueError):check(owner,stage,c)
 def test_current_dispatch_cannot_be_repurposed(self):
  self.helper();tree=ast.parse(P.read_text());f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='bind_transport')
  self.assertTrue(any(isinstance(n,ast.Raise) for n in ast.walk(f)))
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('mkdir','put','get','binding') for n in ast.walk(f)))
if __name__=='__main__':unittest.main(verbosity=2)
