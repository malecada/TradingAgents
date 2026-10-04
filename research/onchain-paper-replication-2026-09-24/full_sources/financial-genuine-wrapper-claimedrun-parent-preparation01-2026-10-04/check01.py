import ast,hashlib,json,sys,copy
from pathlib import Path
from types import SimpleNamespace
import parent01 as P
H=Path(__file__).resolve().parent;checks=[]
def ok(x,n):assert x,n;checks.append(n)
def refuse(f,n):
 try:f()
 except (ValueError,TypeError,KeyError):checks.append(n)
 else:raise AssertionError(n)
s=(H/'parent01.py').read_text();old=(H/'original-parent01.py').read_text();inv=s
for edit in reversed(json.loads((H/'INVERSE01.json').read_text())['edits']):ok(inv.count(edit['new'])==1,'unique inverse');inv=inv.replace(edit['new'],edit['old'])
ok(inv==old,'full byte inverse');ok(ast.dump(ast.parse(inv))==ast.dump(ast.parse(old)),'full AST inverse')
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_text());refuse(lambda:P.validate_release(q),'draft refusal')
for key in q:
 bad=copy.deepcopy(q);bad.pop(key);refuse(lambda:P.validate_release(bad),'missing '+key)
for k in ('final_review',):ok(q[k] is None,'missing actual '+k)
for k in ('full_recovery','independent_source_input_runtime'):ok(q['proofs'][k] is None,'missing proof '+k)
ok(P.sha(P.reference(q['proofs']['cumulative']))=='3268b76971e4e721222707d16d25dfe84e94104779931e647fb4d7a2bf01202e','actual cumulative review body')
for n,pin in q['source_files'].items():ok(P.sha(P.R.read(P.CAP,n))==pin,'actual source '+n)
reg=json.loads(P.R.read(P.CAP,q['registration']));exp=reg['experiments'][P.IDENTITY]
ok(P.sha(P.R.read(P.CAP,q['registration']))==q['registration_sha256'],'actual gate')
for role,ref in exp['inputs'].items():ok(P.sha(P.R.read(P.CAP,ref['path']))==q['input_hashes'][role],'input '+role)
for n,pin in q['helper_hashes'].items():ok(P.sha(P.R.read(H,n))==pin,'unchanged helper '+n)
# Execute only genuine pure job command constructor with scalar args.
tree=ast.parse((H/'original-job.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_command')
ns={'sys':sys,'Path':Path,'MODULE':'tradingagents.research.onchain_replication.job'};exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual command>','exec'),ns)
a=SimpleNamespace(root=str(P.CAP),registration=q['registration'],experiment=P.IDENTITY,source=q['source']);command=ns['_command'](a,'launch');ok(command[command.index('--source')+1]==q['source'],'genuine source command');ok(command[command.index('--root')+1]==str(P.CAP),'genuine root command')
# Source-extracted actual family predicate: metadata only, no Admission object.
fn=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='preflight')
call=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='base18/prior0 and exact genuine cumulative19 review')
expr=compile(ast.Expression(call.args[0]),'<actual family predicate>','eval');family=reg['families'][exp['family']];ok(eval(expr,{'family':family,'exp':exp}),'actual family/review metadata')
for field,value in (('attempt_budget',19),('prior_attempts',1)):
 f=dict(family);f[field]=value;ok(not eval(expr,{'family':f,'exp':exp}),'refuse '+field)
e=copy.deepcopy(exp);e['cumulative_budget_extension']['review']['sha256']='0'*64;ok(not eval(expr,{'family':family,'exp':e}),'refuse review hash')
for name in ('child_cleanup','launch','stream_hash','memory','reference','contract','main'):
 get=lambda body:ast.dump(next(n for n in ast.parse(body).body if isinstance(n,ast.FunctionDef) and n.name==name))
 ok(get(s)==get(old),'unchanged '+name)
ok(s.index('admitted,admitted_job=job._admitted(args)')<s.index("command=job._command(args,'launch')"),'genuine admission before command')
ok(not any(n in sys.modules for n in ('numpy','torch','pandas','scipy')),'no numeric imports')
(H/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'admission_calls':0,'claims':0,'native':False},indent=2)+'\n');print(len(checks))
