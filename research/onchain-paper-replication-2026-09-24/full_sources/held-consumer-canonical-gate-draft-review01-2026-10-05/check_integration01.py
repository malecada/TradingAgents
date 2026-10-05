from pathlib import Path
import json,hashlib,subprocess
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';A=F/'held-consumer-canonical-root-binding01-2026-10-05';P=A/'capsule-metadata-draft01';D=F/'held-consumer-canonical-gate-draft-review01-2026-10-05';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source');ID='original-import-canonical-held-success-20261005-01';HEAD='468d756c16b3825e83a931c082ab4072764a873d';ANCHOR='55e7d50431654aba952b4541ca506524d9feece1'
def h(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
def git(*a):return subprocess.check_output(['git','-c','protocol.allow=never',*a],cwd=S)
prep=load(A/'SOURCE_AND_GATE_PREPARATION01.json');commit=load(A/'SOURCE_GATE_COMMIT02.json');readback=load(A/'ACTUAL_METADATA_DRAFT_READBACK02.json');failure=load(A/'FAILED_SOURCE_GATE_PREPARATION01.json');gate=load(P/'held-fixture-registration01.json');experiment=gate['experiments'][ID]
assert ref(A/'SOURCE_GATE_COMMIT02.json')['sha256']=='8d8002a1a33800f08d433ed3df303c7edd0dd0eeea1a2a3ca6732789560eb46a'
assert ref(A/'ACTUAL_METADATA_DRAFT_READBACK02.json')['sha256']==commit['metadata_sha256']=='6112b95078083d61af20e20953a7ba4e64a03fc774bb7f62a9e4136fe84bc46e'
assert commit['current_source']==commit['design_source']==HEAD and commit['package_anchor']==ANCHOR
assert commit['stage_exit']==commit['commit_exit']==commit['readback_exit']==commit['metadata_exit']==0
assert git('rev-parse','HEAD').decode().strip()==HEAD and git('show','-s','--format=%P',HEAD).decode().split()==[ANCHOR]
assert not git('status','--porcelain','--untracked-files=no').strip()
changed=set(git('diff','--name-only',ANCHOR,HEAD).decode().splitlines());assert len(changed)==42
copies=prep['missing_original_inputs_copied'];assert len(copies)==22 and sum(x['bytes'] for x in copies)==961506
pins={}
for r in copies:
 raw=(S/r['path']).read_bytes();assert len(raw)==r['bytes'] and h(raw)==r['sha256'] and raw==Path(r['origin']).read_bytes()
 inp=experiment['inputs'][r['role']];assert inp['path']==r['path'] and inp['sha256']==r['sha256'];pins[r['path']]=raw
for r in prep['installed_preparation_bodies']:
 raw=(S/r['path']).read_bytes();assert len(raw)==r['bytes'] and h(raw)==r['sha256']
 origin=(F/'held-consumer-canonical-anchor-supplement01-2026-10-05/capsule_builder01.py') if r['path']=='fixture_tools/capsule_builder01.py' else P/r['path'];assert raw==origin.read_bytes();pins[r['path']]=raw
assert changed<=set(pins) and len(set(pins)-changed)==2
# Batch exact committed-object joins for the changed scope only.
entries={}
for line in git('ls-tree','-rz',HEAD,'--',*sorted(changed)).split(b'\0'):
 if line:
  fields,n=line.split(b'\t');mode,kind,oid=fields.decode().split();entries[n.decode()]=(mode,kind,oid)
assert set(entries)==changed
for n,(mode,kind,oid) in entries.items():
 raw=pins[n];assert kind=='blob' and mode in ('100644','100755') and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid
assert (S/'held-fixture-registration01.json').read_bytes()==(P/'held-fixture-registration01.json').read_bytes()
impl=load(P/'IMPLEMENTATION_MAP_DRAFT01.json');source=readback['source_document'];plan=readback['input_plan'];roles=load(P/'ROOT_ROLE_REFERENCES_DRAFT01.json')
assert source['source']==plan['source']==HEAD and source['anchor']==plan['anchor']==ANCHOR and source['source_files']==impl
assert source['source_count']==199 and source['package_count']==148 and source['package_files']=={n:p for n,p in impl.items() if n.startswith('tradingagents/')}
assert plan['observed_metadata']==roles and len(roles)==15 and plan['remaining_roles']==[]
assert plan['auxiliary_metadata']['admission_source_files']==experiment['source_files'] and plan['auxiliary_metadata']['admission_source_count']==204
assert len(plan['input_rows'])==33 and {k:{n:r[n] for n in ('path','sha256','dataset')} for k,r in plan['input_rows'].items()}==experiment['inputs']
assert readback['runtime_readback']==load(A/'RUNTIME_ROLE_READBACK01.json')
assert readback['status']=='draft-not-released' and not readback['execution_admitted'] and readback['native_release'] is None and readback['registration_authority'] is None and readback['budget_authority'] is None
assert readback['route_readback']['numeric_arrays_read'] is False and plan['arrays_generated'] is False and plan['original_sampling_rerun'] is False
assert failure['tool_chunk']=='a35e70' and failure['exit_code']==1 and not failure['identity_spent'] and not failure['claim_created'] and not failure['owner_created']
assert not (S/'research_runs'/ID).exists()
assert len([p for p in (S/'research_runs').iterdir() if (p/'claim.json').is_file()])==5
out={'schema_version':1,'decision':'accepted-actual-source-gate-metadata-integration-only','current_source':HEAD,'design_source':HEAD,'package_anchor':ANCHOR,'commit_receipt':ref(A/'SOURCE_GATE_COMMIT02.json'),'actual_genuine_metadata_readback':ref(A/'ACTUAL_METADATA_DRAFT_READBACK02.json'),'preparation':ref(A/'SOURCE_AND_GATE_PREPARATION01.json'),'retained_preparation_failure':ref(A/'FAILED_SOURCE_GATE_PREPARATION01.json'),'draft_check':ref(D/'DRAFT_CHECK01.json'),'changed_committed_paths':42,'missing_original_inputs_verified':22,'missing_original_input_bytes':961506,'roles':15,'implementation_pins':199,'package_pins':148,'admission_pins':204,'inputs':33,'outputs':6,'runtime_RECORD_readback_reused':251,'five_original_failed_claims_retained':True,'fresh_identity_unclaimed':True,'numerical_arrays_decoded':False,'new_execution_release':False,'qualification':'Exact changed paths joined to local committed Git objects; new opaque inputs joined to preserved originals, accepted draft bodies to live preparation, genuine readback to every fixed map/role. No repeated historical source/runtime matrix. a35e70 remains ordinary preparation failure, not empirical spend. Current committed metadata is not Admission, guarded materialization, native readiness, full external recovery or one-use Parent release.'}
p=D/'INTEGRATION_CHECK01.json'
with p.open('x') as f:json.dump(out,f,sort_keys=True,separators=(',',':'));f.write('\n')
p.chmod(0o444);print(h(p.read_bytes()))
