from pathlib import Path
import json,hashlib,subprocess,copy,importlib.util,sys
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'held-consumer-canonical-root-binding-review01-2026-10-05';A=F/'held-consumer-canonical-root-binding01-2026-10-05';R=F/'held-consumer-canonical-root-recipe02-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source')
def h(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
def enc(d):return (json.dumps(d,sort_keys=True,indent=2)+'\n').encode()
def put(n,d):
 p=D/n;b=(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(b)
 p.chmod(0o444);print(n,h(b))
def git(*args):return subprocess.check_output(['git',*args],cwd=S)
a=load(A/'ROOT_REBOUND_CASE_DRAFTS01.json');old=load(R/'DRAFT_CASES02.json');mat=load(A/'SOURCE_MATERIALIZATION01.json');e=load(A/'CUMULATIVE_EXTENSION05_DRAFT01.json');allocation=load(A/'CUMULATIVE_ALLOCATION05_DRAFT01.json')
assert h((A/'CUMULATIVE_EXTENSION05_DRAFT01.json').read_bytes())=='c161983c753a1aa17fabbe7f3af3f4f6017b59e81d10e667075c661356ef0c1d'
assert h((A/'CUMULATIVE_ALLOCATION05_DRAFT01.json').read_bytes())==e['allocation']['sha256']=='0673e21c83475cfebe48c57f3176a746fed70b6f001f2284646d3c47fe05f097'
review=load(F/'held-consumer-canonical-root-recipe-review02-2026-10-04/REVIEW01.json');assert review['decision']=='ACCEPTED_SOURCE_ONLY_RR1_TO_RR5_CORRECTIONS'
for n in ('prepare01.py','rebind01.py'):assert h((R/n).read_bytes())==review['candidate_pins'][n]
assert git('rev-parse','HEAD').decode().strip()=='55e7d50431654aba952b4541ca506524d9feece1'
assert not git('status','--porcelain','--untracked-files=no').strip()
changed=set(git('diff','--name-only','d443208795f59292c156c5b81b687594efacea4d','HEAD').decode().splitlines())
assert changed=={mat['changed_implementation_body']}|set(mat['root_rebound_inputs'])|set(mat['exact_spent_metadata_mirrors'])
assert h((S/mat['changed_implementation_body']).read_bytes())==review['inherited_source_map']['replacement']=='e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9'
for case,draft in a.items():
 expected=copy.deepcopy(old[case]);expected['capsule_root']=str(S)
 for role in ('execution_job','execution_workspace'):
  n=draft['experiment']['inputs'][role]['path'];base=load(R/'generated01/input-draft'/n)
  if role=='execution_job':base['resources']['disk_paths']=[str(S)];base['resources']['storage_budget']['root']=str(S)
  else:base={'root':str(S),'ledger':str(S/'research_runs'),'artifacts':str(S/'research_artifacts'),'git_common':str(S/'.git')}
  raw=(S/n).read_bytes();assert json.loads(raw)==base and h(raw)==draft['experiment']['inputs'][role]['sha256']
  expected['experiment']['inputs'][role]['sha256']=h(raw)
  expected['case_contract']['additional_inputs'][role]['reference'].update(bytes=len(raw),sha256=h(raw))
 assert draft==expected
 pins=draft['experiment']['source_files'];assert len(pins)==199 and sum(n.startswith('tradingagents/') for n in pins)==148
 assert pins==old[case]['experiment']['source_files']
 if case=='success':
  for n,pin in pins.items():assert h((S/n).read_bytes())==pin
claims=[];total=0
for n,row in mat['exact_spent_metadata_mirrors'].items():
 raw=(S/n).read_bytes();assert raw==Path(row['original_path']).read_bytes() and len(raw)==row['bytes'] and h(raw)==row['sha256'];total+=len(raw)
assert total==207074
for r in e['claims']:
 d=S/'research_runs'/r['experiment'];c=load(d/'claim.json');t=load(d/'failed.json')
 assert h((d/'claim.json').read_bytes())==r['claim_sha256'] and h((d/'failed.json').read_bytes())==r['terminal_sha256']
 assert c['program_id']==e['program_id'] and c['family']==e['base_family'] and c['experiment_id']==r['experiment']
 assert t['experiment_id']==r['experiment'] and t['claim_sha256']==r['claim_sha256'] and t['status']=='failed';claims.append(c)
assert {p.name for p in (S/'research_runs').iterdir() if (p/'claim.json').is_file()}=={c['experiment_id'] for c in claims}
assert len(claims)==e['consumed_before']==5 and max(c['effective_attempt_budget'] for c in claims)==6
assert e['base_family']['attempt_budget']==2 and e['base_family']['prior_attempts']==0 and e['cumulative_ceiling']==7
assert len(allocation['new_attempts'])==1 and allocation['new_attempts'][0]['identity']==e['initial_experiment']=='original-import-canonical-held-success-20261005-01' and allocation['new_attempts'][0]['maximum_claims']==1
assert not (S/'research_runs'/e['initial_experiment']).exists()
assert len(allocation['retained_unclaimed_unavailable'])==1 and allocation['retained_unclaimed_unavailable'][0]['identity']=='original-import-held-publication-failure-20261003-01'
assert not Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-root-launch-20261005-01').exists()
put('SOURCE_BINDING_CHECK01.json',{'schema_version':1,'decision':'accepted-exact-source-input-materialization-only','actual_source':'55e7d50431654aba952b4541ca506524d9feece1','preparation':ref(A/'PREPARATION01.json'),'source_commit':ref(A/'SOURCE_COMMIT01.json'),'materialization':ref(A/'SOURCE_MATERIALIZATION01.json'),'case_drafts':ref(A/'ROOT_REBOUND_CASE_DRAFTS01.json'),'accepted_recipe_review':ref(F/'held-consumer-canonical-root-recipe-review02-2026-10-04/REVIEW01.json'),'implementation_pins':199,'package_pins':148,'unchanged_implementation_bodies':198,'changed_implementation_bodies':1,'root_rebound_input_bodies':4,'closed_metadata_mirrors':10,'closed_metadata_bytes':207074,'new_claims':0,'qualification':'Exact commit diff, installed source pins, root-only input inverse and raw closed metadata mirrors authenticated. No new gate, Parent, runtime binding, admission, recovery or launch authority; no historical numerical outputs copied or decoded.'})
# This is the actual independent exact-extension review, not a synthetic accepted authority.
put('CUMULATIVE_REVIEW01.json',{'schema_version':1,'decision':'accepted','extension_sha256':h((A/'CUMULATIVE_EXTENSION05_DRAFT01.json').read_bytes()),'reviewer':'independent continuation_successor_review; held-consumer-canonical-root-binding-review01-2026-10-05','scope':'Exact same-program/base2/prior0 extension: five actual FAILED spends retained, highest adopted6, proposed ceiling7 solely for one fresh original-import-canonical-held-success-20261005-01. Original conditional publication-failure slot remains unavailable/nontransferable. Allocation0673e21c pins fixed guards and exposed32motifs/512samples; no refund, paper credit, new samples or numerical authority. Source/current gate/roles/caller/runtime and actual recovery require later independent checks. Generic budget validator does not itself enforce allocation identity beyond first adopter; concrete gate/caller must retain the one-case restriction.'})
validator=S/'tradingagents/research/budget_extensions.py';assert h(validator.read_bytes())=='59d22880e9ff7909508db6b0c15a7a833df30be365af4e31d643ed64afabb25a'
spec=importlib.util.spec_from_file_location('review_budget_metadata',validator);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
extref={'path':str(A/'CUMULATIVE_EXTENSION05_DRAFT01.json'),'sha256':h((A/'CUMULATIVE_EXTENSION05_DRAFT01.json').read_bytes())};revref=ref(D/'CUMULATIVE_REVIEW01.json')
def read_bound(r):
 p=Path(r['path']);p=p if p.is_absolute() else A/p;b=p.read_bytes();assert h(b)==r['sha256'];return b
experiment=copy.deepcopy(a['success']['experiment']);experiment['cumulative_budget_extension']={'extension':extref,'review':revref}
assert mod.effective_budget(S,e['program_id'],e['initial_experiment'],experiment,e['base_family'],claims,read_bound)==7
assert not any(n in sys.modules for n in ('numpy','torch','pandas'))
put('CHECK01.json',{'schema_version':1,'decision':'accepted-bounded-binding-and-cumulative-review','source_check':ref(D/'SOURCE_BINDING_CHECK01.json'),'cumulative_review':ref(D/'CUMULATIVE_REVIEW01.json'),'extension':ref(A/'CUMULATIVE_EXTENSION05_DRAFT01.json'),'allocation':ref(A/'CUMULATIVE_ALLOCATION05_DRAFT01.json'),'genuine_validator':ref(validator),'pure_metadata_validator_result':7,'actual_spent':5,'actual_failed':5,'highest_adopted':6,'proposed_ceiling':7,'publication_slot_unavailable':True,'numerical_imports':False,'execution_release':False,'remaining':['genuine current gate/source/design','concrete one-case caller and Parent','all authority/runtime roles','fresh actual external byte recovery','independent final release'],'not_tested':['numerical output correctness','economic accuracy/fees/funding/PnL','new runtime/native capacity','financial experiment rerun','full current recovery']})
