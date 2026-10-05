# Serialized-storage preclaim physical-reader size estimate

Read-only metadata estimate for actual CAP6b07c0f841e7d38102814aabb335751fd71fb7f7 and external Parent `genuine-financial-wrapper-continue100-serialized-storage-root-launch-20261005-01`. Accepted preclaim remains a3a22e972c182251f23d1f8d1261380973b34a7cc689cf6902511adb8d9a7c6e. No numerical arrays/bodies were read or decoded; opaque state.pt sizes were obtained by stat only. No numerical imports, admission/Owner/Run, network or live writes occurred. Only this report is written.

## Current known denominator

Reader.read caches by canonical absolute path, not SHA256; identical bytes at different paths count separately. Reader.finish physically rereads every cached path once. Its subsequent signature loop adds no body bytes. Thus fixed8MiB budget accounting is twice the sum of unique read-path extents, assuming unchanged regular files and successful complete reads. This is Reader accounting, not total process I/O: verify_claim and ordinary imported-module reads outside Reader are not charged by Reader.total.

The stat-based route inventory has257 known unique paths, totaling4,189,824bytes once,8,379,648bytes including all final physical rereads. Fixed cap8,388,608 leaves8,960physical bytes /4,480unique-body bytes. This is58,184physical bytes above the supplied old8,321,464 total, before final-release additions.

Inventory includes all36 registered input paths (including both opaque state extents), selected registration,195-body current installed map with path deduplication, current draft request substituting for future final request, caller and all8 helper paths, existing cumulative/source-runtime proofs,7 fixed reuse anchors, the4 actual original external proof/machine/report bodies read by reuse, completed100 recovery proof and its referenced review. Repeated references and the two trusted-bundle calls do not add duplicate cache reads. The full_recovery proof and final_review are presently null and therefore not counted. No historical raw stores were rescanned.

Current request is123,060bytes. It, gate336,445bytes, proof_reuse_contract3026bytes, cumulative4476bytes and source/runtime proof7760bytes are already compact sorted JSON with trailing newline: reserialization provides zero saving. PROTOCOL_PINS could save only9bytes/18physical bytes but is accepted hash-bound; no helper/source change is recommended while the final compact bodies fit.

## Precise remaining-release formula

Use compact sorted JSON with the existing trailing newline for NEW final files. The exact seven-field final review schema, current identity/source/caller hash and three proof hashes occupies681bytes. This is a size calculation using fixed-width placeholder hashes in memory, not a manufactured review artifact.

Let:

- R = actual compact FULL_CURRENT_RECOVERY_PROOF01.json body size.
- Lr = UTF-8 byte length of its final absolute reference path.
- Lv = UTF-8 byte length of final FINAL_PARENT_REVIEW01.json reference path.

For ordinary ASCII paths, each compact path/sha256 reference occupies87+path_length bytes. Replacing the two null values costs166+Lr+Lv bytes; replacing DRAFT_NOT_RELEASED with RELEASED_ONE_USE_FINANCIAL_PARENT costs15bytes. If all other request values remain equal:

```
final_request_size = 123060 + 181 + Lr + Lv
final_Reader_total = 8379648 + 2 * (R + 862 + Lr + Lv)
fits8MiB iff R <= 3618 - Lr - Lv
```

If both proof paths are in the current binding-review directory, the example lengths would be213 and205; then R must be <=3200bytes. These lengths are illustrative only because Root has not supplied the complete final owning-review directory. Any changed source/runtime/cumulative body, request field, helper or extra Reader reference must be added by its actual size delta. Do not silently reuse this estimate after changing the denominator.

A compact current recovery proof can refer to detailed independently reviewed checks by exact pins; accepted preclaim._parent_release hashes the proof body but does not recursively read every linked diagnostic. Required fields/evidence cannot be dropped merely to fit. Preserve old accepted proof bytes and caller unchanged. Actual final proof/review sizes remain unresolved; current evidence does not establish a completed preflight or guarantee the future total fits.

## Exact filename guard

Actual unchanged parent01.py:131 requires the final contract reference and actual file to be `parent/REQUEST_FINAL01.json`. A proposed `REQUEST_RELEASED01.json` filename would fail this exact guard even with identical JSON. Use REQUEST_FINAL01.json for the concrete release (a separately named preparation draft is permissible). Its raw hash, final review contract hash and reviewed request must match. No caller edit is needed.

Root can avoid a preventable size refusal by evaluating the formula with actual final compact proof/review/request bytes before final release. No cap, predicate, source, ancestry, budget, runtime or RAM change is needed on the evidence currently available.
