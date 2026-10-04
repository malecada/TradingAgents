"""Deterministic eight-role/source registration preparation. Never admission/release."""
import argparse,copy,hashlib,importlib,inspect,json,os,shutil,sys
from pathlib import Path
import recovery04 as R
HERE=Path(__file__).resolve().parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
TARGET=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source')
NEW='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'
OLD='financial-wrapper-classification-eager-interrupt1-20261003-01'
PREFIX='fixture_inputs/financial_wrapper_recordfix01'
ORIGINS='60fc3567dd1124ddebab24dcd2ccdd8f1e4bd09886a7285934116eadf31337d0'
CORRECTION='e2d9208ac51fd5876b63b6a72f734fc4fedd28fa42ac9c7fa1014346feb8404c'
SOURCE_PATH='tradingagents/research/onchain_replication/financial_wrapper_fixture.py'
ROLE_NAMES={'environment','execution_job','model','runtime_mapping','source_closure','synthetic_recipe','training','wrapper_plan'}

def read(name):return R.read(HERE,name)
def authenticate():
 raw=read('ORIGINS01.json');R.require(R.digest(raw)==ORIGINS,'frozen origins');pins=json.loads(raw)
 for name,ref in pins.items():R.require(R.digest(read(name))==ref['sha256'],'prepared original changed '+name)
 q=json.loads(read('ORIGINAL_REQUEST.json'));R.require(q['source']=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0' and R.digest(read('ORIGINAL_GATE.json'))==q['registration_sha256']=='6818dfdc48879fde8bf149bd1dae252885c6460a209e31af5a17a66012247691','actual original gate/source')
 for name,pin in q['source_files'].items():R.require(R.digest(R.read(CAP,name))==pin,'original current capsule body '+name)
 R.require(R.digest(read('corrected_wrapper.py'))==CORRECTION,'accepted correction body')
 R.require(not os.path.lexists(TARGET.parent) and TARGET.resolve()==TARGET and TARGET.parent.parent==CAP.parent.parent,'proposed fresh target not absent/canonical/authorized')
 return q

def schema_check(plan,experiment,job):
 # Actual pinned original APIs; metadata methods only. No admit/start call.
 sys.path.insert(0,str(CAP));ad=importlib.import_module('tradingagents.research.admission');fw=importlib.import_module('tradingagents.research.onchain_replication.financial_wrapper_fixture');lc=importlib.import_module('tradingagents.research.lifecycle')
 q=json.loads(read('ORIGINAL_REQUEST.json'))
 for module in (ad,fw,lc):
  p=Path(module.__file__).resolve();R.require(p.is_relative_to(CAP) and R.digest(R.read(CAP,str(p.relative_to(CAP))))==q['source_files'][str(p.relative_to(CAP))],'actual API origin')
 fw.validate_plan(plan);fw.schema(job);ad._window(experiment['windows'][0])
 for identity in (plan['experiment'],plan['cell_id'],plan['namespace']):ad.identity(identity,'recordfix proposal')
 R.require(set(experiment['inputs'])==ROLE_NAMES and experiment['cells']==[plan['cell_id']] and experiment['parent']is None,'initial exact roles/cell/parent')
 for role,ref in experiment['inputs'].items():
  ad.identity(role,'role');R.require(set(ref)=={'dataset','path','sha256'} and ref['dataset']=='synthetic','actual input mapping schema');ad.local_path(TARGET,ref['path']);R.require(type(ref['sha256'])is str and len(ref['sha256'])==64 and all(c in '0123456789abcdef'for c in ref['sha256']),'actual input hash type')
 R.require(not any(x in sys.modules for x in ('numpy','torch','pandas','scipy')),'no numerical imports')
 return {'admission':ad.__file__,'fixture':fw.__file__,'lifecycle':lc.__file__,'ResearchRun_start_signature':str(inspect.signature(lc.ResearchRun.start)),'admit_or_start_called':False}

def build():
 q=authenticate();gate=json.loads(read('ORIGINAL_GATE.json'));old=gate['experiments'][OLD];order=json.loads(read('ORIGINAL_ORDER.json'))['complete18_topological_order'];phases=json.loads(read('ORIGINAL_PHASES.json'));R.require(len(gate['experiments'])==10 and len(order)==len(phases['slots'])==18 and set(order)=={p['proposed_plan']['experiment']for p in phases['slots']},'actual10 registered/18slots')
 family=gate['families'][old['family']];R.require(family['attempt_budget']==18 and family['prior_attempts']==0,'original family18/0');R.require(NEW not in order and NEW not in gate['experiments'],'fresh fixed identity')
 bodies={};paths={role:PREFIX+'/'+role+'.json'for role in ROLE_NAMES}
 for role in ROLE_NAMES:bodies[paths[role]]=read('original_'+role+'.json')
 plan=json.loads(bodies[paths['wrapper_plan']]);plan.update(experiment=NEW,namespace=NEW);bodies[paths['wrapper_plan']]=R.encode(plan)
 job=json.loads(bodies[paths['execution_job']]);job['resources']['disk_paths']=[str(TARGET)];job['resources']['storage_budget']['root']=str(TARGET);bodies[paths['execution_job']]=R.encode(job)
 closure=json.loads(bodies[paths['source_closure']]);R.require(len(closure['installed'])==194 and sum(n.startswith('tradingagents/')for n in closure['installed'])==149,'original194/149');closure['installed'][SOURCE_PATH]=CORRECTION;bodies[paths['source_closure']]=R.encode(closure)
 source=dict(q['source_files']);R.require(len(source)==289,'original pre-gate289');source[q['registration']]=q['registration_sha256'];source[SOURCE_PATH]=CORRECTION
 source.update({p:R.digest(raw) for p,raw in bodies.items()});R.require(len(source)==298,'290preservedpaths plus8new role bodies')
 exp=copy.deepcopy(old);exp.update(inputs={role:{'dataset':'synthetic','path':paths[role],'sha256':R.digest(bodies[paths[role]])}for role in sorted(ROLE_NAMES)},source_files=source,charter={'path':PREFIX+'/CHARTER_PENDING.json','sha256':None},cumulative_budget_extension={'extension':{'path':PREFIX+'/EXTENSION_PENDING.json','sha256':None},'review':{'path':PREFIX+'/EXTENSION_REVIEW_PENDING.json','sha256':None}})
 api=schema_check(plan,exp,job);proposed=copy.deepcopy(gate);proposed['experiments'][NEW]=exp
 R.require(all(proposed['experiments'][name]==value for name,value in gate['experiments'].items()) and proposed['families']==gate['families'] and proposed['datasets']==gate['datasets'],'original actual definitions changed')
 dependencies=[]
 for slot in phases['slots']:
  p=slot['proposed_plan']
  if p['task']=='classification' and p['execution']=='eager' and p['phase'] in ('continue100','predict'):
   dependencies.append({'identity':p['experiment'],'original_unregistered_draft':slot,'proposed_dependencies':[NEW if d==OLD else d for d in slot['dependencies']],'actual_prior_input':None,'actual_reference_input':None,'actual_claim_pin':None,'actual_checkpoint_members':None,'independent_outcome_acceptance':None,'external_recovery':None,'registration':None,'status':'UNREGISTERED_UNRESERVED_WITHHELD'})
 allocation={'schema_version':1,'program_id':gate['program_id'],'base_family':family,'proposed_cumulative_ceiling':19,'original_order':order,'fresh_identity':NEW,'proposed_executable_order':[NEW]+[x for x in order if x!=OLD],'permanently_reserved_original_outer':OLD,'old_outer_is_numerical_claim':False,'proposed_numerical_claims_before':0,'old18_definitions_preserved':True,'financial_credit':0,'admission':None}
 extension={'schema_version':1,'program_id':gate['program_id'],'base_family':family,'cumulative_ceiling':19,'consumed_before':0,'initial_experiment':NEW,'allocation':{'path':PREFIX+'/ALLOCATION_DRAFT.json','sha256':R.digest(R.encode(allocation))},'claims':[],'reason':'One fixed source-corrected initial wrapper identity added prospectively; prior reserved predispatch outer remains unavailable. No refund, transfer or synthetic claim.'}
 return {'status':'DRAFT_NOT_RELEASED','target':str(TARGET),'original_gate_sha256':q['registration_sha256'],'original_source':q['source'],'original_registered':10,'original_slots':18,'proposed_gate_entries':11,'total_preserved_plus_new_slots':19,'implementation':194,'package':149,'original_tracked_paths':290,'prospective_source_pins_before_authority':298,'prospective_tracked_before_authority':299,'new_gate_excluded_from_own_source_map':True,'source_body_replacements':{SOURCE_PATH:CORRECTION},'future_source_commit':None,'future_design_source':None,'future_registration_commit':None,'charter':None,'cumulative_review':None,'complete_original_failed_recovery':None,'caller':None,'native_capacity':None,'initial_experiment':exp,'gate':proposed,'bodies':bodies,'allocation':allocation,'extension':extension,'dependent_rebindings':dependencies,'original_phases':phases,'api':api,'hard_blocker':'effective_budget requires a nonempty closed-claim snapshot; actual zero numericalclaims cannot satisfy it. Separate reviewed policy/interface decision required; no fabricated claim.','release':False,'paper_financial_credit':0}

def release(*args,**kwargs):raise ValueError('DRAFT_NOT_RELEASED: zero-claim cumulative19 API refusal, genuine charter/source/gate/review/recovery/caller/native authority unresolved')
def write(out):
 R.require(out.parent==HERE and not os.path.lexists(out) and shutil.disk_usage(HERE).free>=R.FLOOR,'fresh owned output/10GiBfloor');v=build();out.mkdir();bodies=v.pop('bodies')
 for name,raw in sorted(bodies.items()):p=out/'bodies'/name;p.parent.mkdir(parents=True,exist_ok=True);R.require(not os.path.lexists(p),'exclusive body');p.open('xb').write(raw)
 for key,name in [('gate','GATE_DRAFT.json'),('allocation','ALLOCATION_DRAFT.json'),('extension','EXTENSION_DRAFT.json'),('dependent_rebindings','DEPENDENT_REBINDINGS_DRAFT.json'),('original_phases','ORIGINAL_PHASES_PRESERVED.json')]:R.put(out/name,v.pop(key))
 v['role_body_pins']={k:R.digest(raw)for k,raw in sorted(bodies.items())};R.put(out/'PREPARATION01.json',v);return v
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--generate',action='store_true');p.add_argument('--release',action='store_true');a=p.parse_args()
 if a.release:release()
 R.require(a.generate,'explicit source generation required');print(json.dumps(write(HERE/'generated01'),sort_keys=True))
