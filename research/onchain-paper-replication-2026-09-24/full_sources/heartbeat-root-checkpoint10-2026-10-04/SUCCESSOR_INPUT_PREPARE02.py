import copy,hashlib,json
from pathlib import Path
root=Path.cwd();f=root/'research/onchain-paper-replication-2026-09-24/full_sources';c=f/'heartbeat-root-checkpoint10-2026-10-04';author=f/'financial-wrapper-continuation-successor-source01-2026-10-05';d=f/'financial-wrapper-continuation-successor-preparation02-2026-10-05';cap=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
def encode(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
 with p.open('xb') as w:w.write(b)
assert not d.exists();d.mkdir(mode=0o700)
policy_raw=(cap/'fixture_inputs/financial_wrapper_compatibility01/policy.json').read_bytes();assert sha(policy_raw)=='ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887';original=json.loads(policy_raw);before=original['target']['installed'];after=copy.deepcopy(before);prefix='tradingagents/research/onchain_replication/'
for name in ('operational_source_compatibility.py','financial_wrapper_fixture.py'):after[prefix+name]=sha((author/name).read_bytes())
assert len(after)==195 and len(before)==195
identity='financial-wrapper-classification-eager-continue100-resource-successor-20261005-01';consumer={'experiment':identity,'cell_id':'financial-wrapper-classification-eager-continued-20261003-01'}
edge={'schema_version':1,'kind':'same-family-continuation-source-successor-v1','original_policy_sha256':sha(policy_raw),'consumer':consumer,'installed':after,'allowed_delta':[{'path':p,'old_sha256':before[p],'new_sha256':after[p]} for p in sorted(before) if before[p]!=after[p]],'original_closure_input':'successor_original_closure','refusal_input':'successor_refusal'}
assert len(edge['allowed_delta'])==2
closure=json.loads((cap/'fixture_inputs/financial_wrapper_compatibility01/source_closure.json').read_bytes());assert closure['installed']==before;closure['installed']=after
plan=json.loads((cap/'fixture_inputs/financial_wrapper_continuation01/continue-plan.json').read_bytes());assert plan['phase']=='continue100';plan['experiment']=plan['namespace']=identity
refusal=(f/'financial-wrapper-continuation-outcome-review01-2026-10-05/FULL_REFUSAL_RECOVERY_PROOF01.json').read_bytes();assert sha(refusal)=='a5357602f130838bbf52fd6fe54288401e91bfd045c96aac73fa128f4be41a42'
for name,raw in {'successor.json':encode(edge),'source_closure.json':encode(closure),'continue-plan.json':encode(plan),'refusal.json':refusal}.items():put(d/name,raw)
expected={}
for kind in ('review','recovery'):
 role='continuation_source_successor_'+kind
 expected[role]={'schema_version':1,'kind':role,'decision':'accepted','policy_sha256':sha(encode(edge)),'original_policy_sha256':sha(policy_raw),'historical_map_sha256':sha(canonical(before)),'target_map_sha256':sha(canonical(after)),'checker_sha256':after[prefix+'operational_source_compatibility.py'],'refusal_sha256':sha(refusal)}
put(d/'PROOF_FIELDS_DRAFT01.json',encode({'status':'not-evidence-not-released','required_future_fields':expected}))
put(d/'PREPARATION01.json',encode({'schema_version':1,'status':'prospective-source-input-preparation-only','identity':identity,'candidate_source_pins':{name:sha((author/name).read_bytes()) for name in ('operational_source_compatibility.py','financial_wrapper_fixture.py','preclaim01.py')},'prepared_inputs':{p.name:{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(d.iterdir()) if p.is_file()},'original_policy_sha256':sha(policy_raw),'original_map_sha256':sha(canonical(before)),'current_candidate_map_sha256':sha(canonical(after)),'native_limits_changed':False,'numerical_source_changed':False,'lifecycle_claim_created':False,'authority':'none; actual installed source and independently reviewed source/recovery evidence remain pending'}))
print(json.dumps({'directory':str(d),'prepared_input_bodies':4,'installed_map':len(after),'candidate_map_sha256':sha(canonical(after)),'successor_policy_sha256':sha(encode(edge))}))
