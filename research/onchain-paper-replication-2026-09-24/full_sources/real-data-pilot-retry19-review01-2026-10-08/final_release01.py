"""Narrow binding/admission composition; reuse immediately accepted public closure."""
from pathlib import Path
import copy, datetime, hashlib, json, stat
H=Path(__file__).resolve().parent;R=H.parents[3];D=H.parent/'real-data-pilot-final19-2026-10-08'
NAME='eth-paper-real-data-end-to-end-resource-20261008-19'
def raw(p):
    p=Path(p);s=p.lstat()
    assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<1024**2
    assert p.is_relative_to(H) or p.is_relative_to(D)
    b=p.read_bytes();z=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
    return b
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(raw(p)).hexdigest()}
def read(p):return json.loads(raw(p))
reviewref=ref(H/'BINDING_REVIEW01.json');assert reviewref['sha256']=='d02a4f08b1e4066a863a00e23aef22fcbec593421b8dd24a631c9a1888692b3c'
review=read(H/'BINDING_REVIEW01.json');refs=copy.deepcopy(review['evidence']);assert len(refs)==420
assert review['decision']=='accepted' and review['identity']==NAME and len(review['focused_counterexamples'])==5
bindingref=ref(D/'BINDING01.json')
binding=read(D/'BINDING01.json');draft=read(D/'BINDING_DRAFT01.json')
assert ref(D/'BINDING_DRAFT01.json')==review['reviewed_draft_binding']
assert binding['status']=='FINAL_BOUND_REQUIRES_COMMITTED_RELEASE'
assert {k:binding['binding_review'][k] for k in ('path','sha256')}==reviewref
assert binding['binding_review']['bytes']==len(raw(H/'BINDING_REVIEW01.json'))
inverse=copy.deepcopy(binding);inverse['status']='DRAFT_NOT_RELEASED';inverse['binding_review']=None;assert inverse==draft
cliref=ref(D/'ACTUAL_READONLY_ADMISSION01.json');assert refs[cliref['path']]==cliref['sha256']
cli=read(D/'ACTUAL_READONLY_ADMISSION01.json');assert cli['read_only'] and cli['exit_code']==0 and not cli['Owner'] and not cli['claim']
assert cli['source']==review['source']=='5f2d4faaa7f8a1f712ac38d7e8a06686f8cd172a'
readonlyref=ref(D/'ACTUAL_JOB_READONLY_ADMISSION01.json');readonly=read(D/'ACTUAL_JOB_READONLY_ADMISSION01.json')
assert readonly['ready'] is True and readonly['effective_attempt_budget']==90 and readonly['source_pins']==298 and readonly['input_roles']==59
assert readonly['source']==cli['source'] and readonly['interface']=='genuine job._admitted' and not readonly['Owner'] and not readonly['claim'] and not readonly['ResearchRun.start'] and not readonly['numerical_work']
jobref=ref(D/'inputs01/execution_job.json');assert refs[jobref['path']]==jobref['sha256']
job=read(D/'inputs01/execution_job.json');assert readonly['resource_policy']==job['resources']
assert readonly['resource_policy']['start_reserve_bytes']==readonly['resource_policy']['reserve_bytes']==2684354560
assert readonly['resource_policy']['memory_max_bytes']==6442450944 and readonly['resource_policy']['memory_high_bytes']==5368709120 and readonly['resource_policy']['disk_floor_bytes']==10737418240
# Authenticate only changed/additional bodies, leaving unchanged420 checks reusable.
for p in [D/'BINDING01.json',D/'ACTUAL_JOB_READONLY_ADMISSION01.json',H/'BINDING_REVIEW01.json',H/'check_binding01.py',H/'BINDING_CHECK01.log',H/'ENTRY_REVIEW01.md',H/'import-review01/REVIEW_SETUP_FAILURE01.json',Path(__file__)]:
    v=ref(p)
    if v['path'] in refs:assert refs[v['path']]==v['sha256']
    refs[v['path']]=v['sha256']
for value in binding.values():
    if isinstance(value,dict) and {'path','sha256'}<=set(value):assert refs[value['path']]==value['sha256']
result={'schema_version':1,'decision':'accepted','identity':NAME,'status':'CONDITIONAL_EXACT_ONE_UNUSED19_RELEASE','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
'committed_protocol_source':readonly['source'],'numerical_source_anchor':review['numerical_source_anchor'],'source_pins':298,'input_roles':59,'package_pins':179,
'actual_readonly_job_admission':readonlyref,'actual_readonly_cli_admission':cliref,'binding_review':reviewref,'reviewed_binding':bindingref,'binding_inverse_only_status_and_exact_review_reference':True,
'reused_current_evidence_count':420,'added_current_evidence_count':len(refs)-420,'private_reference_only':binding['transport'],'evidence':dict(sorted(refs.items())),
 'qualification':'Narrow final composition of immediately accepted420-reference current source/metadata/binder/entry review. Actual BINDING01 differs only by final status and exact accepted review reference. Genuine job._admitted ready90/298/59 at source5f2d4faaa joins the exact startup2.5GiB/runtime2.5GiB/6hard5high/10disk resource policy. The separate original CLI metadata_admitted receipt remains accurately scoped. Prior18 is permanently closed preclaim/reserved89;58 actual closed claims/highest88 remain. Root alone copies this exact release, commits/pushes/authenticates actual remote and runs original full fresh preflight before at most one unused19 invocation. Full preflight must authenticate every public release body at launch HEAD, hash the sole private dispatch, and check original source/runtime/index/storage/RAM/disk/namespace/active-claim/native-unit eligibility. No later refusal grants an extra threshold change, refunded identity or duplicate launcher.', 
'not_tested':['No full preflight, private dispatch body read, scientific data, numerical import, ResearchRun.start, claim or native execution.','The just-accepted420-reference closure and previous unchanged matrices were not repeated; only actual final binding, review, admission and new reviewer artifacts were authenticated.','No claim of capacity, throughput, freshness of samples, successful activation, financial performance or writer exclusion.']}
out=H/'EXACT_LAUNCH_RELEASE01.json'
with out.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':'accepted','release':ref(out),'evidence_count':len(refs),'added':len(refs)-420},sort_keys=True))
