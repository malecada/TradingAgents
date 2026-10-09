import ast,hashlib,importlib,json,os,resource,signal,sys,types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));os.nice(10);signal.alarm(60)
R=Path.cwd();sys.path.insert(0,str(R));H=Path(__file__).resolve().parent;P=H.parent/'matching-exact-numeric-reuse03-2026-10-09';old=P.parent/'matching-exact-numeric-reuse02-2026-10-09';checks=[]
def ck(name,ok):assert ok,name;checks.append(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((P/'MANIFEST01.json').read_text())
for name,pin in manifest.items():ck('body_'+name,sha(P/name)==pin)
ck('literal_inverse',(P/'inverse.py').read_bytes()==(old/'numeric_reuse.py').read_bytes())
def defs(p):return {n.name:ast.dump(n) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=defs(old/'numeric_reuse.py'),defs(P/'numeric_reuse.py');ck('cache_boundaries_exact',all(a[n]==b[n] for n in a if n not in ('digest','attest')))
ck('independently_reviewed_executor02',sha(P/'batched_pair_executor.py')=='5e722ec2035e2549f7584a31bf091e0de4d7854c196086f8736179f367d93b2e' and sha(P.parent/'mcm-immutable-pair-executor-review02-2026-10-09/SOURCE_REVIEW01.json')=='d0412a8fac80bb91f1688660cfa2c4134b1356a9f974a77c98e69db5ed2118e9')
package=types.ModuleType('root_memo03_review');package.__path__=[str(P)];sys.modules[package.__name__]=package
m=importlib.import_module('root_memo03_review.numeric_reuse')
ck('single_executor_object',m.accepted is importlib.import_module('root_memo03_review.batched_pair_executor'))
ck('single_session_object',m.accepted.ImmutablePairSession is m.immutable_session.ImmutablePairSession)
for module,pin in m.SOURCE_PINS:ck('actual_source_'+module.__name__,sha(Path(module.__file__))==pin)
counters={'source_guard_calls':0,'source_hashed_bytes':0};m.attest(counters);ck('actual_complete_attestation',counters['source_guard_calls']==1 and counters['source_hashed_bytes']>0)
# Wrong physical session body must refuse; no original source body is modified.
module=m.immutable_session;original=module.__file__;wrong=H/'wrong-body.txt';wrong.write_text('wrong source body\n');module.__file__=str(wrong)
try:
 try:m.attest(counters)
 except ValueError as error:ck('wrong_session_body_refused',str(error)=='numeric source changed')
 else:raise AssertionError('wrong source accepted')
finally:module.__file__=original
# Newly joined session function roster must refuse before source-batch credit.
original=module.config_pin;module.config_pin=lambda _:None
try:
 try:m.attest(counters)
 except ValueError as error:ck('redirected_session_function_refused',str(error)=='numeric runtime function/code changed')
 else:raise AssertionError('wrong runtime accepted')
finally:module.config_pin=original
result=json.loads((P/'RESULT01.json').read_text());ck('retained_real_tiny_result_pass',result['status']=='PASS' and not result['empirical_inputs'] and not result['real_owner_or_authority'])
ck('retained_occurrence_is_provisional',result['reused_receipt']['mode']=='reused' and not result['reused_receipt']['boundary_validated_batch_complete'] and not result['reused_receipt']['old_per_occurrence_execution_credit'])
out={'schema_version':1,'decision':'accepted-source-only','source_sha256':sha(P/'numeric_reuse.py'),'manifest_sha256':sha(P/'MANIFEST01.json'),'checks':checks,'reused_memo02_review':'3813f9550d4b6b4abf17e86092adf99398713076d9c90a04bf1e226d67bf0ad1','executor02_review':'d0412a8fac80bb91f1688660cfa2c4134b1356a9f974a77c98e69db5ed2118e9','qualification':'Fixed actual module-source/session joins independently checked; unchanged cache/arithmetic/boundaries and retained tiny numerical proof reused. Caller must anchor provisional ordered receipts and actual counters only after successful end_batch. Genuine Owner/admission, installed package path role joins, capacity and real hit-rate/speed unproved.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'decision':out['decision'],'checks':len(checks),'sha256':sha(H/'SOURCE_REVIEW01.json')}))
