# Independent initial sampler-draw review

Acceptance withheld pending the two corrections below and terminal evidence. Source and dependencies were reviewed read-only while check01 was active; no test, historical job or empirical array read was performed by the reviewer.

## CS1 — Wrong graph contract in resident fingerprint

`tradingagents/research/onchain_replication/compact_sampler.py:95–98` invokes `neighborhoods.graph_hash` for each sampled graph. The preserved kernel returns `contracts.AttributedGraph`, while `graph_hash` calls `validate_graph`, which expects weekly GraphSnapshot fields including asset and start/end clocks. Successful sampling therefore cannot produce its completion fingerprint. The positive test repeats the same incorrect graph-hash call in its expected comparison.

Use a bounded attributed-graph identity that validates and binds all numeric arrays with shape/dtype/order and node/parent/center identities. Do not omit numerical bytes to make the fingerprint pass. Compare the actual sampled outputs against the independent existing sampler using the corrected identity or exact array comparisons, and retain this failed attempt.

## CS2 — Draw acknowledgement precedes final saved-byte verification

`compact_sampler.py:210–214` writes the next draw through `score_batches._write`, then invokes the external live lease and returns. `_write` fsyncs bytes and directory but returns the hash of the intended bytes; it does not read the saved file back. A final lease callback can corrupt or remove the draw/start record while returning successfully. The kernel then proceeds to another RNG draw before the eventual complete-result check refuses. That violates the stated per-draw durable acknowledgement boundary even though final admission may fail closed.

After the last external callback, perform callback-free bounded readback against the prebound start/draw hashes, pinned root and expected attempt inventory before acknowledging the draw. Establish the corresponding durable start boundary before the first draw. A targeted regression should mutate acknowledged evidence in the late callback and prove refusal before a second RNG draw/checkpoint, preserving the partial namespace and poisoning its owner.

## Scope and evidence

Exclusive per-workflow/experiment attempt naming, selected plan/job policy, actual compact training/owner authority, retained failure markers, logical `(draw_count + 3) * metadata_cap` allowance and the unchanged leased kernel are appropriate bounded components. The allowance covers start, all draw records and possible complete-plus-failed records; it is not physical quota or process memory. The 16 bytes per training center cover weights and probabilities only, excluding NumPy choice scratch, Python objects and other array/RSS costs.

The PCG64 transition check establishes one uniform transition per saved draw under the pinned NumPy implementation. It does not independently recompute weights, selected probabilities or induced neighborhoods. Numeric sample publication, scientific sample-provenance admission, dictionary consumption, resume and empirical release remain explicitly absent; both public flags correctly remain false.

Read retained red01: 1 missing-module failure and 7 fixture errors in 24.02 seconds; red02: 1 missing-module failure, 7 deselected in 15.89 seconds. No terminal check01 outcome or passing final-source result is claimed by this initial review.

Reviewed source SHA256: `c8ca840a7a1b7fe6684ea89282dfc1979795bf6c7db3f5d8d89b870abc023473`.
Reviewed test SHA256: `2603b2630a1ac30793f141e1bad246f8830c2d87f5f41246c3b2d394ec897761`.
