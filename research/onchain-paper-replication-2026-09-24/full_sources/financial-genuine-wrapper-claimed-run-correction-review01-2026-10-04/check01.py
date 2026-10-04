import ast,copy,hashlib,json,os,stat
from pathlib import Path
HERE=Path(__file__).resolve().parent;PREP=HERE.parent/'financial-genuine-wrapper-claimed-run-correction-preparation01-2026-10-04';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');PREFIX='tradingagents/research/onchain_replication/';ID='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
check(sha((PREP/'MANIFEST01.json').read_bytes())=='b49a17d0dd34c3063b9ecca0adb2af48498b5f4f1d6da7771d07f1265e43f12a','exact author manifest')
m=load(PREP/'MANIFEST01.json');actual=[]
def walk(p):
 for q in p.iterdir():
  actual.append(str(q.relative_to(PREP)))
  if stat.S_ISDIR(q.lstat().st_mode):walk(q)
walk(PREP);check(set(actual)=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'complete author namespace including failed harnesses')
for r in m['members']:
 p=PREP/r['path'];s=p.lstat();check(stat.S_IMODE(s.st_mode)==r['mode'],'mode '+r['path'])
 if r['kind']=='file':check(s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'body '+r['path'])
 else:check(stat.S_ISDIR(s.st_mode),'typed directory '+r['path'])
old=(PREP/'original-financial_wrapper_fixture.py').read_bytes();new=(PREP/'overlay'/PREFIX/'financial_wrapper_fixture.py').read_bytes();check(sha(old)=='e2d9208ac51fd5876b63b6a72f734fc4fedd28fa42ac9c7fa1014346feb8404c' and sha(new)=='f4ea651b4677c83f8e16c316d17f704d44d9ec86ff78a4bf7c4b895e92e1a16e','old and new exact sources')
check((CAP/PREFIX/'financial_wrapper_fixture.py').read_bytes()==old,'actual old source remains installed')
for name in ('admission','lifecycle','job'):
 origin=CAP/('tradingagents/research/'+('onchain_replication/' if name=='job' else '')+name+'.py');check((PREP/('original-'+name+'.py')).read_bytes()==origin.read_bytes(),'genuine source '+name)
for n in ('original-financial_wrapper_fixture.py','original-admission.py','original-lifecycle.py','original-job.py','actual-claim.json','actual-failed.json'):(HERE/n).write_bytes((PREP/n).read_bytes())
(HERE/'candidate-financial_wrapper_fixture.py').write_bytes(new)
claim=load(PREP/'actual-claim.json');check((PREP/'actual-claim.json').read_bytes()==(CAP/'research_runs'/ID/'claim.json').read_bytes(),'actual claim4c54 retained');check((PREP/'actual-failed.json').read_bytes()==(CAP/'research_runs'/ID/'failed.json').read_bytes(),'actual failed35158 retained')
delta=load(PREP/'SOURCE_CLOSURE_DELTA01.json');closure=load(CAP/'fixture_inputs/financial_wrapper_recordfix01/source_closure.json')['installed'];check(len(closure)==len(delta['rows'])==194,'full194 denominator')
changed=[]
for r in delta['rows']:
 p=CAP/r['path'];b=p.read_bytes();check(sha(b)==r['original_sha256']==closure[r['path']] and len(b)==r['original_bytes'] and stat.S_IMODE(p.stat().st_mode)==r['original_mode'],'actual closure '+r['path'])
 if r['candidate_sha256']!=r['original_sha256']:changed.append(r['path']);check(r['candidate_sha256']==sha(new),'sole new closure pin')
check(changed==[PREFIX+'financial_wrapper_fixture.py'],'exact1changed193unchanged');check(delta['actual_candidate_source_commit'] is None,'future source not invented')
# Derive inverse independently from actual old seam and new author function boundaries.
sold=old.decode();snew=new.decode();start=snew.index(' # The worker already owns a genuine claim.');end=snew.index(" require(ad.experiment_id==run.admission.experiment_id",start);block=snew[start:end];inverse=snew[:start]+' ad,j=job._admitted(args);p=admitted(ad,j)\n'+snew[end:]
check(inverse==sold,'independent full byte inverse');check(ast.dump(ast.parse(inverse))==ast.dump(ast.parse(sold)),'independent full AST inverse')
oldt=ast.parse(sold);newt=ast.parse(snew);of={n.name:n for n in oldt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};nf={n.name:n for n in newt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for n in of:
 if n!='authorize':check(ast.dump(of[n])==ast.dump(nf[n]),'all other source AST '+n)
a=nf['authorize'];calls=[ast.unparse(n.func) for n in ast.walk(a) if isinstance(n,ast.Call)];check('job._admitted' not in calls and 'admit' not in calls,'no fresh admission route');check(snew.index('run._active();run._check_source();run._check_inputs()',snew.index('def authorize'))<start,'genuine existing active/source/input checks precede changed block')
check("require(type(run)is ResearchRun" in snew and "require(type(ad)is Admission and ad.ready is True" in block,'exact actual Run/Admission guards preserved')
for snippet in ["run.read_input('execution_job')","run.read_input('execution_workspace')","job.job_schema(j)","job.resource_policy(j['resources'],ad.root)","p=admitted(ad,j)"]:
 check(snippet in block,'original job checks reinstated '+snippet)
# Scalar projections preserve exact predicate logic; never instantiate Run/Admission/Owner.
class Project(ast.NodeTransformer):
 def __init__(self,m):self.m=m
 def visit(self,node):
  key=ast.unparse(node)
  if key in self.m:return ast.copy_location(ast.Name(id=self.m[key],ctx=ast.Load()),node)
  return super().visit(node)
def pred(message,mapping):
 n=next(n for n in ast.walk(a) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value==message)
 e=ast.fix_missing_locations(Project(mapping).visit(copy.deepcopy(n.args[0])));return compile(ast.Expression(e),'<exact candidate scalar predicate>','eval')
def evaluate(code,values):
 try:return bool(eval(code,{'Path':Path,'sha':sha,'json':json,'set':set,'PREFIX':PREFIX},values))
 except (TypeError,ValueError,KeyError,AttributeError):return False
argmap={k:k.replace('.','_') for k in ('args.root','ad.root','args.registration','ad.registration','args.experiment','ad.experiment_id','args.source','ad.source')};code=pred('actual args/existing Run admission differs',argmap);values={'args_root':str(CAP),'ad_root':CAP,'args_registration':claim['registration'],'ad_registration':claim['registration'],'args_experiment':ID,'ad_experiment_id':ID,'args_source':claim['source'],'ad_source':claim['source']};check(evaluate(code,values),'actual scalar args accepted')
for key in ('args_root','args_registration','args_experiment','args_source'):
 for bad in ('/tmp/elsewhere','wrong',None,17,False):
  v=dict(values);v[key]=bad;check(not evaluate(code,v),'args refuses '+key+' '+repr(bad))
code=pred('original job source/design binding differs',{k:k.replace('.','_') for k in ('ad.design_source','ad.source','ad.bindings','ad.bindings_sha256')});v={'ad_design_source':claim['source'],'ad_source':claim['source'],'ad_bindings':None,'ad_bindings_sha256':None};check(evaluate(code,v),'actual no-bindings source/design accepted')
for key in v:
 for bad in ('wrong',False,{},[],0):
  w=dict(v);w[key]=bad;check(not evaluate(code,w),'design/binding refuses '+key+' '+repr(bad))
raw=(CAP/claim['inputs']['execution_job']['path']).read_bytes();code=pred('execution job bytes differ',{"ad.inputs['execution_job']['sha256']":'pin'});check(evaluate(code,{'raw':raw,'pin':sha(raw)}),'actual execution job hash accepted')
for bad in (None,'',sha(raw).upper(),'0'*64,False,[],sha(raw+b' ')):check(not evaluate(code,{'raw':raw,'pin':bad}),'job pin refuses '+repr(bad))
code=pred('execution dependency source closure not registered',{'job.required_sources()':'required',"ad.experiment['source_files']":'sources'});required={PREFIX+p.name for p in (CAP/PREFIX).glob('*.py')}|{'tradingagents/research/'+p.name for p in (CAP/'tradingagents/research').glob('*.py')}|{'tradingagents/__init__.py'};sources=claim['experiment']['source_files'];check(evaluate(code,{'required':required,'sources':sources}),'actual full package closure accepted')
for name in sorted(required):check(not evaluate(code,{'required':required,'sources':set(sources)-{name}}),'each missing required source refuses '+name)
code=pred('execution imported from outside admitted source root',{'job.__file__':'jobfile','ad.root':'root'});check(evaluate(code,{'jobfile':str(CAP/PREFIX/'job.py'),'root':CAP}),'actual job import origin accepted');check(not evaluate(code,{'jobfile':str(HERE/'original-job.py'),'root':CAP}),'outside exact job origin refuses')
code=pred('registered execution workspace/ledger/artifact mapping differs',{"layout['sha256']":'pin','job.workspace_binding(ad.root)':'actual_workspace'});workspace={'root':str(CAP),'ledger':str(CAP/'research_runs'),'artifacts':str(CAP/'research_artifacts'),'git_common':str(CAP/'.git')};b=json.dumps(workspace).encode();check(evaluate(code,{'raw':b,'pin':sha(b),'actual_workspace':workspace}),'workspace scalar equal accepted')
for k in workspace:
 altered=dict(workspace);altered[k]='/wrong';b=json.dumps(altered).encode();check(not evaluate(code,{'raw':b,'pin':sha(b),'actual_workspace':workspace}),'workspace field refuses '+k)
# Original failed Run cannot be reopened: actual _active body scalar projection.
life=ast.parse((PREP/'original-lifecycle.py').read_bytes());active=next(n for n in ast.walk(life) if isinstance(n,ast.FunctionDef) and n.name=='_active');body=Project({'self.directory':'directory','self._claim_sha256':'pin'}).visit(copy.deepcopy(active));body=ast.fix_missing_locations(body);env={'digest':sha,'directory':CAP/'research_runs'/ID,'pin':sha((PREP/'actual-claim.json').read_bytes())};exec(compile(ast.Module(body=[body],type_ignores=[]),'<actual _active scalar projection>','exec'),env)
try:env['_active'](None)
except ValueError as e:check(str(e)=='run is terminal; output/completion cannot be repeated','actual terminal Run remains refused')
else:raise AssertionError('closed claim reopened')
sourcecheck=next(n for n in ast.walk(life) if isinstance(n,ast.FunctionDef) and n.name=='_check_source');own=next(k.value for n in ast.walk(sourcecheck) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='admit' for k in n.keywords if k.arg=='_own_claim');check(ast.unparse(own)=='self.admission.experiment_id','unchanged lifecycle exact own claim path')
ad=ast.parse((PREP/'original-admission.py').read_bytes());repeat=next(n for n in ast.walk(ad) if isinstance(n,ast.If) and n.lineno==317);rc=compile(ast.Expression(repeat.test),'<actual repeat predicate>','eval')
for own,expected in [(None,True),(ID,False),('another',True)]:check(eval(rc,{'prior':[claim],'experiment':ID,'_own_claim':own}) is expected,'unchanged repeat guard '+str(own))
# Compile only genuine pure wrapper schema and constants, no imports/package/run.
pure=[n for n in newt.body if (isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in ('GIB','FILE') for t in n.targets)) or (isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('Unavailable','require','schema'))];ns={};exec(compile(ast.Module(body=pure,type_ignores=[]),'<unchanged wrapper schema>','exec'),ns);job=json.loads(raw);ns['schema'](job);checks.append('actual pure wrapper job schema accepted')
for key in ('memory_high_bytes','memory_max_bytes','reserve_bytes','start_reserve_bytes','disk_floor_bytes','wall_seconds'):
 wrong=copy.deepcopy(job);wrong['resources'][key]+=1
 try:ns['schema'](wrong)
 except ValueError:checks.append('resource mutation refused '+key)
 else:raise AssertionError('weakened envelope '+key)
for path in ('kind','payload','schema_version'):
 wrong=copy.deepcopy(job);wrong[path]='bad'
 try:ns['schema'](wrong)
 except (ValueError,TypeError,KeyError):checks.append('job mutation refused '+path)
 else:raise AssertionError('bad job accepted')
out={'decision':'ACCEPTED_NARROW_SOURCE_CORRECTION_ONLY','checks':len(checks),'check_names':checks,'candidate_sha256':sha(new),'original_sha256':sha(old),'original_claim_sha256':sha((PREP/'actual-claim.json').read_bytes()),'original_failed_sha256':sha((PREP/'actual-failed.json').read_bytes()),'full_byte_and_AST_inverse':True,'changed_implementation_files':1,'unchanged_implementation_files':193,'actual_source_installed':False,'actual_candidate_source_commit':None,'new_identity':None,'new_registration':None,'new_caller':None,'failed_identity_reopen_allowed':False,'budget_extension':False,'runtime_authority_objects_constructed':0,'admit_calls':0,'start_calls':0,'native_jobs':0,'numerical_imports':0,'genuine_active_successful_authorize_execution':None,'qualification':'Exact source and scalar/schema projections only, including original real closed claim refusal. No fake Run/Admission/Owner or synthetic claims used.'}
with (HERE/'READBACK01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k!='check_names'}))
