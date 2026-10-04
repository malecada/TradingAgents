import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-storage-watch-concurrent-publication-correction02-2026-10-04';P=H.parent/'financial-wrapper-storage-watch-concurrent-publication-review01-2026-10-04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A/'MANIFEST01.json')=='7010c22de559e838a7815260caf612f3ebcb9fad3a2bfa3a39509c63b5ce413b'
assert sha(P/'MANIFEST01.json')=='da3279ce476d772db5b5f1950cdd529bb673e2074b03e2c0a716b4dc0e569300'
auth=json.loads((H/'INDEPENDENT01.json').read_text());compat=json.loads((H/'RAW_CONTROLS01.json').read_text());native=json.loads((H/'NATIVE_CONTROLS01.json').read_text());extra=json.loads((H/'ADDITIONAL_CONTROLS01.json').read_text());bound=json.loads((H/'DIAGNOSTIC_BOUNDARY01.json').read_text())
assert auth['checks']==1557 and compat['checks']==1072 and len(native)==7 and extra['cases']==27 and len(bound)==3
assert all(r['original_fatal_selected'] is False for r in bound)
(H/'HARNESS_CORRECTION01.json').write_text(json.dumps({'retained_original':'INDEPENDENT01.json','issue':'cleanup-descriptor-overrides row stored a mutable hooks list; later full-watch annotation controls appended three setattr entries before final serialization. The immediate assertion required no hooks in direct cleanup and passed; final list no longer represents that earlier instant.','additive_correction':'ADDITIONAL_CONTROLS01.json independently repeats direct cleanup with an immutable snapshot copy; hooks_snapshot=[] and all originals retained. Full Watch does invoke diagnostic setattr hooks, but that separate control preserves the original fatal.','original_bytes_preserved':True},indent=2)+'\n')
report='''# Independent nested cleanup successor review

Decision: **WITHHELD_FOR_INHERITED_FATAL_DIAGNOSTIC** for source `21e21dddc5b5008c3dc016839fc5b05c60dfbd345d224e91b8a9c3fb551c62cf`. The exact correction02 `_cleanup` change fixes review01's evidence-loss finding. A newly tested inherited diagnostic boundary still violates the requested original-first-fatal contract. The distinction is explicit: correction02 did not introduce this second defect.

## Actionable finding

**P2 — Select the original fatal before reading overridable diagnostics (`workflow_storage.py:131`; the same pattern is at line108).** A KeyboardInterrupt subclass whose `__cause__` property raises SystemExit can replace the original interrupt in `StorageWatch.check()`. The original body raises during a real owned file stat; the actual root descriptor closes exactly once. `_scan` preserves that interrupt, but `_check` then executes `getattr(error.__cause__ or error.__context__, 'observation', {})` outside any original-fatal protection. The diagnostic property runs and SystemExit becomes the selected outward exception. The original interrupt remains in its exception context; this is wrong fatal precedence, not loss of all original evidence. The same witness reproduces on actual original bf52, withheld75cdf and successor21e21, proving it is inherited. `DIAGNOSTIC_BOUNDARY01.json` includes each exact traceback. Preserve the originally selected fatal through both diagnostic wrappers; use safe builtin exception descriptors or protect diagnostic access before applying the established fatal-selection rule. Do not solve this by suppressing genuine terminal cleanup errors or retrying an uncertain descriptor.

## Correction02 result

The whole author02 typed manifest `7010c22d…`, all declared source01 and review01 members/modes/bytes/links, and the full predecessor scope were independently authenticated. Exactly one literal substitution reconstructs75cdf from21e21; AST equality after removing `_cleanup` establishes that every other definition is unchanged. Earlier withheld artifacts remain immutable, including review01's explicitly excluded freeze streams.

Twenty-four independent real three-level traversal controls cover twelve KeyboardInterrupt/MemoryError/SystemExit primary and RuntimeError/MemoryError/KeyboardInterrupt/SystemExit secondary combinations on both predecessor and successor. Each traversal opens and closes three distinct real owned directory descriptors once. Predecessor retains only the last close error; successor retains all three original secondary objects and the exact original fatal. Cause/context/stored-error graph traversal uses builtin descriptors independently of subject hooks. Direct cleanup controls also cover no primary, ordinary primary, successful cleanup, preexisting tuple/non-tuple/hostile tuple-subclass attachment, overridden public dictionary and cleanup-error descriptors, getattr/setattr/str/repr/add_note hooks and all original error identities. The direct cleanup override control invokes no hooks. Full-Watch hostile setattr controls preserve the original fatal and both real close errors. The separate inherited cause-property counterexample above is distinct.

`INDEPENDENT01` completed1,557 authentication/control assertions; the compatibility replay completed1,072 assertions. These counts overlap in evidence authentication and are not a count of unique empirical claims. Compatibility execution rechecked the original194 current source bodies, full original-source inverse/domain, genuine lifecycle publisher RED-to-GREEN interleaving, pending accounting, limits, sparse files, unsafe types, disappearance/replacement, late callbacks, bounded churn, root identity, aggregate deadline and nested cleanup. Seven genuine resource AST-subset controls passed peak updates, native failed-state evidence, disk floor, outer deadline, diagnostic-fatal handling and independent cleanup progression. Twenty-seven additional control rows passed, including the full twenty primary/no-primary/secondary combinations with three actual closes each. No owned descriptor leak was found. The author's76 rows are separately authenticated historical evidence, not counted as independently rerun76 controls.

## Sampling and scope remain limited

The inherited same-tick late-name boundary remains unchanged by AST equality: review01 observed6/12 returns of logical2 when actual final tree held5, with exactly unchanged directory fingerprints. This is an explicitly documented finite sampled-metadata boundary, not a new demand for atomicity and not an additional blocker. No kernel quota, immutable bytes, writer exclusion, continuous full-tree currentness, blocked-syscall preemption or whole-capacity guarantee follows. Writer bounds/reservations and external/native controls still matter.

Source-provenance compatibility remains blocked: all194 installed source hashes enter original fixture provenance, and prior/reference equality retains them. Accepting this source could not authorize joining an old checkpoint to a new corrected reference, resetting spent attempts, amending the budget or launching a new identity. Those decisions and complete failed-outcome recovery are separately Root-owned.

The independent01 direct-hook output row accidentally held a mutable list later changed by a different full-Watch test. `HARNESS_CORRECTION01.json` discloses the reporting alias; the original bytes are retained. `ADDITIONAL_CONTROLS01.json` independently reruns the direct-hook control using a copied snapshot, confirming zero hooks. No failed source control or original evidence was erased. The three inherited diagnostic counterexamples are expected failures of the source contract, not passing source-acceptance tests.

All execution was pinned Main Python3.13.13 with `-B`, stdlib and tiny owned opaque files. No arrays, labels, checkpoint deserialization, financial experiment, registration/ledger edit, live source integration, Owner/Run/admission/native/helper entry, network or operational launch occurred. Financial validity, training completion, numerical agreement, full runtime/package/native behavior, full-population capacity, arbitrary asynchronous/allocation failures and actual failed-outcome external recoverability were not tested. The specific inherited diagnostic question is already resolved by a small counterexample; higher effort is not needed to reproduce it.
'''
(H/'REPORT01.md').write_text(report)
machine={'status':'WITHHELD_FOR_INHERITED_FATAL_DIAGNOSTIC','source_sha256':sha(A/'workflow_storage.py'),'author_manifest_sha256':sha(A/'MANIFEST01.json'),'prior_review_manifest_sha256':sha(P/'MANIFEST01.json'),'cleanup02_exact_fix_accepted':True,'source_overall_accepted':False,'findings':[{'priority':'P2','file':str(A/'workflow_storage.py'),'line':131,'also_line':108,'inherited':True,'issue':'Overridable cause diagnostic replaces first actual fatal.','witness':'DIAGNOSTIC_BOUNDARY01.json'}],'authentication_and_control_assertions':[1557,1072],'counts_not_unique_experiments':True,'resource_subset_rows':7,'additional_rows':27,'source194_reauthenticated':True,'native_or_financial_execution':False,'sampling_and_provenance_limitations_unchanged':True,'report_sha256':sha(H/'REPORT01.md')}
(H/'MACHINE01.json').write_text(json.dumps(machine,indent=2)+'\n')
rows=[];groups={}
for p in sorted(H.rglob('*')):
 rpath=str(p.relative_to(H))
 if rpath in ('MANIFEST01.json','FREEZE01.out','FREEZE01.err'):continue
 s=p.lstat();r={'path':rpath,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(p),links=s.st_nlink);groups.setdefault((s.st_dev,s.st_ino),[]).append(rpath)
 elif stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 else:raise AssertionError('unexpected file kind')
 rows.append(r)
(H/'MANIFEST01.json').write_text(json.dumps({'manifest_self_excluded':True,'excluded_execution_streams':['FREEZE01.out','FREEZE01.err'],'members':rows,'literal_retained_hardlink_groups':[g for g in groups.values() if len(g)>1]},indent=2)+'\n')
print(json.dumps({'status':machine['status'],'manifest_sha256':sha(H/'MANIFEST01.json'),'machine_sha256':sha(H/'MACHINE01.json'),'report_sha256':sha(H/'REPORT01.md'),'members':len(rows)}))
