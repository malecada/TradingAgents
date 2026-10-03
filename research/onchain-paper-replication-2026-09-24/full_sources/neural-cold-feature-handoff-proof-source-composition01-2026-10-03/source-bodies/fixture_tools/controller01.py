"""Fail-closed controller interface; no subprocess execution entrypoint in preparation."""
from pathlib import Path
import hashlib,json
GIB=1024**3
LIMITS={'memory_max_bytes':3*GIB,'memory_high_bytes':3*GIB,'memory_swap_max_bytes':0,'reserve_bytes':3*GIB,'start_reserve_bytes':6*GIB,'wall_seconds':1800,'file_size_bytes':4194304,'disk_floor_bytes':10*GIB,'max_allocated_bytes':GIB,'max_logical_bytes':GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}
CASES={'success':'original-import-native-success-20261003-01','second_target_publication_failure':'original-import-native-publication-failure-20261003-01'}

def require(value,message):
    if not value:raise ValueError(message)

def command(spec,case):
    require(spec['status']=='released-native-engineering' and spec['remaining']==[],'preparation is not an execution grant')
    require(spec['limits']==LIMITS and case in CASES,'finite native protocol differs')
    source=spec['capsule_commit'];require(type(source) is str and len(source)==40 and all(c in '0123456789abcdef' for c in source),'committed capsule required')
    root=Path(spec['capsule_root']);require(root.is_absolute() and root.resolve()==root and (root/'.git').is_dir() and not (root/'.git').is_symlink(),'genuine isolated committed root required')
    require(spec['program_id']=='original-dictionary-import-engineering-2026-10-02' and spec['mechanism_id']=='original-dictionary-import-engineering-v1','separate engineering family required')
    identity=CASES[case];require(not (root/'research_runs'/identity).exists(),'never reuse claimed identity')
    require(not (root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/identity).exists(),'never reuse launched identity')
    return [spec['runtime']['executable'],'-B','-m','tradingagents.research.onchain_replication.job','--mode','launch','--root',str(root),'--registration',spec['registration'],'--experiment',identity,'--source',source]

def validate_terminal(spec,case,observed):
    """All values are mandatory; caller must authenticate raw paths/joins first."""
    require(case in CASES and observed['identity']==CASES[case],'case identity differs')
    require(observed['source_commit']==spec['capsule_commit'],'source differs')
    require(observed['native_controls']=={'memory.max':str(3*GIB),'memory.high':str(3*GIB),'memory.swap.max':'0'},'native controls differ')
    require(observed['unit_file_limits']==[4194304,4194304] and observed['worker_file_limits']==[4194304,4194304] and observed['coordinator_file_limits']==[4194304,4194304],'file limits missing/differ')
    require(observed['before_claim_receipt'] is True and observed['cleanup_verified'] is True and observed['cgroup_absent'] is True and observed['all_recorded_pids_absent'] is True,'claim/control/cleanup proof absent')
    require(observed['storage_breach'] is False and observed['storage_error'] is None and observed['cleanup_error'] is None and observed['logs_truncated'] is False,'native envelope failed')
    require(observed['final_inventory_complete'] is True and observed['final_free_bytes']>=10*GIB and observed['final_allocated_bytes']<=GIB and observed['final_logical_bytes']<=GIB,'final owned inventory differs')
    expected=['complete','complete'] if case=='success' else ['complete','failed']
    require(observed['cell_statuses']==expected and observed['original_motif_count']==32 and observed['target_nodes']==[2,3],'fixed genuine denominator differs')
    require(observed['lifecycle_status']==('complete' if case=='success' else 'failed'),'failure fixture cannot upgrade lifecycle')
    require(observed['first_artifact_preserved'] is True and observed['real_binding_owner_route'] is True,'original target/authority proof missing')
    return {'operational_proof':'passed','empirical_authority':False,'expected_failure':case!='success'}

if __name__=='__main__':
    raise SystemExit('Source-only controller preparation: exact registration, source review and coordinator release required; no execution entrypoint.')
