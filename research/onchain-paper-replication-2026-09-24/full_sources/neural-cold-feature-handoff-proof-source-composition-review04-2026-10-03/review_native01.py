"""Independent selected metadata helpers with explicit synthetic receipt values."""
import ast,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
C=BASE/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03';G=BASE/'neural-cold-feature-handoff-engineering-registration-preparation04-2026-10-03';B=BASE/'neural-cold-feature-handoff-root-capsule-builder-preparation02-2026-10-03'
def extract(p,names,ns):
 tree=ast.parse(p.read_bytes());ns['__name__']='review_only'
 exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(p),'exec'),ns);return ns
def refuse(call,reason):
 try:call()
 except ValueError as e:assert reason in str(e);return
 raise AssertionError('expected refusal')
source=C/'source-bodies/tradingagents/research/onchain_replication/resources.py';raw=source.read_bytes();root=Path('/synthetic-root-not-created');target='tradingagents/research/onchain_replication/resources.py'
actual=extract(source,{'_native_owned_env'},{'Path':Path})['_native_owned_env'](root)
assert actual['PYTHONPATH']==str(root) and actual['TMPDIR']==str(root/'fixture_runtime/tmp') and 'HOME' not in actual
assert all(actual[k]=='2' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'))
state={'document':actual,'body':raw}
ns=extract(G/'generate04.py',{'require','native_environment'},{'Path':Path,'ast':ast,'digest':lambda b:hashlib.sha256(b).hexdigest(),'document':lambda r,ref:state['document'],'body':lambda r,t:state['body']})
f=ns['native_environment'];sources={target:hashlib.sha256(raw).hexdigest()};request={'native_environment':{'synthetic':True}}
assert f(root,request,sources)==actual
state['document']={'distribution_records':[]};refuse(lambda:f(root,request,sources),'native shell environment')
state['document']=dict(actual,TMPDIR='/other-root/tmp');refuse(lambda:f(root,request,sources),'native shell environment')
state['document']=actual;state['body']=raw+b'\n';refuse(lambda:f(root,request,sources),'selected native helper source')
# Constants and actual source render expressions, never invoke render or compare.
tree=ast.parse((G/'generate04.py').read_bytes());constants={}
for n in tree.body:
 if isinstance(n,ast.Assign):
  try:constants[n.targets[0].id]=ast.literal_eval(n.value)
  except (ValueError,TypeError,AttributeError):pass
assert constants['PINNED_INVENTORY']==hashlib.sha256((C/'source_inventory04.json').read_bytes()).hexdigest()
for role,name in [('recipe','recipe01.json'),('configs','configs01.json'),('model','model01.json'),('training','training01.json')]:
 val=json.loads((C/name).read_bytes());encoded=json.dumps(val,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode();assert hashlib.sha256(encoded).hexdigest()==constants['CONFIG_PINS'][role]
render=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='render')
fields={}
for n in ast.walk(render):
 if isinstance(n,ast.Dict):
  for k,v in zip(n.keys,n.values):
   if isinstance(k,ast.Constant) and k.value in ('attempt_budget','prior_attempts','exposures','native_environment','execution_authorized'):fields.setdefault(k.value,[]).append(ast.unparse(v))
assert fields['attempt_budget']==['2'] and fields['prior_attempts']==['0'] and fields['exposures']==['[]']
assert fields['native_environment']==["request['native_environment']"] and set(fields['execution_authorized'])=={'False'}
# Frozen builder PINS may be validated as actual file contents without executing verify_preparation or Git/copy stages.
btree=ast.parse((B/'builder02.py').read_bytes());assigns=[n for n in btree.body if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in {'BASE','CSC','GEN','PINS','INV','GIB','MAX'} for t in n.targets)]
bn={};exec(compile(ast.Module(body=assigns,type_ignores=[]),'builder-constants-only','exec'),bn)
repo=HERE.parents[3]
for path,h in bn['PINS'].items():assert hashlib.sha256((repo/path).read_bytes()).hexdigest()==h
assert bn['INV']==constants['PINNED_INVENTORY']
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps({'status':'passed','synthetic_native_map_positive_and_three_refusals':True,'native_helper_SHA':hashlib.sha256(raw).hexdigest(),'four_canonical_config_pins_match':True,'family_budget':2,'prior_attempts':0,'exposures':[],'exact_builder_manifest_inventory_pins':True,'receipt_io':'explicit mocked document/body callbacks; helper body real and extracted','runtime_RECORDs_or_native_controls_observed':False,'actual_inputs_or_capsule_created':False,'numerical_imports':False},indent=2))
