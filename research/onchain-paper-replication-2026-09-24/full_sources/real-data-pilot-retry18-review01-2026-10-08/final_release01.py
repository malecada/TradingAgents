"""Narrow binding/admission composition; reuse immediately accepted public closure."""
from pathlib import Path
import copy, datetime, hashlib, json, stat
H=Path(__file__).resolve().parent;R=H.parents[3];D=H.parent/'real-data-pilot-final18-2026-10-08'
NAME='eth-paper-real-data-end-to-end-resource-20261008-18'
def raw(p):
    p=Path(p);s=p.lstat()
    assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<1024**2
    assert p.is_relative_to(H) or p.parent==D
    b=p.read_bytes();z=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
    return b
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(raw(p)).hexdigest()}
def read(p):return json.loads(raw(p))
reviewref=ref(H/'BINDING_REVIEW01.json');assert reviewref['sha256']=='d34bc52bf0eed0938a8b6f7822a6d26bd6634dc5b8eff7df25b62faba40410aa'
review=read(H/'BINDING_REVIEW01.json');refs=copy.deepcopy(review['evidence']);assert len(refs)==410
assert review['decision']=='accepted' and review['identity']==NAME and len(review['focused_counterexamples'])==5
bindingref=ref(D/'BINDING01.json');assert bindingref['sha256']=='cff553faac3f6a465352e09ad7f8e91994272374ef5947c126d1b18647493fd9'
binding=read(D/'BINDING01.json');draft=read(D/'BINDING_DRAFT01.json')
assert ref(D/'BINDING_DRAFT01.json')==review['reviewed_draft_binding']
assert binding['status']=='FINAL_BOUND_REQUIRES_COMMITTED_RELEASE'
assert {k:binding['binding_review'][k] for k in ('path','sha256')}==reviewref
assert binding['binding_review']['bytes']==len(raw(H/'BINDING_REVIEW01.json'))
inverse=copy.deepcopy(binding);inverse['status']='DRAFT_NOT_RELEASED';inverse['binding_review']=None;assert inverse==draft
readonlyref=ref(D/'ACTUAL_READONLY_ADMISSION01.json');assert refs[readonlyref['path']]==readonlyref['sha256']
readonly=read(D/'ACTUAL_READONLY_ADMISSION01.json')
assert readonly['ready'] is True and readonly['effective_attempt_budget']==89 and readonly['source_pins']==298 and readonly['input_roles']==59 and readonly['experiment']==NAME
assert readonly['source']==review['source']=='9c54eb2e029b69f0546d30636e9a964e3a460c3d'
assert readonly['resource_policy']=={'disk_floor_bytes':10737418240,'memory_high_bytes':5368709120,'memory_max_bytes':6442450944,'reserve_bytes':2684354560,'start_reserve_bytes':9126805504}
assert readonly['registration']==binding['gate']['path']
# Authenticate only changed/additional bodies, leaving unchanged410 checks reusable.
for p in [D/'BINDING01.json',H/'BINDING_REVIEW01.json',H/'check_binding01.py',H/'BINDING_CHECK01.log',H/'BINDING_CHECK02.log',H/'REVIEW_SETUP_FAILURES01.json',H/'REVIEW01.md',Path(__file__)]:
    v=ref(p)
    if v['path'] in refs:assert refs[v['path']]==v['sha256']
    refs[v['path']]=v['sha256']
for value in binding.values():
    if isinstance(value,dict) and {'path','sha256'}<=set(value):assert refs[value['path']]==value['sha256']
result={'schema_version':1,'decision':'accepted','identity':NAME,'status':'CONDITIONAL_EXACT_ONE_UNUSED18_RELEASE','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
'committed_protocol_source':readonly['source'],'numerical_source_anchor':review['numerical_source_anchor'],'source_pins':298,'input_roles':59,'package_pins':179,
'actual_readonly_admission':readonlyref,'binding_review':reviewref,'reviewed_binding':bindingref,'binding_inverse_only_status_and_exact_review_reference':True,
'reused_current_evidence_count':410,'added_current_evidence_count':len(refs)-410,'private_reference_only':binding['transport'],'evidence':dict(sorted(refs.items())),
'qualification':'Narrow final composition of immediately accepted410-reference source/metadata/binder/entry review. Actual BINDING01 differs only by final status and exact accepted review reference. Genuine committed readonly source9c54eb2e ready89/298/59 remains historical evidence. All pilot17 FAILED/spent88 evidence and accepted external recovery remain retained. Root alone copies this exact release, commits/pushes/authenticates actual remote and runs original full preflight before at most one unused18 invocation. Full preflight must authenticate every public release body at launch HEAD, hash the sole private dispatch, and check original source/runtime/index/storage/RAM/disk/namespace/active-claim/native-unit eligibility. A later refusal grants no threshold change, claim refund or duplicate launcher.',
'not_tested':['No full preflight, private dispatch body read, scientific data, numerical import, ResearchRun.start, claim or native execution.','The just-accepted410-reference closure and previous unchanged matrices were not repeated; only actual final binding, review, admission and new reviewer artifacts were authenticated.','No claim of capacity, throughput, freshness of samples, successful activation, financial performance or writer exclusion.']}
out=H/'EXACT_LAUNCH_RELEASE01.json'
with out.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':'accepted','release':ref(out),'evidence_count':len(refs),'added':len(refs)-410},sort_keys=True))
