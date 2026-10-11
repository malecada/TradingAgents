import ast,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;D=P.parent/'real-data-pilot-full32-entry-preparation01-2026-10-11';R=P.parents[3]
g=json.loads((D/'gate01.json').read_bytes());b=json.loads((D/'BINDING_DRAFT01.json').read_bytes());exp=g['experiments'][b['identity']]
t=ast.parse((D/'preflight32_02.py').read_bytes());need=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='need');scope={};exec(compile(ast.Module(body=[need],type_ignores=[]),'actual-need','exec'),scope)
try:scope['need'](exp['cumulative_budget_extension']['review']==b['budget_review'],'genuine budget103 review differs')
except ValueError as e:failure=str(e)
else:raise AssertionError('expected current draft refusal absent')
refs={}
for p in (D/'gate01.json',D/'BINDING_DRAFT01.json',D/'preflight32_02.py'):
 raw=p.read_bytes();refs[str(p.relative_to(R))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
out={'decision':'REFUSE_ORIGINAL_BINDING_DRAFT01_ONLY','reason':failure,'binding_budget_review':b['budget_review'],'gate_budget_review':exp['cumulative_budget_extension']['review'],'evidence':refs,'required_correction':'Preserve draft01; remove only extra bytes field from budget_review in new draft. Equality guard unchanged. No genuine admission or preflight executed.'}
with (P/'REFUSAL01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(failure)
