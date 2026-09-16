# Independent review of the single 8 GiB amendment

September 16, 2026. **Approve exactly one resource-only amendment for `eth-temporal-motifs-8gib-20260916`.** The user explicitly authorized raising the memory allowance to 8 GiB. No material blocker remains in the reviewed candidate after the narrow termination-race fix described below. Approval binds the target canonical contract and preservation manifest, not an unbounded retry permission.

Target contract SHA-256, excluding only the later certificate pointer: `076a5f5ff5282a448a6af6bc13a8c4fbc73bd8d3f494babebfbfda4ffe351af3`.

Source-preservation manifest SHA-256: `4fbee732ad3028e003843fcda6c5b46d4ba4277e0c6034e6346e905e6df1b18b`.

## Preserved operation and accounting

Independent comparison verified the unchanged original family, dataset definitions and parent experiment object. The target retains identical inputs, windows, stage/reuse/selection, five cells and 44 outputs. All 128 input hashes matched without numerical replay. The original failed motif claim is the explicit parent. Its claim SHA-256 is `6ba7c1697b7b9e0fa4e8928e596b78efee593eac953d924734b9df38844d8eb1`; failed terminal SHA-256 is `eab9bd876ddebcbf041ab93bf1ac5f4b9e0ed090b75acb3b5041ec3d066ea625`.

The original family remains prior_attempts=2 and attempt_budget=3. Exactly one existing motif claim exhausts that base allowance. The certificate must bind that complete relevant inventory and increment exactly one, yielding effective cap 4. Source/prototype claims remain represented once in the inherited prior_attempts, not counted again as new motif-family claims. The forensic artifact remains inspected history rather than a lifecycle attempt. The amended API requires a failed latest parent and prohibits amendment chaining. The original 2 GiB failure, source/prototype allowances and previous unavailable results remain immutable.

The preservation manifest partitions every original and target source file without omissions or overlaps. Eleven original computational/dependency files remain byte-identical, including benchmark.execute, the exhaustive oracle, original integrity/projection code, Python dependency specification and lockfile. The old launcher is the baseline harness. The target harness introduces only the new lifecycle wrapper, 8 GiB launcher, its synthetic tests/history and explicit pins for the unchanged original runtime imports. All 21 target source hashes, 12 amended/original runtime entries and 79 inherited metadata hashes matched. There are 40 local claims before this target, not a global or independent-hypothesis count; the new identity did not exist during review.

The wrapper invokes the original benchmark.execute directly with amended lifecycle read/write functions. It cannot change the 777 sentinel exclusions, transaction denominator, integer-second timestamps, block/index ordinal order, inclusive one-hour span, day boundary, six bounded subsets or Local40 definitions. Raphtory 0.17.0, Python 3.13.13 and existing package versions are unchanged. No prices, model fitting, new chain data or financial result is introduced.

## Resource review and resolved finding

The new launcher sets the sampled process-tree threshold to exactly 8,589,934,592 bytes, retains two-logical-CPU affinity, explicit checkout PYTHONPATH and 20 ms nominal sampling, and imposes no elapsed/CPU-duration kill. The cap is an upper limit, not a host-memory reservation or a promise of successful completion. A guard/setup/monitor failure remains a failed attempt; it is not permission to retry.

Review independently reproduced a receipt-loss race in the initial new launcher: after a TERM wait timed out, the child could exit just before SIGKILL and cause an uncaught ProcessLookupError. The final new launcher catches that race, still waits for the child and preserves the resource result. Its regression test passes. This correction affects only the new resource harness; frozen earlier guards and the empirical computation were not changed.

Independent validation passed 90 tests in 17.25 seconds across all five graph modules and the amended lifecycle before that narrow fix. The final changed guard module then passed all eight tests independently in 0.05 seconds. Cases cover 3 GiB below the new limit, exactly 8 GiB, one byte above, a simulated billion-second completion at 5 GiB without a time kill, setup and monitor failures, ignored TERM escalation, and exit during escalation. No large allocation or actual data replay was used. The author additionally retained a final 57-test graph/guard passing receipt; its hash and repair-preflight reference were checked.

The coordinator runtime check passed the checkout-local Python 3.13.13 environment, unchanged lockfile, installed-version reconciliation and locked synchronization. The earlier named offline result of 2,060 tests plus 81 subtests remains applicable to unchanged core code. Repeating that broad suite is unnecessary for this resource-only wrapper change. The dedicated detached execution environment must still pass its own runtime/lock and admission preflight.

## Exact reviewed bytes and release boundary

| Artifact | SHA-256 |
|---|---|
| CHARTER.md | `46c17e5d6ace811a477246dbcf7bb9addc07c9bf980282c3bf4b4b17607066ef` |
| run.py | `d933ec5cd2a54dab54c488bfd5e710d253ba6521fd5e5819a8ddd88ac7eb0c14` |
| launch.py | `2f98195952a7dec6533de5733339e6377742ec52ea172c62ee621b69a5cc0603` |
| Pre-certificate gates.json | `ce7fa9371e82cb944cef260d2d86ab2f748f1850f434a69c168f5bea269e7387` |
| source-preservation.json | `4fbee732ad3028e003843fcda6c5b46d4ba4277e0c6034e6346e905e6df1b18b` |
| preparation-verification.json | `6bb8336672c768a0d8c7bc14e53d1c9052823eadd0eaf84c87f6b408a2c7239d` |
| repair-preflight.json | `fac57e8270af28a4ebd4d6f77f454ff2762a09771d879bb59134050650afa539` |
| Guard test module | `75a87b4d7e7264ae66c9af5cfd3f83570e2ea92b5aaa08701a7cc6882a3d2e32` |

The final certificate may add only its bound budget_amendment reference to this target; the canonical target hash above must remain unchanged. It must bind this independent review/approval, the passing repair preflight, exact preservation manifest, original family and sole existing failed motif claim. Final assembly must pass the existing amendment validator after commit and remote verification, before the sole empirical claim in a dedicated fixed-HEAD checkout. The certificate is not yet assembled at this review, so successful final admission is a release condition, not a claimed completed check.

Success, if obtained, will establish completion of the same fixed one-day operation within the revised observed resource envelope. Full-history scalability, exact wei, publication-time availability, independent canonicality/day boundaries, statistical significance, incremental prediction and profitable low-exposure trading are untested. No prospective feature panel or financial admission follows. Every attempted, failed, partial and absent output must remain preserved; terminal reconciliation is required before any success statement.
