from pathlib import Path
import ast,hashlib,json,os,stat,time
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(n,x):
 p=H/n;p.write_text(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
controls=json.loads((H/'CONTROLS01.json').read_bytes());recon=json.loads((H/'RECONSTRUCTION01.json').read_bytes());closure=json.loads((H/'CLOSURE01.json').read_bytes())
source='421cc50f32b1bf1d6a483991deea0fa6700aeb4d165ddc1cecf64dacc08dc4a2';policy='ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887';checker='d0d770b45def89e8e00e81fa1bbb35416034eaace5ecab0f15193fd43b7a32d8';oldmap='ebb1727ccb55678aead9f0d5b5ee43ec81a46019c7fbb13c4b4f76144507bbca';newmap='2e281f7ca64a12be316424d8e93b0eab28ba0d121214e79ada7249c96930b040'
report='''Correction02 is accepted for the exact actual operational SOURCE_POLICY BYTE composition. This independent review authors the accompanying genuine seven-field recovery proof; it does not install source, register a gate, start a claim or release numerical execution.

The five declared literal substitutions invert exactly to original14145d47, with full AST equality after inversion. All semantic run/Git/map/body/cap functions and INPUTSf992 are unchanged. The embedded dependency is exactly owned_io09d1. Independently executed 265 assertions across 106 named error-pair cases and additional normal/currentness checks reproduce original CR1–CR3 failure behavior and corrected first-fatal preservation. Actual opened file descriptors and scandir iterators are closed once; all tested original and secondary objects remain reachable, including hostile string/cause/attribute hooks. Original source01, WITHHELD review, raw witnesses and Root observed-only measurement remain untouched. These tests do not promise allocation-failure equivalence or unstoppable asynchronous immunity.

The independent reconstruction performed 16,965 assertions, reading 1,667 distinct regular paths and 83,692,907 bytes. It freshly reconstructed all 15 canonical gzip/TAR archive scopes: ten original failed-scope shards, three baseline Git shards and both newly restored scopes. The complete original capsule has475 bodies/588 typed entries. Current589 entries equal protected585 plus four explicit source changes. All194 historical and195 target path/hash entries are checked, with191 unchanged bodies and150 package paths. All385 historical plus9 new logical Git objects have authenticated type/framing/OID and complete recursively reachable ancestry, canonical directory-slash tree ordering and current340 tracked body/executable-mode joins. Both actual new flat scopes contain all64 original bodies plus two metadata files/full83 typed descendants.

An additional1,754 assertions authenticate the complete54-member correction source seal, all captured new snapshot/original-body modes, the complete failed receiver43-member tree and all38 literal receipt copies. FIFO, symlink, hardlinked and over-cap negative source controls are classified only from bounded metadata and never followed or decoded. The corrected Root measurement f5f39af8/stdout87d9be65 authenticates a different, explicitly retained read denominator:1,727 files/84,824,406 bytes, child1047751/exit0/2.0186609s, empty stderr and current child absence. The review does not rename its own83.69MB scope as that84.82MB measurement. All substantive complete byte/Git populations and every ancillary receipt are independently joined, rather than relying on the35-receipt subset alone.

The35 original receipt bodies (979,449 bytes) plus three actual corrected-measurement receipts are copied literally below receipts/. Original paths, original modes, private copy modes, extents and hashes are recorded in CLOSURE01.json. Every machine receipt reference is unique and inside this review's typed manifest. Original flat actual_root_exit=NULL remains unchanged; the distinct actual Root exit0 is joined through its real terminal. Failed remote init-observed=NULL/reaped0/Root1 and unknown changed-path fields remain unknown. Three original research identities remain FAILED/spent, highest actual allowance19; no outcome or allowance is reset.

The proof establishes byte preservation and original-mode metadata for the exact Source7b056/policyae8f/oldmapebb1727/newmap2e281 composition. It excludes POSIX reconstruction, installed runtime package bodies, unrelated stores, atomic writer exclusion/ABA immunity, whole-fit resource capacity, numerical or financial agreement, caller/native release, and the still-future gate/final-caller supplement. No numerical package, checkpoint deserializer, network, external restore, Root entry or research lifecycle API was executed. This review only reads opaque checkpoint bytes for hashes. All1,420 paper fits remain pending.

Root must preserve and bind these exact proof/machine/report/manifest and literal receipt bodies, freeze the prospective gate and final caller, measure the complete preclaim8MiB read budget including final rereads without increasing caps or omitting evidence, and complete separately reviewed final recovery and native eligibility. The evidence-subset Reader test is not that full preclaim success path. Future authorisation remains absent.
'''
(H/'REPORT01.md').write_text(report);(H/'REPORT01.md').chmod(0o600)
proof={'schema_version':1,'kind':'operational_source_compatibility_recovery','policy_sha256':policy,'historical_map_sha256':oldmap,'target_map_sha256':newmap,'checker_sha256':checker,'decision':'accepted'};save('RECOVERY_PROOF01.json',proof)
refs=closure['actual_receipts'];assert len({r['path'] for r in refs})==len(refs)==38
machine={'schema_version':1,'decision':'ACCEPTED_ACTUAL_OPERATIONAL_SOURCE_POLICY_BYTE_RECOVERY','reviewer':'combined_worker_review; independent from correction source author storage_watch_review and actual Root execution','source_commit':'7b056a574e3e7b3c7ba209a39ee6a615e649d60c','source_sha256':source,'source_author_manifest_sha256':'7770b127e03f3c6ef0a3169844c6cb8bccba3a7eada3f401d2f88487434cc76e','policy_sha256':policy,'checker_sha256':checker,'historical_map_sha256':oldmap,'target_map_sha256':newmap,'recovery_proof_sha256':sha((H/'RECOVERY_PROOF01.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'recovery_receipts':refs,'actual_corrected_measurement_sha256':'f5f39af820922a2bb4b38762bd9f4a2218790c52504a67eee4b8620494deecf7','actual_corrected_stdout_sha256':'87d9be65addeb2f43f96606f6d0b5daf4e8ad787b40db395de0f141d7b8299d3','actual_root_files':1727,'actual_root_bytes':84824406,'independent_reconstruction_files':1667,'independent_reconstruction_bytes':83692907,'assertions':{'cleanup_source':265,'complete_reconstruction':16965,'supplemental_authentication':1754},'current_typed':589,'protected_typed':585,'historical_paths':194,'target_paths':195,'unchanged_paths':191,'package_paths':150,'old_git_objects':385,'new_git_objects':9,'complete_reachable_git_objects':394,'tracked':340,'failed_claims':recon['claims'],'global_spent':3,'highest_actual_allowance':19,'actual_original_root_nulls_preserved':True,'source_installed_by_reviewer':False,'byte_and_original_mode_metadata_only':True,'posix_tree':False,'runtime_package_bodies':False,'unrelated_stores':False,'atomic_writer_exclusion':False,'whole_capacity':None,'numerical_authority':False,'final_caller_release':None,'full_preclaim_success_or_8MiB_fit_proven':False,'original_CR1_CR2_CR3_preserved':True}
save('MACHINE01.json',machine)
# Execute only the genuine stdlib Reader and _sealed metadata functions against
# actual authored proof and literal existing receipt copies, no Admission/Inputs.
pre=B/'financial-wrapper-compatibility-preclaim-source01-2026-10-04/preclaim01.py';tree=ast.parse(pre.read_bytes());names={'Unavailable','CleanupFailure','require','sha','canonical','digest','relative','_close','Reader','_sealed'}
ns={'Path':Path,'PurePosixPath':__import__('pathlib').PurePosixPath,'json':json,'os':os,'stat':stat,'hashlib':hashlib,'time':time,'FILE':4194304,'TOTAL':8388608,'SECONDS':120}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names],type_ignores=[]),'genuine preclaim metadata components','exec'),ns)
def census():
 rows=[];todo=[H]
 while todo:
  p=todo.pop()
  with os.scandir(p) as it:
   for e in it:
    n=Path(e.path).relative_to(H).as_posix()
    if n=='MANIFEST01.json':continue
    s=e.stat(follow_symlinks=False);r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
    if stat.S_ISDIR(s.st_mode):r['kind']='directory';todo.append(Path(e.path))
    elif stat.S_ISREG(s.st_mode):assert s.st_nlink==1 and s.st_size<=4194304;r.update(kind='file',bytes=s.st_size,sha256=sha(Path(e.path).read_bytes()))
    else:raise AssertionError('unowned unexpected special')
    rows.append(r)
 return sorted(rows,key=lambda r:r['path'])
manifest={'members':census()};reader=ns['Reader']();mref={'path':str(H/'MANIFEST01.json'),'sha256':'0'*64}
for r in refs+[{'path':str(H/n),'sha256':sha((H/n).read_bytes())} for n in ['RECOVERY_PROOF01.json','MACHINE01.json','REPORT01.md']]:ns['_sealed'](manifest,mref,r,reader)
reader.finish()
save('SEALED_COMPONENT_CHECK01.json',{'genuine_preclaim_source_path':str(pre),'genuine_preclaim_source_sha256':sha(pre.read_bytes()),'component_only':'Reader.reference + _sealed + Reader.finish','actual_references':41,'actual_read_bytes_including_finish':reader.total,'bound':8388608,'full_preclaim_or_Admission_executed':False,'final_complete_bundle_fit':None,'result':'passed'})
rows=census();save('MANIFEST01.json',{'schema_version':1,'manifest_self_excluded':True,'root':str(H),'members':rows,'typed_members':len(rows),'regular_files':sum(x['kind']=='file' for x in rows),'logical_bytes':sum(x.get('bytes',0) for x in rows),'links_followed':False})
# final immutable seal consistency
for r in rows:
 p=H/r['path'];assert stat.S_IMODE(p.lstat().st_mode)==r['mode']
 if r['kind']=='file':assert len(p.read_bytes())==r['bytes'] and sha(p.read_bytes())==r['sha256']
print(json.dumps({'MANIFEST01':sha((H/'MANIFEST01.json').read_bytes()),'MACHINE01':sha((H/'MACHINE01.json').read_bytes()),'REPORT01':sha((H/'REPORT01.md').read_bytes()),'RECOVERY_PROOF01':sha((H/'RECOVERY_PROOF01.json').read_bytes()),'typed':len(rows),'regular':sum(x['kind']=='file' for x in rows),'bytes':sum(x.get('bytes',0) for x in rows),'genuine_Reader_subset_bytes':reader.total},sort_keys=True))
