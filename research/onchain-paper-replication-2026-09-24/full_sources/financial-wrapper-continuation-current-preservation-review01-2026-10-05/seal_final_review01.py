"""Seal the consolidated review after its actual public-preflight readback.

Only the review directory is writable. No launch or lifecycle invocation.
"""
from pathlib import Path
import sys, json
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import R
def ref(name):
 p=H/name
 return {'path':str(p),'sha256':R.digest(R.read(H,name))}
preflight=json.loads(R.read(H,'PUBLIC_PREFLIGHT_READBACK01.json'))
release=json.loads(R.read(H,'FINAL_PARENT_RELEASE_READBACK01.json'))
recovery=json.loads(R.read(H,'CURRENT_RECOVERY_MACHINE01.json'))
report='''# Consolidated current preservation and Parent release review

The exact current source-bound draft byte recovery and final one-use Parent release are accepted within the recorded bounds. The actual recovered archive contains159 regular bodies and175 typed entries, including all27 new payloads842,160 bytes. The complete current CAP composition is823 regular/1,049 typed with416 logical Git objects. Accepted prior818 body hashes and407-object recovery are reused explicitly; no duplicate old-body scan or new recovery claim is attributed to that reuse. Source664e,359 source pins,360 tracked bodies and29 registered roles remain fixed.

Original bind02.py:50 acquired a descriptor before fallible digest allocation and its cleanup region. The real MemoryError witness leaked that descriptor; it was observed and closed by the reviewer. Corrected bind03 allocates first. The literal/AST inverse, original failure and narrow successful regression remain retained. An earlier reviewer cleanup hypothesis was incorrect; its failed harness and corrected control are also retained as such.

The exact locally pinned transport then completed one remote receiver and one flat restoration. Actual receipts, selected Git bodies, canonical archive bytes, all returned bodies and current composition were independently joined. Actual Root and child exits are zero; the original inner Parent exit remains null. Recorded process absence is scoped to actual recorded identities, not universal process history. New transport source was locally contract-bound and is not falsely claimed externally recovered in the three-body payload.

Final Parent review independently proves that the released request differs from the recovered draft only in released status and the genuine full-current recovery proof; the final-review reference is additive authority. The actual unchanged validate_release functions accepted the genuine release; missing-review and draft-status controls refused. Caller, helper, source, registered-input, cumulative and recovery proof joins are fixed. The family remains one COMPLETE and three FAILED, four spent claims, highest allowance20 and16 remaining; no refund, transfer or budget amendment follows.

The actual Root public preflight FAILED and numerical entry is WITHHELD. The second invocation reaches preclaim01.py:318 in _historical, where exact historical alias equality refuses. Its reader-byte total is unknown; no complete8MiB pass is claimed. The source/recovery and exact validate_release checks do not discharge this additional integration predicate. The original first invocation failed on the canonical request filename before PRECLAIM.validate_preclaim; its failure, unchanged correct request bytes and byte-identical filename correction remain preserved. Both actual failures and the second raw traceback are retained. No numerical identity was consumed, and its actual claim/run/Parent attempt namespaces remain absent at readback. A separately reviewed exact alias/descriptor correction is required before another public preflight; no predicate relaxation is authorized here. This reviewer never ran public preflight, Owner, ResearchRun, a numerical import, restoration or network operation.

Claims not tested: economic performance, fees/funding, timing leakage, new scientific outcomes, universal process history, continuous writer exclusion, installed runtime body recovery, POSIX reconstruction and whole capacity. Final resource eligibility and any actual numerical entry remain Root responsibilities. Frozen source-phase and current-recovery artifacts retain their original historical qualifications; this final seal adds no retroactive outcome to them.
'''
with (H/'REPORT01.md').open('x') as f:f.write(report)
machine={'schema_version':1,'decision':'ACCEPTED_CURRENT_RECOVERY_AND_VALIDATE_RELEASE_PUBLIC_PREFLIGHT_FAILED','reviewer':'/root/storage_watch_review','source':release['source'],'identity':release['identity'],'source_snapshot':ref('SOURCE_PHASE_MANIFEST01.json'),'source_release':ref('SOURCE_PRESERVATION_RELEASE01.json'),'current_recovery_proof':ref('CURRENT_FULL_RECOVERY_PROOF01.json'),'current_recovery_machine':ref('CURRENT_RECOVERY_MACHINE01.json'),'final_parent_release':ref('FINAL_PARENT_RELEASE01.json'),'final_parent_readback':ref('FINAL_PARENT_RELEASE_READBACK01.json'),'public_preflight_readback':ref('PUBLIC_PREFLIGHT_READBACK01.json'),'public_preflight_status':preflight['status'],'numerical_entry_status':'WITHHELD','public_preflight_reader_bytes':None,'report':ref('REPORT01.md'),'original_helper_withheld':'9161fc3812687708f4365b3137b05f9d2b65bb8a8b9a314cdc966cf64b99ccec','corrected_helper':'53f4a5fc154311e7dcbbb77dcdd37954a6f07f9ab83e5ad7ecc543932b98375b','scope':recovery['scope'],'old818_hashes_reused_not_reread':True,'numerical_entry_executed_by_reviewer':False,'new_financial_outcome_claimed':False,'whole_capacity':False,'continuous_writer_exclusion':False,'installed_runtime_body_recovery':False,'POSIX_reconstruction':False}
R.put(H/'MACHINE01.json',machine)
m=R.scan(H)
m['self_excluded']='MANIFEST01.json'
m['scope']='Complete consolidated review; original source snapshot and subsequent exact source, entry, actual recovery and Parent-release evidence retained.'
R.put(H/'MANIFEST01.json',m)
print(json.dumps({'machine':ref('MACHINE01.json'),'report':ref('REPORT01.md'),'manifest':ref('MANIFEST01.json'),'members':len(m['members'])}))
