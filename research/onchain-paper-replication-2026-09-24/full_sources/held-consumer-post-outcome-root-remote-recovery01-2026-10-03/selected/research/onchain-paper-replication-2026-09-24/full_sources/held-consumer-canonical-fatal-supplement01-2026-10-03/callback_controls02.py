"""Scalar adapter of actual action/recheck statements, never fake authority.
Only two self._check calls are renamed to an opaque callback parameter, and
the local pure fatal import is bound to its extracted original definition.
No ImportedOriginal/Run/Binding/Owner object or real evidence check is made.
"""
import ast,copy,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
IO=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source/tradingagents/research/onchain_replication/owned_io.py')
iotree=ast.parse(IO.read_bytes());env={};exec(compile(ast.Module(body=[n for n in iotree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('CleanupFailure','_fatal')],type_ignores=[]),'<original-fatal>','exec'),env)
def select_method(raw):
 cls=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='ImportedOriginal')
 return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='with_evidence')
class Adapt(ast.NodeTransformer):
 def __init__(self):self.calls=self.imports=0
 def visit_Call(self,node):
  if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='self' and node.func.attr=='_check':
   self.calls+=1;node.func=ast.Name(id='check',ctx=ast.Load())
  return self.generic_visit(node)
 def visit_ImportFrom(self,node):
  assert node.module=='score_batches' and len(node.names)==1 and node.names[0].name=='_fatal' and node.names[0].asname=='fatal'
  self.imports+=1;return None
def adapter(raw):
 method=select_method(raw);outer=next(n for n in method.body if isinstance(n,ast.Try));body=copy.deepcopy(outer.body)
 module=ast.parse('def pipeline(action,check):\n primary=None\n result=None\n');module.body[0].body+=body
 transform=Adapt();module=transform.visit(module);assert (transform.calls,transform.imports)==(2,1)
 assert not any(isinstance(n,ast.Name) and n.id=='self' for n in ast.walk(module))
 ast.fix_missing_locations(module);e={'fatal':env['_fatal']};exec(compile(module,'<actual-callback-statements-scalar-adapter>','exec'),e);return e['pipeline']
raw=(P/'original_dictionary.py').read_bytes();assert H(raw)=='e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9'
method=select_method(raw);branch=next(n for n in ast.walk(method) if isinstance(n,ast.If) and ast.unparse(n.test)=='primary is None')
lines=raw.decode().splitlines(keepends=True);verbatim=''.join(lines[branch.lineno-1:branch.end_lineno]);body=''.join('    '+line[16:] for line in verbatim.splitlines(keepends=True))
with (P/'exact_reducer02.py').open('x') as f:f.write('"""Exact source slice, indentation-only wrapper; caller supplies actual fatal predicate."""\ndef select(primary,error,fatal):\n'+body+'    return primary\n')
records=[]
for label,first_kind,recheck_kind,note_kind,want in [
 ('first MemoryError survives later SystemExit and diagnostic KeyboardInterrupt',MemoryError,SystemExit,KeyboardInterrupt,'first'),
 ('first SystemExit survives ordinary recheck and diagnostic MemoryError',SystemExit,ValueError,MemoryError,'first'),
 ('ordinary action promotes first recheck fatal',ValueError,MemoryError,RuntimeError,'recheck'),
 ('ordinary action/recheck promotes first diagnostic fatal',ValueError,ValueError,SystemExit,'note'),
 ('successful action cannot bypass failed postcheck',None,ValueError,None,'recheck'),
 ('successful result only after both checks',None,None,None,'return')]:
 trace=[];note_error=note_kind('note') if note_kind else None
 if first_kind:
  class First(first_kind):
   def add_note(self,text):
    trace.append('note')
    if note_error is not None:raise note_error
    return super().add_note(text)
  first=First('first')
 else:first=None
 recheck=recheck_kind('post') if recheck_kind else None;calls=0;value=object();result=object()
 def check():
  global calls
  trace.append('check'+str(calls));calls+=1
  if calls==2 and recheck is not None:raise recheck
  return value
 def action(received):
  assert received is value;trace.append('action')
  if first is not None:raise first
  return result
 try:actual=adapter(raw)(action,check);returned=True
 except BaseException as error:actual=error;returned=False
 expected={'first':first,'recheck':recheck,'note':note_error,'return':result}[want]
 assert actual is expected and returned==(want=='return')
 assert trace[:3]==['check0','action','check1'] and trace.count('action')==1 and calls==2
 if want in ('first','note'):assert trace==['check0','action','check1','note']
 else:assert trace==['check0','action','check1']
 records.append({'case':label,'selected':want,'trace':trace,'selected_object_identity':True,'authority_evidence':False})
for name,body in [('CALLBACK_RESULTS02.json',{'schema_version':1,'source_sha256':H(raw),'cases':records,'exact_reducer_source_lines':[branch.lineno,branch.end_lineno],'verbatim_original_reducer':verbatim,'adapter_changes':['two self._check() calls renamed check()','pure fatal import supplied by exact original AST definition','outer lock/cleanup excluded; tested separately in regression01'],'real_authority_calls':False})]:
 with (P/name).open('x') as f:json.dump(body,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'adversarial_order_cases':len(records),'source_sha256':H(raw),'real_authority_calls':False}))
