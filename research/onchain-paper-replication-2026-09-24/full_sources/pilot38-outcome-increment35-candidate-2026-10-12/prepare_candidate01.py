"""Prepare fixed literal tools only; never executes selector/capture/recovery."""
import ast,difflib,hashlib,json,os,stat,subprocess
from pathlib import Path
C=Path(__file__).resolve().parent;F=C.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';OLD=H/'full38increment34';DEPLOY=H/'full38outcome35'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=64*1024**2
 assert not ({'.git','.venv','node_modules','keys','apis','__pycache__'}&set(p.parts)) and p.name not in {'.env','hf_token.txt','connection.json'}
 raw=p.read_bytes();t=p.lstat();assert (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns)
 return {'path':str(p.relative_to(R)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'mode':format(stat.S_IMODE(s.st_mode),'04o')}
def save(name,v):(C/name).write_text(json.dumps(v,indent=2)+'\n')
outcome=F/'pilot38-preparation-outcome-review-2026-10-12/OUTCOME_REVIEW01.json';review=json.loads(outcome.read_text());assert review['decision']=='accepted' and review['original_outer_status']=='failed' and review['scientific_disposition']['training'] is None
check=json.loads((outcome.parent/'CHECK02.json').read_text());experiment=review['experiment_id'];owned={str(Path(v['path']).parts[0]) for v in check['owned_namespace']}
owner_root=Path(check['owned_namespace'][0]['path']);owner_root=R/Path(*owner_root.parts[:4]);assert owner_root.name==experiment
closed=[R/Path(review['original_claim']['path']).parent,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/experiment,R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/experiment,owner_root,R/'research_artifacts/archive-dispatch-ethpilot-20261012-38']
public_roots=['real-data-pilot-full38-entry-preparation01-2026-10-12','pilot38-final-binding-release-review-2026-10-12','pilot38-increment34-return-review-2026-10-12','pilot38-live-git-attribution-2026-10-12','pilot38-preparation-outcome-review-2026-10-12','pilot39-whole-capacity-candidate-2026-10-12','pilot39-public-preparation-candidate-2026-10-12','pilot39-successor-preparation-review-2026-10-12','pilot-historical-proof-transport-candidate-2026-10-12','real-data-pilot-full39-binding-preparation01-2026-10-12','pilot38-root-closure-checkpoint-2026-10-12']
paths=set();directory_roster=[];dirpins=[]
for root in closed:
 assert root.is_dir() and not root.is_symlink()
 for parent,dirs,files in os.walk(root,followlinks=False):
  p=Path(parent);assert p.resolve()==p and not p.is_symlink();children=[]
  for name in sorted(dirs+files):
   q=p/name;s=q.lstat();assert stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode),str(q)
   children.append(name)
   if stat.S_ISREG(s.st_mode):paths.add(q)
  row={'path':str(p.relative_to(R)),'mode':format(stat.S_IMODE(p.stat().st_mode),'04o'),'children':children};directory_roster.append(row);dirpins.append({'path':row['path'],'mode':row['mode']})
for name in public_roots:
 root=F/name;assert root.is_dir() and not root.is_symlink()
 for parent,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=[d for d in dirs if d not in {'.git','.venv','node_modules','__pycache__'}]
  for leaf in files:
   p=Path(parent)/leaf;assert not p.is_symlink();paths.add(p)
# Three original36 archive controls only; never decode or traverse old36.
opaque36=[R/'research_artifacts/archive-dispatch-ethpilot-20261011-36'/n for n in ('close-failed.json','intent.json','terminal.json')];paths.update(opaque36)
# Exact original34 postcapture files only, no old archive/body duplicate read.
excluded={'pilot38-preparation-increment34.tar','fresh-git-recovered-full38increment34.tar','actual_external_archive_blob_return.stdout'}
for p in OLD.iterdir():
 if p.is_file() and p.name not in excluded:paths.add(p)
# Read-only names only: capture post34 committed source changes, never navigation.
base=json.loads((OLD/'FRESH_GIT_RECOVERY34.json').read_text())['source'];head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
changes=subprocess.check_output(['git','diff','--name-only',base,head],cwd=R,text=True).splitlines()
nav={'research/onchain-paper-replication-2026-09-24/STATE.md','research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md'}
for name in changes:
 if name.endswith(tuple('/'+x for x in excluded)):continue
 p=R/name
 assert p.is_relative_to(F) or name.startswith(('tradingagents/','tests/')) or name in nav,name
 paths.add(p)
paths.add(R/'tradingagents/research/onchain_replication/real_pilot_import_caller.py')
paths.update(R/name for name in nav)
# Reuse only exact typed prior33/34 rows, authenticated by retained receipts.
prior_rows={}
for leaf,num in [('full38increment33',33),('full38increment34',34)]:
 d=H/leaf;rec=json.loads((d/f'FRESH_GIT_RECOVERY{num}.json').read_text());cap=json.loads((d/f'CAPTURE{num}.json').read_text());assert sha(d/f'CAPTURE{num}.json')==rec['capture']['sha256'] and sha(d/f'SELECTION{num}.json')==cap['selection']['sha256']
 prior_rows.update({v['path']:v for v in json.loads((d/f'SELECTION{num}.json').read_text())['rows']})
selected=[];reused=[]
for p in sorted(paths):
 v=pin(p);old=prior_rows.get(v['path'])
 if old and old['type']=='regular' and all(old[k]==v[k] for k in ('bytes','sha256','mode')):reused.append(v)
 else:selected.append(v)
baseline=[pin(OLD/'FRESH_GIT_RECOVERY34.json'),pin(F/'pilot38-increment34-return-review-2026-10-12/RETURN_REVIEW01.json'),pin(OLD/'CAPTURE34.json'),pin(OLD/'SELECTION34.json')]
assert baseline[1]['sha256']=='4808fc224d8edaa4f31a5c3df61d544031d01feef9e6b6f59ba1515dfa0a8104'
# Exact source34 selector with finite payload/namespace substitutions. New closed
# directory pins preserve empty context dirs and refuse later roster mutations.
source=(OLD/'select34.py').read_text();tree=ast.parse(source)
def replace_assign(text,name,value):
 tree=ast.parse(text);n=next(n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name);lines=text.splitlines(True);lines[n.lineno-1:n.end_lineno]=[name+'='+repr(value)+'\n'];return ''.join(lines)
source=source.replace('increment34','outcome35').replace('select34','select35').replace('capture34','capture35').replace('recover34','recover35').replace('SELECTION34','SELECTION35')
source=replace_assign(source,'baseline_pins',baseline);source=replace_assign(source,'selected_pins',selected)
source=source.replace("sha(path)==pin['sha256'], pin['path']","sha(path)==pin['sha256'] and format(stat.S_IMODE(path.stat().st_mode),'04o')==pin['mode'], pin['path']")
source=source.replace('names=[]', 'reused_pins='+repr(reused)+"\nfor value in reused_pins:\n    p=ROOT/value['path'];assert p.is_file() and not p.is_symlink() and p.stat().st_size==value['bytes'] and sha(p)==value['sha256'] and format(stat.S_IMODE(p.stat().st_mode),'04o')==value['mode'], value['path']\nnames=[]")

source=source.replace("    assert relative.startswith('research/onchain-paper-replication-2026-09-24/full_sources/'), relative", "    assert relative in expected_hashes, relative")
source=source.replace('directories = set()','directories = set()\nclosed_directory_roster='+repr(directory_roster)+"\nfor value in closed_directory_roster:\n    p=ROOT/value['path'];assert p.is_dir() and not p.is_symlink() and p.resolve()==p\n    assert format(stat.S_IMODE(p.stat().st_mode),'04o')==value['mode'] and sorted(x.name for x in p.iterdir())==value['children'], value['path']\n    directories.add(p)")
source=source.replace("'qualification':'Only fixed corrected38 registration metadata and actual33 postcapture/review bodies. No claim, release, final binding,36 recopy, runtime envelope or historical store is selected.'", "'exact_prior33_34_rows_reused':"+repr(reused)+",'closed_scopes':"+repr([str(p.relative_to(R)) for p in closed])+",'qualification':'Fixed original closed38 FAILED evidence, complete38 archive context, exact three opaque36 controls and bounded post34 metadata/source evidence. No scientific admission, credential decoding, historical store recopy or future tool outputs. Current navigation explicitly frozen by Root is included.'")
(C/'select35.py').write_text(source)
aliases=[('full38increment34','full38outcome35'),('pilot38-preparation-increment34','pilot38-outcome-increment35'),('preparation38-20261012-34.git','outcome38-20261012-35.git'),('SELECTION34','SELECTION35'),('CAPTURE34','CAPTURE35'),('FRESH_GIT_RECOVERY34','FRESH_GIT_RECOVERY35'),('GIT_OPERATIONS34','GIT_OPERATIONS35'),('no dispatch envelope is recopied in this increment','only explicitly declared opaque archive controls are retained without decoding')]
for name in ('capture','recover'):
 old=(OLD/(name+'34.py')).read_text();new=old
 for a,b in aliases:new=new.replace(a,b)
 restore=new
 for a,b in reversed(aliases):restore=restore.replace(b,a)
 assert restore==old and ast.dump(ast.parse(restore))==ast.dump(ast.parse(old));(C/(name+'35.py')).write_text(new)
scope={'status':'UNEXECUTED_CANDIDATE','deployment_directory':str(DEPLOY.relative_to(R)),'baseline':baseline,'accepted_closed38_outcome':pin(outcome),'closed_scope_roots':[str(p.relative_to(R)) for p in closed],'closed_directory_roster':directory_roster,'opaque36_exact':[pin(p) for p in opaque36],'opaque38_context_root':str(closed[-1].relative_to(R)),'selected_pins':selected,'exact_prior33_34_rows_reused':reused,'public_roots':public_roots,'navigation_explicitly_frozen_by_Root':sorted(nav),'prior_archive_duplicates_excluded':sorted(excluded),'capture_recover_aliases':aliases,'git_names_only_anchor':head,'original38_disposition':'FAILED preserved, training and completed graph counters remain null; component qualification does not rewrite originals','helpers_executed':False}
save('TOOL_SCOPE01.json',scope)
patch=[];inverse=[]
for name in ('select','capture','recover'):
 old=(OLD/(name+'34.py')).read_text();new=(C/(name+'35.py')).read_text();op=str((OLD/(name+'34.py')).relative_to(R));np=str((DEPLOY/(name+'35.py')).relative_to(R));patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=op,tofile=np));inverse.extend(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=np,tofile=op));ast.parse(new)
(C/'LITERAL_PATCH01.diff').write_text(''.join(patch));(C/'LITERAL_INVERSE01.diff').write_text(''.join(inverse))
save('HELPERS_MANIFEST01.json',{str((DEPLOY/name).relative_to(R)):sha(C/name) for name in ('select35.py','capture35.py','recover35.py','TOOL_SCOPE01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff')})
print(json.dumps({'selected':len(selected),'bytes':sum(p['bytes'] for p in selected),'reused':len(reused),'closed_dirs':len(directory_roster),'helpers_executed':False}))
