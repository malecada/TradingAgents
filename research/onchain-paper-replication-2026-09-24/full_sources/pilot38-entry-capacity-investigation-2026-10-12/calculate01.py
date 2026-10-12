"""Read-only source/metadata adaptation map. No Git, claims or runtime imports."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3]
E=F/'real-data-pilot-full36-entry-preparation01-2026-10-11'
B=F/'real-data-pilot-full38-binding-preparation01-2026-10-12'
O=F/'real-data-pilot-full36-binding-preparation01-2026-10-11'
read=lambda p:json.loads(p.read_bytes())
ref=lambda p:{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
capacity=read(E/'CAPACITY_DECLARATION_ROOT01.json');pins=capacity['source_body_pins'];current={k:hashlib.sha256((R/k).read_bytes()).hexdigest() for k in pins}
changed={k:{'prior36':pins[k],'current':current[k]} for k in pins if pins[k]!=current[k]}
assert len(pins)==428 and len(changed)==6
(P/'CURRENT_CAPACITY_SOURCE_PINS01.json').write_text(json.dumps(current,indent=2)+'\n')
old=read(O/'ALL_INPUT_REFS01.json');new=read(B/'ALL_INPUT_REFS01.json');assert len(old)==len(new)==73 and set(old)==set(new)
roles={k:{'prior36':old[k],'actual38':new[k],'body_hash_changed':old[k]['sha256']!=new[k]['sha256']} for k in new if old[k]!=new[k]}
job36=read(R/old['execution_job']['path']);job38=read(R/new['execution_job']['path']);name36='eth-paper-real-data-end-to-end-resource-20261011-36';name38='eth-paper-real-data-end-to-end-resource-20261012-38'
assert json.dumps(job36['resources'],sort_keys=True).replace(name36,name38)==json.dumps(job38['resources'],sort_keys=True)
mcm=read(R/new['mcm_policy']['path']);assert mcm['entry_qualification']['experiment_id']==name38
fields={'preparation':ref(B/'PREPARED01.json'),'public_preparation':ref(B/'MANIFEST01.json'),'public_refs':ref(B/'PUBLIC_INPUT_REFS_DRAFT01.json'),'transport_binding':ref(B/'BOUND01.json'),'binding_readback':ref(B/'BINDING_CHECK01.json'),'unbound_archive':ref(B/'public01/archive_policy.json'),'budget_review':{k:v for k,v in ref(F/'pilot38-integration-cumulative-review-2026-10-12/EXTENSION110_REVIEW01.json').items() if k!='bytes'},'transport':read(B/'BINDING_CHECK01.json')['actual_opaque_input']['archive_transport'],'input_refs':new}
(P/'BINDING_FIELD_MAP01.json').write_text(json.dumps({'status':'REFERENCE_MAPPING_ONLY_NOT_BINDING_OR_APPROVAL','identity':name38,'available_actual_fields':fields,'new_reviewed_fields_still_required':['binding_review','core_manifest','public_manifest','public_review','capacity_observation','gate','complete_increment_recovery','new_increment_recovery_review','prior_outcome_review','prior_root_closure_review','prior_preservation_complete','prior_recovery_review']},indent=2)+'\n')
source_anchor=read(B/'ROOT_PREPARATION01.json')['source_anchor']
summary={'status':'SOURCE_METADATA_ONLY_NOT_CAPACITY_ADMISSION','source_anchor_from_actual38_preparation_not_independently_git_verified':source_anchor,'prior36_source_count':len(pins),'prior35_source_count':len(read(F/'real-data-pilot-full35-entry-preparation01-2026-10-11/CAPACITY_DECLARATION_ROOT01.json')['source_body_pins']),'changed_source_pins':changed,'unchanged_source_count':len(pins)-len(changed),'changed_input_refs':roles,'changed_content_roles':[k for k,v in roles.items() if v['body_hash_changed']],'path_only_roles':[k for k,v in roles.items() if not v['body_hash_changed']],'unchanged_role_count':len(new)-len(roles),'resource_caps_identical_after_experiment_path_rename':True,'actual38_resources':job38['resources'],'entry_selection':mcm['entry_qualification'],'capacity_terms_inherited_for_root_redeclaration_only':{k:capacity[k] for k in ('new_logical_growth_bytes','new_allocated_growth_bytes','non_directory_new_allocated_growth_bytes','new_entries','directory_allocated_bound_bytes','other_writer_reserved_bytes')},'no_full39_capacity':True,'refs':{p.name:ref(p) for p in (E/'CAPACITY_DECLARATION_ROOT01.json',E/'preflight36_01.py',B/'PREPARED01.json',B/'BOUND01.json',B/'ALL_INPUT_REFS01.json')}}
(P/'REFRESH_MAP01.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ('prior36_source_count','prior35_source_count','unchanged_source_count','changed_content_roles','path_only_roles','unchanged_role_count','resource_caps_identical_after_experiment_path_rename')},indent=2))
