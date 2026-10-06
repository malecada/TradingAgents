"""Read-only entry checks for the fixed fourth real-data pilot graph."""
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
NAME='eth-paper-real-pilot-graph-20220523-20261005-01'
GATE=str((HERE/'gate01.json').relative_to(ROOT))


def preceding_storage(inputs):
    """Require actual COMPLETE May16 BYTE backup and exact two-path retirement."""
    backup='research/onchain-paper-replication-2026-09-24/storage/real-pilot-third-graph-preservation-20261006-01'
    identity=Path(backup).name
    expected={'storage_complete':'complete.json','storage_recovered_complete':'recovered-complete.json',
        'storage_selection':'selection01.json','storage_native_final':'guard01/final.json',
        'storage_outer_exit':'outer-exit01.json','storage_root_terminal':'ROOT_TERMINAL01.json',
        'storage_restore':'11-restore.json','storage_recovered_restore':'11-recovered-restore.json',
        'storage_kept':'11-kept.json','storage_body_get_receipt':'11-recovered.bin.transport.json'}
    def read(role):
        ref=inputs[role];q=Path(ref['path']);p=ROOT/q
        if (q.is_absolute() or '..' in q.parts or p.resolve(strict=True)!=p or not p.is_file()
                or p.stat().st_nlink!=1 or p.stat().st_size>4*1024**2 or file_hash(p)!=ref['sha256']):
            raise ValueError('exact bounded preceding proof differs: '+role)
        if role in expected and ref['path']!=backup+'/'+expected[role]:raise ValueError('fixed backup role differs')
        return json.loads(p.read_bytes())
    review=read('storage_closure_review')
    if review['decision']!='accepted' or review['identity']!=identity or review['full_scope_byte_recovery'] is not True:
        raise ValueError('independent actual full36 BYTE acceptance required')
    for role in expected:
        ref=inputs[role]
        if review['evidence'].get(ref['path'])!=ref['sha256']:raise ValueError('independent backup evidence join differs')
    complete=read('storage_complete');selected=read('storage_selection')
    if (complete!=read('storage_recovered_complete') or complete['identity']!=identity
            or selected['identity']!=identity or complete['selection']!=selected
            or complete['count']!=36 or len(complete['files'])!=36 or selected['count']!=36
            or len(selected['files'])!=36 or len(selected['directories'])!=8
            or complete['bytes_preserved']!=selected['total_bytes']
            or complete['originals_retained'] is not True or complete['recoveries_retained'] is not True):
        raise ValueError('actual complete selected36 names/modes/bytes differ')
    if len({r['path'] for r in selected['files']})!=36:raise ValueError('duplicate original membership')
    for original,record in zip(selected['files'],complete['files']):
        if any(record[k]!=v for k,v in original.items()):raise ValueError('original/complete membership differs')
    if sum(r['bytes'] for r in selected['files'])!=selected['total_bytes']:raise ValueError('selected byte denominator differs')
    final=read('storage_native_final');outer=read('storage_outer_exit');root=read('storage_root_terminal')
    if ((ROOT/backup/'failed.json').exists() or (ROOT/backup/'failed.json').is_symlink()
            or final['phase']!='complete' or final['child_exit_code']!=0 or final['cleanup_verified'] is not True
            or outer['entry_selected_exit_code']!=0 or outer['guard_child_exit_code']!=0 or outer['cleanup_verified'] is not True
            or root['identity']!=identity or root['actual_root_tool_exit_code']!=0
            or Path(final['cgroup']).exists() or Path('/proc',str(final['monitor_pid'])).exists()):
        raise ValueError('actual native/outer/Root zero and cleanup required')
    pids=root['selected_recorded_pids']
    if not isinstance(pids,list) or not pids or any(type(pid) is not int or pid<=0 or Path('/proc',str(pid)).exists() for pid in pids):
        raise ValueError('actual selected recorded PIDs must be absent')
    kept=read('storage_kept');restore=read('storage_restore');get=read('storage_body_get_receipt')
    paths=['research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220516-20261005-01/aggregation/ledger.sqlite',backup+'/11-recovered.bin']
    if (complete['files'][11]!=kept or kept['path']!=paths[0] or kept['bytes']!=3310923776
            or restore!=read('storage_recovered_restore') or any(kept[k]!=v for k,v in restore.items())
            or kept['body_roundtrip_verified'] is not True or kept['original_retained'] is not True or kept['recovered_body_retained'] is not True
            or get['status']!='complete' or get['returncode']!=0
            or not (get['expected_bytes']==get['received_bytes']==kept['bytes'])):
        raise ValueError('exact ledger11 fullget/restoration join differs')
    retired=read('storage_retirement_complete');terminal=read('storage_retirement_root_exit')
    if (retired['identity']!='real-pilot-third-graph-ledger-retirement-20261006-01'
            or retired['payload_bytes_retired']!=6621847552 or retired['removed']!=paths
            or retired['preservation_backup']!=identity or retired['remote_restore']!=kept
            or retired['arrays_retained'] is not True or retired['all_other_originals_and_recoveries_retained'] is not True
            or terminal['actual_root_exit_code']!=0 or terminal['complete_sha256']!=inputs['storage_retirement_complete']['sha256']):
        raise ValueError('actual exact third-ledger retirement differs')
    for relative in paths:
        p=ROOT/relative
        if p.exists() or p.is_symlink():raise ValueError('retired payload reappeared: '+relative)
    return {'backup':identity,'retired_bytes':6621847552,'retired_paths':paths}


def check():
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
