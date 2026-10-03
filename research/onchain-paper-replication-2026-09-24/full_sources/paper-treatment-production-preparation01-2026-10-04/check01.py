"""Source/stdlib synthetic metadata only; no authority objects or graph arrays."""
import ast,copy,importlib.util,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'overlay/tradingagents/research/onchain_replication'
spec=importlib.util.spec_from_file_location('treatment_contract',O/'treatment_contract.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
checks=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuses(n,fn):
 try:fn()
 except (ValueError,TypeError,KeyError):checks.append(n)
 else:raise AssertionError(n)
# Opaque role names, not a Run, cohort, claim, actual graph or registration.
weeks=['2022-01-03T00:00:00Z','2022-01-10T00:00:00Z'];ref={'manifest_input':'opaque_manifest','coverage_input':'opaque_coverage','claim_input':'opaque_claim','terminal_input':'opaque_terminal','ledger_input':'opaque_ledger','components':{'edge_index.npy':'opaque_edges'}}
p={'schema_version':1,'kind':'paper-graph-treatment-v1','asset':'ETH','variant':'whale','coverage':[[weeks[0],'2022-01-17T00:00:00Z']],'expected_weeks':weeks,'parents':{w:copy.deepcopy(ref) for w in weeks},'cohort_input':None,'cohort_review_input':None}
ids=C.schema(p);ok('full two week identifiers',ids==['treatment-eth-whale-2022-01-03','treatment-eth-whale-2022-01-10'])
for label,mutate in [('missing week',lambda x:x['expected_weeks'].pop()),('missing parent',lambda x:x['parents'].pop(weeks[0])),('duplicate week',lambda x:x['expected_weeks'].append(weeks[0])),('wrong asset',lambda x:x.update(asset='DOGE')),('undeclared treatment',lambda x:x.update(variant='latest_funds')),('unknown field',lambda x:x.update(extra=True)),('boolean version',lambda x:x.update(schema_version=True)),('partial week',lambda x:x['coverage'][0].__setitem__(1,'2022-01-16T00:00:00Z')),('absolute role',lambda x:x['parents'][weeks[0]].update(manifest_input='/tmp/opaque')),('traversing component',lambda x:x['parents'][weeks[0]]['components'].update({'../escape.npy':'opaque'})),('unpaired cohort',lambda x:x.update(variant='fund',cohort_input='opaque_cohort'))]:
 q=copy.deepcopy(p);mutate(q);refuses(label,lambda q=q:C.schema(q))
q=copy.deepcopy(p);q.update(variant='fund');ok('unknown cohort keeps every source cell',len(C.schema(q))==2);q['asset']='BTC';refuses('fund scope BTC refused',lambda:C.schema(q))
refuses('no invented missing cohort',lambda:C.cohort({}, {}, '0'*64,weeks[0],weeks[1]))
refuses('no contemporary proxy',lambda:C.cohort({'schema_version':1,'kind':'latest_list','entities':{},'known_at':weeks[0],'valid_from':weeks[0],'valid_to':weeks[1],'evidence_inputs':{}},{},'0'*64,weeks[0],weeks[1]))
refuses('missing historical parent refuses',lambda:C.parent_receipts({}, {}, [],'0'*64,'1'*64,weeks[0],'ETH'))
# Exact job source inverse and legacy control-flow preservation.
inv=json.loads((H/'JOB_INVERSE01.json').read_bytes());new=(O/'job.py').read_text();restored=new
for item in reversed(inv['changes']):ok('one exact dispatch delta',restored.count(item['new'])==1);restored=restored.replace(item['new'],item['old'])
base=(H/'baseline-job.py').read_text();ok('full job byte inverse',restored==base);ok('full job AST inverse',ast.dump(ast.parse(restored))==ast.dump(ast.parse(base)))
t=ast.parse((O/'treatment_production.py').read_bytes());top=[n for n in t.body if isinstance(n,(ast.Import,ast.ImportFrom))];ok('no top-level numerical imports',all(not any(term in ast.unparse(n) for term in ['numpy','torch','graph_store','btc_store','subsets','graph_production']) for n in top))
f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='produce_registered_treatments');ok('guard is first producer operation',ast.unparse(f.body[0])=='_guard(run, plan_input)')
text=(O/'treatment_production.py').read_text();ok('unavailable cohort branch precedes array imports',text.index("if p['variant']=='fund' and p['cohort_input'] is None:")<text.index('from .graph_store import'))
# Exact pure first-fatal finalizer: scalar callbacks only.
close=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_close');env={};exec(compile(ast.Module(body=[close],type_ignores=[]),'<exact-finalizer>','exec'),env);events=[];primary=KeyboardInterrupt('first');secondary=MemoryError('second')
def fail():events.append('first-action');raise secondary
try:env['_close']((fail,lambda:events.append('second-action')),primary)
except BaseException as e:ok('original actual fatal wins',e is primary)
ok('all cleanup attempted',events==['first-action','second-action']);ok('no numerical module imported',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
(H/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'actual_native_commands':False,'numerical_imports':False,'research_run_constructed':False,'fund_addresses_created':False},indent=2)+'\n');print(len(checks),'passed')
