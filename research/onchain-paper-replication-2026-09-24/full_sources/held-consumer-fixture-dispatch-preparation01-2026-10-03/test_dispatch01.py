import ast,copy,json,os,unittest
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;T=H.parent/'held-consumer-positive-case-contract-investigation01-2026-10-03';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-03/source/tradingagents/research/onchain_replication')
P=Path(os.environ.get('CANDIDATE_SOURCE',H/'resource_fixture.py'))
def functions(path,names,ns):
 t=ast.parse(path.read_bytes());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id in names for v in n.targets)];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
ns={'Path':Path};functions(P,{'KEYS','require','selection'},ns);cs={'Path':Path};functions(S/'held_score_consumer.py',{'KIND','require','_policy'},cs)
pre=next(n for n in ast.parse(P.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='preflight');out=[];take=False
for n in pre.body:
 if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='outputs' for x in n.targets):take=True
 if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='control' for x in n.targets):break
 if take:out.append(n)
class Imports(ast.NodeTransformer):
 def visit_ImportFrom(self,node):return ast.copy_location(ast.Pass(),node)
fragment=compile(ast.fix_missing_locations(Imports().visit(ast.Module(body=out,type_ignores=[]))),str(P),'exec')
class Tests(unittest.TestCase):
 def setUp(self):
  self.job=json.loads((T/'JOB_TEMPLATE01.json').read_bytes());self.plan=json.loads((T/'PLAN_TEMPLATE01.json').read_bytes());self.policy=json.loads((T/'HELD_POLICY01.json').read_bytes());self.s=self.job['payload']['representation_jobs']['original32'];self.item=self.plan['producers']['original32'];self.outputs=['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json']+[v['output'] for v in self.policy['targets'].values()]
 def check(self,registered=True):
  ns['selection'](self.job);raw=json.dumps(self.policy).encode();run=SimpleNamespace(admission=SimpleNamespace(experiment={'outputs':self.outputs},inputs={'held_score_policy':{}} if registered else {}));orig=SimpleNamespace(parse=json.loads,_read_registered=lambda r,n:raw)
  env=dict(ns,run=run,s=self.s,item=self.item,original=orig,held_score_consumer=SimpleNamespace(_policy=cs['_policy']));exec(fragment,env)
 def test_default(self):
  del self.s['held_score_consumer_input'];del self.item['held_score_consumer_input'];self.outputs=self.outputs[:4];self.check()
 def test_selected(self):self.check()
 def test_bad_selector(self):
  for v in [None,True,'']:
   self.s['held_score_consumer_input']=v
   with self.assertRaises(ValueError):self.check()
 def test_unknown_selector(self):
  self.s['held_score_typo']='x'
  with self.assertRaises(ValueError):self.check()
 def test_missing_registered_policy(self):
  with self.assertRaises(ValueError):self.check(False)
 def test_missing_output(self):
  self.outputs.pop()
  with self.assertRaises(ValueError):self.check()
 def test_extra_output(self):
  self.outputs.append('extra.json')
  with self.assertRaises(ValueError):self.check()
 def test_target_mismatch(self):
  self.policy['targets'].pop(next(iter(self.policy['targets'])))
  with self.assertRaises(ValueError):self.check()
 def test_output_conflict(self):
  self.policy['targets'][next(iter(self.policy['targets']))]['output']='resource-binding.json'
  with self.assertRaises(ValueError):self.check()
 def test_bool_and_mutated_policy(self):
  self.check();self.policy['max_read_bytes']=True
  with self.assertRaises(ValueError):self.check()
 def test_oversize_policy(self):
  self.policy['extra']='x'*8192
  with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main(verbosity=2)
