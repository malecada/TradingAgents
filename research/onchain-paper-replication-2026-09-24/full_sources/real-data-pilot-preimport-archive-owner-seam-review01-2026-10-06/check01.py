"""Bounded source and extracted changed-seam witnesses; no authority activation."""
import ast,copy,hashlib,importlib.util,json,sys,types
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[3];F=D.parent;C=F/'real-data-pilot-preimport-archive-owner-seam01-2026-10-06';P=Path('tradingagents/research/onchain_replication');evidence={}
def raw(p):
 value=p.read_bytes();evidence[str(p.relative_to(ROOT))]=hashlib.sha256(value).hexdigest();return value
def read(p):return json.loads(raw(p))
manifest=read(C/'MANIFEST01.json');assert evidence[str((C/'MANIFEST01.json').relative_to(ROOT))]=='310134ee24e490d7303c651ecda8fd8e6395b6c28099784321cb96e6c0259928'
for name,h in manifest['files'].items():assert hashlib.sha256(raw(C/name)).hexdigest()==h
for path,h in read(C/'SOURCE_EVIDENCE01.json')['original_sources'].items():assert hashlib.sha256(raw(ROOT/path)).hexdigest()==h
for name,row in read(C/'SOURCE_DELTA01.json').items():
 value=raw(C/'candidate'/P/name).decode();assert hashlib.sha256(value.encode()).hexdigest()==row['candidate_sha256'];ast.parse(value)
 for edit in reversed(row['edits']):assert value.count(edit['new'])==1;value=value.replace(edit['new'],edit['old'],1)
 assert value.encode()==raw(Path(row['baseline'])) and hashlib.sha256(value.encode()).hexdigest()==row['baseline_sha256']
def fn(name,function):return next(x for x in ast.parse(raw(C/'candidate'/P/name)).body if isinstance(x,ast.FunctionDef) and x.name==function)
def require(v,m):
 if not v:raise ValueError(m)
admitted=fn('real_pilot_import_caller.py','admitted')
start=next(i for i,x in enumerate(admitted.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='expected_archive' for t in x.targets))
code=compile(ast.Module(body=admitted.body[start:start+2],type_ignores=[]),'actual-pair-join','exec')
for s,p,expected in [({}, {},True),({'compact_archive_input':'a','compact_archive_transport_input':'t'},{'archive_inputs':{'policy_input':'a','transport_input':'t'}},True),({'compact_archive_input':'a','compact_archive_transport_input':'t'},{'archive_inputs':{'policy_input':'t','transport_input':'a'}},False),({}, {'archive_inputs':{'policy_input':'a','transport_input':'t'}},False)]:
 try:exec(code,{'s':s,'p':p,'require':require});accepted=True
 except ValueError:accepted=False
 assert accepted==expected
attach=fn('original_import_stage.py','attach');handler=next(x for x in attach.body if isinstance(x,ast.Try)).handlers[0]
# Only the exact new exception handler is executed on plain witness state.
# These states are not Run/Binding/Owner/Context instances or authority substitutes.
body=[ast.Try(body=[ast.Raise(exc=ast.Name(id='initial',ctx=ast.Load()))],handlers=[copy.deepcopy(handler)],orelse=[],finalbody=[])]
probe=ast.FunctionDef(name='probe',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=x) for x in ['owner','initial']],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[])
spec=importlib.util.spec_from_file_location('cleanup_only',ROOT/P/'owned_io.py');io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)
ns={'io':io};exec(compile(ast.fix_missing_locations(ast.Module(body=[probe],type_ignores=[])),'actual-cleanup-handler','exec'),ns)
for initial,closing in [(ValueError('body'),None),(ValueError('body'),MemoryError('close')),(MemoryError('body'),OSError('close'))]:
 calls=[]
 def close():
  calls.append(1)
  if closing:raise closing
 ledger=types.SimpleNamespace(_poisoned=False,close=close);state=types.SimpleNamespace(poisoned=False,_archive_operations=ledger)
 try:ns['probe'](state,initial);raise AssertionError('failure disappeared')
 except BaseException as actual:assert actual is (closing if isinstance(closing,MemoryError) else initial)
 assert state.poisoned and ledger._poisoned and calls==[1]
# The original default return remains verbatim under an explicit None branch.
default=next(x for x in attach.body if isinstance(x,ast.If) and ast.unparse(x.test)=='archive_transport is None')
assert ast.unparse(default.body[0])=='return (owner, complete_import(owner, prepared, stage_policy=policy))'
calls={ast.unparse(n.func):n.lineno for n in ast.walk(attach) if isinstance(n,ast.Call)}
assert calls['owners.Owner']<calls['archive_owner_operations.attach']<max(n.lineno for n in ast.walk(attach) if isinstance(n,ast.Call) and ast.unparse(n.func)=='complete_import')
assert not {'numpy','torch','scipy','networkx'}&set(sys.modules)
result={'decision':'changed_seam_checks_passed','literal_inverses':3,'reused_original_source_pins':8,'pair_join_controls':4,'failure_cleanup_controls':3,'default_return_preserved':True,'authority_objects_constructed':False,'numerical_imports':False,'evidence':evidence}
(D/'CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence'},sort_keys=True))
