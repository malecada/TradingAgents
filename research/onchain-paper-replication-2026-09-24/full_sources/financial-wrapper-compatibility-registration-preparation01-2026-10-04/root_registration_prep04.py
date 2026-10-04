from pathlib import Path
import json,hashlib,copy,subprocess,datetime
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-registration-preparation01-2026-10-04';D.mkdir(mode=0o700);T=D/'fixture_inputs/financial_wrapper_compatibility01';T.mkdir(parents=True,mode=0o700)
S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P=F/'financial-wrapper-compatibility-root-policy01-2026-10-04';B=F/'financial-wrapper-cumulative20-preparation01-2026-10-04';V=F/'financial-wrapper-cumulative20-review01-2026-10-04';I=F/'financial-wrapper-compatibility-three-consumer-input-investigation01-2026-10-04';C=F/'financial-wrapper-compatibility-concrete-policy-review01-2026-10-04'
def h(b):return hashlib.sha256(b).hexdigest()
def J(p):return json.loads(p.read_bytes())
def put(p,o):
 with p.open('x') as f:json.dump(o,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
def literal(src,name):
 body=src.read_bytes();p=T/name;p.write_bytes(body);return {'path':p.relative_to(D).as_posix(),'sha256':h(body)}
oldgate=J(S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json');oldexp=oldgate['experiments']['financial-wrapper-classification-eager-complete100-20261003-01'];policy=J(P/'POLICY01.json');ref=policy['consumers']['complete100'];id=ref['experiment'];roles={}
for role,descriptor in oldexp['inputs'].items():
 if role in ['wrapper_plan','source_closure']:continue
 desc=literal(S/descriptor['path'],role+'.json');roles[role]={'dataset':'synthetic',**desc}
roles['source_closure']={'dataset':'synthetic',**literal(P/'SOURCE_CLOSURE01.json','source_closure.json')}
roles['operational_source_compatibility']={'dataset':'synthetic',**literal(P/'POLICY01.json','policy.json')}
roles['operational_source_compatibility_review']={'dataset':'synthetic',**literal(C/'REVIEW_PROOF01.json','policy-review.json')}
plan=J(S/oldexp['inputs']['wrapper_plan']['path']);plan.update(experiment=id,namespace=id,cell_id=ref['cell_id']);put(T/'wrapper_plan.json',plan);roles['wrapper_plan']={'dataset':'synthetic','path':(T/'wrapper_plan.json').relative_to(D).as_posix(),'sha256':h((T/'wrapper_plan.json').read_bytes())}
assert len(roles)==10
for n,src in [('allocation20.json',B/'allocation20.DRAFT.json'),('extension20.json',B/'extension20.DRAFT.json'),('extension-review20.json',V/'REVIEW_ACCEPTANCE01.json')]:literal(src,n)
assert h((T/'extension20.json').read_bytes())=='07100b23f9a8c2dfcae98a8647f9f1eeb019f4093192cd4b2576c6a13bf9840e'
assert h((T/'allocation20.json').read_bytes())=='461df69895a0a5e70b23882c759790a4c000eb33d1662629cacd322b7d3b0116'
put(D/'UNRESOLVED_RECOVERY_ROLE01.json',{'role':'operational_source_compatibility_recovery','path':'fixture_inputs/financial_wrapper_compatibility01/policy-recovery.json','sha256':None,'genuine_body':None,'status':'ABSENT_NOT_SYNTHESIZED_NOT_ADMITTED'})
# Literal closed predecessor gate, no mutation of any original twelve definitions.
(D/'ORIGINAL_GATE12.json').write_bytes((S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json').read_bytes())
newexp=copy.deepcopy(oldexp);newexp['parent']=None;newexp['cells']=[ref['cell_id']];newexp['inputs']=roles;newexp['cumulative_budget_extension']={'extension':{'path':'fixture_inputs/financial_wrapper_compatibility01/extension20.json','sha256':h((T/'extension20.json').read_bytes())},'review':{'path':'fixture_inputs/financial_wrapper_compatibility01/extension-review20.json','sha256':h((T/'extension-review20.json').read_bytes())}}
newexp['source_files']=None
put(D/'EXPERIMENT_DRAFT_NOT_REGISTRATION01.json',{'identity':id,'experiment':newexp,'required_remaining':['actual independently accepted operational-source/policy recovery body, registered role11 and source pin','exact all tracked target source/body/runtime/gate map and genuine source=design commit','independent actual gate/admission/source and preclaim/caller review','complete final writable capsule/caller/contract/runtime metadata preservation and actual external complete recovery','final one-use release/fresh absent namespace/PID/resource checks'],'status':'DRAFT_NOT_REGISTRATION_NOT_ADMITTED_NOT_NUMERICALLY_RELEASED'})
# Freeze all three exact method/identity contracts now; dependencies stay genuine future outcomes.
for phase,c in policy['consumers'].items():
 pp=copy.deepcopy(plan);pp.update(phase=phase,experiment=c['experiment'],namespace=c['experiment'],cell_id=c['cell_id']);pp['prior_input']=None if phase=='complete100' else 'prior';pp['reference_input']='reference' if phase=='continue100' else None;put(D/(phase+'-PLAN_TEMPLATE01.json'),pp)
put(D/'PREPARATION_BINDING01.json',{'schema_version':1,'status':'CONCRETE_BYTES_PREPARATION_ONLY_NO_LIVE_MUTATION','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root':str(S),'current_source_design':'7b056a574e3e7b3c7ba209a39ee6a615e649d60c','existing_gate12_sha256':h((S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json').read_bytes()),'fixed_consumers':policy['consumers'],'current_reference_roles':10,'required_reference_roles_after_genuine_recovery':11,'actual_claims':3,'actual_spent_FAILED':3,'highest_actual_budget':19,'prospective_extension20_substance_review':h((V/'MACHINE01.json').read_bytes()),'extension20_adopted':False,'existing_twelve_experiments_changed':False,'original18phase_contracts':18,'original_remaining_phase_contracts':17,'paper_budget_changed':False,'paper_fits_completed':0,'scientific_inputs_unchanged':[{'role':r,'sha256':oldexp['inputs'][r]['sha256']} for r in ['model','training','synthetic_recipe','runtime_mapping','environment']],'history_or_checkpoint_rewritten':False,'independent_input_investigation_manifest':h((I/'MANIFEST01.json').read_bytes()),'own_input_count_is_preparation_not_final_release_cardinality':True})
print(id,len(roles))
