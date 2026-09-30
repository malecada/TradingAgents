# Independent first-owner binding review

Initial acceptance is withheld for the two concrete checks below. This review concerns only the stated first-owner binding component, not deferred pair workload membership, continuation/death admission, orphan recovery or production numerical routing. Source and synthetic test evidence were read without running tests, jobs, empirical inputs or numerical arrays. Only this review was written.

## O1 — live monitor identity is not joined to its owner

In the initially inspected `Binding._guard`, the returned live receipt's `owner_identity` is checked against immutable guard ownership, and `same_process_alive` verifies that the retained owner PID/start ticks are alive. However, the live receipt's top-level `monitor_pid` is never compared with that owner PID. `resources.assert_guarded_worker` verifies command, boot, lease, cgroup, affinity, kernel controls and resource boundaries but does not supply this missing comparison. `job.py`'s observer reconciliation does explicitly require that join.

Consequently a returned live receipt naming another monitor while retaining the expected owner_identity passes this candidate's monitor binding. Require exact typed equality of live monitor PID and retained owner PID before checking the owner's start ticks. Add a negative fixture that retains the valid owner/command/policy but changes only the live monitor PID; rejection must occur without pair work. This is a missing component-local join, not a demand to implement deferred workload or predecessor admission.

## O2 — schema versions admit boolean/float aliases

The candidate uses Python numeric equality for producer-plan version 2, pair-policy version 1 and FeatureJournal start version 1. Values such as 2.0, True and 1.0 can therefore pass those schema checks despite the intended exact versioned contract. Use explicit integer/non-boolean type checks before the version comparison. The inherited job-schema check similarly uses numeric equality; an exact candidate-level contract should reject a non-integer execution-job version as well rather than silently inherit that ambiguity. Add admitted-input fixtures with those representations, ensuring they fail at the binding schema boundary rather than merely because an input hash was changed after admission.

## Inspected sound behavior and scope

The component requires an actual ResearchRun, rechecks its active claim and source admission, reads the exact selected execution job, producer plan and policy through registered input access, and derives the expected representation workflow/path and current owner from admitted data. The first-owner restriction rejects supplied journal ancestry and other representation directories. Owner/start/claim and launch/guard-owner metadata are read as compact regular nonsymlink same-device files through no-follow descriptors. Stable signatures appropriately omit atime while retaining modification/change clocks, inode, mode, links, size and blocks.

The explicit numerical source anchor is kept separate from the actual execution commit. `_source` requires the complete current `job.required_sources()` set, exact numerical file membership, equality to admitted execution pins, equality of imported implementation files to those pins, and equality to the nominated older commit's file bytes. The candidate's own source is also required in the execution closure. This is exact-byte compatibility, not arbitrary cross-commit reuse or a substituted execution owner. Runtime environment is joined to its admitted input and numerical context. No checkpoint or pair is allocated by binding.

`lease()` checks active claim, immutable owner metadata, nonterminal journal and guard status; it explicitly does not rehash all sources/inputs. `check()` additionally revalidates source, inputs, numerical anchor and runtime. Neither method is a lock. The existing source freeze and sole-worker guard must remain effective between these checks and any later numerical action.

The author independently added a sibling recheck to `lease()` after retained red02 exposed acceptance of a sibling appearing after binding. That correction is present in the inspected current source. Its initial 13-test green02 result is saved as 13 passes in 48.232 seconds; expanded final evidence remains pending. The earlier green01 errors arose from comparing atime across metadata reads, and must remain described as fixture/implementation failures, not a passing run. The original missing-module red and intermediate sources remain retained.

Reviewed intermediate source SHA-256 after sibling correction: `e03bbf666a9e2dd8dee47553f4717fb9a24349e61e6693fa2f67603f09395dd8`. Corresponding test SHA-256: `dc03eac00c64da781dad59d957a2633abec4029b8417858507ef7a834b04fd27`. `green02.log` SHA-256: `b4d361fb410549d4009fd69ce651c4e21c377931381f7245cdad5e1c8b9c509e`.

No live kernel guard is exercised by these synthetic tests: the guard assertion boundary is mocked, while the ResearchRun, registered inputs, source commits and FeatureJournal are real temporary fixtures. This can test the ownership joins around that boundary, but must not be presented as a new guarded integration run or empirical admission. A later production layer must also consume the returned immutable context/limits through the exact expected API types and retain all remaining admission and publication obligations.

## Final closure review — September 30, 2026

Accepted for the isolated first-owner binding scope. O1 and O2 are closed in the inspected candidate; no remaining material blocker was identified within that scope. This conclusion supersedes the initial withholding above, while preserving its findings and the failed evidence.

O1: `owner.py:63–66` now joins the live receipt's owner identity and registered resource values, requires an integer live monitor PID equal to the retained owner PID, and checks the retained process start ticks through `job.same_process_alive`. The latter also rejects noninteger/nonpositive retained PIDs and malformed ticks. `test_owner.py:194–196` changes only the live monitor PID, preserving the other valid joins; retained `red03-monitor.log` demonstrates its previous acceptance.

O2: `owner.py:108`, `117`, `122` and `141` explicitly require integer execution, producer-plan, policy and journal-start versions before their contracts can pass. `test_owner.py:64–79` applies the malformed registered contract, rewrites its input hash and dependent descriptor/plan/job hashes, commits, and only then starts the actual temporary ResearchRun. Thus the boolean/float negatives at lines198–217 reach admitted malformed contracts rather than incidental input drift. The journal-start negative correctly mutates journal metadata, which is a separate ownership boundary. Retained version red logs show four contract failures and the additional execution-version failure before correction.

The source independently confirms the actual claim, selected producer, registered policy, exact journal path/owner and live guard joins. Parent ancestry is rejected at `owner.py:145`; siblings are rejected at initial binding and on lease recheck at lines146 and72. The actual execution commit remains in the binding record, while the distinct numerical anchor requires exact membership and byte equality across the complete83-file `job.required_sources()` closure at lines86–100. Independent filesystem reconstruction found83 required files, all identical to reviewed HEAD `149e8639b5fc41618fc35675973df959546ae2b7`. This does not substitute the older numerical anchor for the execution owner.

All212 entries in `bindings.json` were independently hashed with zero mismatches. Its196 inherited entries exactly preserve `pair-extent-2026-09-30/bindings.json`, with16 additions for this component and its evidence. This evidence manifest is distinct from the83-file execution closure; its package entries omit the eight surrounding research/package files, whose bytes were separately checked against the reviewed HEAD. The complete closure requirement is enforced by the candidate and constructed by the temporary fixtures. The final retained `green04.log` reports24 passing tests in79.627seconds. Tests were not rerun during this review.

Verified SHA-256 identities:

- `owner.py`: `d68daa794ab97e7a8cc6acc2d81694043a3831d1854bc95770b15580b07c492c`.
- `test_owner.py`: `216009f81d2fd5f943cae08839230942dacc04d89cef15c70d1a1149926dd10f`.
- `green04.log`: `4c872e8f510d35a14598c35258ad5cd1c6ccfcec00960eef67566a3123b0a27f`.
- `bindings.json`: `d69146ab854e0e1b8ba427a1d8fbe0c0044ba593fb331aca30c00915c1039f86`.

Not tested or admitted: live kernel dispatch, actual registered pair workload membership, predecessor/observer death, continuation or orphan recovery, ancestor-inclusive quotas, dictionary/MCM routing and numerical parity, or production/empirical release. The synthetic guard boundary remains mocked. `lease()` and `check()` remain snapshots rather than locks; outer source freeze, sole ownership and later execution/publication checks remain necessary. No tests, jobs, empirical bodies or numerical arrays were executed/read during closure review, and no registration, ledger, implementation source or active-job source was changed. Only this review section was appended. Graph10 operation and its source gate are outside this acceptance.
