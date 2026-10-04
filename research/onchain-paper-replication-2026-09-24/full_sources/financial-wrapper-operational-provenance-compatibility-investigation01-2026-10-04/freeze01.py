import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((H/'SOURCE_MAP01.json').read_text())
for row in source['rows']:
 assert sha(S/row['path'])==sha(H/'source-original'/row['path'])==row['sha256']
 assert stat.S_IMODE((S/row['path']).stat().st_mode)==row['mode']
raw=json.loads((H/'RAW_CONTROLS01.json').read_text());assert raw['checks']==985
machine={'status':'PREPARATION_ONLY_NO_MIGRATION_IMPLEMENTED_OR_AUTHORIZED','source_bodies_retained':194,'source_map_unique_hashes':193,'historical_parent_source':'0a2e7639b42b9423b90743feadcda4078aa21816','current_capsule_source':'9dc5c79f738920b52947b4e63fed0397f1b5b207','actual_metadata_source_checks':985,'additional_semantic_refusals':9,'synthetic_nonrecursive_lock_control':True,'watcher_only_change_migration_possible_under_current_APIs':False,'minimum_existing_source_files_requiring_declared_changes':['workflow_storage.py','financial_wrapper_fixture.py','training.py'],'remaining_original_deployed_bodies_equal_if_only_these3change':191,'checkpoint_loader_change_needed':False,'old_and_new_hash_sets_must_remain_literal':True,'future_implementation_or_receipts':None,'source_author_handoff':'Exact constraints shared with operational-provenance candidate author; no candidate implementation reviewed here.','limitations':['No numeric imports or checkpoint deserialization','No native or claim/admission execution','No registration/accounting/source adoption','No actual external recovery acceptance','No numerical equivalence or capacity proof'],'report_sha256':sha(H/'REPORT01.md'),'protocol_sha256':sha(H/'PROTOCOL_REQUIREMENTS01.md'),'preserved_harness_failure':'INVESTIGATE01 selected enclosing If instead of exact comparison; INVESTIGATE02 corrects selector.'}
(H/'MACHINE01.json').write_text(json.dumps(machine,indent=2,sort_keys=True)+'\n')
rows=[]
for p in sorted(H.rglob('*')):
 rel=str(p.relative_to(H))
 if rel in ('MANIFEST01.json','FREEZE01.out','FREEZE01.err'):continue
 s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(p),links=s.st_nlink)
 else:raise AssertionError('unexpected kind')
 rows.append(r)
(H/'MANIFEST01.json').write_text(json.dumps({'manifest_self_excluded':True,'excluded_execution_streams':['FREEZE01.out','FREEZE01.err'],'members':rows},indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':machine['status'],'manifest_sha256':sha(H/'MANIFEST01.json'),'machine_sha256':sha(H/'MACHINE01.json'),'report_sha256':sha(H/'REPORT01.md'),'protocol_sha256':sha(H/'PROTOCOL_REQUIREMENTS01.md'),'members':len(rows)}))
