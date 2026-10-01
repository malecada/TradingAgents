# Independent supplement — RP1 content and extent correction

The initial review is preserved unchanged. This supplement records read-only review of the correction; it is not final component acceptance. No test, research job or empirical array read was performed by the reviewer.

The first hash-based correction still had a bounded-I/O gap: an array extent was checked separately before Snapshot opened the file, while capture hashed the newly observed `fstat` size. Growth between those operations could cause reads beyond the admitted extent before the hash mismatch refused admission. This was an independently identified source-level counterexample, not a reviewer-executed race test.

The current correction addresses that gap at `publication.py:30–62`. Snapshot requires explicit admitted SHA256/byte pairs, checks the opened file's size against the admitted extent before any digest read, and passes only that admitted extent to the bounded digest helper. The helper reads chunks of at most 262144 bytes and checks one extra byte for growth. Subsequent checks retain content identity, signature, path containment, regular/single-link/same-device status, exact directory identities and exact member inventories. Capture also rejects missing or extra entries relative to the expected file map.

At `publication.py:136–160`, metadata extents come from bounded reads against admitted hashes; numeric extents and hashes come from those exact component manifests. Graph/MCM completion and start references come from the actual closure record. The correction also includes the issued dictionary ticket's dictionary and sample component references. This is necessary because retaining the ticket's leases alone leaves those stored numerical files protected by inherited signature checks. The ticket continues to content-check its proof/start/draw metadata; this extension binds the remaining stored numerical prerequisites across the handoff. It does not add a new claim about resident-array or whole-process memory bounds.

At `publication.py:186`, the new scalar representation component is retained by Metadata against its prebound expected hash before completion-proof writing. Its final lease therefore rechecks content as well as inventory/signatures, covering the late-manifest exposure described in the initial review.

Saved `snapshot-check03.log` closes six methods in 0.013 seconds. Source inspection confirms coverage of false content before capture, equal-length changes after capture, extra/replaced directory members, entry limits, links, and wrong extent rejection with `digest_stream` forbidden. The last test proves refusal before content hashing for an already-grown file; it does not reproduce a concurrent filesystem race. Earlier failed and interrupted evidence remains retained. In particular, interrupted integration check02 is not a passing verification run.

No remaining material error is identified in this correction's source delta. Final acceptance still requires the fresh full integration closure, verification of the frozen and final bindings, and accurate final scope. Sequential content checks do not establish an atomic filesystem snapshot against continuous concurrent mutation. Repeated streaming hashes add I/O; no full-fold performance, physical quota, total RSS, durable saved-representation admission, journal sealing or empirical release is inferred.

Reviewed hashes:

- `publication.py`: `0dcd200b50ec464f1f1bf7c70035eedff4421dbe4581d8e0763f657e1a40377e`.
- `test_snapshot.py`: `092d46704bf06bc4cc3ada57e60a5c614129fcdf35aac823b337d75587b5766b`.
- `snapshot-check03.log`: `e2cbdfef2ec831969f8e62239fb26aee7ced2953bea28d695d15daedf76f6340`.
- Unchanged `INITIAL_REVIEW.md`: `bb05014f6e0794b53cfedcd73217e6c8320284b7eea50211fa4955bd75fa0d5c`.
