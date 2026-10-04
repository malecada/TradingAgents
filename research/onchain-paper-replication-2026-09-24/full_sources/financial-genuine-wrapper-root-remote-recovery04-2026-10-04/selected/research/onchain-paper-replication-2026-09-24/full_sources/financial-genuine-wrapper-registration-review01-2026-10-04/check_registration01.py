"""Independent metadata/source-only review; no admit, start, job, array or generator execution."""
import ast,copy,hashlib,importlib,importlib.abc,inspect,json,os,pathlib,stat,subprocess,sys,time
ROOT=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';P=BASE/'financial-genuine-wrapper-registration-preparation01-2026-10-04';G=P/'generated03';OUT=pathlib.Path(__file__).resolve().parent;CAP=pathlib.Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');H=lambda b:hashlib.sha256(b).hexdigest();checks=0;pins={}
def ok(v,n):
 global checks
 if not v:raise AssertionError(n)
 checks+=1
def read(p):
 s=p.lstat();ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'bounded regular source/metadata');b=p.read_bytes();ok(len(b)==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns,'stable bytes');pins[str(p)]={'sha256':H(b),'bytes':len(b)};return b
def js(p):return json.loads(read(p))
def git(*args):
 r=subprocess.run(['git','--no-optional-locks','-c','protocol.allow=never','-C',str(CAP),*args],capture_output=True,timeout=30,check=True,env={**os.environ,'GIT_NO_REPLACE_OBJECTS':'1','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'});ok(not r.stderr and len(r.stdout)<=4*1024**2,'bounded offline Git');return r.stdout
source=read(P/'generate03.py');ok(H(source)=='520d097a036483287eb0de2ec9bfa20c6a303ce60eace4c37383164d2f5d9209','exact reviewed generator03')
refsraw=read(P/'ORIGINS01.json');ok(H(refsraw)=='192a711f60cca5d0314069ec1c49f5606f3c06cfbe1e5670e7b326cc6796d8cc','author frozen origins');refs={}
for k,v in json.loads(refsraw).items():raw=read(pathlib.Path(v['path']));ok(H(raw)==v['sha256'],'declared actual origin '+k);refs[k]=json.loads(raw)
head=git('rev-parse','HEAD').decode().strip();ok(head=='868bfa6404a2c34d6e5b6e0932a2baf4b38eb370','actual current source')
objects={}
for raw in git('ls-tree','-r','-z',head).split(b'\0'):
 if raw:left,n=raw.split(b'\t');mode,kind,oid=left.decode().split();objects[n.decode()]=(mode,kind,oid)
rows=refs['sources']['rows'];ok(len(rows)==len(objects)==243 and set(objects)=={r['path'] for r in rows},'whole current243')
current={}
for row in rows:
 n=row['path'];raw=read(CAP/n);mode,kind,oid=objects[n]
 ok(kind=='blob' and mode in ('100644','100755') and H(raw)==row['sha256'] and len(raw)==row['bytes'] and stat.S_IMODE((CAP/n).stat().st_mode)==row['mode'],'actual exact source byte/type/mode')
 ok(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid==row['git_object'] and mode==row['git_mode'],'actual OID');current[n]=H(raw)
regraw=read(G/'INITIAL_REGISTRATION_DRAFT01.json');reg=json.loads(regraw);prep=js(G/'PREPARATION01.json');phase=js(G/'PHASES01.json');dh=js(G/'DATASET_HISTORY01.json');charter=refs['charter'];byid={p['proposed_identity']:p for p in charter['phases']};body={}
for root,dirs,files in os.walk(G/'bodies',followlinks=False):
 for n in dirs:ok(not (pathlib.Path(root)/n).is_symlink(),'body directory type')
 for n in files:
  p=pathlib.Path(root)/n;rel=p.relative_to(G/'bodies').as_posix();ok(rel.startswith('fixture_inputs/financial_wrapper_registered01/'),'explicit portable prefix');body[rel]=read(p)
ok(len(body)==26 and {n:H(b) for n,b in body.items()}==prep['proposed_body_pins'],'exact26portable body pins')
prospective={**current,**{n:H(b) for n,b in body.items()}};ok(len(prospective)==269 and not set(current)&set(body),'243+26 prospective269 no collision')
# Block numerical module imports even if a future source unexpectedly adds one.
class ForbidNumerics(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'torch','numpy','scipy','pandas'}:raise RuntimeError('numerical import forbidden in reviewer')
sys.meta_path.insert(0,ForbidNumerics());ok(not any(n=='tradingagents' or n.startswith('tradingagents.') for n in sys.modules),'fresh authentic package context');sys.path.insert(0,str(CAP))
ad=importlib.import_module('tradingagents.research.admission');lc=importlib.import_module('tradingagents.research.lifecycle');fw=importlib.import_module('tradingagents.research.onchain_replication.financial_wrapper_fixture')
imports={}
for n,m in tuple(sys.modules.items()):
 if n=='tradingagents' or n.startswith('tradingagents.'):
  p=pathlib.Path(m.__file__).resolve();ok(p.is_relative_to(CAP) and H(read(p))==current[str(p.relative_to(CAP))],'actual imported module source');imports[n]={'path':str(p),'sha256':H(read(p))}
ok(not hasattr(ad,'DatasetSchema') and callable(lc.ResearchRun.start),'actual API no fake DatasetSchema or Run')
ok(inspect.signature(lc.ResearchRun.start).parameters['design_source'].default is None and inspect.signature(lc.ResearchRun.start).parameters['bindings'].default is None,'genuine lifecycle default signature')
# Import validation helpers by extraction only, not generator top level or generate().
module=ast.parse(source);defs={n.name:n for n in module.body if isinstance(n,ast.FunctionDef)}
class Require:
 @staticmethod
 def require(v,msg):
  if not v:raise ValueError(msg)
ENV={'R':Require,'CAP':CAP,'INPUTS':{'environment','execution_job','model','runtime_mapping','source_closure','synthetic_recipe','training','wrapper_plan'}}
exec(compile(ast.Module(body=[defs['validate_initial'],defs['release']],type_ignores=[]),'<actual-generator-pure-validators>','exec'),ENV)
initial=[p for p in charter['phases'] if not p['dependencies']];dependent=[p for p in charter['phases'] if p['dependencies']]
ok(len(initial)==len(reg['experiments'])==10 and len(dependent)==len(phase['withheld_dependent_registrations'])==8,'10exactinitial8withheld')
ok(set(reg['experiments'])=={p['proposed_identity'] for p in initial},'initial exact identity set')
models={};inputrows=[]
for name,exp in reg['experiments'].items():
 row=byid[name];plan=json.loads(body[exp['inputs']['wrapper_plan']['path']]);job=json.loads(body[exp['inputs']['execution_job']['path']]);fw.validate_plan(plan);fw.schema(job);ENV['validate_initial'](exp,plan,ad,fw)
 ok(plan['experiment']==name and plan['cell_id']==row['proposed_cell'] and plan['namespace']==name and (plan['task'],plan['execution'],plan['phase'])==(row['task'],row['backend'],row['phase']),'all actual plan identity/task/backend/cell phases')
 ok(plan['prior_input'] is None and plan['reference_input'] is None and exp['parent'] is None,'initial no invented parent')
 ok(set(exp['inputs'])==ENV['INPUTS'] and exp['source_files']==prospective and exp['runtime_hashes']==ad.runtime_hashes(),'each exact8roles269source/runtimehelper pins')
 ok(exp['charter']=={'path':None,'sha256':None} and set(exp['outputs'])==fw.OUTPUTS and exp['family']==charter['family'],'no charterfake and exactoutputfamily')
 ok(job['payload']=={'plan_input':'wrapper_plan'} and job['environment_input']=='environment' and job['resources']['disk_paths']==[str(CAP)] and job['resources']['storage_budget']['root']==str(CAP),'genuine whole source job route')
 for role,ref in exp['inputs'].items():
  ok(set(ref)=={'dataset','path','sha256'} and ref['dataset']=='synthetic' and ref['path'] in body and H(body[ref['path']])==ref['sha256'],'80 exact descriptor-body joins');ad.local_path(CAP,ref['path']);inputrows.append({'experiment':name,'role':role,**ref})
 ok(exp['reuse']=='exploratory' and exp['stage']=='development' and len(exp['windows'])==1,'conservative exploratory mode')
 ad._window(exp['windows'][0]);models[name]={'plan':plan,'job':job}
ok(len(inputrows)==80,'full descriptor denominator80')
common='fixture_inputs/financial_wrapper_registered01/common/'
for role in ENV['INPUTS']-{'wrapper_plan','execution_job'}:
 oldpath=refs['sources']['environment_input']['path'] if role=='environment' else 'fixture_inputs/financial_wrapper_draft01/'+role+'.json';ok(body[common+role+'.json']==read(CAP/oldpath),'six common body byte-identical actual origin')
closure=json.loads(body[common+'source_closure.json']);ok(len(closure['installed'])==194 and sum(n.startswith('tradingagents/') for n in closure['installed'])==149 and all(current[n]==v for n,v in closure['installed'].items()),'194149 code closure exact subset243')
ok(H(body[common+'model.json'])==fw.MODEL and H(body[common+'training.json'])==fw.TRAINING and json.loads(body[common+'synthetic_recipe.json'])==fw.RECIPE and H(body[common+'environment.json'])=='1ff7418a2b7c77300aea731cea5bba78277d323241ac0ec59f41f43207c66d87','science recipe expectation exact')
for p in phase['withheld_dependent_registrations']:
 row=byid[p['proposed_identity']];ok(p['dependencies']==row['proposed_dependencies'] and p['proposed_cell']==row['proposed_cell'] and all(p[k] is None for k in ['registration','actual_parent_hash','actual_checkpoint_members']),'eight withheld actualdependency fields')
for p in phase['slots']:
 row=byid[p['proposed_plan']['experiment']];fw.validate_plan(p['proposed_plan']);ok(p['dependencies']==row['proposed_dependencies'] and p['actual_claim'] is None and p['actual_outcome'] is None,'all18plans unclaimedDAG')
ok(phase['all18_unreserved'] is True and phase['conditional_dispositions']=={'COMPLETE':14,'FAILED':4} and phase['paper_credit']==0,'no actual outcomes or credit')
fam=reg['families'][charter['family']];ok(fam['mechanism_id']==charter['mechanism'] and all(fam[k] is None for k in ['attempt_budget','prior_attempts','history_reference']),'no fabricatedallowance/history')
ok(dh['window_is_market_date_or_fresh_holdout'] is False and dh['prior_related_trial_accounting'] is None and dh['independent_history_acceptance'] is None,'dataset history stillunadmitted')
ds=reg['datasets']['synthetic'];window=next(iter(reg['experiments'].values()))['windows'][0];ok(ds['identity']==dh['identity']=='financial-wrapper-synthetic-f8b1ec1eed90' and window==dh['administrative_synthetic_window'] and ds['exposures']==[{'start':window['start'],'end':window['end'],'state':'exposed'}],'explicit one-second administrative dataset clock')
# Concrete immutable reference DAG: no future registration/source hash appears as a dependency.
for key in ['future_source_commit','future_design_source','future_registration_commit','actual_charter','actual_gate','cumulative_allowance','caller','complete_recovery','native_capacity']:ok(prep[key] is None,'future authority null '+key)
ok('registration_commit' not in reg and not any(n.endswith('INITIAL_REGISTRATION_DRAFT01.json') for n in prospective),'no registration selfpin or invented schemafield')
ok(H(regraw) not in regraw.decode() and all(H(regraw).encode() not in b for b in body.values()),'no own registrationhash cycle')
jobast=ast.parse(read(CAP/'tradingagents/research/onchain_replication/job.py'));starts=[n for n in ast.walk(jobast) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='start' and ast.unparse(n.func.value)=='ResearchRun'];ok(len(starts)==1 and {k.arg for k in starts[0].keywords}=={'root','registration','experiment','source'},'actual job no separate design/bindings forwarding')
adast=ast.parse(read(CAP/'tradingagents/research/admission.py'));af=next(n for n in adast.body if isinstance(n,ast.FunctionDef) and n.name=='admit');ok(any(isinstance(n,ast.Assign) and ast.unparse(n)=='design_source = design_source or source' for n in af.body),'actual admit design defaults executing source')
# Negative controls and explicit limits of partial validation; never full admit/start.
negative=[]
def case(name,fn,accept=False):
 error=None
 try:fn()
 except (ValueError,TypeError,KeyError) as e:error=type(e).__name__+': '+str(e)
 ok((error is None)==accept,name);negative.append({'name':name,'accepted':error is None,'error':error})
e=next(iter(reg['experiments'].values()));plan=models[next(iter(reg['experiments']))]['plan'];job=models[next(iter(reg['experiments']))]['job']
for k,v in [('experiment',None),('namespace','../escape'),('phase','unknown'),('task','other'),('execution','cold'),('prior_input','fakeparent')]:
 t=copy.deepcopy(plan);t[k]=v;case('actual plan refuses '+k,lambda t=t:fw.validate_plan(t))
for k,v in [('dataset','other'),('path','../escape'),('sha256','invalid')]:
 t=copy.deepcopy(e);t['inputs']['model'][k]=v;case('partial validator refuses '+k,lambda t=t:ENV['validate_initial'](t,plan,ad,fw))
for name,mut in [('memory',lambda j:j['resources'].__setitem__('memory_max_bytes',4*1024**3)),('wall',lambda j:j['resources'].__setitem__('wall_seconds',1801)),('physical_policy',lambda j:j['resources'].__setitem__('physical_policy',{})),('fsize',lambda j:j['resources']['native_unit_limits'].__setitem__('file_size_bytes',8*1024**2))]:
 t=copy.deepcopy(job);mut(t);case('actual job refuses '+name,lambda t=t:fw.schema(t))
case('release always refuses',lambda:ENV['release'](reg))
t=copy.deepcopy(e);t['inputs']['model']['sha256']='0'*64;case('LIMIT format-valid wrong hash passes partial helper',lambda:ENV['validate_initial'](t,plan,ad,fw),True)
t=copy.deepcopy(plan);t['experiment']='different-valid-identity';case('LIMIT other valid identity passes partial helper',lambda:ENV['validate_initial'](e,t,ad,fw),True)
ok(not any(n in sys.modules for n in ['numpy','torch','scipy','pandas']),'no numericalimports at end');ok(git('rev-parse','HEAD').decode().strip()==head,'actual current HEAD stable')
for n in body:ok(not (CAP/n).exists(),'newbody not installed')
ok(not (CAP/'research_runs').exists() or not list((CAP/'research_runs').iterdir()),'no livefinancialrun namespace')
r={'schema_version':1,'decision':'ACCEPTED_CONCRETE_SOURCE_ONLY_DRAFT_NOT_ADMITTED','checks':checks,'generator_sha256':H(source),'registration_draft_sha256':H(regraw),'current_source':head,'actual_current_files':243,'prospective_source_files_before_charter_gate':269,'implementation_files':194,'package_files':149,'initial_count':10,'dependent_withheld':8,'proposed_body_count':26,'input_descriptor_count':80,'common_origin_bodies_unchanged':6,'no_hash_cycle_observed':True,'actual_imported_sources':imports,'no_fictitious_DatasetSchema':True,'runtime_environment_is_expectation_not_current_observation':True,'admit_or_start_called':False,'numericalimports':False,'network':False,'controls':negative,'all_input_descriptors':inputrows,'all_read_body_pins':pins,'actual_allowance':None,'actual_registration':None,'actual_source_or_design_release':None,'actual_native':None,'qualification':'Partial validate_initial checks do not bind actual digest/experiment identity. Exact generated bodies were independently bound above; genuine admission/fixture run guards remain required.'}
with (OUT/'READBACK01.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'checks':checks,'initial':10,'withheld':8,'bodies':26,'descriptors':80,'current':243,'prospective':269,'controls':len(negative),'partial_validation_counterexamples':2,'admit_or_start':False}))
