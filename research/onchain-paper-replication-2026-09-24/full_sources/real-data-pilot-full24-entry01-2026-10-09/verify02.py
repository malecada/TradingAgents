"""Changed ancestry/age seam only. No real admission, Git mutation or preflight."""
import ast,copy,datetime,difflib,json,types
from pathlib import Path
H=Path(__file__).resolve().parent
before=(H/'preflight24.py').read_text();after=(H/'preflight24_02.py').read_text();tree=ast.parse(after)
def need(value,message):
 if not value:raise ValueError(message)
trace=[]
sub=types.SimpleNamespace(run=lambda argv,**kw:(trace.append(('ancestor',argv)) or types.SimpleNamespace(returncode=0)))
ns=dict(need=need,datetime=datetime,subprocess=sub,ROOT=Path('/synthetic'),authenticate_committed=lambda anchor,pins:trace.append(('source_body_join',anchor,len(pins))))
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_capacity_source');exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual changed helper>','exec'),ns)
pins={f'metadata/source{i}.py':'a'*64 for i in range(365)}
c=dict(source_anchor='b'*40,source_body_pins=pins,at='2000-01-01T00:00:00+00:00');public={'source_pins':pins}
ns['_capacity_source'](c,public,pins,'c'*40);assert [x[0] for x in trace]==['ancestor','source_body_join'];checks=['old_declaration_no_expiry','ancestor_then_exact_body_join']
for label,change in [('source_self_reference',{'source':'c'*40}),('obsolete_expiry',{'max_age_seconds':300}),('future_timestamp',{'at':'2999-01-01T00:00:00+00:00'}),('naive_timestamp',{'at':'2000-01-01T00:00:00'}),('changed_map',{'source_body_pins':{}})]:
 x=copy.deepcopy(c);x.update(change)
 try:ns['_capacity_source'](x,public,pins,'c'*40)
 except ValueError:checks.append('refuse_'+label)
 else:raise AssertionError(label)
changed=dict(pins);changed[next(iter(changed))]='d'*64
try:ns['_capacity_source'](c,public,changed,'c'*40)
except ValueError:checks.append('refuse_current_admission_changed_pin')
else:raise AssertionError('changed current pin')
sub.run=lambda *a,**k:types.SimpleNamespace(returncode=1)
try:ns['_capacity_source'](c,public,pins,'c'*40)
except ValueError:checks.append('refuse_nonancestor')
else:raise AssertionError('nonancestor')
# Every original function except the narrow prepared_inputs seam is unchanged.
base=ast.parse(before)
for old in base.body:
 if isinstance(old,(ast.FunctionDef,ast.AsyncFunctionDef)) and old.name!='prepared_inputs':
  new=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==old.name);assert ast.dump(new)==ast.dump(old),old.name
checks.append('all_other_original_functions_AST_identical')
assert (H/'root_io24_02.py').read_text().replace('from preflight24_02 import check','from preflight24 import check')==(H/'root_io24.py').read_text();checks.append('literal_rootio_inverse')
(H/'inverse02.patch').write_text(''.join(difflib.unified_diff(after.splitlines(True),before.splitlines(True),fromfile='preflight24_02.py',tofile='preflight24.py')))
r=dict(status='PASS_CHANGED_SEAM_ONLY',checks=checks,genuine_preflight_executed=False,git_or_private_body_read=False)
(H/'RESULT02.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
