import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-storage-watch-concurrent-publication-correction01-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A/'MANIFEST01.json')=='ffbcc1efc6e56d1bf5b19830dd46a279e79f0a2b242e0e3a8ca182da421aaafb'
readback=json.loads((A/'SOURCE194_READBACK01.json').read_text());closure=json.loads((S/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json').read_text());assert closure['installed']=={r['path']:r['sha256'] for r in readback['bodies']};assert sha(S/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json')==readback['original_closure_sha256']
for r in readback['bodies']:assert sha(S/r['path'])==r['sha256']
counts=[]
for name in ('TEST05.out','TEST06.out','TEST07.out'):
 v=json.loads((A/name).read_text());counts.append(len(v['results']))
assert counts==[37,9,2]
(H/'AUTH_FINAL01.json').write_text(json.dumps({'author_manifest_sha256':sha(A/'MANIFEST01.json'),'candidate_sha256':sha(A/'workflow_storage.py'),'original_sha256':sha(A/'original_workflow_storage.py'),'inverse_sha256':sha(A/'FINAL_INVERSE08.json'),'actual_source_body_count':194,'actual_source_closure_equal':True,'declared_final_author_case_counts':counts,'author_evidence_read_only':True},indent=2)+'\n')
report='''# Independent concurrent-publication correction review

Decision: **WITHHELD_FOR_CLEANUP_EVIDENCE** for candidate `75cdf844080ec6d71e37ae81ce98f62e11beee19c81173fcd4f76ee1c1ac45d8`. The actual publication-race correction succeeds in a controlled interleaving of the genuine lifecycle helper. One independently reproduced evidence-loss defect needs a narrow correction before source acceptance.

## Actionable finding

**P2 — Preserve every nested close failure (`workflow_storage.py:60–63`, specifically line61).** On a real nested directory traversal, a KeyboardInterrupt during the child-file stat causes both the child descriptor and root descriptor to unwind. Both actual `os.close` calls completed, then distinct injected errors reported uncertain cleanup. `_cleanup` correctly re-raises the original KeyboardInterrupt, but each unwind assigns `primary.storage_cleanup_errors=(error,)`, replacing earlier evidence. Independent traversal of `__cause__`, `__context__`, `storage_cleanup_errors` and exception-group members finds only the last close error; the first is unreachable. The retained error therefore cannot establish whether child cleanup failed as well as root cleanup. Accumulate earlier secondary exception objects using the existing first-fatal discipline, without calling unsafe diagnostic formatting or re-closing any descriptor. Add a nested traversal control with two independent close failures. `CLEANUP_PROBE01.json` and `cleanup_probe01.py` preserve the exact witness. The reviewer made no candidate edits.

## Authenticated domain and successful controls

The complete author typed manifest, all retained bodies/modes/links and literal hardlink groups were independently joined to manifest `ffbcc1ef…`. All194 installed source body hashes/modes/lengths and the actual194-entry source closure were checked against the immutable capsule. Actual Git HEAD was read as `9dc5c79f738920b52947b4e63fed0397f1b5b207`. The candidate's complete literal inverse reconstructs exact original `bf52b940…`; AST comparison confirms only `_cleanup`, `StorageWatch._check`, `StorageWatch._scan` changed and only the two declared helpers were added. The original source/model/training/scientific closure remains unchanged. The author's48-case denominator is exactly37+9+2, authenticated as retained evidence rather than reused as independent expected answers.

Independent execution used pinned Main Python3.13.13 with `-B`, only stdlib and owned tiny filesystem fixtures. It extracted the actual lifecycle `_immutable`, `_encode`, `_fsync_dir` functions and ran their real exclusive creation, data flush/fsync, link, directory fsync and temporary unlink. A thread barrier released the actual publisher after the watcher enumerated the pending name and before its stat: original source raises FileNotFoundError; candidate retries and accounts the published body exactly on attempt2. No pending name is ignored. Independent controls also exercised pending-name accounting, sparse/logical/allocated/entry/depth limits, symlink and hardlink refusal, disappearance, replacement, unchanged root identity, late growth, repeated churn, aggregate deadline, ordinary close uncertainty and first-fatal precedence.

`AUDIT04` completed1,072 authentication/control assertions and27 recorded rows (including diagnostics and repeated descriptions; these are not27 distinct financial trials). `NATIVE_CONTROLS01` passed seven additional controls using actual AST-extracted `observe_storage`, `boundaries`, `_native_select`, `_native_reason`, `_native_finalize`, and the real stdlib-only owned_io implementation. These verify peak updates, breach evidence/failed phase, exact disk floor and below-floor refusal, outer deadline, first fatal surviving diagnostic failure and all independent finalization actions running after failures. Only tiny real owned descriptor closes were performed; disk/clock values were explicit synthetic inputs. No native guard, helper entry point, claim or admission ran.

## Demonstrated sampled boundary

The twelve `LATE_PROBE01` observations explicitly retain a later-directory iterator-close callback that creates a new file in the previously enumerated root. Six observations return the pre-add logical total2 while the actual tree holds5 bytes. In those six, the real filesystem reports exactly equal directory identity/mode/link/size/block/mtime/ctime signatures before and after the addition. The new literal name appears after that directory's namespace sample and is absent from `seals`. This does **not** establish a violation of the stated non-atomic, same-signature sampling qualification and is not an additional source-acceptance blocker. It is concrete evidence that “complete rejoin” cannot mean a complete tree at return time or exclude all mutations during cleanup. It must remain explicit in any acceptance description. Stronger prevention requires enforceable writer coordination or a snapshot contract, not an assertion that additional metadata scans prove immutability.

## Retained reviewer errors and limitations

AUDIT01's final raw descriptor-count assertion failed. AUDIT04 descriptor inventory identifies the extra descriptor as `/dev/urandom`, lazily opened by genuine UUID generation, not an owned tree descriptor. The separate cleanup probe has no owned descriptors left. AUDIT02/03's overstrong requirement that every late addition produce attempt2 failed on the real same-signature boundary above; original scripts/errors/fixtures remain. AUDIT04 explicitly records that boundary instead of declaring stale counts correct. All raw runs and probe bodies remain in this review directory.

No financial experiment, arrays, labels, checkpoint deserialization, runtime package admission, native launch, registration/ledger mutation, actual helper entry, network or live capsule mutation occurred. No full-production runtime, hostile syscall scheduling, interrupted/blocked syscalls, kernel quota, atomicity, continuous immutability, complete100 reference, full capacity, financial/economic validity or complete failed-outcome external recovery is established. Source inspection independently confirms the migration blocker: financial_wrapper_fixture.py:177 returns all194 source hashes, line231 puts their set in provenance, and lines277/353 require equality across prior/reference comparisons. The guard change therefore cannot silently join the old checkpoint and new corrected reference. Accounting/amendment/new identities and complete actual failed-outcome preservation remain Root-owned separate decisions. No broader effort recommendation is needed to fix the specific nested-cleanup defect.
'''
(H/'REPORT01.md').write_text(report)
machine={'status':'WITHHELD_FOR_CLEANUP_EVIDENCE','author_manifest_sha256':sha(A/'MANIFEST01.json'),'candidate_sha256':sha(A/'workflow_storage.py'),'findings':[{'priority':'P2','file':str(A/'workflow_storage.py'),'line':61,'issue':'Nested cleanup overwrites earlier secondary error objects; first fatal retained but earlier close failure unreachable.','witness':'CLEANUP_PROBE01.json'}],'authentication_assertions_and_control_assertions':1072,'audit04_record_rows':27,'native_subset_cases':7,'late_same_signature_probe_total':12,'late_same_signature_stale_samples':6,'author_case_denominator':[37,9,2],'actual_source_bodies':194,'actual_publication_red_green':True,'no_financial_execution':True,'no_source_integration':True,'reviewer_failed_runs_retained':['AUDIT01','AUDIT02','AUDIT03'],'acceptance_scope':'sampled filesystem metadata only','report_sha256':sha(H/'REPORT01.md')}
(H/'MACHINE01.json').write_text(json.dumps(machine,indent=2)+'\n')
rows=[];groups={}
for p in sorted(H.rglob('*')):
 rel=str(p.relative_to(H))
 if rel in ('MANIFEST01.json','FREEZE01.out','FREEZE01.err'):continue
 s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(p),links=s.st_nlink);groups.setdefault((s.st_dev,s.st_ino),[]).append(rel)
 elif stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 else:raise AssertionError('unexpected type')
 rows.append(r)
(H/'MANIFEST01.json').write_text(json.dumps({'manifest_self_excluded':True,'excluded_execution_streams':['FREEZE01.out','FREEZE01.err'],'members':rows,'literal_retained_hardlink_groups':[v for v in groups.values() if len(v)>1]},indent=2)+'\n')
print(json.dumps({'status':machine['status'],'manifest_sha256':sha(H/'MANIFEST01.json'),'machine_sha256':sha(H/'MACHINE01.json'),'report_sha256':sha(H/'REPORT01.md'),'members':len(rows)}))
