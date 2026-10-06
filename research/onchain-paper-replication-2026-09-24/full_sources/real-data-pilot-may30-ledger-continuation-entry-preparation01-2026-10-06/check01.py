from pathlib import Path
import ast,hashlib,json,importlib.util,sys
H=Path(__file__).resolve().parent;R=H.parents[3]
for name in ('prepare01.py','preflight01.py','launch01.py'):ast.parse((H/name).read_bytes())
v=json.loads((H/'INVERSE01.json').read_text());s=(R/v['baseline']).read_text();assert hashlib.sha256(s.encode()).hexdigest()==v['before_sha256']
for e in v['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'])
assert s==(H/'preflight01.py').read_text();assert (H/'launch01.py').read_bytes()==(R/v['launcher_baseline']).read_bytes()
sp=importlib.util.spec_from_file_location('entry_metadata',H/'prepare01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
d=json.loads((H/'BINDINGS_DRAFT01.json').read_text())
try:m.prepare(d,H/'never-emitted')
except ValueError as e:assert 'unavailable' in str(e)
else:raise AssertionError('missing proofs accepted')
assert not (H/'never-emitted').exists()
wrong={k:{} for k in d};wrong['identity']='eth-paper-real-pilot-graph-20220530-20261005-01'
try:m.validate_binding(wrong)
except ValueError as e:assert 'fixed fresh continuation identity' in str(e)
else:raise AssertionError('old identity accepted')
# Before any actual admission, check reads and validates exact missing bindings.
t=ast.parse((H/'preflight01.py').read_text());fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='check');assert 'validate_binding' in ast.unparse(fn.body[1])
assert not any(n in sys.modules for n in ('numpy','sqlite3','torch'))
print('PASS preflight literal inverse; launcher identical; null bindings refuse without output; old identity refusal; pre-admission ordering; no scientific imports')
