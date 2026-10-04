from pathlib import Path
import hashlib,json,os,stat
D=Path(__file__).resolve().parent;B=D.parent;I=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';H=lambda b:hashlib.sha256(b).hexdigest()
def put(n,o):(D/n).write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
assert len(json.loads((D/'CHECKS01.json').read_bytes()))==158;assert all((D/n).read_bytes()==b'' for n in ['CHECK01.stderr','WITNESS01.stderr'])
report='''# Independent installed one-use remote entry03 review

Decision: WITHHELD_ACTUAL_DRAFT_BODY_NOT_AUTHENTICATED_BY_CALLER. No actual invocation is released. Root03 remains a fresh, unspent forensic namespace at the recorded observation; no accepted entry machine is issued.

## P1 — caller trusts helper pins from an unauthenticated actual installation draft

Location: heartbeat-root-checkpoint10-2026-10-04/root_operational_remote03.py:12–13, with declarations at lines9–10. Exact caller91b1bc524b614fe6b84cfc1df74d887e94c267b91509b679b563e21f304b83c7 compares the review's installation_draft_sha256 field to the frozen literal4ac664..., then separately parses actual ROOT_INSTALLATION_DRAFT01.json without hashing those actual bytes against that pin. Its helper loop trusts this unpinned document. Likewise the review's remote_helper_sha256 field is compared to a literal but not directly joined to actual helper bytes except through that mutable draft. A changed helper paired with an updated draft pin can pass the installation loop while the approved draft and helper hashes have both ceased to match.

WITNESS01 executes only the exact extracted draft-load and helper-loop AST on an owned copy. The literal installed copy passes. Appending a harmless opaque comment to the owned helper while retaining the old draft correctly refuses. Updating that owned draft's helper hash then passes the same exact code despite both actual draft and helper hashes differing from the caller's approved constants. The modified helper is never imported or executed. No accepted review, actual remote receipt, financial proof, complete caller, main, entry or launch is fabricated. All original live files remain unchanged.

Required correction: read the actual draft once under bounded regular-file/type/path/currentness checks, authenticate those exact bytes against both the reviewed hash and fixed expected pin before JSON parsing, and check its exact expected schema/scope. Authenticate the actual source helper and complete installed closure against those authenticated pins, retaining a finite final currentness check at the launch boundary. Preserve the original failed caller and this witness; a separately named successor caller and fresh review are needed. A metadata flag saying that the draft was reviewed does not repair the missing byte join.

## Independently observed current preconditions

All158 positive installation checks passed despite the blocking caller defect. Actual ROOT_INSTALLATION_DRAFT01 is4ac66420883fe2605db005152c4492e0597aaab1593ebc9976d1857b0ff6a96d; SELECTED_BODIES01 isd2f64f4a7175ab13de9f40bcb7c700dc615197c61e65c39456233a21617bb23b. All six installed helper/selection entries have exact declared bytes/hashes, regular type, single link and canonical path. Helperada3, watchbdea and three original utilities match. No flat helper is installed or authorized.

Read-only local Git HEAD is4d0dbef40c978788ec9ddd9a5e4f4c2d18c52714. Its actual ls-tree records exactly the fifteen selected regular blobs. Each committed Git OID equals the independently computed OID from current Main bytes, and each SHA256/extent equals its selection pin. Total507946 bytes, fifteen distinct blob OIDs, expected prospective operations55. This is an expected denominator, not an observed retrieval count.

The complete REMOTE_CONFIRMATION46_COMPLETE01 record joins that Main commit to its recorded remote HEAD with commit/push/ls-remote exits0 and actual final chunk47f374. The earlier incomplete working record is copied and its hash matches the complete record's preserved-incomplete hash. No fresh network confirmation was performed in this review; the current review authenticates the Root-provided completed receipt and local committed objects, not a new external retrieval.

The exact accepted source review bd33dac0/MANIFEST7b2a3246 and genuine different-author watcher acceptance aed1248d/MANIFEST7a94ef04 were byte/type/mode authenticated across their38 and70 declared members. The watch is used only as the peer-accepted pinned metadata dependency. Its author does not self-review it here.

Actual intent, spawn, exit, receiver Git directory, selected directory, both flat directories, success/failure receipts, stdout/stderr, and restore01.py were absent at observation. No exact matching installed receiver, flat helper or caller argv appeared in the bounded process readback. The actual installed root passed its complete sampled whole-tree census and10GiB disk floor; BASELINE01 retains the observed values. These are finite observations, not future guarantees. No process environment or credential store was read.

Old Root02 remains permanently failed with FAILED7491cc3, original init observed exit null and separately reaped0, and no remote-success receipt. Historical path/component and discarded earlier retry details remain unknown. Current installation draft and helper pins were rechecked unchanged at the end of the source checks. The review made no live Main/CAP/Parent/gate/caller edits, network calls, numerical imports, checkpoint decode, ResearchRun/Owner construction or claim/ledger writes.

## Scope limits

This review withholds the one-use entry; it does not reverse the earlier bounded remote source acceptance. The original outer process supervision mechanics are retained, not newly certified for arbitrary timeout/crash/hostile operating-system behavior. Actual external15-body retrieval, its genuine acceptance, the separate corrected flat caller/review, full flat recovery, old385 and failed171 composition, final source-policy proof, installed runtime packages, final Parent/caller/gate supplement and numerical release remain pending. Resource observation is sampled, not a kernel quota, immutable snapshot or empirical capacity test. Financial timing, return/cashflow conventions, fees/funding, exposure reuse and scientific outcomes were not tested. The demonstrated missing actual-body hash join is sufficient to decide this exact caller without higher-effort speculation.
'''
(D/'REPORT01.md').write_text(report)
put('MACHINE01.json',{'schema_version':1,'decision':'WITHHELD_ACTUAL_DRAFT_BODY_NOT_AUTHENTICATED_BY_CALLER','owned_root':str(I),'commit':'4d0dbef40c978788ec9ddd9a5e4f4c2d18c52714','root_outer_caller_sha256':'91b1bc524b614fe6b84cfc1df74d887e94c267b91509b679b563e21f304b83c7','selection_sha256':'d2f64f4a7175ab13de9f40bcb7c700dc615197c61e65c39456233a21617bb23b','installation_draft_sha256':'4ac66420883fe2605db005152c4492e0597aaab1593ebc9976d1857b0ff6a96d','remote_helper_sha256':'ada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf','expected_operations':55,'flat_execution_released':False,'numerical_authority':False,'remote_execution_released':False,'current_precondition_checks':158,'actual_entry_started':False,'actual_remote_receipt':None,'actual_flat_receipt':None,'finding':{'priority':'P1','caller_line':12,'reason':'Actual draft bytes are never hashed against approved installation_draft_sha256 before trusting mutable helper pin map.'},'witness_sha256':H((D/'WITNESS01.json').read_bytes()),'report_sha256':H((D/'REPORT01.md').read_bytes()),'baseline_sha256':H((D/'BASELINE01.json').read_bytes()),'complete_confirmation_sha256':H((D/'REMOTE_CONFIRMATION46_COMPLETE01.json').read_bytes())})
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
print(json.dumps({n:H((D/n).read_bytes()) for n in ['MANIFEST01.json','MACHINE01.json','REPORT01.md','WITNESS01.json']}));print(json.dumps({'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'bytes':sum(r.get('bytes',0) for r in rows)}))
