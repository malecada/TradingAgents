"""Write prospective templates only. No registration, claims, imports or launch."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];BASE=P.parent
ORIGIN=BASE/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03/source-bodies'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(P/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
source={}
# Conservative frozen source composition: source references, not an installed tree.
for p in sorted(ORIGIN.rglob('*')):
 if p.is_file() and not p.is_symlink() and p.suffix=='.py':source[str(p.relative_to(ORIGIN))]={'source':str(p.relative_to(ROOT)),'sha256':sha(p)}
for p in sorted((P/'candidate02').glob('*.py')):source['tradingagents/research/onchain_replication/'+p.name]={'source':str(p.relative_to(ROOT)),'sha256':sha(p)}
for n in ('job.py','replay.py','financial_wrapper_fixture.py'):
 p=P/n;source['tradingagents/research/onchain_replication/'+n]={'source':str(p.relative_to(ROOT)),'sha256':sha(p)}
put('SOURCE_CLOSURE01.json',{'schema_version':1,'installed':{n:r['sha256'] for n,r in source.items()},'scientific_model':sha(P/'model.json'),'scientific_training':sha(P/'training.json'),'candidate02':sha(P/'candidate02/financial_execution.py')})
put('INSTALLATION01.json',{'schema_version':1,'status':'uninstalled; independent source review required','sources':source,'genuine_installed_commit':None,'genuine_installed_capsule':None,'source_review':None})
recipe={'schema_version':1,'kind':'opaque-sha256-synthetic-16x28-distinct-v1','seed':11,'batch':16,'lookback':28,'nodes':4,'mcm_width':32,'empirical_inputs':False,'fitted_dictionary':False};put('RECIPE01.json',recipe)
resource={'memory_max_bytes':3*1024**3,'memory_high_bytes':3*1024**3,'reserve_bytes':3*1024**3,'start_reserve_bytes':6*1024**3,'disk_floor_bytes':10*1024**3,'disk_paths':None,'wall_seconds':1800,'native_unit_limits':{'file_size_bytes':4*1024**2},'storage_budget':{'root':None,'limits':{'max_allocated_bytes':1024**3,'max_logical_bytes':1024**3,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}}
put('JOB_TEMPLATE01.json',{'schema_version':1,'kind':'financial_wrapper','resources':resource,'environment_input':'environment','payload':{'plan_input':'wrapper_plan'}})
plans=[]
for task in ('classification','regression'):
 for backend in ('eager','selected'):
  for phase in ('agreement','interrupt1','complete100','continue100','predict'):
   if phase=='agreement' and backend=='eager':continue
   plans.append({'schema_version':1,'kind':'genuine-financial-wrapper-synthetic-v1','phase':phase,'experiment':None,'cell_id':None,'task':task,'execution':backend,'model_input':'model','training_input':'training','recipe_input':'synthetic_recipe','closure_input':'source_closure','runtime_input':'runtime_mapping','prior_input':'prior' if phase in ('continue100','predict') else None,'reference_input':'uninterrupted_reference' if phase=='continue100' else None,'namespace':None})
put('PHASE_TEMPLATES01.json',{'templates':plans,'accounting':'18 prospective phase/task/backend slots; no identities reserved, allowance inferred or executions performed','coordinator_required':{'new_program':None,'family':None,'independently_reviewed_cumulative_budget':None,'ancestry_layout':None,'source':None,'design_source':None}})
put('PRIOR_TEMPLATE01.json',{'parent':None,'claim_input':None,'terminal_input':None,'checkpoint_input':None,'completion_input':None,'provenance':None})
put('REFERENCE_TEMPLATE01.json',{'claim_input':None,'terminal_input':None,'checkpoint_input':None,'completion_input':None,'provenance':None})
put('RUNTIME_TEMPLATE01.json',{'python':'3.13.13','executable':None,'resolved_executable':None,'prefix':None,'executable_sha256':None,'lock_sha256':None,'distribution_records':None})
inputs={}
for name,file in [('model','model.json'),('training','training.json'),('synthetic_recipe','RECIPE01.json'),('source_closure','SOURCE_CLOSURE01.json')]:inputs[name]={'path':None,'sha256':sha(P/file),'dataset':None}
for name in ('execution_job','wrapper_plan','environment','runtime_mapping'):inputs[name]={'path':None,'sha256':None,'dataset':None}
put('INPUT_TEMPLATE01.json',{'inputs':inputs,'prior_artifact_members':'Each genuine prior checkpoint manifest AND every state.pt body, claim, terminal, fit completion and schedule must have independently authenticated registered input paths/hashes. No generated placeholder may satisfy ancestry.'})
put('REGISTRATION_TEMPLATE01.json',{'schema_version':1,'program_id':None,'datasets':None,'families':None,'experiments':None,'experiment_shape':{'cells':None,'charter':{'path':None,'sha256':None},'family':None,'inputs':inputs,'outputs':['cell-ledger.json','wrapper-summary.json','artifact-index.json'],'parent':None,'question':'Finite genuine synthetic financial wrapper verification; no empirical data, paper fit or capacity claim','reuse':None,'runtime_hashes':None,'selection':None,'source_files':None,'stage':'development','windows':None},'not_admissible':True})
# Full conditional inverse; no equations or scientific config are rewritten.
inverses={};adapt=json.loads((P/'adaptations.json').read_bytes())
for n,steps in adapt.items():
 s=(P/n).read_text()
 for x in reversed(steps):
  assert s.count(x['after'])==x.get('count',1),(n,x['after']);s=s.replace(x['after'],x['before'])
 original=P/'job.baseline.py' if n=='job.py' else P/'candidate02/replay.py';assert s==original.read_text();inverses[n]={'inverse_sha256':sha(original),'new_sha256':sha(P/n),'complete_original_recovered':True}
for p in (P/'candidate02').glob('*.py'):assert p.read_bytes()==(BASE/'financial-streamed-execution-candidate02-2026-10-02'/p.name).read_bytes()
put('INVERSE01.json',{'adaptations':inverses,'candidate02_seven_modules_exact':True,'candidate02_financial_sha256':sha(P/'candidate02/financial_execution.py'),'scientific_model_sha256':sha(P/'model.json'),'scientific_training_sha256':sha(P/'training.json'),'model_equations_modified':False})
print(json.dumps({'source_targets':len(source),'phase_slots':len(plans),'inverse':True}))
