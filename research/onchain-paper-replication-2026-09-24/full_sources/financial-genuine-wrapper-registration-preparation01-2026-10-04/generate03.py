"""Genuine API checked registration DRAFT; never calls admit/start or releases."""
import argparse,copy,hashlib,importlib,inspect,json,os,shutil,stat,sys
from pathlib import Path
import recovery04 as R
from bounded_git01 import git
H=Path(__file__).resolve().parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
SOURCE='868bfa6404a2c34d6e5b6e0932a2baf4b38eb370'
ORIGIN='192a711f60cca5d0314069ec1c49f5606f3c06cfbe1e5670e7b326cc6796d8cc'
INPUTS={'environment','execution_job','model','runtime_mapping','source_closure','synthetic_recipe','training','wrapper_plan'}
DATASET='financial-wrapper-synthetic-f8b1ec1eed90'
WINDOW={'dataset':'synthetic','start':'2026-10-03T00:00:00Z','end':'2026-10-03T00:00:01Z','availability':'existing'}

def references():
 raw=R.read(H,'ORIGINS01.json');R.require(R.digest(raw)==ORIGIN,'origin pins');refs=json.loads(raw);result={}
 for k,v in refs.items():
  p=Path(v['path']);raw=R.read(p.parent,p.name);R.require(R.digest(raw)==v['sha256'],'origin changed');result[k]=json.loads(raw)
 return result

def authenticate(refs):
 rows=refs['sources']['rows'];R.require(len(rows)==243 and refs['sources']['current_source']==SOURCE,'actual243 source map')
 R.require(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'HEAD differs')
 rawtree=git(CAP,['ls-tree','-r','-z',SOURCE],cap=R.FILE);tree={}
 for entry in rawtree.split(b'\0')[:-1]:
  header,name=entry.split(b'\t');mode,kind,oid=header.decode().split();R.require(kind=='blob','tree type');tree[name.decode()]=(mode,oid)
 R.require(rawtree.endswith(b'\0') and set(tree)=={r['path'] for r in rows},'whole actual tracked set')
 pins={}
 for row in rows:
  name=row['path'];raw=R.read(CAP,name);oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  R.require(R.digest(raw)==row['sha256'] and len(raw)==row['bytes'] and stat.S_IMODE((CAP/name).lstat().st_mode)==row['mode'],'source body/mode')
  R.require(tree[name]==(row['git_mode'],row['git_object']) and oid==row['git_object'],'source OID/mode');pins[name]=row['sha256']
 R.require(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'HEAD changed');return pins

def actual_api(pins):
 # Genuine imports from the exact authenticated isolated source, no aliases/stubs.
 R.require(not any(n=='tradingagents' or n.startswith('tradingagents.') for n in sys.modules),'fresh actual package import required')
 sys.path.insert(0,str(CAP));ad=importlib.import_module('tradingagents.research.admission');lc=importlib.import_module('tradingagents.research.lifecycle');fw=importlib.import_module('tradingagents.research.onchain_replication.financial_wrapper_fixture')
 for name,module in tuple(sys.modules.items()):
  if name=='tradingagents' or name.startswith('tradingagents.'):
   p=Path(module.__file__).resolve();R.require(p.is_relative_to(CAP),'wrong imported package prefix');rel=p.relative_to(CAP).as_posix();R.require(R.digest(R.read(CAP,rel))==pins[rel],'actual import body not authenticated')
 R.require(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'numerical import forbidden')
 R.require('root' in inspect.signature(lc.ResearchRun.start).parameters,'genuine lifecycle signature')
 return ad,lc,fw

def validate_initial(exp,plan,ad,fw):
 fw.validate_plan(plan)
 for name in (plan['experiment'],plan['cell_id'],plan['namespace']):ad.identity(name,'proposed')
 R.require(exp['cells']==[plan['cell_id']] and set(exp['inputs'])==INPUTS,'exact cell/eight inputs')
 for name,ref in exp['inputs'].items():
  R.require(set(ref)=={'dataset','path','sha256'} and ref['dataset']=='synthetic','exact input descriptor')
  ad.identity(name,'input');ad.local_path(CAP,ref['path']);R.require(len(ref['sha256'])==64 and all(c in '0123456789abcdef' for c in ref['sha256']),'input hash')
 ad._window(exp['windows'][0]);R.require(exp['reuse']=='exploratory' and exp['stage']=='development','exposure semantics')
 R.require(plan['phase'] not in ('continue100','predict'),'dependent actual outcomes unavailable')

def release(_value):raise ValueError('DRAFT_NOT_RELEASED: charter/cumulative allowance/current gate/caller/recovery/native eligibility missing')

def generate():
 out=H/'generated03';R.require(not out.exists(),'one-use preparation identity');R.require(shutil.disk_usage(H).free>=R.FLOOR,'10GiB floor')
 refs=references();pins=authenticate(refs);ad,lc,fw=actual_api(pins);charter=refs['charter'];phases=charter['phases'];templates=refs['plans']['templates'];R.require(len(phases)==len(templates)==18,'18 slots')
 R.require(len({p['proposed_identity'] for p in phases})==18 and len({p['proposed_cell'] for p in phases})==10,'proposed identities/cells')
 runtime=ad.runtime_hashes();bodies={};initial={};withheld=[];plans=[]
 common={}
 for role in sorted(INPUTS-{'wrapper_plan','execution_job'}):
  origin=refs['sources']['environment_input']['path'] if role=='environment' else 'fixture_inputs/financial_wrapper_draft01/'+role+'.json'
  path='fixture_inputs/financial_wrapper_registered01/common/'+role+'.json';bodies[path]=R.read(CAP,origin);R.require(R.digest(bodies[path])==pins[origin],'current common body changed after source authentication');common[role]=path
 for row,t in zip(phases,templates,strict=True):
  p=copy.deepcopy(t);p.update(experiment=row['proposed_identity'],cell_id=row['proposed_cell'],namespace=row['proposed_identity'])
  R.require('/'.join((p['task'],p['execution'],p['phase']))==row['logical_key_not_identity'],'DAG shape');fw.validate_plan(p)
  plans.append({'proposed_plan':p,'dependencies':row['proposed_dependencies'],'expected_disposition_if_contract_met':row['expected_lifecycle_status'],'actual_claim':None,'actual_outcome':None})
  if row['dependencies']:
   withheld.append({'proposed_identity':p['experiment'],'proposed_cell':p['cell_id'],'dependencies':row['proposed_dependencies'],'registration':None,'actual_parent_hash':None,'actual_checkpoint_members':None,'reason':'genuine dependent outcomes unavailable'});continue
  base='fixture_inputs/financial_wrapper_registered01/'+p['experiment'];pp=base+'/plan.json';jp=base+'/job.json';job=copy.deepcopy(refs['job']);job['resources']['disk_paths']=[str(CAP)];job['resources']['storage_budget']['root']=str(CAP);fw.schema(job)
  bodies[pp]=R.encode(p);bodies[jp]=R.encode(job)
  inputs={}
  for role in sorted(INPUTS):
   path={'wrapper_plan':pp,'execution_job':jp}.get(role,common.get(role))
   raw=bodies[path] if path in bodies else R.read(CAP,path)
   inputs[role]={'dataset':'synthetic','path':path,'sha256':R.digest(raw)}
  R.require(inputs['model']['sha256']==fw.MODEL and inputs['training']['sha256']==fw.TRAINING and inputs['environment']['sha256']=='1ff7418a2b7c77300aea731cea5bba78277d323241ac0ec59f41f43207c66d87','science/expected environment pins')
  exp=copy.deepcopy(refs['template']['experiment_shape']);exp.update(cells=[p['cell_id']],family=charter['family'],inputs=inputs,parent=None,reuse='exploratory',runtime_hashes=runtime,selection=None,source_files=dict(pins),windows=[WINDOW])
  validate_initial(exp,p,ad,fw);initial[p['experiment']]=exp
 prospective={**pins,**{path:R.digest(raw) for path,raw in bodies.items()}}
 for exp in initial.values():exp['source_files']=prospective
 reg={'schema_version':1,'program_id':charter['program_id'],'families':{charter['family']:{'mechanism_id':charter['mechanism'],'attempt_budget':None,'prior_attempts':None,'history_reference':None}},'datasets':{'synthetic':{'identity':DATASET,'history_reference':'Conservative exposed synthetic recipe; see DATASET_HISTORY01.json in registration preparation; independent history review pending','exposures':[{'start':WINDOW['start'],'end':WINDOW['end'],'state':'exposed'}]}},'experiments':initial}
 R.require(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'source changed during composition')
 out.mkdir(mode=0o700)
 for path,raw in bodies.items():
  dest=out/'bodies'/path;dest.parent.mkdir(parents=True,exist_ok=True)
  with R.new_file(dest) as fd:sink=R.Sink(fd);sink.write(raw);os.fsync(fd)
 R.put(out/'INITIAL_REGISTRATION_DRAFT01.json',reg)
 R.put(out/'PHASES01.json',{'slots':plans,'withheld_dependent_registrations':withheld,'all18_unreserved':True,'ten_proposed_cells':10,'conditional_dispositions':{'COMPLETE':14,'FAILED':4},'paper_credit':0})
 R.put(out/'DATASET_HISTORY01.json',{'identity':DATASET,'recipe_sha256':'f8b1ec1eed902f3cca76bd7e06d2435accda699173b9a7942d10c37c64f01040','administrative_synthetic_window':WINDOW,'window_is_market_date_or_fresh_holdout':False,'classification':'conservatively exposed exploratory engineering','prior_related_trial_accounting':None,'independent_history_acceptance':None,'physical_or_numerical_replay_authorized':False})
 result={'status':'DRAFT_NOT_RELEASED','current_source':SOURCE,'current_tracked':243,'implementation':194,'package':149,'existing_auxiliary':49,'new_proposed_plan_job_bodies':20,'new_unchanged_common_input_bodies':6,'proposed_total_bodies':len(bodies),'code_closure_anchor':'390c82a9958e135c24bcca80f3a636313ca27932','future_root_owned_input_prefix':'fixture_inputs/financial_wrapper_registered01','future_source_commit':None,'future_design_source':None,'future_registration_commit':None,'prospective_source_files_before_charter_gate':len(prospective),'initial_experiments':len(initial),'dependent_withheld':len(withheld),'actual_class':'tradingagents.research.lifecycle.ResearchRun','DatasetSchema_class_exists':hasattr(ad,'DatasetSchema'),'dataset_contract':'actual admission.admit plain mapping validation','actual_import_origins':{'admission':ad.__file__,'lifecycle':lc.__file__,'fixture':fw.__file__},'ResearchRun_start_signature':str(inspect.signature(lc.ResearchRun.start)),'admit_or_start_called':False,'current_Torch_API_observed':False,'postclaim_environment_mismatch_spends_attempt':True,'actual_charter':None,'actual_gate':None,'cumulative_allowance':None,'caller':None,'complete_recovery':None,'native_capacity':None,'proposed_body_pins':{p:R.digest(b) for p,b in bodies.items()}}
 R.put(out/'PREPARATION01.json',result);R.require(shutil.disk_usage(out).free>=R.FLOOR,'final floor');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--generate',action='store_true');p.add_argument('--release',action='store_true');a=p.parse_args()
 if a.release:release(None)
 R.require(a.generate,'explicit generation required');print(json.dumps(generate()))
