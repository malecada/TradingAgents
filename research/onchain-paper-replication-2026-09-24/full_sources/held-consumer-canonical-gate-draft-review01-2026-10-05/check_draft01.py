from pathlib import Path
import json,hashlib,copy,subprocess
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';A=F/'held-consumer-canonical-root-binding01-2026-10-05';P=A/'capsule-metadata-draft01';D=F/'held-consumer-canonical-gate-draft-review01-2026-10-05';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source');ID='original-import-canonical-held-success-20261005-01'
def h(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
old=json.loads(subprocess.check_output(['git','show','55e7d50431654aba952b4541ca506524d9feece1:held-fixture-registration01.json'],cwd=S));g=load(P/'held-fixture-registration01.json');n=g['experiments'][ID]
assert set(g)==set(old)
for k in g:
 if k!='experiments':assert g[k]==old[k]
assert len(old['experiments'])==6 and set(g['experiments'])==set(old['experiments'])|{ID}
for k,v in old['experiments'].items():assert g['experiments'][k]==v
roles=load(P/'ROOT_ROLE_REFERENCES_DRAFT01.json');assert len(roles)==15
for role,r in roles.items():
 raw=(P/r['path']).read_bytes();assert len(raw)==r['bytes'] and h(raw)==r['sha256']
for role in ('runtime','software_environment','native_environment','native_policy','original_import_index','original_evidence','matching','target_catalog'):
 assert (P/roles[role]['path']).read_bytes()==(A/'metadata-draft01/roles'/(role+'.json')).read_bytes()
assert (P/roles['case_contract']['path']).read_bytes()==(A/'metadata-draft01/contracts/success.json').read_bytes()
assert (P/'CUMULATIVE_REVIEW01.json').read_bytes()==(F/'held-consumer-canonical-root-binding-review01-2026-10-05/CUMULATIVE_REVIEW01.json').read_bytes()
assert h((P/'CUMULATIVE_REVIEW01.json').read_bytes())=='7ec00d22ec0edff27032cbc3328b12dbf95a5ed4d1aac4a7170704df9d61f63d'
for name in ('CUMULATIVE_EXTENSION05_DRAFT01.json','CUMULATIVE_ALLOCATION05_DRAFT01.json'):assert (P/name).read_bytes()==(A/name).read_bytes()
implementation=load(P/'IMPLEMENTATION_MAP_DRAFT01.json');original=load(A/'ROOT_REBOUND_CASE_DRAFTS01.json')['success']['experiment'];expect=copy.deepcopy(original['source_files']);expect['fixture_tools/capsule_builder01.py']='d30c30e41810df094298582ef2e9ac01e3292e178b0d52277466a4c08118a636';assert implementation==expect
assert len(implementation)==199 and sum(k.startswith('tradingagents/') for k in implementation)==148
aux=load(P/'held-auxiliary-canonical-success01.json');assert aux['experiment_id']==ID and aux['implementation_map_sha256']==h(json.dumps(implementation,sort_keys=True,separators=(',',':')).encode())
assert aux['entry_count']==len(aux['entries'])==4
assert {r['role'] for r in aux['entries']}=={'budget_allocation','budget_extension','budget_review','charter'}
union=dict(implementation)
for row in aux['entries']:
 assert row['reference']==roles[row['role']];union[row['reference']['path']]=row['reference']['sha256']
union['held-auxiliary-canonical-success01.json']=h((P/'held-auxiliary-canonical-success01.json').read_bytes());assert n['source_files']==union and len(union)==204
expected=copy.deepcopy(original);expected['source_files']=union;expected['charter']={k:roles['charter'][k] for k in ('path','sha256')};expected['cumulative_budget_extension']={'extension':{k:roles['budget_extension'][k] for k in ('path','sha256')},'review':{k:roles['budget_review'][k] for k in ('path','sha256')}}
pair=expected['inputs']['pair_policy']['path'];pairraw=(P/pair).read_bytes();assert pairraw==(A/'metadata-draft01/inputs'/pair).read_bytes();expected['inputs']['pair_policy']['sha256']=h(pairraw);assert n==expected
assert len(n['inputs'])==33 and len(n['outputs'])==6
allocation=load(P/'CUMULATIVE_ALLOCATION05_DRAFT01.json');assert len(allocation['new_attempts'])==1 and allocation['new_attempts'][0]['identity']==ID and allocation['new_attempts'][0]['maximum_claims']==1
assert allocation['retained_unclaimed_unavailable'][0]['identity']=='original-import-held-publication-failure-20261003-01'
assert [name for name,e in g['experiments'].items() if e.get('cumulative_budget_extension')==n['cumulative_budget_extension']]==[ID]
contract=load(P/roles['case_contract']['path']);assert contract['experiment_id']==ID
assert load(A/'metadata-draft01/contracts/second_target_publication_failure.json')['experiment_id'] is None
result={'schema_version':1,'decision':'accepted-one-identity-gate-draft-seam-only','registration':ref(P/'held-fixture-registration01.json'),'role_references':ref(P/'ROOT_ROLE_REFERENCES_DRAFT01.json'),'implementation_map':ref(P/'IMPLEMENTATION_MAP_DRAFT01.json'),'auxiliary':ref(P/'held-auxiliary-canonical-success01.json'),'charter':ref(P/'held-charter-canonical-success01.md'),'cumulative_review_sha256':'7ec00d22ec0edff27032cbc3328b12dbf95a5ed4d1aac4a7170704df9d61f63d','historical_experiments_unchanged':6,'top_level_family_datasets_unchanged':True,'new_experiments':1,'identity':ID,'role_count':15,'implementation_pins':199,'package_pins':148,'admission_pins':204,'inputs':33,'outputs':6,'same_extension_registered_identities':[ID],'conditional_publication_slot_unavailable':True,'case2_new_identity':None,'actual_integration_check_pending':True,'execution_release':False,'qualification':'Exact draft references and accepted metadata bodies joined; only new success consumes proposed extension. Historical gates/claims untouched. Concrete one-use caller, genuine current design/admission/runtime/native eligibility and actual recovery remain prerequisites; generic ceiling alone is not transferable authority.'}
p=D/'DRAFT_CHECK01.json'
with p.open('x') as f:json.dump(result,f,sort_keys=True,separators=(',',':'));f.write('\n')
p.chmod(0o444);print(h(p.read_bytes()))
