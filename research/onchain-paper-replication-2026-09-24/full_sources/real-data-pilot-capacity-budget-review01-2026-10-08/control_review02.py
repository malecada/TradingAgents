import json,hashlib,copy
from pathlib import Path
F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
O=F/'real-data-pilot-capacity-budget-review01-2026-10-08'
A=F/'real-data-pilot-capacity-selection02-2026-10-08';B=F/'real-data-pilot-capacity-selection03-2026-10-08'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
v=read(B/'CONTROL_SELECTION01.json');assert sha(B/'CONTROL_SELECTION01.json')=='1d34ff8c337877948a941d6a7fad518171c734ec64643c258535f21edaf504c2'
for ref in [v['base_manifest'],v['selected_source_review'],*v['policies'].values()]:assert sha(Path(ref['path']))==ref['sha256']
a=read(A/'compact_policy.json');b=read(B/'compact_policy.json');old=read(A/'CAPACITY_SELECTION01.json')
d=2*(64*1024**2-16384);assert d==134184960
expected=copy.deepcopy(a);p=expected['stage_policy']['restart_retention'];p['max_selected_input_json_bytes']=64*1024**2
for k in ('max_input_bytes','max_live_bytes','max_cumulative_bytes'):p[k]+=d
expected['stage_policy']['max_retained_logical_bytes']+=d
expected['max_workflow_retained_logical_bytes']+=7*d
assert b==expected
for n in ('mcm_policy.json','pair_limits.json'):assert (A/n).read_bytes()==(B/n).read_bytes()
assert v['global_retention_domain_logical_bytes']==old['candidate_retention_global_reservation_bytes']+7*d
assert v['workflow_logical_bytes']==b['max_workflow_retained_logical_bytes']
for vk,pk in [('max_input_bytes','max_input_bytes'),('stage_live_bytes','max_live_bytes'),('stage_cumulative_bytes','max_cumulative_bytes')]:assert v[vk]==p[pk]
assert v['selected_input_capacity_is_proven'] is False
pair=b['stage_policy']['pair'];q=(pair['max_pair_entries_override']+pair['checkpoint_layout']['chunk_entries']-1)//pair['checkpoint_layout']['chunk_entries'];assert q==33
n=4*q;constant=15+2+2*(n+3)+12+2*n;assert constant==563
G=b['stage_policy']['schedule']['max_total_checkpoints'];S=min(p['max_stores'],G)
result={'status':'ACCEPT_EXACT_PROSPECTIVE_CONTROL_DELTA_ONLY_RESIDUAL_FILE_INVENTORY_CORRECTION_REQUIRED','selection_sha256':sha(B/'CONTROL_SELECTION01.json'),'separate_writer_review_sha256':v['selected_source_review']['sha256'],'delta_per_stage':d,'delta_seven_stages':7*d,'unchanged_numeric_policies':True,'selected_input_actual_capacity_proven':False,'residuals02_correction':{'shards_per_array':q,'numeric_files_per_snapshot':n,'complete_files_per_snapshot':n+3,'old_regular_files':7*(10*G+9*S+51),'conservative_corrected_regular_files':7*(10*G+9*S+constant),'old_scratch_files':8,'corrected_scratch_files':2*n,'unchanged_scratch_bytes':2*pair['max_checkpoint_bytes'],'unchanged_directories':7*(11+S+4*G)},'scope':'metadata-only; no numerical imports, source-body self-review, claims, real arrays, native jobs or budget matrix rerun'}
(O/'CONTROL_SELECTION_REVIEW02.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
