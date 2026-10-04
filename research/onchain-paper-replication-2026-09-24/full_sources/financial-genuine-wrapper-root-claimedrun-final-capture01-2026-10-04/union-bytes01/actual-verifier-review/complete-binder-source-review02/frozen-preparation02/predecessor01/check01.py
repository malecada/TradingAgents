import ast,copy,hashlib,json,sys
from pathlib import Path
import bind01 as B
H=Path(__file__).resolve().parent;checks=[]
def ok(v,n):assert v,n;checks.append(n)
def refuse(f,n):
 try:f()
 except (ValueError,KeyError,TypeError):checks.append(n)
 else:raise AssertionError(n)
P=B.prepared();q=json.loads(B.R.read(H,'ACTUAL_PARENT_DRAFT01.json'));refuse(lambda:B.fixed(q),'real unreleased draft refusal');refuse(lambda:B.authenticate(Path(B.PARENT)/'REQUEST_DRAFT01.json',B.R.digest(B.R.read(H,'ACTUAL_PARENT_DRAFT01.json'))),'actual installed draft cannot bind')
# Pure transformation only, no claim of real request/review/outcome or emission.
original=B.R.read(H,'original-verifier03.py');candidate,edits=B.rewrite(original,'1'*64,'REQUEST_FINAL01.json');inv=candidate.decode()
for e in reversed(edits):ok(inv.count(e['new'])==1,'unique verifier inverse');inv=inv.replace(e['new'],e['old'])
ok(inv.encode()==original,'full verifier byte inverse');ok(ast.dump(ast.parse(inv))==ast.dump(ast.parse(original)),'full verifier AST inverse')
a={n.name:ast.dump(n) for n in ast.parse(original).body if isinstance(n,ast.FunctionDef)};z={n.name:ast.dump(n) for n in ast.parse(candidate).body if isinstance(n,ast.FunctionDef)}
for n in a:
 if n!='verify':ok(a[n]==z[n],'unchanged outcome helper '+n)
for h in (B.OLD_QHASH,'bad','0'*63):refuse(lambda:B.rewrite(original,h,'REQUEST_FINAL01.json'),'bad old/request pin '+h[:6])
for n in ('REQUEST_DRAFT01.json','../REQUEST_FINAL01.json','/REQUEST_FINAL01.json'):refuse(lambda:B.rewrite(original,'2'*64,n),'request path refusal '+n)
# Typed metadata predicate controls only; synthetic release label never passed authenticate/generate/emit.
t=copy.deepcopy(q);t['status']='RELEASED_ONE_USE_FINANCIAL_PARENT';t['final_review']={'path':'UNRESOLVED','sha256':'0'*64};B.fixed(t);ok(True,'fixed metadata predicate only')
for field in ('source','design_source','identity','capsule_root','parent_root','caller_sha256','registration','registration_sha256'):
 v=copy.deepcopy(t);v[field]='wrong';refuse(lambda:B.fixed(v),'wrong '+field)
for field in ('source_files','input_hashes','runtime_mapping','helper_hashes'):
 v=copy.deepcopy(t);v[field]={};refuse(lambda:B.fixed(v),'wrong '+field)
for role in ('cumulative','independent_source_input_runtime'):
 v=copy.deepcopy(t);v['proofs'][role]['sha256']='0'*64;refuse(lambda:B.fixed(v),'wrong proof '+role)
# Exact original scientific/exit/CPU/cleanup functions are unchanged; scalar budget/denominator mutation evidence.
verify=next(n for n in ast.parse(candidate).body if isinstance(n,ast.FunctionDef) and n.name=='verify')
exprs=[n.args[0] for n in ast.walk(verify) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='fixed cumulative allowance']
expr=compile(ast.Expression(exprs[0]),'<exact scalar budget>','eval')
for value in (18,19,20):ok(eval(expr,{'claim':{'effective_attempt_budget':value,'family':{'prior_attempts':0}}})==(value==19),'actual allowance predicate '+str(value))
for n in ('numpy','torch','pandas'):ok(n not in sys.modules,'no '+n)
ok(not (H/'generated-claimedrun01').exists(),'no actual emitted verifier')
(H/'CHECKS01.json').write_bytes(B.R.encode({'count':len(checks),'checks':checks,'actual_emissions':0,'outcomes_verified':0,'claims':0}));print(len(checks))
