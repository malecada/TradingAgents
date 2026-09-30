# Independent release review — graph08 saved arrays

Decision: accepted for one finite read-only saved-array verification, conditional on immediate fresh binding/runtime/HEAD, owner and resource preflight. No verifier, test, producer or body read was executed by this review. The bound preparation review is unchanged.

All **217 compact bindings** independently match. `bindings.json` SHA-256 is `9df3daeb973d6b04187a5a1a5a6c7ce1b5d20fc36a1bdee73fe65cba839e6431`. The actual source HEAD remains `5befae305d02585bd3b034ddabbc140f780b0d34`. The binding set contains every one of the claim's 88 source pins and 87 unique input paths (98 input references), all 22 producer JSON artifacts, **all three lifecycle output receipts**, and the actual claim, complete terminal, owner, observer, final guard, gate, producer closure and its independent review. Five verifier files are also included. No array, raw or SQLite body was hashed to perform this compact review; large-file hashes remain producer evidence until the planned verifier reads them.

The bound graph08 gate is `18b8302552a7a54e8f0462499710dbe713d82d56fb935dc83cd607136b8792e2`. Producer closure is now actual: eight complete cells, 7,621,136 raw rows and 3,649,155 admitted transactions, successful guard/cleanup and exact old owner/cgroup absence. The independent producer `CLOSURE_REVIEW.md` hash is `f161662a38e2c1ed1327a42e6c982829d525c2cdc1fe2f84c4ba107c112c288e`. None of those facts is inferred from merely prospective fields. The new verifier's guard, started receipt and result remain absent at this inspection.

| Bound verifier file | SHA-256 |
| --- | --- |
| `verify.py` | `b303b74be985b1afbcf219090b107d9963ec205ffba6b6acf219fb6d280c9221` |
| `run_guard.py` | `4903bcb9217060c8242570587101d506e0b741e9025f89ec58ce0e838c976257` |
| `PROTOCOL.md` | `4ea817771c64580bb54e43510bc47802ae64066688c5556dddb09c69fdd4d193` |
| `reconcile_compact.py` | `423803b5658ae2c55f8dab3c83d48d113bbe2e5cffb0ac60d4d47e84e396909c` |
| `VERIFY_PLAN_REVIEW.md` | `de07e1e3123bf55ffff780d65e5c423a16fd2902d6e5b637989198fbf7cef13e` |

The previously reviewed algorithm and August substitutions are unchanged. It checks all five arrays' bytes/hash, structure, canonical graph identity, coverage joins, admitted edge-count conservation, log1p edge attributes and independent four-feature bincount reconstruction. A full edge-index row may be converted to a Python list during canonical encoding; validation, comparison and bincount temporaries remain covered by the outer guard, not an asserted constant-memory implementation.

Before one launch, retain fresh proof of all 217 hashes and exact unchanged HEAD, runtime match, no active replication unit, absent verifier identity, actual producer cleanup, at least 6 GiB available startup RAM and the 10 GiB disk floor. Use the exact reviewed launcher with 3 GiB maximum, 2 GiB high, zero swap, 3 GiB host reserve, two-CPU affinity and 1,800 seconds. Keep source/bindings/HEAD frozen through terminal. Do not retry a reserved identity or treat a result file alone as success.

Actual result/log/guard reconciliation, post-run binding hashes and exact verifier owner/cgroup absence require a separate terminal review. Even a successful result will not independently replay raw uniqueness, values or exclusion classification, validate financial outcomes, complete Task 8, admit fitting or prove remote graph recoverability. The producer is terminal and must not be rerun.
