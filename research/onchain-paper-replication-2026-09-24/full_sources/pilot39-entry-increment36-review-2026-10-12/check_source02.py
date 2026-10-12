"""Finite source/pin checks; never executes preservation tools."""
import ast,copy,difflib,hashlib,json,stat
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'pilot39-entry-increment36-candidate-2026-10-12';D=F/'pilot39-entry-increment36-review-2026-10-12';H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';O=H/'full38outcome35'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_bytes())
scope=load(C/'TOOL_SCOPE01.json');selected=scope['selected_pins'];reused=scope['reused_pins'];assert len(selected)==143 and len(reused)==23 and sum(r['bytes'] for r in selected)==3148874
assert len({r['path'] for r in selected+reused})==166
for row in selected+reused:
 p=R/row['path'];s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1
 assert s.st_size==row['bytes'] and format(stat.S_IMODE(s.st_mode),'04o')==row['mode'] and sha(p)==row['sha256']
 assert not ({'.git','.venv','keys','apis','node_modules'}&set(p.parts));assert p.name not in ('connection.json','.env','hf_token.txt')
assert sum(r['path'].startswith('research_artifacts/') for r in selected)==1
assert scope['opaque39'] in selected and scope['opaque39']['bytes']==930
prior=load(O/'SELECTION35.json');oldrows={r['path']:r for r in prior['rows']+prior['exact_prior33_34_rows_reused']}
for row in reused:assert all(oldrows[row['path']][k]==row[k] for k in ('bytes','sha256','mode'))
for ref in (scope['baseline'],scope['accepted_review']):assert sha(R/ref['path'])==ref['sha256']
review=load(R/scope['accepted_review']['path']);assert review['decision']=='accepted' and review['evidence'][scope['baseline']['path']]==scope['baseline']['sha256']
def assignment(tree,name):return next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
selector=(C/'select36.py').read_text();tree=ast.parse(selector)
assert ast.literal_eval(assignment(tree,'selected_pins'))==selected and ast.literal_eval(assignment(tree,'reused_pins'))==reused
assert ast.literal_eval(assignment(tree,'closed_directory_roster'))==[]
assert len(ast.literal_eval(assignment(tree,'helper_names')))==7
for n in ast.walk(tree):
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):assert n.func.attr not in ('rglob','glob','walk')
forward=[];inverse=[]
for name in ('capture','recover','select'):
 before=(O/(name+'35.py')).read_text();after=(C/(name+'36.py')).read_text();ast.parse(after)
 if name!='select':
  restored=after
  for a,b in reversed(scope['aliases'][name]):restored=restored.replace(b,a)
  assert restored==before
  def shape(s):
   t=ast.parse(s)
   for n in ast.walk(t):
    if isinstance(n,ast.Constant) and isinstance(n.value,str):n.value='string'
   return ast.dump(t)
  assert shape(before)==shape(after)
 old=str((O/(name+'35.py')).relative_to(R));new=scope['deployment_directory']+'/'+name+'36.py'
 forward.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=old,tofile=new));inverse.extend(difflib.unified_diff(after.splitlines(True),before.splitlines(True),fromfile=new,tofile=old))
assert ''.join(forward)==(C/'LITERAL_PATCH01.diff').read_text() and ''.join(inverse)==(C/'LITERAL_INVERSE01.diff').read_text()
manifest=load(C/'HELPERS_MANIFEST01.json');assert len(manifest)==6
for path,digest in manifest.items():assert sha(C/Path(path).name)==digest
paths={r['path'] for r in selected+reused};entry=F/'real-data-pilot-full39-entry-preparation01-2026-10-12'
gate=load(entry/'gate01.json');name='eth-paper-real-data-end-to-end-resource-20261012-39';assert len(gate['experiments'])==16 and len(gate['experiments'][name]['source_files'])==1142 and len(gate['experiments'][name]['inputs'])==73
assert load(entry/'BINDING_DRAFT01.json')['status']=='DRAFT_NOT_RELEASED'
for n in ('gate01.json','BINDING_DRAFT01.json','BASELINE_STORAGE_OBSERVATION01.json','ROOT_GROWTH_TERMS01.json','CAPACITY_DECLARATION_ROOT01.json'):
 assert str((entry/n).relative_to(R)) in paths,n
assert str((F.parent/'STATE.md').relative_to(R)) in paths and str((F/'parallel-execution-2026-10-02/COORDINATION.md').relative_to(R)) in paths
assert not any('/pilot39-entry-increment36-review-' in p or p.endswith('/BINDING01.json') or p.endswith('.tar') or p.endswith('actual_external_archive_blob_return.stdout') for p in paths)
print(json.dumps({'status':'SOURCE_SCOPE_PASS','selected_files':143,'selected_bytes':3148874,'reused_files':23,'helpers':7,'gate_definitions':16,'new_gate_source_pins':1142,'input_roles':73,'literal_and_AST_inverse':True,'helper_execution':False,'opaque_decoded':False,'manifest_sha256':sha(C/'HELPERS_MANIFEST01.json')},indent=2))
