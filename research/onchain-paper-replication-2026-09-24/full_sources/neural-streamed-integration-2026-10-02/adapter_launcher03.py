"""One-use finite synthetic oracle launcher using the reviewed native guard."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.metadata
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
GIB = 1024**3
LIMITS = {'memory_max_bytes': GIB, 'memory_high_bytes': GIB,
          'memory_swap_max_bytes': 0, 'reserve_bytes': 3*GIB,
          'start_reserve_bytes': 4*GIB, 'wall_seconds': 120,
          'disk_floor_bytes': 10*GIB, 'file_limit_bytes': 4*1024**2,
          'allocated_stop_bytes': 64*1024**2, 'logical_stop_bytes': 64*1024**2}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class CleanupFailure(BaseException):
    """An owned descriptor close is uncertain; receipt publication is terminal."""

def _close_owned(descriptors,io):
    """Close each descriptor once; select actual fatal errors before wrapping."""
    import os
    import sys
    primary=sys.exception();errors=[]
    fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
    for fd in descriptors:
        try:os.close(fd)
        except BaseException as error:errors.append(error)
    if not errors:return
    selected=primary if primary is not None and fatal(primary) else next((e for e in errors if fatal(e)),None)
    if selected is not None:
        for error in errors:
            if error is not selected:selected.add_note('import descriptor close unresolved: '+type(error).__name__)
        if selected is primary:return
        earlier=errors[:next(i for i,e in enumerate(errors) if e is selected)]
        prior=([primary] if primary is not None else [])+earlier
        if prior:
            cause=prior[0] if len(prior)==1 else ExceptionGroup('prior import body/close failures',prior)
            if selected.__cause__ is not None and selected.__cause__ is not cause:
                cause=BaseExceptionGroup('prior import evidence and original fatal cause',[cause,selected.__cause__])
            selected.__cause__=cause
        raise selected
    # Only ordinary cleanup errors remain. Construct the terminal wrapper now,
    # after every owned descriptor and actual fatal have been considered.
    failure=io.CleanupFailure('import descriptor close unresolved')
    causes=([primary] if primary is not None else [])+errors
    failure.__cause__=causes[0] if len(causes)==1 else ExceptionGroup('import body/close failures',causes)
    for error in errors:failure.add_note(type(error).__name__)
    raise failure

def immutable(path, value):
    raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    if len(raw)>1024**2:raise ValueError('bounded metadata required')
    path=Path(path).absolute();parent=path.parent
    if parent.resolve()!=parent:raise ValueError('receipt parent redirected')
    before=parent.lstat()
    if not stat.S_ISDIR(before.st_mode):raise ValueError('receipt parent not directory')
    fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);child=None
    def rejoin():
        current=parent.lstat();opened=os.fstat(fd)
        if parent.resolve()!=parent or not stat.S_ISDIR(current.st_mode) or (current.st_dev,current.st_ino)!=(before.st_dev,before.st_ino) or (opened.st_dev,opened.st_ino)!=(before.st_dev,before.st_ino):
            raise ValueError('receipt original parent changed')
    try:
        rejoin();child=os.open(path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=fd)
        offset=0
        while offset<len(raw):
            written=os.write(child,raw[offset:])
            if type(written) is not int or written<=0:raise OSError('receipt write made no progress')
            offset+=written
        os.fsync(child)
        opened=os.fstat(child);entry=os.stat(path.name,dir_fd=fd,follow_symlinks=False)
        signature=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_nlink,x.st_size)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink!=1 or opened.st_size!=len(raw) or signature(opened)!=signature(entry):raise ValueError('receipt published file changed')
        rejoin();os.fsync(fd);rejoin()
    finally:
        _close_owned((() if child is None else (child,))+(fd,),SimpleNamespace(CleanupFailure=CleanupFailure))

def _cleanup_complete(result, proof, *, exists=None):
    """Authenticate current guard owner; require every workload descendant absent."""
    if exists is None:exists=lambda path:Path(path).exists()
    if result['cleanup_verified'] is not True or type(result['cleanup_stop_returncode']) is not int:return False
    if type(result['monitor_pid']) is not int or result['monitor_pid']!=os.getpid():return False
    if result['cleanup_stop_returncode']==0:return True
    if result['cleanup_stop_returncode']!=5 or result['phase']!='complete' or result['child_exit_code']!=0 or proof['child_exit']['exit_code']!=0:return False
    expected={'Result':'success','ExecMainStatus':'0','ControlGroup':'','ActiveState':'inactive','SubState':'dead'}
    for key in ('unit_properties','cleanup_unit_properties'):
        if any(result[key][name]!=value for name,value in expected.items()):return False
    pids={proof['cpu_ready']['pid'],proof['child_exit']['workload_pid']}
    pids.update(int(pid) for pid in result['cpu_thread_readback'])
    if not all(type(pid) is int and pid>0 for pid in pids):return False
    return not exists(result['cgroup']) and all(not exists('/proc/'+str(pid)) for pid in pids)

EXPECTED_CHECKS=['layer_mixed_self_isolated','layer_zero_edges','layer_masked','layer_float64','dropout_rng','duplicate_refusal','full_model_16x28_all_gradients_Adam_RNG_reload','aggregation_output_all_gradients','independent_gradcheck','independent_central_difference','invalid_block_refusal']

def validate_result(mode,result,report,proof):
    """A named RED assertion is acceptable only inside the complete real envelope."""
    def require(value,message):
        if not value:raise RuntimeError(message)
    require(mode in ('red','green'),'unknown oracle mode')
    for key in ('storage_breach','storage_last_error','cleanup_error','child_log_limit_reached','log_truncated','truncated_logs'):
        require(key not in result,'guard has forbidden terminal diagnostic: '+key)
    require(_cleanup_complete(result,proof),'descendant cleanup unverified')
    require(result['elapsed_time_kill'] is False and result['retry'] is False and type(result['elapsed_seconds']) in (int,float) and 0<=result['elapsed_seconds']<=120,'elapsed/identity envelope differs')
    for key in ('memory_max_bytes','memory_high_bytes','memory_swap_max_bytes','reserve_bytes','start_reserve_bytes','wall_seconds','disk_floor_bytes'):
        require(type(result[key]) is int and result[key]==LIMITS[key],'actual guard policy differs: '+key)
    controls={'memory.max':str(GIB),'memory.high':str(GIB),'memory.swap.max':'0'}
    require(result['kernel_controls']==controls==report['native']['controls'],'native memory controls differ')
    for name in ('initial_memory_events','memory_events'):
        require(type(result[name]) is dict,'missing kernel events')
        for key in ('high','max','oom','oom_kill','oom_group_kill'):
            require(type(result[name][key]) is int and result[name][key]==0,'kernel memory event occurred or is unavailable')
    terminal=result['terminal_memory_snapshot'];child=proof['child_exit']
    require(child['snapshot_error'] is None and child['reason']=='workload exited' and type(child['workload_pid']) is int and child['workload_pid']>0,'actual workload exit snapshot missing')
    require(child['terminal_memory_snapshot']==terminal and terminal['memory_events']==result['memory_events'],'terminal memory events differ')
    require(type(terminal['memory_current_bytes']) is int and 0<=terminal['memory_current_bytes']<=GIB,'terminal memory extent differs')
    require(type(result['peak_sampled_memory_current_bytes']) is int and 0<=result['peak_sampled_memory_current_bytes']<=GIB,'sampled peak exceeded limit')
    cpus=result['cpus'];ready=proof['cpu_ready']
    require(type(cpus) is list and len(cpus)==2 and cpus==sorted(set(cpus)) and all(type(x) is int and x>=0 for x in cpus),'exact two CPU IDs missing')
    require(report['native']['cpus']==ready['cpus']==cpus and type(ready['pid']) is int and ready['pid']>0,'actual CPU readiness/readback differs')
    require(type(result['cpu_thread_readback']) is dict and all(type(k) is str and k.isdecimal() and v==cpus for k,v in result['cpu_thread_readback'].items()),'CPU thread readback missing/different')
    require(result['cpu_enforcement']=='inherited two-CPU affinity with per-thread cgroup readback','CPU enforcement differs')
    require(report['native']['cgroup']==result['cgroup'],'native cgroup differs')
    native=proof['native_controls']
    require(native['LimitFSIZE']==native['LimitFSIZESoft']=='4194304' and native['RuntimeMaxUSec'] in ('2min','120s','120000000'),'native file/wall controls differ')
    require('/sys/fs/cgroup'+native['ControlGroup']==result['cgroup'] and native['MainPID']==str(ready['pid']),'native unit identity differs')
    require(report['native']['rlimit_fsize']==[4194304,4194304],'actual inherited file limit differs')
    require(type(proof['child_log_bytes']) is int and 0<=proof['child_log_bytes']<4194304,'child log reached cap or truncation unknown')
    limits={'max_allocated_bytes':64*1024**2,'max_logical_bytes':64*1024**2,'max_entries':12000,'max_depth':32,'max_scan_seconds':2}
    require(result['storage_budget']=={'root':proof['owned_root'],'limits':limits},'sampled storage guard missing/different')
    for key,maximum in [('allocated_bytes',limits['max_allocated_bytes']),('logical_file_bytes',limits['max_logical_bytes']),('entries',limits['max_entries'])]:
        value=result['storage_observation'][key];peak=result['storage_peak_'+key]
        require(type(value) is int and type(peak) is int and 0<=value<=peak<=maximum,'storage observation/peak missing or breached')
    require(type(result['disk_free_bytes']) is dict and set(result['disk_free_bytes'])=={proof['owned_root']} and all(type(x) is int and x>=10*GIB for x in result['disk_free_bytes'].values()),'disk readback/floor differs')
    props=result['unit_properties'];cleanup=result['cleanup_unit_properties'];code=1 if mode=='red' else 0
    require(result['child_exit_code']==child['exit_code']==code and type(result['child_exit_code']) is int and type(child['exit_code']) is int,'child terminal code differs')
    require(props['Result']==cleanup['Result']==('exit-code' if mode=='red' else 'success') and props['ExecMainStatus']==cleanup['ExecMainStatus']==str(code),'native terminal status differs')
    require(props['ActiveState'] in ('inactive','failed') and cleanup['ActiveState'] in ('inactive','failed'),'unit remains live')
    expected_checks=['production_adapter_four_tests']
    require(type(report['schema_version']) is int and report['schema_version']==1 and report['mode']==mode and report['passed_checks']==expected_checks,'oracle reached different phase')
    if mode=='red':
        require(result['phase']=='failed' and report['status']=='failed' and report['error']['type']=='AssertionError' and report['error']['message']=='RESOURCE_EDGE_WIDE_SAVED_TENSORS','RED failed for unexpected reason')
        prefix='RuntimeError: child or unit failed: ';reason=result['limit_reason']
        require(type(reason) is str and reason.startswith(prefix) and len(reason)<=8192,'RED guard reason differs')
        require(ast.literal_eval(reason[len(prefix):])==props,'RED guard terminal reason differs')
    else:
        require(result['phase']=='complete' and result['limit_reason'] is None and report['status']=='passed' and report['error'] is None,'GREEN not cleanly complete')


def verify(spec):
    if spec['status'] != 'released_single_tiny_engineering_attempt' or spec['limits'] != LIMITS:
        raise ValueError('exact reviewed release required')
    mode = spec['mode']
    if mode != 'green' or spec['identity'] != 'neural-streamed-production-adapter-20261002-01':
        raise ValueError('identity/mode differs')
    if spec['oracle_file'] != 'adapter_tests03.py':
        raise ValueError('only frozen correction oracle03 is selectable')
    if sys.prefix != str(ROOT/'.venv') or platform.python_version() != '3.13.13':
        raise ValueError('pinned interpreter required')
    versions = {d.metadata['Name']: d.version for d in importlib.metadata.distributions() if d.metadata['Name']}
    if versions != spec['installed_distribution_versions']:
        raise ValueError('distribution metadata changed')
    total = 0
    for name, expected in spec['source_files'].items():
        path = ROOT/name
        if path.resolve() != path or not path.is_relative_to(ROOT) or path.stat().st_nlink != 1 or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError('source path/type/link differs')
        total += path.stat().st_size
        if path.stat().st_size > 4*1024**2 or total > 16*1024**2 or sha(path) != expected:
            raise ValueError('source bytes/capacity differ')
    if sha(__file__) != spec['launcher_sha256']:
        raise ValueError('launcher bytes differ')
    if any(name in sys.modules for name in ('torch', 'numpy')):
        raise ValueError('numerical import occurred before native release')

def load(path, expected):
    if path.resolve() != path or path.stat().st_size > 2*1024**2 or sha(path) != expected:
        raise ValueError('exact release object differs')
    spec = json.loads(path.read_bytes())
    verify(spec)
    return spec

def worker(spec):
    owned = HERE/'owned'/spec['identity']
    os.chdir(HERE)
    sys.path.insert(0, str(HERE))
    sys.argv = [str(HERE/spec['oracle_file']), '--mode', spec['mode'],
                '--report', str(owned/'oracle-report.json')]
    runpy.run_path(str(HERE/spec['oracle_file']), run_name='__main__')

def launch(path, spec, expected):
    owned = HERE/'owned'/spec['identity']
    if owned.exists() or owned.is_symlink():
        raise ValueError('identity already reserved; inspect it, never invoke again')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=10).strip()
    # All selected source must actually be committed under this exact HEAD.
    for name, expected_source in spec['source_files'].items():
        raw = subprocess.check_output(['git', 'show', head+':'+name], cwd=ROOT, timeout=10)
        if hashlib.sha256(raw).hexdigest() != expected_source:
            raise ValueError('selected committed source differs')
    (HERE/'owned').mkdir(exist_ok=True)
    owned.mkdir()
    immutable(owned/'reservation.json', {'identity': spec['identity'], 'head': head,
              'release_sha256': expected, 'started_utc': datetime.now(timezone.utc).isoformat()})
    for name in ('tmp', 'cache'):
        (owned/name).mkdir()
    environment = {'PYTHONPATH': str(ROOT), 'PYTHONDONTWRITEBYTECODE': '1',
                   'TMPDIR': str(owned/'tmp'), 'XDG_CACHE_HOME': str(owned/'cache'),
                   'TORCH_HOME': str(owned/'cache/torch'), 'OMP_NUM_THREADS': '2',
                   'MKL_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2',
                   'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTEST_PLUGINS': '', 'PYTEST_ADDOPTS': ''}
    resource.setrlimit(resource.RLIMIT_FSIZE, (4*1024**2, 4*1024**2))
    sys.path.insert(0, str(ROOT))
    from tradingagents.research.onchain_replication import resources
    real = resources.subprocess
    def run(args, **kwargs):
        if args[0] != 'systemd-run':
            return real.run(args, **kwargs)
        changed = [args[0], '--property=LimitFSIZE=4194304', '--property=RuntimeMaxSec=120s',
                   *['--setenv='+key+'='+value for key, value in sorted(environment.items())], *args[1:]]
        result = real.run(changed, **kwargs)
        unit = next(arg.split('=',1)[1] for arg in args if arg.startswith('--unit='))
        answer = real.run(['systemctl', '--user', 'show', unit,
                          '--property=LimitFSIZE,LimitFSIZESoft,RuntimeMaxUSec,CPUQuotaPerSecUSec,ControlGroup,MainPID'],
                          check=True, capture_output=True, text=True, timeout=10)
        properties = dict(line.split('=',1) for line in answer.stdout.splitlines() if '=' in line)
        immutable(owned/'native-unit-controls.json', properties)
        if properties.get('LimitFSIZE') != '4194304' or properties.get('LimitFSIZESoft') != '4194304' or properties.get('RuntimeMaxUSec') not in ('2min', '120s', '120000000'):
            raise ValueError('native file/runtime readback differs')
        return result
    result = None; primary = None
    resources.subprocess = SimpleNamespace(run=run, Popen=real.Popen)
    try:
        result = resources.guarded_run(
            [sys.executable, '-B', str(Path(__file__).resolve()), '--worker', str(path), expected],
            cwd=HERE, receipt_dir=owned/'guard', memory_max_bytes=GIB, memory_high_bytes=GIB,
            memory_swap_max_bytes=0, reserve_bytes=3*GIB, start_reserve_bytes=4*GIB,
            wait_seconds=0, wall_seconds=120, sample_seconds=.25,
            disk_paths=[owned], disk_floor_bytes=10*GIB,
            storage_budget={'root': str(owned), 'limits': {'max_allocated_bytes': 64*1024**2,
                'max_logical_bytes': 64*1024**2, 'max_entries': 12000, 'max_depth': 32, 'max_scan_seconds': 2}})
        verify(spec)
        def metadata(path,maximum=65536):
            info=path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>maximum:raise ValueError('bounded terminal metadata required')
            return json.loads(path.read_bytes())
        report=metadata(owned/'oracle-report.json')
        log=owned/'guard/child.log';log_info=log.lstat()
        if not stat.S_ISREG(log_info.st_mode) or log_info.st_nlink!=1:raise ValueError('actual regular child log required')
        proof={'native_controls':metadata(owned/'native-unit-controls.json'),
            'cpu_ready':metadata(owned/'guard/cpu_ready.json'),
            'child_exit':metadata(owned/'guard/child_exit.json'),
            'child_log_bytes':log_info.st_size,'owned_root':str(owned)}
        validate_result(spec['mode'],result,report,proof)
    except BaseException as error:
        primary = error
    finally:
        resources.subprocess = real
    try:
        immutable(owned/'launcher-terminal.json', {
            'identity': spec['identity'], 'status': 'expected_red' if primary is None and spec['mode']=='red' else 'passed' if primary is None else 'failed',
            'error': None if primary is None else repr(primary), 'head': head,
            'guard_phase': None if result is None else result.get('phase'),
            'cleanup_verified': False if result is None else result.get('cleanup_verified',False),
            'retry': False, 'finished_utc': datetime.now(timezone.utc).isoformat()})
    except BaseException as error:
        fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
        if primary is None:
            primary=error
        elif fatal(error) and not fatal(primary):
            error.__cause__=primary; primary=error
        else:
            primary.add_note('terminal publication failure: '+type(error).__name__)
    if primary is not None:
        raise primary
    return 0

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode', choices=('--run','--worker'))
    parser.add_argument('spec', type=Path); parser.add_argument('sha256')
    args=parser.parse_args(['--', *sys.argv[1:]])
    path=args.spec.resolve(strict=True); spec=load(path,args.sha256)
    return launch(path,spec,args.sha256) if args.mode=='--run' else worker(spec)

if __name__=='__main__':
    raise SystemExit(main())
