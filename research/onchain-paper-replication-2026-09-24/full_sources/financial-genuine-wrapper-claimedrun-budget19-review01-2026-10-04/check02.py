import collections,copy,hashlib,importlib.util,json,os,stat
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;PREP=BASE/'financial-genuine-wrapper-root-claimedrun-budget19-preparation01-2026-10-04';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def load(p):return json.loads(p.read_bytes())
pins={'MANIFEST01.json':'a7561b86a0fa4c6403a0be21849657b43297f90b7690e040cfdaacff78000e73','ALLOCATION19.PROPOSAL.json':'fe135553dc8ebebd84b8adf5cd8011008d53f5c8f6a72761ed3a5837662ac427','EXTENSION19.PROPOSAL.json':'dfed4dd70d7ed37f3b57f155e1f3acadde6ac673d5261be4a1510a96b0c615e4'}
for n,h in pins.items():check(sha((PREP/n).read_bytes())==h,'exact proposal '+n)
m=load(PREP/'MANIFEST01.json');check({p.name for p in PREP.iterdir()}=={r['path'] for r in m['rows']}|{'MANIFEST01.json'},'complete proposal tree')
for r in m['rows']:
 p=PREP/r['path'];s=p.lstat();check(stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==r['mode'] and s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'proposal member '+r['path'])
a=load(PREP/'ALLOCATION19.PROPOSAL.json');e=load(PREP/'EXTENSION19.PROPOSAL.json');plan=load(PREP/'FIRST_PLAN.PROPOSAL.json');g=load(CAP/'fixture_inputs/financial_wrapper_recordfix01/gates.json');fresh=e['initial_experiment'];spent='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';old='financial-wrapper-classification-eager-interrupt1-20261003-01';c=load(CAP/'research_runs'/spent/'claim.json');failed=load(CAP/'research_runs'/spent/'failed.json');family=g['families']['synthetic-financial-wrapper'];check(sha((CAP/'fixture_inputs/financial_wrapper_recordfix01/gates.json').read_bytes())=='4474df26460aab41281bfdcc311129b613a90d76963e853858841200d9faa69a','immutable actual gate')
for n,live in [('historical-claim.json',CAP/'research_runs'/spent/'claim.json'),('historical-failed.json',CAP/'research_runs'/spent/'failed.json')]:check((PREP/n).read_bytes()==live.read_bytes(),'complete exact original closed '+n)
check(c['effective_attempt_budget']==18 and c['family']==family==e['base_family']==a['unchanged_base_family'],'unchanged basefamily/effective historical18');check(family['attempt_budget']==18 and family['prior_attempts']==0,'base18prior0')
actualclaims=[p for p in (CAP/'research_runs').iterdir() if (p/'claim.json').is_file()];check([p.name for p in actualclaims]==[spent],'one actual same-program claim');snapshot=[{'experiment':spent,'claim_sha256':sha((CAP/'research_runs'/spent/'claim.json').read_bytes()),'terminal_status':'failed','terminal_sha256':sha((CAP/'research_runs'/spent/'failed.json').read_bytes())}];check(e['claims']==a['claim_snapshot']==snapshot,'full exact closed snapshot');check(failed['claim_sha256']==snapshot[0]['claim_sha256'] and failed['status']=='failed','failed terminal join')
check(e['program_id']==a['program_id']==g['program_id']==c['program_id'],'same actual programme');check(e['consumed_before']==a['actual_spent_before']==1 and e['cumulative_ceiling']==a['prospective_cumulative_ceiling']==19,'one spent + finite nineteen');check(e['allocation']=={'path':'fixture_inputs/financial_wrapper_claimedrun01/allocation19.json','sha256':pins['ALLOCATION19.PROPOSAL.json']},'exact future allocation byte reference')
check(not any('cumulative_budget_extension' in exp for exp in g['experiments'].values()),'actual gate no adopted extension19');check(fresh==a['new_first_identity']==plan['experiment']==plan['namespace'] and fresh not in g['experiments'] and not os.path.lexists(CAP/'research_runs'/fresh),'fresh proposed identity absent')
check(a['new_first_parent']==spent and a['new_first_prior_input'] is None and a['new_first_reference_input'] is None and plan['prior_input'] is None and plan['reference_input'] is None,'parent is correction ancestry without checkpoint')
check(a['retained_reserved_predispatch_identity']==old and a['retained_spent_unexpected_identity']==spent and a['retained_old_gate_entry_count']==len(g['experiments'])==11,'both original failed identities and11definitions retained')
check(all(a[k] is None for k in ('actual_new_admission','actual_new_caller','actual_new_registration','actual_new_source','paper_budget_extension')) and a['paper_fit_credit']==0 and a['numeric_scientific_change'] is False,'futureauthoritynull and no science/papercredit')
# Reconstruct all rows directly from authenticated original phase contracts.
prior=BASE/'financial-genuine-wrapper-recordfix-registration-preparation02-2026-10-04';pm=load(prior/'MANIFEST02.json');pr=next(r for r in pm['members'] if r['path']=='ORIGINAL_PHASES.json');check(sha((prior/'ORIGINAL_PHASES.json').read_bytes())==pr['sha256'],'authentic original18 phase body');phases=load(prior/'ORIGINAL_PHASES.json')['slots'];mapping={s['proposed_plan']['experiment']:(fresh if s['proposed_plan']['experiment']==old else s['proposed_plan']['experiment']) for s in phases};expected=[]
for i,s in enumerate(phases):
 p=s['proposed_plan'];expected.append(dict(ordinal=i+1,original_phase_identity=p['experiment'],proposed_execution_identity=mapping[p['experiment']],phase=p['phase'],task=p['task'],execution=p['execution'],cell_id=p['cell_id'],conditional_expected_disposition=s['expected_disposition_if_contract_met'],scientific_dependencies=[mapping[x] for x in s['dependencies']],registration_parent_for_fresh_first=spent if p['experiment']==old else None,actual_phase_achieved=False,future_definition_adopted=False))
check(a['original_phase_dag']['rows']==a['remaining_phase_contracts']==expected and len(expected)==18,'entire original DAG/order/types/cells retained in both copies')
counts=dict(collections.Counter(r['phase'] for r in expected));check(counts==a['original_phase_dag']['counts']=={'interrupt1':4,'complete100':4,'continue100':4,'predict':4,'agreement':2},'all phase denominator counts')
check(1+len(expected)==19 and 18-1<len(expected),'strict minimal ceiling derivation')
science={'required_completed100epoch_fits':8,'required_fit_calls':12,'training_updates_across_interrupted_continued_reference':800,'agreement_updates':4,'replay_copies':16,'distinct_training_cells':10,'paper_fit_credit':0}
for k,value in science.items():check(a['original_phase_dag'][k]==value,'original requirement '+k)
check(a['original_model_sha256']==c['inputs']['model']['sha256'] and a['original_training_sha256']==c['inputs']['training']['sha256'],'actual unchanged sciencepins')
expectedplan=copy.deepcopy(phases[0]['proposed_plan']);expectedplan.update(experiment=fresh,namespace=fresh);check(plan==expectedplan,'exact only fresh first identity/namespace plan changes')
# Independently authored five-field acceptance, after exact policy/source review above.
review={'schema_version':1,'decision':'accepted','extension_sha256':pins['EXTENSION19.PROPOSAL.json'],'reviewer':'Independent reviewer /root/combined_worker_review; financial-genuine-wrapper-claimedrun-budget19-review01-2026-10-04','scope':'Prospective source/metadata acceptance of exact extension dfed4dd70d7ed37f3b57f155e1f3acadde6ac673d5261be4a1510a96b0c615e4 and allocation fe135553dc8ebebd84b8adf5cd8011008d53f5c8f6a72761ed3a5837662ac427 only: unchanged same-program base18/prior0, one immutable failed claim, finite18 remaining original phases and cumulative19. No current19 admission, source installation, identity replay, refund/transfer, native release, numerical capacity or paper credit. New isolated capsule requires reviewed complete byte-identical closed-history/Git relocation, exact new source/current=design/gate/caller, full failed-scope and future-source actual external/flat recovery, and fresh release.'}
reviewraw=enc(review);extensionraw=(PREP/'EXTENSION19.PROPOSAL.json').read_bytes();allocationraw=(PREP/'ALLOCATION19.PROPOSAL.json').read_bytes();extpath='fixture_inputs/financial_wrapper_claimedrun01/extension19.json';reviewpath='fixture_inputs/financial_wrapper_claimedrun01/extension19_review.json';references={'extension':{'path':extpath,'sha256':sha(extensionraw)},'review':{'path':reviewpath,'sha256':sha(reviewraw)}}
# Existing exact metadata budget API only; no admission/sourcepin verification is impersonated.
bp=CAP/'tradingagents/research/budget_extensions.py';check(sha(bp.read_bytes())==c['experiment']['source_files']['tradingagents/research/budget_extensions.py'],'genuine budget API pinned');(HERE/'original-budget_extensions.py').write_bytes(bp.read_bytes());spec=importlib.util.spec_from_file_location('review_only_effective_budget',bp);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
reads=[]
def run_api(ref=references,initial=fresh,relevant=None,basefamily=family,raw_extension=extensionraw,raw_allocation=allocationraw,raw_review=reviewraw):
 bodies={extpath:raw_extension,e['allocation']['path']:raw_allocation,reviewpath:raw_review}
 def bound(reference):
  if type(reference)is not dict or set(reference)!={'path','sha256'} or reference['path'] not in bodies:raise ValueError('review harness exact body reference refused')
  b=bodies[reference['path']]
  if sha(b)!=reference['sha256']:raise ValueError('review harness byte pin differs')
  reads.append(reference['path']);return b
 return api.effective_budget(CAP,e['program_id'],initial,{'cumulative_budget_extension':ref},basefamily,[c] if relevant is None else relevant,bound)
check(api.effective_budget(CAP,e['program_id'],spent,g['experiments'][spent],family,[c],lambda _: (_ for _ in ()).throw(AssertionError('unexpected extension read')))==18,'actual unmodified gate stays18')
check(run_api()==19,'genuine API prospective reviewed exact metadata computes19 notadmission')
refusals=[]
def reject(label,**kw):
 try:run_api(**kw)
 except (ValueError,KeyError,TypeError) as er:checks.append('API refusal '+label);refusals.append({'case':label,'error_type':type(er).__name__,'reason':str(er)})
 else:raise AssertionError('API accepted mutation '+label)
reject('wrong first adopter',initial=spent);reject('missing genuine history',relevant=[]);ff=dict(family);ff['attempt_budget']=19;reject('rewritten basefamily',basefamily=ff)
for key,value in [('schema_version',True),('cumulative_ceiling',18),('cumulative_ceiling',True),('consumed_before',0),('consumed_before',2),('claims',[]),('reason',''),('initial_experiment',spent),('program_id','another'),('cumulative_ceiling',20)]:
 changed=copy.deepcopy(e);changed[key]=value;raw=enc(changed);rr=copy.deepcopy(references);rr['extension']['sha256']=sha(raw);reject('changed extension '+key+' '+repr(value),ref=rr,raw_extension=raw)
# Allocation corruption is refused by its original exact reviewed pin, not by a fabricated changed review.
for index in range(18):
 changed=copy.deepcopy(a);changed['original_phase_dag']['rows'][index]['actual_phase_achieved']=True;reject('fabricated achieved phase '+str(index),raw_allocation=enc(changed))
reject('truncated allocation',raw_allocation=allocationraw[:-1]);rr=copy.deepcopy(references);rr['review']['sha256']='0'*64;reject('wrong actual review pin',ref=rr);rr=copy.deepcopy(references);rr['extension']['path']='elsewhere';reject('unselected extension path',ref=rr)
# No forged alternate accepted review was authored for any mutated extension.
with (HERE/'EXTENSION_REVIEW01.json').open('xb') as f:f.write(reviewraw)
for n in ('ALLOCATION19.PROPOSAL.json','EXTENSION19.PROPOSAL.json','FIRST_PLAN.PROPOSAL.json','historical-claim.json','historical-failed.json'):(HERE/n).write_bytes((PREP/n).read_bytes())
out={'decision':'ACCEPTED_EXACT_PROSPECTIVE_METADATA_EXTENSION_NOT_ADMITTED','checks':len(checks),'check_names':checks,'refusals':refusals,'extension_sha256':sha(extensionraw),'allocation_sha256':sha(allocationraw),'genuine_review_sha256':sha(reviewraw),'genuine_budget_API_source_sha256':sha(bp.read_bytes()),'original_current_gate_effective_ceiling':18,'isolated_metadata_API_prospective_ceiling':19,'current_claims_spent':1,'remaining_original_phase_contracts':18,'actual_new_admission':None,'actual_new_source':None,'actual_new_registration':None,'actual_new_caller':None,'source_registration_admission_calls':0,'authority_objects_constructed':0,'old_failed_identity_reopened':False,'numerical_or_native_release':False,'paper_credit':0,'qualification':'Existing pure metadata budget API exercised against genuine current original closed claim plus this reviewer-authored exact prospective review. A bounded in-memory body resolver is not current/design Git admission and grants no authority.'}
with (HERE/'READBACK01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('check_names','refusals')}))
