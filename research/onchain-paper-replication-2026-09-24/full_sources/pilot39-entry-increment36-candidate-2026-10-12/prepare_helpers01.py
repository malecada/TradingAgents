"""Generate finite source candidates only; never select/capture/recover."""
import argparse,ast,difflib,hashlib,json,stat
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3]
H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';OLD=H/'full38outcome35';DEP=H/'full39entry36'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=64*1024**2
 return {'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size,'mode':format(stat.S_IMODE(p.stat().st_mode),'04o')}
def shape(s):
 t=ast.parse(s)
 for n in ast.walk(t):
  if isinstance(n,ast.Constant) and isinstance(n.value,str):n.value='<string>'
 return ast.dump(t)
def assignment(text,name,value):
 n=next(n for n in ast.parse(text).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
 return text.replace(ast.get_source_segment(text,n),name+'='+repr(value),1)
products={};originals={};aliases={}
for name in ('capture','recover'):
 old=(OLD/(name+'35.py')).read_text();new=old
 changes=[('full38outcome35','full39entry36'),('pilot38-outcome-increment35','pilot39-entry-increment36'),('outcome38-20261012-35.git','entry39-20261012-36.git'),('SELECTION35','SELECTION36'),('CAPTURE35','CAPTURE36'),('FRESH_GIT_RECOVERY35','FRESH_GIT_RECOVERY36'),('GIT_OPERATIONS35','GIT_OPERATIONS36')]
 for a,b in changes:new=new.replace(a,b)
 reverse=new
 for a,b in reversed(changes):reverse=reverse.replace(b,a)
 assert reverse==old and shape(new)==shape(old)
 products[name]=new;originals[name]=old;aliases[name]=changes;(P/(name+'36.py')).write_text(new)
(P/'ALIAS_CHECK01.json').write_text(json.dumps({'status':'ALIASES_READY_SCOPE_NOT_FROZEN','capture_recover_only_string_changes':True,'exact_inverse':True,'helpers_executed':False,'aliases':aliases,'hashes':{n+'36.py':sha(P/(n+'36.py')) for n in products}},indent=2)+'\n')
parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
if not args.freeze:raise SystemExit(0)
entry=F/'real-data-pilot-full39-entry-preparation01-2026-10-12';public=F/'real-data-pilot-full39-binding-preparation01-2026-10-12'
for n in ('gate01.json','BINDING_DRAFT01.json','REGISTRATION_DRAFT01.json','CAPACITY_DECLARATION_ROOT01.json','preflight39_01.py','root_io39_01.py'):assert (entry/n).is_file(),n
prior=OLD/'FRESH_GIT_RECOVERY35.json';review=F/'pilot38-outcome-increment35-review-2026-10-12/RETURN_REVIEW01.json'
assert sha(review)=='fa56521cd5bde84ee4bf9289cb9d66c6d8ef9653b7ce278bd2c79f772e22df63'
base=json.loads((OLD/'SELECTION35.json').read_bytes());priorrows={r['path']:r for r in base['rows']}
for r in base.get('exact_prior33_34_rows_reused',[]):priorrows.setdefault(r['path'],r)
# Fixed new public roots and explicitly permitted immediate subdirectories only.
scopes={str(public.relative_to(F)):['','public01','inputs01'],str(entry.relative_to(F)):[''],
 'pilot39-entry-preparation-candidate-2026-10-12':['','iteration01'],
 'pilot39-entry-source-review-2026-10-12':[''],
 'pilot38-outcome-increment35-review-2026-10-12':['']}
names={F.parent/'STATE.md',F/'parallel-execution-2026-10-02/COORDINATION.md'}
excluded_future={'BINDING01.json','RELEASE_REVIEW01.json','RELEASE01.json'}
for name,subdirs in scopes.items():
 for subdir in subdirs:
  root=F/name/subdir;assert root.is_dir() and not root.is_symlink()
  for p in root.iterdir():
   if p.is_file() and not p.is_symlink() and p.suffix!='.pyc' and p.name not in excluded_future:names.add(p)
growth=F/'pilot39-final-entry-review-2026-10-12'
for n in ('GROWTH_CHECK01.json','GROWTH_CHECK01.log','GROWTH_REPORT.md','GROWTH_REVIEW01.json','check_growth01.py'):assert (growth/n).is_file();names.add(growth/n)
# Literal post35 receipts/operations only; no old archive or blob stdout.
post=['CAPTURE35.json','FRESH_GIT_RECOVERY35.json','GIT_OPERATIONS35.json','ROOT_INSTALL_PRECHECK_FAILED01.json','ROOT_RETURN_OPERATION35.json','ROOT_SELECT_CAPTURE_OPERATIONS35.json']
for stem in ('ROOT_capture35','ROOT_recover35','ROOT_select35','actual_external_archive_blob_return','actual_external_commit_body','actual_external_commit_only_fetch','actual_external_selected_blob_fetch','fetched_head_readback','fresh_bare_init','fresh_remote_add','local_archive_git_tree_join','local_head','remote_actual_branch_readback','remote_get_url','set_promisor','set_tree_zero_filter'):
 for extension in ('.stderr','.stdout'):
  if stem=='actual_external_archive_blob_return' and extension=='.stdout':continue
  post.append(stem+extension)
for n in post:assert (OLD/n).is_file();names.add(OLD/n)
# Only public binder metadata is decoded. Envelope inspection is raw bytes/hash/mode.
opaque=json.loads((public/'BOUND01.json').read_bytes())['private_input']['archive_transport'];assert opaque['bytes']==930
op=R/opaque['path'];assert op==R/'research_artifacts/real_pilot_runtime/pilot-transport-20261012-39-01/archive_transport01.json'
actual=pin(op);assert all(actual[k]==v for k,v in opaque.items());names.add(op)
selected=[];reused=[]
for p in sorted(names):
 value=pin(p);old=priorrows.get(value['path'])
 if old and all(old[k]==value[k] for k in ('sha256','bytes','mode')):reused.append(value)
 else:selected.append(value)
old=(OLD/'select35.py').read_text();s=old.replace('full38outcome35','full39entry36').replace('select35.py','select36.py').replace('capture35.py','capture36.py').replace('recover35.py','recover36.py').replace('SELECTION35','SELECTION36').replace('selection34 already spent','selection36 already spent')
for name,value in [('baseline_pins',[pin(prior),pin(review),pin(OLD/'CAPTURE35.json'),pin(OLD/'SELECTION35.json')]),('selected_pins',selected),('reused_pins',reused),('closed_directory_roster',[])]:s=assignment(s,name,value)
start=s.index('selection=');end=s.index('\nwith (HERE/',start)
s=s[:start]+"selection={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_actual_recovery':baseline_pins[0],'baseline_accepted_review':baseline_pins[1],'baseline_source':prior['source'],'files':len(rows),'body_bytes':sum(r['bytes'] for r in rows),'rows':rows,'directories':dirs,'symlinks':sum(r['type']=='symlink' for r in rows),'exact_unchanged_prior35_rows_reused':reused_pins,'qualification':'Fixed full39 public/binding/draft entry and source/growth evidence, actual35 postcapture receipts, sole new39 opaque envelope. No future final binding/release/currenttoolsreview, credential target access, original38 outcome recopy or historical store traversal.'}"+s[end:]
s=s.replace('Finite corrected-registration outcome35','Finite whole39 entry increment36');ast.parse(s)
products['select']=s;originals['select']=old;(P/'select36.py').write_text(s)
forward=[];inverse=[]
for n,body in products.items():
 forward.extend(difflib.unified_diff(originals[n].splitlines(True),body.splitlines(True),fromfile=str((OLD/(n+'35.py')).relative_to(R)),tofile=str((DEP/(n+'36.py')).relative_to(R))))
 inverse.extend(difflib.unified_diff(body.splitlines(True),originals[n].splitlines(True),fromfile=str((DEP/(n+'36.py')).relative_to(R)),tofile=str((OLD/(n+'35.py')).relative_to(R))))
(P/'LITERAL_PATCH01.diff').write_text(''.join(forward));(P/'LITERAL_INVERSE01.diff').write_text(''.join(inverse))
scope={'status':'UNEXECUTED_FIXED_ENTRY36_CANDIDATE','deployment_directory':str(DEP.relative_to(R)),'baseline':pin(prior),'accepted_review':pin(review),'selected_pins':selected,'reused_pins':reused,'public_roots_and_subdirectories':scopes,'growth_names':['GROWTH_CHECK01.json','GROWTH_CHECK01.log','GROWTH_REPORT.md','GROWTH_REVIEW01.json','check_growth01.py'],'post35_exact_names':post,'opaque39':actual,'excluded':['old returned archives','actual_external_archive_blob_return.stdout','final BINDING01/release','current36 tools-review','historical original38 stores'],'aliases':aliases,'helper_execution':False,'qualification':'Exact finite declared increment only. Actual35 and its reviewed inherited33/34 evidence retain unchanged prior bodies; no assertion of unselected historical store reconstruction or deletion authority.'}
(P/'TOOL_SCOPE01.json').write_text(json.dumps(scope,indent=2)+'\n')
files=('select36.py','capture36.py','recover36.py','TOOL_SCOPE01.json','HELPERS_MANIFEST01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff')
(P/'HELPERS_MANIFEST01.json').write_text(json.dumps({str((DEP/n).relative_to(R)):sha(P/n) for n in files if n!='HELPERS_MANIFEST01.json'},indent=2)+'\n')
(P/'FREEZE_CHECK01.json').write_text(json.dumps({'status':'STATIC_SOURCE_CHECKS_ONLY','selected_files':len(selected),'selected_bytes':sum(r['bytes'] for r in selected),'reused_files':len(reused),'capture_recover_nonstring_ast_equal':True,'inverse_exact':True,'helper_execution':False,'helper_hashes':{n:sha(P/n) for n in files}},indent=2)+'\n')
print(json.dumps({'selected':len(selected),'bytes':sum(r['bytes'] for r in selected),'reused':len(reused),'executed':False}))
