# Independent final cold-reader disposition

Accepted for bounded cold verification of a closed archive writer through a separate fresh read claim. APR1–4 in REVIEW_INITIAL.md are resolved by the inspected delta and retained regression evidence. Earlier source, tests, logs and review remain preserved. No tests, remote operations or empirical jobs were rerun by the reviewer.

- **APR1:** The source descriptor close captures the in-flight exception and uses `_close_after_failure` when one exists. Cleanup uncertainty remains fatal, the primary operation error becomes the explicit cause, and the new read attempt records failure. The regression injects an error after a real source close and verifies the exact original transport exception as cause; it does not demonstrate recovery from a genuinely leaked descriptor or exhaustive I/O cleanup behavior.
- **APR2:** After each external lease, `live` checks both source and attempt failure-marker paths using lexists. Both dangling source marker variants now refuse before the instrumented next transport call. Final full source and new-read checks remain in place; this correction prevents premature additional transfers rather than repairing a previously false final acceptance.
- **APR3:** After capacity preflight, a fresh lease and callback-free full source check precede the exclusive claim. Revocation injected at the capacity boundary refuses with no attempt created. This is a sampled authority/source boundary, not an atomic filesystem or liveness guarantee during an arbitrarily long scan.
- **APR4:** The minimum logical metadata allowance is now `(3*max_chunks+8)*META_LIMIT`. This conservatively covers the declared successful child receipts plus terminal/failure/cleanup records. The old margin4 is explicitly rejected before claim. The test checks policy admission; it does not generate every maximal failure-record combination or measure physical storage consumption.

Saved review-red01 reports **5 failed, 17 deselected in0.59s** on preserved reader-check01.py. The corrected combined check02 reports **117 passed in9.55s**, comprising22 reader cases and95 prior archive checks. The delta, fault injection points, cause assertion, before-transfer trap and before-claim absence assertion were inspected independently. No combined-suite timing is used as a throughput or scaling estimate.

Acceptance covers exact trusted completion/owner/scope/archive-policy joins, canonical ordered metadata and retained inventory checks, every remote chunk fetched into a fresh disposable cache and replayed, and final source/new-read evidence checks after the last external callback. Source evidence is read-only; duplicate read identities refuse. Failed attempts retain their metadata and any payload not already deliberately disposed by a successful child consumption. Previously disposed caches are not promised to reappear after a later failure.

The tests use synthetic filesystem transport and no-op or injected leases. No real network, current-owner/scientific admission, checkpoint-body or score-stream join, writer reopening, generic archived-stage selection, empirical source eviction, physical quota, cumulative cross-call budget or global RSS claim is accepted. Source policy and completion authority remain caller responsibilities. Concurrent adversarial filesystem changes and loss of future remote availability remain outside the sampled verification contract.

Inspected SHA-256:

- archive_pair_reader.py: `9f452da351a0d2352d8b47120e4a6a6956692a752876e543faef4bb60a76b77d`
- test_archive_pair_reader.py: `77c2a8ba7d06ab4024ab92da170d303a0819093759dc37b689631772d0441f11`
- reader-check01.py: `9d7539cd207d18fd53db9ff4d7e5aa47158869e872aed2f84b0ecdf4562387bd`
- test-check01.py: `45118ba9b871b60976726e2f15d7bb1c3b900bd13ba23f718e1ef22ea360fe6a`
- review-red01.log: `edc1900856a176a28f3c7dd4a3eda31147b91a026b67d7913013ad8dab004722`
- check02.log: `85c57d364f66dabfe5dff2daa3103a92cdc3de3ad80f40dde9b8a7e54dfc4fa4`
