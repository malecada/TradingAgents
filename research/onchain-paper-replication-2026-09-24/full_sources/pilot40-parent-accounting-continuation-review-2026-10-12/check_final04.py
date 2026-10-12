from pathlib import Path
import os,resource
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
import ast,runpy,json,hashlib,difflib
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');C=F/'pilot40-parent-accounting-continuation-candidate-2026-10-12';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((C/'SOURCE_MANIFEST04.json').read_text());assert h(C/'SOURCE_MANIFEST04.json')=='2f583d916aa7316d8b4bc3754ccf44fdf5c7fd727e5ed93558de56eaf22bf19a'
for row in m['files']:
 p=Path(row['path']);assert h(p)==row['sha256'] and p.stat().st_size==row['bytes']
a=(C/'BASELINE_batched_continuation.py').read_text();b=(C/'batched_continuation.py').read_text();name='tradingagents/research/onchain_replication/batched_continuation.py'
assert ''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+name,tofile='b/'+name))==(C/'CANDIDATE04.diff').read_text()
assert ''.join(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='b/'+name,tofile='a/'+name))==(C/'INVERSE04.diff').read_text()
t=ast.parse(b);t.body=[n for n in t.body if not(isinstance(n,ast.FunctionDef) and n.name in ('_original39_contract','_original39_accounting'))];f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_authority');f.body=[n for n in f.body if not(isinstance(n,ast.If) and ast.unparse(n.test)=="'parent_accounting_mode' in m")];assert ast.dump(t)==ast.dump(ast.parse(a))
ns=runpy.run_path(str(C/'check02.py'));fixture=ns['Checks']();count=0
for field in ['spent_counters','retained_partial_work','manifest_spent']:
 for value in [False,0.0]:
  d=fixture.fixture();target=d[1]['spent_counters'] if field=='manifest_spent' else d[0][field];target['checkpoint_attempts']=value
  try:fixture.call(d)
  except ValueError:count+=1
  else:raise AssertionError((field,value))
assert fixture.call(fixture.fixture())['spent_counters']==ns['fixed']['costs']
print(json.dumps({'status':'PASS','new_bool_float_refusals':count,'valid_exact_integer_proof':True,'full_default_module_ast_restored':True,'literal_inverse':True,'candidate_sha256':h(C/'batched_continuation.py'),'builder_executed_or_reviewed':False},indent=2))
