"""Finite read-only metadata/source handoff; never imports project or scientific code."""
from pathlib import Path
import json,hashlib,stat,ast,os,subprocess
H=Path(__file__).resolve().parent;B=H.parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');OLD=B/'financial-wrapper-compatibility-three-consumer-input-investigation01-2026-10-04';ORIGINAL=B/'financial-wrapper-complete100-next-phase-investigation01-2026-10-04';rows={};checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v):
 global checks
 assert v;checks+=1
def raw(p,pin=None):
 p=Path(p);s=p.lstat();ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304);body=p.read_bytes();t=p.lstat();ok((s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns));ok(pin is None or sha(body)==pin);rows[str(p)]={'path':str(p),'sha256':sha(body),'bytes':len(body),'mode':stat.S_IMODE(s.st_mode)};return body
def load(p,pin=None):return json.loads(raw(p,pin))
def emit(name,obj):
 with (H/name).open('x') as f:json.dump(obj,f,sort_keys=True,separators=(',',':'));f.write('\n')
gp=CAP/'fixture_inputs/financial_wrapper_compatibility01/gates.json';g=load(gp,'e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806');ok(len(g['experiments'])==13);identity='financial-wrapper-classification-eager-complete100-compatibility-20261004-01';e=g['experiments'][identity]
templates=load(OLD/'INPUT_BODY_TEMPLATES01.json');roles=load(OLD/'ROLE_MAP01.json');original=load(ORIGINAL/'ORIGINAL_PHASE_TEMPLATES01.json');ok(len(original['slots'])==18)
inputs={k:load(CAP/v['path'],v['sha256']) for k,v in e['inputs'].items()};policy=inputs['operational_source_compatibility'];ok(policy['consumers']=={k:{'experiment':v['experiment'],'cell_id':v['cell_id']} for k,v in templates['plans'].items()});ok(len(inputs['source_closure']['installed'])==195)
accepted=load(B/'financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/MACHINE01.json','27e29cab0b784748bdd0fef2ca484215b39b2b025784a469de443f619ae9b124');ok(accepted['decision']=='ACCEPTED_ACTUAL_SYNTHETIC_ENGINEERING_COMPLETE100' and accepted['epochs']==100 and accepted['actual_engineering_attempts']==4 and accepted['highest_claimed_allowance']==20)
claims=[]
for d in sorted((CAP/'research_runs').iterdir()):
 if not d.is_dir():continue
 c=load(d/'claim.json');status='complete' if (d/'complete.json').exists() else 'failed';t=load(d/(status+'.json'));ok(t['claim_sha256']==rows[str(d/'claim.json')]['sha256'] and t['experiment_id']==c['experiment_id'] and t['status']==status);claims.append(c)
ok(len(claims)==4 and sum((CAP/'research_runs'/c['experiment_id']/'complete.json').exists() for c in claims)==1)
cp=next(c for c in claims if c['experiment_id']==identity);ok(cp['source']==cp['design_source']=='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41' and cp['effective_attempt_budget']==20);ok(rows[str(CAP/'research_runs'/identity/'claim.json')]['sha256']==accepted['actual_claim_sha256'])
fit=CAP/'research_artifacts/onchain_fit_cells'/sha(cp['experiment']['cells'][0].encode())/identity;complete=load(fit/'complete.json');manifestpath=Path(complete['checkpoint']);manifest=load(manifestpath,accepted['actual_checkpoint_sha256']);ok(complete['epochs']==100 and complete['sha256']==sha(raw(manifestpath)));ok(len(manifest['members'])==1)
refroles={}
for role,p in {'reference_claim':CAP/'research_runs'/identity/'claim.json','reference_complete':CAP/'research_runs'/identity/'complete.json','reference_fit_complete':fit/'complete.json','reference_checkpoint':manifestpath}.items():
 raw(p);v=rows[str(p)];refroles[role]={'path':str(p.relative_to(CAP)),'bytes':v['bytes'],'sha256':v['sha256'],'dataset':'synthetic','source':'actual current metadata'}
for name,m in manifest['members'].items():
 ok(Path(name).name==name);p=manifestpath.parent/name;s=p.lstat();ok(stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_size==m['size']);refroles['reference_state']={'path':str(p.relative_to(CAP)),'bytes':m['size'],'sha256':m['sha256'],'dataset':'synthetic','source':'exact manifest and accepted outcome27e29cab; this investigation did not read/decode checkpoint member'}
for role,v in roles['historical_aliases_actual'].items():
 if role=='historical_state':continue
 raw(CAP/v['path'],v['sha256'])
prior=templates['prior_continue100'];ok(prior['parent']==policy['historical']['identity'] and prior['completion_input'] is None and prior['provenance']['source_commit']=='0a2e7639b42b9423b90743feadcda4078aa21816')
reference={'checkpoint_input':'reference_checkpoint','provenance':manifest['provenance'],'completion_input':'reference_fit_complete','claim_input':'reference_claim','terminal_input':'reference_complete'}
for phase in ('continue100','predict'):
 i=policy['consumers'][phase]['experiment'];ok(i not in g['experiments'] and not os.path.lexists(CAP/'research_runs'/i));ok(templates['plans'][phase]['cell_id']=='financial-wrapper-classification-eager-continued-20261003-01')
cellroot=CAP/'research_artifacts/onchain_fit_cells'/sha(templates['plans']['continue100']['cell_id'].encode());ok([p.name for p in cellroot.iterdir()]==[prior['parent']])
extref=e['cumulative_budget_extension'];extension=load(CAP/extref['extension']['path'],extref['extension']['sha256']);review=load(CAP/extref['review']['path'],extref['review']['sha256']);ok(extension['cumulative_ceiling']==20 and extension['consumed_before']==3 and extension['initial_experiment']==identity and review['decision']=='accepted');ok(g['families'][e['family']]['attempt_budget']==18 and g['families'][e['family']]['prior_attempts']==0)
# Inspect genuine metadata API, without creating Admission/Run or evaluating it.
pointers={}
for name,functions in {'financial_wrapper_fixture.py':['_parent','_interrupt_parent','_reference_state','execute','validate_plan'],'operational_source_compatibility.py':['_context','_parent_predicate','require_reference_policy','validate_prediction_parent'],'training.py':['_reserve','fit_cell'],'checkpoints.py':['load_checkpoint']}.items():
 p=CAP/'tradingagents/research/onchain_replication'/name;body=raw(p);tree=ast.parse(body);pointers[name]={'source':rows[str(p)],'functions':{n.name:{'line':n.lineno,'end_line':n.end_lineno} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in functions}}
p=CAP/'tradingagents/research/budget_extensions.py';body=raw(p);pointers['budget_extensions.py']={'source':rows[str(p)],'functions':{'effective_budget':{'line':9,'end_line':78}}}
p=CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01/preclaim01.py';body=raw(p);pointers['preclaim01.py']={'source':rows[str(p)],'functions':{n.name:{'line':n.lineno,'end_line':n.end_lineno} for n in ast.walk(ast.parse(body)) if isinstance(n,ast.FunctionDef) and n.name in ['validate_preclaim','_historical','_complete','_roles','_checkpoint']}}
head=subprocess.run(['git','rev-parse','HEAD'],cwd=CAP,env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL=''),check=True,capture_output=True,timeout=10).stdout.decode().strip();ok(head==cp['source'])
phases=[]
for i,s in enumerate(original['slots'],1):
 p=s['proposed_plan'];state='SATISFIED_PLANNED_FAILED' if i==1 else 'SATISFIED_COMPLETE' if i==2 else 'REQUIRED_PENDING';phases.append({'original_slot':i,'task':p['task'],'execution':p['execution'],'phase':p['phase'],'original_identity':p['experiment'],'coverage':state,'expected_status':s['expected_disposition_if_contract_met']})
ok(sum(x['coverage']=='REQUIRED_PENDING' for x in phases)==16 and 20-len(claims)==16)
emit('NEXT_INPUT_HANDOFF01.json',{'status':'DRAFT_SOURCE_POINTERS_NOT_REGISTRATION_OR_RELEASE','current_source':head,'actual_gate_definitions':13,'gate_after_only_two_dependents':15,'current_gate':rows[str(gp)],'reuse_base_inputs_except_plan':{k:v for k,v in e['inputs'].items() if k!='wrapper_plan'},'job':templates['job_for_all_three'],'next_plan':templates['plans']['continue100'],'next_parent':prior['parent'],'wrapper_prior':prior,'wrapper_reference':reference,'historical_roles':roles['historical_aliases_actual'],'actual_reference_roles':refroles,'continue100_roles':roles['phase_required_roles']['continue100'],'continue100_role_count':29,'following_plan':templates['plans']['predict'],'following_parent':policy['consumers']['continue100']['experiment'],'predict_role_count_if_one_actual_member':17,'prediction_actual_prior_descriptor':None,'prediction_actual_complete_checkpoint_roles':None,'carry_forward_exact_extension_reference':extref,'future_current_design_commit':None,'future_gate_sha256':None,'actual_complete100_external_recovery_proof':None,'future_parent_release':None,'numerical_authority':False})
emit('PHASE_ACCOUNTING01.json',{'original_phases':phases,'required_original_total':18,'satisfied_original_phases':2,'pending_original_phases':16,'closed_claims':4,'COMPLETE':1,'FAILED':3,'unexpected_spent_attempts':2,'base':18,'prior':0,'actual_highest_allowance':20,'remaining_claim_slots':16,'minimum_total_to_cover_original_scope':20,'new_amendment_required_now':False,'if_one_additional_unexpected_attempt_consumed_without_satisfying_phase':'A separate prospective reviewed21 ceiling would become the finite minimum; not automatic or authorized here.','paper_fits_credited':0})
emit('SOURCE_POINTERS01.json',pointers);emit('READBACK01.json',{'checks':checks,'actual_source':head,'metadata_files':len(rows),'metadata_bytes':sum(v['bytes'] for v in rows.values()),'read_set':list(rows.values()),'checkpoint_members_read':False,'project_modules_imported':False,'ledger_or_gate_mutated':False});print(json.dumps({'checks':checks,'files':len(rows),'bytes':sum(v['bytes'] for v in rows.values()),'gate_definitions':13,'pending':16,'allowance_remaining':16}))
