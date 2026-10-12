# Bounded historical verification policy

This ordinary engineering change addresses repeated historical proof work in
the authorized real-data pilot. It does not spend a research attempt or release
an empirical entry. The original scientific architecture, matching procedure,
32 motifs, 512 spent samples, numerical tolerances and data scope remain fixed.

The proposed selector is explicit:

```json
{"format":"bounded-claims-v2","workers":2,"max_audit_seconds":300}
```

Absent selection and `bounded-claims-v1` retain their existing full-verification
behavior. A selected genuine run starts with full historical verification.
Subsequent checks freshly read the canonical history roster and SHA256 of exact
claim and terminal bytes. The verified history is immutable metadata private to
that run. Current HEAD, registration, design, charter, working source and Git
bodies, runtime, input/binding contract, own claim, budget, parent and exposure
checks remain fresh. No Git process or Git-body success is retained between
checks. Budget totals are recomputed; no refund or transfer is introduced.

Full historical verification also occurs at every completed 4,096-cell batch,
finish, elapsed time of at least 300 seconds at a check, and any
roster/claim/terminal change. The clock starts at audit entry; auditing time is
included. No background timer interrupts an indivisible operation. Snapshot
integrity, run identity and source/policy joins are required. Nonfinite or
backwards clock observations fail closed. The new path is bounded and refuses
unsupported history size rather than silently truncating it.

This changes historical Git mutation detection and failure timing. Historical
Git objects are checked at the stated audit boundaries rather than at every
warm admission. A corruption-and-restoration between audits is not excluded;
claim/receipt-byte hashing does not certify Git object freshness. This is not
claimed to be equivalent to the original sampling policy. Terminal-byte change
detection does not add `verify_run` or complete output-tree verification.

The exact source delta and focused mutation/failure controls require independent
review. A future empirical gate and charter must explicitly adopt this policy
and pin the reviewed source. Previously prepared pilot40 metadata remains
unreleased and must be rebased before use with changed source. No closed pilot
identity may be relaunched. The capability-free component benchmark times
historical scanning only and excludes fresh own-claim/current admission checks.
Its result is not whole-pilot throughput, population capacity, a complete MCM,
or a training result.
