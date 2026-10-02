# Final independent review

Accepted for read-only local revalidation of a trusted, previously fully replayed v2 archived-stage proof. ASC1–3 are resolved in the inspected source and evidence. No further material blocker was identified in this bounded scope. Source, test assertions, retained logs and SHA-256 identities were inspected independently; no tests, network operations or empirical jobs were rerun. The initial review and predecessor snapshots remain preserved.

## Corrections and authority

ASC1 is closed by applying the original reader's minimum `(3 * max_chunks + 8) * META_LIMIT` from the validated archive policy in the shared join. ASC2 is closed by checking exact attempt membership before opening the source/reference handles and before each scientific join, including after the final lease. A failed or foreign attempt is refused before checkpoint traversal. ASC3 is closed by comparing regenerated canonical result bytes to the exact trusted completion bytes and using canonical comparisons for event-read completion and cross-proof replay summaries. Integer/float or boolean aliases can no longer pass solely through Python object equality in the reconstructed result.

The v2 result binds its stage-read intent and event-read intent/completion. The checker verifies those anchors, regenerates the event-read contract, joins its replay summary to the source archive completion, and checks policy, counts, checkpoint references and actual checkpoint trees. For MCM it also rejoins retained score tails/batches and the ordered score digest. The same helper is used by the initial full verifier. The original source, attempt and reference descriptors remain pinned through two local joins around the caller lease. Independently owned handles close once with fatal, primary-preserving cleanup.

The checker does not invoke the event visitor, create a new read claim or fetch remote chunks. Legacy v1 results are refused rather than silently upgraded. An expected hash must come from an independently trusted previous verification; hashing arbitrary supplied bytes does not establish that provenance. Caller-rehashed malformed-proof tests establish schema/policy consistency, not an ability to bypass an unchanged trusted SHA.

## Retained verification

- Original `check01.log`: **46 passed, 121.03 seconds**, before the review corrections.
- `review-red01.log`: **4 failed, 3 passed, 15 deselected, 8.18 seconds**. The failures reproduce the minimum allowance, exact count representation and two early-inventory gaps. Three cleanup injections already passed.
- Corrected `check02.log`: **57 passed, 340.17 seconds**: 22 local-check cases, 17 archived-stage cases, 14 finalizer cases and four actual-owner dictionary-route cases. This is a selected engineering population, not the full repository suite.

The local dictionary/MCM positives first create real synthetic archived evidence through full replay, then forbid transport get/put/mkdir and `_write` during checking and verify unchanged retained file bytes. Nine final-lease mutations cover intent, event-read proofs, checkpoint numeric content, score data, references, source metadata and invalid attempt membership. Other cases reject v1, unknown fields, invalid policy, altered replay summary and a rehashed integral-float count. Three close injections require fatal failure with no file-byte changes. These inject errors after a real close and demonstrate propagation; they do not demonstrate recovery of leaked descriptors or independently exercise every simultaneous failure combination.

## Limits

This result establishes current local content consistency with a trusted earlier remote observation. It does not establish current remote availability. No network transport is exercised; the actual-owner fixtures mock the OS guard, and their coverage is dictionary-only. The generic fixtures cover MCM separately. No stage-seal publication, scientific producer selection, whole-owner closure, post-owner-close authority or empirical admission follows. Outer stage membership and source/current-owner authority remain caller obligations.

The checker is read-only and writes no new failure ledger. Failed checks leave original proof evidence unchanged; an integrating owner must preserve its own failure disposition. Existing local checkpoint and score payloads are still required. No source eviction, transfer meter, whole-workflow RSS/physical quota, latency or bulk-throughput claim is made. Reads and leases are sampled rather than atomic. Timing, returns/cashflows, exposure reuse, fees and funding were not tested.

## Exact identities

| File | SHA-256 |
|---|---|
| `archived_stage.py` | `7fa3f48620ddf74a890643df28bf8efc92332c31f2f680fb89707d55475e24a8` |
| `test_archived_stage_check.py` | `7b520cea0510a48717b8691a10df753e22edc580b0d803a5ba0771b5940ac166` |
| `check01.log` | `7b89b1fb7eda65be1d0f075b12c68b155e6bee76082052053d4031f4d073af28` |
| `review-red01.log` | `0dd26d2a1fa1c7ac228d1f51e0d4066763d8615b1a0570789070d56a05a3324f` |
| `check02.log` | `534df7daaa8f2573f26d7678ae079f6380c1e8adca545120b82ecc1ef268b5e0` |

The preserved v1 predecessor and pre-correction v2 source/test snapshots were also inspected and hashed. They remain distinct historical evidence, without retroactive correction of their acceptance scope.
