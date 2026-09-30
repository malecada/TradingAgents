# Independent ranked-hardening workspace profile review

September 30, 2026. **Accepted for one finite synthetic engineering invocation after commit/push and fresh exclusive-owner/resource checks.** All 88 bindings independently match. No guard, started receipt or result exists at review. No profile or test was executed by this reviewer.

The probe creates two fresh C-order float64 2,000-square matrices sequentially: all zero, then negative absolute row-column distance. It retains the four-million-entry pair cap and exact 68,036,000-byte explicit rank allowance. For the flat fixture, stable row-major ties followed by used-row/column masking select the full diagonal in order. For the distance fixture, all diagonal entries are zero and all off-diagonals strictly negative, so stable ordering selects every diagonal entry before any negative entry. Comparing both pair columns with `arange(2000)` verifies all 2,000 choices and their order, not merely assignment cardinality. Before/after SHA checks verify unchanged input. The hash is over deterministic in-memory scratch, not empirical data.

The distance matrix is formed with broadcasted subtraction directly into the allocated matrix, followed by in-place absolute value and negation. Input matrices are 32,000,000 bytes each and are explicitly discarded with pair/expected arrays before the next fixture. The tiny scalar result list does not retain matrix buffers. Python/allocator caches need not return to the OS, so the guard peak measures the combined sequential process. The ranked function's native stable-sort workspace, input, imports and runtime costs remain outside its explicit formula but inside the outer guard. The fixture construction and two matrix hashes are outside the measured rank-call elapsed interval; reported algorithm timing includes native sort and Python selection only.

The launcher and worker agree on 1 GiB maximum, 768 MiB high, zero swap, two-CPU affinity, 3 GiB host reserve, 4 GiB startup, 10 GiB disk floor and 300 seconds. Fresh binding/runtime checks and exclusive publication paths are present. No-active-unit, committed/pushed-source and fresh dispatch capacity checks are external protocol conditions, not all enforced by this thin launcher. Enforce them immediately before one launch, record the resulting HEAD and owner identity, and run no graph, verifier or preservation concurrently. If resources fail, preserve the identity and any partial compact outputs; do not retry or enlarge limits based on the outcome.

The function and stable sort are atomic and cannot resume. Compact publication uses exclusive writes but is not a standalone crash-durability protocol; an interrupted/partial JSON or result without successful guard cleanup must not be accepted. Successful terminal assessment must reconcile actual guard/child output, exact source hashes, owner/cgroup absence, both fixture hashes and exact analytical assertions. No future result is inferred here.

The two fixtures test capacity-sized ranking with strong ties and a structured value distribution, not worst-case sorting or arbitrary greedy selection cost. In particular, the distance fixture finds all selected entries at the beginning of sorted order. Passing would establish only this bounded synthetic measurement. It cannot demonstrate checkpoint/resume, general full matching speedup, nonzero-edge annealing, real-hub feasibility, production integration or financial performance. Comparison against the earlier contention-affected scan profile must not be presented as a controlled speedup experiment.

Reviewed hashes:

- `probe.py`: `318f3e13c057885d3a1741d39f1b3588c2fb0cd36093fceb2eaa51493a063793`
- `run_guard.py`: `efa37014ffd453610e9a4ec614f3499e69d91cdf26fd126b5e0d0f0a31aad0fb`
- `PROTOCOL.md`: `1ecde07af5046e84e3c117dcf0bd6f2bc531c17e87582de81ff55539ccc9ddab`
- `bindings.json`: `20c79210975a3b69378a86a967fd2f7a972a9e469ef68e556148f3e6286930ef`
- `environment.json`: `f4f0ba42f05f9fda82345a4c5158a53f82225d7d224ce1b8b0fc39e1d9c99c2a`

Only this review was written. No test, profile, empirical body read, network action, source mutation or commit was performed.
