"""Explicit shared-runtime/capsule mapping, stdlib-only; no venv symlink."""
import hashlib,importlib.machinery,importlib.metadata,os,platform,sys
from pathlib import Path

def check(capsule,expected):
    capsule=Path(capsule)
    if capsule.resolve()!=capsule or Path.cwd()!=capsule:raise ValueError('capsule cwd differs')
    if sys.executable!=expected['executable'] or sys.prefix!=expected['prefix'] or platform.python_version()!=expected['python']:raise ValueError('locked shared runtime differs')
    exe=Path(sys.executable).resolve()
    if str(exe)!=expected['resolved_executable'] or hashlib.sha256(exe.read_bytes()).hexdigest()!=expected['executable_sha256']:raise ValueError('interpreter body differs')
    if hashlib.sha256((capsule/'uv.lock').read_bytes()).hexdigest()!=expected['lock_sha256']:raise ValueError('capsule lock differs')
    if (capsule/'.venv').exists() or (capsule/'.venv').is_symlink():raise ValueError('capsule cannot spoof shared runtime prefix')
    top=importlib.machinery.PathFinder.find_spec('tradingagents',[str(capsule)])
    if top is None or Path(top.origin)!=capsule/'tradingagents/__init__.py':raise ValueError('capsule package origin differs')
    origins={}
    for p in sorted((capsule/'tradingagents/research/onchain_replication').glob('*.py')):
        spec=importlib.machinery.PathFinder.find_spec(p.stem,[str(p.parent)])
        if spec is None or Path(spec.origin)!=p:raise ValueError('module origin differs')
        origins[p.stem]=spec.origin
    for name,module in tuple(sys.modules.items()):
        if name=='tradingagents' or name.startswith('tradingagents.'):
            path=getattr(module,'__file__',None)
            if path is None or not Path(path).resolve().is_relative_to(capsule):raise ValueError('already loaded foreign research module')
    for row in expected['distribution_records']:
        if importlib.metadata.version(row['name'])!=row['version']:raise ValueError('runtime distribution version changed')
        if row['record'] is None:raise ValueError('unbound runtime distribution record')
        if hashlib.sha256(Path(row['record']).read_bytes()).hexdigest()!=row['record_sha256']:raise ValueError('runtime distribution file manifest changed')
    if any(name in sys.modules for name in ('numpy','torch')):raise ValueError('numerical import before native release')
    return {'python':platform.python_version(),'prefix':sys.prefix,'executable':sys.executable,'sys_path':list(sys.path),'package_origin':top.origin,'module_origins':origins,'numerical_imports':False,'runtime_record_qualification':'RECORD hashes bind installed body expectations; this check does not rehash every dependency body'}
