# Independent initial MCM score-stream review

Acceptance withheld for MS1. This review concerns synthetic callback composition only; no numerical or financial experiment was run by the reviewer.

## MS1 — later stream publication can invalidate previously checked children

`mcm_score_stream.py`, seal-link publication in `__call__` and `finish`: after `tail.seal` has checked both tail and batch, the stream writes its seal link and invokes an external lease through `_check`. That callback can invalidate the already checked tail/batch. The final completion path similarly writes complete.json, invokes another callback, and verifies only complete.json. It never revalidates its start manifest, full seal-link chain, earlier batch payloads/headers or retained tail proofs against the returned completion record.

A deterministic counterexample is a lease callback triggered after complete.json publication that changes the first batch payload or first seal link while leaving complete.json untouched: finish returns success. A corresponding mutation during seal-link publication can let the last score of a chunk return successfully with invalid retained child evidence. The new tail primitive's checks do not cover these later stream callbacks.

Required correction: retain exact expected stream start/link/child references and provide a bounded combined content/chain/inventory check after external callbacks before acknowledging a completed chunk and before final completion. Final references must bind the actual complete tail terminal and destination header, not whichever hashes are observed at verification time. Preserve partial/conflicting files and refuse success on late failure. Do not execute the matcher again to validate storage. Add late-child and late-link drift regressions.

## Supported identities and evidence qualifications

The constructor derives the same MCM workload scope as the frozen kernel from graph hash/node order, dictionary identity, ordered motif identities, matching configuration, explicit backend and workflow. Each callback checks the exact sequential center/motif occurrence, local parent/center attribution, ordered graph identities and complete purpose hash before compute. A tail is reserved before computation; the callback result must match the expected purpose and pass tail range/finite checks before it is persisted. Completed tails and destination chunks are retained, with links naming both hashes. These are useful composition checks; actual induced-local-graph membership and registered scientific/owner admission still rely on the surrounding kernel/lease contract.

Saved check01 reports **3 passes in 0.55 seconds**. The positive fixture uses the real frozen MCM kernel and scalar reference callback for 14 cells across four chunks; it proves exact purpose order and final float32 matrix parity. However, recovered tail scores are compared only after float32 conversion. That comparison does not independently establish exact retained float64 equality to the 14 scalar values already available in the reference callback's `saved` mapping. Add a direct little-endian float64 byte comparison if claiming that stronger parity. The cleanup fixture raises a synthetic RuntimeError labeled cleanup; it proves propagation, identity closure and no later compute, not actual PairSession cleanup behavior.

The adapter still delegates convergence, checkpoint publication and cleanup to compute. Wrapping the old Serial route therefore retains its per-pair artifacts/reservations in addition to tails/chunks; this change alone is not the scalable scratch/persistence replacement. No source/registration admission, successor reuse, financial fit, capacity measurement or process-RSS limit is established. No closed test was rerun.

Reviewed SHA-256: source `cd6ade1794f2fe00cf0c4dab5f89f64b6e2ceb18876b5aea25ded6cfb2779873`; tests `30c6c99a423b8ac834d84e7a1d35f65cf905f0d881449f27bdf43a9a24140527`; check01 `b11328f75e4df8d01db7477c465137e02f64e7b08a056ac8ae0fe82878167022`.
