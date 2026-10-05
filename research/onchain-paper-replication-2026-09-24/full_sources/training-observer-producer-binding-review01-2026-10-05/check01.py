"""Finite source/plan-expression review; no Run, Admission, arrays or publication."""
import ast,copy,hashlib,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[2]
RECEIPT=BASE/'training-observer-producer-binding01-2026-10-05'
SOURCE=ROOT/'tradingagents/research/onchain_replication'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def defs(p):return {n.name:n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
def dump(n):return ast.dump(n,include_attributes=False)
index=json.loads((BASE/'real-population-capacity-next-step-investigation01-2026-10-05/SOURCE_PIN_INDEX01.json').read_text())
pins={Path(r['path']).name:r['sha256'] for r in index['rows']}
for name in ['population_assembly.py','population_batch_projection.py']:
 assert sha(RECEIPT/(name+'.baseline'))==pins[name]
 assert (SOURCE/name).read_bytes()==(RECEIPT/name).read_bytes()
for name in ['training_batch_observer.py','evaluation.py']:assert sha(SOURCE/name)==pins[name]
assert (ROOT/'tests/research/onchain_replication/test_training_observer_projection.py').read_bytes()==(RECEIPT/'test_training_observer_projection.py').read_bytes()
before=defs(RECEIPT/'population_batch_projection.py.baseline');after=defs(SOURCE/'population_batch_projection.py')
assert all(dump(before[k])==dump(after[k]) for k in before if k!='publish_projection')
a=defs(RECEIPT/'population_assembly.py.baseline');b=defs(SOURCE/'population_assembly.py')
assert all(dump(a[k])==dump(b[k]) for k in a if k!='produce_registered_population')
# Evaluate only the actual local plan-schema/output expressions. No fake capability.
class LocalInputs(ast.NodeTransformer):
 def visit_Subscript(self,node):
  if ast.unparse(node)=="run.admission.experiment['outputs']":return ast.copy_location(ast.Name(id='registered',ctx=ast.Load()),node)
  return self.generic_visit(node)
 def visit_Attribute(self,node):
  if ast.unparse(node)=='run._published_outputs':return ast.copy_location(ast.Name(id='published',ctx=ast.Load()),node)
  return self.generic_visit(node)
def predicate(fn):
 statements=[];started=False
 for n in fn.body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='treatment' for t in n.targets):started=True
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='refs' for t in n.targets):break
  if started:statements.append(copy.deepcopy(n))
 tree=ast.Module(body=statements,type_ignores=[]);tree=LocalInputs().visit(tree);ast.fix_missing_locations(tree)
 assert 'run.' not in ast.unparse(tree)
 code=compile(tree,'<source-local-plan-guards>','exec')
 def accepts(plan,registered,published=()):
  try:exec(code,{'plan':plan,'registered':registered,'published':published});return True
  except (ValueError,KeyError,TypeError):return False
 return accepts
legacy=predicate(a['produce_registered_population']);current=predicate(b['produce_registered_population'])
def plan(version,treatment=False):
 roles=['population','binding','assembly']+(['projection'] if version>=2 else [])+(['training_observer_projection'] if version==3 else [])
 p=dict(schema_version=version,graphs={},price_input='prices',fold={},calendar_input='calendar',expected_weeks=[],admission_input='admission',outputs={x:x+'.json' for x in roles})
 if version>=2:p['projection_input']='policy'
 if treatment:p['treatment_input']='treatment'
 return p
checks=[]
for v in (1,2,3):
 for treatment in (False,True):
  p=plan(v,treatment);registered=list(p['outputs'].values());assert current(p,registered)
  if v<3:assert legacy(p,registered)
  else:assert not legacy(p,registered)
  checks.append(f'v{v}/treatment{treatment}: accepted with exact {len(registered)} outputs')
p=plan(3);registered=list(p['outputs'].values())
cases=[]
x=copy.deepcopy(p);del x['outputs']['training_observer_projection'];cases.append(('missing_fifth',x,registered,()))
x=copy.deepcopy(p);x['outputs']['training_observer_projection']=x['outputs']['projection'];cases.append(('duplicate_fifth',x,registered,()))
x=copy.deepcopy(p);del x['projection_input'];cases.append(('missing_projection_policy',x,registered,()))
x=copy.deepcopy(p);x['outputs']['extra']='extra.json';cases.append(('extra_output',x,registered+['extra.json'],()))
cases.extend([('unregistered_fifth',p,registered[:-1],()),('published_fifth',p,registered,[p['outputs']['training_observer_projection']])])
for name,value,registered,published in cases:assert not current(value,registered,published);checks.append(name+': refused')
assert not {'torch','numpy','pandas','scipy'}&set(sys.modules)
print(json.dumps({'schema_version':1,'decision':'ACCEPTED_FUNCTIONAL_SOURCE_AND_PLAN_SCHEMA_ONLY','source_pins':{n:sha(SOURCE/n) for n in ['population_assembly.py','population_batch_projection.py','training_batch_observer.py','evaluation.py']},'test_sha256':sha(RECEIPT/'test_training_observer_projection.py'),'baseline_pins':{n:sha(RECEIPT/(n+'.baseline')) for n in ['population_assembly.py','population_batch_projection.py']},'unchanged_original_projection_functions':True,'checks':checks,'prior_five_test_receipt_sha256':sha(RECEIPT/'CHECKS01.json'),'numerical_imports':False,'genuine_run_constructed':False,'publication_executed':False},sort_keys=True,indent=2))
