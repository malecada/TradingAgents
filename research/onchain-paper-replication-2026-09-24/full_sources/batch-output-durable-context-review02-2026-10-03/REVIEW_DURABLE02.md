# Independent durable non-tail correction02 review

Disposition: **WITHHELD for DNT3**. Original DNT1/DNT2 are corrected within the source-only scope. No live authority, native run, transport or capacity is accepted.

The selected manifest is `04cb2bae36d3b3de6d8e2ef7adf89a8068c06f4fcee96e3400c99d1f8e23704d`; `archive_non_tail.py` is `d55a0caeb4b0ffbde5cbfcefda9852a6cde15ca9729ba6635313f21972caf89f`. All24 manifest bodies and12 dependency references were hash/length checked (the consumer reference appears twice; these are11 unique dependency paths). Author bytes remain untouched. Exact source copies, independent checks and raw logs are retained only in this reviewer directory.

## New finding

**DNT3 — full original job inherits the compact control limit only after namespace birth.** `archive_non_tail.py:187` calls `encode(self.execution)` and `encode(json.loads(self.job_raw))`. Changing module META from128KiB to8KiB therefore narrows the allowable complete job document, despite the report stating that original job documents remain governed by their own original contracts. Constructor lines150–166 preflight the policy, selection, small hash-bound configuration and complete intent, but never encode the full job. Lines167–174 then create the namespace and publish intent/receipt before `self.check()` discovers this deterministic bound failure.

`check_additional02.py` uses the actual constructor prefix up to, excluding, namespace birth. Complete matching synthetic metadata with40 distinct producer selections and registered headers yields an11,504-byte canonical job; policy/configuration/intent all fit. The prefix returns, while the exact extracted check statement raises `ValueError: non-tail control metadata cap`. No namespace, actual ResearchRun, native guard or Owner was created. This counterexample demonstrates the candidate's inconsistent pre-birth contract; it does **not** claim that this synthetic40-representation configuration is a fully admitted future scientific job.

Either explicitly preflight the same complete job bound before birth and document that selected restriction, or preserve the separately bounded original-job canonical equality without imposing the control-record encoder on it. Keep complete8KiB control publication; do not truncate ancestry, widen global authority metadata, or replace the real job with a partial projection. Recheck the exact actual future selected job extent before release.

## Corrections independently supported

The original independent reviewer script was copied byte-for-byte and rerun against preserved01 in this reviewer-owned tree. Both original fatal-masking and contradictory-population examples reproduced. Their output remains in `old_counterexamples01.log`; no original files or namespace were changed.

The12 exact-source correction tests were independently rerun using exact copied02 bodies. They passed. Source bootstrap `_source_body` is additionally AST-identical to the previously accepted consumer02 `_body`, apart from its name: descriptor-relative no-follow regular single-link source,1MiB stat ceiling, original-size-plus-one reads at most64KiB, growth/refile/parent/inode rejoins, and canonical actual owned_io cleanup. Real tiny FD tests preserve the original MemoryError while closing both owned descriptors once, reject uncertain clean-body close, growth, replacement, links and oversize source. These test files are synthetic; the tested reducer is actual canonical source, not a fake authority type.

The corrected selection function requires registered job/plan inputs, version2 producer plans, exact producer selection/operation/descriptor and job fields, only the permitted plan-only header fields, registered selected top-level input roles, sorted unique graph hashes, complete policy population, distinct registered headers and disjoint Context outputs before birth. Mismatched source/operation/selector/descriptor/input/header cases refuse before the extracted prefix can reach mkdir. Real ResearchRun/type/native checks remain code paths, not exercised positive authority.

Complete control encoding is8KiB and complete intent is encoded before mkdir without truncation. Exact boundary tests pass. Complete inventory records above that limit still refuse; maximum4096 members or128slots do not prove an inventory of those maxima fits. Authenticated paging, simultaneous capacity and actual finite policy intersection remain outstanding. Local reservation counters retain the existing proposal semantics and are not actual SSH/readback/control-command charges.

Inverse full-module byte reconstruction passes after restoring only Context.__init__, removing the two new helpers and restoring the declared META/headroom expressions. All other method ASTs match01; archive_dispatch and archive_transport match01 exactly. Original dispatch remains its unchanged byte prefix and transport its unchanged whole body. There is no alteration of matching/numerical bodies, event transport defaults or prior authorities.

## Unproved scope

Raw-f32 and graph-artifact typed binding still refuse; positive SSH dispatch still refuses. Original event/168-byte transport authority is not substituted. The three copied modules are not a complete installed200-source/149-package closure: genuine Root Git/source anchor, registered finite population/policy and outputs, runtime, current native guard, exact held/cold Owner/Target joins, durable recovery and disposition remain required. This review neither activates exhausted historical identities nor changes financial budgets.

No numerical module, array value, network, genuine claim, native job, upload, deletion, Main/CAP/STATE/Git mutation or source integration occurred. Full inventory/storage capacity, remote recovery, scalar/model/gradient/checkpoint equivalence and financial fits remain untested. The counterexample is source-only and preserves every original failure and frozen candidate.
