"""Bounded independent budget/source/opaque metadata review, no admission."""
import ast,copy,hashlib,json,os,re,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-wrapper-cumulative20-preparation01-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,name):
 if not v:raise AssertionError(name)
 checks.append(name)
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_size<=4194304 and p.resolve()==p,'bounded canonical '+str(p));raw=p.read_bytes();t=p.lstat();ck((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns),'stable '+str(p));return raw
def put(n,v):(H/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
ck(sys.version_info[:3]==(3,13,13),'pinned runtime')
ext_raw=read(A/'extension20.DRAFT.json');alloc_raw=read(A/'allocation20.DRAFT.json');ck(sha(ext_raw)=='07100b23f9a8c2dfcae98a8647f9f1eeb019f4093192cd4b2576c6a13bf9840e','exact extension draft');ck(sha(alloc_raw)=='461df69895a0a5e70b23882c759790a4c000eb33d1662629cacd322b7d3b0116','exact allocation draft');extension=json.loads(ext_raw);allocation=json.loads(alloc_raw)
for name in ('extension20.DRAFT.json','allocation20.DRAFT.json','PREPARATION01.json','ORIGINAL_PHASES18_CURRENT01.json'):(H/name).write_bytes(read(A/name))
graw=read(S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json');ck(sha(graw)=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c','actual gate unchanged');gate=json.loads(graw);(H/'GATE_ORIGINAL01.json').write_bytes(graw);family=gate['families']['synthetic-financial-wrapper'];ck(family==extension['base_family'] and family['attempt_budget']==18 and family['prior_attempts']==0 and family['mechanism_id']=='synthetic-full-financial-wrapper-v1','same base family18 prior0')
claims=[];actual_rows=[]
for p in sorted((S/'research_runs').glob('*/claim.json')):
 raw=read(p);c=json.loads(raw);terminal=read(p.parent/'failed.json');f=json.loads(terminal)
 ck(c['family']==family and c['program_id']==extension['program_id']==gate['program_id'],'all same exact family/program');ck(f['status']=='failed' and f['experiment_id']==c['experiment_id'] and f['claim_sha256']==sha(raw),'genuine failed join');ck(not (p.parent/'complete.json').exists(),'no complete terminal');ck(c['experiment']==gate['experiments'][c['experiment_id']],'parent definitions preserved');ck(not list((p.parent/'outputs').glob('*.json')),'no registered completed outputs')
 claims.append(c);actual_rows.append({'experiment':c['experiment_id'],'claim_sha256':sha(raw),'terminal_status':'failed','terminal_sha256':sha(terminal)});q=H/'actual-claims'/c['experiment_id'];q.mkdir(parents=True);(q/'claim.json').write_bytes(raw);(q/'failed.json').write_bytes(terminal)
ck(actual_rows==extension['claims']==allocation['claims'] and len(claims)==3,'complete three-claim snapshot');ck(max(c['effective_attempt_budget'] for c in claims)==19,'actual highest19');ck(extension['consumed_before']==3,'spent3')
for r in allocation['original_mapping']:
 original=read(Path(r['original_path']));retained=read(A/r['retained_path']);ck(original==retained and sha(original)==r['sha256'] and len(original)==r['bytes'],'all six original body copies exact')
# Reconstruct DAG from actual charter pinned in the original reference registration.
refid='financial-wrapper-classification-eager-complete100-20261003-01';refexp=gate['experiments'][refid];desc=refexp['charter'];charraw=read(S/desc['path']);ck(sha(charraw)==desc['sha256']=='041ab6260eeb81805202ba31c4ba1710b3109bbd0b24131e83a5c4f05984cbb1','authentic original charter');charter=json.loads(charraw);(H/'CHARTER_ORIGINAL01.json').write_bytes(charraw);phases=charter['phases'];ck(len(phases)==18 and [p['slot_index'] for p in phases]==list(range(1,19)),'full18 denominator');bykey={p['logical_key_not_identity']:p for p in phases};ck(len(bykey)==18,'unique phase keys')
for p in phases:
 ck(p['original_schedule_epochs']==100 and p['paper_fit_credit']==0,'original phase science/credit')
 for dep in p['dependencies']:ck(dep in bykey and bykey[dep]['slot_index']<p['slot_index'],'acyclic original dependency')
ck(sum(p['expected_lifecycle_status']=='COMPLETE' for p in phases)==14,'14 complete phase contracts');ck(sum(p['expected_lifecycle_status']=='FAILED' for p in phases)==4,'4 planned failed contracts');ck(sum(p['phase'] in ('complete100','continue100') for p in phases)==8,'8 required full fits');ck(sum(p['training_fit_cell_calls'] for p in phases)==12,'12 fit invocations');ck(sum(p['optimizer_updates_if_successful'] for p in phases)==804,'800 training plus4 agreement updates')
ck([r['original_slot'] for r in allocation['pending_original_phase_mapping']]==list(range(2,19)),'exact17pending slots')
for row,p in zip(allocation['pending_original_phase_mapping'],phases[1:],strict=True):ck(row['original_identity']==p['proposed_identity'] and row['logical_key']==p['logical_key_not_identity'] and row['phase']==p['phase'] and row['actual_fulfilled'] is False and row['release'] is None,'pending mapping original contract')
# Authenticate deliberate failed interruption from actual primitive metadata, never state decoding.
parent='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01';cpinfo=json.loads(read(B/'financial-wrapper-complete100-next-phase-investigation01-2026-10-04/PARENT_INPUT_REQUIREMENTS01.json'));parentmeta={}
for row in cpinfo['rows']:
 raw=read(S/row['path']);ck(sha(raw)==row['sha256'] and len(raw)==row['bytes'],'old interruption evidence')
 if not row['descriptor_field'].startswith('checkpoint_member:'):parentmeta[row['descriptor_field']]=json.loads(raw)
ck(parentmeta['diagnostic_input']['epochs_completed']==1 and parentmeta['diagnostic_input']['requires_genuine_failed_parent'] is True,'one epoch diagnostic');ck(parentmeta['failed_fit_input']['type']=='PlannedInterruption' and parentmeta['fit_claim_input']['parent_checkpoint'] is None,'fresh intentional failed interruption');ck(parentmeta['parent_plan_input']['phase']=='interrupt1' and parentmeta['parent_plan_input']['cell_id']==phases[0]['proposed_cell'],'slot1 actual phase mapping')
# Full100 failed fit is a separate cell, with durable epoch metadata but no full result.
refcell=phases[1]['proposed_cell'];fit=S/'research_artifacts/onchain_fit_cells'/sha(refcell.encode())/refid
ck(fit.is_dir() and (fit/'failed.json').is_file() and not (fit/'complete.json').exists(),'no reference completion');epochs=sorted(fit.glob('epoch-*.json'));ck(len(epochs)==29,'29 partial epochs')
for i,p in enumerate(epochs):v=json.loads(read(p));ck(v['epoch']==i and v['examples']==16 and v['seed']==11,'actual epoch journal identity')
ck(allocation['fulfilled_original_phases']==1 and allocation['remaining_original_phases']==17,'one phase fulfilled17remain');ck(19-3==16 and 20-3==17 and extension['cumulative_ceiling']==20,'minimal cumulative20 arithmetic')
# Proposed adopter and associated actual namespaces absent; this is no admission.
initial=extension['initial_experiment'];ck(initial==allocation['one_fixed_prospective_adopter']=='financial-wrapper-classification-eager-complete100-compatibility-20261004-01','fixed initial identity');ck(initial not in gate['experiments'],'no actual gate entry')
absences=[S/'research_runs'/initial,S/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/initial,S/'research_artifacts/financial_wrapper_engineering'/initial,fit.parent/initial]
for p in absences:ck(not os.path.lexists(p),'unused namespace '+str(p))
for k in ('actual_new_policy','actual_new_registration','actual_new_source','actual_recovery_review','actual_release'):ck(allocation[k] is None,'no fabricated actual prerequisite '+k)
# Authenticate and execute genuine original stdlib budget validator only for EXISTING19.
bsrc=read(S/'tradingagents/research/budget_extensions.py');closure=json.loads(read(S/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json'));ck(sha(bsrc)==closure['installed']['tradingagents/research/budget_extensions.py'],'budget source pin');(H/'budget_extensions_original.py').write_bytes(bsrc);env={};exec(compile(bsrc,'actual-budget-extensions','exec'),env)
def read_actual_bound(ref):
 ck(type(ref)is dict and set(ref)=={'path','sha256'},'actual bounded descriptor');raw=read(S/ref['path']);ck(sha(raw)==ref['sha256'],'actual bound metadata hash');return raw
actual=env['effective_budget'](S,gate['program_id'],refid,refexp,family,claims,read_actual_bound);ck(actual==19,'full authentic existing-ceiling validator19')
# Proposed20: execute only source schema/allocation and snapshot fragments.
# Deliberately do not construct an accepted review or run prospective admission.
t=ast.parse(bsrc);f=next(n for n in t.body if isinstance(n,ast.FunctionDef));schema_nodes=[n for n in f.body if 21<=n.lineno<=37];snapshot_nodes=[n for n in f.body if 44<=n.lineno<=68];first_adopter=next(n.test for n in ast.walk(f) if isinstance(n,ast.If) and n.lineno==71)
def validate_parts(experiment_id,ext,relevant):
 local={'extension':ext,'family':family,'program':gate['program_id'],'base':18,'previous':19,'root':S,'relevant':relevant,'experiment_id':experiment_id,'read_bound':lambda desc: alloc_raw if desc==extension['allocation'] else (_ for _ in ()).throw(ValueError('unknown actual allocation descriptor'))}
 exec(compile(ast.Module(body=schema_nodes+snapshot_nodes,type_ignores=[]),'actual-budget-fragments','exec'),{'json':json,'re':re,'hashlib':hashlib},local)
 refused=eval(compile(ast.Expression(first_adopter),'<actual-first-adopter-predicate>','eval'),{'__builtins__':{'set':set}},local)
 if refused:raise ValueError('actual first-adopter snapshot predicate refused')
 return local['ceiling']
ck(validate_parts(initial,extension,claims)==20,'proposed source schema/snapshot sections pass independently of review/admission')
refusals=[]
for name,alter,who in [('drop-one-claim',lambda v:v['claims'].pop(),initial),('duplicate-claim',lambda v:v['claims'].append(v['claims'][0]),initial),('claim-hash-tamper',lambda v:v['claims'][0].__setitem__('claim_sha256','a'*64),initial),('wrong-spent',lambda v:v.__setitem__('consumed_before',2),initial),('baseline-refund',lambda v:v.__setitem__('cumulative_ceiling',18),initial),('family-transfer',lambda v:v['base_family'].__setitem__('mechanism_id','other'),initial),('wrong-initial',lambda v:None,'not-fixed-initial')]:
 bad=copy.deepcopy(extension);alter(bad)
 try:validate_parts(who,bad,claims)
 except ValueError:refusals.append(name)
 else:raise AssertionError('invalid snapshot accepted '+name)
put('BUDGET_VALIDATOR_CONTROLS01.json',{'full_authentic_existing_validator_result':actual,'draft_source_sections_result':20,'not_executed_sections':['accepted review gate38-43','actual admission/source/registration adoption'],'refusals':refusals,'synthetic_accepted_review_created':False})
put('RECONSTRUCTION01.json',{'claims':actual_rows,'claim_details':[{'identity':c['experiment_id'],'source':c['source'],'effective_attempt_budget':c['effective_attempt_budget'],'family':c['family']} for c in claims],'actual_spent':3,'actual_ceiling':19,'remaining_existing':16,'original_phases':18,'fulfilled_phase_slots':[1],'pending_phase_slots':list(range(2,19)),'proposed_ceiling':20,'remaining_if_later_adopted':17,'partial_reference_epochs':29,'reference_complete':False,'paper_fit_credit':0,'absent_prospective_namespaces':[str(p) for p in absences]})
put('RAW_CHECKS01.json',{'count':len(checks),'checks':checks});print(json.dumps({'checks':len(checks),'actual_claims':3,'actual_ceiling':19,'proposed20_source_fragments':True,'adoption':False}))
