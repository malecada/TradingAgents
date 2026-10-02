# Bounded archive prototype verification

Transport-neutral copy/readback and fresh retrieval are implemented in
archive_chunks.py. They bind a trusted expected extent/hash, scope, transport
identity and exclusive remote member. Source bytes remain local. Complete
publication is followed by a live lease and exact content/metadata/root checks.
Foreign files and conflicting failure receipts are rejected. Failures retain
originals, partial copies and diagnostics; a terminal identity cannot replay.

- red01: 16 failures from the absent module, 0.17s.
- check01: 16 passed, 0.25s.
- Independent REVIEW_INITIAL found AC1 late completion-publication and AC2
  missing exact inventory/conflicting failure refusal. Original source retained
  as archive-check01.py.
- review-red01: all 15 targeted regression cases failed as intended, 0.53s.
- check02: 31 passed, 1.19s after the single correction pass.
- Companion adapter check01: 34 passed, 0.47s (same 31 plus three real local
  subprocess transport tests); see storage/archive-chunk-smoke-2026-10-02-01.

This is synthetic filesystem-backed transport verification, not external backup
verification. The SSH adapter and real external guard are separately reviewed.
No eviction, live compact reader change, whole-workflow capacity admission or
financial experiment is performed. Scope authority is caller-provided; hashes
alone do not prove a chunk is closed or eligible. The local free-space check is
not physical space reservation; allocation overhead and existing retained
evidence need whole-workflow accounting.
