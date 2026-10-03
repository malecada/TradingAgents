"""Independent exact read-only helper checks against synthetic tiny evidence."""
import ast,hashlib,importlib.util,json,pathlib,sys
P=pathlib.Path(__file__).resolve().parent;A=P.parent/'neural-cold-feature-handoff-root-launcher-preparation01-2026-10-03'
s=importlib.util.spec_from_file_location('review_launcher_evidence',A/'launcher01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def refuse(f):
 try:f()
 except (ValueError,FileNotFoundError):return
 raise AssertionError('required refusal missing')
a=P/'synthetic-recovery-original';b=P/'synthetic-recovery-restored';a.mkdir();b.mkdir()
for root in (a,b):(root/'d').mkdir();(root/'d/member').write_bytes(b'only-five')
rows=[{'path':'d','kind':'directory'},{'path':'d/member','kind':'file','bytes':9,'sha256':sha(b'only-five')}]
index={'schema_version':1,'source':'ab'*20,'original_root':str(a),'recovered_root':str(b),'members':rows};path=P/'synthetic-recovery-index.json';path.write_text(json.dumps(index))
q={'source':'ab'*20,'recovery':{'path':str(path),'sha256':sha(path.read_bytes())}}
assert m.recovery(q,a)['members']==2
(b/'d/member').write_bytes(b'different');refuse(lambda:m.recovery(q,a))
(b/'d/member').write_bytes(b'only-five');(b/'extra').write_bytes(b'extra');refuse(lambda:m.recovery(q,a))
# Keep changed/extra state; only these explicitly synthetic review files changed.
fn=next(n for n in ast.parse((A/'launcher01.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
call=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='original release/outer acceptance differs')
expr=compile(ast.Expression(call.args[0]),'actual-fourfield-release-join','eval');ref={'path':'r','sha256':'ab'*32,'bytes':24,'kind':'metadata'}
base={'wait':{'release':ref},'accepted':{'release':dict(ref),'status':'accepted','source':'ab'*20,'identity':'synthetic'},'release_reference':ref,'q':{'source':'ab'*20},'identity':'synthetic'}
assert eval(expr,base)
refusals=0
for k,v in [('path','other'),('sha256','cd'*32),('bytes',25),('kind','document')]:
 bad=dict(base);bad['accepted']=dict(base['accepted'],release=dict(ref,**{k:v}));assert not eval(expr,bad);refusals+=1
bad=dict(base);bad['accepted']=dict(base['accepted'],release={'path':'r','sha256':'ab'*32});assert not eval(expr,bad)
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps({'synthetic_full_membership_passed':2,'changed_and_extra_bodies_refused':True,'exact_actual_fourfield_join_passed':True,'four_mutations_and_twofield_reference_refused':True,'actual_remote_recovery_or_authority':False},indent=2))
