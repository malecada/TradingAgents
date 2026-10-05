from pathlib import Path
import json,hashlib,stat
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'held-consumer-canonical-increment-preservation-review01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04';P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-root-launch-20261005-01');Q=F/'held-consumer-canonical-current-capture01-2026-10-05'
def h(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
r=load(C/'CANONICAL_FINAL_PARENT_READONLY_CHECK01.json');assert ref(C/'CANONICAL_FINAL_PARENT_READONLY_CHECK01.json')['sha256']=='a4ba4af9e953bc8e0fd6f5d405b32939354013cd6cfc1723ff4d02ec89cac69f'
assert r['actual_read_only_prepared_exit']==0 and r['prepared_tool']=='c39483' and not r['genuine_Owner_or_ResearchRun_start'] and not r['numerical_imports']
for k in ('stdout','stderr'):assert h((C/('CANONICAL_FINAL_PARENT_PREPARED01.'+k)).read_bytes())==r['prepared_'+k+'_sha256']
actual={str(p.relative_to(P)):p for p in P.rglob('*')};assert set(actual)==set(r['Parent_members']) and len(actual)==10 and stat.S_IMODE(P.stat().st_mode)==r['Parent_root_mode']
for n,p in actual.items():
 st=p.lstat();row=r['Parent_members'][n];assert stat.S_IMODE(st.st_mode)==row['mode'] and st.st_size==row['bytes'] and st.st_nlink==row['nlink'] and [st.st_dev,st.st_ino]==row['physical_identity']
 if row['kind']=='file':assert stat.S_ISREG(st.st_mode) and h(p.read_bytes())==row['sha256']
 else:assert row['kind']=='directory' and stat.S_ISDIR(st.st_mode)
old=load(Q/'snapshot/COMPOSITION01.json')['manifests']['Parent'];assert old['root_mode']==r['Parent_root_mode']
for row in old['members']:
 n=row['path'];assert {k:v for k,v in r['Parent_members'][n].items() if k in row}=={k:v for k,v in row.items() if k!='path'}
new=set(actual)-{x['path'] for x in old['members']};assert new==set(r['new_Parent_origin_mapping'])|{'proofs'} and len(r['new_Parent_origin_mapping'])==5
for n,x in r['new_Parent_origin_mapping'].items():assert (M/x['path']).read_bytes()==(P/n).read_bytes() and h((P/n).read_bytes())==x['sha256']
q=load(P/'request-final01.json');draft=load(P/'request-unreleased01.json');assert {k for k in q if q[k]!=draft[k]}=={'status','remaining','release','evidence'} and set(q)==set(draft)
assert q['status']=='released-one-use-native-parent' and q['remaining']==[] and q['release']=={'path':'release-final01.json','sha256':r['release_sha256']}
release=load(P/'release-final01.json');candidate=load(C/'CANONICAL_RELEASE_CANDIDATE01.json');fields={'release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256'};assert {k for k in release if release[k]!=candidate[k]}==fields and set(release)==set(candidate)
expected={'release_review':('RELEASE_EXECUTION_REVIEW01.json','release_review_sha256'),'external_recovery':('FULL_CURRENT_RECOVERY_PROOF01.json','external_capsule_recovery_sha256'),'external_recovery_review':('FINAL_BASELINE_RECOVERY_REVIEW01.json','external_recovery_review_sha256')}
for key,(n,field) in expected.items():assert q['evidence'][key]=={'path':'proofs/'+n,'sha256':h((D/n).read_bytes())} and release[field]==q['evidence'][key]['sha256'] and (P/'proofs'/n).read_bytes()==(D/n).read_bytes()
assert h((P/'request-final01.json').read_bytes())==r['request_sha256']=='da6a681c81da17c304714e46e47a9e1f2dc886097b9b2c387a36dcc17f1b3db5'
assert h((P/'release-final01.json').read_bytes())==r['release_sha256']=='5ebe7fd9f944ed317d094390ddaf48479bae58066464e5baecd41935c05aa7cb'
contract=h(json.dumps({k:v for k,v in release.items() if k not in fields},sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode());assert contract=='1b7ad898ee326ce69566cdd23d97123e0959efa84ba523d47a60f80a13c7b1ed'
out={'schema_version':1,'decision':'accepted-actual-canonical-final-parent-binding-pending-direct-recovery','actual_prepared_record':ref(C/'CANONICAL_FINAL_PARENT_READONLY_CHECK01.json'),'contract_sha256':contract,'request':ref(P/'request-final01.json'),'release':ref(P/'release-final01.json'),'Parent_regular':9,'Parent_typed':10,'accepted_old_regular':4,'new_regular':5,'new_directory':'proofs','original_path_metadata_mapping_checked':True,'exact_three_review_body_joins':True,'complete_parent_membership_checked':True,'new_Parent_origin_mapping':r['new_Parent_origin_mapping'],'old_drafts_unchanged':True,'actual_prepared_tool':'c39483','actual_prepared_exit':0,'numerical_or_native_entry':False,'pending':'Actual committed eight-body direct recovery, independent final complete union, fresh physical/native eligibility and separate exact one-use launch entry. Recorded instantaneous resources do not prove capacity.'}
p=D/'FINAL_PARENT_BINDING_CHECK01.json'
with p.open('x') as f:json.dump(out,f,sort_keys=True,separators=(',',':'));f.write('\n')
p.chmod(0o444);print(h(p.read_bytes()))
