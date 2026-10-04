from pathlib import Path
import ast,copy,hashlib,json
H=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();canonical=lambda o:json.dumps(o,sort_keys=True,separators=(',',':'),allow_nan=False).encode();checks=json.loads((H/'CHECKS01.json').read_bytes());assert checks['checks']==1644 and all(r['passed'] for r in checks['rows']);assert (H/'CHECK02.err').read_bytes()==b''
raw=(H/'POLICY01.json').read_bytes();policy=json.loads(raw);hist=policy['historical'];target=policy['target'];helper_sha=sha((H/'operational_source_compatibility.py').read_bytes());role='operational_source_compatibility_review'
proof={'schema_version':1,'kind':role,'policy_sha256':sha(raw),'historical_map_sha256':sha(canonical(hist['installed'])),'target_map_sha256':sha(canonical(target['installed'])),'checker_sha256':helper_sha,'decision':'accepted'}
module=ast.parse((H/'operational_source_compatibility.py').read_bytes());context=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='_context')
expressions=[]
for n in ast.walk(context):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and n.args and ('set(proof)' in ast.unparse(n.args[0]) or "proof['policy_sha256']" in ast.unparse(n.args[0])):expressions.append(n.args[0])
assert len(expressions)==2
codes=[compile(ast.Expression(e),'actual-seven-field-proof-predicate','eval') for e in expressions]
def accepts(p):return all(eval(c,{}, {'proof':p,'role':role,'raw':raw,'hist':hist,'target':target,'helper_sha':helper_sha,'sha':sha,'canonical':canonical}) for c in codes)
assert accepts(proof);rows=[{'case':'genuine independently authored exact review proof','passed':True}]
for key in proof:
 bad=copy.deepcopy(proof);bad[key]=None
 try:accepted=accepts(bad)
 except (KeyError,TypeError):accepted=False
 assert not accepted,key;rows.append({'case':'refuse null '+key,'passed':True})
bad=proof|{'kind':'operational_source_compatibility_recovery'};assert not accepts(bad);rows.append({'case':'review cannot stand in for recovery role','passed':True})
(H/'REVIEW_PROOF01.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n');(H/'PROOF_CHECKS01.json').write_text(json.dumps({'rows':rows,'predicate_AST':[ast.unparse(e) for e in expressions],'proof_schema_fields':sorted(proof),'scope':'Review only; no recovery proof generated or validated'},indent=2)+'\n')
print(json.dumps({'proof_sha256':sha((H/'REVIEW_PROOF01.json').read_bytes()),'checks':len(rows),'proof':proof}))
