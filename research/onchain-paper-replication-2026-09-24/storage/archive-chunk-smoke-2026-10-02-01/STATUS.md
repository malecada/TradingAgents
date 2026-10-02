# External synthetic check status

external01 CLOSED session40021 exit0: actual1MiB upload plus two verified
readbacks (second through fresh transport). Guard complete/childexit0/cleanuptrue.
Never rerun this identity. See RESULT.md and guard01/final.json. Independent
result REVIEW accepted, SHA2410e76d0fce640d61ba997328628c2709a988199d9c488670196f3f78e3ef2a. Package freeze is released.

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
