"""Read only fixed public metadata/source and hash one opaque body without decode."""
from pathlib import Path
import copy,hashlib,json,stat,os
ROOT=Path.cwd();F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';P=F/'real-data-pilot-full39-binding-preparation01-2026-10-12'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
raw=lambda obj:(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
load=lambda p:json.loads(p.read_bytes())
def auth(ref):
 p=ROOT/ref['path'];assert p.resolve()==p and p.is_file() and not p.is_symlink();s=p.stat();assert s.st_nlink==1
 b=p.read_bytes();assert sha(b)==ref['sha256'] and ('bytes' not in ref or len(b)==ref['bytes']);assert all(getattr(s,k)==getattr(p.stat(),k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'));return b
bound=load(P/'BOUND01.json');prepared=load(P/'PREPARED01.json');check=load(P/'BINDING_CHECK01.json');refs=load(P/'ALL_INPUT_REFS01.json');prior=load(P/'PUBLIC_INPUT_REFS_DRAFT01.json')
assert len(refs)==73 and check['all_input_roles']==73
assert check['experiment']=='eth-paper-real-data-end-to-end-resource-20261012-39'
for key in ('claim','launch','network'):assert check[key] is False
for key in ('bound','prepared','request','binder'):auth(check[key])
assert check['binder']['sha256']=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
assert bound['status']=='BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED' and bound['independent_approval'] is False
private=bound['private_input'];assert list(private)==['archive_transport'] and private==check['actual_opaque_input']
opaque=private['archive_transport'];assert refs['archive_transport']['path']==opaque['path'] and refs['archive_transport']['sha256']==opaque['sha256']
op=ROOT/opaque['path'];assert op.is_relative_to(ROOT/'research_artifacts/real_pilot_runtime')
assert opaque['bytes']==930 and stat.S_IMODE(op.stat().st_mode)==0o600 and stat.S_IMODE(op.parent.stat().st_mode)==0o700
assert op.stat().st_uid==os.getuid() and op.parent.stat().st_uid==os.getuid();auth(opaque) # Never json.loads opaque.
req=bound['source_request'];assert str(Path(req['private_parent'])/req['private_leaf'])==opaque['path'];assert req['prepared']==check['prepared']
archive=json.loads(auth(req['archive_policy']));assert prepared['builder03_spec']['references']['archive_policy']==req['archive_policy']
docs=copy.deepcopy(bound['inputs']);roles=prepared['builder03_spec']['template_roles'];bridge=bound['binding'];assert bridge['transport_role']=='archive_transport' and bridge['archive_role']==roles['archive']
for role,value in docs.items():assert auth(refs[role])==raw(value)
changed={'archive_transport'}|set(docs)
for role,ref in prior.items():
 if role not in changed:assert refs[role]==ref
policy=docs.pop(roles['archive']);assert policy['transport_identity']==bridge['transport_identity'] and sha(raw(policy))==bridge['archive_policy_sha256'];policy['transport_identity']=None;assert policy==archive
selected=next(iter(docs[roles['job']]['payload']['representation_jobs'].values()));item=docs[roles['producer_plan']]['producers'][selected['producer']]
for value in (selected,item):
 assert value['compact_archive_transport_input']=='archive_transport' and value['descriptor']['compact_archive_execution']=={'backend':archive['backend'],'policy_sha256':bridge['archive_policy_sha256']}
 value['descriptor']['compact_archive_execution']['policy_sha256']=bridge['prior_descriptor_policy_sha256']
expected=copy.deepcopy(prepared['builder03_result']['inputs']);assert 'archive_transport' not in docs and expected['archive_transport']['connection'] is None;docs['archive_transport']=expected['archive_transport'];assert docs==expected
join=load(P/'CURRENT_NUMERICAL_GIT_JOIN01.json');assert join['count']==205 and len(join['files'])==205 and join['actual_git_batch_exit']==0 and join['source']=='989e805ed5ae59126f096135eea43095eaebc81d'
for ref in join['files']:auth(ref)
review_path=F/'pilot38-outcome-increment35-review-2026-10-12/RETURN_REVIEW01.json';review=load(review_path);assert sha(review_path.read_bytes())=='fa56521cd5bde84ee4bf9289cb9d66c6d8ef9653b7ce278bd2c79f772e22df63';assert review['decision']=='accepted'
recovery=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full38outcome35/FRESH_GIT_RECOVERY35.json';assert review['evidence'][str(recovery.relative_to(ROOT))]==sha(recovery.read_bytes())
evidence={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [P/n for n in ['BOUND01.json','BINDING_CHECK01.json','ALL_INPUT_REFS01.json','PREPARED01.json','PUBLIC_INPUT_REFS_DRAFT01.json','CURRENT_NUMERICAL_GIT_JOIN01.json']]+[review_path,recovery]}
print(json.dumps({'status':'ACTUAL_PUBLIC39_READBACK_AND_BINDER_INVERSE_PASS','input_roles':73,'bound_public_roles':len(bound['inputs']),'unchanged_numerical_source_bodies':205,'original_source':join['source'],'opaque':opaque,'opaque_decoded':False,'actual35_review_schema_join':True,'evidence':evidence,'helper_binder_admission_scan_numerics_executed':False},indent=2))
