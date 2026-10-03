"""Extracted actual selection with qualified synthetic object/type/source stand-ins."""
import ast,json,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Selection(unittest.TestCase):
 def test_selection_refusals_and_default(self):
  tree=ast.parse((P/'held_score_consumer.py').read_text());func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_route');func.body=[n for n in func.body if not isinstance(n,ast.ImportFrom)]
  h='a'*64;calls=[]
  class Owner:pass
  class Target:
   def check(self):calls.append('target')
  owner=Owner();target=Target();target.owner=owner;target.key=h
  selected={'descriptor':{'required_graphs':[h]},'binding_output':'binding.json'};item={}
  target.execution=types.SimpleNamespace(_stage=types.SimpleNamespace(prepared=types.SimpleNamespace(_selection_now=lambda:{'selected':selected,'producer':item})))
  policy={'schema_version':1,'kind':'original-import-held-score-readback-v1','targets':{h:{'output':'read.json'}},'part_bytes':8,'max_read_bytes':1024,'max_members':10}
  run=types.SimpleNamespace(admission=types.SimpleNamespace(inputs={'policy':{}},experiment={'outputs':['read.json','binding.json']}),read_input=lambda n:json.dumps(policy).encode())
  owner.bound=types.SimpleNamespace(record={'resource_only':True},_run=run)
  def require(v,m):
   if not v:raise ValueError(m)
  ns={'imported_mcm_identity':types.SimpleNamespace(Target=Target),'compact_owner':types.SimpleNamespace(Owner=Owner),'FIELD':'held_score_consumer_input','require':require,'json':json,'_sources':lambda r:calls.append('source')}
  policyfunc=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_policy')
  ns.update(KIND='original-import-held-score-readback-v1',Path=Path)
  exec(compile(ast.fix_missing_locations(ast.Module(body=[policyfunc,func],type_ignores=[])),'actual selection','exec'),ns)
  self.assertIsNone(ns['_route'](target));self.assertEqual(calls,['target'])
  selected['held_score_unknown']=True
  with self.assertRaisesRegex(ValueError,'unknown'):ns['_route'](target)
  del selected['held_score_unknown'];selected['held_score_consumer_input']='policy'
  with self.assertRaisesRegex(ValueError,'job/plan'):ns['_route'](target)
  item['held_score_consumer_input']='policy';self.assertEqual(ns['_route'](target)[1],'policy')
  policy['targets'][h]['output']='binding.json'
  with self.assertRaisesRegex(ValueError,'conflicts'):ns['_route'](target)
  policy['targets'][h]['output']='read.json';owner.bound.record['resource_only']=False
  with self.assertRaisesRegex(ValueError,'resource input'):ns['_route'](target)
if __name__=='__main__':unittest.main(verbosity=2)
