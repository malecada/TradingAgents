# Independent corrected tail/seal review 03

Accepted for the bounded MCM tail/seal primitive. The reciprocal ST1 destination gap is addressed; both earlier withheld reviews remain historical evidence.

The corrected seal pins the destination index/start hash and exact float64 payload before append. After destination publication it performs the external tail lease and batch writer check, then invokes callback-free two-pass verification of the original tail terminal. Finally it checks the destination root and exact start/header hashes and payload bytes without another external callback. Consequently a final tail callback cannot silently alter the destination that the returned head describes. Late failures retain the already written stores and return no successful seal; there is no automatic retry.

The targeted red03 regression demonstrates the former gap by corrupting the destination from the final tail callback: one failed, 13 deselected, in 0.20 seconds. Saved check03 closes with **14 passes in 0.28 seconds**. The reviewer inspected the delta and saved evidence without rerunning tests.

Acceptance remains non-atomic after the final individual file observations. It does not establish actual workload membership, registered owner admission, recovery of an unterminated tail, per-pair checkpoint replacement, matcher convergence/cleanup or full-workflow resource feasibility. The 8 MiB tail limit bounds record bytes; decoded values/purposes, rereads, copied payloads and retained destination bytes require separate memory/storage accounting. Exact [0,1] float64 records and purpose chains are checked, but the caller must establish that those purposes arose from the admitted MCM schedule.

Exact SHA-256: source `deb225ccb9d4002d619d4a09c23272ee93bcfa675a8c54d932fc4f3758420e88`; tests `27af4c26c4810cf8cefad4836786856bc6c0e86e52dc339e9ca5f64a89791a7a`; check03 `2d66fa7d835f3895ae3e8836e01e5746407b7263fbb3ce59bd3d2896ed4bcaf7`; red03 `cf2c8c07304c4fc60787634d7b118c56a0638547bc4dc760e3089868562f2f5d`.
