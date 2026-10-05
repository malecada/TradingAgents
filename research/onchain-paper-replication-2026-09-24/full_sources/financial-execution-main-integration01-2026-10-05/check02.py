"""Nonnumerical metadata contracts and exact scientific source preservation."""
import ast,copy,hashlib,importlib.util,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;checks=[]
def ok(value,name):
 if not value:raise AssertionError(name)
 checks.append(name)
def refuses(call,name):
 try:call()
 except (ValueError,TypeError,KeyError):checks.append(name);return
 raise AssertionError(name)
def raw(group,n):return (H/group/n).read_text()
def tree(group,n):return ast.parse(raw(group,n))
def fn(group,n,name):return next(x for x in tree(group,n).body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name)
def samefn(a,b,n,name):return ast.dump(fn(a,n,name))==ast.dump(fn(b,n,name))
for n in sorted((H/'candidate').glob('*.py')):compile(n.read_text(),str(n),'exec');checks.append('AST compile '+n.name)
for n in ('financial_execution.py','model_registry.py','checkpoints.py','replay.py'):ok(raw('candidate',n)==raw('origins/CAP',n),'exact CAP '+n)
ok(samefn('candidate','origins/Main','training.py','_reserve'),'Main genuine reserve completely unchanged')
ok(samefn('candidate','origins/Main','training.py','predict_cell'),'Main prediction batching completely unchanged')
ok(samefn('candidate','origins/CAP','training.py','fit_cell'),'CAP fit engine including execution checks exact')
for name in ('batch_factory','feature_hash','reuse_cell','prediction_directory','validate_cell_admission','validate_manifest','validate_scientific_cell'):
 ok(samefn('candidate','origins/Main','evaluation.py',name),'Main preserved evaluation '+name)
for name in ('_configuration','_published'):ok(samefn('candidate','origins/Main','run.py',name),'Main preserved run '+name)
# Remove ONLY the two new selected-model guards: the complete fit function must
# recover Main's exact scientific AST (optimizer, loss, gradients, cursor, saves).
fit=copy.deepcopy(fn('candidate','training.py','fit_cell'))
class RemoveGuards(ast.NodeTransformer):
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='financial' and n.value.func.attr=='check_model':return None
  return self.generic_visit(n)
ok(ast.dump(RemoveGuards().visit(fit))==ast.dump(fn('origins/Main','training.py','fit_cell')),'all original training science AST unchanged after exact guards removed')
for n in ('run.py','evaluation.py'):
 old=raw('origins/Main',n);new=raw('candidate',n)
 for line in old.splitlines():
  if any(s in line for s in ('preflight_treatment(',"from .treatment_admission",'training_batch_observer','observation=prepare(','observation=None if observation')):ok(line in new,'retained treatment/observer '+n+':'+line.strip())
ev=fn('candidate','evaluation.py','evaluate_cell');kw=[n.arg for n in ev.args.kwonlyargs]
ok('execution' in kw and 'treatment_reference' in kw,'execution and original treatment keywords coexist')
evcall=[n for n in ast.walk(fn('candidate','run.py','execute_batch')) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='evaluate_cell']
ok(len(evcall)==1 and {'execution','treatment_reference'}<=set(k.arg for k in evcall[0].keywords),'run forwards both execution and treatment')
spec=importlib.util.spec_from_file_location('isolated_financial_execution_metadata',H/'candidate/financial_execution.py');financial=importlib.util.module_from_spec(spec);spec.loader.exec_module(financial)
ok(not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')),'new helper imports no numerical module')
ok(financial.identity(None) is None and financial.authenticate(None) is None,'legacy None identity/authentication')
policy={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536}
valid={'policy':policy,'policy_sha256':hashlib.sha256(financial.canonical(policy)).hexdigest(),'source_path':financial.SOURCE,'source_sha256':financial.SHA,'candidate_sha256':financial.SHA}
detached=financial.identity(valid);detached['policy']['block_edges']=1;ok(valid['policy']['block_edges']==65536,'execution identity detaches policy mapping')
for key,value in [('source_path','other.py'),('source_sha256','0'*64),('candidate_sha256','0'*64),('policy_sha256','0'*64)]:
 bad=copy.deepcopy(valid);bad[key]=value;refuses(lambda b=bad:financial.identity(b),'wrong '+key+' refuses')
for key,value in [('schema_version',True),('backend','eager'),('block_edges',True),('block_edges',65535)]:
 bad=copy.deepcopy(valid);bad['policy'][key]=value;bad['policy_sha256']=hashlib.sha256(financial.canonical(bad['policy'])).hexdigest();refuses(lambda b=bad:financial.identity(b),'wrong policy '+key+' '+str(value))
for bad in ({},True,{**valid,'extra':1}):refuses(lambda b=bad:financial.identity(b),'identity exact type/keys '+repr(bad))
plan={k:{} for k in financial.PLAN_KEYS};plan.update(schema_version=1,cells=[{'cell':{'arm':'proposed'}}],model={})
ok(financial.plan_selection(plan)=={},'legacy schema1 no selected backend')
selected={**plan,'schema_version':2,'model_execution':{'proposed':valid}}
ok(financial.plan_selection(selected)=={'proposed':valid},'exact schema2 selected arm')
for bad in ({**selected,'schema_version':1},{**selected,'schema_version':True},{**selected,'model_execution':{}},{**selected,'model_execution':{'lstm':valid}},{**selected,'model_execution':{'proposed':None}},{**selected,'model':{'graph_activation_checkpointing':True}},{**selected,'extra':1}):
 refuses(lambda b=bad:financial.plan_selection(b),'plan schema/arm/policy refusal '+repr(bad))
financial.validate_state({},{});checks.append('legacy checkpoint without selected metadata')
financial.validate_state({'model_execution':valid,'model_contract':{}},{'model_execution':valid});checks.append('selected checkpoint metadata presence')
for state,provenance in [({}, {'model_execution':valid}),({'model_execution':valid,'model_contract':{}},{}),({'model_execution':None}, {'model_execution':None}),({'model_execution':valid}, {'model_execution':valid}),({'model_contract':{}},{})]:
 refuses(lambda s=state,p=provenance:financial.validate_state(s,p),'checkpoint provenance/contract mismatch refuses')
# Exact original build_model AST, executed only for legacy dispatch with opaque
# constructor call markers: no framework class, authority handle or fit exists.
registry=fn('candidate','model_registry.py','build_model');calls=[];marker=object()
def constructor(*args):calls.append(args);return marker
ns={'financial':financial,'ReplicationModel':constructor}
exec(compile(ast.Module(body=[registry],type_ignores=[]),'extracted_build_model','exec'),ns)
ok(ns['build_model']('proposed','direction',{'opaque':1}) is marker and calls==[({'opaque':1},'classification')],'legacy None constructor route and direction alias')
refuses(lambda:ns['build_model']('proposed','unknown',{}),'unknown task still refuses before model construction')
refuses(lambda:ns['build_model']('proposed','direction',{},execution={}), 'invalid selected identity refuses before construction')
ok(not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')),'all controls remained nonnumerical')
print(json.dumps({'passed':len(checks),'checks':checks,'numerical_imports':False,'genuine_model_construction':False,'admission_or_fit':False},sort_keys=True))
