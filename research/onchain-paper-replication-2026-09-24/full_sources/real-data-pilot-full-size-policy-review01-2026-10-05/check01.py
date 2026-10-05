from pathlib import Path
import ast,hashlib,json,sys
D=Path(__file__).resolve().parent;M=D.parents[3];A=D.parent/'real-data-pilot-full-size-policy01-2026-10-05';P=Path('tradingagents/research/onchain_replication');T=A/'candidate'/P
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(A/'MANIFEST01.json')=='ca40a8638e3e2a722ebab86aeab8c35f5d08f144ddcc29fca9c21efc311f8972'
manifest=json.loads((A/'MANIFEST01.json').read_text())
for row in manifest['members']:
 p=A/row['path'];assert h(p)==row['sha256'] and p.stat().st_size==row['bytes']
delta=json.loads((A/'SOURCE_DELTA01.json').read_text())
for r in delta['files']:
 p=Path(r['path']);raw=(A/'candidate'/p).read_bytes();assert h(M/p)==r['baseline_sha256']==h(A/'baseline'/p.name);assert hashlib.sha256(raw).hexdigest()==r['candidate_sha256'];lines=raw.decode().splitlines(True)
 for e in reversed(r['edits']):assert lines[e['new_start']:e['new_end']]==e['new'];lines[e['new_start']:e['new_end']]=e['old']
 assert ''.join(lines).encode()==(M/p).read_bytes()
def functions(p):return {n.name:n for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
changed={'resources.py':{'_native_policy'},'resource_fixture.py':{'publication_boundary'},'job.py':{'worker','_resource_limit_receipt'},'real_pilot_import_caller.py':{'schema','validate_plan','admitted'}}
unchanged=[]
for name,exceptions in changed.items():
 old=functions(A/'baseline'/name);new=functions(T/name)
 for n,node in old.items():
  if n not in exceptions:assert ast.dump(node)==ast.dump(new[n]);unchanged.append(name+':'+n)
# Counterexample: widening the low-level validator must not admit graph jobs
# carrying native policy. Execute only actual pure early job-schema refusal.
f=functions(T/'job.py')['job_schema'];env={};exec(compile(ast.Module(body=[f],type_ignores=[]),str(T/'job.py'),'exec'),env)
job={'schema_version':1,'kind':'graphs','resources':{'native_unit_limits':{'file_size_bytes':16*1024**2}},'environment_input':'synthetic','payload':{'plan_input':'synthetic'}}
try:env['job_schema'](job)
except ValueError as error:assert str(error)=='native-only file limits require compact_resource'
else:raise AssertionError('large graph file policy accepted')
# Pure policy-shape checks reject bool masquerading as the exact selected size,
# without calling resource.setrlimit or loading any actual owner/guard.
n=functions(T/'resources.py')['_native_policy'];e={};exec(compile(ast.Module(body=[n],type_ignores=[]),str(T/'resources.py'),'exec'),e)
assert e['_native_policy'](None) is None
for invalid in [True,2**63]:
 try:e['_native_policy']({'file_size_bytes':invalid})
 except ValueError:pass
 else:raise AssertionError('nonfinite/bool native policy accepted')
assert e['_native_policy']({'file_size_bytes':16*1024**2})=={'file_size_bytes':16*1024**2}
assert not {'numpy','torch','scipy','networkx'}&set(sys.modules)
print(json.dumps({'decision':'pass','manifest_members':len(manifest['members']),'exact_inverse_and_current_baselines':4,'unchanged_existing_functions':unchanged,'counterexample':'native-policy graph route refused despite wider low-level native validator','nativeNone_preserved':True,'native_limit_boolean_and_overflow_refused':True,'numerical_imports':False,'process_limits_changed':False,'authority_objects_or_native_execution':False},sort_keys=True,indent=2))
