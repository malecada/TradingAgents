"""Prepare finite native03 outcome preservation source; execute no helpers."""
import ast,difflib,hashlib,json,os,re,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
H=Path(__file__).resolve().parent;O=H.parent/'postnative28';F=H.parent.parent
owned=['pilot34-native-owner-qualification03-2026-10-11','pilot34-native-owner03-outcome-review01-2026-10-11','pilot34-postnative-increment-return-review01-2026-10-11','pilot34-two-attribute-main-integration-bundle01-2026-10-11','pilot34-native03-increment-tools-review01-2026-10-11', 'pilot34-two-attribute-main-integration-review01-2026-10-11']
helpers=('select29.py','capture29.py','recover29.py','prepare29.py','check_source29.py','HELPERS_MANIFEST01.json','AUTHOR_CHECK01.json','PROSPECTIVE_ROSTER01.json','PREPARATION_CHECK01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff','REPORT.md')
operations=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
priorfiles=['SELECTION28.json','CAPTURE28.json','FRESH_GIT_RECOVERY28.json','GIT_OPERATIONS28.json','ROOT_ACTUAL_OPERATIONS28.json','root_commit28.stdout','root_commit28.stderr']+[n+'.'+k for n in operations for k in ('stdout','stderr')]
recovery_hash=hashlib.sha256((O/'FRESH_GIT_RECOVERY28.json').read_bytes()).hexdigest()
def once(text,mapping):
 for token in mapping:assert token in text,token
 return re.sub('|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True)),lambda m:mapping[m.group()],text)
def assignment(text,name,value):
 start=text.index(name+'=') if name+'=' in text else text.index(name+' =')
 end=text.index('\n',start);return text[:start]+name+'='+repr(value)+text[end:]
old=(O/'select28.py').read_text()
select=once(old,{
 "outcome27/FRESH_GIT_RECOVERY27.json":"postnative28/FRESH_GIT_RECOVERY28.json",
 '4bf7836d45312d5a089f94825cf97762c9121cff163d2ddd9bbb889cdaa199ca':recovery_hash,
 'pilot34-outcome-increment-return-review01-2026-10-11':'pilot34-postnative-increment-return-review01-2026-10-11',
 '15f94fd288e1bf89feb911e578829303e9b223be70524047a70053b894381af8':'71e99df6ce8daf7226c2b91a42716cbbd35fd97d1bd6a9656365918f6d35259b',
 "prior.parent/'CAPTURE27.json'":"prior.parent/'CAPTURE28.json'",
 "prior.parent/'SELECTION27.json'":"prior.parent/'SELECTION28.json'",
 "'failed-outcome-increment27.tar'":"'post-native-increment28.tar'",
 "'fresh-git-recovered-outcome27.tar'":"'fresh-git-recovered-postnative28.tar'",
 "HERE/'SELECTION28.json'":"HERE/'SELECTION29.json'",
 'actual27':'actual28','accepted27':'accepted28','generated27':'generated28','outcome27 archive':'postnative28 archive','selection28 already spent':'selection29 already spent','generated postnative28':'generated nativeoutcome29','declared postnative28 scope':'declared nativeoutcome29 scope'})
for name,value in [('owned',owned),('prior_generated_names',priorfiles),('helper_names',helpers),('main_source_names',[])]:select=assignment(select,name,value)
start=select.index("assert set(main_source_names)<=names");end=select.index('\nreused=[]',start)
select=select[:start]+"# Main installation is outside this preparation; only public bundle bodies.\n"+select[end:]
select=select.replace("    'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused'],", "    'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused'],\n    'earlier_inherited_reuse_preserved_by_receipt':prior_selection['prior_inherited_reuse_preserved_by_receipt'],")
start=select.index("    'selection_rule': ");end=select.index('\n',start)
select=select[:start]+"    'selection_rule': 'Finite postnative28 receipts and raw Git outputs, actual native03 source/outcome/review, accepted28 return review, new public integration bundle and independent tools review. Previous28 eight reused rows and67 earlier inherited rows retain accepted receipt continuity. No Main installation, empirical/private/runtime store traversal, older archive replay or deletion authority.',"+select[end:]
capture_map={'SELECTION28.json':'SELECTION29.json','CAPTURE28.json':'CAPTURE29.json','post-native-increment28.tar':'native-outcome-increment29.tar','Complete declared public postnative28 increment':'Complete declared public nativeoutcome29 increment'}
recover_map={'Recover the one declared postnative28 public increment':'Recover the one declared nativeoutcome29 public increment','real-pilot-postnative-20261011-28.git':'real-pilot-native03-outcome-20261011-29.git','FRESH_GIT_RECOVERY28.json':'FRESH_GIT_RECOVERY29.json','GIT_OPERATIONS28.json':'GIT_OPERATIONS29.json','CAPTURE28.json':'CAPTURE29.json','fresh-git-recovered-postnative28.tar':'fresh-git-recovered-nativeoutcome29.tar','Complete declared postnative28 public increment only':'Complete declared nativeoutcome29 public increment only'}
texts={'select':select,'capture':once((O/'capture28.py').read_text(),capture_map),'recover':once((O/'recover28.py').read_text(),recover_map)}
patch=[];inverse=[]
for name,text in texts.items():
 ast.parse(text)
 with (H/(name+'29.py')).open('x') as f:f.write(text)
 before=(O/(name+'28.py')).read_text();patch.extend(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile=name+'28.py',tofile=name+'29.py'));inverse.extend(difflib.unified_diff(text.splitlines(True),before.splitlines(True),fromfile=name+'29.py',tofile=name+'28.py'))
for name,text in [('LITERAL_PATCH01.diff',''.join(patch)),('LITERAL_INVERSE01.diff',''.join(inverse))]:
 with (H/name).open('x') as f:f.write(text)
roster={'status':'PROSPECTIVE_UNEXECUTED','owned_public_roots':owned,'main_source_names':[],'helper_names':helpers,'prior_generated_files':priorfiles,'fixed_public_names':['research/onchain-paper-replication-2026-09-24/STATE.md','research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md'],'capture_literal_map':capture_map,'recovery_literal_map':recover_map,'baseline_source':'7d7adf135f319530770c328cb19a7ec438364994','baseline_recovery_sha256':recovery_hash,'accepted_return_sha256':'71e99df6ce8daf7226c2b91a42716cbbd35fd97d1bd6a9656365918f6d35259b','prior_reused_rows':8,'earlier_inherited_rows':67,'scopes':[],'helpers_executed':False}
with (H/'PROSPECTIVE_ROSTER01.json').open('x') as f:json.dump(roster,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'status':'PREPARED_SOURCE_ONLY','mandatory_roots':owned,'missing':[n for n in owned if not (F/n).is_dir()]}))
