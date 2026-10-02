# Final independent review

Accepted for the bounded current-owner archived stage seal and local sealed-content check. AOSL1 and AOSL2 are resolved. No additional material blocker was identified in the inspected scope. Source, assertions, raw terminal logs and hashes were reviewed independently; no tests, transfers or empirical jobs were rerun. `REVIEW_INITIAL.md` and all retained failed/pre-correction evidence remain preserved.

**AOSL1 closed.** The actual owner metadata/inventory helpers `compact_owner.exact` and `entries` now use the shared primary-aware fatal release contract. Four targeted cases cover each helper with and without an in-flight body failure, requiring one close and fatal propagation; the failing-body cases retain a `ValueError` cause. These injections raise after performing a real close. They demonstrate exception handling and preservation, not recovery of leaked kernel descriptors.

**AOSL2 closed.** After `_publish` returns from its final owner callback, `_execute` now checks the original matching snapshot and original read-attempt handle, followed by callback-free owner/ledger/closing-stage/lock postconditions. Only successful cleanup permits in-memory stage acknowledgement. Additional authority and stage-integrity checks precede that acknowledgement. The regression renames the original matching directory and creates an equal-byte replacement during publication. It reproduced acceptance before the correction and now refuses, retaining the original tree, spent read claim and failed evidence without closing the stage successfully.

The revised sealed-check mutation test is armed on the second owner lease, so it now supports a final-callback refusal claim. Its original first-callback-only version remains historical evidence rather than evidence for that stronger boundary.

## Accepted contract

`seal` performs a fresh actual reserved full scientific read. An earlier caller-completed reader reservation cannot replace that replay. The seal joins exact writer/read operation identity, stage intent, completion references, deterministic read path/inode, trusted v2 proof and scientific result. Its distinct archived marker is bounded by the original intent-plus-seal metadata allowance. The stage remains in an explicit closing state during publication; descriptor cleanup completes before reference/contract/closed state is installed and `owner.active` is cleared. Failure preserves the marker when present, records failed alongside a completed read claim when necessary, poisons the owner and retains the reservation.

`check` pins the original sealed reference, contract and marker before live callbacks and uses the anchored local checker afterward. It remains usable for an already sealed dictionary while a later legitimate stage is active. It makes no remote read and does not rewrite historical successful claims. Check failure poisons owner/ledger and uses one fixed owner-ledger failure record, within the existing fixed control allowance. This is logical metadata accounting, not a filesystem quota.

## Verification and limitations

- `check01.log`: **1 failed, 4 passed, 247.68 seconds**. The actual seal close injection exposed the inherited reader cleanup gap.
- `review-red01.log`: **5 failed, 5 deselected, 53.50 seconds**. Four owner-reader cleanup variants and the equal-byte source namespace replacement reproduced the findings.
- Corrected `check02.log`: **14 passed, 501.05 seconds**: six seal cases, four focused owner-reader cleanup cases and four existing reserved owner-stage cases. This is a selected engineering population, not a full repository suite.

The six seal cases exercise actual publication/local checking, duplicate preservation, checking a dictionary with another stage active, a caller-completed read followed by a required fresh replay, marker-callback and close failures, second-lease sealed-marker corruption, and original matching namespace replacement (the callback/close test expands into two cases). Positive transport counting observes one new full read; subsequent sealed checking forbids transport get/put/mkdir. Prior successful claims remain unchanged on a later sealed-check failure.

The actual-owner fixtures cover a synthetic dictionary stage, use filesystem transport and mock the OS guard. There is no actual-owner MCM or capacity-count seal integration case in this population. Source supports these branches through the maintained stage/scientific checks, but that is distinct from exercised end-to-end evidence. No empirical data, actual network transfer, guarded workload or financial result was evaluated.

This component does not yet select an archived scientific producer or replace full owner-finish/representation/terminal dispatch. The existing local closure is not silently reinterpreted as an archive closure. Post-owner-close authority, historical reuse, source eviction, per-transfer metering and whole-workflow physical/RSS/performance capacity remain outside scope. Remote bytes were observed during the reserved full replay; local checks do not prove continuing remote availability. All checks are sampled, not atomic. Financial timing, return/cashflow convention, exposure, fees and funding were not tested.

## Exact inspected identities

| File | SHA-256 |
|---|---|
| `archive_owner_seal.py` | `c351085eb24793111b6df858c650d78f895e8fbb6b979f3cd5f7cbcf7ca86549` |
| `archive_owner_stage.py` | `07555f0c3df878e67e3ab22a5a94cd0e1369584334ec33ff8c19fa311d56e830` |
| `compact_owner.py` | `0ccda2d3d3b63b7e0e57af999e0b3e0c9f322e9f2fd8671a9e92e95c352ea25f` |
| `test_archive_owner_seal.py` | `5522e4b264713a293436d70ca5325434cd66840b06e590a30c3884002f6e2570` |
| `test_compact_owner_read_cleanup.py` | `776e910da7229941dbd24911481cd1c525e4421507c9a0741462a1ee46198738` |
| `check01.log` | `1dfd84a10f432a3aa22f226e4cbb6ed0eb0a8ea08bd41e538c27770b7e7d6433` |
| `review-red01.log` | `306d22705a6308b767dcc3e2bcdb9590db6ddb022da476bc046b1dae35cc8b41` |
| `check02.log` | `31f2468ce346827a2ea2f6cc4e461cc604f2604e317e67c21fade5f7cc21f347` |

The preserved initial seal/stage/owner sources and test snapshot were also hashed; their original identities remain separate from the corrected evidence.
