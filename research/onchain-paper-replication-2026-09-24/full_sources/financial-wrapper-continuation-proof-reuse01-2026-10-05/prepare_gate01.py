"""Four-definition prospective gate preparation. Never writes CAP or admits anything."""
from pathlib import Path
import json,hashlib,copy,ast
H=Path(__file__).resolve().parent;B=H.parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');NEXT=B/'financial-wrapper-compatible-next-phases-investigation01-2026-10-05';sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def load(p):return json.loads(p.read_bytes())
def save(n,x):
 p=H/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(enc(x))
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
t=load(NEXT/'NEXT_INPUT_HANDOFF01.json');gp=CAP/'fixture_inputs/financial_wrapper_compatibility01/gates.json';oldraw=gp.read_bytes();assert sha(oldraw)=='e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806';g=json.loads(oldraw);assert len(g['experiments'])==13
ref='financial-wrapper-classification-eager-complete100-compatibility-20261004-01';base=g['experiments'][ref];parent=t['next_parent'];grand=g['experiments'][parent]['parent'];assert grand and g['experiments'][grand]['parent'] is None
for i in (parent,grand):assert load(CAP/'research_runs'/i/'claim.json')['experiment']==g['experiments'][i]
newpath='fixture_inputs/financial_wrapper_continuation01';payload={}
for name,v in [('continue-plan.json',t['next_plan']),('predict-plan.json',t['following_plan']),('prior.json',t['wrapper_prior']),('reference.json',t['wrapper_reference'])]:payload[name]=save('inputs/'+name,v)
continuation=copy.deepcopy(base);continuation['parent']=parent;continuation['cells']=[t['next_plan']['cell_id']];continuation['inputs']=copy.deepcopy(t['reuse_base_inputs_except_plan'])
continuation['inputs']['wrapper_plan']={'path':newpath+'/continue-plan.json','sha256':payload['continue-plan.json']['sha256'],'dataset':'synthetic'}
for role,v in {**t['historical_roles'],**t['actual_reference_roles']}.items():continuation['inputs'][role]={k:v[k] for k in ('path','sha256','dataset')}
for role,name in [('wrapper_prior','prior.json'),('wrapper_reference','reference.json')]:continuation['inputs'][role]={'path':newpath+'/'+name,'sha256':payload[name]['sha256'],'dataset':'synthetic'}
assert len(continuation['inputs'])==29
# This is a provisional source map, not the actual later Root commit/map.
continuation['source_files'][str(gp.relative_to(CAP))]=sha(oldraw)
for name,row in payload.items():continuation['source_files'][newpath+'/'+name]=row['sha256']
prediction=copy.deepcopy(continuation);prediction['parent']=t['next_plan']['experiment'];prediction['cells']=[t['following_plan']['cell_id']];prediction['inputs']=copy.deepcopy(t['reuse_base_inputs_except_plan']);prediction['inputs']['wrapper_plan']={'path':newpath+'/predict-plan.json','sha256':payload['predict-plan.json']['sha256'],'dataset':'synthetic'}
# Every unavailable prediction role stays explicit null; selecting this draft
# must fail. Root can replace only after genuine COMPLETE continuation exists.
for role in ('wrapper_prior','continuation_claim','continuation_complete','continuation_checkpoint','continuation_fit_complete','continuation_state'):prediction['inputs'][role]={'path':None,'sha256':None,'dataset':'synthetic'}
assert len(prediction['inputs'])==17
candidate={k:copy.deepcopy(v) for k,v in g.items() if k!='experiments'};candidate['experiments']={parent:copy.deepcopy(g['experiments'][parent]),grand:copy.deepcopy(g['experiments'][grand]),t['next_plan']['experiment']:continuation,t['following_plan']['experiment']:prediction};assert len(candidate['experiments'])==4
for current in (t['next_plan']['experiment'],t['following_plan']['experiment']):
 seen=set();name=current
 while name is not None:
  assert name not in seen and name in candidate['experiments'];seen.add(name);name=candidate['experiments'][name]['parent']
assert candidate['program_id']==g['program_id'] and candidate['families']==g['families'] and candidate['datasets']==g['datasets'];assert len(set(g['experiments'])|set(candidate['experiments']))==15
row=save('GATE4_DRAFT01.json',candidate)
ad=(CAP/'tradingagents/research/admission.py').read_bytes();budget=(CAP/'tradingagents/research/budget_extensions.py').read_bytes();save('GATE_REQUIREMENTS01.json',{'status':'DRAFT_NOT_ADMITTED','original_gate_preserved':{'path':str(gp),'sha256':sha(oldraw),'bytes':len(oldraw)},'prospective_gate_relative_path':newpath+'/gates.json','new_gate_draft':row,'future_current_design_commit':None,'future_exact_source_map':None,'prediction_missing_actual_roles':[k for k,v in prediction['inputs'].items() if v['path'] is None],'continuation_input_roles':29,'prediction_input_roles':17,'file_definition_count':4,'old_definitions_repeated_identically':2,'original_definition_count':13,'globally_distinct_definitions':15,'same_program_family':True,'cumulative_ceiling':20,'spent':4,'new_budget':False,'source_api_pins':{'admission':sha(ad),'budget_extensions':sha(budget)},'guard_locations':{'parent_same_registration':[270,278],'global_claims_mechanism':[316,338],'actual_direct_parent_equality':[339,347]},'implementation_body_changes':0,'required_root_actions':['independent source review','actual100 outcome external and fresh recovery acceptance','genuine current source map including old gate and new source metadata','actual later current/design commit','real phase-specific external Parent/proofs/release','full unchanged8MiB public preclaim']})
print(json.dumps({'gate4_bytes':row['bytes'],'gate4_sha256':row['sha256'],'old_gate_bytes':len(oldraw),'retained_global_identities':15,'only4_file_definitions':True,'unbound_prediction_roles':6}))
