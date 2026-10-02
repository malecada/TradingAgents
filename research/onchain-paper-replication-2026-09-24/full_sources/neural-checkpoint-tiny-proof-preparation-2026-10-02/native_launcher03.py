"""One reviewed bounded checkpoint proof; no financial or empirical admission."""
import argparse
import copy
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
    require(spec['coordinator_file']=='coordinator02.py','unexpected proof coordinator')
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
    require(set(spec['runtime_files'])=={'.venv/lib/python3.13/site-packages/torch/utils/checkpoint.py'},'exact installed checkpoint body required')
    require(set(spec['runtime_policy'])==set(spec['runtime_files']),'runtime metadata denominator differs')
    for name,expected in spec['runtime_files'].items():
        path=ROOT/name;info=path.lstat();policy=spec['runtime_policy'][name]
        require(path.resolve()==path and stat.S_ISREG(info.st_mode) and info.st_size==policy['bytes']
                and info.st_nlink==policy['nlink'] and stat.S_IMODE(info.st_mode)==policy['mode']
                and info.st_size<4194304 and sha(path)==expected,'installed runtime body/metadata differs')
    require(sha(__file__)==spec['launcher_sha256'],'launcher source differs')
    require(sha(HERE/'source-manifest02.json')==spec['proof_manifest_sha256'],'proof source manifest differs')
    require(sha(HELPER)==spec['guard_helper_sha256'],'reviewed guard helper differs')


def phase_names(protocol,mode):
    names=['numerical_import']
    if mode=='correctness':
        suffixes=['construct','forward','backward','optimizer','save','reload',
            'continue-original.forward','continue-original.backward','continue-original.optimizer',
            'continue-restored.forward','continue-restored.backward','continue-restored.optimizer','eval','no_grad']
        for case in protocol['cases']:
            for enabled in (False,True):
                label=case['name']+('.true' if enabled else '.false')
                names.extend(label+'.'+suffix for suffix in suffixes)
            names.append(case['name']+'.comparison_complete')
    else:
        for name in protocol['profile_cases']:
            names.extend(name+'.'+suffix for suffix in ['construct','forward','backward','optimizer','save','reload',
                'continuation-forward','continuation-backward','continuation-optimizer','complete'])
    return names+['complete']


def validate_mode(directory,outcome,protocol,mode):
    require(outcome['schema_version']==1 and outcome['error'] is None,'arm terminal schema/error differs')
    expected=[(case,enabled) for case in protocol['cases']
        if mode=='correctness' or case['name'] in protocol['profile_cases']
        for enabled in ((False,True) if mode=='correctness' else (mode=='profile_true',))]
    rows=outcome['result']['cases'];require(len(rows)==len(expected),'case denominator differs')
    core=metadata(ROOT/protocol['model_input'])
    for row,(case,enabled) in zip(rows,expected,strict=True):
        require(row['case']==case['name'] and type(row['checkpoint']) is bool and row['checkpoint'] is enabled,
                'case order/execution flag differs')
        config=copy.deepcopy(core);config['graph_activation_checkpointing']=enabled
        if mode=='correctness':config['gat_dropout']=case['dropout']
        expected_hash=hashlib.sha256((json.dumps(config,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()).hexdigest()
        require(row['config_sha256']==expected_hash,'derived config hash differs')
        checkpoint=Path(row['checkpoint_directory'])
        require(not checkpoint.is_absolute() and '..' not in checkpoint.parts,'checkpoint path escapes arm')
    names=phase_names(protocol,mode);phase=outcome['phases']
    require(type(phase['phase_markers']) is int and phase['phase_markers']==len(names),'phase denominator differs')
    require(type(phase['sample_count']) is int and 0<phase['sample_count']<=protocol['max_phase_samples'],'sample count differs')
    require(sum(row['samples'] for row in phase['samples'].values())==phase['sample_count'],'sample denominator differs')
    for name,row in phase['samples'].items():
        require(name in ['startup',*names] and type(row['samples']) is int and row['samples']>0
                and type(row['max_memory_current_bytes']) is int and 0<=row['max_memory_current_bytes']<=GIB,
                'sample schema/limit differs')
    require({path.name for path in directory.glob('phase-*.json')}=={f'phase-{i:04d}.json' for i in range(len(names))},
            'phase file denominator differs')
    last_time=0;last_peak=0
    for index,name in enumerate(names):
        marker=metadata(directory/f'phase-{index:04d}.json')
        require(marker['schema_version']==1 and type(marker['index']) is int and marker['index']==index
                and marker['mode']==mode and marker['phase']==name,'phase identity/order differs')
        require(type(marker['monotonic_ns']) is int and marker['monotonic_ns']>last_time,'phase time differs')
        current=marker['memory_current_bytes'];peak=marker['cumulative_cgroup_memory_peak_bytes']
        require(type(current) is int and type(peak) is int and 0<=current<=peak<=GIB and peak>=last_peak,
                'phase native memory observation differs')
        last_time=marker['monotonic_ns'];last_peak=peak


def validate_observations(result,owned,protocol):
    # These additional actual-result fields do not appear in minimal validator
    # control fixtures. They are mandatory before the launcher declares success.
    for mode in protocol['modes']:
        terminal=metadata(owned/'workload'/mode/'terminal.json')
        if mode!='correctness':continue
        evidence=terminal['result'];rows=evidence['cases']
        for row in rows:
            case=next(case for case in protocol['cases'] if case['name']==row['case'])
            require(row['recompute']=={'forward':case['graphs'],'backward':case['graphs'] if row['checkpoint'] else 0,'phase':'backward'},
                    'actual encode/recompute entry counts differ')
            storage=row['storage']
            require(type(storage['records']) is int and 0<storage['records']<=protocol['max_saved_records'],
                    'saved diagnostic record bound differs')
            require(type(storage['distinct_backing_bytes']) is int and 0<storage['distinct_backing_bytes']<=protocol['max_distinct_saved_bytes'],
                    'saved diagnostic backing storage bound differs')
        require(0<len(evidence['comparisons'])<=protocol['max_compare_records'],'actual tensor comparison denominator differs')
        require(evidence['bitwise_different_tensors']==sum(not row['bitwise_equal'] for row in evidence['comparisons']),
                'bitwise comparison count differs')
    storage_limits={'allocated_bytes':64*1024**2,'logical_file_bytes':64*1024**2,'entries':12000}
    for key,maximum in storage_limits.items():
        require(type(result['storage_peak_'+key]) is int and 0<=result['storage_peak_'+key]<=maximum,
                'owned storage peak differs')
    terminal=result['terminal_memory_snapshot']
    require(terminal['memory_events']==result['memory_events'],'actual terminal memory events differ')
    require(type(terminal['memory_current_bytes']) is int and 0<=terminal['memory_current_bytes']<=GIB,'actual terminal memory differs')
    require(type(result['peak_sampled_memory_current_bytes']) is int and 0<=result['peak_sampled_memory_current_bytes']<=GIB,
            'actual sampled memory peak differs')
    for receipt in (result['unit_properties'],result['cleanup_unit_properties']):
        require(receipt['Result']=='success' and receipt['ExecMainStatus']=='0'
                and receipt['ActiveState']=='inactive','actual native terminal outcome differs')
    for key,maximum in storage_limits.items():
        value=result['storage_observation'][key]
        require(type(value) is int and 0<=value<=result['storage_peak_'+key]<=maximum,'actual storage observation differs')
    log=owned/'guard/child.log';info=log.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<4194304,'native child log capped/aliased')


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
    coordinator_intent=metadata(owned/'workload/intent.json')
    for receipt in (report,coordinator_intent):
        require(receipt['run_id']==IDENTITY and receipt['source_commit']==head
                and receipt['manifest_sha256']==spec['proof_manifest_sha256'],'coordinator source/manifest identity differs')
    require(coordinator_intent['native']=={'cgroup':result['cgroup'],'controls':controls,'cpus':result['cpus'],'file_limit_bytes':4194304},
            'coordinator native identity differs')
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
        require(intent['mode']==arm['mode'] and intent['run_id']==IDENTITY and intent['source_commit']==head
                and intent['manifest_sha256']==spec['proof_manifest_sha256'],'arm intent identity differs')
        validate_mode(directory,outcome,protocol,arm['mode'])
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
    io_spec=importlib.util.spec_from_file_location('frozen_checkpoint_terminal_boundary',HERE/'oracle02.py')
    io=importlib.util.module_from_spec(io_spec);io_spec.loader.exec_module(io)
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
        validate_observations(result,owned,metadata(HERE/'protocol01.json'))
    except BaseException as error: primary=error
    finally: resources.subprocess=real
    def assemble(selected):
        return {'identity':IDENTITY,'status':'passed' if selected is None else 'failed',
            'error':None if selected is None else {'type':type(selected).__name__},'head':head,'proof':proof,
            'guard_phase':None if result is None else result.get('phase'),
            'cleanup_verified':False if result is None else result.get('cleanup_verified',False),
            'retry':False,'finished_utc':datetime.now(timezone.utc).isoformat()}
    return io.terminal_boundary(primary,None,assemble,lambda value:h.immutable(owned/'launcher-terminal.json',value))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('--run','--worker'))
    parser.add_argument('spec',type=Path);parser.add_argument('sha256')
    args=parser.parse_args(['--',*sys.argv[1:]])
    path=args.spec.absolute();require(sha(path)==args.sha256,'release SHA differs')
    spec=metadata(path);verify(spec)
    return launch(path,spec,args.sha256) if args.mode=='--run' else worker(path,spec)


if __name__=='__main__': raise SystemExit(main())
