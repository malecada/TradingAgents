import ast,copy,hashlib,importlib.util,json,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-canonical-fatal-supplement01-2026-10-03';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
def raw(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2,'typed bounded body');return p.read_bytes()
mraw=raw(P/'MANIFEST02.json');ck(sha(mraw)=='912fd8b38ee3ea1d7e9431e3072c61448226a04115e155d250ddd315a945cc93','final manifestpin');manifest=json.loads(mraw)
for r in manifest['members']:
 p=P/r['path'];b=raw(p);ck(len(b)==r['bytes'] and sha(b)==r['sha256'] and stat.S_IMODE(p.lstat().st_mode)==r['mode'],'all17 actual member pins')
ck({p.name for p in P.iterdir()}=={r['path'] for r in manifest['members']}|{'MANIFEST02.json'},'exact candidate directory membership')
origins=json.loads(raw(P/'ORIGINS01.json'))
for r in origins['references']:
 p=Path(r['path']);b=raw(p);ck(len(b)==r['bytes'] and sha(b)==r['sha256'] and stat.S_IMODE(p.lstat().st_mode)==r['mode'],'real prior source/review origin')
new=raw(P/'original_dictionary.py');old=raw(P/'baseline93c.py');ck(sha(new)=='e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9' and sha(old)=='93c0cd1ae882d51df185458ce7304a46dfb66dc7ca337285039541fa70176e88','new oldpin');inv=json.loads(raw(P/'INVERSE01.json'));ck(new.decode().count(inv['new_text'])==1 and new.decode().replace(inv['new_text'],inv['old_text']).encode()==old,'fullbyte inverse');restored=ast.parse(new.decode().replace(inv['new_text'],inv['old_text']));ck(ast.dump(restored)==ast.dump(ast.parse(old)),'allotherAST inverse')
owned=Path(origins['references'][-1]['path']);spec=importlib.util.spec_from_file_location('actual_owned_scalar',owned);io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)
def method(body):
 t=ast.parse(body);return next(x for n in t.body if isinstance(n,ast.ClassDef) and n.name=='ImportedOriginal' for x in n.body if isinstance(x,ast.FunctionDef) and x.name=='with_evidence')
def reducer(body):
 nodes=[n for n in ast.walk(method(body)) if isinstance(n,ast.If) and ast.unparse(n.test)=='primary is None'];ck(len(nodes)==1,'one exact selection reducer');fn=ast.FunctionDef(name='select',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=n) for n in ['primary','error','fatal']],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[copy.deepcopy(nodes[0]),ast.Return(value=ast.Name(id='primary',ctx=ast.Load()))],decorator_list=[]);mod=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));ns={};exec(compile(mod,'<exact reducer AST>','exec'),ns);return ns['select']
before=reducer(old);after=reducer(new);trials=[]
def throwing(base,diagnostic,trace):
 class Actual(base):
  def add_note(self,note):trace.append(note);raise diagnostic
 return Actual('primary')
# RED is observed behavior, not an altered candidate or manufactured authority.
trace=[];diagnostic=RuntimeError('actual note failure');primary=throwing(MemoryError,diagnostic,trace);error=ValueError('later ordinary')
try:result=before(primary,error,io._fatal)
except BaseException as escaped:ck(escaped is diagnostic and escaped is not primary,'RED exact93c loses original fatal');red={'original_type':type(primary).__mro__[1].__name__,'later_type':type(error).__name__,'escaped_type':type(escaped).__name__,'escaped_is_diagnostic':escaped is diagnostic,'original_preserved':escaped is primary,'note_attempts':len(trace)}
else:raise AssertionError('RED not reproduced')
(O/'RED01.json').write_text(json.dumps(red,indent=2)+'\n')
for pclass in [ValueError,MemoryError,SystemExit,KeyboardInterrupt]:
 for eclass in [ValueError,MemoryError,SystemExit,KeyboardInterrupt]:
  for dclass in [RuntimeError,MemoryError,SystemExit,KeyboardInterrupt]:
   trace=[];diagnostic=dclass('diagnostic');primary=throwing(pclass,diagnostic,trace);error=eclass('postcheck');result=after(primary,error,io._fatal)
   expected=primary if io._fatal(primary) else error if io._fatal(error) else diagnostic if io._fatal(diagnostic) else primary
   ck(result is expected,'GREEN actual object priority');ck(len(trace)==(0 if io._fatal(error) and not io._fatal(primary) else 1),'one diagnostic only in else branch')
   if result is error:ck(error.__cause__ is primary,'unchanged laterfatal cause link')
   trials.append({'primary':pclass.__name__,'later':eclass.__name__,'diagnostic':dclass.__name__,'selected':'primary' if result is primary else 'later' if result is error else 'diagnostic','note_attempts':len(trace)})
for eclass in [ValueError,MemoryError,SystemExit]:
 e=eclass('no primary');ck(after(None,e,io._fatal) is e,'no primary identity')
p=ValueError('primary');e=ValueError('postcheck');ck(after(p,e,io._fatal) is p and p.__notes__==['post-callback evidence/authority check failed: ValueError'],'successful note exact text')
# Exact callback/check body with declared scalar adaptation only. No self/Owner/Run.
class Adapt(ast.NodeTransformer):
 def visit_ImportFrom(self,node):return ast.Pass()
 def visit_Call(self,node):
  node=self.generic_visit(node)
  if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='self' and node.func.attr=='_check':node.func=ast.Name(id='check',ctx=ast.Load())
  return node
m=method(new);block=next(n for n in m.body if isinstance(n,ast.Try));body=ast.parse('primary=None\nresult=None').body+[Adapt().visit(copy.deepcopy(n)) for n in block.body];fn=ast.FunctionDef(name='pipeline',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=n) for n in ['check','action','fatal']],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[]);ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<exact callback AST scalar adaptation>','exec'),ns);pipeline=ns['pipeline'];callbacks=[]
for first_error,action_error,last_error in [(None,None,None),(None,MemoryError('action'),ValueError('check')),(None,ValueError('action'),SystemExit('check')),(None,None,ValueError('check')),(ValueError('first'),None,None)]:
 trace=[];value=object();returned=object();count=[0]
 def check():
  i=count[0];count[0]+=1;trace.append('check'+str(i));err=first_error if i==0 else last_error
  if err is not None:raise err
  return value
 def action(v):
  trace.append('action');ck(v is value,'exact callback input')
  if action_error is not None:raise action_error
  return returned
 try:result=pipeline(check,action,io._fatal)
 except BaseException as escaped:
  expected=first_error if first_error is not None else action_error if action_error is not None and io._fatal(action_error) else last_error if last_error is not None and (action_error is None or io._fatal(last_error)) else action_error
  ck(escaped is expected,'callback actual chosen identity')
 else:ck(first_error is action_error is last_error is None and result is returned,'result only after both checks')
 ck(trace==(['check0'] if first_error is not None else ['check0','action','check1']),'exact callback once ordered');callbacks.append(trace)
for primary,cleanup in [(MemoryError('body'),SystemExit('cleanup')),(SystemExit('body'),MemoryError('cleanup')),(ValueError('body'),MemoryError('cleanup'))]:
 count=[]
 def close():count.append(1);raise cleanup
 try:
  try:raise primary
  finally:io._release(close)
 except BaseException as escaped:ck(escaped is (primary if io._fatal(primary) else cleanup) and count==[1],'real owned cleanup firstfatal once')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports');out={'decision':'ACCEPTED_NARROW_DIAGNOSTIC_GUARD_SOURCE_ONLY','checks':len(checks),'matrix_cases':len(trials),'trials':trials,'callback_traces':callbacks,'red':red,'source_sha256':sha(new),'baseline_sha256':sha(old),'full_byte_and_other_AST_inverse':True,'fake_authority_constructed':False,'source_installed':False};(O/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['trials','callback_traces']},indent=2))
