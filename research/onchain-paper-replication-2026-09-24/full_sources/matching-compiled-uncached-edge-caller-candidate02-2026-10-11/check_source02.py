"""Bounded actual-AST/parser/cleanup/inverse checks; no research imports."""
import ast,hashlib,json
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;checks=[];failure=None
try:
 trees={p.name:ast.parse(p.read_text()) for p in P.glob('*.py')};checks.append('syntax_all')
 def inverse(lines,patch):
  result=[];cursor=0;parts=patch.splitlines(True);i=2
  while i<len(parts):
   header=parts[i];assert header.startswith('@@ ');start=int(header.split()[1][1:].split(',')[0])-1
   result.extend(lines[cursor:start]);cursor=start;i+=1
   while i<len(parts) and not parts[i].startswith('@@ '):
    tag=parts[i][0];value=parts[i][1:]
    if tag in ' -':assert lines[cursor]==value;cursor+=1
    if tag in ' +':result.append(value)
    i+=1
   
  result.extend(lines[cursor:]);return ''.join(result)
 for name,pin in json.loads((P/'BASELINES01.json').read_text()).items():
  restored=inverse((P/name).read_text().splitlines(True),(P/(name+'.inverse.patch')).read_text())
  assert hashlib.sha256(restored.encode()).hexdigest()==pin and restored==(Path('tradingagents/research/onchain_replication')/name).read_text();checks.append('inverse:'+name)
 # Actual source parser functions only, no owner construction/runtime policy.
 tree=trees['compiled_edge_owner.py'];nodes=[n for n in tree.body if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in {'SOURCE','LIBRARY','ADAPTER','FORMAT','FIELDS'} for t in n.targets) or isinstance(n,ast.FunctionDef) and n.name in {'require','freeze','attach','current_policy','options','join','abi_metadata'}]
 env={'Path':Path,'json':json};exec(compile(ast.Module(body=nodes,type_ignores=[]),'edge-metadata','exec'),env)
 assert env['freeze'](None) is None
 receiver=SimpleNamespace();env['attach'](receiver,None);assert env['options'](receiver)=={};checks.append('default_empty_forwarding')
 receiver._compiled_edge_policy=('changed',)
 try:env['options'](receiver)
 except ValueError:checks.append('replaced_policy_refuses')
 else:raise AssertionError('mutable policy accepted')
 for bad in (False,True,{},[],{'format':'wrong'}):
  try:env['freeze'](bad)
  except (ValueError,TypeError):checks.append('policy_refusal')
  else:raise AssertionError('bad policy accepted')
 body=trees['compact_mcm_batched.py'];fns=[n for n in body.body if isinstance(n,ast.FunctionDef) and n.name in {'_edge_policy','_edge_inputs'}]
 select_env={'require':env['require'],'compiled_edge_owner':SimpleNamespace(freeze=env['freeze'])};exec(compile(ast.Module(body=fns,type_ignores=[]),'real-selector-functions','exec'),select_env)
 assert select_env['_edge_policy']({}) is None and select_env['_edge_inputs']({},None) is None;checks.append('selector_unselected_no_run_access')
 for item in ({'compiled_edge_inputs':{}},{'compiled_edge_policy':None},{'compiled_edge_policy':False}):
  try:select_env['_edge_policy'](item)
  except ValueError:checks.append('selector_refusal')
  else:raise AssertionError('bad selector accepted')
 # No fake Run/Admission: prove joined-role syntax and original genuine calls.
 joined=next(n for n in fns if n.name=='_edge_inputs');text=ast.unparse(joined)
 assert "('source', 'adapter', 'library', 'runtime', 'abi')" in text and 'run.read_input(role)' in text and "runtime['runtime_inventory_sha256'] == ad.inputs['environment']['sha256']" in text and "run.read_input('environment')" in text
 checks.append('five_roles_actual_body_and_environment_join')
 # Every real call edge is present; originals keep genuine authority functions.
 for file,needle in [('compact_mcm_batched.py','compiled_edge_policy_value'),('batched_numeric_execution.py','compiled_edge_owner.options(self)'),('batched_numeric_reuse.py','compiled_edge_owner.options(self)'),('batched_pair_executor.py','"edge_chunk_owner":self._edge_owner'),('matching_immutable_session.py','"edge_chunk_fill":self._edge_functions[0][1]'),('matching_checkpoint.py',"'edge_chunk_fill':edge_chunk_fill")]:
  assert needle in (P/file).read_text();checks.append('forward:'+file)
 # Actual combined parent cleanup AST, injected ordinary callbacks only.
 fn=next(n for n in ast.walk(trees['batched_pair_executor.py']) if isinstance(n,ast.FunctionDef) and n.name=='combined_cleanup')
 for mode in ('success','edge_only','normal_and_edge','note_repr_fails'):
  calls=[];primary=KeyboardInterrupt('original primary')
  class BadRepr(OSError):
   def __repr__(self):raise MemoryError('annotation allocation')
  secondary=BadRepr('cleanup') if mode=='note_repr_fails' else OSError('cleanup')
  def normal():
   calls.append('normal')
   if mode in ('normal_and_edge','note_repr_fails'):raise primary
  def edge():
   calls.append('edge')
   if mode!='success':raise secondary
  scope={'normal_cleanup':normal,'edge_cleanup':edge};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-parent-cleanup','exec'),scope)
  caught=None
  try:scope['combined_cleanup']()
  except BaseException as error:caught=error
  assert calls==['normal','edge'] and caught is (None if mode=='success' else secondary if mode=='edge_only' else primary)
  checks.append('independent_cleanup:'+mode)
 # Pin all modified dependencies to candidate bytes; no relaxed source guard.
 tree=trees['batched_numeric_reuse.py'];pins=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE_PINS' for t in n.targets))
 for expr,name in [('accepted','batched_pair_executor.py'),('engine','matching_checkpoint.py'),('engine.ann','matching_annealing.py'),('immutable_session','matching_immutable_session.py')]:
  pin=next(x.elts[1].value for x in pins.elts if ast.unparse(x.elts[0])==expr);assert pin==hashlib.sha256((P/name).read_bytes()).hexdigest();checks.append('dependent_pin:'+name)
 assert hashlib.sha256((P/'compiled_edge_owner.py').read_bytes()).hexdigest() in (P/'batched_numeric_reuse.py').read_text()
 assert env['ADAPTER']==hashlib.sha256((P/'edge_chunk_adapter.py').read_bytes()).hexdigest();checks.append('helper_and_adapter_pins')
except BaseException as error:failure={'type':type(error).__name__,'message':str(error)}
result={'status':'FAILED' if failure else 'PASS_SOURCE_ONLY','checks':checks,'failure':failure,'genuine_run_or_owner_constructed':False,'selected_loader_executed':False,'native_or_scientific_imports':False}
(P/'RESULT02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if failure:raise SystemExit(1)
