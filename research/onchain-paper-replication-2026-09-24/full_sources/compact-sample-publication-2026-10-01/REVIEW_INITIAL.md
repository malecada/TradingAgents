# Independent initial numeric sample publication review

Acceptance withheld for two concrete callback-boundary issues. This note reviews source and tests while check01 is active; it does not claim terminal test success. No tests, historical runs or empirical array reads were performed by the reviewer. Only this review note was written.

## CSP1 — Final callback can invalidate the returned resident/draw join

In `tradingagents/research/onchain_replication/compact_samples.py`, `Published.check()` compares loaded arrays with the original resident sample payload, releases the loaded payload, calls `self.lease()`, then checks only the new publication through `_evidence()`. That last lease invokes external owner/training callbacks. Cheap Draws.lease does not rehash resident sample arrays or read saved draw files.

A late callback can therefore replace a resident sample array or corrupt its saved draw evidence while leaving the newly published numeric artifact valid. The final `_evidence()` succeeds and check returns a changed original resident result or an invalid draw-to-artifact join. Add a callback-free verification of the pinned Draws evidence and resident fingerprint after the last external callback, followed by publication verification. Regressions should separately mutate an original resident sample and a saved draw record during that final callback.

## CSP2 — Resident growth after sizing reaches the writer

At lines 212 and 217–228, `_prepare` computes exact encoded sizes and the two-payload numeric reservation, but subsequent external draw leases precede `save_component`. Those cheap leases do not revalidate resident numerical bytes. Replacing a sample array with a larger valid array during the last such callback reaches the component writer with sizes different from those admitted. The later full Draws check can refuse completion, but only after the excessive payload has been written.

Immediately after the last external callback before component writing, verify the original pinned draw/resident fingerprint without further callbacks and compare the actual payload's encoded size/numeric count with the precomputed proof. A late-growth regression should forbid entry to `save_component`, require refusal and retain the attempt/failure evidence. This requirement concerns the promised pre-write cap, not independent sampler science.

## Other reviewed boundaries

The estimator mirrors the component writer's array naming, native NPY header encoding and canonical tree/manifest format for the restricted contiguous float64/int64 subset. Its running structural/scalar/descriptor charge limits tree construction by a metadata lower bound; it is not a Python-memory limit. Exact encoded size remains checked after serialization. The prospective allowance is artifact cap plus three compact receipts, allowing start, completion and failure to coexist. Resident allowance counts original and loaded numeric payloads; loaded arrays are compared directly without constructing another AttributedGraph copy.

The strict reader is separately source-admitted and verifies all declared member hashes/extents before allocation. Exact namespace inventory, pinned root identity, exclusive creation, retained partial output and owner poisoning are appropriate. Existing final artifact checks catch late saved numeric-file corruption; they do not substitute for CSP1's original sample/draw checks.

No independent weighted-choice, selected-neighborhood or scientific sample-proof admission is claimed. Numeric publication must remain separate from dictionary consumption, native selection, cold reuse and empirical release. Review of the complete final evidence remains pending.

Reviewed source SHA256: `aa2cfa8368f6e74ec95cbb54a7ae65e1199d2e7c96c69107b12c1d77a79184f1`.
Reviewed tests SHA256: `c348e2b43f783d4e557b0c972255807afe9104882d6314942cabaa73862ca497`.
