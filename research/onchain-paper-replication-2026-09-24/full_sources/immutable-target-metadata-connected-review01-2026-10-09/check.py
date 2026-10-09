import ast,hashlib,json,os,resource,signal,time,types
from pathlib import Path
D=Path(__file__).resolve().parent;P=D.parent/'immutable-target-metadata-connected01-2026-10-09';S=D.parents[3]/'tradingagents/research/onchain_replication'
os.sched_setaffinity(0,{3});os.nice(10)
for r,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)):resource.setrlimit(r,(v,v))
signal.alarm(30);start=time.monotonic_ns();(D/'LIMITER01.json').write_text(json.dumps({'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'wall_seconds':30},indent=2)+'\n')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert h(P/'MANIFEST01.json').startswith('f056b875')
for name,changes in json.loads((P/'CHANGES01.json').read_text()).items():
 text=(P/name).read_text()
 for a,b in reversed(changes):assert text.count(b)==1;text=text.replace(b,a)
 assert text==(S/name).read_text();assert ast.dump(ast.parse(text))==ast.dump(ast.parse((S/name).read_text()))
t=ast.parse((S/'provenance.py').read_text());ns={'json':json};exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('thaw','canonical_bytes')],type_ignores=[]),'actual_encoder','exec'),ns);canonical=ns['canonical_bytes']
t=ast.parse((P/'immutable_target_metadata.py').read_text());t.body=[n for n in t.body if not isinstance(n,ast.ImportFrom) or not n.level];ns={'canonical_bytes':canonical};exec(compile(t,'actual_helper','exec'),ns);helper=types.SimpleNamespace(**ns)
# Distinct Unicode/key/alias/negative-zero roundtrip and exact private backing.
a={'nested':[{'é':'😀','zero':-0.0}], 'limits':[-2**63,2**63-1]};before=canonical(a);anchor=helper.snapshot(a);assert anchor[1]==before and canonical(anchor[0])==before;a['nested'][0]['é']='changed';a['limits'].clear();assert canonical(anchor[0])==before
try:anchor[0]['nested'][0]['é']='replacement'
except TypeError:pass
else:raise AssertionError('private backing mutable')
x=types.SimpleNamespace(_execution_anchor=anchor,_execution_anchor_pin=anchor,_execution=anchor[0],_execution_pin=anchor[1]);helper.current(x);x._execution_anchor=(anchor[0],anchor[1])
try:helper.current(x)
except ValueError:pass
else:raise AssertionError('equal replacement anchor accepted')
# Cardinality/cycle/UTF8/int/exact-type bounds refuse without retained alias.
cycle=[];cycle.append(cycle)
class Foreign(dict):pass
for value in (cycle,{'x':'😀'*20000},[None]*8192,{'x':2**63},Foreign(x=1)):
 try:helper.snapshot(value)
 except ValueError:pass
 else:raise AssertionError('unsupported snapshot accepted')
# Fresh decoder rejoin is unchanged, actual AST executes without authority fabrication.
t=ast.parse((S/'imported_authority_lease.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_checked_value');f.body=[n for n in f.body if not isinstance(n,ast.ImportFrom)];scope={'require':helper.require,'json':json,'canonical_bytes':canonical};exec(compile(ast.Module(body=[f],type_ignores=[]),'actual_rejoin','exec'),scope);current={'id':'owner','values':[1]};original={'source':'immutable'};raw=canonical({'current':current,'original':original});pin=canonical(current);value=scope['_checked_value'](raw,raw,current,pin,original);snap=helper.snapshot(value);current['values'].append(2)
try:scope['_checked_value'](raw,raw,current,pin,original)
except ValueError:pass
else:raise AssertionError('live-root mutation ignored')
assert snap[0]['current']['values']==(1,)
# Connected keyword reaches every original Target creation and producer call.
caller=ast.parse((P/'real_pilot_import_caller.py').read_text());calls=[n for n in ast.walk(caller) if isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id=='Target') or (isinstance(n.func,ast.Attribute) and n.func.attr=='produce_imported'))];assert len(calls)==3 and all('immutable_execution' in ast.unparse(n) for n in calls)
(D/'RESULT01.json').write_text(json.dumps({'status':'PASS_STDLIB_SOURCE_ONLY','three_literal_ast_inverses':True,'unicode_alias_negativezero_roundtrip':True,'anchor_identity_mutation_refused':True,'bounded_type_cycle_cardinality_utf8_integer_refusals':True,'fresh_decoder_mutable_root_refusal':True,'three_forwarding_sites':True,'elapsed_ns':time.monotonic_ns()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'qualification':'Actual extracted metadata helper/decoder, no genuine authority object or numerical import.'},indent=2)+'\n');print('PASS')
