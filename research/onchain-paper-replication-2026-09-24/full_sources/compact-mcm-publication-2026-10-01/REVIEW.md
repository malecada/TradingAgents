# Independent compact MCM publication review

Acceptance withheld for two concrete boundaries. Source and retained evidence were inspected without rerunning tests or numerical jobs. Existing implementation and evidence remain unchanged.

## CMP1 — Wrapper evidence can change during the underlying mapping's final callbacks

`compact_mcm_publication.py:139–143` performs its last wrapper `_verify` inside the body of `output.open_verified`. After that body finishes, the underlying context performs additional external lease callbacks while checking the mapped artifact. Its lease closure checks owner/stage authority but does not pin `receipt.json` or the wrapper attempt inventory. A final underlying exit lease can therefore corrupt the receipt or create a foreign attempt entry after wrapper verification; artifact verification can still succeed and the wrapper can return normally.

Perform a callback-free wrapper receipt/content/inventory check after the underlying context fully exits, or make the underlying final lease enforce the same pinned wrapper evidence. Avoid introducing another unchecked external callback after that final check. Add a targeted regression that mutates only during underlying context exit, after the body's final wrapper verification, and requires refusal. The failure path was reconstructed statically, not executed by this reviewer.

## CMP2 — Valid positive publication fails its receipt cap after writing the artifact

The closed `check01.log` reports **1 failed, 3 passed in 76.57s**. The positive registered-owner fixture reaches `publish` line 118 and fails `io._json`'s 8192-byte metadata bound. The proof embeds the entire Binding record, so the reserved one-record allowance is insufficient for the actual fixture. The artifact namespace has already been consumed and the owner is poisoned before this deterministic serialization limit is discovered.

Use a bounded, exact authority reference/projection whose identity remains checked against the admitted owner, or explicitly register and enforce a different receipt cap. Preflight the exact receipt encoding before any namespace creation, using a fixed-length placeholder for the not-yet-known artifact hash. Preserve this failed attempt and its source/test/log; do not reinterpret it as a successful roundtrip. The existing failure means the positive fixture has not yet exercised this wrapper's mapping and final owner closure.

## Other inspected contracts and limits

The selected output input must match both plan and execution job under the explicit compact backend. The actual Owner and closed required Stage are checked; stage contract owner/scope/count/policy and receipt are verified. Caller scope is joined to the selected graph, workload, registered matching hash and saved stream scope before output creation. The conservative separate reservation is every required graph's full artifact allowance plus one receipt cap. The artifact allowance includes float32 bytes and its manifest; retained pair/score evidence belongs to the distinct owner policy. This arithmetic is consistent subject to the actual receipt-size defect above.

Publication and reads hold the owner's nonblocking transition lock. Namespace paths are derived from the admitted workflow/run/stage, publication is exclusive, and post-creation failure preserves bytes and poisons the owner. The direct `_verify` path includes callback-free final content checks; the nested mapping context adds the extra lifecycle ordering addressed by CMP1.

The three passing check01 cases cover mismatched selected route, insufficient workflow output allowance, foreign expected graph and revoked claim. They use real temporary ResearchRun/Binding and actual fourteen-pair MCM evidence, with a mocked kernel guard and zero-pair synthetic dictionary stage. Scientific sampling/dictionary provenance, native producer selection, FeatureJournal publication, representation closure, physical capacity and process RSS remain outside this component. No empirical execution is admitted.

Reviewed source SHA-256: `84d5cabd39aa653c1880a4cecff5435fa4fe6c488263d43a5d7c86ba556d722d`.

Reviewed test SHA-256: `af00e44c3c2f1949bee9b0b918f1555b7a462ddbf49448d9fcf785368a0fe66f`.

These identify inspected files, not a complete execution-time dependency manifest.
