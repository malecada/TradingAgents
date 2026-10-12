"""Authenticate the actual finite binding request without numerical imports."""
import ast, hashlib, json, os, stat
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;F=HERE.parent
ENTRY=F/'real-data-pilot-full38-entry-preparation01-2026-10-12'
NAME='eth-paper-real-data-end-to-end-resource-20261012-38'
evidence={};sizes={}
def digest(p):
    before=p.stat();h=hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda:stream.read(65536),b''):h.update(b)
    after=p.stat()
    signature=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    assert signature(before)==signature(after)
    return h.hexdigest()
def authenticate(ref):
    relative=ref['path'];p=ROOT/relative
    assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
    assert not {'keys','apis','.env','hf_token.txt'}&set(p.parts)
    assert p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1
    assert digest(p)==ref['sha256'],relative
    if 'bytes' in ref:assert p.stat().st_size==ref['bytes']
    assert relative not in evidence or evidence[relative]==ref['sha256']
    evidence[relative]=ref['sha256'];sizes[relative]=p.stat().st_size
    return p
def read(ref):return json.loads(authenticate(ref).read_bytes())
def direct(p):return {'path':str(p.relative_to(ROOT)),'sha256':digest(p),'bytes':p.stat().st_size}

request_ref=direct(ENTRY/'BINDING_REQUEST03.json')
assert request_ref['sha256']=='597589404cef978e32863f61442b340ef6bb7a9a90c32ed0e1c7e8e4a9937192'
request=read(request_ref);b=request['binding']
assert request['identity']==b['identity']==NAME and b['schema_version']==1
assert [k for k,v in b.items() if v is None]==['binding_review']
for k,v in b.items():
    if isinstance(v,dict) and {'path','sha256'}<=set(v):authenticate(v)
for k,v in request.items():
    if isinstance(v,dict) and {'path','sha256'}<=set(v):authenticate(v)
gate=read(b['gate']);experiment=gate['experiments'][NAME]
assert len(experiment['source_files'])==1036
for p,d in experiment['source_files'].items():authenticate({'path':p,'sha256':d})
actual={r:{k:v[k] for k in ('path','sha256')} for r,v in experiment['inputs'].items()}
assert len(actual)==73 and actual==b['input_refs'] and all(set(v)=={'path','sha256'} for v in actual.values())
for ref in actual.values():authenticate(ref)
transport=ROOT/b['transport']['path'];s=transport.stat();parent=transport.parent.stat()
assert s.st_size==930 and stat.S_IMODE(s.st_mode)==0o600 and s.st_uid==os.getuid()
assert stat.S_IMODE(parent.st_mode)==0o700 and parent.st_uid==os.getuid()
assert b['transport']['sha256']==actual['archive_transport']['sha256']=='267cc1d38f13245afdf27fc40fb4333ebbf775857ade36ec6fa3007f95929983'
assert b['budget_review']==experiment['cumulative_budget_extension']['review']
assert set(b['budget_review'])=={'path','sha256'}
for v in experiment['cumulative_budget_extension'].values():authenticate(v)
runtime={p.name:digest(p) for p in (ROOT/'tradingagents/research').glob('*.py')};assert runtime==experiment['runtime_hashes']
job=read(actual['execution_job']);selected=next(iter(job['payload']['representation_jobs'].values()));pilot=read(actual[selected['real_pilot_input']])
assert experiment['cells']==[pilot['cell_id']]==['real-eth-first-graph-entry-preparation-resource38']
metadata=read(request['actual_job_metadata_admission'])
for v in metadata['raw'].values():authenticate(v)
assert metadata['exit_code']==0 and metadata['claim'] is False and metadata['native_launched'] is False
returned_metadata=read(metadata['raw']['stdout'])
assert returned_metadata['ready'] is True and returned_metadata['effective_attempt_budget']==110
assert returned_metadata['source_pins']==1036 and returned_metadata['input_roles']==73
assert returned_metadata['registered_cells']==experiment['cells']
prior=read(b['prior_recovery_review']);new=read(b['new_increment_recovery_review'])
assert prior['decision']==new['decision']=='accepted'
assert new['baseline33_return_review_sha256']==b['prior_recovery_review']['sha256']
assert new['corrected_gate_sha256']==b['gate']['sha256']
assert new['corrected_generator_sha256']==experiment['source_files'][str((ENTRY/'prepare_entry01.py').relative_to(ROOT))]
assert new['cell_correction_review_sha256']==request['supplemental_changed_entry_review']['sha256']
assert prior['original36_review_sha256']==b['prior_outcome_review']['sha256']==b['prior_root_closure_review']['sha256']
for review,role in ((prior,'prior_preservation_complete'),(new,'complete_increment_recovery')):
    assert review['evidence'][b[role]['path']]['sha256']==b[role]['sha256']
    for p,v in review['evidence'].items():authenticate({'path':p,**v})
assert new['source']==request['source_anchor']=='0d4b1a9b294a4b0a484fbd2a1d7e27f8257738ec'
assert new['actual_returned_admission02']==returned_metadata
assert prior['regular_files']==430 and prior['directories']==62 and new['regular_files']==74 and new['directories']==9
assert prior['operation_count']==new['operation_count']==13
capacity=read(b['capacity_observation']);public=read(b['public_manifest']);pins=read(direct(ENTRY/'CAPACITY_SOURCE_MAP01.json'))
assert len(pins)==428 and pins==capacity['source_body_pins']==public['source_pins']
assert all(experiment['source_files'][p]==d for p,d in pins.items())
assert capacity['source_anchor']=='1394d8b03163233df2fcefe658378e0f7b13424d'
assert capacity['full_pilot_capacity_admitted'] is False and capacity['entry_qualification_only']['experiment_id']==NAME
core=read(b['core_manifest'])
for role,v in core['inputs'].items():assert read(v)==read(actual[role])
entry_review=read(direct(F/'pilot38-entry-registration-review-2026-10-12/ENTRY_REGISTRATION_REVIEW01.json'))
cell_review=read(request['supplemental_changed_entry_review'])
for filename in ('preflight38_01.py','root_io38_01.py'):
    p=ENTRY/filename;assert digest(p)==entry_review['evidence'][str(p.relative_to(ROOT))];authenticate(direct(p))
for p,d in cell_review['evidence'].items():authenticate({'path':p,'sha256':d})
assert b['gate']['sha256']=='cd22da5d2d036b54e9f7d17af64d9d51e331e5e7b503d3123acc7c46e9de1489'
result={'decision':'accepted-known-reference-joins','request':request_ref,'identity':NAME,'source_anchor':request['source_anchor'],'input_refs':actual,'source_count':1036,'capacity_source_count':428,'registered_cells':experiment['cells'],'binding_self_review_only_null':True,'opaque_envelope':{'bytes':930,'mode':'0600','parent_mode':'0700','decoded':False},'original36_and_old_gate_recovery_scope':{'regular_files':430,'directories':62,'review_sha256':b['prior_recovery_review']['sha256']},'corrected_gate_recovery_scope':{'regular_files':74,'directories':9,'review_sha256':b['new_increment_recovery_review']['sha256']},'actual_prior_metadata_ready':returned_metadata,'evidence':evidence,'evidence_sizes':sizes,'qualification':'Current byte/ref joins and accepted independent33/34 review reuse; no fresh remote operation, archive replay, native/runtime/numerical import, claim or final eligibility check. Local committed capacity ancestry is a separate check.'}
print(json.dumps(result,indent=2,sort_keys=True))
