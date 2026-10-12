from pathlib import Path
import hashlib,json,difflib,shutil
P=Path(__file__).resolve().parent;R=P.parents[3]
shutil.copy2(P/'static_check01.py',P/'iteration02/static_check01.py')
p=P/'static_check01.py';s=p.read_text().replace("elif method.name in ('current','fill'):method.body=method.body[1:]","elif method.name=='current':method.body=method.body[:1]+method.body[2:]\n      elif method.name=='fill':method.body=method.body[1:]");p.write_text(s)
(P/'AMENDMENT03.md').write_text('''# Original currentness refusal order amendment03

Original02 policy16b0cccc340b7d646ac5ace7e41ee81bb264d822e4b738593b3ce1e107254240 and manifest1f7a80a3b0d0c688bb99642009eddcab2e2f864a727982349bf88942fce5ba13 remain unchanged in iteration02. Only current() source ordering changes: exact original policy-object/kernel-NumPy identity refusal executes before new dict(policy)/v2 cache-current parsing. Changed legacy policy now raises original ValueError, including substitution of v2 selection or a malformed noniterable object, instead of incidental AttributeError/TypeError. The direct AST restoration fixture removes the moved inserted node at its new index; it was not rerun.

CURRENT_CHECK03 passes one focused exact AST-method fixture with stdlib stubs in0.008s; no NumPy import. Both legacy-to-v2 and malformed replacement refuse before any cache helper executes. Session, timing, numeric hooks, cache arithmetic and reservations remain unchanged02. No unchanged matrix or numerical execution.
''')
for name in ('matching_numeric_policy.py','static_check01.py'):
 a=(P/'iteration02'/name).read_text();b=(P/name).read_text();compile(b,name,'exec')
 for suffix,x,y,xf,yf in [('diff',a,b,'iteration02/'+name,'iteration03/'+name),('inverse.diff',b,a,'iteration03/'+name,'iteration02/'+name)]:
  (P/('AMENDMENT03_'+name+'.'+suffix)).write_text(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=xf,tofile=yf)))
def pin(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
old=json.loads((P/'SOURCE_MANIFEST02.json').read_text())
for item in old['targets']:item['candidate']=pin(P/Path(item['target']).name)
m={'status':'UNINSTALLED_CURRENT_REFUSAL_ORDER_AMENDMENT03_NUMERICAL_UNEXECUTED','prior_manifest':pin(P/'iteration02/SOURCE_MANIFEST02.json'),'targets':old['targets'],'caller_reservation_bytes':33619968,'unchanged_source_pins':old['unchanged_source_pins'],'files':[pin(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='SOURCE_MANIFEST03.json']}
(P/'SOURCE_MANIFEST03.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({n:pin(P/n) for n in ('SOURCE_MANIFEST03.json','matching_numeric_policy.py')},indent=2))
