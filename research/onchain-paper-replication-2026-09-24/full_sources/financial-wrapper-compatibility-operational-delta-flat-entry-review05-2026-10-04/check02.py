from pathlib import Path
import ast,json,os,stat,hashlib
H=Path(__file__).resolve().parent;B=H.parent;C=B/'heartbeat-root-checkpoint10-2026-10-04/root_operational_flat05.py';t=ast.parse(C.read_bytes());functions=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in {'read','digest','signature'}];ns={'os':os,'stat':stat,'hashlib':hashlib,'FILE':4194304};exec(compile(ast.Module(body=functions,type_ignores=[]),'exact-original-read','exec'),ns);node=next(n for n in t.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='name' and isinstance(n.iter,ast.Tuple));names=ast.literal_eval(node.iter);compiled=compile(ast.Module(body=[node],type_ignores=[]),'exact-fresh-refusals','exec');results=[]
for i,name in enumerate(names):
 p=H/('fresh-negative-%02d'%i);p.mkdir(mode=0o700);(p/name).write_bytes(b'opaque existing name');ns['D']=p
 try:exec(compiled,ns)
 except AssertionError:results.append({'existing_name':name,'refused':True})
 else:raise AssertionError('existing name accepted')
p=H/'pin-negative';p.write_bytes(b'opaque')
try:ns['read'](p,'0'*64)
except AssertionError:results.append({'wrong_body_pin':True,'refused':True})
else:raise AssertionError('wrong pin accepted')
# Exact draft literal supplied to read before JSON parsing; not a value read from mutable draft.
stmt=next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='draft' for x in n.targets))
assert ast.unparse(stmt)=="draft = json.loads(read(D / 'ROOT_FLAT04_INSTALLATION_DRAFT01.json', DRAFT))"
assert next(n.value.value for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='DRAFT' for x in n.targets))=='770f509c8a65a1a5a6cb33e2efbf8215c9466ba5af235251b883ac1452299e21'
(H/'READBACK02.json').write_text(json.dumps({'status':'PASS','refusals':results,'actual_draft_pin_precedes_parse':True,'actual_entry':False},indent=2)+'\n');print('PASS16 existing-namespace and wrong-pin refusals plus exact draft-before-parse AST')
