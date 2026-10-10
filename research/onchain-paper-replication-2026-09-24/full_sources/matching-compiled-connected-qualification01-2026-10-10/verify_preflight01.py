"""CPU3 stdlib-only qualification source/refusal tests. Never executes numerics."""
import ast,builtins,hashlib,importlib.util,json,os,resource,signal,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'matching-compiled-normalization-connected02-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(30)
assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[]
def ok(name,value=True):assert value,name;checks.append(name)
original=builtins.__import__
def no_science(name,*a,**kw):
    assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes','tradingagents'},'forbidden import '+name
    return original(name,*a,**kw)
builtins.__import__=no_science
spec=importlib.util.spec_from_file_location('qualification_source',HERE/'qualify.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
frozen=q.inputs();requirements=frozen['SOURCE_REQUIREMENTS.json'];cases=frozen['CASES.json']
ok('eight exact connected source requirements',len(requirements['installed_module_sha256'])==8)
for name,digest in requirements['installed_module_sha256'].items():ok('frozen02 actual source pin '+name,hashlib.sha256((OLD/name).read_bytes()).hexdigest()==digest)
ok('frozen02 manifest reference',hashlib.sha256((OLD/'MANIFEST01.json').read_bytes()).hexdigest()==requirements['candidate02_manifest_sha256'])
ok('four fixed graph cases',len(cases['graph_cases'])==4 and [(x['n'],x['m']) for x in cases['graph_cases']]==[(3,3),(2,4),(5,3),(2,2)])
ok('finite primitive cases',len(cases['primitive_cases'])==4 and sum(len(x['values'])*len(x['values'][0]) for x in cases['primitive_cases'])==17)
ok('original matching config unchanged',(HERE/'matching-config.json').read_bytes()==(q.CHECKOUT/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_bytes())
# Current installed baseline must refuse BEFORE reading runtime file/importing
# scientific code. The nonexistent policy cannot be mistaken for authority.
try:q.preflight(q.CHECKOUT,HERE/'ROOT_RUNTIME_POLICY_NOT_SUPPLIED.json')
except ValueError as error:ok('actual uninstalled source fails closed',str(error).startswith('exact input/source SHA256 differs:'))
else:raise AssertionError('current frozen baseline accepted as02')
# Only synthetic source metadata layout; not a fake admission/runtime inventory.
fixture=HERE/'source-layout-fixture';target=fixture/'tradingagents/research/onchain_replication';target.mkdir(parents=True,exist_ok=False)
for name in requirements['installed_module_sha256']:(target/name).write_bytes((OLD/name).read_bytes())
for index,value in enumerate(({},False,{'format':'wrong'})):
    path=HERE/('invalid-policy-'+str(index)+'.json');path.write_text(json.dumps(value)+'\n')
    try:q.preflight(fixture,path)
    except (ValueError,TypeError):ok('actual existing policy parser refuses invalid input '+str(index))
    else:raise AssertionError('invalid policy accepted')
# Tampering any one source blocks before policy/scientific import.
changed=target/'matching_checkpoint.py';changed.write_bytes(changed.read_bytes()+b'\n')
try:q.preflight(fixture,HERE/'ROOT_RUNTIME_POLICY_NOT_SUPPLIED.json')
except ValueError as error:ok('source tamper fails closed',str(error).startswith('exact input/source SHA256 differs:'))
else:raise AssertionError('tamper accepted')
# Source-level route assertions are not numerical test credit.
t=ast.parse((HERE/'qualify.py').read_text());functions={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
for node in t.body:ok('no scientific top-level import '+str(getattr(node,'lineno',0)),not isinstance(node,(ast.Import,ast.ImportFrom)) or not any(alias.name.split('.')[0] in {'numpy','scipy','torch','ctypes','tradingagents'} for alias in node.names))
source=ast.unparse(functions['execute'])
for route in ('numeric.NumericExecution','executor.finish','numeric.verify','sessions.ImmutablePairSession','engine.save','engine.load','engine.result','policy_module.open_backend'):
    ok('real API seam '+route,route in source)
for prohibited in ('setattr(engine','setattr(numeric','sys.modules[','monkeypatch','Owner('):ok('no guard/authority patch '+prohibited,prohibited not in source)
need_call=next(i for i,n in enumerate(functions['main'].body) if 'preflight(CHECKOUT' in ast.unparse(n))
execute_call=next(i for i,n in enumerate(functions['main'].body) if ast.unparse(n).startswith('execute('))
ok('main preflight precedes scientific execute',need_call<execute_call)
ok('explicit post-terminal action required','execute_after_terminal' in ast.unparse(functions['main']))
ok('Owner disabled','binding_owner=None' in source and 'binding_timing=None' in source and 'authority_poll=None' in source)
ok('unchanged strict numerical criteria','tobytes()' in source and 'allclose' not in source and 'isclose' not in source)
ok('read-only closure observation','inspect.getclosurevars' in source and 'fcntl.fcntl(fd, 1034)' in source)
ok('fresh-root outputs and finite cap','not output.exists()' in source and "cases['max_advances_per_pair']" in source)
result={'status':'PASS_STDLIB_PREFLIGHT_SOURCE_ONLY','checks':checks,'count':len(checks),'elapsed_ns':time.perf_counter_ns()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'affinity':sorted(os.sched_getaffinity(0)),'numerical_harness_executed':False,'valid_root_runtime_policy_supplied':False,'actual_admission':False}
(HERE/'PREFLIGHT_TEST_RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','count','elapsed_ns','peak_rss_kib')}))
