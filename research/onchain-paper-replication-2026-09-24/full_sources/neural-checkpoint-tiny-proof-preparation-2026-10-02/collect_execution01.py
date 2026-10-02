"""Metadata-only closure; preserve failed launcher and passed numeric components.

No numerical imports, checkpoint deserialization, replay, source mutation or retry.
The original ready receipt is never supplemented with a synthetic file field.
"""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import sys
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OWNED=HERE/'owned/neural-checkpoint-comparison-20261002-01'

def require(value,message):
    if not value:raise RuntimeError(message)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while raw:=f.read(262144):h.update(raw)
    return h.hexdigest()

def write(path,value):
    with path.open('x') as f:json.dump(value,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')

spec=importlib.util.spec_from_file_location('closed_native_source_only',HERE/'native_launcher03.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
release=m.metadata(HERE/'release02.json');m.verify(release)
require('torch' not in sys.modules and 'numpy' not in sys.modules,'no numerical imports allowed')
reservation=m.metadata(OWNED/'reservation.json');head=reservation['head']
require(head=='09f2a2066a445d7399dac3165014e0ffd0019269','original execution commit differs')
for name,pin in release['source_files'].items():
    raw=subprocess.check_output(['git','show',head+':'+name],cwd=ROOT,timeout=10)
    require(hashlib.sha256(raw).hexdigest()==pin==sha(ROOT/name),'committed/current source differs')
g=m.metadata(OWNED/'guard/final.json');ready=m.metadata(OWNED/'guard/cpu_ready.json')
child=m.metadata(OWNED/'guard/child_exit.json');native=m.metadata(OWNED/'native-unit-controls.json')
parent=m.metadata(OWNED/'launcher-terminal.json');coordinator=m.metadata(OWNED/'workload/terminal.json')
intent=m.metadata(OWNED/'workload/intent.json');protocol=m.metadata(HERE/'protocol01.json')
require(parent['status']=='failed' and parent['error']=={'type':'KeyError'} and parent['proof'] is None,'original parent failure differs')
require(set(ready)=={'cpus','pid'},'original ready schema differs')
require(g['phase']=='complete' and g['child_exit_code']==child['exit_code']==0 and g['limit_reason'] is None
        and g['retry'] is False and g['elapsed_time_kill'] is False,'actual guard not complete')
require(g['cleanup_verified'] is True and g['cleanup_stop_returncode']==5,'actual cleanup differs')
require(g['terminal_memory_snapshot']==child['terminal_memory_snapshot'] and child['snapshot_error'] is None
        and child['reason']=='workload exited','native child snapshot differs')
require(all(g[k]==m.LIMITS[k] for k in ('memory_max_bytes','memory_high_bytes','memory_swap_max_bytes','reserve_bytes',
        'start_reserve_bytes','wall_seconds','disk_floor_bytes')),'actual policy differs')
require(0<g['elapsed_seconds']<=120 and g['cpus']==ready['cpus'] and len(g['cpus'])==2,'CPU/wall differs')
controls={'memory.max':'1073741824','memory.high':'1073741824','memory.swap.max':'0'}
require(g['kernel_controls']==controls and all(type(v) is int and v==0 for kind in ('initial_memory_events','memory_events')
        for v in g[kind].values()),'hard controls/events differ')
require(all({'high','max','oom','oom_kill','oom_group_kill'}<=set(g[k]) for k in ('initial_memory_events','memory_events')),'kernel events unknown')
require(native['LimitFSIZE']==native['LimitFSIZESoft']=='4194304' and native['RuntimeMaxUSec']=='2min'
        and '/sys/fs/cgroup'+native['ControlGroup']==g['cgroup'] and native['MainPID']==str(ready['pid']),
        'actual independent native unit/file/wall readback differs')
for props in (g['unit_properties'],g['cleanup_unit_properties']):
    require(props=={'ActiveState':'inactive','ControlGroup':'','ExecMainStatus':'0','Result':'success','SubState':'dead'},'unit terminal differs')
require(g['cpu_enforcement']=='inherited two-CPU affinity with per-thread cgroup readback'
        and all(cpus==g['cpus'] for cpus in g['cpu_thread_readback'].values()),'thread affinity differs')
require(coordinator['status']=='passed' and coordinator['error'] is None and coordinator['active_child_pid'] is None
        and coordinator['cleanup_owner']=='outer-native-guard','coordinator differs')
for receipt in (coordinator,intent):
    require(receipt['run_id']==m.IDENTITY and receipt['source_commit']==head
            and receipt['manifest_sha256']==release['proof_manifest_sha256'],'coordinator source identity differs')
expected_native={'cgroup':g['cgroup'],'controls':controls,'cpus':g['cpus'],'file_limit_bytes':4194304}
require(intent['native']==expected_native,'actual coordinator native/file readback differs')
require([arm['mode'] for arm in coordinator['arms']]==protocol['modes'],'actual arm denominator differs')
pids={g['monitor_pid'],ready['pid'],child['workload_pid'],*map(int,g['cpu_thread_readback'])}
arms=[];last_end=0
for arm in coordinator['arms']:
    mode=arm['mode'];directory=OWNED/'workload'/mode
    terminal=m.metadata(directory/'terminal.json');start=m.metadata(OWNED/'workload'/(mode+'.started.json'))
    end=m.metadata(OWNED/'workload'/(mode+'.exited.json'));arm_intent=m.metadata(directory/'intent.json')
    require(arm['status']=='exited' and arm['returncode']==0 and arm['pid']>0 and end==arm
            and start['pid']==arm['pid'] and start['mode']==mode and start['status']=='running','actual arm PID/exit receipt differs')
    require(arm['started_monotonic_ns']>=last_end and arm['ended_monotonic_ns']>arm['started_monotonic_ns'],'fresh sequential arm ordering differs')
    last_end=arm['ended_monotonic_ns'];pids.add(arm['pid'])
    for receipt in (terminal,arm_intent):
        require(receipt['mode']==mode and receipt['run_id']==m.IDENTITY and receipt['source_commit']==head
                and receipt['manifest_sha256']==release['proof_manifest_sha256'],'actual arm identity differs')
    require(terminal['status']=='passed' and arm_intent['protocol_sha256']==sha(HERE/'protocol01.json')
            and arm_intent['native']==expected_native,'arm native/file/protocol readback differs')
    m.validate_mode(directory,terminal,protocol,mode)
    arms.append({'mode':mode,'pid':arm['pid'],'cases':len(terminal['result']['cases']),
        'phase_markers':terminal['phases']['phase_markers'],'phase_sample_count':terminal['phases']['sample_count'],
        'max_phase_sampled_cgroup_current_bytes':max(row['max_memory_current_bytes'] for row in terminal['phases']['samples'].values()),
        'comparisons':len(terminal['result'].get('comparisons',[])),'bitwise_different_tensors':terminal['result'].get('bitwise_different_tensors'),
        'terminal_sha256':sha(directory/'terminal.json')})
m.validate_observations(g,OWNED,protocol)
require(len({arm['pid'] for arm in coordinator['arms']})==3,'fresh process identity differs')
require(all(type(pid) is int and pid>0 and not Path('/proc',str(pid)).exists() for pid in pids)
        and not Path(g['cgroup']).exists(),'original descendant or cgroup remains')
for k in ('storage_breach','storage_last_error','cleanup_error','child_log_limit_reached','log_truncated','truncated_logs'):
    require(k not in g,'guard diagnostic differs: '+k)
entries=[];logical=0;allocated=0
for path in [OWNED,*sorted(OWNED.rglob('*'))]:
    info=path.lstat();require(path.resolve()==path and len(path.relative_to(OWNED).parts)<=32,'original path/depth differs')
    kind='directory' if stat.S_ISDIR(info.st_mode) else 'regular' if stat.S_ISREG(info.st_mode) else None
    require(kind is not None and (kind!='regular' or info.st_nlink==1),'special file/alias found')
    allocated+=info.st_blocks*512
    row={'path':str(path.relative_to(OWNED)),'kind':kind,'mode':stat.S_IMODE(info.st_mode),'allocated_bytes':info.st_blocks*512}
    if kind=='regular':
        require(info.st_size<4194304,'file bound breached');logical+=info.st_size
        row.update(bytes=info.st_size,sha256=sha(path))
    entries.append(row)
require(logical<67108864 and allocated<67108864 and len(entries)<=12000,'complete original storage bound differs')
archive=HERE/'retained-execution01.tar.gz'
with tarfile.open(archive,'w:gz') as t:t.add(OWNED,arcname=OWNED.name,recursive=True)
inventory={'schema_version':1,'root':str(OWNED.relative_to(ROOT)),'entries':entries,'member_count':len(entries),
    'regular_files':sum(row['kind']=='regular' for row in entries),'directories':sum(row['kind']=='directory' for row in entries),
    'logical_bytes':logical,'allocated_bytes':allocated,'archive_file':archive.name,'archive_sha256':sha(archive)}
write(HERE/'retained-execution01.json',inventory)
result={'schema_version':1,'status':'failed_outer_validator_with_passed_components','identity':m.IDENTITY,'source_commit':head,
    'release_sha256':sha(HERE/'release02.json'),'parent_status':'failed','parent_exception':"KeyError('file_size_limit')",
    'numeric_and_profile_components':'passed','arms':arms,'native_guard_phase':g['phase'],'native_guard_child_exit_code':0,
    'native_elapsed_seconds':g['elapsed_seconds'],'peak_sampled_cgroup_current_bytes':g['peak_sampled_memory_current_bytes'],
    'all_known_pids':sorted(pids),'all_pids_absent':True,'original_cgroup_absent':True,'cleanup_verified':True,
    'retained_inventory_sha256':sha(HERE/'retained-execution01.json'),'retained_archive_sha256':sha(archive),
    'source_git_and_current_pins':len(release['source_files']),'installed_runtime_body_pins':len(release['runtime_files']),
    'numeric_replay_or_import':False,'retry':False,'paper_claim':False,'financial_fit':False,'verified_utc':datetime.now(timezone.utc).isoformat(),
    'qualification':'Original failed outer launcher remains failed. Separate retrospective metadata verifier authenticates original complete numeric/profile components and native unit/file/RLIMIT readbacks. cpu_ready genuinely lacks optional file_size_limit because no physical_policy was selected; no field was fabricated. No rerun or checkpoint deserialization. Tiny graphs do not prove fullgraph capacity; profiles are phase-sampled whole-cgroup current and cumulative unit peak includes prior arms; saved-hook backing observations are not process peaks.'}
write(HERE/'execution-result01.json',result)
print(json.dumps(result,sort_keys=True))
