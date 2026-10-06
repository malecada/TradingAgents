"""Seven-count declaration delta; no fictitious baseline or resolved residuals."""
import hashlib,json,types,ast
from pathlib import Path
HERE=Path(__file__).resolve().parent
base=json.loads((HERE.parent/'DECLARATION_DRAFT01.json').read_text());a=base['source_derived'];Q=a['stage_variables']['Q'];R=a['stage_variables']['R'];T=a['stage_variables']['G'];M=8192;ops=8*(1+R)
# Execute only pure scalar definitions extracted from candidate; no package import.
p=HERE/'candidate/archive_read_control_capacity.py';tree=ast.parse(p.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('policy','capacity') or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'POLICY','ROLE_BYTES','FRAME_OVERHEAD'} for t in n.targets)]
def require(v,m):
    if not v:raise ValueError(m)
ns={'require':require};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns)
cap=ns['capacity'](Q,ns['POLICY']);writer=(7*Q+8)*M;stage=cap['logical_bytes']+40*T+8*M
newarchive=(4+3*ops+8)*M+8*(writer+8*M+R*stage)
oldarchive=a['archive_policy']['max_workflow_metadata_bytes']
oldfiles=4+3*ops+8+8*((7*Q+8)+8+R*((3*Q+8)+9))
newfiles=4+3*ops+8+8*((7*Q+8)+8+R*(cap['files']+9))
olddirs=1+ops+8*(5+2*Q+R*(5+Q))
newdirs=1+ops+8*(5+2*Q+R*(5+cap['directories']))
known=base['known_reservation_conflict']['subtotal_logical_bytes']-oldarchive+newarchive
batches=sum(x['batch_count'] for x in a['by_week'].values());streams=5*batches+35;attempts=a['typed_chunk_credits'];ledgerfiles=a['typed_file_slots']
remaining_known=(streams+42)*M+max(3*8388608,max(x['selected_payload_overlap_upper_bytes'] for x in a['by_week'].values()))
res=base['residual_domains'];known_res=sum(res[k]['logical_bytes']+res[k]['additional_scratch_bytes'] for k in ('checkpoint_retention','import_owner_stage_journal'))
files=streams+42+4*attempts+ledgerfiles+newfiles+a['history_bounds']['control_files']+a['history_bounds']['diagnostic_files']+7+6+sum(res[k]['regular_files']+res[k]['scratch_files'] for k in ('checkpoint_retention','import_owner_stage_journal'))
dirs=21+2*batches+28+attempts+newdirs+2+2+sum(res[k]['directories'] for k in ('checkpoint_retention','import_owner_stage_journal'))
logical=known+remaining_known+known_res
# Preserve earlier proposals explicitly without treating them as source bounds.
proposals=base['prospective_reservations_not_source_bounds'];proposed_logical=sum(v['logical_bytes'] for v in proposals.values());proposed_files=sum(v['regular_files'] for v in proposals.values());proposed_dirs=sum(v['directories'] for v in proposals.values())
fs=json.loads((HERE.parent.parent/'real-data-pilot-current-graph-counts05-2026-10-06/INPUT_DRAFT01.json').read_text())['protocol']['filesystem']
def overhead(f,d):return f*(fs['allocation_unit_bytes']-1+fs['per_regular_inode_overhead_bytes'])+d*fs['per_directory_allocated_bytes']+fs['extra_allocated_bytes']
result={'status':'DRAFT_CANDIDATE_NOT_ADMITTED','policy':ns['POLICY'],'unchanged':{'Q':Q,'R':R,'G':T,'stages':8,'typed':a['typed_max_control_bytes'],'transport':a['transport_limits'],'resources':a['resources_unchanged']},'read_capacity':cap,'new_archive_policy':a['archive_policy']|{'read_controls':ns['POLICY'],'max_read_metadata_bytes':cap['logical_bytes'],'max_stage_bytes':stage,'max_workflow_metadata_bytes':newarchive},'delta':{'old_archive_logical_bytes':oldarchive,'new_archive_logical_bytes':newarchive,'saved_logical_bytes':oldarchive-newarchive,'old_archive_file_slots':oldfiles,'new_archive_file_slots':newfiles,'old_archive_directory_slots':olddirs,'new_archive_directory_slots':newdirs},'known_new_reservations_without_two_unknown_residuals':{'logical_bytes':logical,'regular_files':files,'directories':dirs,'allocated_model_bytes':logical+overhead(files,dirs),'entries_with_extra':files+dirs+fs['extra_entries']},'conditional_example_NOT_CAPACITY':{'basis':'Unchanged earlier lifecycle/cache proposals; genuine seven array-byte metadata3496602912 alone, NOT full writable baseline. No admission.', 'logical_plus_array_bytes_and_proposals':logical+3496602912+proposed_logical,'allocated_model_plus_array_bytes_and_proposals':logical+3496602912+proposed_logical+overhead(files+proposed_files,dirs+proposed_dirs),'entries_before_actual_baseline':files+dirs+proposed_files+proposed_dirs+fs['extra_entries']},'remaining':['Actual fresh complete writable baseline (array-byte metadata is not baseline).','Source-proven/enforced lifecycle and native cache bounds, failure controls and scratch.','Independent source/ABI/packed inverse review and final current closure/admission.','Actual5-second scan-time adequacy remains unproven; fewer entries does not prove timing.'],'candidate_source_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(HERE/'ARITHMETIC02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('read_capacity','delta','known_new_reservations_without_two_unknown_residuals','conditional_example_NOT_CAPACITY')},indent=2))
