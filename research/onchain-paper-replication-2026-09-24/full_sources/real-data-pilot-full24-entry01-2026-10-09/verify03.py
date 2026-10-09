"""Actual public metadata roster regression; no admission or private-body reads."""
import ast,hashlib,json,difflib
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent
old=(P/'preflight24_02.py').read_text();new=(P/'preflight24_03.py').read_text()
reverse=new.replace("    bound=read(binding['transport_binding'])\n    changed={'archive_transport','matching_ordered_edge_scratch'}|set(bound['inputs'])","    changed={'archive_transport','archive_policy','producer_plan','execution_job','matching_ordered_edge_scratch'}").replace("prepared=read(binding['preparation']);unbound=read(binding['unbound_archive'])","prepared=read(binding['preparation']);unbound=read(binding['unbound_archive']);bound=read(binding['transport_binding'])")
assert reverse==old
assert (P/'root_io24_03.py').read_text().replace('from preflight24_03 import check','from preflight24_02 import check')==(P/'root_io24_02.py').read_text()
prior=json.loads((F/'real-data-pilot-full24-input-binding01-2026-10-09/PUBLIC_INPUT_REFS04.json').read_text())
bound=json.loads((F/'real-data-pilot-full24-transport-binding01-2026-10-09/BOUND01.json').read_text());actual=json.loads((F/'real-data-pilot-full24-transport-binding01-2026-10-09/ALL_INPUT_REFS01.json').read_text())
def mismatch(changed):return sorted(role for role,ref in prior.items() if role not in changed and actual[role]['sha256']!=ref['sha256'])
old_refused=mismatch({'archive_transport','archive_policy','producer_plan','execution_job','matching_ordered_edge_scratch'})
new_changed={'archive_transport','matching_ordered_edge_scratch'}|set(bound['inputs'])
assert len(old_refused)==8 and not mismatch(new_changed)
# Exercise the actual changed AST assignment, not a separately assumed expression.
fn=next(x for x in ast.parse(new).body if isinstance(x,ast.FunctionDef) and x.name=='prepared_inputs')
node=next(x for x in fn.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='changed' for t in x.targets))
ns={'bound':bound};exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual changed roster>','exec'),ns);assert ns['changed']==new_changed
inherited=next(role for role in prior if role not in new_changed);keep=actual[inherited]['sha256'];actual[inherited]['sha256']='0'*64;assert inherited in mismatch(new_changed);actual[inherited]['sha256']=keep
root=P.parents[3]
for role,document in bound['inputs'].items():
 path=root/actual[role]['path'];body=path.read_bytes();assert hashlib.sha256(body).hexdigest()==actual[role]['sha256'] and json.loads(body)==document
(P/'inverse03.patch').write_text(''.join(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile='preflight24_03.py',tofile='preflight24_02.py')))
r={'status':'PASS_CHANGED_ROSTER_ONLY','old_refusal_roles':old_refused,'new_bound_public_documents':len(bound['inputs']),'inherited_mismatch_refused':True,'literal_full_inverse':True,'actual_public_body_hash_and_decoded_equality':True,'genuine_preflight_or_private_read':False}
(P/'RESULT03.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
