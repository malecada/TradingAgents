"""Author-only literal adaptation. Does not select, capture, recover, or run Git."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
D=Path(__file__).resolve().parent
F=D.parent.parent
R=F.parents[2]
B=D.parent/'full35increment30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace_once(source, old, new):
    assert source.count(old)==1, old
    return source.replace(old,new)
source=(B/'select30.py').read_text()
# Explicit identity substitutions, never blanket digit replacements.
for old,new in {
'nativeoutcome29/FRESH_GIT_RECOVERY29.json':'full35increment30/FRESH_GIT_RECOVERY30.json',
'd297b714a4cc2cc014a026040d85cd2da537e50b3eab94e273edd08abbc54609':'32023dba761dbdcfc0fccd9bb9749a5320bdd345efa26a22411ca58be0f15d62',
'pilot34-native03-increment-return-review01-2026-10-11/REVIEW01.json':'pilot35-preparation-increment-return-review01-2026-10-11/REVIEW01.json',
'a522ca34f5e90c317002d3431875aab2896afeb64b01c9bc710d5454aacaa9e7':'170c85ab7eb08000467d7eeec098e1feb153ce8675b687d99f959728767dfbed',
'actual29':'actual30','accepted29':'accepted30','generated29':'generated30',
'CAPTURE29.json':'CAPTURE30.json','SELECTION29.json':'SELECTION30.json',
'SELECTION30.json\').exists()':'SELECTION31.json\').exists()',
'SELECTION30.json\').open':'SELECTION31.json\').open',
'selection30 already spent':'selection31 already spent','full35increment30 products':'full35outcome31 products',
'full35increment30 scope':'full35outcome31 scope',
'native-outcome-increment29.tar':'full35-preparation-increment30.tar',
'fresh-git-recovered-nativeoutcome29.tar':'fresh-git-recovered-full35increment30.tar',
}.items():
    assert old in source,old
    source=source.replace(old,new)
owned=[f'pilot-efficiency-{n}-2026-10-11' for n in ('implementation','admission-timing-review','authority-profile','backend-caller','bottleneck-model','error-retention','expected-code-review','numeric-kernel','storage-scan')]
owned+=['authority-expected-code-cache-candidate02-2026-10-11']
owned += [f'implementation-audit-{n}-2026-10-11' for n in ('performance','science-data','runtime-storage')]
owned += ['pilot35-stale-boundary-investigation01-2026-10-11','pilot35-terminal-outcome-review-2026-10-11','real-data-pilot-full35-entry-preparation01-2026-10-11','pilot35-efficiency-increment31-tools-review-2026-10-11','pilot35-preparation-increment-return-review01-2026-10-11']
snapshot=F/'pilot-efficiency-implementation-2026-10-11/SOURCE_SNAPSHOT01.json'
snap=json.loads(snapshot.read_bytes());pins={row['path']:row['sha256'] for row in snap['files']};assert len(pins)==23
terminal=F/'pilot35-terminal-outcome-review-2026-10-11/REVIEW01.json'
assert sha(terminal)=='7224646b35c3fe8094c19288ad81be7c1650be458b7a3723198e82bc1a86aba4'
raw_scopes=json.loads(terminal.read_bytes())['incremental_raw_scopes']
assert len(raw_scopes)==6 and [row['exists'] for row in raw_scopes]==[True]*5+[False]
helpers=('select31.py','capture31.py','recover31.py','prepare31.py','check_source31.py','CAPTURE_RECOVERY_LITERAL_MAP01.json','HELPERS_MANIFEST01.json','AUTHOR_CHECK01.json','PROSPECTIVE_ROSTER01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff','REPORT.md')
prior_names=['SELECTION30.json','CAPTURE30.json','FRESH_GIT_RECOVERY30.json','GIT_OPERATIONS30.json','ROOT_ACTUAL_OPERATIONS30.json','root_commit30.stdout','root_commit30.stderr']
ops=('local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return')
prior_names += [n+'.'+s for n in ops for s in ('stdout','stderr')]
fixed=['research/onchain-paper-replication-2026-09-24/STATE.md','research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md','research/onchain-paper-replication-2026-09-24/IMPLEMENTATION_REVIEW_2026-10-11.md','docs/superpowers/plans/2026-10-11-onchain-pilot-efficiency.md']
assignments={'owned':repr(owned),'prior_generated_names':repr(prior_names),'helper_names':repr(helpers),'fixed_public_names':repr(fixed),'main_source_names':repr(sorted(pins)),'main_source_pins':repr(pins)}
for name,value in assignments.items():
    tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    old='\n'.join(source.splitlines()[node.lineno-1:node.end_lineno]);source=replace_once(source,old,name+'='+value)
old='# No original failed34 scientific/runtime scopes are traversed or admitted.\nscopes=[]'
new="""# Exact original35 scope from independently accepted terminal metadata.
terminal_review=F/'pilot35-terminal-outcome-review-2026-10-11/REVIEW01.json'
assert sha(terminal_review)=='7224646b35c3fe8094c19288ad81be7c1650be458b7a3723198e82bc1a86aba4'
raw_scope_states=RAW_STATES
assert json.loads(terminal_review.read_bytes())['incremental_raw_scopes']==raw_scope_states
scopes=[]
for row in raw_scope_states:
    root=ROOT/row['path']
    if not row['exists']:
        assert not root.exists() and not root.is_symlink(), 'originally absent sixth scope appeared: '+row['path']
        continue
    assert root.is_dir() and not root.is_symlink() and root.resolve(strict=True)==root, row['path']
    scopes.append(root);scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
# Source snapshot is the engineering body roster, not original pilot35 source.
snapshot=F/'pilot-efficiency-implementation-2026-10-11/SOURCE_SNAPSHOT01.json'
assert sha(snapshot)=='SNAP_SHA', 'reviewed engineering snapshot changed'
""".replace('RAW_STATES',repr(raw_scopes)).replace('SNAP_SHA',sha(snapshot)).rstrip()
source=replace_once(source,old,new)
source=replace_once(source,'allowed_roots=[F/name for name in owned]','allowed_roots=[F/name for name in owned]+scopes')
source=replace_once(source,"'actual_scope_states': [{'path':str(scope.relative_to(ROOT)),'exists':scope.exists(),'empty_directories_included':True} for scope in scopes],","'actual_scope_states': raw_scope_states,")
source=replace_once(source,"'baseline_source': base,","'baseline_source': base,\n    'baseline_accepted_review': {'path':str(review.relative_to(ROOT)), 'sha256':sha(review)},\n    'terminal_review': {'path':str(terminal_review.relative_to(ROOT)), 'sha256':sha(terminal_review)},\n    'engineering_source_snapshot': {'path':str(snapshot.relative_to(ROOT)), 'sha256':sha(snapshot)},")
source=source.replace('Already returned postnative28 archive/blob','Already returned preparation30 archive/blob')
old='Finite fresh35 public preparation and reviews, exact installed ten Main sources and actual30 postcapture receipts. Prior rows reused only on exact typed body match; inherited coverage retained through authenticated actual30 receipt. No empirical/private/runtime stores or deletion authority.'
new='Finite failed35 five original raw scopes as opaque bodies, sixth absent; exact23 reviewed engineering source/tests, named docs/public evidence and actual30 postcapture receipts. Prior rows reused only on exact typed body match; inherited coverage retained through authenticated actual30 receipt. No private runtime, unrelated historical raw traversal or deletion authority.'
source=replace_once(source,old,new)
(D/'select31.py').write_text(source)
roster={'public_roots':owned,'raw_scope_states':raw_scopes,'source_snapshot':{'path':str(snapshot.relative_to(R)),'sha256':sha(snapshot)},'fixed_public_files':fixed,'source_files':sorted(pins),'prior_generated_files':prior_names,'helper_names':helpers,'selection_precondition':'Root final scope freeze after offline logs and independent tools review; no selection/capture/recovery executed by author.'}
(D/'PROSPECTIVE_ROSTER01.json').write_text(json.dumps(roster,indent=2,sort_keys=True)+'\n')
patch=[];inverse=[]
for stem in ('select','capture','recover'):
    old=(B/(stem+'30.py')).read_text().splitlines(True);new=(D/(stem+'31.py')).read_text().splitlines(True)
    patch.extend(difflib.unified_diff(old,new,fromfile=stem+'30.py',tofile=stem+'31.py'))
    inverse.extend(difflib.unified_diff(new,old,fromfile=stem+'31.py',tofile=stem+'30.py'))
(D/'LITERAL_PATCH01.diff').write_text(''.join(patch));(D/'LITERAL_INVERSE01.diff').write_text(''.join(inverse))
print('Prepared finite31 source; no selector/capture/recovery execution.')
