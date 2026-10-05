"""Independent source/stdlib checks; never imports numerical package or creates authority."""
import ast,copy,hashlib,importlib.util,json,stat,sys,subprocess,re
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;A=F/'financial-execution-main-integration01-2026-10-05';M=H.parents[3];C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');REL=Path('tradingagents/research/onchain_replication')
checks=[]
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def sha(b):return hashlib.sha256(b).hexdigest()
def reject(fn,label):
 try:fn()
 except (ValueError,TypeError,KeyError):checks.append(label);return
 raise AssertionError(label)
def tree(raw):return ast.dump(ast.parse(raw),include_attributes=False)
def func(raw,name):return next(n for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
def extract(raw,name,env):
 node=func(raw,name);exec(compile(ast.Module(body=[node],type_ignores=[]),'<exact extracted source>','exec'),env);return env[name]
raw=(A/'MANIFEST01.json').read_bytes();ok(sha(raw)=='6e424349683e8831bd85fdc1b13b6209efdd2ca2c4c5018255c59d7b8885966f','author seal')
manifest=json.loads(raw);rows=manifest['members'];ok({r['path'] for r in rows}=={str(p.relative_to(A)) for p in A.rglob('*') if p.name!='MANIFEST01.json'},'complete actual source tree')
for r in rows:
 p=A/r['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==r['mode'],'mode '+r['path'])
 if r['kind']=='file':ok(stat.S_ISREG(s.st_mode) and len(p.read_bytes())==r['bytes'] and sha(p.read_bytes())==r['sha256'],'body '+r['path'])
 else:ok(stat.S_ISDIR(s.st_mode),'directory '+r['path'])
inv=json.loads((A/'SOURCE_INVERSE01.json').read_bytes())['modules'];bodies={p.name:p.read_bytes() for p in (A/'candidate').iterdir()}
for name,raw in bodies.items():
 compile(raw,name,'exec');checks.append('compile '+name)
 for label,base in [('Main',M),('CAP',C)]:
  original=(base/REL/name).read_bytes() if (base/REL/name).exists() else b''
  item=inv[name][label];ok(sha(original)==item['original_sha256'],'current base '+name+label)
  restored=raw.decode()
  for seg in reversed(item['literal_segments']):
   x,y=seg['candidate_offsets'];ok(restored[x:y]==seg['candidate'],'segment '+name+label);restored=restored[:x]+seg['original']+restored[y:]
  ok(restored.encode()==original and tree(restored)==tree(original),'byte AST inverse '+name+label)
  if original:
   committed=subprocess.check_output(['git','-C',str(base),'show',json.loads((A/'MACHINE01.json').read_bytes())['heads'][label]+':'+str(REL/name)])
   ok(original==committed,'committed source '+label+name)
for name in ['financial_execution.py','model_registry.py','checkpoints.py','replay.py']:ok(bodies[name]==(C/REL/name).read_bytes(),'CAP identical '+name)
for name in ['model.py','streamed_gat.py']:ok((M/REL/name).read_bytes()==(C/REL/name).read_bytes(),'actual constructor dependency '+name)
for name,fs in {'training.py':['_reserve','predict_cell'],'evaluation.py':['batch_factory','feature_hash','validate_scientific_cell','validate_manifest'],'run.py':['_configuration','_published']}.items():
 for fn in fs:ok(ast.dump(func(bodies[name],fn))==ast.dump(func((M/REL/name).read_bytes(),fn)),'preserved Main '+name+fn)
fit=copy.deepcopy(func(bodies['training.py'],'fit_cell'))
class RemoveGuard(ast.NodeTransformer):
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='financial.check_model':return None
  return self.generic_visit(n)
fit=RemoveGuard().visit(fit);ok(ast.dump(fit)==ast.dump(func((M/REL/'training.py').read_bytes(),'fit_cell')),'entire training loop inverse except two guards')
spec=importlib.util.spec_from_file_location('review_financial',A/'candidate/financial_execution.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
policy={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536};identity={'policy':policy,'policy_sha256':sha(f.canonical(policy)),'source_path':f.SOURCE,'source_sha256':f.SHA,'candidate_sha256':f.SHA}
ok(f.identity(None) is None,'legacy absent identity');ok(f.identity(identity)==identity,'exact selected identity')
for k,v in [('schema_version',True),('block_edges',65536.0),('backend','other')]:
 bad=copy.deepcopy(identity);bad['policy'][k]=v;reject(lambda:f.identity(bad),'policy refuses '+k)
for k in ['policy_sha256','source_path','source_sha256','candidate_sha256']:
 bad=copy.deepcopy(identity);bad[k]='bad';reject(lambda:f.identity(bad),'identity refuses '+k)
plan={k:None for k in f.PLAN_KEYS};plan.update(schema_version=1,model={},cells=[{'cell':{'arm':'proposed'}}]);ok(f.plan_selection(plan)=={},'legacy plan unchanged')
plan.update(schema_version=2,model_execution={'proposed':identity});ok(f.plan_selection(plan)=={'proposed':identity},'selected plan')
for mapping in [{},{'gru':identity},{'proposed':None}]:
 bad=copy.deepcopy(plan);bad['model_execution']=mapping;reject(lambda:f.plan_selection(bad),'mapping refusal '+repr(mapping)[:30])
bad=copy.deepcopy(plan);bad['model']['graph_activation_checkpointing']=True;reject(lambda:f.plan_selection(bad),'checkpoint policy refusal')
for state,provenance,good in [({}, {},True),({'model_execution':identity,'model_contract':{}},{'model_execution':identity},True),({}, {'model_execution':identity},False),({'model_execution':identity},{'model_execution':identity},False),({'model_execution':identity,'model_contract':{}},{},False),({}, {'model_execution':None},False),({'model_execution':identity,'model_contract':None},{'model_execution':identity},False)]:
 if good:f.validate_state(state,provenance);checks.append('state allowed '+str(len(checks)))
 else:reject(lambda:f.validate_state(state,provenance),'state refusal '+str(len(checks)))
# Pure provenance parser uses the actual stdlib hash predicate, with no checkpoint/tensor decoding.
provsrc=(M/REL/'provenance.py').read_bytes();env={'re':re};extract(provsrc,'require_hash',env)
pfn=extract(bodies['checkpoints.py'],'_provenance',{'financial':f,'require_hash':env['require_hash']})
p={'source_hashes':['0'*64],'config_hash':'1'*64,'input_hash':'2'*64,'dictionary_hash':'3'*64,'fold_id':'f','cell_id':'c','source_commit':'4'*40};pfn(p);checks.append('legacy provenance accepted');pfn({**p,'model_execution':identity});checks.append('selected provenance accepted')
reject(lambda:pfn({**p,'model_execution':None}),'explicit null provenance refused');reject(lambda:pfn({**p,'source_commit':'bad'}),'wrong source refused')
# Cross-module exact keyword signature joins, without execution.
evalfn=func(bodies['evaluation.py'],'evaluate_cell');ok('execution' in [a.arg for a in evalfn.args.kwonlyargs] and 'treatment_reference' in [a.arg for a in evalfn.args.kwonlyargs],'evaluation both keyword interfaces')
call=next(n for n in ast.walk(func(bodies['run.py'],'execute_batch')) if isinstance(n,ast.Call) and ast.unparse(n.func)=='evaluate_cell');ok({'execution','treatment_reference','feature_binding_output','example_binding_output'}<={k.arg for k in call.keywords},'batch forwards financial and retained treatment bindings')
for s in ['preflight_treatment','prepare','batch_factory']:
 ok(any(isinstance(n,ast.Call) and ast.unparse(n.func)==s for n in ast.walk(evalfn)),'retained evaluation '+s)
job=(M/REL/'job.py').read_text();ok("package.glob('*.py')" in job,'actual job closure automatically includes new module')
ok(not {'numpy','torch','scipy','pandas'}&set(sys.modules),'no numerical imports')
result={'checks':len(checks),'passed':checks,'candidate_sha256':{k:sha(v) for k,v in bodies.items()},'author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes()),'actual_models_or_authority_constructed':False,'numerical_execution':False}
(H/'CHECKS01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks),'status':'passed'}))
