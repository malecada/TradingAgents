# Independent cold-history metadata review

Acceptance withheld for the bounded read-only component pending the findings below. This does not reject the already accepted guarded synthetic run; it concerns the new historical certificate reader. Only this review was written. No tests, old jobs, numerical arrays, checkpoint payloads or registrations were executed, reread or changed.

Reviewed terminal.py SHA-256: `4a4fdd4ca04a005896153ee27baf92e3fdfd8aa3119a3fa35c390d931c34d1ee`; test_terminal.py: `6e32e9ef9e08c01b150e05f7d4f3d294387bdb8d8f8bf05ffb9364c1f7f87895`. The saved check02 log reports six passing methods in0.041s, SHA-256 `f5b2a087a6b782bb5a6e40e6ffe122c9cb2a042542b7c41eff2d64e91c97de5e`. check01's observer-reconciliation failure remains preserved, SHA-256 `e30b9d4ddfe8d4ff8be40f1e9a9568eb81cf2386ce577ec8207033395803a40f`.

## CH1: caller metadata limits are not bound to the actual read

terminal.py lines31–36 charge a preliminary path.stat extent, then matching_ancestry._read restats and reads with its fixed2MiB global limit. The preliminary signature is not passed through. A file grown/replaced between those operations can exceed max_metadata_bytes or max_total_bytes yet be accepted and undercounted, particularly launch/owner metadata whose expected hash is established by this read. Once recorded, subsequent reads skip the caller's size/accounting checks. The final signature check pins the later read, not the original admitted extent.

Use a cap-aware reader that binds the admitted signature/extent to the opened descriptor and reads no more than the caller's bound plus a refusal byte. Retain the actual unique-file byte count and per-file cap for later checks. A deterministic tiny-file growth/replacement injection between budget admission and read should prove refusal without exceeding the requested read allowance. The existing tests only pass a static limit1 and do not exercise this boundary.

## CH2: output inventory is neither streamed nor rechecked at return

terminal.py lines55–59 use Path.iterdir. In the pinned Python3.13 pathlib/_local.py implementation, this constructs a list of all entry paths before returning its iterator, so the loop's bound does not bound enumeration memory. Use os.scandir with immediate foreign/excess-entry refusal and explicit directory identity/containment checks.

The output inventory is checked only before the remaining metadata reads. The final loop rereads known records and checks the failed marker, but does not detect a new foreign/pending output added during those reads. Repeat the exact bounded inventory at the final boundary. Likewise repeat same-boot monitor/cgroup observations after the final metadata checks if the returned certificate claims their current death/emptiness. This does not require atomicity against continuous mutation; it closes changes occurring inside this finite inspection sequence. Tests should inject an extra output and a changed cgroup observation at the late-read boundary.

## CH3: unavailable dispositions may omit their reason

terminal.py lines49–52 accept any unavailable cell without checking its reason. The maintained job._terminal contract requires a reason for every unavailable disposition. A completed historical denominator with unexplained unavailable cells should not receive historical_run_verified. Require a nonempty reason for each unavailable row and explicitly validate integer counts/schema where this reader makes corresponding claims. A small decoded-record counterexample is sufficient; no financial job is needed.

## Supported scope and evidence limits

The implementation correctly joins the pinned claim, registration experiment, lifecycle terminal, exact output names/hashes, launch/owner, worker command, canonical cgroup/boot, final/live guard and observer evidence. The corrected all_cells_complete comparison now agrees with terminal unavailable_count. It returns explicit false flags for current-run admission, native feature verification, source compatibility and array reads; these limits are appropriate.

No additional demand is made here for the deferred seal/publication/scientific/source/member/current-guard layers. Those remain mandatory before constructing PreparedFeatures or permitting native reuse. Historical guard policy/resources are not compared to execution_job in this primitive; future guard/input admission must provide that join before asserting registered resource compliance. Successful historical metadata inspection alone must not become an implicit producer, financial or resource approval.

Tests inspect actual retained tiny synthetic metadata. Several negative semantic cases mutate decoded objects returned by a mocked metadata reader while retaining original hashes; these exercise joins, not independently rehashed filesystem construction or hash-reader integrity. No complete source-closure manifest was supplied for this component, and none is inferred from six passing methods. Preserve this review and the current source/tests/logs before correcting the new reader boundary.
