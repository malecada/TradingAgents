"""Focused source/metadata check only; no module/native/numerical imports."""
import ast
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
M=D.parents[3]
# full_sources/directory -> study -> research -> checkout
assert (M/'tradingagents/research/onchain_replication').is_dir()
record=json.loads((D/'PREPARATION01.json').read_text())
for name,pin in record['copies_verbatim'].items():
 raw=(D/'candidate'/name).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==pin
 compile(raw,name,'exec')
base=(D/'main-job.baseline.py').read_text()
new=(D/'candidate/tradingagents/research/onchain_replication/job.py').read_text()
assert hashlib.sha256(new.encode()).hexdigest()==record['candidate_job_sha256']
restored=new
for before,after in reversed(json.loads((D/'DISPATCH_EDITS01.json').read_text())['edits']):
 assert restored.count(after)==1
 restored=restored.replace(after,before)
assert restored==base
compile(new,'candidate-job.py','exec')
old_ast=ast.parse(base);new_ast=ast.parse(new)
old_functions={n.name:ast.dump(n,include_attributes=False) for n in old_ast.body if isinstance(n,ast.FunctionDef)}
new_functions={n.name:ast.dump(n,include_attributes=False) for n in new_ast.body if isinstance(n,ast.FunctionDef)}
assert old_functions.keys()==new_functions.keys()
changed={n for n in old_functions if old_functions[n]!=new_functions[n]}
assert changed=={'job_schema','_admitted','worker'}
# Run only the actual, unchanged resource-policy function on synthetic metadata.
# It must refuse the required new key before any path, process or guard access.
policy=next(n for n in new_ast.body if isinstance(n,ast.FunctionDef) and n.name=='resource_policy')
namespace={}
exec(compile(ast.Module(body=[policy],type_ignores=[]),'actual-resource-policy','exec'),namespace)
value={k:1 for k in ('memory_max_bytes','memory_high_bytes','reserve_bytes','start_reserve_bytes','disk_floor_bytes','disk_paths','wall_seconds')}
value.update(storage_budget={},native_unit_limits={'file_size_bytes':4*1024**2})
try: namespace['resource_policy'](value,object())
except ValueError as error: assert str(error)=='execution resource policy fields differ'
else: raise AssertionError('native key unexpectedly admitted')
package=M/'tradingagents/research/onchain_replication'
def parsed(name):return ast.parse((package/name).read_text())
def function(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
bind=function(parsed('matching_owner.py'),'bind')
assert '_resource' not in {a.arg for a in [*bind.args.args,*bind.args.kwonlyargs]}
owner=next(n for n in parsed('compact_owner.py').body if isinstance(n,ast.ClassDef) and n.name=='Owner')
init=function(owner,'__init__')
assert 'imported' not in {a.arg for a in [*init.args.args,*init.args.kwonlyargs]}
assert 'produce_imported' not in {n.name for n in parsed('compact_mcm.py').body if isinstance(n,ast.FunctionDef)}
assert '_native_policy' not in {n.name for n in parsed('resources.py').body if isinstance(n,ast.FunctionDef)}
print(json.dumps({'status':'passed','verbatim_copies':15,'dispatcher_exact_inverse':True,
 'changed_functions':sorted(changed),'actual_native_key_refused_before_path_access':True,
 'missing_api_signatures_confirmed':['_native_policy','bind(_resource=...)','Owner(imported=...)','produce_imported'],
 'execution_ready':False,'numerical_modules_imported':False}))
