"""Read-only entry checks for the fixed second real-data pilot graph."""
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
NAME='eth-paper-real-pilot-graph-20220509-20261005-01'
GATE=str((HERE/'gate01.json').relative_to(ROOT))


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
    prior=json.loads((ROOT/admission.inputs['storage_closure_review']['path']).read_bytes())
    if prior['decision']!='accepted':raise ValueError('actual preceding full BYTE recovery not accepted')
    retired=json.loads((ROOT/admission.inputs['storage_retirement_complete']['path']).read_bytes())
    terminal=json.loads((ROOT/admission.inputs['storage_retirement_root_exit']['path']).read_bytes())
    if (retired['identity']!='real-pilot-first-graph-ledger-retirement-20261006-01'
            or retired['payload_bytes_retired']!=6571245568 or len(retired['removed'])!=2
            or terminal['actual_root_exit_code']!=0 or retired['arrays_retained'] is not True):
        raise ValueError('actual preceding ledger retirement differs')
    for relative in retired['removed']:
        path=ROOT/relative
        if path.exists() or path.is_symlink():raise ValueError('retired payload reappeared: '+relative)
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
