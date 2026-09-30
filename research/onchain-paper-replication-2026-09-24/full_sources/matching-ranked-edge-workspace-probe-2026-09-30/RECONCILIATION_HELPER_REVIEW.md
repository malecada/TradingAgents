# Independent compact reconciliation helper review

Accepted for conditional use after an actual successful terminal profile and cleanup. This is static helper acceptance, not a success outcome. No helper, test or numerical job was executed and no array body was read.

The initial helper SHA-256 was `d7eba214fda79d5ecb8b53f079f337fa006753c280c3f6fff1962ca7dcbe7c65`. Two concrete gaps were reported: final metadata phases/cursor were recorded without enforcing completion and result agreement; checkpoint extent totals lacked exact file membership and individual allowance checks.

The corrected `reconcile.py` SHA-256 is `03ed715812a2d73f495715123c44553b187428e7b2607763986085ee2814dd83`. Lines 94–109 now enforce the exact five-file annealing or seven-file ranked checkpoint set, each checkpoint's 128 MiB cap, intermediate annealing-only states, and checkpoint02 outer/annealing/hardening completion with 48 iterations, result/cursor agreement, cursor in `(0, 4,000,000]`, and selected-count agreement. Both reported gaps are resolved within the intended trusted-worker compact-consistency scope.

The helper requires actual complete guard/zero child exit/verified cleanup, exact owner joins and absent cgroup/process identity, and explicit inactive/dead unit state. It checks frozen HEAD and all 100 current and committed bindings. It parses the worker's JSONL into 14 ordered checkpoint entries plus the final result, joins each saved receipt, verifies outer/inner compact hashes and array extents, and independently counts conserved directed-chain edges from the final complete bijection. The result must match that scalar oracle and the expected schedule counters. Publication uses a fresh exclusive closure path and fsync; it does not delete or retry a failed attempt.

Large NPY hashes, successful restoration and mapping-close assertions remain guarded-worker evidence. The helper verifies their metadata/extent relationships without opening those bodies. It does not validate an arbitrary hostile checkpoint, replay annealing or prove optimality. A failed or partial profile requires a separately qualified failure closure and must not be forced through this success-only helper. Actual terminal evidence still requires independent review.

The helper is outside the active source bindings; reviewed HEAD remains `e6417c6f2f59c1ccf9fdb9ffd2af4c5b59020977`. No production, numerical-profile source or frozen evidence was changed by this review. This correction assessment supersedes the pending helper status recorded in the separate integration audit.
