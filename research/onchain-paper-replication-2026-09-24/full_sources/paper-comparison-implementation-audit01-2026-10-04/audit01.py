"""Bounded source AST/metadata snapshot; never imports research/numerical modules."""
import ast,hashlib,json,os,stat,subprocess
from pathlib import Path
from coverage_contract01 import check
H=Path(__file__).resolve().parent;R=H.parents[1];MAIN=R.parents[1];P=MAIN/'tradingagents/research/onchain_replication'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2
 b=p.read_bytes();assert len(b)==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns;return b
def put(n,x):
 with (H/n).open('xb') as f:f.write(json.dumps(x,indent=2,sort_keys=True).encode()+b'\n')
paths=[P/(n+'.py') for n in ('model_registry','model','temporal','graph_baselines','baselines','subsets','btc_subsets','cells','comparison','feature_pipeline','registered_features','run','evaluation','job','job_payload','population_assembly','graph_production','training','metrics','contracts')]
paths += [MAIN/'tests/research/onchain_replication'/n for n in ('test_graph_baselines.py','test_subsets.py','test_btc_subsets.py','test_registry.py','test_comparison.py','test_feature_pipeline.py','test_metrics_baselines.py','test_cells.py')]
paths += [R/n for n in ('REPLICATION_SPEC.md','TABLE_COVERAGE.md','fidelity.json','PROTOCOL.md','SOURCE_AUDIT.md','DECISIONS.md','table-map.json','protocol-freeze-v5.json','config/baselines.json','config/training.json','config/model.json','config/dictionary.json','config/matching-stable.json')]
paths += [MAIN/'docs/superpowers/plans/2026-09-24-onchain-paper-replication.md']
paths += [CAP/'tradingagents/research/onchain_replication'/n for n in ('financial_execution.py','financial_wrapper_fixture.py','model_registry.py','job.py')]
pins=[]
for i,p in enumerate(paths):
 b=read(p);target=H/'snapshot'/str(i);target.parent.mkdir(exist_ok=True);target.write_bytes(b)
 row={'path':str(p),'bytes':len(b),'sha256':sha(b),'mode':stat.S_IMODE(p.stat().st_mode),'snapshot':str(target.relative_to(H))}
 if p.suffix=='.py':
  tree=ast.parse(b);row['definitions']=[{'name':n.name,'line':n.lineno,'kind':type(n).__name__} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef))];row['calls']=sorted({ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)})
 pins.append(row)
rows=json.loads(read(R/'table-map.json'));training=json.loads(read(R/'config/training.json'));coverage=check(rows,training)
# Execute only exact original pure metadata functions, removing imports; no modules imported.
env={'cache_key':lambda x:sha(json.dumps(x,sort_keys=True).encode())}
for name,functions in [('cells',{'enumerate_cells','initial_cells'}),('comparison',{'execution_batches'})]:
 tree=ast.parse(read(P/(name+'.py')));body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions];assert {n.name for n in body}==functions;exec(compile(ast.Module(body=body,type_ignores=[]),'<exact-pure-metadata-'+name+'>','exec'),env)
actual=env['enumerate_cells'](rows,training);batches=env['execution_batches'](rows,training)
assert [c['id'] for c in actual]==[c['id'] for c in coverage['cells']]
assert [(b['id'],b['cells']) for b in batches['batches']]==[(b['id'],b['cell_ids']) for b in coverage['batches']]
put('COVERAGE01.json',coverage);put('SOURCE_PINS01.json',pins)
# Scope-limited whole package AST call census for missing treatment dispatch.
calls=[];definitions=[]
for p in sorted(P.glob('*.py')):
 raw=read(p);t=ast.parse(raw)
 for n in ast.walk(t):
  if isinstance(n,ast.Call) and ('filter_graph' in ast.unparse(n.func) or 'filter_btc_graph' in ast.unparse(n.func)):calls.append({'path':str(p),'sha256':sha(raw),'line':n.lineno,'call':ast.unparse(n.func)})
  if isinstance(n,ast.FunctionDef) and n.name in ('make_graph_baseline','apply_variant'):definitions.append({'path':str(p),'line':n.lineno,'name':n.name})
put('CALL_CENSUS01.json',{'scope':str(P),'filter_calls':calls,'plan_interface_names_found':definitions,'not_a_dynamic_call_graph':True})
registry=ast.parse(read(P/'model_registry.py'));fn=next(n for n in registry.body if isinstance(n,ast.FunctionDef) and n.name=='build_model')
put('REGISTRY_DISPATCH01.json',{'path':str(P/'model_registry.py'),'sha256':sha(read(P/'model_registry.py')),'actual_function_ast':ast.dump(fn,include_attributes=False),'branches':[{'line':n.lineno,'condition':ast.unparse(n.test),'returns':[ast.unparse(k.value) for k in ast.walk(n) if isinstance(k,ast.Return)]} for n in fn.body if isinstance(n,ast.If)],'executed':False})
put('READBACK01.json',{'source_bodies':len(pins),'exact_live_pure_metadata_agrees':True,'fits':len(actual),'batch_count':len(batches['batches']),'initial':len(env['initial_cells'](actual)),'numeric_imports':False,'fits_executed':0,'claim_budget_authority':None})
print(len(pins),'source bodies;',len(actual),'metadata cells;',len(batches['batches']),'batches')
