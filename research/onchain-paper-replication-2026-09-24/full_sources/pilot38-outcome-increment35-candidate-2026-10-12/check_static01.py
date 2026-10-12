"""Focused static joins and literal/AST inverses; never executes tools."""
import ast,difflib,hashlib,json,stat
from pathlib import Path
C=Path(__file__).resolve().parent;F=C.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';OLD=H/'full38increment34'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope=json.loads((C/'TOOL_SCOPE01.json').read_text());dest=R/scope['deployment_directory'];newpins=scope['selected_pins'];reused=scope['exact_prior33_34_rows_reused'];allpins=newpins+reused;paths={p['path'] for p in allpins};assert len(paths)==len(allpins)
for p in allpins:
 q=R/p['path'];assert q.is_file() and not q.is_symlink() and q.stat().st_size==p['bytes'] and sha(q)==p['sha256'] and format(stat.S_IMODE(q.stat().st_mode),'04o')==p['mode']
for pin in scope['baseline']:
 q=R/pin['path'];assert sha(q)==pin['sha256']
manifest=json.loads((C/'HELPERS_MANIFEST01.json').read_text())
for p,h in manifest.items():assert sha(C/Path(p).name)==h
patch=[];inverse=[]
for name in ('select','capture','recover'):
 old=(OLD/(name+'34.py')).read_text();new=(C/(name+'35.py')).read_text();ast.parse(new)
 op=str((OLD/(name+'34.py')).relative_to(R));np=str((dest/(name+'35.py')).relative_to(R));patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=op,tofile=np));inverse.extend(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=np,tofile=op))
 if name!='select':
  restored=new
  for a,b in reversed(scope['capture_recover_aliases']):restored=restored.replace(b,a)
  assert restored==old and ast.dump(ast.parse(restored))==ast.dump(ast.parse(old))
assert ''.join(patch)==(C/'LITERAL_PATCH01.diff').read_text() and ''.join(inverse)==(C/'LITERAL_INVERSE01.diff').read_text()
source=(C/'select35.py').read_text();tree=ast.parse(source);values={}
for n in tree.body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name):
  try:values[n.targets[0].id]=ast.literal_eval(n.value)
  except (TypeError,ValueError):pass
assert values['selected_pins']==newpins and values['reused_pins']==reused and values['closed_directory_roster']==scope['closed_directory_roster']
assert len(values['helper_names'])==7 and all('35.py' in n for n in values['helper_names'][:3])
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('rglob','glob','walk','run','check_output','Popen') for n in ast.walk(tree))
for row in scope['closed_directory_roster']:
 q=R/row['path'];assert sorted(p.name for p in q.iterdir())==row['children'] and format(stat.S_IMODE(q.stat().st_mode),'04o')==row['mode']
 for name in row['children']:
  p=q/name
  if p.is_file():assert str(p.relative_to(R)) in paths
opaque36={p['path'] for p in scope['opaque36_exact']};assert len(opaque36)==3
assert {p for p in paths if p.startswith('research_artifacts/archive-dispatch-ethpilot-20261011-36/')}==opaque36
context=scope['opaque38_context_root'];assert {p for p in paths if p.startswith(context+'/')}=={context+'/'+n for n in ('close-failed.json','intent.json','terminal.json')}
assert {v['path'] for v in scope['closed_directory_roster'] if v['path'].startswith(context+'/')}=={context+'/'+n for n in ('controls','diagnostic-controls','diagnostics')}
assert not any(Path(p).name in scope['prior_archive_duplicates_excluded'] for p in paths)
assert not any((R/p).is_relative_to(dest) or (R/p).is_relative_to(C) for p in paths)
assert set(scope['navigation_explicitly_frozen_by_Root'])<=paths
outcome=json.loads((R/scope['accepted_closed38_outcome']['path']).read_text());assert outcome['original_outer_status']=='failed' and outcome['scientific_disposition']['training'] is None
for ref in (outcome['original_claim'],outcome['original_terminal']):assert ref['path'] in paths and next(p for p in allpins if p['path']==ref['path'])['sha256']==ref['sha256']
for name in ('SELECTION35.json','CAPTURE35.json','FRESH_GIT_RECOVERY35.json','pilot38-outcome-increment35.tar'):assert not (dest/name).exists()
result={'status':'STATIC_SOURCE_CHECK_PASS_UNEXECUTED','selected_files':len(newpins),'selected_bytes':sum(p['bytes'] for p in newpins),'reused_files':len(reused),'helper_files':7,'closed_directories':len(scope['closed_directory_roster']),'capture_recover_literal_AST_inverse':True,'published_diffs_exact':True,'original38_FAILED_and_nulls_unchanged':True,'opaque_decoded':False,'tools_executed':False,'helper_hashes':{name:sha(C/name) for name in ('select35.py','capture35.py','recover35.py')}}
(C/'STATIC_CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
