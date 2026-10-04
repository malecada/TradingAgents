import ast,copy,hashlib,json,sys
from pathlib import Path
import bind01 as B
H=Path(__file__).resolve().parent;checks=[]
def ok(v,n):assert v,n;checks.append(n)
s=(H/'bind01.py').read_text();o=(H/'predecessor01/bind01.py').read_text();inv=json.loads((H/'INVERSE02.json').read_bytes());back=s.replace(inv['new'],inv['old']);ok(back==o,'binder exact byte inverse');ok(ast.dump(ast.parse(back))==ast.dump(ast.parse(o)),'binder AST inverse')
original=B.R.read(H,'original-verifier03.py');rewritten,edits=B.rewrite(original,'1'*64,'REQUEST_FINAL01.json');back=rewritten.decode()
for e in reversed(edits):back=back.replace(e['new'],e['old'])
ok(back.encode()==original,'complete verifier inverse')
claim=json.loads((H/'window-evidence/actual-old-claim.json').read_bytes());gate=json.loads((H/'window-evidence/actual-old-gate.json').read_bytes());e=gate['experiments'][claim['experiment_id']]
ok(hashlib.sha256((H/'window-evidence/actual-old-claim.json').read_bytes()).hexdigest()=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','actual old claim pin')
ok(claim['windows']!=e['windows'],'actual raw equality RED')
# Extract only new exact assignments/comparison, never the outcome verifier.
fn=next(n for n in ast.parse(rewritten).body if isinstance(n,ast.FunctionDef) and n.name=='verify');assigns=[n for n in ast.walk(fn) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('expected_windows','expected_exposures')];guard=next(n.args[0] for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='claim exposure windows differ from committed registration')
def accepts(c,g=gate,ex=e):
 ns={'claim':c,'gate':g,'e':ex};exec(compile(ast.Module(body=assigns,type_ignores=[]),'<actual new pure window calculation>','exec'),ns);return eval(compile(ast.Expression(guard),'<exact comparator>','eval'),ns)
ok(accepts(claim),'actual old claim GREEN')
# Independently extracted genuine verify_claim assignments must produce identical ordered values.
tree=ast.parse((H/'window-evidence/actual-verify.py').read_bytes());auth=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('windows','exposures')];ns={'registered':gate,'exp':e};exec(compile(ast.Module(body=auth,type_ignores=[]),'<genuine verify_claim calculation>','exec'),ns);ok(claim['windows']==ns['windows'] and claim['prior_exposures']==ns['exposures'],'independent exact ordered original expansion')
for group in ('windows','prior_exposures'):
 for key in claim[group][0]:
  v=copy.deepcopy(claim);v[group][0][key]='changed';ok(not accepts(v),'mutate '+group+key)
  v=copy.deepcopy(claim);v[group][0].pop(key);ok(not accepts(v),'missing '+group+key)
 v=copy.deepcopy(claim);v[group].append(copy.deepcopy(v[group][0]));ok(not accepts(v),'duplicate '+group)
 v=copy.deepcopy(claim);v[group]=[];ok(not accepts(v),'empty '+group)
# Pure multi-window registration metadata ordering fixture, no generated claim artifact.
g=copy.deepcopy(gate);ex=copy.deepcopy(e);ex['windows'].append({**ex['windows'][0],'start':'different-order-marker'});ns={'registered':g,'exp':ex};exec(compile(ast.Module(body=auth,type_ignores=[]),'<genuine expected ordered metadata>','exec'),ns);metadata={'windows':ns['windows'],'prior_exposures':ns['exposures']};ok(accepts(metadata,g,ex),'ordered pure metadata comparator');metadata['windows'].reverse();ok(not accepts(metadata,g,ex),'reordered windows refuse')
# Confirmation state and all-dataset exposure ordering remain genuine source semantics.
g=copy.deepcopy(gate);ex=copy.deepcopy(e);ex['stage']='confirmation';ns={'registered':g,'exp':ex};exec(compile(ast.Module(body=auth,type_ignores=[]),'<genuine confirmation metadata>','exec'),ns);metadata={'windows':ns['windows'],'prior_exposures':ns['exposures']};ok(accepts(metadata,g,ex) and metadata['windows'][0]['state']=='spent','confirmation spent exact');metadata['windows'][0]['state']='exposed';ok(not accepts(metadata,g,ex),'confirmation state refusal')
g=copy.deepcopy(gate);ex=copy.deepcopy(e);first=next(iter(g['datasets']));g['datasets']['second-opaque-dataset']=copy.deepcopy(g['datasets'][first]);g['datasets']['second-opaque-dataset']['identity']='second-order-marker';ns={'registered':g,'exp':ex};exec(compile(ast.Module(body=auth,type_ignores=[]),'<genuine multidataset exposures>','exec'),ns);metadata={'windows':ns['windows'],'prior_exposures':ns['exposures']};ok(accepts(metadata,g,ex),'all datasets prior exposure order');metadata['prior_exposures'].reverse();ok(not accepts(metadata,g,ex),'reordered prior exposure refusal')
for field in ('windows','prior_exposures'):
 v=copy.deepcopy(claim);v[field][0]['unregistered_extra']='x';ok(not accepts(v),'extra field refusal '+field)
q=json.loads((H/'ACTUAL_PARENT_DRAFT01.json').read_bytes())
try:B.fixed(q)
except ValueError:ok(True,'actual draft still refused')
else:raise AssertionError('draft')
ok(not (H/'generated-claimedrun01').exists(),'no verifier emitted');ok(not any(n in sys.modules for n in ('numpy','torch','pandas')),'no numerical imports')
(H/'CHECKS02.json').write_bytes(B.R.encode({'count':len(checks),'checks':checks,'actual_outcomes_verified':0,'actual_emissions':0}));print(len(checks))
