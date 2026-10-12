"""Read only finite public metadata and source bodies; never arrays or live scans."""
import hashlib,json
from pathlib import Path
from capacity import LIMITS,graph_growth,project
D=Path(__file__).resolve().parent;F=D.parent;R=F.parents[2];pins={}
def load(p):
 p=Path(p);b=p.read_bytes();assert len(b)<2*1024**2;pins[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return json.loads(b)
def save(name,v):(D/name).write_text(json.dumps(v,indent=2)+'\n')
b=F/'real-data-pilot-full38-binding-preparation01-2026-10-12';refs=load(b/'PUBLIC_INPUT_REFS_DRAFT01.json');typed=load(b/'public01/typed_payload.json');mcm=load(b/'public01/mcm_policy.json');pilot=load(b/'public01/pilot.json');old=load(F/'pilot37-continuation-capacity-2026-10-11/CAPACITY01.json');memory=load(F/'pilot37-training-memory-investigation-2026-10-11/SIZES01.json');old_inputs=memory['observed'];writer_join={}
for leaf in ('batched_continuation.py','batched_journal.py','batched_numeric_execution.py','compact_mcm_batched.py','grouped_offload.py','grouped_offload_semantics.py','typed_payload_operations.py','archive_control_history.py'):
 p=R/'tradingagents/research/onchain_replication'/leaf;raw=p.read_bytes();key=str(p.relative_to(R));pins[key]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()};writer_join[key]=pins[key]==old['source_pins'][key]
graphs={};input_join={}
for key,role in pilot['graph_inputs'].items():
 pin=refs[role];p=R/pin['path'];manifest=load(p);assert pins[pin['path']]['sha256']==pin['sha256'] and manifest['graph_hash']==key
 input_join[key]=old_inputs[pin['path']]['sha256']==pin['sha256'];v=typed['graphs'][key];a=manifest['arrays'];bundle=v['kinds']['mcm-batched-bundle-v3']
 graphs[key]={'nodes':v['rows'],'motifs':32,'output_bytes':v['kinds']['mcm-output-f32']['max_preserved_bytes'],'bundle_chunk_bytes':bundle['chunk_bytes'],'bundle_preserved_bytes':bundle['max_preserved_bytes'],'bundle_recovered_bytes':bundle['max_recovered_bytes'],'bundle_operations':bundle['max_operations'],'bundle_chunks':bundle['max_chunks'],'original_parent_bytes':sum(x['bytes'] for x in a.values()),'edge_index_file_bytes':a['edge_index']['bytes'],'node_features_file_bytes':a['node_features']['bytes'],'manifest_pin':pin}
metadata={'source_route':'whole39-from38-remove-entry-stop-only','batch_cells':mcm['batched']['batch_cells'],'group_batches':mcm['batched']['group_batches'],'journal_body_bytes':mcm['batched']['max_body_bytes'],'continuation_manifest_input':mcm['batched']['continuation']['manifest_input'],'graph_manifest_inputs':mcm['batched']['continuation']['graph_manifest_inputs'],'graphs':graphs,'storage_writer_sources_unchanged':all(writer_join.values()),'original_input_manifest_pins_unchanged':all(input_join.values()),'writer_join':writer_join,'input_join':input_join}
save('WHOLE_METADATA01.json',metadata)
# Exact route output is raw f32; graph source inputs are read-only existing stores.
# Any new file-based header/edge copy must be explicitly added to these terms.
terms={'review_status':'conditional-dated','observation_sha256':None,'limits':LIMITS,'base_entry_bound':650016,'directory_allocated_bytes':2147549184,'directory_entries':101559,'directory_evidence':'DATED conditional inherited2GiB+64KiB declaration; expanded marker directory headroom requires Root final acceptance','other_writer_logical_bytes':1073741824,'other_writer_allocated_bytes':1073741824,'other_writer_entries':0,'other_writer_evidence':'DATED inherited1GiB allowance; 650016 base entry budget already includes previous writer aggregate; Root must supply current explicit additional entries','additional_headers_edges_logical_bytes':0,'additional_headers_edges_allocated_bytes':0,'additional_headers_edges_entries':0,'additional_headers_edges_evidence':'Existing unchanged graph NPY arrays remain read-only. compact_mcm_output uses raw matrix.f32; output manifest covered by sidecars; original journal headers included in92+53cells/group; new copies require recalculation.','other_new_logical_bytes':0,'other_new_allocated_bytes':0,'other_new_entries':0}
save('CONDITIONAL_TERMS01.json',terms)
obs=load(F/'real-data-pilot-full38-entry-preparation01-2026-10-12/BASELINE_STORAGE_OBSERVATION01.json');obs.update(kind='dated-pre38-only',post38_closed_and_recovered=False,source_and_scope_current=False,free_inodes=None,filesystem_identity=None,observation_sha256=pins[str((F/'real-data-pilot-full38-entry-preparation01-2026-10-12/BASELINE_STORAGE_OBSERVATION01.json').relative_to(R))]['sha256'])
save('DATED_OBSERVATION01.json',obs)
calculated=graph_growth(metadata);assert {x['graph']:x['cells'] for x in calculated}=={x['graph']:x['cells'] for x in old['graphs']}
save('CONDITIONAL_PROJECTION01.json',project(metadata,obs,terms,conditional=True));save('INPUT_SOURCE_PINS01.json',pins)
print(json.dumps({'writer_joins':writer_join,'graph_count':len(graphs),'cells':sum(x['cells'] for x in calculated)}))
