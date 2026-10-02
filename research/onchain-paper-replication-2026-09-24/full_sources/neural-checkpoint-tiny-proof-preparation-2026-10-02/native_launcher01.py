"""One reviewed bounded checkpoint proof; no financial or empirical admission."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import resource
import runpy
import stat
import subprocess
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
IDENTITY='neural-checkpoint-comparison-20261002-01'
HELPER=HERE.parent/'neural-streamed-integration-2026-10-02/adapter_launcher04.py'
GIB=1024**3
LIMITS={'memory_max_bytes':GIB,'memory_high_bytes':GIB,'memory_swap_max_bytes':0,
        'reserve_bytes':3*GIB,'start_reserve_bytes':4*GIB,'wall_seconds':120,
        'disk_floor_bytes':10*GIB,'file_limit_bytes':4*1024**2,
        'allocated_stop_bytes':64*1024**2,'logical_stop_bytes':64*1024**2}


def require(value,message):
    if not value: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def helper():
    spec=importlib.util.spec_from_file_location('reviewed_checkpoint_guard_helpers',HELPER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def metadata(path,maximum=1024**2):
    info=path.lstat()
    require(path.resolve()==path and stat.S_ISREG(info.st_mode) and info.st_nlink==1
            and info.st_size<=maximum,'bounded original regular metadata required')
    return json.loads(path.read_bytes())


def verify(spec):
    require(spec['schema_version']==1 and spec['status']=='released_single_tiny_engineering_attempt', 'exact source release required')
    require(spec['identity']==IDENTITY and spec['limits']==LIMITS,'identity/limits differ')
    require(spec['coordinator_file']=='coordinator01.py','unexpected proof coordinator')
    require(sys.prefix==str(ROOT/'.venv') and platform.python_version()=='3.13.13','pinned interpreter required')
    require(not any(name in sys.modules for name in ('torch','numpy')),'numerical import before release')
    versions={d.metadata['Name']:d.version for d in importlib.metadata.distributions() if d.metadata['Name']}
    require(versions==spec['installed_distribution_versions'],'installed distribution versions differ')
    total=0
    for name,expected in spec['source_files'].items():
        path=ROOT/name; info=path.lstat();total+=info.st_size
        require(path.resolve()==path and path.is_relative_to(ROOT) and stat.S_ISREG(info.st_mode)
                and info.st_nlink==1 and info.st_size<=4*1024**2 and total<=16*1024**2,
                'source path/type/link/extent differs')
        require(sha(path)==expected,'selected source changed: '+name)
    require(sha(__file__)==spec['launcher_sha256'],'launcher source differs')
    require(sha(HERE/'source-manifest01.json')==spec['proof_manifest_sha256'],'proof source manifest differs')
    require(sha(HELPER)==spec['guard_helper_sha256'],'reviewed guard helper differs')


def validate(result,owned,spec,head,h):
    ready=metadata(owned/'guard/cpu_ready.json');child=metadata(owned/'guard/child_exit.json')
    native=metadata(owned/'native-unit-controls.json');report=metadata(owned/'workload/terminal.json')
    proof={'cpu_ready':ready,'child_exit':child}
    require(h._cleanup_complete(result,proof),'actual guard cleanup unresolved')
    require(result['phase']=='complete' and result['child_exit_code']==child['exit_code']==0,
            'guard/child not complete')
    require(result['limit_reason'] is None and result['retry'] is False and result['elapsed_time_kill'] is False,
            'guard failed/limited/retried')
    require(0<=result['elapsed_seconds']<=120,'wall envelope differs')
    for key in ('memory_max_bytes','memory_high_bytes','memory_swap_max_bytes','reserve_bytes',
                'start_reserve_bytes','wall_seconds','disk_floor_bytes'):
        require(type(result[key]) is int and result[key]==LIMITS[key],'native policy differs: '+key)
    controls={'memory.max':str(GIB),'memory.high':str(GIB),'memory.swap.max':'0'}
    require(result['kernel_controls']==controls,'kernel hard controls differ')
    for group in ('initial_memory_events','memory_events'):
        require(all(type(value) is int and value==0 for value in result[group].values()),'kernel event/unknown occurred')
        require({'high','max','oom','oom_kill','oom_group_kill'}<=set(result[group]),'required events unavailable')
    require(child['snapshot_error'] is None and child['reason']=='workload exited','child snapshot missing')
    require(child['terminal_memory_snapshot']==result['terminal_memory_snapshot'],'terminal snapshots differ')
    require(native['LimitFSIZE']==native['LimitFSIZESoft']=='4194304'
            and native['RuntimeMaxUSec'] in ('2min','120s','120000000'),'native file/wall limits differ')
    require('/sys/fs/cgroup'+native['ControlGroup']==result['cgroup']
            and native['MainPID']==str(ready['pid']),'native unit identity differs')
    require(len(result['cpus'])==2 and result['cpus']==ready['cpus']
            and ready['file_size_limit']==[4194304,4194304],'CPU/file ready readback differs')
    require(result['cpu_enforcement']=='inherited two-CPU affinity with per-thread cgroup readback','CPU enforcement differs')
    require(all(value==result['cpus'] for value in result['cpu_thread_readback'].values()),'thread affinity differs')
    require(report['status']=='passed' and report['run_id']==IDENTITY and report['error'] is None
            and report['active_child_pid'] is None and report['cleanup_owner']=='outer-native-guard',
            'coordinator not complete')
    protocol=metadata(HERE/'protocol01.json')
    require([arm['mode'] for arm in report['arms']]==protocol['modes'],'arm denominator/order differs')
    pids={ready['pid'],child['workload_pid'],*(int(pid) for pid in result['cpu_thread_readback'])}
    for arm in report['arms']:
        require(arm['status']=='exited' and type(arm['pid']) is int and arm['pid']>0
                and type(arm['returncode']) is int and arm['returncode']==0,'arm exit failed or unknown')
        pids.add(arm['pid']);directory=owned/'workload'/arm['mode']
        outcome=metadata(directory/'terminal.json');intent=metadata(directory/'intent.json')
        require(outcome['status']=='passed' and outcome['mode']==arm['mode'] and outcome['run_id']==IDENTITY
                and outcome['source_commit']==head and outcome['manifest_sha256']==spec['proof_manifest_sha256'],
                'arm outcome identity/status differs')
        require(intent['protocol_sha256']==sha(HERE/'protocol01.json') and intent['native']['cgroup']==result['cgroup']
                and intent['native']['controls']==controls and intent['native']['cpus']==result['cpus']
                and intent['native']['file_limit_bytes']==4194304,'actual arm native/source intent differs')
        for suffix in ('.started.json','.exited.json'):
            record=metadata(owned/'workload'/(arm['mode']+suffix))
            require(record['pid']==arm['pid'] and record['mode']==arm['mode'],'arm PID receipt differs')
        log=owned/'workload'/(arm['mode']+'.log');info=log.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<4194304,'arm log capped/aliased')
    require(not Path(result['cgroup']).exists() and all(not Path('/proc',str(pid)).exists() for pid in pids),
            'owned descendant remains')
    limits={'max_allocated_bytes':64*1024**2,'max_logical_bytes':64*1024**2,
            'max_entries':12000,'max_depth':32,'max_scan_seconds':2}
    require(result['storage_budget']=={'root':str(owned),'limits':limits},'complete owned storage watch differs')
    require(set(result['disk_free_bytes'])=={str(owned)}
            and all(value>=10*GIB for value in result['disk_free_bytes'].values()),'disk floor differs')
    for key in ('storage_breach','storage_last_error','cleanup_error','child_log_limit_reached','log_truncated','truncated_logs'):
        require(key not in result,'guard diagnostic forbids completion: '+key)
    return {'arm_pids':sorted(pids),'modes':protocol['modes'],
            'qualification':'Tiny actual model correctness/profile proof only. Separate fresh arms; sampled cgroup current and cumulative unit peak are distinct from instrumented saved backing storage. No fullgraph/financial capacity or memory-reduction threshold inferred.'}


def worker(path,spec):
    owned=HERE/'owned'/IDENTITY;head=metadata(owned/'reservation.json')['head']
    os.chdir(HERE);sys.path.insert(0,str(ROOT))
    script=HERE/spec['coordinator_file']
    sys.argv=[str(script),'--owned',str(owned/'workload'),'--source-commit',head,
              '--run-id',IDENTITY,'--manifest-sha256',spec['proof_manifest_sha256']]
    runpy.run_path(str(script),run_name='__main__')


def launch(path,spec,expected):
    owned=HERE/'owned'/IDENTITY
    require(not os.path.lexists(owned),'identity active, terminal or reserved; no retry')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=10).strip()
    for name,value in spec['source_files'].items():
        body=subprocess.check_output(['git','show',head+':'+name],cwd=ROOT,timeout=10)
        require(hashlib.sha256(body).hexdigest()==value,'selected committed body differs')
    require(subprocess.check_output(['git','ls-remote','origin','refs/heads/research/onchain-paper-replication-2026-09-24'],
            cwd=ROOT,text=True,timeout=30).split()[0]==head,'actual remote HEAD differs')
    h=helper();(HERE/'owned').mkdir(exist_ok=True);owned.mkdir(mode=0o700)
    h.immutable(owned/'reservation.json',{'identity':IDENTITY,'head':head,'release_sha256':expected,
                'started_utc':datetime.now(timezone.utc).isoformat(),'paper_claim':False,'financial_fit':False})
    for name in ('tmp','cache'): (owned/name).mkdir()
    environment={'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(owned/'tmp'),
        'XDG_CACHE_HOME':str(owned/'cache'),'TORCH_HOME':str(owned/'cache/torch'),
        'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2',
        'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTEST_PLUGINS':'','PYTEST_ADDOPTS':''}
    resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304))
    sys.path.insert(0,str(ROOT))
    from tradingagents.research.onchain_replication import resources
    real=resources.subprocess
    def run(command,**kwargs):
        if command[0]!='systemd-run': return real.run(command,**kwargs)
        changed=[command[0],'--property=LimitFSIZE=4194304','--property=RuntimeMaxSec=120s',
                 *['--setenv='+key+'='+value for key,value in sorted(environment.items())],*command[1:]]
        answer=real.run(changed,**kwargs)
        unit=next(value.split('=',1)[1] for value in command if value.startswith('--unit='))
        response=real.run(['systemctl','--user','show',unit,
            '--property=LimitFSIZE,LimitFSIZESoft,RuntimeMaxUSec,CPUQuotaPerSecUSec,ControlGroup,MainPID'],
            check=True,capture_output=True,text=True,timeout=10)
        props=dict(line.split('=',1) for line in response.stdout.splitlines() if '=' in line)
        h.immutable(owned/'native-unit-controls.json',props)
        require(props.get('LimitFSIZE')==props.get('LimitFSIZESoft')=='4194304'
                and props.get('RuntimeMaxUSec') in ('2min','120s','120000000'),'native controls missing')
        return answer
    result=None;primary=None;proof=None
    resources.subprocess=SimpleNamespace(run=run,Popen=real.Popen)
    try:
        result=resources.guarded_run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker',str(path),expected],
            cwd=HERE,receipt_dir=owned/'guard',memory_max_bytes=GIB,memory_high_bytes=GIB,
            memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=4*GIB,
            wait_seconds=0,wall_seconds=120,sample_seconds=.25,disk_paths=[owned],disk_floor_bytes=10*GIB,
            storage_budget={'root':str(owned),'limits':{'max_allocated_bytes':64*1024**2,
                'max_logical_bytes':64*1024**2,'max_entries':12000,'max_depth':32,'max_scan_seconds':2}})
        verify(spec);require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==head,'HEAD moved')
        proof=validate(result,owned,spec,head,h)
    except BaseException as error: primary=error
    finally: resources.subprocess=real
    try:
        h.immutable(owned/'launcher-terminal.json',{'identity':IDENTITY,'status':'passed' if primary is None else 'failed',
            'error':None if primary is None else repr(primary)[:4096],'head':head,'proof':proof,
            'guard_phase':None if result is None else result.get('phase'),
            'cleanup_verified':False if result is None else result.get('cleanup_verified',False),
            'retry':False,'finished_utc':datetime.now(timezone.utc).isoformat()})
    except BaseException as error:
        fatal=lambda value:isinstance(value,MemoryError) or not isinstance(value,Exception)
        if primary is None: primary=error
        elif fatal(error) and not fatal(primary): error.__cause__=primary;primary=error
        else: primary.add_note('terminal receipt failure: '+type(error).__name__)
    if primary is not None: raise primary
    return 0


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('--run','--worker'))
    parser.add_argument('spec',type=Path);parser.add_argument('sha256')
    args=parser.parse_args(['--',*sys.argv[1:]])
    path=args.spec.absolute();require(sha(path)==args.sha256,'release SHA differs')
    spec=metadata(path);verify(spec)
    return launch(path,spec,args.sha256) if args.mode=='--run' else worker(path,spec)


if __name__=='__main__': raise SystemExit(main())
