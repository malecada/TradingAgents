"""Exact header/request/helper inverse and draft refusal; no launch or public preflight."""
import ast,json,os
from pathlib import Path
import build01 as B
H=B.H;rows=[]
def ok(n,v):
 assert v,n
 rows.append(n)
receipt=json.loads((H/'READBACK01.json').read_bytes());candidate=H/'candidate';old=(H/'original_parent01.py').read_text();new=(candidate/'parent01.py').read_text();inverse=new
for e in reversed(receipt['caller_inverse']):assert inverse.count(e['new'])==1;inverse=inverse.replace(e['new'],e['old'])
ok('whole caller byte inverse',inverse==old);ok('whole caller AST inverse',ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False))
oldq=json.loads((H/'original_REQUEST_DRAFT01.json').read_bytes());q=json.loads((candidate/'REQUEST_DRAFT01.json').read_bytes())
allowed={'source','design_source','parent_root','registration_sha256','source_files','input_hashes','caller_sha256','helper_hashes'}
ok('all other request fields unchanged',all(v==q[k] for k,v in oldq.items() if k not in allowed))
ok('all actualproofsnull',all(v is None for v in q['proofs'].values()) and q['final_review'] is None)
ok('fixed unchanged unusedidentity',q['identity']==oldq['identity']==B.ID)
ok('exact newroot and currentdesign',q['parent_root']==str(B.TARGET) and q['source']==q['design_source']==B.SOURCE)
ok('29correctactualroles',len(q['input_hashes'])==29 and 'historical_plan' in q['input_hashes'] and 'historical_wrapper_plan' not in q['input_hashes'])
for n,pin in oldq['helper_hashes'].items():
 if n!='proof_reuse_contract01.json':ok('unchanged helper '+n,(candidate/n).read_bytes()==(H/n).read_bytes() and B.sha((candidate/n).read_bytes())==pin)
oldc=(H/'original_proof_reuse_contract01.json').read_bytes();newc=(candidate/'proof_reuse_contract01.json').read_bytes();ok('contract exact one source literal inverse',newc.replace(B.SOURCE.encode(),B.OLD_SOURCE.encode())==oldc and newc.count(B.SOURCE.encode())==1)
ok('seven accepted anchors unchanged',json.loads(oldc)['anchors']==json.loads(newc)['anchors'])
# Extract actual validator with its real require dependency. Draft refuses before any proof IO.
tree=ast.parse(new);validate=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_release');module=ast.Module(body=[validate],type_ignores=[]);env={'require':B.need,'CAP':B.CAP};exec(compile(ast.fix_missing_locations(module),'actual_parent_validate_release','exec'),env)
try:env['validate_release'](q)
except ValueError as e:ok('actual draft validator refuses',str(e)=='no draft release')
else:raise AssertionError('draft released')
ok('fixed Root destination still absent',not os.path.lexists(B.TARGET))
owned=H/'occupied-control';owned.mkdir(mode=0o700);saved=B.TARGET;B.TARGET=owned
try:
 try:B.fresh()
 except ValueError:rows.append('actual owned occupied destination refused')
 else:raise AssertionError('existing target accepted')
finally:B.TARGET=saved
print(json.dumps({'passed':len(rows),'checks':rows,'Root_materialized':False,'public_preflight':False,'numerical_execution':False},sort_keys=True))
