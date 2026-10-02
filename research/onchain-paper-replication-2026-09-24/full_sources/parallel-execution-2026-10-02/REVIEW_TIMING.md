# Independent bounded timing review — October 2, 2026

Verdict: the retained evidence supports a single matched-fixture observation:
baseline04 took 57.81 seconds wall time and candidate05 took 26.33 seconds,
with the same synthetic test passing in both. The observed reduction is
31.48 seconds (54.45%); the elapsed-time ratio is 2.196. This is not a
statistical benchmark or a general training-speedup claim.

## Independent reconstruction

Both manifests identify base commit
`b449a2a59549ea500790e95df1615df21b753401` and the same eight exported paths.
A fresh read-only `git archive` reconstruction of those exact paths produced
SHA256 `6692590b765a5bafc9aec0f602517ca4617c542c627de641bb6d3afd35bc1639`,
matching both manifests. Its 430 regular files were compared byte for byte
with both retained snapshots. Each snapshot has exactly those 430 files, with
no missing or additional regular files. Baseline04 matches every archive file.
Candidate05 differs only in `tradingagents/research/admission.py`, exactly the
declared overlay.

The candidate overlay SHA256 is
`585d66f526d88f8488c6efcc4989a09328006e393566a596fe9e95c6c7f60cfd`.
It matches the current source and the independently accepted batching review.
The baseline admission SHA256 is
`61d7f91a331a95c3f00b56ba35daab63d18ab903ee0ea64a0eada3f9a7871e4f`,
the original implementation retained in the batching evidence. No test source
or configuration differs between these two snapshots.

Both saved time receipts name the same pinned interpreter and command:
`python -B -m pytest -q tests/research/onchain_replication/test_archive_owner_stage.py::test_actual_reserved_stage_read_joins_writer_once[writer_matching] --durations=5`.
Neither command invokes a profiler. Both time receipts record exit status 0;
both pytest logs identify that exact test and one pass. Inspection of the
retained test shows assertions for the writer/read join, one transport read,
reader reservation, completion reference and owner-ledger close.

| Measurement | baseline04 | candidate05 |
| --- | ---: | ---: |
| External wall time, seconds | 57.81 | 26.33 |
| Pytest elapsed time, seconds | 56.57 | 24.98 |
| Test call, seconds | 42.16 | 16.66 |
| Fixture setup, seconds | 12.27 | 6.20 |
| Maximum RSS, KiB | 710376 | 712008 |
| Time receipt exit status | 0 | 0 |

Maximum RSS increased by 1632 KiB in this observation; no memory reduction is
supported. External wall time and pytest time are different measurements and
have not been combined or substituted for each other. Historical profile03's
instrumented 118.12 seconds is not used as the baseline.

## Limits

The coordinator reports sequential execution. These retained stdout/time
receipts do not independently capture the complete environment, host workload
or cache state. One observation per variant cannot quantify variance, remove
run-order effects or isolate the causal contribution of batching from changing
host conditions. The source isolation and identical fixture are independently
verified; repeated trials, broad-suite behavior and full workflow/training
performance are not established.

This closes the previously untested exact-fixture observation for the accepted
batching overlay only. It does not accept producer-to-terminal integration or
make a financial, market-data, external-transfer or empirical-admission claim.
No benchmark, test or financial experiment was rerun during this review; only
the retained evidence and immutable Git source were read.

## Evidence identities

- baseline04 manifest: `c382645de24ff1fa249c8d43db43b41dbe4c46937cb2dcb063b2168ee0f8d5dd`
- candidate05 manifest: `8355954cf1a01b04d3e1804ef0cf2b7e3e34c9f61537d17403b982087eb113d2`
- baseline04 log: `00323f8b23aa66684a12dd9437733d9e0696d1bb62063152d282281f2e803f59`
- candidate05 log: `4abfa3c2d1a43ccdd70772b491f81d8bce6bfa4093f39722bd128a5e944cbc34`
- baseline04 time: `4838fb6cb93256ca507f5a7c83a0d23be5e91020f205f7d2fb92e9e3d722476c`
- candidate05 time: `b405bd8b48304697d01b57ba13357eec06dda91115dd0fb877584db73ddf8299`
