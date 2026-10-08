"""Source-backed default refusal probe; creates no authority or registration."""
import ast,contextlib,hashlib,json,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
source=ROOT/'tradingagents/research/onchain_replication/imported_authority_lease.py'
tree=ast.parse(source.read_text())
interval=ROOT/'tradingagents/research/onchain_replication/imported_authority_interval.py'
require=next(n for n in ast.parse(interval.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='require')
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'_loaded','_authenticate_loaded'} or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='AUTHORITY_CLASSES' for t in n.targets)]
ns={'contextlib':contextlib,'hashlib':hashlib,'sys':sys,'types':types,'Path':Path}
exec(compile(ast.Module(body=[require]+selected,type_ignores=[]),str(source),'exec'),ns)
path=HERE/'fixture.py';raw=b'def value():\n    return 42\n'
if path.exists():assert path.read_bytes()==raw
else:path.write_bytes(raw)
name='source_origin_refusal_fixture';module=types.ModuleType(name);module.__file__=str(path)
sys.modules[name]=module
try:
    exec(compile(raw,str(path),'exec',dont_inherit=True,optimize=sys.flags.optimize),vars(module))
    sources={'fixture.py':hashlib.sha256(raw).hexdigest()}
    ns['_authenticate_loaded'](ns['_loaded'](HERE,sources),sources,HERE)
    bad=compile(b'def value():\n    return 999\n',str(path),'exec',dont_inherit=True,optimize=sys.flags.optimize)
    exec(bad,vars(module));refreshed=ns['_loaded'](HERE,sources)
    forged=types.MappingProxyType({name:(str(path),sources['fixture.py'],sys.flags.optimize,(bad,bad.co_consts[0]))})
    result={'authentic_source_default':'accepted','source_sha256':sources['fixture.py'],
            'default_validator_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'source_value':42,'replaced_loaded_value':module.value()}
    try:ns['_authenticate_loaded'](refreshed,sources,HERE)
    except ValueError as error:result['forged_refreshed_snapshot_default']='refused';result['refusal']=str(error)
    else:raise AssertionError('source-backed default accepted forged code')
    try:ns['_authenticate_loaded'](refreshed,sources,HERE,compiled=forged)
    except TypeError:result['forged_cache_argument_default']='refused: no cache authority accepted'
    else:raise AssertionError('default accepted cache authority')
    assert path.read_bytes()==raw and 'torch' not in sys.modules
    result['scope']='AST-executed actual default validator on synthetic source module; no Owner/Lease/run/manifest/graph/neural'
    print(json.dumps(result,indent=2))
finally:sys.modules.pop(name,None)
