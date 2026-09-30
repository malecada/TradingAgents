# Independent isolated composite review

Accepted for the documented synthetic component scope. No blocking defect was identified in the inspected composition. This is not production, empirical, capacity-scale or backend-substitution approval.

Review inspected the actual composite, component contracts, tests and retained logs. No tests, profiles, financial jobs or checkpoint body reads were performed. All 89 compact source/evidence bindings independently matched. Observed HEAD was `eb5ddb51aa49537ec53fca6b3a3d7f4803d29900`.

Reviewed SHA-256 identities:

- `combined.py`: `0c692084bd7f4fb746a6529c37ec1475cfe3640b5f7f1f3bf2ae249de3a43d16`
- `test_combined.py`: `43a0c1de0da698f791cba2773258bbe8246407965c42155130556736941f398e`
- `IMPLEMENTATION.md`: `1b069490dc5f4201b0af07f8861c448f96af61813a167bc41732ad98668e51bd`
- `bindings.json`: `b60cea6e3d622577ab544ab83ad93bfde2f94ab1389256b0b6964ed0198b0fa2`
- `green02.log`: `11e6983fd58b03f2e35f18bb7a8d3241adfaf592a6b5fe484c3a82282250f764`

The saved final log records eight tests passing in 1.095 seconds. The missing-module red and earlier five-test green remain retained. This review does not represent an independent rerun.

## Numerical and state identity

The composite delegates annealing to the unchanged scalar normalization state machine and ranks the resulting C-order float64 matrix without a new cast. Stable descending ranking preserves row-major ties; accepting candidates only on unused rows and columns preserves the reviewed greedy rule. The complete matrix is hashed before ranking and the rank component independently hashes it during creation. The completed matrix becomes read-only. Restoration separately rehashes the annealing matrix and joins it to the ranking input identity, rather than trusting the outer identity string alone.

Schema 2 requires the exact outer policy and rejects schema 1. Configuration and graph identities remain checked by the annealer, and the original pair-capacity check remains active. Trusted manifests and exclusive state, graph and checkpoint ownership are substantive requirements: structural validation does not replay an adversarially edited greedy prefix or prevent an owner from forcibly changing array flags.

Three tiny fixture pairs compare exact soft-assignment bytes, hard assignment, scalar score, iteration count and convergence against the literal reference, saving and restoring at each advance boundary. The fixtures include nonzero directed edges, ties, rectangular shapes and a singleton column. These establish useful composition regressions, not general floating-point equivalence to the accelerated Torch backend. Sparse finalization retains its explicitly narrower representable-agreement domain and propagates refusal; the domain-propagation test uses an injected component refusal rather than new numerical overflow fixtures.

## Ownership and interruption

Both outer and affected component state are poisoned on mutation-path interruption. Atomic ranking occurs only after annealing completes; failure there requires the preceding annealing checkpoint and cannot resume the sort. A hardening advance scans at most the smaller of its operation allowance and the admitted chunk size, capped at 65,536 ranking entries.

Restoration opens the ranking mapping first, then restores and validates annealing state. On any later escaping `BaseException`, it attempts to close the actual ranking mapping and preserves the primary error; a secondary cleanup failure is noted. Saved tests retain the mapping handle and verify closure after an annealing-loader interruption and after an independently inconsistent restored matrix. Successful parity-test states are explicitly closed before replacement and on exit, addressing the lifecycle limitation of the standalone ranking fixture. `close` invalidates the outer state and drops dense-state ownership even if ranking close raises. External aliases and retained exception tracebacks remain outside a claim that all process memory has been reclaimed.

Exclusive directories, component file/directory fsync and final outer-manifest publication preserve completed checkpoint identity. Partial failed directories are retained; no restart into an existing destination is provided. Crash recovery and secondary cleanup-failure behavior were assessed statically, not exercised by the eight saved tests.

## Resource and release limits

Retained numeric state is three float64 matrices plus one int64 permutation: `32*n*m`, or 128,000,000 bytes at 2,000 square. Ranking's separate explicit allowance is `17*n*m+n+m+16*min(n,m)`: 68,036,000 bytes at that shape. Adding the 96,000,000-byte annealing state gives the documented conservative 164,036,000-byte overlap. These formulas exclude graphs, Python containers, validation temporaries, native sort workspace, allocator/runtime and I/O buffers. The default 80 MiB ranking allowance is not an old small-workspace policy reused silently.

The checkpoint reservation `32*n*m+512+3*65,536` equals 128,197,120 bytes at 2,000 square. It reserves four normal NPY headers and three bounded manifests; it is a logical-byte allowance, not a filesystem allocation or total retained multi-checkpoint budget. Total state, ranking scratch and checkpoint insufficiency are rejected before their respective allocations/publication paths in the inspected tests.

Score-only reserves the int64 pair array plus the sparse objective allowance, totaling `80*min(n,m)+32*min(chunk_edges,Eright)`. It avoids the diagnostic dense assignment and soft-matrix copy. The dense `result` helper remains explicitly outside that memory claim. Sparse scoring, ranking, full identity/finite checks and checkpoint publication remain atomic; an entry limit does not establish a complete-call wall-time limit.

A new finite profile must measure this composition's actual peak, checkpoint extents, restoration and cleanup under its own frozen inputs and resource admission. The earlier atomic-ranking or old-composite profiles cannot supply those measurements. No production dispatch, cache/backend lineage, GPU precision, full nonzero-edge or real-hub schedule, dictionary/MCM/neural feasibility, financial accounting or empirical denominator was tested or changed here. Graph 10 admission remains a separate resource-gated action.
