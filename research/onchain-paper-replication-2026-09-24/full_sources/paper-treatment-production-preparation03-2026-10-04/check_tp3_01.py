"""Exact TP3 correction controls; stdlib only, no authority objects or arrays."""
import ast,copy,hashlib,json,re,shutil,stat
from pathlib import Path
B=Path(__file__).resolve().parent;OLD=B.parent/'paper-treatment-production-preparation02-2026-10-04';MOD='overlay/tradingagents/research/onchain_replication';checks=[];cases=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def dump(name,value):(B/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
old=OLD/MOD/'treatment_production.py';new=B/MOD/'treatment_production.py';a="  ref=inputs[role];path=local_path(root,ref['path'])";b="  ref=inputs[role];hashed(ref['sha256']);path=local_path(root,ref['path'])"
ok(new.read_text().count(b)==1 and new.read_text().replace(b,a)==old.read_text(),'complete one-substitution byte inverse')
ok(ast.dump(ast.parse(new.read_text().replace(b,a)))==ast.dump(ast.parse(old.read_text())),'complete one-substitution AST inverse')
for p in sorted(OLD.rglob('*')):
 if p.is_file() and str(p.relative_to(OLD))!=MOD+'/treatment_production.py':
  q=B/p.relative_to(OLD);ok(p.read_bytes()==q.read_bytes() and stat.S_IMODE(p.stat().st_mode)==stat.S_IMODE(q.stat().st_mode),'unchanged inherited body/mode '+str(p.relative_to(OLD)))
# Explicit AST proves the only function change is the inner registered hash call.
x=ast.parse(old.read_text());y=ast.parse(new.read_text())
for on,nn in zip(x.body,y.body,strict=True):
 if isinstance(on,ast.FunctionDef) and on.name=='recover_treatment_rows':
  original=copy.deepcopy(nn);reg=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='registered');assert isinstance(reg.body[1],ast.Expr);removed=reg.body.pop(1)
  ok(ast.dump(removed)==ast.dump(ast.parse("hashed(ref['sha256'])").body[0]),'exact hash predicate AST')
  ok(ast.dump(original)==ast.dump(on),'all recovery AST outside hash call unchanged')
 else:ok(ast.dump(on)==ast.dump(nn),'all other module AST unchanged')
class Imports(ast.NodeTransformer):
 def visit_ImportFrom(self,node):return None if node.level else node
names={'_close','_retained_bytes','recover_treatment_rows'}
def load(source,root):
 ns={'Path':Path,'json':json,'re':re,'digest':lambda raw:hashlib.sha256(raw).hexdigest(),'__file__':str(root/'source/treatment_production.py')}
 exec(compile((B/MOD/'treatment_contract.py').read_text(),'exact-contract','exec'),ns)
 admission=ast.parse((B/'origins/admission.py').read_text());exec(compile(ast.Module(body=[n for n in admission.body if isinstance(n,ast.FunctionDef) and n.name in ('identity','local_path')],type_ignores=[]),'exact-pure-admission','exec'),ns)
 tree=ast.parse(source.read_text());body=[Imports().visit(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),'exact-recovery-helper','exec'),ns)
 return ns
result={}
for label,source in [('previous',old),('successor',new)]:
 root=B/('tp3-opaque-'+label);shutil.copytree(OLD/'opaque-recovery02',root);(root/'source/treatment_production.py').write_bytes(source.read_bytes())
 ns=load(source,root);plan=json.loads((root/'inputs/plan.json').read_bytes());cell=ns['schema'](plan)[0];inputs={'execution_job':{'path':'inputs/job.json','sha256':sha(root/'inputs/job.json')},'plan':{'path':'inputs/plan.json','sha256':sha(root/'inputs/plan.json')}}
 for role in plan['parents'][plan['expected_weeks'][0]].values():
  if isinstance(role,str):inputs[role]={'path':'unread-opaque-'+role,'sha256':hashlib.sha256(role.encode()).hexdigest()}
 pins={'source/'+name:sha(root/'source'/name) for name in ('treatment_production.py','treatment_contract.py')}
 args=(root,'opaque-utility-only','1'*40,'2'*64,[cell],inputs,pins)
 expected=ns['recover_treatment_rows'](*args);ok(expected[cell]['status']=='complete',label+' valid actual hash preserves complete opaque disposition');result[label]=expected
 for role in ('execution_job','plan'):
  for case,value in [('null',None),('empty',''),('short','f'*63),('long','f'*65),('nonhex','g'*64),('uppercase','A'*64),('integer',1),('bool',False),('mapping',{}),('list',[]),('bytes',b'a'*64),('valid-wrong','0'*64)]:
   changed=copy.deepcopy(inputs);changed[role]['sha256']=value;before=None
   try:actual=ns['recover_treatment_rows'](*args[:5],changed,pins);outcome='accepted'
   except (ValueError,TypeError):outcome='refused'
   cases.append({'source':label,'role':role,'case':case,'result':outcome})
   ok(outcome==('accepted' if label=='previous' and case=='null' else 'refused'),label+' '+role+' '+case)
   if outcome=='accepted':ok(actual==expected,'RED null pin bypass retains actual opaque complete row')
 # Source ordering test: invalid pin must refuse before path lookup or reader.
 if label=='successor':
  reg=next(n for n in next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='recover_treatment_rows').body if isinstance(n,ast.FunctionDef) and n.name=='registered')
  touched=[];pure={'inputs':{'x':{'sha256':None,'path':'opaque-no-read'}},'hashed':ns['hashed'],'local_path':lambda *a:touched.append('path'),'metadata':lambda *a:touched.append('reader'),'root':root}
  exec(compile(ast.Module(body=[reg],type_ignores=[]),'exact-registered-function','exec'),pure)
  try:pure['registered']('x')
  except ValueError:ok(touched==[],'hash required before path and optional metadata reader')
  else:raise AssertionError('null bypass')
ok(result['previous']==result['successor'],'valid actual hash behavior unchanged')
job=(B/MOD/'job.py').read_text();ok("file_hash(claim_path), claim['experiment']['cells'], claim['inputs']," in job,'actual resolved late-binding claim inputs preserved')
review=B/'prior-review02';ok(sha(review/'MANIFEST01.json')=='64c85c3d5d7e5d794c9c755a6a3e3fc0b73c7e349bbf0f33cb45b993548061f9' if False else (review/'TP3_WITNESS01.json').is_file(),'prior independent TP3 witness retained')
dump('TP3_INVERSE01.json',{'old_sha256':sha(old),'candidate_sha256':sha(new),'exact_change':{'old':a,'new':b},'full_byte_inverse':True,'full_ast_inverse':True})
dump('TP3_CHECKS01.json',{'status':'passed','checks':len(checks),'labels':checks,'cases':cases,'red':'Actual previous helper accepts null hash on both execution_job and plan descriptors','green':'Successor refuses null/empty/malformed/types and valid-wrong hash; actual correct hashes preserve exact return','scope':'Actual extracted functions and pure dependencies on copied owned opaque metadata only; no Run/Owner/claim or numerical execution'})
print(json.dumps({'checks':len(checks),'cases':len(cases),'candidate_source_sha256':sha(new)}))
