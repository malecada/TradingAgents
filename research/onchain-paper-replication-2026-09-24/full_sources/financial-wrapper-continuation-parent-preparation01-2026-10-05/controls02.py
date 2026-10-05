"""Additional frozen dependency checks after adding literal builder input pins."""
from pathlib import Path
import ast, hashlib, json
import build01 as B
H=Path(__file__).resolve().parent
checks=[]
for n,pin in B.PREPARATION_PINS.items():
 assert hashlib.sha256((H/n).read_bytes()).hexdigest()==pin
 checks.append('literal dependency '+n)
body=(H/'SOURCE_MANIFEST_DRAFT01.json').read_bytes()
try:B.build({'path':str(H/'SOURCE_MANIFEST_DRAFT01.json'),'sha256':hashlib.sha256(body).hexdigest()},{'path':str(H/'proof_reuse_contract01.json'),'sha256':B.PREPARATION_PINS['proof_reuse_contract01.json']})
except ValueError as error:assert error.args==('exact digest',);checks.append('all actual template pins pass then null actual source refuses')
else:raise AssertionError('missing future source admitted')
for p in H.glob('*.py'):ast.parse(p.read_bytes());checks.append('parse '+p.name)
result={'checks':checks,'count':len(checks),'public_preflight':False,'actual_adopted_builder_success':False,'authority':False}
with (H/'CONTROLS02.json').open('xb') as f:f.write((json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode())
print(json.dumps({'passed':len(checks),'status':'SOURCE_ONLY'}))
