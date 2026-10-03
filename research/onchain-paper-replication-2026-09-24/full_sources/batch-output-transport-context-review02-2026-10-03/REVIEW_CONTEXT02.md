# Independent local non-tail context02 review

Disposition: **WITHHELD for NTC4, a remaining source-origin rejoin defect**. NTC1's first-fatal/bounded-read failure, NTC2 and NTC3 are corrected in the finite independent checks. No genuine durable authority, transfer or empirical release is accepted.

Exact author manifest `49dc408e23e327116d6c040631369c54f0ef0c82430b224993e4d5b8f1effa3a`, all34 listed bodies and seven declared dependencies were independently hashed. The selected module is `52858e18ce1bf01715380dc149da0e6bf95728879c5d5798c5d3b24a587360d2`. Author files and previous reviews remain unchanged.

## Remaining finding

**NTC4 — canonical dependency origin is checked only before reading.** `bootstrap_read` requires `path.resolve()==path` initially, then opens only the file descriptor and checks the file's own inode/size/mode/time against `path.lstat()` at completion. It holds no parent descriptor and does not rejoin the final canonical path. The actual function accepts this deterministic interleaving: after the file opens, rename its parent directory and replace the original parent name with a symlink to the renamed directory, then perform the real read. File inode, bytes/hash and leaf lstat remain identical; the function returns the source bytes even though `path.resolve()!=path` at return. This is a canonical-origin failure, not source-body hash corruption or an inferred malicious execution.

`check03.py` retains the actual OS-file counterexample and CHECK03.log reports it. The deliberately redirected synthetic path is under `owned-bytes03/bootstrap-parent`, linking to the sibling `bootstrap-parent-moved`; it is not an accepted repository/source capsule. A successor should hold/rejoin the original parent directory and final canonical path in addition to current file signatures, using independent first-fatal cleanup for every acquired descriptor. Executing the already captured bytes is correct but does not restore the asserted source-path origin after redirection.

## Independently verified corrections

The unchanged original reviewer script was rerun in this new review directory. BASELINE01.log reproduces all three original failures and original complete-copy controls; its fixtures are retained separately in owned-bytes01.

The corrected bootstrap rejects growth during reads at the original-size-plus-one bound and preserves the same first MemoryError object after an injected ordinary close error, with the real file descriptor closed once. It hashes and executes captured source bytes rather than rereading through the import loader. The distinct bootstrap uncertainty class is used before accepted owned_io can be imported; no authority capability is inferred from that class.

Two foreign threads now both fail before a reservation update, revoke the shared budget and leave zero commands, eliminating the demonstrated lost-update schedule. The owner is the original Thread object, not a recyclable integer. Same-thread nested reservation refusal revokes the object; even when that nested error is swallowed, the outer pre-publication check prevents committing the successor counters. Previously reserved amounts remain unchanged.

Clean-body reader-close uncertainty, reader birth failure, body failure and body MemoryError with later close uncertainty each revoke the shared Reservations alias. Subsequent reserve attempts refuse, and prior spend is not refunded. The actual root descriptor closes exactly once. A normal completed context may deliberately leave the shared budget available for the next sequential container; local-context revocation and failure-wide shared revocation remain distinct.

Independent complete original/recovered byte checks pass for score-batches (four members), raw f32 MCM output (two members) and graph-artifact/NPY companion content (three members). These are synthetic byte fixtures with no numerical-package imports or empirical array decoding. Complete metadata/headers and declared companion bodies are retained, not replaced by payload-only hashes. Activation still raises NotImplementedError.

The proposal uses `(size //32768 +1)*32768`; an exact32768-byte extent reserves65536. Independent AST readback confirms the existing Transport.get uses the same floor-plus-one block expression. Original/recovery part totals were recomputed separately. This establishes conservative prospective block arithmetic, not actual SSH command counts, framing, wire bytes, durable reservation spend or remote recovery.

PARITY02.log independently confirms inverse whole-module AST and exact unaffected existing top-level bodies, including the entire Context class. Only declared load/Reservations/open_context changes and bootstrap/import additions are needed to reconstruct original01. Other data/member and recovery behavior is unchanged.

## Preserved harness limitation and scope

CHECK02.log retains an initial reviewer harness failure: contextlib.__exit__ returns False when an incoming fatal should propagate back through a with statement, rather than necessarily raising it inside the manual __exit__ call. check03.py corrects that assertion, retains all earlier fixtures and uses a fresh owned-bytes03 tree. It verifies False is not suppression and preserves original fatal identity where raised. This was a reviewer interpretation error, not a candidate failure.

No genuine ResearchRun, Binding, Owner, held/cold capability, native unit, claim, registration, source integration, numerical fit, network, remote upload/recovery, retirement or resource capacity was exercised. No actual source/array generation occurred. The candidate remains unadmitted local preparation. Raw-f32/NPY local byte readers do not supply missing genuine held authority. The separate durable context and positive transport remain independent integration requirements. Zero bytes were freed; full55.44GB payload accounting and9.24GB nontail scope remain unchanged.
