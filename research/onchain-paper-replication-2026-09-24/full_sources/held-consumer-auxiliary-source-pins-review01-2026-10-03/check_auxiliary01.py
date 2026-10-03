"""Actual-source/metadata investigation only; no legacy generator or authority."""
import ast,copy,hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;C=F/'held-consumer-auxiliary-source-pins-preparation01-2026-10-03'
S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-04/source')
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((C/'MANIFEST01.json').read_bytes())=='71f0e4a7afc7c7fad26f902ad2b078698eda1a51154e7e0d4fc6f183fdb9adb8'
members=json.loads((C/'MANIFEST01.json').read_bytes())['files']
if isinstance(members,dict):members=[dict(v,path=k) for k,v in members.items()]
for r in members:
 b=(C/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
def load(path,names,env):
 tree=ast.parse(path.read_bytes());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env)
names={'canonical','sha','require','HELD_ROLES','AUXILIARY_ROLES','_held_ref','render_held_auxiliary_declaration','held_auxiliary_metadata','held_input_plan','generate_held_arrays'}
G={'Path':Path,'json':json,'hashlib':hashlib};load(C/'generate_inputs01.py',names,G)
OLD={'Path':Path,'json':json,'hashlib':hashlib};load(C/'generate_inputs01.py.baseline04.txt',names,OLD)
fixtures={'G':G};load(C/'test_auxiliary01.py',{'role','fixture'},fixtures);data=fixtures['fixture']
def refusal(call):
 try:call()
 except (ValueError,TypeError,KeyError) as e:return str(e)
 raise AssertionError('unexpected acceptance')
source,roles=data();oldroles={k:v for k,v in roles.items() if k in OLD['HELD_ROLES']}
reason=refusal(lambda:OLD['held_input_plan'](oldroles,source));assert reason=='registered199 source map differs'
out=G['held_input_plan'](roles,source);assert out['auxiliary_metadata']['admission_source_count']==204 and out['execution_admitted'] is False
checks=['actual old199 equality RED; new204 synthetic metadata join GREEN']
mutations={
 'extra_source':lambda s,r:r['registration']['document']['experiments']['future-held-fixture']['source_files'].update(extra='e'*64),
 'missing_code':lambda s,r:r['registration']['document']['experiments']['future-held-fixture']['source_files'].pop(next(iter(s['source_files']))),
 'missing_auxiliary':lambda s,r:r.update(auxiliary_sources=None),
 'bool_count':lambda s,r:r['auxiliary_sources']['document'].update(entry_count=True),
 'wrong_map':lambda s,r:r['auxiliary_sources']['document'].update(implementation_map_sha256='f'*64),
 'approval_pending':lambda s,r:r['budget_review']['document'].update(decision='pending'),
 'approval_hash':lambda s,r:r['budget_review']['document'].update(extension_sha256='f'*64),
 'family':lambda s,r:r['budget_extension']['document'].update(base_family={}),
 'initial_absent':lambda s,r:r['budget_extension']['document'].update(initial_experiment='absent'),
 'charter_ref':lambda s,r:r['registration']['document']['experiments']['future-held-fixture']['charter'].update(path='other.md'),
 'declaration_alias_registration':lambda s,r:r['auxiliary_sources']['reference'].update(path=r['registration']['reference']['path']),
 'path_traversal':lambda s,r:r['auxiliary_sources']['reference'].update(path='../auxiliary.json'),
 'private_path':lambda s,r:r['auxiliary_sources']['reference'].update(path='.git/auxiliary.json'),
 'source_collision':lambda s,r:r['charter']['reference'].update(path=next(iter(s['source_files']))),
 'program':lambda s,r:r['registration']['document'].update(program_id='different'),
 'confirmation':lambda s,r:r['registration']['document']['experiments']['future-held-fixture'].update(stage='confirmation'),
 'unknown_declaration':lambda s,r:r['auxiliary_sources']['document'].update(source='1'*40),
 'declaration_selfhash':lambda s,r:r['auxiliary_sources']['document'].update(sha256='f'*64),
}
for name,mutate in mutations.items():
 s,r=data();mutate(s,r);refusal(lambda:G['held_input_plan'](r,s));checks.append(name+' refusal')
s,r=data();null=G['held_input_plan']({},s);assert null['auxiliary_metadata'] is None and len(null['remaining_roles'])==15 and null['execution_admitted'] is False
refusal(lambda:G['generate_held_arrays']());checks.append('null15 roles/noauthority and numerical generation refused')
# Actual Source04 builder and real read-only Git; no body reader needed before
# the deterministic lineage refusal. All subprocess calls prohibit protocols.
builder_path=S/'fixture_tools/capsule_builder01.py'
B={'Path':Path,'os':os,'subprocess':subprocess,'json':json,'hashlib':hashlib}
load(builder_path,{'require','HELD_S2','HELD_OLD_INVENTORY','HELD_IO','HELD_COUNTS','HELD_PACKAGE_CHANGES','HELD_READER','HELD_ADDITIONS','HELD_SUCCESSOR_HELPERS','_held_git','held_source_plan'},B)
composition=json.loads((F/'held-consumer-root-source-composition04-2026-10-03/SOURCE_COMPOSITION04.json').read_bytes())
rows=[{'path':r['target'],'sha256':r['sha256'],'bytes':r['bytes']} for r in composition['source_entries']]
rows.sort(key=lambda x:x['path'])
actual_reason=refusal(lambda:B['held_source_plan'](S,composition['actual_source_commit'],composition['actual_148_package_anchor'],rows))
assert actual_reason=='held anchor must genuinely descend directly from original S2'
actual_parent=B['_held_git'](S,'show','-s','--format=%P',composition['actual_148_package_anchor']).decode().strip()
assert actual_parent=='903488c49ad25e8026ec849a1c8b30ca5f90bcff'
# Independently reconstruct the later unchanged-source guard from actual function
# statements, without bypassing real admission or modifying any source.
tree=ast.parse(builder_path.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='held_source_plan')
start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='old_path' for t in n.targets))
end=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='package' for t in n.targets))
def read(root,rel,pin,count):
 b=(root/rel).read_bytes();assert len(b)==count and sha(b)==pin;return b
env=dict(B,root=S,rows=rows,read=read)
guard=compile(ast.Module(body=fn.body[start:end],type_ignores=[]),str(builder_path),'exec')
try:exec(guard,env)
except ValueError as e:second_reason=str(e)
else:raise AssertionError('expected stale package pin refusal')
assert second_reason=='undeclared held source replacement'
differences={k:{'expected':env['expected'][k],'actual':env['registered'][k]} for k in set(env['expected'])-B['HELD_SUCCESSOR_HELPERS'] if env['expected'][k]!=env['registered'][k]}
assert list(differences)==['tradingagents/research/onchain_replication/resource_fixture.py']
# New current/design block: inspect no writes, inject fatal at its existing
# registered metadata reader; source/Git stand-ins explicitly not genuine.
d=ast.parse((C/'build_release_draft01.py').read_bytes());fn=next(n for n in d.body if isinstance(n,ast.FunctionDef) and n.name=='held_metadata_draft')
for name in ['MemoryError','KeyboardInterrupt','SystemExit']:
 error=globals().get(name) or getattr(__import__('builtins'),name)
 fatal=error('registered metadata boundary')
 s,r=data();plan=G['held_input_plan'](r,s);s['source_origins']=[]
 from types import SimpleNamespace
 def readfatal(*args):raise fatal
 start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='auxiliary' for t in n.targets))
 block=compile(ast.Module(body=fn.body[start:start+2],type_ignores=[]),str(C/'build_release_draft01.py'),'exec')
 e=dict(plan=plan,source_plan=s,source='1'*40,design_source=None,root=S,roles=r,builder=SimpleNamespace(_held_git=lambda *args:b'',held_document=readfatal),generator=SimpleNamespace(AUXILIARY_ROLES=G['AUXILIARY_ROLES']),require=G['require'])
 try:exec(block,e)
 except BaseException as caught:assert caught is fatal
 else:raise AssertionError('fatal hidden')
 checks.append(name+' exact firstfatal at new metadata block')
result={'scope':'actual source/real read-only lineage and synthetic metadata boundaries only','checks':checks,'composition_blockers':[{'id':'HAP1','path':str(builder_path),'lines':[169,176,178],'actual_anchor':composition['actual_148_package_anchor'],'actual_parent':actual_parent,'required_immediate_parent':B['HELD_S2'],'real_first_refusal':actual_reason,'extracted_later_refusal':second_reason,'unlisted_package_change':differences}],'author_manifest_bodies':len(members),'claims_jobs':0,'numeric_imports':False}
(H/'READBACK01.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS',len(checks),'bounded metadata controls;',len(members),'manifest bodies')
print('REPRODUCED HAP1 actual Source04 helper lineage refusal:',actual_reason)
print('REPRODUCED HAP1 later exact source guard:',second_reason,json.dumps(differences,sort_keys=True))
