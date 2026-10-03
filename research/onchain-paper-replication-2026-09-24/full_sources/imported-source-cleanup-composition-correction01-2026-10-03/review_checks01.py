"""Independent source and exception-seam review; no package/numerical imports."""
import ast,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;F=P.parent;ROOT=P.parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((P/'MANIFEST01.json').read_bytes())
assert sha((P/'MANIFEST01.json').read_bytes())=='6fe9331f25d93c93feb399f2ed644afb5aee539dac51fda2b564e9c5c08e6588'
for item in m['files']+m['dependencies']:
 path=(P/item['path']) if '/' not in item['path'] else ROOT/item['path'];raw=path.read_bytes();assert len(raw)==item['bytes'] and sha(raw)==item['sha256']
inv=json.loads((F/'original-import-native-successor-preparation03-2026-10-03/source_inventory01.json').read_bytes());rows={r['target']:r for r in inv['source_inventory']};package={k:r for k,r in rows.items() if k.startswith('tradingagents/')};assert len(package)==142
bodies={k:(ROOT/r['origin']).read_bytes() for k,r in rows.items()}
for k,r in rows.items():assert len(bodies[k])==r['bytes'] and sha(bodies[k])==r['sha256']
bodies['tradingagents/research/onchain_replication/compact_mcm.py']=(P/'compact_mcm.py').read_bytes()
missing=[];edges=[]
for target,raw in bodies.items():
 if not target.endswith('.py'):continue
 for node in ast.walk(ast.parse(raw)):
  if isinstance(node,ast.ImportFrom):
   if node.level:
    parent=list(Path(target).parent.parts);base=parent[:len(parent)-node.level+1];parts=base+(node.module.split('.') if node.module else [])
    wanted=['/'.join(parts)]+([] if node.module else ['/'.join(parts+[a.name]) for a in node.names if a.name!='*'])
   elif node.module and node.module.startswith('tradingagents'):wanted=[node.module.replace('.','/')]
   else:continue
   for name in wanted:
    if not name.startswith('tradingagents/'):continue
    if name+'.py' not in bodies and name+'/__init__.py' not in bodies:missing.append((target,node.lineno,name))
    edges.append((target,name))
  elif isinstance(node,ast.Import):
   for alias in node.names:
    if alias.name.startswith('tradingagents.'):
     name=alias.name.replace('.','/')
     if name+'.py' not in bodies and name+'/__init__.py' not in bodies:missing.append((target,node.lineno,name))
assert not missing,repr(missing)
print('Selected static import closure:',len(package),'package bodies;',len(edges),'local import edges; no unresolved relative/absolute research module imports.')
# Actual cleanup code, source extracted into a pure stdlib namespace.
own=ROOT/rows['tradingagents/research/onchain_replication/owned_io.py']['origin'];env={};exec(compile(own.read_bytes(),str(own),'exec'),env)
io=SimpleNamespace(**{k:env[k] for k in ('_cleanup','CleanupFailure')})
tree=ast.parse((P/'compact_mcm.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked');block=next(n for n in fn.body if isinstance(n,ast.Try));handler=block.handlers[0]
# Exact handler in a synthetic throwing function; no producer/Owner instantiated.
definition=ast.FunctionDef(name='boundary',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=x) for x in ('initial','stream','log','owner','io','claimed','fd')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[ast.Try(body=[ast.Raise(exc=ast.Name(id='initial',ctx=ast.Load()))],handlers=[handler],orelse=[],finalbody=[])],decorator_list=[])
ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[definition],type_ignores=[])),'actual-exception-handler','exec'),ns)
for mode in ('ordinary','body-memory','close-memory','fail-ordinary'):
 calls=[];primary=MemoryError('body fatal') if mode=='body-memory' else ValueError('body');fatal=MemoryError('close fatal');owner=SimpleNamespace(poisoned=False,identity='synthetic-no-authority')
 class Stream:
  closed=False
  def close(self):
   calls.append('stream.close')
   if mode=='close-memory':raise fatal
 class Log:
  closed=False
  def fail(self,reason):
   calls.append(('log.fail',reason))
   if mode=='fail-ordinary':raise OSError('failure receipt uncertain')
  def close(self):calls.append('log.close')
 try:ns['boundary'](primary,Stream(),Log(),owner,io,False,None)
 except BaseException as observed:
  expected=fatal if mode=='close-memory' else primary
  assert (isinstance(observed,io.CleanupFailure) if mode=='fail-ordinary' else observed is expected)
 else:raise AssertionError('failure was swallowed')
 assert calls==['stream.close',('log.fail','MCM producer failed'),'log.close'] and owner.poisoned is True
 print('Actual handler ordered close/fail/close and poison:',mode)
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print('No numerical/package import, array, genuine Owner, claim or guard.')
