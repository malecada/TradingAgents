# Integration review correction scope

The accepted transport source and closed check03/check04 attempts remain unchanged.
Candidate03 preserves the source and four-cell test assertion used for check04.
Check04 closed with 12 passed in 366.83 seconds, session30978, exit0.

Two remaining integration corrections were authorized by the coordinator:

1. On failure, an attached still-open archive ledger must receive a poisoned
   close under its original captured owner transition. Original claims and spent
   reservations are retained. An already-closed ledger is never rewritten;
   invalid authority refuses unsafe mutation. All independent failure-evidence
   actions are attempted. A fatal primary remains fatal and retains its identity
   even when a close is uncertain. An ordinary primary cannot hide fatal cleanup.
2. Successful terminal validation must derive the exact start/closed metadata
   from original ledger identity and original terminal spending authority.
   Changing closed.json together with the mutable runtime expected-byte map is
   insufficient authority. The check remains local and callback-free.

review-red01 freezes the package and adds three negative assertions against the
uncorrected candidate: coherent closed-metadata tampering, an open ledger after
late MCM failure, and fatal-primary preservation when poisoned close raises.
The complete archive positive must be checked with a fresh synthetic fixture
following correction because its post-close verifier changes. Closed local-route
and unrelated public archive checks need no contextual repetition.

The injected in-process route remains the scope. job_payload does not yet pass
archive_transport; registered outer dispatch, SSH execution, physical workflow
accounting, empirical workloads and paid/network activity remain untested.
