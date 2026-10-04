from pathlib import Path
import json,hashlib,os,stat,subprocess
D=Path(__file__).resolve().parent;B=D.parent;I=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';C=B/'heartbeat-root-checkpoint10-2026-10-04';MAIN=B.parents[2];H=lambda b:hashlib.sha256(b).hexdigest()
def put(n,o):(D/n).write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
assert len(json.loads((D/'CHECKS01.json').read_bytes()))==158 and len(json.loads((D/'PREDICATES01.json').read_bytes()))==58
assert all((D/n).read_bytes()==b'' for n in ['CHECK01.stderr','PREDICATE01.stderr'])
assert H((C/'root_operational_remote04.py').read_bytes())=='169c638054cacd242335be40eed2507d49172885a9bdfd106b6f07fe31650e28' and (C/'root_operational_remote04.py').read_bytes()==(D/'root_operational_remote04.py').read_bytes()
assert H((I/'ROOT_INSTALLATION_DRAFT01.json').read_bytes())=='4ac66420883fe2605db005152c4492e0597aaab1593ebc9976d1857b0ff6a96d';assert H((I/'SELECTED_BODIES01.json').read_bytes())=='d2f64f4a7175ab13de9f40bcb7c700dc615197c61e65c39456233a21617bb23b'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=MAIN,text=True,timeout=15).strip()=='4d0dbef40c978788ec9ddd9a5e4f4c2d18c52714'
assert all(not os.path.lexists(I/n) for n in ['ROOT_REMOTE03_INTENT01.json','ROOT_REMOTE03_SPAWN01.json','ROOT_REMOTE03_EXIT01.json','ROOT_REMOTE03.stdout','ROOT_REMOTE03.stderr','REMOTE_RECOVERY01.json','FAILED01.json','selected','fresh-operational-source-policy02.git','restore01.py','flat-operational-delta01','flat-failed-remote02-01'])
report='''# Independent exact one-use forensic remote entry04 review

Decision: ACCEPTED_EXACT_ONE_USE_FORENSIC_REMOTE_ENTRY_ONLY. This grants Root one invocation of exact outer caller169c638054cacd242335be40eed2507d49172885a9bdfd106b6f07fe31650e28 for the still-unspent installed Root03 directory and exact selection/Main commit listed in MACHINE01. It does not release any flat helper, financial/numerical claim or production work. The caller itself requires this machine's exact externally supplied CLI SHA256 and all bound fields before launch. The reviewer did not invoke the caller.

## Correction and adversarial evidence

The two literal edits invert exactly to preserved caller91b1bc524b614fe6b84cfc1df74d887e94c267b91509b679b563e21f304b83c7. One edit redirects the review path to this entry04 directory. The other hashes ACTUAL installation draft bytes against the reviewed draft pin before JSON parsing, and directly hashes ACTUAL recover01.py against the reviewed helper pin. All other caller mechanics and AST are preserved by the complete inverse. No owned-root definition, selection, Main commit, resource cap or operation count changes.

The original entry03 finding is resolved for this bounded caller: both versions are tested using exact extracted installation-predicate AST on seven distinct owned copies. Original unchanged input passes both. Helper-only drift refuses both. Paired helper+draft drift, whitespace-only draft drift, a foreign draft field, paired selection+draft drift and omitted helper-pin drift pass the old unauthenticated loop but refuse the corrected predicate. For every changed-draft case, corrected refusal occurs before json.loads. The only supplied predicate context contains the two actual expected hashes; no accepted-review shape, remote receipt, Run/Owner, complete entry or outcome is fabricated. None of the modified helper bodies is imported or executed. All predecessor entry03 evidence34 members authenticates unchanged, including its original withheld machine and concrete counterexample.

PREDICATES01 records58 checks covering those predicates, complete literal/AST inverse and retained prior evidence. CHECKS01 separately reruns158 current installed-precondition checks against actual originals; total216 checks. No prior positive review is automatically promoted to entry authority.

## Exact installed and committed joins

Actual ROOT_INSTALLATION_DRAFT01 remains4ac66420883fe2605db005152c4492e0597aaab1593ebc9976d1857b0ff6a96d, SELECTED_BODIES01 remainsd2f64f4a7175ab13de9f40bcb7c700dc615197c61e65c39456233a21617bb23b, and installed remote helper remainsada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf. All six installed selection/helper entries match exact declared type, canonical path, single-link, length and hash. Watchbdeaca and all three unchanged utilities are installed. No restore01.py is installed.

Actual local Main HEAD is4d0dbef40c978788ec9ddd9a5e4f4c2d18c52714. Read-only local ls-tree contains all15 selected regular blobs, and each actual committed OID equals a Git blob hash independently computed from the current literal Main bytes. All SHA256s/lengths match the selection. The selected bodies total507946 bytes and15 distinct Git OIDs, giving prospective expected operations10+15+2*15=55. This does not claim an observed55-operation outcome.

The complete REMOTE_CONFIRMATION46_COMPLETE01 receipt records that same commit as actual remote HEAD with commit/push/ls-remote exits0 and final returned chunk47f374. Its preserved incomplete receipt hash matches the separate literal prior working record. Both are copied. This review makes no new network call; it authenticates the completed Root receipt and actual local Git objects. A future genuine remote body receipt remains necessary before claiming retrieval.

Accepted remote source review bd33dac0/MANIFEST7b2a3246 and genuine different-author watcher acceptance aed1248d/MANIFEST7a94ef04 are authenticated across all38 and70 current declared members. Watch04 is only a pinned, peer-accepted dependency; this reviewer authored it and does not self-review it here. Its original sampled policy remains64MiB logical/96MiB allocated/4MiB file/32768 members/depth32/10GiB floor/three attempts/five seconds/8192 samples. The fixed two100ms waits remain an explicit operational timing deviation. Original Git/process and Root outer mechanics remain as previously scoped; this review is not new kernel or hostile-OS process certification.

## Freshness, bounds and retained failures

At the independent process observation no exact matching installed receiver, flat helper or current outer caller argv was present. Actual intent, spawn, exit, receiver Git namespace, selected directory, both flat destinations, success/failure receipts, stdout/stderr and flat helper were absent. Exact relevant paths and Main HEAD were checked again before this machine was emitted. Exclusive intent creation before launch remains the one-use guard; any attempted launch consumes that identity and its failures must be retained rather than replayed.

The current complete installed-tree sample reports9 members,59191 logical bytes,81920 allocated bytes and no extent changes, with16,544,522,240 free bytes. BASELINE01 retains the actual measured values and accepted dependency qualification. These are finite observations, not guaranteed future resource capacity. Caller-owned source/draft/selection hashes were rechecked at sealing. No live installation or original evidence was edited by the reviewer.

Old Root02 remains permanently FAILED/spent with FAILED7491cc3, original init observed exit null, separately reaped0, and no remote-success receipt. Root exit1 and historical changed directory/path/component unknowns retain their original meaning. The entry03 caller and withheld review remain intact. No failed identity is reopened and no financial budget is refunded or changed.

## Strict release boundary

Only exact caller169c with this exact reviewed machine SHA may launch the existing installed remote helper once under Main4d0 and selectiond2f64 in Root03. No flat execution is released, even if a separate flat source review later accepts its code. Actual remote exit/complete receipt and different-author acceptance must precede any separately reviewed installed flat entry. Old385 Git, new nine opaque Git objects, failed171 bytes, complete source-policy recovery proof, final Parent/caller/gate supplement, runtime-package recovery, whole empirical capacity and numerical admission remain separate requirements.

No caller main/entry, network transfer, receiver/Git child, financial experiment, numerical import, checkpoint decode, genuine Run/Owner or ledger/registration/gate mutation occurred in this review. Only bounded local Git readback commands were executed. No credentials or process environments were read. This acceptance does not establish continuous atomicity, immutability, kernel aggregate quota, hard real-time scheduling, external recovered bytes, economic timing/PnL/fees/funding/exposure validity or scientific outcomes. No unresolved source-binding issue remains in the demonstrated paired-drift correction; actual execution and recovery evidence are still absent.
'''
(D/'REPORT01.md').write_text(report)
put('MACHINE01.json',{'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_FORENSIC_REMOTE_ENTRY_ONLY','owned_root':str(I),'commit':'4d0dbef40c978788ec9ddd9a5e4f4c2d18c52714','root_outer_caller_sha256':'169c638054cacd242335be40eed2507d49172885a9bdfd106b6f07fe31650e28','selection_sha256':'d2f64f4a7175ab13de9f40bcb7c700dc615197c61e65c39456233a21617bb23b','installation_draft_sha256':'4ac66420883fe2605db005152c4492e0597aaab1593ebc9976d1857b0ff6a96d','remote_helper_sha256':'ada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf','expected_operations':55,'flat_execution_released':False,'numerical_authority':False,'permitted_invocations':1,'current_precondition_checks':158,'predicate_and_preservation_checks':58,'prior_entry03_preserved':True,'original_paired_draft_helper_witness_now_refused':True,'exact_two_edit_inverse':True,'actual_entry_started':False,'actual_remote_receipt':None,'actual_flat_receipt':None,'source_acceptance_sha256':'bd33dac061d5a7dba3f7f9e1dd38f194770f66f6f37c487ba76d2e1eeefd5b02','different_author_watch_acceptance_sha256':'aed1248d003fbe19ccbd5f0f57b6801e6cf08713bb01d6d9fa56a145e172bb57','report_sha256':H((D/'REPORT01.md').read_bytes()),'baseline_sha256':H((D/'BASELINE01.json').read_bytes()),'complete_confirmation_sha256':H((D/'REMOTE_CONFIRMATION46_COMPLETE01.json').read_bytes()),'predicate_controls_sha256':H((D/'PREDICATES01.json').read_bytes()),'scope':'One exact remote-only Root invocation; sampled current preconditions. No actual recovery, flat or numerical authority.'})
rows=[]
for base,dirs,files in os.walk(D,followlinks=False):
 for n in sorted(dirs+files):
  p=Path(base)/n
  if p==D/'MANIFEST01.json':continue
  s=p.lstat();r={'path':str(p.relative_to(D)),'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=H(p.read_bytes()),nlink=s.st_nlink)
  elif stat.S_ISDIR(s.st_mode):r['kind']='directory'
  else:raise AssertionError(p)
  rows.append(r)
put('MANIFEST01.json',{'schema_version':1,'root_mode':stat.S_IMODE(D.stat().st_mode),'members':sorted(rows,key=lambda r:r['path'])})
print(json.dumps({n:H((D/n).read_bytes()) for n in ['MANIFEST01.json','MACHINE01.json','REPORT01.md','PREDICATES01.json']}));print(json.dumps({'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'bytes':sum(r.get('bytes',0) for r in rows)}))
