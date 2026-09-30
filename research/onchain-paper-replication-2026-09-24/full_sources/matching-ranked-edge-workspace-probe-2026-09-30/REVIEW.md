# Independent prospective directed-chain profile review

Conditionally accepted for one fresh finite synthetic invocation after the checks below. No blocking defect was identified in the worker, objective oracle, checkpoint accounting or declared guard. This review executed no tests or profiles and opened no large bodies.

All 100 compact bindings independently match at observed HEAD `acfed7fd5922c4254be024454672791abf238102`. They include the worker/oracle/tests, retained focused logs, unchanged reviewed composite and component sources, imported production source, configuration, runtime description and launcher. Exact identities:

- `probe.py`: `1dea41d27bca9ca79f9b54dc3c719a7f4d82f5731875707d10f83d4cbc68c856`
- `oracle.py`: `46ba66767e9fffb54a20d68d0ad5e7f5560b855a7714eed309c18fc2b2c29329`
- `test_oracle.py`: `8293f788f14b726b6e0e9fa44d346ac573cd8da16f3f383681a17080143d0410`
- `run_guard.py`: `d38dc0860a6c8d593e41486254d74094482e60b92c014f246e650de46c0fe834`
- `PROTOCOL.md`: `bdc3bef780c2df0eb4d52549ecd785f2daada2176f9b63e5da14306b04ffbe66`
- `bindings.json`: `b2eb5bed55282013224376aba14959d0597f7118788860c668a1cbe4f6f8840c`

## Work and independent oracle

The graph constructor creates the stated two identical fresh directed chains: 2,000 nodes, 1,999 edges, zero node attributes and unit edge attributes. The unchanged configuration retains its 4,000,000-pair cap and 48-iteration temperature schedule.

Independent arithmetic gives `48*1999^2 = 191,808,048` edge-pair updates and `4,000,000 + 48*(1999^2+251) = 195,820,096` annealing operations. At 4,000,000 operations per advance, this requires 49 calls. Calls 4 through 48, spaced by four, are still before the final operation total and therefore produce 12 intermediate annealing snapshots. These counts reflect the reviewed implementation's operation accounting, not equal-duration work units.

A full bijection of two constant-feature chains gives node contribution one. A directed source edge contributes exactly when its mapped endpoints are adjacent in the forward target direction. Counting these conserved edges as `h` gives the literal edge contribution `h/(2*1999)` and total `(h/(2*1999)+alpha)/(1+alpha)`. The independent oracle checks a complete integer bijection and computes that count without importing matching or graph-validation code. It neither forces the diagonal nor asserts optimality. The saved log records two tiny tests passing, including identity, reversal, rotation and malformed assignments; this is an arithmetic check of the oracle, not a full-profile result.

The worker compares the actual scalar score with this oracle within `1e-12`, checks 48 iterations and temperature termination, and retains final pairs in checkpoint metadata. Column normalization is a tolerance diagnostic, not a prescribed assignment or general rectangular normalization claim. A hardening prefix may already complete; the worker correctly accepts that outcome without artificially extending the search.

## Checkpoint and resource accounting

The checkpoint helper saves to an exclusive directory, closes the old state and any actual ranking mapping, then restores against the supplied manifest hash. It compares phase and scalar cursors/schedule, and the hardening prefix where present. The inherited loaders verify array identities; the hardening-stage composite independently hashes the restored soft matrix. Final restoration additionally checks the original soft-matrix identity and exact restored score. Final mapped-state closure precedes result publication.

Twelve annealing snapshots plus two hardening/final snapshots give at most 14 directories. Fourteen separate 128 MiB allowances total 1,879,048,192 bytes (1.75 GiB), below the enforced 2 GiB total logical checkpoint allowance. Before each save, the helper checks both count and the existing logical sum plus a full new 128 MiB reservation, as well as fresh free space of 10 GiB plus 144 MiB (10,888,413,184 bytes). Launch requires 10 GiB plus 2 GiB (12,884,901,888 bytes). Receipt/log bytes, filesystem allocation and unrelated host writers are not part of the logical checkpoint sum; the extra headroom and outer disk guard remain necessary.

Partial save/restore failures escape and stop this invocation. Already written bodies and receipts are retained, with no deletion, automatic retry or reuse of a failed identity. Process cleanup by the outer guard, rather than a successful-state assertion, is authoritative on failure. No destructive recovery path is introduced.

The reviewed launcher and worker agree on 1 GiB maximum, 768 MiB high, zero swap, two CPU affinities, 3 GiB host reserve, 4 GiB startup, 10 GiB disk floor and 1,800 seconds. The worker verifies both all bindings and runtime inventory. Retained state, ranking and scoring allowances remain 128 MiB, 80 MiB and 8 MiB. Checkpoint page cache, validation/diagnostic temporaries, native sorting, Python/runtime and graph residency are inside the process guard but outside component formulas. No completion, worst-case peak or periodic checkpoint wall-time promise follows from the shorter prior edge probe.

## Release conditions and remaining claims

Commit and push the exact reviewed source and manifest before dispatch. Freshly verify the recorded HEAD, all 100 hashes and committed bytes, pinned runtime, absent attempt identities, closed prior owners and no active replication unit. Apply Graph 10's stated priority if its fresh 9 GiB plus 128 MiB startup and 22,103,159,134-byte disk requirement are both met. Otherwise this independent lower-startup-memory profile may run after its own 4 GiB RAM and 12 GiB disk checks; Graph 10 must wait until the profile closes. These priority/exclusivity/startup-headroom requirements are outer preflight duties, not additional checks in the thin launcher.

Freeze HEAD and bindings during execution. A terminal timeout remains a failed finite measurement; do not change its limits or restart its identity. Independent terminal review must reconcile actual checkpoints, counters, score oracle, source stability, guard closure and ownership before accepting a result.

This is a fresh synthetic fixture, not a replay of a closed profile or a financial experiment. Even successful completion will not establish real-hub, dictionary/MCM/neural or GPU feasibility, production backend/cache equivalence, a controlled speedup, financial performance or completion of the original resource and 1,420-fit denominators.
