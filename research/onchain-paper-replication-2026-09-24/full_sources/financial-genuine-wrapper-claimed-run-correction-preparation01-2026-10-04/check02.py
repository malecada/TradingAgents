"""Offline source predicates on authenticated real closed metadata; no Run construction."""
import ast,copy,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;P=H/'overlay/tradingagents/research/onchain_replication/financial_wrapper_fixture.py';checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ok(n,v):assert v,n;checks.append(n)
old=(H/'original-financial_wrapper_fixture.py').read_text();new=P.read_text();inv=json.loads((H/'INVERSE01.json').read_text());back=new
for row in reversed(inv['edits']):ok('exact single inverse',back.count(row['new'])==1);back=back.replace(row['new'],row['old'])
ok('full byte inverse',back==old);ok('full AST inverse',ast.dump(ast.parse(back))==ast.dump(ast.parse(old)))
oldnodes={n.name:n for n in ast.parse(old).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};nodes={n.name:n for n in ast.parse(new).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for name in oldnodes:
 if name!='authorize':ok('unchanged function '+name,ast.dump(oldnodes[name])==ast.dump(nodes[name]))
claimraw=(H/'actual-claim.json').read_bytes();failraw=(H/'actual-failed.json').read_bytes();ok('actual claim pin',sha(claimraw)=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128');ok('actual failure pin',sha(failraw)=='35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450')
claim=json.loads(claimraw);failure=json.loads(failraw);ok('actual failure records repeat refusal',failure['reason']=='ValueError: repeat run prohibited; use a separately justified registration')
admission=ast.parse((H/'original-admission.py').read_text());admit=next(n for n in admission.body if isinstance(n,ast.FunctionDef) and n.name=='admit');guard=next(n.test for n in ast.walk(admit) if isinstance(n,ast.If) and isinstance(n.test,ast.Call) and "c['experiment_id'] == experiment" in ast.unparse(n.test))
code=compile(ast.Expression(guard),'<actual-repeat-predicate>','eval');base={'prior':[claim],'experiment':claim['experiment_id'],'_own_claim':None};ok('RED actual claimed metadata rejects fresh admission',eval(code,{'any':any,**base}) is True)
base['_own_claim']=claim['experiment_id'];ok('GREEN existing lifecycle own-claim predicate only',eval(code,{'any':any,**base}) is False)
base['_own_claim']='different';ok('other own identity still refuses',eval(code,{'any':any,**base}) is True)
life=ast.parse((H/'original-lifecycle.py').read_text());sourcecheck=next(n for n in ast.walk(life) if isinstance(n,ast.FunctionDef) and n.name=='_check_source');call=next(n for n in ast.walk(sourcecheck) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='admit');own=next(k.value for k in call.keywords if k.arg=='_own_claim');ok('original lifecycle uses exact existing claim',ast.unparse(own)=='self.admission.experiment_id')
authorize=ast.get_source_segment(new,nodes['authorize']);oldauth=ast.get_source_segment(old,oldnodes['authorize']);ok('RED old authorize contains second fresh admission','job._admitted(args)' in oldauth);ok('GREEN no second fresh admission','job._admitted' not in authorize)
ok('active/source/input checks remain before existing admission',authorize.index('run._active();run._check_source();run._check_inputs()')<authorize.index('ad=run.admission'))
ok('exact actual Run/Admission types retained',"type(run)is ResearchRun" in authorize and "type(ad)is Admission and ad.ready is True" in authorize)
ok('genuine read_input performs own validation',"raw=run.read_input('execution_job')" in authorize)
# Extract the exact args-join predicate; replace only attribute reads with scalar
# variables from the authenticated real claim. No Admission/Run/Owner is built.
require=next(n for n in ast.walk(nodes['authorize']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='actual args/existing Run admission differs')
expr=copy.deepcopy(require.args[0]);mapping={'args.root':'args_root','ad.root':'root','args.registration':'args_registration','ad.registration':'registration','args.experiment':'args_experiment','ad.experiment_id':'experiment','args.source':'args_source','ad.source':'source'}
class Scalars(ast.NodeTransformer):
 def visit_Attribute(self,node):
  key=ast.unparse(node)
  if key in mapping:return ast.copy_location(ast.Name(id=mapping[key],ctx=ast.Load()),node)
  return self.generic_visit(node)
expr=ast.fix_missing_locations(Scalars().visit(expr));code=compile(ast.Expression(expr),'<exact-args-predicate>','eval');root=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');env={'args_root':str(root),'root':root,'args_registration':claim['registration'],'registration':claim['registration'],'args_experiment':claim['experiment_id'],'experiment':claim['experiment_id'],'args_source':claim['source'],'source':claim['source'],'Path':Path};ok('actual argument scalar joins',eval(code,{'__builtins__':{}},env))
for key,val in [('args_root','/tmp'),('args_registration','wrong.json'),('args_experiment','wrong'),('args_source','0'*40)]:
 changed=dict(env);changed[key]=val;ok('mutation refusal '+key,not eval(code,{'__builtins__':{}},changed))
for text in ['job.job_schema(j)','job.resource_policy(j[\'resources\'],ad.root)','job.required_sources()<=set(ad.experiment[\'source_files\'])',"Path(job.__file__).resolve()==ad.root/(PREFIX+'job.py')","p=admitted(ad,j)","job.workspace_binding(ad.root)","resources.assert_guarded_worker","live['owner_identity']==owner","inventory(ad.root,include_torch=True)"]:
 ok('retained check '+text,text in authorize)
ok('shared admission repeat rule unchanged',sha((H/'original-admission.py').read_bytes())==claim['experiment']['source_files']['tradingagents/research/admission.py'])
(H/'CHECKS02.json').write_text(json.dumps({'count':len(checks),'checks':checks,'genuine_claim_metadata_used':True,'claim_created':False,'real_run_objects_constructed':0,'admission_calls':0,'native_jobs':0,'numerical_imports':0},indent=2)+'\n');print('PASS',len(checks))
