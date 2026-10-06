"""Read-only entry checks for the DRAFT fixed sixth real-data pilot graph."""
from pathlib import Path
from types import SimpleNamespace
import datetime
import json
import shutil
import subprocess

from tradingagents.research.onchain_replication.job import _admitted, PREFIX
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.resources import mem_available
from tradingagents.research.onchain_replication.workflow_storage import StorageWatch

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
NAME='eth-paper-real-pilot-graph-20220606-20261005-01'
GATE=str((HERE/'gate01.json').relative_to(ROOT))


def preceding_storage(inputs):
    """Exact May9 FAILED backup + successful metadata union + actual retirement."""
    def read(role):
        info=inputs[role];path=ROOT/info['path']
        if path.resolve(strict=True)!=path or not path.is_relative_to(ROOT) or not path.is_file() or path.stat().st_size>4*1024**2 or file_hash(path)!=info['sha256']:
            raise ValueError('preceding compact proof changed: '+role)
        return json.loads(path.read_bytes())
    prior=read('storage_closure_review')
    union_id='real-pilot-second-graph-preservation-metadata-20261006-01'
    old_id='real-pilot-second-graph-preservation-20261006-01'
    if prior['decision']!='accepted' or prior['identity']!=union_id or prior['full_scope_byte_recovery'] is not True:
        raise ValueError('actual preceding full union BYTE recovery not accepted')
    for role in ('storage_complete','storage_recovered_complete','storage_native_final','storage_outer_exit'):
        info=inputs[role]
        if prior['evidence'].get(info['path'])!=info['sha256']:raise ValueError('independent union receipt join differs')
    union=read('storage_complete');selected=read('storage_selection')
    if (union!=read('storage_recovered_complete') or union['identity']!=union_id
            or union['parent']!=old_id or union['parent_status']!='FAILED'
            or union['count']!=36 or len(union['files'])!=36 or selected['count']!=36 or len(selected['files'])!=36
            or union['fresh_body_transfers']!=0 or union['fresh_restoration_metadata_rows']!=[35]
            or union['bytes_preserved']!=selected['total_bytes'] or union['directories']!=selected['directories']):
        raise ValueError('actual full36 metadata-only composition differs')
    for inherited,record in zip(selected['files'],union['files']):
        if any(record[k]!=v for k,v in inherited.items()):raise ValueError('union original membership differs')
    failed=read('storage_failed_closure_review');old_ref=inputs['storage_failed_closure_review']
    if (union['parent_proof']['review']['path']!=old_ref['path'] or union['parent_proof']['review']['sha256']!=old_ref['sha256']
            or failed['decision']!='accepted-failed-parent-partial-byte-evidence' or failed['identity']!=old_id
            or failed['parent_status']!='failed' or failed['authenticated_body_get_count']!=36):
        raise ValueError('old FAILED body proof differs')
    for role in ('storage_selection','storage_failed_native_final','storage_failed_outer_exit','storage_failed_root_terminal','storage_restore','storage_recovered_restore','storage_kept','storage_body_get_receipt'):
        info=inputs[role]
        if failed['evidence'].get(info['path'])!=info['sha256']:raise ValueError('independent failed-parent receipt join differs')
    old_final=read('storage_failed_native_final');old_outer=read('storage_failed_outer_exit');old_root=read('storage_failed_root_terminal')
    if (old_final['phase']!='failed' or old_final['child_exit_code'] is not None or old_final['cleanup_verified'] is not True
            or old_outer['entry_selected_exit_code']!=1 or old_outer['guard_child_exit_code'] is not None
            or old_root['actual_root_tool_exit_code']!=1 or old_root['separate_actual_worker_exit_code']!=-15
            or Path(old_final['cgroup']).exists() or Path('/proc',str(old_final['monitor_pid'])).exists()):
        raise ValueError('permanent FAILED old parent/cleanup differs')
    final=read('storage_native_final');outer=read('storage_outer_exit')
    if (final['phase']!='complete' or final['child_exit_code']!=0 or final['cleanup_verified'] is not True
            or outer['entry_selected_exit_code']!=0 or outer['guard_child_exit_code']!=0 or outer['cleanup_verified'] is not True
            or Path(final['cgroup']).exists() or Path('/proc',str(final['monitor_pid'])).exists()):
        raise ValueError('actual NEW preservation union/native cleanup differs')
    restore=read('storage_restore');kept=read('storage_kept');get=read('storage_body_get_receipt')
    if (restore!=read('storage_recovered_restore') or union['files'][11]!=kept
            or any(kept[k]!=v for k,v in restore.items()) or kept['bytes']!=3599704064
            or get['status']!='complete' or get['returncode']!=0 or not (get['expected_bytes']==get['received_bytes']==kept['bytes'])):
        raise ValueError('old ledger11 restoration/get join differs')
    retired=read('storage_retirement_complete');terminal=read('storage_retirement_root_exit')
    expected_paths=['research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220509-20261005-01/aggregation/ledger.sqlite',
                    'research/onchain-paper-replication-2026-09-24/storage/'+old_id+'/11-recovered.bin']
    if (kept['path']!=expected_paths[0] or retired['identity']!='real-pilot-second-graph-ledger-retirement-20261006-01'
            or retired['payload_bytes_retired']!=7199408128 or retired['removed']!=expected_paths
            or retired['preservation_union']!=union_id or retired['old_preservation_parent_status']!='FAILED'
            or retired['remote_restore']!=kept or retired['arrays_retained'] is not True
            or retired['all_other_originals_and_recoveries_retained'] is not True or terminal['actual_root_exit_code']!=0):
        raise ValueError('actual preceding second-ledger retirement differs')
    for relative in expected_paths:
        path=ROOT/relative
        if path.exists() or path.is_symlink():raise ValueError('retired payload reappeared: '+relative)
    return {'parent_status':'FAILED','union':union_id,'retired_bytes':7199408128,'retired_paths':expected_paths}


def check():
    raise ValueError('DRAFT_NOT_RELEASED: actual May30 BYTE recovery, retirement and fresh storage/gate binding required')
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    release_path=HERE/'RELEASE_REVIEW01.json'
    release=json.loads(release_path.read_bytes())
    if release.get('decision')!='accepted':raise ValueError('exact source/entry review missing')
    for relative,expected in release['evidence'].items():
        path=ROOT/relative
        if file_hash(path)!=expected:raise ValueError('reviewed entry changed: '+relative)
        committed=subprocess.check_output(['git','show',source+':'+relative],cwd=ROOT)
        if committed!=path.read_bytes():raise ValueError('reviewed entry not committed: '+relative)
    if subprocess.check_output(['git','show',source+':'+str(release_path.relative_to(ROOT))],cwd=ROOT)!=release_path.read_bytes():
        raise ValueError('source/entry review itself not committed')
    args=SimpleNamespace(root=ROOT,registration=GATE,experiment=NAME,source=source)
    admission,job=_admitted(args)
    if not admission.ready or admission.effective_attempt_budget!=71:raise ValueError('exact pilot admission/budget differs')
    for relative,expected in admission.experiment['source_files'].items():
        if file_hash(ROOT/relative)!=expected:raise ValueError('source pin changed: '+relative)
    for info in admission.inputs.values():
        path=ROOT/info['path']
        if path.stat().st_size>4*1024**2 or file_hash(path)!=info['sha256']:
            raise ValueError('compact input pin changed: '+info['path'])
    if inventory(ROOT)!=json.loads((ROOT/admission.inputs['environment']['path']).read_bytes()):raise ValueError('installed runtime inventory differs')
    for path in (ROOT/'research_runs'/NAME,ROOT/PREFIX/'runs'/NAME,ROOT/PREFIX/'sources'/NAME,HERE/'launch-attempt01.json',HERE/'outer-exit01.json'):
        if path.exists() or path.is_symlink():raise ValueError('fixed namespace already reserved: '+str(path))
    units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True)
    if units.strip():raise ValueError('another native resource process is active')
    for claim_path in (ROOT/'research_runs').glob('*/claim.json'):
        claim=json.loads(claim_path.read_bytes())
        if claim.get('program_id')==admission.spec['program_id'] and not any((claim_path.parent/name).exists() for name in ('complete.json','failed.json')):
            raise ValueError('another program claim is active: '+str(claim_path.parent))
    preceding_storage(admission.inputs)
    extent=json.loads((HERE/'RAW_EXTENT01.json').read_bytes()); count=0
    for member in extent['daily_members']:
        if file_hash(ROOT/member['mapping_path'])!=member['mapping_sha256']:raise ValueError('daily map changed')
        for segment in member['segments']:
            path=Path(segment['path']); info=path.lstat()
            if path.is_symlink() or not path.is_file() or (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)!=(segment['device'],segment['inode'],segment['bytes'],segment['mtime_ns'],segment['ctime_ns']):
                raise ValueError('original raw extent changed: '+str(path))
            count+=1
    policy=json.loads((HERE/'STORAGE_POLICY01.json').read_bytes())
    for candidate in policy['scratch_scope']['sqlite_temp_candidates']:
        path=Path(candidate)
        if path.exists() and path.stat().st_dev!=ROOT.stat().st_dev:raise ValueError('SQLite temp candidate outside guarded volume')
    storage=StorageWatch(**job['resources']['storage_budget']).check()
    free=shutil.disk_usage(ROOT).free; available=mem_available()
    if free<policy['startup_free_requirement_bytes']:raise ValueError('full projected source/scratch plus disk floor unavailable')
    if available<job['resources']['start_reserve_bytes']:raise ValueError('frozen startup RAM reserve unavailable')
    return args,{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':source,'experiment':NAME,
        'registration_sha256':file_hash(HERE/'gate01.json'),'release_sha256':file_hash(release_path),'effective_attempt_budget':71,
        'source_pins':len(admission.experiment['source_files']),'compact_input_pins':len(admission.inputs),
        'original_raw_extents_stat_only':count,'host_mem_available_bytes':available,'free_disk_bytes':free,
        'startup_free_requirement_bytes':policy['startup_free_requirement_bytes'],'storage_observation':storage,
        'qualification':'Read-only source/metadata/namespace/resource check; original raw hashes are enforced inside the genuine source worker. Projection is an estimate. No empirical body, claim or result was opened.'}


if __name__=='__main__':print(json.dumps(check()[1],sort_keys=True))
