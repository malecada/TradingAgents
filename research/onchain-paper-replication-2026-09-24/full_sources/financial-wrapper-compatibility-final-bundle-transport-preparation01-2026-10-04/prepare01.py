from pathlib import Path
import ast,json,hashlib,shutil
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];A=F/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';S=F/'financial-wrapper-compatibility-operational-delta-flat-source-mode-successor04-2026-10-04';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(A/'recover01.py')=='ada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf';assert h(A/'watch01.py')=='bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18'
shutil.copyfile(A/'watch01.py',D/'watch01.py');shutil.copytree(A/'utilities',D/'utilities');shutil.copyfile(A/'recover01.py',D/'ORIGINAL_REMOTE01.py');shutil.copyfile(S/'restore01.py',D/'ORIGINAL_FLAT01.py')
known={}
for dirname in ['financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04','financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04']:
 for p in sorted((F/dirname).iterdir()):
  if p.is_file():known[str(p.relative_to(ROOT))]={'bytes':p.stat().st_size,'sha256':h(p)}
(D/'KNOWN_REQUIRED01.json').write_text(json.dumps(known,indent=2,sort_keys=True)+'\n')
# This is an unbound executable template: explicit None refuses before network.
s=(A/'recover01.py').read_text();ed=[]
def replace(old,new):
 global s
 assert s.count(old)==1;s=s.replace(old,new);ed.append({'old':old,'new':new})
line=next(x for x in s.splitlines() if x.startswith('REQUIRED ='))
replace(line,'REQUIRED = None\nFINAL_POPULATION_COUNT = None')
replace("rows=selection['rows'];require(type(rows) is list and len(rows)==len(REQUIRED)==15, 'exact fifteen selected paths')","require(type(REQUIRED) is dict and type(FINAL_POPULATION_COUNT) is int, 'unreleased final population')\n    rows=selection['rows'];require(type(rows) is list and len(rows)==len(REQUIRED)==FINAL_POPULATION_COUNT, 'exact fixed final selected paths')")
replace('fresh-operational-source-policy02.git','fresh-compatibility-final-bundle01.git')
replace('fresh-actual-remote-operational-source-policy01-supervised-recovered','fresh-actual-remote-compatibility-final-bundle01-supervised-recovered')
(D/'recover.template01.py').write_text(s);back=s
for e in reversed(ed):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(A/'recover01.py').read_text()
# Inherited verified readers, canonical-byte checks and fatal cleanup remain exact AST.
raw=(S/'restore01.py').read_text();tree=ast.parse(raw);names=['VerifiedCohort','hexpin','number','verify_flat'];segments=[]
for name in names:
 node=next(x for x in tree.body if isinstance(x,(ast.ClassDef,ast.FunctionDef)) and x.name==name);segments.append(ast.get_source_segment(raw,node))
(D/'inherited01.py.txt').write_text('\n\n'.join(segments)+'\n')
(D/'SOURCE_INVERSE01.json').write_text(json.dumps({'remote_original_sha256':h(A/'recover01.py'),'watch_unchanged_sha256':h(D/'watch01.py'),'remote_template_sha256':h(D/'recover.template01.py'),'literal_edits':ed,'whole_literal_AST_inverse':ast.dump(ast.parse(back))==ast.dump(tree if False else ast.parse((A/'recover01.py').read_text())),'inherited_classes_functions':names,'inherited_source_sha256':h(S/'restore01.py')},indent=2)+'\n')
draft={'schema_version':1,'status':'DRAFT_NOT_RELEASED','source':'32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41','source_tracked':355,'source_pins':354,'input_roles':11,'whole_source_typed':605,'whole_source_regular':491,'whole_git_objects':407,'basis_git_objects':394,'additional_git_objects':13,'basis_source_typed':589,'additional_files':15,'additional_directories':1,'actual_main_commit':None,'exact_required':None,'bundles':None,'complete_final_request':None,'complete_final_release':None,'complete_three_proofs':None,'coalesced_actual_review':None,'source_runtime_bridge':None,'accepted_baseline_byte_review':None,'independent_final_population_review':None,'actual_remote_receipt':None,'actual_selected_mode_profile':None,'actual_restore_release':None}
(D/'REQUEST_DRAFT01.json').write_text(json.dumps(draft,sort_keys=True,indent=2)+'\n');print('source template and seven known capture bodies pinned; final dependencies null')
