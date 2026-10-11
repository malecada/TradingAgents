"""Finite stdlib parser/AST/inverse proof; never execute selected owner/load path."""
import ast,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;checks=[]
for p in P.glob('*.py'):ast.parse(p.read_bytes());checks.append('syntax:'+p.name)
tree=ast.parse((P/'compiled_edge_owner.py').read_text())
selected=[n for n in tree.body if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in {'SOURCE','LIBRARY','ADAPTER','FORMAT','FIELDS'} for t in n.targets) or isinstance(n,ast.FunctionDef) and n.name in {'require','freeze','abi_metadata'}]
env={'Path':Path,'json':json};exec(compile(ast.Module(body=selected,type_ignores=[]),'policy-extraction','exec'),env)
assert env['freeze'](None) is None;checks.append('default_none_no_load')
for value in (False,True,{},[],{'format':env['FORMAT']},{'format':'wrong'}):
 try:env['freeze'](value)
 except (ValueError,TypeError):checks.append('refuse:'+repr(value))
 else:raise AssertionError('bad policy accepted')
for value in ({}, {'format':'cpython-edge-abi-v1'}, {'implementation':'pypy'}):
 try:env['abi_metadata'](json.dumps(value))
 except ValueError:checks.append('bad_abi_refused')
 else:raise AssertionError('bad ABI accepted')
# Reconstruct each baseline using only retained inverse hunks, never patch Main.
def inverse(lines,patch):
 result=[];cursor=0;parts=patch.splitlines(True);i=2
 while i<len(parts):
  header=parts[i];assert header.startswith('@@ ');old=header.split()[1][1:].split(',');start=int(old[0])-1
  result.extend(lines[cursor:start]);cursor=start;i+=1
  while i<len(parts) and not parts[i].startswith('@@ '):
   line=parts[i];tag=line[0];value=line[1:]
   if tag in ' -':assert lines[cursor]==value;cursor+=1
   if tag in ' +':result.append(value)
   i+=1
 result.extend(lines[cursor:]);return ''.join(result)
for name,pin in json.loads((P/'BASELINES01.json').read_text()).items():
 baseline=Path('tradingagents/research/onchain_replication')/name
 restored=inverse((P/name).read_text().splitlines(True),(P/(name+'.inverse.patch')).read_text())
 assert restored==baseline.read_text() and hashlib.sha256(restored.encode()).hexdigest()==pin
 checks.append('literal_inverse:'+name)
# Exact forwarding AST call keywords at both lower layers, no numeric execution.
for name,target in [('matching_immutable_session.py','_advance_owned'),('matching_checkpoint.py','_advance_checked')]:
 t=ast.parse((P/name).read_text());calls=[n for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr==target]
 assert any('edge_chunk_fill' in ast.unparse(n) for n in calls);checks.append('forward:'+name)
result={'status':'PASS_SOURCE_REFUSAL_ONLY','checks':checks,'native_load':False,'scientific_import':False,'actual_runtime_policy_supplied':False,'selected_loader_or_session_executed':False}
(P/'SOURCE_RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
