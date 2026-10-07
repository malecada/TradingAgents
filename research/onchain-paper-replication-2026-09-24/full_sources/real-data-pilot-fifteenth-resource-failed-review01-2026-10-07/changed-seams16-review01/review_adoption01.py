"""Read-only exact adoption and changed fixed-identity seams; no metadata rerun."""
from pathlib import Path
import hashlib,json,subprocess
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');H=F/'real-data-pilot-fifteenth-resource-failed-review01-2026-10-07/changed-seams16-review01';D=F/'real-data-pilot-final16-2026-10-07';M=F/'real-data-pilot-ram-candidate01-2026-10-07';B=F/'real-data-pilot-fixed16-metadata-successor01-2026-10-07';O=F/'real-data-pilot-fixed15-metadata-successor01-2026-10-07'
evidence={}
def raw(p):
 b=Path(p).read_bytes();evidence[str(p)]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':hashlib.sha256(raw(p)).hexdigest()}
def write(n,v):
 p=H/n
 with p.open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return p
adoption=read(D/'SOURCE_ADOPTION01.json');assert adoption['status']=='SOURCE_ADOPTED_NOT_EMPIRICALLY_RELEASED'
assert adoption['ram_source_review']==ref(H/'SOURCE_REVIEW01.json')
for n in ('job.py','resources.py','matching_owner.py','real_pilot_import_caller.py'):
 assert raw(Path('tradingagents/research/onchain_replication')/n)==raw(M/n)
strict=adoption['strict_selection_change'];old=subprocess.run(['git','show',adoption['previous_source']+':'+strict['path']],capture_output=True,check=True).stdout;new=raw(strict['path'])
assert hashlib.sha256(old).hexdigest()==strict['before_sha256'] and hashlib.sha256(new).hexdigest()==strict['after_sha256']
assert old.count(b'20261007-15')==strict['identity_replacements']==1 and new==old.replace(b'20261007-15',b'20261007-16')
assert raw(B/'successor02.py')==raw(O/'successor02.py')
delta=read(B/'IDENTITY_DELTA01.json');dep=read(B/'DEPENDENCIES02.json');prior=read(O/'DEPENDENCIES02.json')
assert set(dep)==set(prior) and len(dep)==8
for role,r in dep.items():
 if role not in ('builder','controls'):assert r==prior[role];continue
 row=delta['candidate_replacements'][role];before=raw(row['original_path']);after=raw(r['path'])
 assert r==row['candidate'] and hashlib.sha256(after).hexdigest()==r['sha256'] and hashlib.sha256(before).hexdigest()==row['original_sha256']
 assert before.count(b'20261007-15')==row['identity_replacements']==1 and after==before.replace(b'20261007-15',b'20261007-16')
p=write('ADOPTION_REVIEW01.json',{'schema_version':1,'decision':'accepted_source_adoption_identity_seams_only','identity':'eth-paper-real-data-end-to-end-resource-20261007-16','evidence':evidence,'source_review':ref(H/'SOURCE_REVIEW01.json'),'entry_review':ref(H/'ENTRY_SEAM_REVIEW01.json'),'checks':['All four actual package files equal accepted RAM candidate bytes.','real_pilot_storage bytes equal original source1f0894a2 with exactly one fixed identity15to16 replacement.','Fixed16 successor source bytes unchanged; builder and controls each exactly one identity15to16 replacement; six other dependency references unchanged.'],'findings':[],'qualification':'No final metadata rebuild, genuine admission, allowance87 acceptance, commit identity, native launch or release asserted. Existing prior15 failure and frozen scientific selection retained.','not_tested':['Final concrete draft/preparation/registration/binding/source-pin closure and external recovery pending separate acceptance.','No unchanged metadata matrix, runtime/numerical workload or physical-capacity test.']})
m=write('ADOPTION_MANIFEST01.json',{'schema_version':1,'files':[ref(H/'review_adoption01.py'),ref(p)]})
print(json.dumps({'review':ref(p),'manifest':ref(m)},sort_keys=True))
