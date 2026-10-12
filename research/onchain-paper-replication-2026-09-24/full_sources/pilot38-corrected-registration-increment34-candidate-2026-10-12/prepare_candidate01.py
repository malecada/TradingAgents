"""Create finite source candidates only; no helper execution."""
import ast,difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3]
H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';OLD=H/'full38increment33';DEP=H/'full38increment34'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:{'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size}
prior=OLD/'FRESH_GIT_RECOVERY33.json';review=F/'pilot38-increment33-return-review-2026-10-12/RETURN_REVIEW01.json'
assert sha(review)=='ea801acb7276c98409a60b7018a38d7e6fc1e3bd16253bc4e4a501c56608d923'
oldrows={r['path']:r for r in json.loads((OLD/'SELECTION33.json').read_bytes())['rows']}
entry=F/'real-data-pilot-full38-entry-preparation01-2026-10-12'
entry_names=['JOB_METADATA_ADMISSION02.json','JOB_METADATA_ADMISSION02.stdout','JOB_METADATA_ADMISSION02.stderr','BINDING_DRAFT01.json','CELL_ID_CORRECTION01.diff','CELL_ID_CORRECTION01.json','CELL_ID_CORRECTION_INVERSE01.diff','CELL_ID_GENERATOR_CORRECTION01.diff','REGISTRATION_DRAFT01.json','ROOT_METADATA_ADMISSION_OPERATION01.json','gate01.json','metadata_admission01.stderr','metadata_admission01.stdout','prepare_entry01.py']
# Fixed names from actual33 postcapture listing; no archive/blob bodies.
post=['CAPTURE33.json','FRESH_GIT_RECOVERY33.json','GIT_OPERATIONS33.json','ROOT_ACTUAL_OPERATIONS33.json','ROOT_CAPTURE_FAILURE33.json','ROOT_CAPTURE_OPERATIONS33.json']
post += [stem+ext for stem in ['actual_external_archive_blob_return','actual_external_commit_body','actual_external_commit_only_fetch','actual_external_selected_blob_fetch','fetched_head_readback','fresh_bare_init','fresh_remote_add','local_archive_git_tree_join','local_head','remote_actual_branch_readback','remote_get_url','root_capture33','root_commit33','root_diffcheck33','root_push33','root_select33','root_select33_02','set_promisor','set_tree_zero_filter'] for ext in ('.stderr','.stdout') if not(stem=='actual_external_archive_blob_return' and ext=='.stdout')]
return_names=['MANIFEST01.json','REPORT01.md','RETURN_CHECK01.txt','RETURN_CHECK02.txt','RETURN_REVIEW01.json','SOURCE_INPUT_JOIN01.json','check_return33.py','check_return33b.py']
cell_names=sorted(p.name for p in (F/'pilot38-entry-registration-review-2026-10-12').iterdir() if p.is_file() and not p.is_symlink())
paths=[entry/n for n in entry_names]+[OLD/n for n in post]+[review.parent/n for n in return_names]+[F/'pilot38-entry-registration-review-2026-10-12'/n for n in cell_names]
selected=[];reused=[]
for p in paths:
 assert p.is_file() and not p.is_symlink(),p
 row=ref(p)
 if oldrows.get(row['path'],{}).get('sha256')==row['sha256']:reused.append(row['path'])
 else:selected.append(row)
assert len({r['path'] for r in selected})==len(selected)
products={};originals={};maps={}
for name in ('capture','recover'):
 old=(OLD/(name+'33.py')).read_text();s=old
 mapping=[('full38increment33','full38increment34'),('pilot38-preparation-increment33','pilot38-preparation-increment34'),('preparation38-20261012-33.git','preparation38-20261012-34.git'),('SELECTION33','SELECTION34'),('CAPTURE33','CAPTURE34'),('FRESH_GIT_RECOVERY33','FRESH_GIT_RECOVERY34'),('GIT_OPERATIONS33','GIT_OPERATIONS34')]
 for a,b in mapping:s=s.replace(a,b)
 # Qualification changes are literal only: no new opaque body exists in34.
 mapping += [('the one new bound dispatch envelope is retained as an opaque body','no dispatch envelope is recopied in this increment')]
 s=s.replace(*mapping[-1]);back=s
 for a,b in reversed(mapping):back=back.replace(b,a)
 assert back==old
 def shape(body):
  t=ast.parse(body)
  for n in ast.walk(t):
   if isinstance(n,ast.Constant) and isinstance(n.value,str):n.value='<string>'
  return ast.dump(t)
 assert shape(s)==shape(old)
 products[name]=s;originals[name]=old;maps[name]=mapping
# Retain accepted typed row construction and file-stability checks verbatim.
oldselect=(OLD/'select33_02.py').read_text();body=oldselect[oldselect.index('rows = []'):oldselect.index('selection = {')]
body=body.replace('directories = set(scope_directories)','directories = set()')
private_line="    assert not relative.startswith(('research_artifacts/', 'research_runs/')) or relative==private_relative or any(path.is_relative_to(root) for root in closed_scopes), relative\n"
assert private_line in body;body=body.replace(private_line,"    assert relative.startswith('research/onchain-paper-replication-2026-09-24/full_sources/'), relative\n")
header='''"""Finite corrected-registration increment34; Root execution only."""
import datetime,hashlib,json,os,stat
from pathlib import Path
ROOT=Path.cwd().resolve();HERE=Path(__file__).resolve().parent
'''
header+='assert HERE==ROOT/'+repr(str(DEP.relative_to(R)))+", 'deploy reviewed exact helper copies before execution'\n"
header+="assert not (HERE/'SELECTION34.json').exists(), 'selection34 already spent'\n"
header+="def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()\n"
header+='baseline_pins='+repr([ref(prior),ref(review),ref(OLD/'CAPTURE33.json'),ref(OLD/'SELECTION33.json')])+'\n'
header+='''for pin in baseline_pins:
    path=ROOT/pin['path'];assert path.is_file() and not path.is_symlink() and path.stat().st_size==pin['bytes'] and sha(path)==pin['sha256'], pin['path']
prior=json.loads((ROOT/baseline_pins[0]['path']).read_bytes())
prior_capture=json.loads((ROOT/baseline_pins[2]['path']).read_bytes())
assert prior['capture']['sha256']==baseline_pins[2]['sha256']
assert prior_capture['selection']['sha256']==baseline_pins[3]['sha256']
'''
header+='selected_pins='+repr(selected)+'\n'
header+='''names=[]
expected_hashes={pin['path']:pin['sha256'] for pin in selected_pins}
for pin in selected_pins:
    path=ROOT/pin['path'];assert path.is_file() and not path.is_symlink() and path.stat().st_size==pin['bytes'] and sha(path)==pin['sha256'], pin['path']
    names.append(pin['path'])
helper_names=('select34.py','capture34.py','recover34.py','TOOL_SCOPE01.json','HELPERS_MANIFEST01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff')
manifest=json.loads((HERE/'HELPERS_MANIFEST01.json').read_bytes())
assert set(manifest)=={str((HERE/n).relative_to(ROOT)) for n in helper_names if n!='HELPERS_MANIFEST01.json'}
for relative,expected in manifest.items():assert sha(ROOT/relative)==expected, relative
expected_hashes.update(manifest)
expected_hashes[str((HERE/'HELPERS_MANIFEST01.json').relative_to(ROOT))]=sha(HERE/'HELPERS_MANIFEST01.json')
for name in helper_names:
    path=HERE/name;assert path.is_file() and not path.is_symlink(), name
    names.append(str(path.relative_to(ROOT)))
assert len(names)==len(set(names))
'''
footer="""selection={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_actual_recovery':baseline_pins[0],'baseline_accepted_review':baseline_pins[1],'baseline_source':prior['source'],'files':len(rows),'body_bytes':sum(r['bytes'] for r in rows),'rows':rows,'directories':dirs,'symlinks':sum(r['type']=='symlink' for r in rows),'qualification':'Only fixed corrected38 registration metadata and actual33 postcapture/review bodies. No claim, release, final binding,36 recopy, runtime envelope or historical store is selected.'}
with (HERE/'SELECTION34.json').open('x') as stream:json.dump(selection,stream,indent=2,sort_keys=True);stream.write('\\n')
print(json.dumps({'selected_files':len(rows),'selected_bytes':selection['body_bytes'],'directories':len(dirs)}))
"""
body=body.replace('    rows.append(row)', "    assert row['type']=='regular' and row['sha256']==expected_hashes[relative], relative\n    rows.append(row)")
products['select']=header+body+footer;originals['select']=oldselect
forward=[];inverse=[]
for name,s in products.items():
 ast.parse(s);(P/(name+'34.py')).write_text(s)
 oldname=name+('33_02.py' if name=='select' else '33.py')
 forward.extend(difflib.unified_diff(originals[name].splitlines(True),s.splitlines(True),fromfile=str((OLD/oldname).relative_to(R)),tofile=str((DEP/(name+'34.py')).relative_to(R))))
 inverse.extend(difflib.unified_diff(s.splitlines(True),originals[name].splitlines(True),fromfile=str((DEP/(name+'34.py')).relative_to(R)),tofile=str((OLD/oldname).relative_to(R))))
(P/'LITERAL_PATCH01.diff').write_text(''.join(forward));(P/'LITERAL_INVERSE01.diff').write_text(''.join(inverse))
scope={'status':'UNEXECUTED_CANDIDATE','deployment_directory':str(DEP.relative_to(R)),'baseline':ref(prior),'accepted_return_review':ref(review),'selected_pins':selected,'unchanged33_rows_omitted':reused,'excluded_duplicate_names':['pilot38-preparation-increment33.tar','fresh-git-recovered-full38increment33.tar','actual_external_archive_blob_return.stdout'],'capture_recover_aliases':maps,'capture_recover_nonstring_ast_equal':True,'helper_execution':False,'final_binding_or_release_selected':False}
(P/'TOOL_SCOPE01.json').write_text(json.dumps(scope,indent=2)+'\n')
files=['select34.py','capture34.py','recover34.py','TOOL_SCOPE01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff']
(P/'HELPERS_MANIFEST01.json').write_text(json.dumps({str((DEP/n).relative_to(R)):sha(P/n) for n in files},indent=2)+'\n')
print(json.dumps({'selected':len(selected),'bytes':sum(r['bytes'] for r in selected),'reused':reused,'helpers_executed':False}))
