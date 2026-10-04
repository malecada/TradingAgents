import ast,atexit,copy,hashlib,json,os,stat,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P='tradingagents/research/onchain_replication/';checks=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(n,x):(H/n).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 assert v,n
atexit.register(lambda:save('CHECKS_PROGRESS01.json',checks))
(H/'raw_metadata').mkdir();(H/'source').mkdir()
def raw(path):
 st=path.lstat();ck('canonical bounded regular '+str(path),stat.S_ISREG(st.st_mode) and path.resolve()==path and st.st_size<=4194304);b=path.read_bytes();ck('stable extent '+str(path),len(b)==st.st_size);return b
sources={};asts={}
for rel in [P+n for n in ('financial_wrapper_fixture.py','operational_source_compatibility.py','training.py','workflow_storage.py','job.py','evaluation.py','checkpoints.py','cache.py')]+['tradingagents/research/'+n for n in ('lifecycle.py','admission.py','verify.py')]:
 b=raw(S/rel);sources[rel]={'sha256':sha(b),'bytes':len(b)};(H/'source'/Path(rel).name).write_bytes(b);asts[Path(rel).name]=ast.parse(b)
commit=subprocess.run(['git','-C',str(S),'rev-parse','HEAD'],capture_output=True,check=True,timeout=10).stdout.decode().strip();ck('actual adopted source7b056',commit=='7b056a574e3e7b3c7ba209a39ee6a615e649d60c')
constants={}
for n in asts['operational_source_compatibility.py'].body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('OLD_MAP','CONTROL_TARGETS','HISTORICAL_ID','HISTORICAL_SOURCE','HISTORICAL_CLAIM_SHA256','HISTORICAL_FAILED_SHA256','HISTORICAL_CHECKPOINT_SHA256','HISTORICAL_STATE_SHA256'):constants[n.targets[0].id]=ast.literal_eval(n.value)
oldmap=constants['OLD_MAP'];newmap=oldmap|constants['CONTROL_TARGETS']|{P+'operational_source_compatibility.py':sources[P+'operational_source_compatibility.py']['sha256']}
for rel,pin in newmap.items():ck('actual195 source '+rel,sha(raw(S/rel))==pin)
ck('old194/193 new195/194 and191unchanged',len(oldmap)==194 and len(set(oldmap.values()))==193 and len(newmap)==195 and len(set(newmap.values()))==194 and sum(newmap[p]==v for p,v in oldmap.items())==191)
identity=constants['HISTORICAL_ID'];claimpath=S/'research_runs'/identity/'claim.json';claimraw=raw(claimpath);claim=json.loads(claimraw);ck('actual oldclaim/source fixed',sha(claimraw)==constants['HISTORICAL_CLAIM_SHA256'] and claim['source']==claim['design_source']==constants['HISTORICAL_SOURCE']);failedpath=claimpath.with_name('failed.json');failedraw=raw(failedpath);ck('actual oldfailed fixed',sha(failedraw)==constants['HISTORICAL_FAILED_SHA256'])
base={};bodies={}
for role,info in claim['inputs'].items():
 b=raw(S/info['path']);ck('exact historical input '+role,sha(b)==info['sha256']);base[role]=dict(info,bytes=len(b));bodies[role]=json.loads(b);(H/'raw_metadata'/('historical_'+role+'.json')).write_bytes(b)
oldplan=bodies['wrapper_plan'];oldjob=bodies['execution_job'];ck('actual job-selected original plan',oldjob['payload']['plan_input']=='wrapper_plan' and oldplan['experiment']==identity and oldplan['phase']=='interrupt1')
fit=S/'research_artifacts/onchain_fit_cells'/sha(oldplan['cell_id'].encode())/identity;diagnosticpath=S/'research_artifacts/financial_wrapper_engineering'/oldplan['namespace']/'interrupted-checkpoint.json';diagnostic=json.loads(raw(diagnosticpath));cp=Path(diagnostic['checkpoint']);cpraw=raw(cp);manifest=json.loads(cpraw);ck('actual oldcheckpoint hash/provenance',sha(cpraw)==constants['HISTORICAL_CHECKPOINT_SHA256'] and diagnostic['sha256']==sha(cpraw) and diagnostic['provenance']==manifest['provenance'] and manifest['provenance']['source_commit']==constants['HISTORICAL_SOURCE'])
roles={}
def known(role,p,copy_json=True):
 b=raw(p);roles[role]={'dataset':'synthetic','path':str(p.relative_to(S)),'bytes':len(b),'sha256':sha(b),'available':True}
 if copy_json:(H/'raw_metadata'/(role+'.json')).write_bytes(b)
known('historical_claim',claimpath);known('historical_failed',failedpath)
for role,oldrole in [('historical_execution_job','execution_job'),('historical_wrapper_plan','wrapper_plan'),('historical_source_closure','source_closure')]:known(role,S/base[oldrole]['path'])
known('historical_checkpoint',cp);known('historical_fit_claim',fit/'claim.json');known('historical_fit_failed',fit/'failed.json');known('historical_diagnostic',diagnosticpath);known('historical_schedule',fit/'schedule.json')
for name,item in manifest['members'].items():
 ck('strict checkpoint member name',Path(name).name==name and name not in ('.','..'));role='historical_state' if name=='state.pt' else 'historical_member_'+sha(name.encode())[:16];known(role,cp.parent/name,False);ck('actual opaque state hash/size '+name,roles[role]['sha256']==item['sha256'] and roles[role]['bytes']==item['size'])
ck('one actual original state member',len(manifest['members'])==1 and roles['historical_state']['bytes']==493424 and roles['historical_state']['sha256']==constants['HISTORICAL_STATE_SHA256'])
ck('sole old failed fit',sorted(p.name for p in fit.parent.iterdir())==[identity] and (fit/'failed.json').is_file() and not (fit/'complete.json').exists())
charterpath=S/claim['experiment']['charter']['path'];charterraw=raw(charterpath);ck('actual original charter hash',sha(charterraw)==claim['experiment']['charter']['sha256']);charter=json.loads(charterraw);(H/'raw_metadata/original_charter.json').write_bytes(charterraw)
gatepath=S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json';gateraw=raw(gatepath);gate=json.loads(gateraw);(H/'raw_metadata/original_gate12.json').write_bytes(gateraw);ck('actual original12 registrations retained',len(gate['experiments'])==12)
ids={'complete100':'financial-wrapper-classification-eager-complete100-compatibility-20261004-01','continue100':'financial-wrapper-classification-eager-continue100-compatibility-20261004-01','predict':'financial-wrapper-classification-eager-predict-compatibility-20261004-01'}
cells={'complete100':'financial-wrapper-classification-eager-reference-compatibility-20261004-01','continue100':'financial-wrapper-classification-eager-continued-20261003-01','predict':'financial-wrapper-classification-eager-continued-20261003-01'}
for phase,i in ids.items():ck('fixed new identity unregistered/claim absent '+phase,i not in gate['experiments'] and not os.path.lexists(S/'research_runs'/i) and not os.path.lexists(S/'research_artifacts/financial_wrapper_engineering'/i))
ck('new reference fit cell absent',not os.path.lexists(S/'research_artifacts/onchain_fit_cells'/sha(cells['complete100'].encode())))
# Execute only the actual pure schema functions extracted from the source AST.
fixture=asts['financial_wrapper_fixture.py'];scope={'Path':Path,'json':json,'hashlib':hashlib}
keep=[n for n in fixture.body if isinstance(n,ast.ClassDef) and n.name=='Unavailable' or isinstance(n,ast.FunctionDef) and n.name in ('require','validate_plan','schema') or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('PHASES','FILE','GIB') for t in n.targets)]
exec(compile(ast.Module(body=keep,type_ignores=[]),'actual-pure-wrapper-schema','exec'),scope)
plans={}
for phase,i in ids.items():
 plan=copy.deepcopy(oldplan);plan.update(experiment=i,namespace=i,cell_id=cells[phase],phase=phase,prior_input=None if phase=='complete100' else 'wrapper_prior',reference_input='wrapper_reference' if phase=='continue100' else None);scope['validate_plan'](plan);plans[phase]=plan;ck('exact extracted plan schema '+phase,True)
scope['schema'](oldjob);ck('unchanged current-root job schema',True)
# These are source-only input body templates, not a gate or policy/proof.
prior_continue={'parent':identity,'claim_input':'historical_claim','terminal_input':'historical_failed','checkpoint_input':'historical_checkpoint','completion_input':None,'provenance':manifest['provenance'],'parent_job_input':'historical_execution_job','parent_plan_input':'historical_wrapper_plan','fit_claim_input':'historical_fit_claim','failed_fit_input':'historical_fit_failed','diagnostic_input':'historical_diagnostic','schedule_input':'historical_schedule'}
reference={'checkpoint_input':'reference_checkpoint','provenance':None,'completion_input':'reference_fit_complete','claim_input':'reference_claim','terminal_input':'reference_complete'}
prior_predict={'parent':ids['continue100'],'claim_input':'continuation_claim','terminal_input':'continuation_complete','checkpoint_input':'continuation_checkpoint','completion_input':'continuation_fit_complete','provenance':None}
parents={'complete100':None,'continue100':identity,'predict':ids['continue100']}
base_roles=list(base)+['operational_source_compatibility','operational_source_compatibility_review','operational_source_compatibility_recovery']
required={'complete100':base_roles,'continue100':base_roles+list(roles)+['wrapper_prior','wrapper_reference','reference_claim','reference_complete','reference_checkpoint','reference_fit_complete','reference_state'],'predict':base_roles+['wrapper_prior','continuation_claim','continuation_complete','continuation_checkpoint','continuation_fit_complete','continuation_state']}
ck('minimum roles11/29/17',list(map(lambda p:len(required[p]),('complete100','continue100','predict')))==[11,29,17])
for p,rs in required.items():ck('role uniqueness '+p,len(rs)==len(set(rs)))
future={role:{'path':None,'sha256':None,'bytes':None,'available':False,'required_actual_origin':'future independently accepted COMPLETE '+('reference' if role.startswith('reference_') else 'continuation')} for role in set(required['continue100']+required['predict']) if role.startswith(('reference_','continuation_'))}
# Pure preclaim presence/shape refusal. It does not implement runtime authority.
def missing(phase,registry):
 return sorted(role for role in required[phase] if role not in registry or not isinstance(registry[role],dict) or not isinstance(registry[role].get('path'),str) or not isinstance(registry[role].get('sha256'),str) or len(registry[role]['sha256'])!=64)
for phase in ids:ck('unfilled concrete role map refuses '+phase,bool(missing(phase,roles)))
# Authenticate all original phase records as retained metadata, without claiming coverage.
phases=charter['phases'];ck('full original18 phase denominator',len(phases)==18)
line_map={}
for name,tree in asts.items():
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in ('start','_admitted','admitted','_parent','_interrupt_parent','_reference_state','_reserve','_context','_parent_predicate','require_prediction_policy','validate_prediction_parent','require_reference_policy','recover_completed_model','provenance','runtime_check','_one_epoch_state'):
   line_map[name+':'+n.name]={'line':n.lineno,'end_line':n.end_lineno,'sha256':sources[next(k for k in sources if Path(k).name==name)]['sha256']}
source_readback={'actual_source':commit,'source_pins':sources,'old_map':oldmap,'current_map':newmap,'source_functions':line_map,'old_claim_sha256':sha(claimraw),'old_failed_sha256':sha(failedraw),'original_gate_sha256':sha(gateraw),'original_gate_ids':list(gate['experiments']),'original_charter_sha256':sha(charterraw),'original18_phases':phases,'old_plan':oldplan,'old_job':oldjob}
save('SOURCE_READBACK01.json',source_readback)
save('ROLE_MAP01.json',{'qualification':'prospective role names only; no input registration performed','base8_actual_historical_bodies':base,'historical_aliases_actual':roles,'policy_historical_alias_fields':{'closure_input':'historical_source_closure','claim_input':'historical_claim','failed_input':'historical_failed','checkpoint_input':'historical_checkpoint','plan_input':'historical_wrapper_plan','job_input':'historical_execution_job'},'phase_required_roles':required,'future_completed_roles':future,'minimum_counts':{p:len(rs) for p,rs in required.items()},'member_count_qualification':'29 and17 assume future real manifests each have exactly one state member; Root must add every actual member and recalculate if not. Historical member count1 is actual.', 'historical_completion_input':None,'historical_completion_unavailable_reason':'Planned interruption is genuinely FAILED; no completion body exists or may be fabricated.'})
save('INPUT_BODY_TEMPLATES01.json',{'status':'DRAFT_NOT_REGISTERED_NOT_RELEASED','job_for_all_three':oldjob,'job_bytes_may_be_reused':base['execution_job'],'plans':plans,'registered_parent_requirements':parents,'prior_continue100':prior_continue,'reference_for_continue100':reference,'prior_predict':prior_predict,'future_input_paths':None,'actual_gate':None,'actual_policy_or_proofs':None,'actual_registration':None,'numerical_release':None})
save('MACHINE_BASE01.json',{'status':'EXACT_SOURCE_METADATA_HANDOFF_NOT_ADMISSION','source':commit,'checks':len(checks),'old_parent':identity,'old_checkpoint':roles['historical_checkpoint'],'opaque_state':roles['historical_state'],'no_state_deserialization':True,'fixed_future_ids':ids,'fixed_future_cells':cells,'genuine_parent_topology':parents,'original18phases':18,'old_gate_entries':12,'new_gate_entries_if_all_three_added_and_all_old_retained':15,'old_gate_stale_for_new_source':True,'current_source_body_adoption_only':True,'existing_family_highest':19,'actual_spent_failed':3,'existing_remaining':16,'original_requirements_remaining':17,'prospective20_adopted_here':False,'checkpoint_numerical_cursor_unverified':True})
print(json.dumps({'status':'PASS_METADATA_INVESTIGATION','checks':len(checks),'roles':{p:len(rs) for p,rs in required.items()}}))
