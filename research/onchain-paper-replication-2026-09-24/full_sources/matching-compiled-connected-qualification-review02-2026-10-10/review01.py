"""Changed-harness source/entry review only. Never calls execute or native APIs."""
import ast,builtins,copy,hashlib,importlib.util,json,os,resource,signal,sys,time,types
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];Q=F/'matching-compiled-connected-qualification02-2026-10-10';O=F/'matching-compiled-connected-qualification01-2026-10-10';C=F/'matching-compiled-normalization-connected04-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(15,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(20);assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[];refs={};observations={}
def sha(b):return hashlib.sha256(b).hexdigest()
def body(p):
 b=p.read_bytes();refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
def ok(n,v=True):assert v,n;checks.append(n)
original_import=builtins.__import__
def guarded(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes','array','tradingagents'},name
 return original_import(name,*a,**kw)
builtins.__import__=guarded
m=body(Q/'MANIFEST01.json');ok('frozen qualification02 manifest',sha(m)=='b6eb54c3d8aa37b98b45a0f7bd1975d6f2e33821c489d25e098d4c4fb64d104b')
for section,base in [('files',Q),('references',F)]:
 for n,v in json.loads(m)[section].items():
  b=body(base/n);ok('manifest '+n,sha(b)==v['sha256'] and len(b)==v['bytes'])
source=(Q/'qualify.py').read_bytes();ok('exact qualification02 script',sha(source)=='07374bbcc71f81e1932d5a164e08f1bf6bd5d4a0a2235284e9f688659d7cd920')
ok('accepted qualification01 review',sha((F/'matching-compiled-connected-qualification-review01-2026-10-10/REVIEW01.json').read_bytes())=='58f551ff6041cc0ea8ebcdffa28e4e78f8acb96978f225a5e8f0213b39e93c14')
ok('accepted source04 review',sha((F/'matching-compiled-normalization-connected-review04-2026-10-10/REVIEW01.json').read_bytes())=='a296744020b0169cbd2497da8b679abea35d31b0f2641dfb68922a0e05d5e6aa')
for n in ('CASES.json','matching-config.json'):ok('unchanged01 '+n,(Q/n).read_bytes()==body(O/n))
req=json.loads((Q/'SOURCE_REQUIREMENTS.json').read_bytes());cases=json.loads((Q/'CASES.json').read_bytes())
expected={'matching_annealing.py','matching_checkpoint.py','matching_immutable_session.py','batched_pair_executor.py','batched_numeric_reuse.py','batched_numeric_execution.py','compiled_normalization_policy.py','compiled_small_lse.py'}
ok('exact eight04 files',set(req['installed_module_sha256'])==expected)
for n,d in req['installed_module_sha256'].items():ok('exact04 pin '+n,sha(body(C/n))==d)
def apply(data,patch):
 if not patch:return data
 lines=data.decode().splitlines(True);p=patch.decode().splitlines(True);out=[];cursor=0;i=2
 while i<len(p):
  h=p[i];assert h.startswith('@@ ');pos=int(h.split()[1][1:].split(',')[0])-1;i+=1;assert cursor<=pos;out.extend(lines[cursor:pos]);cursor=pos
  while i<len(p) and not p[i].startswith('@@ '):
   q=p[i];i+=1
   if q[0] in ' -':assert lines[cursor]==q[1:];cursor+=1
   if q[0] in ' +':out.append(q[1:])
 out.extend(lines[cursor:]);return ''.join(out).encode()
for n in ('qualify.py','SOURCE_REQUIREMENTS.json'):ok('exact declared forward delta '+n,apply(body(O/n),(Q/(n+'.from01.patch')).read_bytes())==(Q/n).read_bytes())
t=ast.parse(source);ot=ast.parse((O/'qualify.py').read_bytes());tops=lambda t:{n.name:n for n in t.body if isinstance(n,ast.FunctionDef)};top=tops(t);oldtop=tops(ot);ex=top['execute'];nested=tops(ex);oldnested=tops(oldtop['execute']);src=ast.unparse
for n in top:
 if n!='execute':ok('unchanged entry/parser function '+n,ast.dump(top[n])==ast.dump(oldtop[n]))
for n in oldnested:
 if n!='checkpoint':ok('unchanged nested comparison '+n,ast.dump(nested[n])==ast.dump(oldnested[n]))
# Actual metadata import + preflight against current uninstalled source, no mocked
# runtime references and no fabricated selected policy.
spec=importlib.util.spec_from_file_location('qualification02_metadata',Q/'qualify.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
frozen=q.inputs();ok('actual exact input preflight',frozen['CASES.json']==cases)
try:q.preflight(R,P/'ABSENT_ROOT_POLICY.json')
except ValueError as e:
 observations['current_main_preflight_refusal']={'type':type(e).__name__,'message':str(e)}
 ok('uninstalled Main refuses before absent Root policy/imports',str(e).startswith('exact input/source SHA256 differs:') and 'matching_annealing.py' in str(e))
else:raise AssertionError('uninstalled candidate admitted')
text=src(ex);checkpoint=src(nested['checkpoint']);nb=src(nested['numeric_backend'])
ok('genuine load returned only after state equality',checkpoint.index('restored = engine.load(')<checkpoint.index('need(before == state_body(restored)')<checkpoint.index('return (digest, restored)'))
ok('untransferred restored state closes',"if restored is not None and (not transferred):" in checkpoint and 'engine.close(restored)' in checkpoint)
ok('checkpoint normalization/hardening both routes retained',all(x in text for x in ("roundtrips == 0 and states[0]['annealing']['phase'].startswith('normalize')","roundtrips == 1 and states[0]['phase'] == 'hardening'",'for route, state in enumerate(states):','if roundtrips < 2:', 'checkpoint(state, path, a, b, retain=True)',"'route': route", "'state': restored")))
ok('same genuine session advances loaded state',"owned[restored['route']].advance(restored['state'], max_operations=budget)" in text and "need(resumed_used == used[restored['route']]" in text)
ok('every resumed step compares complete state',"state_equal(restored['state'], states[restored['route']])" in text and "restored['continued_advances'] += 1" in text)
ok('all four restored states must actually finish',all(x in text for x in ('need(len(resumed) == 4',"restored['continued_advances'] > 0 and restored['state']['phase'] == 'done'",'result.assignment.tobytes() == expected.assignment.tobytes()','result.soft_assignment.tobytes() == expected.soft_assignment.tobytes()','score(result) == score(expected)')))
ok('resumed state cleanup included',"for state in states + [restored['state'] for restored in resumed]:" in text and 'engine.close(restored)' in text)
loop=next(n for n in ast.walk(ex) if isinstance(n,ast.While));looptext=src(loop)
ok('aggregate cap before all advance calls',looptext.index('advance_calls + 2 + len(resumed) <= 2 *')<looptext.index('s.advance(state'))
ok('both original and resumed calls accounted','advance_calls += 2' in looptext and 'advance_calls += 1' in looptext)
cap=next(n.args[0] for n in ast.walk(loop) if isinstance(n,ast.Call) and src(n.func)=='need' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='original aggregate direct advance allowance exhausted by continuation')
for used,borrowed,expected_result in [(8190,0,True),(8191,0,False),(8188,2,True),(8189,2,False),(8186,4,True),(8187,4,False)]:
 value=eval(compile(ast.Expression(cap),'actual-cap','eval'),{'advance_calls':used,'resumed':[None]*borrowed,'cases':cases});ok('actual cap boundary '+str((used,borrowed)),value is expected_result)
ok('logical4096 cap retained',"step < cases['max_advances_per_pair']" in looptext and cases['max_advances_per_pair']==4096)
ok('no cap/tolerance scientific shortening',cases['operation_budgets']==[1,7,31] and cases['cpu_seconds']==120 and cases['wall_seconds']==180 and cases['address_space_bytes']==3*1024**3 and not any(x in text for x in ('allclose','isclose','settrace','setprofile')))
# Inspect code objects without executing the helper/native imports: closure
# nonlocals referenced by the harness must really exist in exact04 sources.
def code_children(code):
 for c in code.co_consts:
  if isinstance(c,types.CodeType):yield c;yield from code_children(c)
owner_codes=list(code_children(compile((C/'compiled_normalization_policy.py').read_bytes(),'policy-source','exec')))
borrow=next(c for c in owner_codes if c.co_qualname=='BackendOwner.__init__.<locals>.borrow');close=next(c for c in owner_codes if c.co_qualname=='BackendOwner.__init__.<locals>.close')
ok('real04 borrow observation fields exist',{'active','backend','opened'}<=set(borrow.co_freevars))
ok('real04 close observation fields exist',{'closed','close_attempted','close_error'}<=set(close.co_freevars))
helper_codes=list(code_children(compile((C/'compiled_small_lse.py').read_bytes(),'helper-source','exec')))
lse=next(c for c in helper_codes if c.co_name=='lse');live=next(c for c in helper_codes if c.co_name=='_live')
ok('real04 helper observation fields exist',{'_fn','_live'}<=set(lse.co_freevars) and {'_fd','_pin'}<=set(live.co_freevars))
ok('genuine memo owner and readonly observations',all(x in nb for x in ('executor.memo.executor._normalization_owner', 'owner is executor.memo.executor._normalization_owner_pin','owner.current()','inspect.getclosurevars(owner.borrow).nonlocals',"closure['active'] is None", "closure['opened'] is False and backend is None", "backend.loaded()",'backend.current()','kernel_backend(backend)')))
ok('default owner absent required',"need(owner is None, 'default numeric route unexpectedly owns backend')" in nb)
ok('same backend and original descriptor across occurrences',"observed_backend is held_backend and observed['fd'] == held_fd" in text and 'observed_owner is held_owner' in text)
ok('actual NumericExecution finish closes before FD proof',text.index('binding = executor.finish()')<text.index('closed_fd(held_fd)')<text.index('closure = numeric.verify(root, binding)'))
ok('terminal owner and close error observed',"closed['closed'] is True and closed['close_attempted'] is True and (closed['close_error'] is None)" in text)
ok('eight genuine occurrences and verified4compute4reuse',len(cases['graph_cases'])*cases['numeric_repeats']==8 and all(x in text for x in ("binding['computed'] == len(population)","binding['reused'] == len(population)",'numeric.verify(root, binding)')))
ok('actual load count unobserved and overhead declared',"'load_attempt_count': 'NOT_OBSERVED; opened flag and stable backend/FD only; profiling forbidden by genuine guard'" in text and "'timing_includes_readonly_observation_overhead': True" in text and "'mapping_unload_claim': False" in text)
# Read-only closure access must not introduce writes to source modules or their
# inspected closures, tracing, fake authority or replacement method calls.
for n in ast.walk(ex):
 if isinstance(n,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
  targets=n.targets if isinstance(n,ast.Assign) else [n.target]
  for target in targets:
   for x in ast.walk(target):
    if isinstance(x,ast.Attribute) and isinstance(x.value,ast.Name):ok('no module/owner attribute mutation line'+str(x.lineno),x.value.id not in {'engine','annealing','sessions','numeric','policy_module','owner','held_owner','backend','held_backend'})
    if isinstance(x,ast.Subscript) and isinstance(x.value,ast.Name):ok('no inspected closure mutation line'+str(x.lineno),x.value.id not in {'closure','closed'})
ok('entry command genuine action flag',all(x in src(top['main']) for x in ('--runtime-policy','--output','--execute-after-terminal','preflight(CHECKOUT, args.runtime_policy)','execute(args.output, frozen, selected, record)')))
ok('failing mismatch retained and re-raised',"record['status'] = 'FAILED_OR_UNAVAILABLE'" in text and "write(output / 'RESULT.json', record)" in text)
ok('external terminal/admission precondition explicit','Root admission and pilot terminal status remain external preconditions' in src(top['preflight']))
ok('no prohibited imports and execute uncalled',not {'numpy','scipy','torch','ctypes','array','tradingagents'}&set(sys.modules))
ok('manifest remains frozen',body(Q/'MANIFEST01.json')==m)
r=dict(disposition='ACCEPT_SOURCE_ENTRY_ONLY_UNEXECUTED',checks=checks,check_count=len(checks),observations=observations,body_references=refs,numerical_execute_called=False,valid_runtime_policy_supplied=False,actual_admission=False,sourceguard_patched=False,elapsed_ns=time.perf_counter_ns()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,limits=dict(cpu=3,cpu_seconds=15,alarm_seconds=20,external_seconds=25,address_space_bytes=512*1024**2,file_size_bytes=4*1024**2))
(P/'RESULT01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('disposition','check_count','elapsed_ns','peak_rss_kib')}))
