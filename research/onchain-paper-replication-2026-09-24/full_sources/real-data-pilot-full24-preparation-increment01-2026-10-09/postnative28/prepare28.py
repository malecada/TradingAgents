"""Write prospective helpers only; never execute selection/capture/recovery."""
import ast,difflib,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'outcome27';F=HERE.parent.parent;ROOT=F.parents[2]
owned=['pilot34-outcome-increment-return-review01-2026-10-11','pilot34-native-owner-qualification02-2026-10-11','pilot34-linux-memfd-compatibility-probe01-2026-10-11','pilot34-serializer-postclosure-install01-2026-10-11','pilot34-native-owner02-outcome-and-serializer-install-review01-2026-10-11','matching-compiled-two-attribute-caller-candidate01-2026-10-11','matching-compiled-two-attribute-caller-candidate02-2026-10-11','matching-compiled-two-attribute-caller-candidate03-2026-10-11','matching-compiled-two-attribute-caller-source-review01-2026-10-11','matching-compiled-two-attribute-caller-source-review02-2026-10-11','matching-compiled-two-attribute-caller-source-review03-2026-10-11','pilot34-native-owner-qualification03-2026-10-11','pilot34-native-owner-qualification03-entry-review01-2026-10-11','pilot34-postnative-increment-tools-review01-2026-10-11']
helpers=('capture28.py','recover28.py','select28.py','HELPERS_MANIFEST01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff','AUTHOR_CHECK01.json','REPORT.md','prepare28.py','check_source28.py','PROSPECTIVE_ROSTER01.json','PREPARATION_CHECK01.json')
operations=['local_head','remote_get_url','remote_actual_branch_readback','local_archive_git_tree_join','fresh_bare_init','fresh_remote_add','set_promisor','set_tree_zero_filter','actual_external_commit_only_fetch','fetched_head_readback','actual_external_commit_body','actual_external_selected_blob_fetch','actual_external_archive_blob_return']
prior_files=['SELECTION27.json','CAPTURE27.json','FRESH_GIT_RECOVERY27.json','GIT_OPERATIONS27.json','ROOT_ACTUAL_OPERATIONS27.json']+[name+'.'+kind for name in operations for kind in ('stdout','stderr')]
main_files=['tradingagents/research/onchain_replication/'+name for name in ('provenance.py','neighborhoods.py','imported_mcm_identity.py','imported_authority_lease.py','original_import_preparation.py')]
fixed=['research/onchain-paper-replication-2026-09-24/STATE.md','research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
recovery_hash=digest(OLD/'FRESH_GIT_RECOVERY27.json')
select=(OLD/'select27.py').read_text()
select=select.replace("prior = HERE.parent/'full34increment26/FRESH_GIT_RECOVERY26.json'",f"prior = HERE.parent/'outcome27/FRESH_GIT_RECOVERY27.json'\nassert sha(prior)=={recovery_hash!r}, 'actual27 baseline receipt changed'\nreview=F/'pilot34-outcome-increment-return-review01-2026-10-11/REVIEW01.json'\nassert sha(review)=='15f94fd288e1bf89feb911e578829303e9b223be70524047a70053b894381af8', 'accepted27 return review changed'")
start=select.index('owned = ');end=select.index('\nscope_directories=set()',start);select=select[:start]+'owned = '+repr(owned)+select[end:]
start=select.index('public_metadata_dependencies = ');end=select.index('# Already returned preparation',start)
block=f'''# Exact generated27 receipts/raw operations only. Never traverse historical H.
prior_generated_names={prior_files!r}
for name in prior_generated_names:
    path=prior.parent/name
    assert path.is_file() and not path.is_symlink(), 'required actual27 receipt absent: '+name
    names.add(str(path.relative_to(ROOT)))
helper_names={helpers!r}
for name in helper_names:names.add(str((HERE/name).relative_to(ROOT)))
fixed_public_names={fixed!r}
for relative in fixed_public_names:
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink(), relative
    names.add(relative)
main_source_names={main_files!r}
# No original failed34 scientific/runtime scopes are traversed or admitted.
scopes=[]
'''
select=select[:start]+block+select[end:]
select=select.replace('# Already returned preparation archive/blob stdout stay immutable at original','# Already returned outcome27 archive/blob stdout stay immutable at original')
select=select.replace("prior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())", "assert prior_receipt['capture']['path']==str((prior.parent/'CAPTURE27.json').relative_to(ROOT))\nassert sha(ROOT/prior_receipt['capture']['path'])==prior_receipt['capture']['sha256'], 'actual27 capture receipt changed'\nprior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())")
select=select.replace("for relative in excluded:", "assert excluded=={str((prior.parent/name).relative_to(ROOT)) for name in ('failed-outcome-increment27.tar','fresh-git-recovered-outcome27.tar','actual_external_archive_blob_return.stdout')}\nfor relative in excluded:")
select=select.replace("assert path.is_file() and sha(path)==prior_receipt['returned_archive']['sha256'], relative","assert path.is_file() and not path.is_symlink() and path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256'], relative")
select=select.replace("prior.parent/'SELECTION26.json'","prior.parent/'SELECTION27.json'")
select=select.replace("assert not (HERE/'SELECTION27.json').exists(), 'selection27 already spent'","assert not (HERE/'SELECTION28.json').exists(), 'selection28 already spent'")
start=select.index('assert all(not (ROOT/relative).is_relative_to(HERE)');end=select.index('\nreused=[]',start)
select=select[:start]+'''assert all(not (ROOT/relative).is_relative_to(HERE) or (ROOT/relative).name in helper_names for relative in names), 'generated postnative28 products are outside selection'
# Bound actual committed/working Git deltas to this declared finite increment.
allowed_files=set(fixed_public_names+main_source_names)|{str((prior.parent/name).relative_to(ROOT)) for name in prior_generated_names}|{str((HERE/name).relative_to(ROOT)) for name in helper_names}
allowed_roots=[F/name for name in owned]
assert all(relative in allowed_files or relative in excluded or any((ROOT/relative).is_relative_to(root) for root in allowed_roots) for relative in names), 'Git delta outside declared postnative28 scope'
assert set(main_source_names)<=names, 'actual five installed Main changes absent from Git delta'
installation=json.loads((F/'pilot34-serializer-postclosure-install01-2026-10-11/INTEGRATION01.json').read_bytes())
assert sha(F/'pilot34-serializer-postclosure-install01-2026-10-11/INTEGRATION01.json')=='bbab2992398b06cd8a9fd583f95cc973d7944364279ccfb2bffdf0a3f5b9da59', 'accepted serializer receipt changed'
assert not (F/'pilot34-native-owner-qualification03-2026-10-11/attempt01').exists(), 'prospective native03 identity already attempted'
assert len(installation['modules'])==5 and {m['destination']['path'] for m in installation['modules']}==set(main_source_names)
for item in installation['modules']:
    reference=item['destination'];path=ROOT/reference['path']
    assert path.stat().st_size==reference['bytes'] and sha(path)==reference['sha256'], 'installed serializer differs'
''' +select[end:]
select=select.replace("'selection_rule': 'Actual failed34 public outcomes, typed trees and Root entry/closure increments plus independent actual outcome review since recovered26; exact new/changed Git bodies and immutable prior row reuse. No private dispatch, scientific/raw/runtime store duplication, alias admission or deletion authority.'","'selection_rule': 'Exact post-outcome27 public receipts, failed native02, compatibility probe, five installed serializers, prospective native03 and caller/review increments. Prior27 archive plus inherited prior26 rows retained by accepted receipt continuity; no original failed34 scope traversal, private/runtime/scientific store replay or deletion authority.'")
select=select.replace("    'actual_scope_states':", "    'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused'],\n    'mandatory_public_roots':owned,\n    'prior_generated_files':prior_generated_names,\n    'actual_scope_states':")
select=select.replace("with (HERE/'SELECTION27.json').open('x')","with (HERE/'SELECTION28.json').open('x')")
capture=(OLD/'capture27.py').read_text()
capture_map={'SELECTION27.json':'SELECTION28.json','CAPTURE27.json':'CAPTURE28.json','failed-outcome-increment27.tar':'post-native-increment28.tar','Complete declared public failed34 outcome increment':'Complete declared public postnative28 increment'}
for before,after in capture_map.items():capture=capture.replace(before,after)
recover=(OLD/'recover27.py').read_text()
recover_map={'Recover the one declared failed34 outcome public increment':'Recover the one declared postnative28 public increment','real-pilot-failed34-outcome-20261011-27.git':'real-pilot-postnative-20261011-28.git','FRESH_GIT_RECOVERY27.json':'FRESH_GIT_RECOVERY28.json','GIT_OPERATIONS27.json':'GIT_OPERATIONS28.json','CAPTURE27.json':'CAPTURE28.json','fresh-git-recovered-outcome27.tar':'fresh-git-recovered-postnative28.tar','Complete declared failed34 outcome public increment only':'Complete declared postnative28 public increment only'}
for before,after in recover_map.items():recover=recover.replace(before,after)
patch=[];inverse=[]
for name,text in [('select',select),('capture',capture),('recover',recover)]:
 ast.parse(text);path=HERE/(name+'28.py')
 with path.open('x') as stream:stream.write(text)
 before=(OLD/(name+'27.py')).read_text();patch.extend(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile=name+'27.py',tofile=name+'28.py'));inverse.extend(difflib.unified_diff(text.splitlines(True),before.splitlines(True),fromfile=name+'28.py',tofile=name+'27.py'))
for name,text in [('LITERAL_PATCH01.diff',''.join(patch)),('LITERAL_INVERSE01.diff',''.join(inverse))]:
 with (HERE/name).open('x') as stream:stream.write(text)
roster={'status':'PROSPECTIVE_REQUIRED_ROOTS_NOT_YET_ALL_FROZEN','owned_public_roots':owned,'main_source_names':main_files,'fixed_public_names':fixed,'prior_generated_files':prior_files,'helper_names':helpers,'capture_literal_map':capture_map,'recovery_literal_map':recover_map,'baseline_recovery_sha256':recovery_hash,'baseline_source':'401089cc3e973c134054fb6ef2e762cb4b152e07','scopes':[],'helpers_executed':False}
with (HERE/'PROSPECTIVE_ROSTER01.json').open('x') as stream:json.dump(roster,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps({'status':roster['status'],'mandatory_roots':len(owned),'missing_now':[n for n in owned if not (F/n).is_dir()],'helpers_executed':False},sort_keys=True))
