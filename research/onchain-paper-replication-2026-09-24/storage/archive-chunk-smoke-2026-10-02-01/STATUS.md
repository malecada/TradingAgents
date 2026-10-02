# External synthetic check status

Pre-execution: independent gate release accepted, REVIEW
9b88745c088ef41d0ecbd150e2e080f2d4bb671797fffa826bf4dc0bb1857b3a. No network action under this
identity has occurred. All120source/contract/test bindings are prepared.

Local verification:
- red01: missing runner,3failed0.11s.
- check01 and check02:34passed0.47s each, before transport findings.
- AT1 fresh per-subprocess lease and AT2 mutable upload extent findings retained
  in REVIEW_INITIAL.md.
- lease-red01:1failure from missing planned constructor keyword; improved
  lease-red02:2failures3deselected0.29s directly demonstrate both unsafe outcomes.
- check03:1failure35passed0.58s due to pinned Python missing memfd bindings.
- check04:36passed0.57s after verified Linux libc/ABI implementation.

All attempts and source snapshots remain. No historical identity is replayed.
The combined suite is focused engineering validation, not the full offline suite.
