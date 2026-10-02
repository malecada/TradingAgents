# Independent initial transport review

Disposition: acceptance withheld for the cleanup and acknowledgement boundaries below. This is a read-only source/evidence review; no test, network operation, historical job or numerical experiment was executed by the reviewer.

Reviewed source `archive_transport.py` SHA256 `5dd39e887d0550bfbf0f8ab99a2d1860c36f4b77425583b366c1671f77468060`; test source SHA256 `32d8386e5a74817dc78c5aeed44537b5048fc6d1f7c51779ed23c2a9bfe22ec4`. Saved `check02.xml` SHA256 `14f73728cb3c8a68bb9db063fdadac0b9bd5c801e44dde9703d604059e281ff6` records 29 tests, zero failures/errors, suite time 1.110 s (reported pytest wall summary 1.12 s): 24 maintained adapter cases and five preserved adapter cases. These tests do not cover the following cleanup faults.

## ATP1 — cleanup can stop early and obscure the primary failure

At `tradingagents/research/onchain_replication/archive_transport.py:113`, receiver cleanup sequentially invokes process-group kill, child wait, stderr read, stdout close and stderr close before writing the diagnostic receipt. Except for ProcessLookupError/BlockingIOError, an error in any earlier operation skips the remaining actions and receipt. The resulting ordinary exception can replace a timeout, lease revocation or receive error, while process or descriptor cleanup remains uncertain. The raw descriptor closes in `put` at lines 212 and 233 have the same ordinary/masking failure behavior. This is material for use inside an owner operation whose ordinary unavailable handler must not continue after uncertain cleanup.

Required correction: retain the primary exception, independently attempt all applicable owned cleanup actions once, preserve bounded failure diagnostics where possible, and propagate the shared fatal CleanupFailure when cleanup is unresolved. Do not retry a possibly closed descriptor. A failure of evidence writing must not prevent remaining cleanup. Test early kill/wait failure and pipe/output/upload-descriptor close failures, including a primary already in flight. Explicitly distinguish a kill request and direct-child wait from independently confirmed descendant termination; the outer guard remains responsible for complete worker cleanup.

## ATP2 — complete receipt precedes output close

At lines 125–131, the receiver writes `status: complete` inside the `with destination.open('xb')` body. The output context-manager close occurs afterwards, at line 68's exit. If close reports uncertainty, the durable receipt still reports complete and the error escapes without a failed/cleanup-failed acknowledgement. This affects both download staging and silent command diagnostics.

Required correction: successful receipt acknowledgement must follow successful output and owned process/pipe cleanup. Preserve failure evidence rather than overwrite an already published success. Add a deterministic output-close failure regression for both successful reception and an existing primary error, checking fatal propagation, primary cause and absence of a false complete-only result.

## Supported bounds and exclusions

The current source preserves the dated adapter's bounded upload read and sealed memfd snapshot before exact payload reservation. The upload child opens the sealed parent descriptor rather than the mutable source pathname. Download reservations remain `32768 * (expected_bytes // 32768 + 1)`; output is capped at the expected extent plus one detection byte, exact extent is required, stderr retains a 16 KiB tail, and destination publication is exclusive. The maintained tests exercise immutable upload despite source growth, lease refusal/revocation, short/excess/error output, ordinary timeout, bounded stderr, budgets and temporary local archive round trips.

Configuration has a new explicit identity, and command attributes/callbacks remain trusted caller inputs. The review does not establish concurrent shared-budget safety, actual SSH/SCP interoperability, current remote availability, remote capacity, wire-byte accounting, external recovery, owner/producer integration, an OS resource guard, or scientific/financial admission. The historical accepted smoke evidence is preserved; it does not prove the new cleanup paths. No external action is released by this note.
