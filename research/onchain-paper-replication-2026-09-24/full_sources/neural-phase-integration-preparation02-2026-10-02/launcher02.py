"""Prepared one-shot synthetic owner launcher; explicit reviewed release required.

No total-filesystem quota: StorageWatch enforces sampled stop thresholds.
Only main --run starts a reviewed systemd guard. Import is side-effect free.
"""
import argparse
import hashlib
import importlib.machinery
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import stat
import subprocess
import sys
from types import SimpleNamespace

GIB=1024**3
IDENTITY='neural-phase-integration-20261002-01'
BASE='e0cb08b6bf763ffec0bb4058d5d1d89bd3977486'
TEST='phase_fixture.py'
CASES=['success','fatal','publication_refusal','near_cap','entry_cap']


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(65536),b''):h.update(chunk)
    return h.hexdigest()


def immutable(path,value):
    data=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    if len(data)>1024**2:raise ValueError('control output exceeds 1MiB')
    with Path(path).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    fd=os.open(Path(path).parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def reserve(root,value):immutable(Path(root)/'reservation.json',value)


def retain(primary,error):
    if primary is None:return error
    if primary is error:return primary
    if isinstance(primary,Exception) and not isinstance(primary,MemoryError) and (not isinstance(error,Exception) or isinstance(error,MemoryError)):
        error.__cause__=primary;return error
    primary.add_note('additional launcher failure: '+repr(error));return primary


def verify_files(root,files):
    root=Path(root)
    if root.resolve(strict=True)!=root or not files:raise ValueError('source root/mapping differs')
    actual=set()
    for p in root.rglob('*'):
        info=p.lstat()
        if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):raise ValueError('source symlink/special entry')
        if p.is_file():
            if info.st_nlink!=1:raise ValueError('source hardlink')
            actual.add(str(p.relative_to(root)))
    if actual!=set(files):raise ValueError('source closure contains missing/extra file')
    for name,expected in files.items():
        p=root/name
        if p.resolve()!=p or not p.is_relative_to(root) or sha(p)!=expected:raise ValueError('source bytes differ: '+name)


def require_release(spec):
    if spec.get('status')!='released_single_isolated_synthetic_attempt':raise ValueError('explicit reviewed release missing')


def unit_arguments(args,environment):
    if args[0]!='systemd-run':return args
    if any(any(arg.startswith('--property='+key+'=') for key in ('LimitFSIZE','LimitFSIZESoft','RuntimeMaxSec')) for arg in args):raise ValueError('conflicting added unit limits')
    return [args[0],'--property=LimitFSIZE=4194304','--property=RuntimeMaxSec=1800s',
            *['--setenv='+k+'='+v for k,v in sorted(environment.items())],*args[1:]]


def verify_unit_properties(properties):
    if properties.get('LimitFSIZE')!='4194304' or properties.get('LimitFSIZESoft')!='4194304' or properties.get('RuntimeMaxUSec') not in ('30min','1800s','1800000000'):
        raise ValueError('finite systemd file/runtime controls differ')


def load_spec(path,expected):
    path=Path(path).resolve(strict=True)
    if path.stat().st_size>2*1024**2 or sha(path)!=expected:raise ValueError('release spec bytes differ')
    spec=json.loads(path.read_bytes())
    if spec['identity']!=IDENTITY or spec['source_commit']!=BASE or spec['cases']!=CASES or spec['test_file']!=TEST:raise ValueError('fixture identity/cases/source differs')
    if sha(__file__)!=spec['launcher_sha256']:raise ValueError('launcher bytes differ')
    if spec['limits']!={'wall_seconds':1800,'memory_max_bytes':3*GIB,'memory_high_bytes':2*GIB,'memory_swap_max_bytes':0,'allocated_stop_bytes':GIB,'logical_stop_bytes':GIB,'log_and_per_file_limit_bytes':4*1024**2,'disk_free_floor_bytes':10*GIB}:raise ValueError('fixed limits differ')
    return path,spec


def runtime(spec):
    source=Path(spec['isolated_source_root']).resolve(strict=True)
    shared=Path(spec['shared_checkout']).resolve(strict=True)
    if sys.prefix!=str(shared/'.venv') or platform.python_version()!='3.13.13':raise ValueError('locked interpreter mapping differs')
    if sha(source/'uv.lock')!=spec['source_files']['uv.lock']:raise ValueError('lock differs')
    sys.path[:]=[str(source)]+[p for p in sys.path if p and Path(p).resolve() not in (shared,Path(__file__).resolve().parent,source)]
    observations={}
    for name in ('tradingagents','phase_fixture'):
        found=importlib.machinery.PathFinder.find_spec(name,sys.path)
        if found is None:raise ValueError('isolated package missing '+name)
        origins=[found.origin] if found.origin else list(found.submodule_search_locations or ())
        if not origins or any(not Path(p).resolve().is_relative_to(source) for p in origins):raise ValueError('package resolves outside snapshot '+name)
        observations[name]=origins
    versions={d.metadata['Name']:d.version for d in importlib.metadata.distributions() if d.metadata['Name']}
    if versions!=spec['installed_distribution_versions']:raise ValueError('installed runtime metadata changed')
    return {'python':platform.python_version(),'prefix':sys.prefix,'origins':observations,'numerical_imports_performed':False,'binary_attestation':False}


def environment(spec,path,expected):
    root=Path(spec['owned_root'])
    return {'PYTHONPATH':spec['isolated_source_root'],'PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1',
            'NEURAL_PHASE_FIXTURE_RELEASE':str(path),'NEURAL_PHASE_FIXTURE_RELEASE_SHA256':expected,
            'TMPDIR':str(root/'tmp'),'HOME':str(root/'home'),'XDG_CACHE_HOME':str(root/'cache'),
            'TORCH_HOME':str(root/'cache/torch'),'MPLCONFIGDIR':str(root/'cache/matplotlib'),
            'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_TERMINAL_PROMPT':'0',
            'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'}


def worker(path,spec,expected):
    require_release(spec)
    if resource.getrlimit(resource.RLIMIT_FSIZE)!=(4*1024**2,4*1024**2):raise ValueError('worker file limit differs')
    verify_files(Path(spec['isolated_source_root']),spec['source_files']);runtime(spec)
    os.environ.update(environment(spec,path,expected));os.chdir(spec['isolated_source_root'])
    import phase_fixture
    return phase_fixture.run(spec)


def launch(path,spec,expected):
    require_release(spec)
    root=Path(spec['owned_root']);source=Path(spec['isolated_source_root'])
    if root.resolve()!=root or source.parent!=root.parent or Path(spec['attempt_root'])!=root/'attempts':raise ValueError('owned path mapping differs')
    verify_files(source,spec['source_files']);observed=runtime(spec)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=spec['shared_checkout'],text=True).strip()
    if head!=spec['expected_shared_head']:raise ValueError('shared HEAD changed; review required')
    root.mkdir(exist_ok=False)
    reserve(root,{'identity':IDENTITY,'source_commit':BASE,'spec_sha256':expected,'runtime':observed})
    primary=None;result=None
    try:
        for name in ('attempts','tmp','home','cache'):(root/name).mkdir()
        env=environment(spec,path,expected)
        from tradingagents.research.onchain_replication import resources
        real=resources.subprocess
        def run(args,**kwargs):
            changed=unit_arguments(args,env)
            answer=real.run(changed,**kwargs)
            if args[0]=='systemd-run':
                unit=next(x.split('=',1)[1] for x in args if x.startswith('--unit='))
                output=real.run(['systemctl','--user','show',unit,'--property=LimitFSIZE,LimitFSIZESoft,RuntimeMaxUSec'],check=True,capture_output=True,text=True,timeout=10)
                verify_unit_properties(dict(line.split('=',1) for line in output.stdout.splitlines() if '=' in line))
            return answer
        # Adapter only adds finite controls/env to the original guard's launch;
        # the original kernel readback, release lease and cleanup remain intact.
        resources.subprocess=SimpleNamespace(run=run,Popen=real.Popen)
        try:
            result=resources.guarded_run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker',str(path),expected],
                cwd=source,receipt_dir=root/'guard',memory_max_bytes=3*GIB,memory_high_bytes=2*GIB,memory_swap_max_bytes=0,
                reserve_bytes=3*GIB,start_reserve_bytes=6*GIB,wait_seconds=0,wall_seconds=1800,
                disk_paths=[root],disk_floor_bytes=10*GIB,sample_seconds=.25,
                storage_budget={'root':str(root),'limits':{'max_allocated_bytes':GIB,'max_logical_bytes':GIB,'max_entries':12000,'max_depth':32,'max_scan_seconds':2}})
        finally:resources.subprocess=real
        if result.get('phase')!='complete' or not result.get('cleanup_verified'):raise RuntimeError('guard did not complete with verified cleanup')
        if (root/'guard/child.log').stat().st_size>=4*1024**2:raise RuntimeError('log reached finite limit; result incomplete')
    except BaseException as error:primary=error
    try:verify_files(source,spec['source_files'])
    except BaseException as error:primary=retain(primary,error)
    try:immutable(root/'launcher-terminal.json',{'status':'complete' if primary is None else 'failed','error':None if primary is None else repr(primary),'guard_phase':None if result is None else result.get('phase'),'cleanup_verified':False if result is None else result.get('cleanup_verified',False),'retry':False})
    except BaseException as error:primary=retain(primary,error)
    if primary is not None:raise primary
    return 0


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['--run','--worker','--runtime-check']);parser.add_argument('spec');parser.add_argument('sha256')
    # Modes start with --, so parse the positional sequence after a literal --.
    args=parser.parse_args(['--',*sys.argv[1:]])
    path,spec=load_spec(args.spec,args.sha256)
    if args.mode=='--runtime-check':print(json.dumps(runtime(spec),indent=2));return 0
    return worker(path,spec,args.sha256) if args.mode=='--worker' else launch(path,spec,args.sha256)

if __name__=='__main__':raise SystemExit(main())
