"""Narrow reproducible source substitutions; no installation or execution."""
from pathlib import Path
import json,difflib
P=Path(__file__).resolve().parent;OLD=P.parent/'financial-genuine-wrapper-preparation01-2026-10-03';original=(OLD/'financial_wrapper_fixture.py').read_text();s=original;changes=[]
def replace(a,b):
 global s
 assert s.count(a)==1,(a[:80],s.count(a));s=s.replace(a,b);changes.append({'before':a,'after':b})
replace(" value=json.loads(run.read_input(p['prior_input']));require(set(value)=={'parent','claim_input','terminal_input','checkpoint_input','completion_input','provenance'},'exact genuine prior descriptor required')", " value=json.loads(run.read_input(p['prior_input']));fields={'parent','claim_input','terminal_input','checkpoint_input','completion_input','provenance'}\n if p['phase']=='continue100':fields|={'parent_job_input','parent_plan_input','fit_claim_input','failed_fit_input','diagnostic_input','schedule_input'}\n require(set(value)==fields,'exact genuine prior descriptor required')")
replace(" return value,checkpoint\n\ndef replay_package", " if p['phase']=='continue100':_interrupt_parent(run,p,prov,value,checkpoint,claim)\n return value,checkpoint\n\ndef replay_package")
helpers='''def _select_failure(first,later):
 """First actual fatal wins, including failures of diagnostic construction."""
 fatal=lambda e:not isinstance(e,Exception) or isinstance(e,MemoryError)
 return first if fatal(first) or not fatal(later) else later

def _interrupt_case(current,parent_plan,parent):
 validate_plan(parent_plan)
 require(parent_plan['experiment']==parent and parent_plan['phase']=='interrupt1','continuation parent must be the actual admitted interrupt1 phase')
 require(all(parent_plan[k]==current[k] for k in ('cell_id','task','execution')),'interrupt1 task/backend/cell differs')

def _one_epoch_state(state):
 import math
 require(type(state)is dict and type(state.get('epoch'))is int and state['epoch']==1 and type(state.get('batch'))is int and state['batch']==0,'continuation actual loaded cursor must be epoch1/batch0')
 require(type(state.get('epoch_count'))is int and state['epoch_count']==0 and type(state.get('epoch_loss'))in (int,float) and state['epoch_loss']==0,'continuation epoch accumulators differ')
 logs=state.get('logs');require(type(logs)is list and len(logs)==1 and type(logs[0])is dict and set(logs[0])=={'epoch','loss','examples','seed'},'one completed original epoch log required')
 row=logs[0];require(all(type(row[k])is int and row[k]==v for k,v in {'epoch':0,'examples':16,'seed':11}.items()) and type(row['loss'])in (int,float) and math.isfinite(row['loss']),'original one-epoch log differs')

def _interrupt_parent(run,p,prov,value,checkpoint,claim):
 """Authenticate original claim-selected plan and immutable failed-fit evidence."""
 def registered(name,expected,claim_info=None):
  raw=run.read_input(name);info=run.admission.inputs[name];path=run.admission.root/info['path']
  require(path.resolve()==expected.resolve() and path.resolve()==path and raw==expected.read_bytes(),'registered interrupt1 evidence origin differs')
  if claim_info is not None:require(info['path']==claim_info['path'] and info['sha256']==claim_info['sha256']==sha(raw),'parent claim input differs')
  return json.loads(raw)
 parent=value['parent'];inputs=claim['inputs'];job_info=inputs['execution_job'];job=registered(value['parent_job_input'],run.admission.root/job_info['path'],job_info)
 schema(job);plan_info=inputs[job['payload']['plan_input']];old=registered(value['parent_plan_input'],run.admission.root/plan_info['path'],plan_info);_interrupt_case(p,old,parent)
 require(claim['experiment']['cells']==[p['cell_id']],'parent admitted cell differs')
 for key,pin in (('model_input',MODEL),('training_input',TRAINING),('recipe_input',prov['input_hash'])):
  require(inputs[old[key]]['sha256']==pin,'parent original science/recipe input differs')
 fit=run.admission.root/'research_artifacts/onchain_fit_cells'/sha(p['cell_id'].encode())/parent
 require(checkpoint.resolve().is_relative_to((fit/'checkpoints').resolve()) and not (fit/'complete.json').exists(),'interrupt1 checkpoint must belong to failed fit')
 fitclaim=registered(value['fit_claim_input'],fit/'claim.json')
 require(fitclaim=={'experiment_id':parent,'provenance':value['provenance'],'parent_checkpoint':None},'fresh interrupt1 fit claim differs')
 failed=registered(value['failed_fit_input'],fit/'failed.json')
 require(failed=={'type':'PlannedInterruption','reason':'prospective engineering failed-parent fixture after one real update; no fit completion','last_checkpoint':str(checkpoint)},'actual interrupt1 failed-fit terminal differs')
 diagnostic=registered(value['diagnostic_input'],run.admission.root/'research_artifacts/financial_wrapper_engineering'/old['namespace']/'interrupted-checkpoint.json')
 require(diagnostic=={'checkpoint':str(checkpoint),'sha256':sha(checkpoint.read_bytes()),'provenance':value['provenance'],'epochs_completed':1,'requires_genuine_failed_parent':True},'actual interrupt1 diagnostic checkpoint join differs')
 schedule=registered(value['schedule_input'],fit/'schedule.json')
 expected={'training':json.loads(run.read_input(p['training_input'])),'seed':11,'task':p['task'],'n_examples':16}
 require(canonical(schedule)==canonical(expected),'actual registered interrupt1 schedule differs')

'''
replace('def replay_package(torch,',helpers+'def replay_package(torch,')
# Move existing authentic reference validation/loading before original fit_cell.
a=s.index("     from ..verify import verify_claim\n     ref=json.loads(run.read_input(p['reference_input']))")
b=s.index("     current=factory();",a)
reference_block=s[a:b]
reference_helper="def _reference_state(run,p,prov,factory,t,checkpoints,torch):\n from .provenance import file_hash\n"+''.join(line[4:]+'\n' for line in reference_block.splitlines())+" return state\n\n"
replace('def execute(run,args,plan_input):',reference_helper+'def execute(run,args,plan_input):')
replace("     prior,cp=_parent(run,p,prov);continuation={'checkpoint':str(cp),'provenance':prior['provenance']}","     prior,cp=_parent(run,p,prov)\n     # Decode through the genuine loader before reserving or running continuation.\n     probe=factory();probe_optimizer=optimizer(torch,probe,t);probe_rng=checkpoints.seed_all(11)\n     loaded=checkpoints.load_checkpoint(cp,probe,probe_optimizer,probe_rng,prior['provenance']);_one_epoch_state(loaded)\n     del probe,probe_optimizer,probe_rng,loaded\n     reference_state=_reference_state(run,p,prov,factory,t,checkpoints,torch)\n     continuation={'checkpoint':str(cp),'provenance':prior['provenance']}")
replace(reference_block,"     state=reference_state\n")
old="""  try:_immutable(directory/'failure.json',{'type':type(error).__name__,'reason':str(error),'success':False,'retry':False})
  except BaseException as later:
   error.add_note('failure evidence publication unresolved: '+repr(later))
   if not isinstance(later,Exception) or isinstance(later,MemoryError):raise later from error
  raise
"""
new="""  selected=error
  try:_immutable(directory/'failure.json',{'type':type(error).__name__,'reason':str(error),'success':False,'retry':False})
  except BaseException as later:
   selected=_select_failure(selected,later)
   try:selected.add_note('failure evidence publication unresolved: '+repr(later))
   except BaseException as diagnostic:selected=_select_failure(selected,diagnostic)
  if selected is not error:raise selected from error
  raise
"""
replace(old,new)
(P/'financial_wrapper_fixture.py').write_text(s);(P/'fixture_adaptations02.json').write_text(json.dumps(changes,indent=2)+'\n');(P/'financial_wrapper_fixture.py.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='preserved01/financial_wrapper_fixture.py',tofile='successor02/financial_wrapper_fixture.py')))
