"""Finite metadata-only Root adaptation of accepted36 to unused38/110.

No admission, claim, runtime numerical imports, private dispatch decoding,
network operation or scientific data execution occurs here.
"""
import ast
import copy
import datetime
import difflib
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from tradingagents.research.admission import runtime_hashes
from tradingagents.research.onchain_replication.real_pilot_storage import WritableUnion
from tradingagents.research.onchain_replication.resources import mem_available

ROOT=Path.cwd().resolve(); HERE=Path(__file__).resolve().parent; F=HERE.parent
OLD=F/'real-data-pilot-full36-entry-preparation01-2026-10-11'
PUBLIC=F/'real-data-pilot-full38-binding-preparation01-2026-10-12'
CUMULATIVE=F/'real-data-pilot-full38-cumulative-preparation01-2026-10-12'
OLD_NAME='eth-paper-real-data-end-to-end-resource-20261011-36'
NAME='eth-paper-real-data-end-to-end-resource-20261012-38'
ANCHOR='1394d8b03163233df2fcefe658378e0f7b13424d'

def read(path):
    assert path.resolve(strict=True)==path and path.is_file() and not path.is_symlink()
    assert path.stat().st_nlink==1 and path.stat().st_size<=4*1024**2
    before=path.stat(); body=path.read_bytes(); after=path.stat()
    assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
    return body

def load(path):return json.loads(read(path))
def pin(path,*,size=True):
    body=read(path); result={'path':str(path.relative_to(ROOT)), 'sha256':hashlib.sha256(body).hexdigest()}
    if size:result['bytes']=len(body)
    return result
def save(name,value):
    body=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    with (HERE/name).open('xb') as stream:stream.write(body)
def text(name,body):
    with (HERE/name).open('x') as stream:stream.write(body)

def main():
    assert HERE==F/'real-data-pilot-full38-entry-preparation01-2026-10-12'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==ANCHOR
    assert not (HERE/'gate01.json').exists(), 'Root38 preparation already used'
    gate=load(OLD/'gate01.json'); original=copy.deepcopy(gate)
    experiment=copy.deepcopy(gate['experiments'][OLD_NAME])
    inputs=load(PUBLIC/'ALL_INPUT_REFS01.json'); assert len(inputs)==73
    # The accepted public binder deliberately leaves this Root-owned declaration
    # at its original public reference. Adapt only the exact experiment selector.
    scratch=load(OLD/'MATCHING_SCRATCH_RESERVATION01.json')
    assert scratch['experiment']==OLD_NAME
    scratch['experiment']=NAME; save('MATCHING_SCRATCH_RESERVATION01.json',scratch)
    inputs['matching_ordered_edge_scratch']={'dataset':'eth',**pin(HERE/'MATCHING_SCRATCH_RESERVATION01.json',size=False)}
    job=load(ROOT/inputs['execution_job']['path']); resources=job['resources']
    selected=next(iter(job['payload']['representation_jobs'].values()))
    experiment['cells']=[load(ROOT/inputs[selected['real_pilot_input']]['path'])['cell_id']]
    assert resources['storage_budget']['experiment']==NAME
    assert resources['memory_max_bytes']==6442450944 and resources['memory_high_bytes']==5368709120 and resources['wall_seconds']==28800
    assert resources['disk_floor_bytes']==10737418240 and resources['start_reserve_bytes']==2684354560
    observation=WritableUnion(resources['storage_budget'],ROOT,experiment=NAME).check()
    save('BASELINE_STORAGE_OBSERVATION01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':ANCHOR,'experiment':NAME,'host_mem_available_bytes':mem_available(),'disk_free_bytes':shutil.disk_usage(ROOT).free,'resources':resources,'storage_observation':observation,'qualification':'Actual read-only sampled current writable union and host availability, not whole-job peak, future usage, reservation or final release.'})
    pins=load(F/'pilot38-entry-capacity-investigation-2026-10-12/CURRENT_CAPACITY_SOURCE_PINS01.json')
    assert len(pins)==428
    for path,digest in pins.items():assert pin(ROOT/path)['sha256']==digest
    save('CAPACITY_SOURCE_MAP01.json',pins)
    core=load(OLD/'CORE_MANIFEST01.json')
    core['inputs']={role:pin(ROOT/inputs[role]['path']) for role in core['inputs']}
    core['builder_sha256']=pin(PUBLIC/'build_public01.py')['sha256']
    core['scope']=core['scope'].replace('fixed36','fixed38')
    save('CORE_MANIFEST01.json',core)
    public=load(OLD/'PUBLIC_MANIFEST01.json'); public.update(experiment=NAME,source_pins=pins)
    save('PUBLIC_MANIFEST01.json',public)
    capacity=load(OLD/'CAPACITY_DECLARATION_ROOT01.json')
    capacity.update(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),identity=NAME,source_anchor=ANCHOR,source_body_pins=pins)
    capacity['entry_qualification_only']['experiment_id']=NAME
    capacity['owned_paths']=[path.replace(OLD_NAME,NAME) for path in capacity['owned_paths']]
    capacity['basis']['prior_declaration']=pin(OLD/'CAPACITY_DECLARATION_ROOT01.json')
    capacity['basis']['currentness_sample']=pin(HERE/'BASELINE_STORAGE_OBSERVATION01.json')
    capacity['basis']['public_source_manifest']=pin(HERE/'CAPACITY_SOURCE_MAP01.json')
    capacity['basis']['source_adoption']=pin(F/'pilot-efficiency-integration-2026-10-12/SOURCE02.json')
    capacity['basis']['changed_source_review']=pin(F/'pilot38-integration-cumulative-review-2026-10-12/REVIEW_CLOSURE01.json')
    capacity['qualification']='Fixed38 conditional preparation-only declaration, refreshed428 current bodies at actual1394 anchor. Original growth/caps preserved. No MCM writer or training stage is admitted by this endpoint; whole39 requires a separate current full growth/capacity join. Sampled aggregate guards are not physical reservations or quotas.'
    assert capacity['full_pilot_capacity_admitted'] is False
    save('CAPACITY_DECLARATION_ROOT01.json',capacity)
    replacements=[(OLD_NAME,NAME),('full36-binding-preparation01-2026-10-11','full38-binding-preparation01-2026-10-12'),('f95f0bcb1d2fa0d98f681963332fa9710d7a679b4f490454db257d5577f9a20d','16dca252c1d0e8e73070e5a2136e458eecc73c7ae026332cf19ae377452dbc41'),('budget108','budget110'),('preparation36','preparation38'),('!=108','!=110'),("'effective_attempt_budget':108","'effective_attempt_budget':110")]
    for oldname,newname in [('preflight36_01.py','preflight38_01.py'),('root_io36_01.py','root_io38_01.py')]:
        before=read(OLD/oldname).decode(); after=before
        for old,new in replacements:after=after.replace(old,new)
        after=after.replace('from preflight36_01 import','from preflight38_01 import')
        ast.parse(after); text(newname,after)
        text(newname+'.diff',''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(OLD/oldname),tofile=str(HERE/newname))))
    # Preserve every original definition. Only the newly added experiment gets
    # refreshed source/runtime/body pins and the genuine110 extension/review.
    changed={}
    for path,digest in experiment['source_files'].items():
        actual=pin(ROOT/path)['sha256']
        if actual!=digest:changed[path]={'previous':digest,'current':actual}
    old_pins=load(OLD/'PUBLIC_MANIFEST01.json')['source_pins']
    assert len(changed)==6
    assert set(changed)==set(p for p in pins if pins[p]!=old_pins[p])
    for path,value in changed.items():experiment['source_files'][path]=value['current']
    source_dirs=[PUBLIC,CUMULATIVE,F/'pilot38-public-binding-review-2026-10-12',F/'pilot38-integration-cumulative-review-2026-10-12',F/'pilot38-entry-capacity-investigation-2026-10-12',F/'pilot36-outcome-review-2026-10-12',F/'pilot-efficiency-integration-2026-10-12']
    for directory in source_dirs:
        for path in sorted(directory.rglob('*')):
            if path.is_file():experiment['source_files'][str(path.relative_to(ROOT))]=pin(path)['sha256']
    for name in ['prepare_entry01.py','MATCHING_SCRATCH_RESERVATION01.json','BASELINE_STORAGE_OBSERVATION01.json','CAPACITY_SOURCE_MAP01.json','CORE_MANIFEST01.json','PUBLIC_MANIFEST01.json','CAPACITY_DECLARATION_ROOT01.json','preflight38_01.py','root_io38_01.py','preflight38_01.py.diff','root_io38_01.py.diff']:
        experiment['source_files'][str((HERE/name).relative_to(ROOT))]=pin(HERE/name)['sha256']
    experiment.update(inputs=inputs,parent=None,runtime_hashes=runtime_hashes(),charter=pin(CUMULATIVE/'CHARTER01.md'),cumulative_budget_extension={'extension':pin(CUMULATIVE/'EXTENSION_PROPOSED110_01.json',size=False),'review':pin(F/'pilot38-integration-cumulative-review-2026-10-12/EXTENSION110_REVIEW01.json',size=False)},question='Qualify the genuine first-graph serial preparation after the accepted generic-policy correction, actual observer correction, size-read reduction, GAT local-lifetime correction and same-boundary value coalescing. Stop before any MCM stage through registered EntryPreparationComplete under unchanged60000ms and physical/native policy; retain actual FAILED/spent outer disposition. Only an accepted and recovered genuine component qualifies the separate whole39 pilot; no financial fit is granted.')
    assert NAME not in gate['experiments']; gate['experiments'][NAME]=experiment
    assert {k:v for k,v in gate.items() if k!='experiments'}=={k:v for k,v in original.items() if k!='experiments'}
    assert {k:v for k,v in gate['experiments'].items() if k!=NAME}==original['experiments']
    save('gate01.json',gate)
    mapping=load(F/'pilot38-entry-capacity-investigation-2026-10-12/BINDING_FIELD_MAP01.json')['available_actual_fields']
    binding=load(OLD/'BINDING01.json'); binding.update(identity=NAME,status='DRAFT_NOT_RELEASED_REAL_RECOVERY_AND_FINAL_REVIEW_REQUIRED')
    for role,value in mapping.items():
        if role!='input_refs':binding[role]=value
    for role,name in [('core_manifest','CORE_MANIFEST01.json'),('public_manifest','PUBLIC_MANIFEST01.json'),('capacity_observation','CAPACITY_DECLARATION_ROOT01.json'),('gate','gate01.json')]:binding[role]=pin(HERE/name)
    binding['input_refs']={role:{key:value[key] for key in ('path','sha256')} for role,value in inputs.items()}
    binding['public_review']=pin(F/'pilot38-public-binding-review-2026-10-12/PUBLIC_BINDING_REVIEW01.json')
    binding['integration_review']=pin(F/'pilot38-integration-cumulative-review-2026-10-12/REVIEW_CLOSURE01.json')
    prior=pin(F/'pilot36-outcome-review-2026-10-12/OUTCOME_REVIEW01.json')
    binding['prior_outcome_review']=prior;binding['prior_root_closure_review']=prior
    for role in ['binding_review','complete_increment_recovery','new_increment_recovery_review','prior_preservation_complete','prior_recovery_review']:binding[role]=None
    save('BINDING_DRAFT01.json',binding)
    save('REGISTRATION_DRAFT01.json',{'status':'DRAFT_NOT_RELEASED','identity':NAME,'original_gate':pin(OLD/'gate01.json'),'new_gate':pin(HERE/'gate01.json'),'scientific_and_native_inputs_preserved':True,'all_original_experiment_definitions_preserved':True,'changed_source_pins':changed,'unchanged_prior_source_pins':909-6,'current_source_pins':len(experiment['source_files']),'input_roles':73,'root_scratch_identity_override':pin(HERE/'MATCHING_SCRATCH_RESERVATION01.json'),'actual_new_recovery':None,'final_release':None,'claim':False,'execution':False})
    print(json.dumps({'status':'DRAFT_NOT_RELEASED','identity':NAME,'source_pins':len(experiment['source_files']),'input_roles':73,'claim':False,'execution':False}))

if __name__=='__main__':main()
