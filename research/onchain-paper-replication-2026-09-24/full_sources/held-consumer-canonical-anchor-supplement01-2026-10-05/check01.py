"""Source-bound scalar transcript controls; no Git process or authority creation."""
import ast,copy,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
old=(HERE/'baseline_capsule_builder01.py').read_text();new=(HERE/'capsule_builder01.py').read_text()
addition="HELD_CANONICAL_ANCHOR='55e7d50431654aba952b4541ca506524d9feece1'\nHELD_CANONICAL_PARENT='d443208795f59292c156c5b81b687594efacea4d'\nHELD_CANONICAL_DICTIONARY='e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9'\n"
block="    canonical=anchor==HELD_CANONICAL_ANCHOR\n    if canonical:\n        require(parents==[HELD_CANONICAL_PARENT],'canonical anchor sole parent differs')\n        _held_git(root,'merge-base','--is-ancestor',HELD_SOURCE04,HELD_CANONICAL_PARENT)\n    source04=anchor==HELD_SOURCE04_ANCHOR or canonical"
inverse=new.replace(addition,'',1).replace(block,'    source04=anchor==HELD_SOURCE04_ANCHOR',1).replace("\n    if canonical:expected['tradingagents/research/onchain_replication/original_dictionary.py']=HELD_CANONICAL_DICTIONARY",'',1)
assert inverse==old and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old))
tree=ast.parse(new);ns={}
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith('HELD_') for t in n.targets):exec(compile(ast.Module(body=[n],type_ignores=[]),'constants','exec'),ns)
def require(v,m):
 if not v:raise ValueError(m)
ns['require']=require
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='held_source_plan')
start=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='parents')
end=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='old_path')
anchor_code=compile(ast.Module(body=f.body[start:end],type_ignores=[]),'actual-anchor-branch','exec')
startmap=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='registered')
endmap=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='package')
map_code=compile(ast.Module(body=f.body[startmap:endmap],type_ignores=[]),'actual-map-branch','exec')
def anchor_test(anchor,parent,bad_lineage=False):
 env=dict(ns,root='/mechanical-not-a-capsule',source='1'*40,anchor=anchor);calls=[]
 def git(root,*args):
  calls.append(args)
  if args[:3]==('show','-s','--format=%P'):
   child=args[-1]
   if child==anchor:return (parent+'\n').encode()
   actual=dict(ns['HELD_SOURCE04_LINEAGE'])[child]
   return (('2'*40 if bad_lineage else actual)+'\n').encode()
  assert args[:2]==('merge-base','--is-ancestor');return b''
 env['_held_git']=git;exec(anchor_code,env);return env,calls
def refuse(fn):
 try:fn()
 except ValueError:return
 raise AssertionError('expected refusal')
env,calls=anchor_test(ns['HELD_CANONICAL_ANCHOR'],ns['HELD_CANONICAL_PARENT']);assert env['source04'] and env['canonical'];assert ('merge-base','--is-ancestor',ns['HELD_SOURCE04'],ns['HELD_CANONICAL_PARENT']) in calls
refuse(lambda:anchor_test('3'*40,ns['HELD_CANONICAL_PARENT']))
refuse(lambda:anchor_test(ns['HELD_CANONICAL_ANCHOR'],'4'*40))
refuse(lambda:anchor_test(ns['HELD_CANONICAL_ANCHOR'],ns['HELD_CANONICAL_PARENT'],True))
legacy,_=anchor_test(ns['HELD_SOURCE04_ANCHOR'],dict(ns['HELD_SOURCE04_LINEAGE'])[ns['HELD_SOURCE04_ANCHOR']]);assert not legacy['canonical'] and legacy['source04']
# Actual frozen maps only, no array bodies or imports.
froot=HERE.parent;expected=json.loads((froot/'held-consumer-canonical-root-recipe02-2026-10-04/SOURCE_EXPECTATIONS02.json').read_bytes())
cap=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source')
inv=json.loads((cap/'cold_prep/source_inventory.json').read_bytes());baseline={x['target']:x['sha256'] for x in inv['source_inventory']}
def map_test(mapping,selected=env):
 scope=dict(selected,baseline=baseline,rows=[{'path':k,'sha256':v} for k,v in mapping.items()]);exec(map_code,scope)
map_test(expected['candidate']);changed=dict(expected['candidate']);changed['tradingagents/research/onchain_replication/original_dictionary.py']='0'*64;refuse(lambda:map_test(changed))
changed=dict(expected['candidate']);changed['tradingagents/research/onchain_replication/training.py']='0'*64;refuse(lambda:map_test(changed))
map_test(expected['baseline'],legacy);refuse(lambda:map_test(expected['candidate'],legacy))
print('PASS: exact byte/AST inverse; fixed canonical anchor,parent,lineage; canonical/legacy source maps; wrong anchor,parent,lineage,dictionary and unrelated source refused. No Git/native/numerical execution.')
