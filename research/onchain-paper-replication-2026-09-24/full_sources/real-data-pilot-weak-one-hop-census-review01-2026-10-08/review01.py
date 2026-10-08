import ast, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
P=HERE.parent/'real-data-pilot-weak-one-hop-census-candidate01-2026-10-08'
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((P/'MANIFEST01.json').read_text())
for name,digest in m['files'].items():assert sha((P/name).read_bytes())==digest,name
raw=(P/'weak_one_hop_census.py').read_bytes()
assert sha(raw)=='4ee889efc0c70645f28f4188796718e93f588f98c98ae421eb222c7f54206b42'
ast.parse(raw);compile(raw,'weak_one_hop_census.py','exec')
# Pure integer boundary proof, no array allocations/import execution.
n=2**32
assert (n-1)*n+(n-1)==2**64-1
assert n<2**63
assert 16+1+8+8<=48
assert 8*10002+8*10001+48*127==166120
# Verify exact budget comparison itself at below/equal/above using extracted AST.
t=ast.parse(raw);f=next(x for x in t.body if isinstance(x,ast.FunctionDef))
predicate=next(x.test for x in f.body if isinstance(x,ast.If) and 'envelope >' in ast.unparse(x.test))
code=compile(ast.Expression(predicate),'budget-predicate','eval')
class Limit:maxsize=2**63-1
assert [eval(code,{'envelope':104,'max_work_bytes':b,'sys':Limit}) for b in (103,104,105)]==[True,False,False]
r={'decision':'ACCEPT source-only preparation helper','candidate_sha256':sha(raw),'author_manifest_sha256':sha((P/'MANIFEST01.json').read_bytes()),'checks':['retained manifest hashes match','source parses and compiles without execution','uint64 packing upper bound and int64 counts proved with Python integers','33B simultaneous explicit chunk arrays fit 48B envelope','hub envelope independently recalculated','actual budget predicate rejects below bound and permits equality'],'functional_evidence':'retained 512-pattern, duplicate/reciprocal/loop/stride/chunk and 10002-node hub tests inspected, not rerun','scope':'No NumPy/Torch imports, arrays, real graph census, authority, claims or native process execution'}
(HERE/'SOURCE_REVIEW01.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
