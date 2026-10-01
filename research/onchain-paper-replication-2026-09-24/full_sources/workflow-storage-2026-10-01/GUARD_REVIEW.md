# Independent sampled-storage guard review

Accepted for the bounded optional guard/job integration reviewed on 2026-10-01. No blocking correctness finding remains in this delta. This is not a hard filesystem quota or empirical resource admission.

`resources.guarded_run` validates and pins the storage root before reserving a receipt, checks storage before dispatch, before worker release, at monitor boundaries, and after owned-unit cleanup before final disposition. A breach enters the existing failure/cleanup path. Its first partial accounting observation and error remain in the receipt even if a subsequent observation succeeds; cleanup cannot turn the run back into a success. The final scan cannot prevent growth caused by later receipt writes, which the recorded qualification explicitly excludes from the sampled guarantee. Successful-sample peak counters must be interpreted together with the separately retained breach counts, not as a complete peak allocation measurement.

`job.resource_policy` accepts only the existing field set or that set plus the exact storage budget schema. The root must already be canonical and inside the admitted workspace. The monitor forwards the selected policy unchanged. Existing worker and matching-owner checks compare every registered policy field, including the nested storage budget, against the live receipt. `job.required_sources()` includes the new package module through its package inventory. This validates the selected subtree, not that the subtree contains every workflow output; a prospective registration must explicitly establish that coverage.

Saved evidence read without execution:

- `guard-red01.log` is an inventory refusal before the dated test ran. The maintained test imports the existing admitted `test_resources.mock_unit`; it does not bypass that inventory restriction.
- `guard-red02.log` retains the three unsupported-keyword failures. `guard-check01.log` closes with 42 passes in 1.62 seconds, combining the three new cases and existing resource tests. The new cases exercise no-dispatch startup refusal, post-release breach with owned cleanup and durable failed receipt, and successful observation.
- `job-red01.log` retains the two new policy failures. `job-check01.log` closes with 46 passes in 16.67 seconds, adding nested-root acceptance and foreign-root/malformed-limit refusal to existing job coverage.

These are mocked systemd/kernel tests with real tiny filesystem observations. A distinct late change introduced specifically during cleanup is not a dedicated regression; the post-cleanup call was checked in source. No actual OS probe, full registered storage job, concurrent growth ceiling, stalled-syscall deadline, full offline suite, financial experiment, or numerical data validation was performed by this review. The logs explicitly qualify the reviewed profile's withheld historical files.

Exact reviewed SHA-256:

| File | SHA-256 |
|---|---|
| `resources.py` | `3962f2d5abd1e29e53108b76f3b14cebed9cb8217ee4b73fa4fe0bd2734f05ef` |
| `job.py` | `3716646a0b753c72854982b88432aed867e0561157cb117b7a2e5bcdae55124f` |
| `workflow_storage.py` | `a0b1bd5e3f73f22f3c5922740a8bddde0437c3c635ea372a6853d4d504e7751f` |
| `test_workflow_storage_guard.py` (final five cases) | `c53859f6fee7480d1cdcf01a48564830d404a5420fbbf80e1020655a130f1cb3` |
| `guard-check01.log` | `22d739b899d00fcba1b4ca41fc18883eb4d25aa8946eca2e2b73a738dfdba189` |
| `job-check01.log` | `ec6adba3f15f0033971b665ee76fbfe0462ff854e22d0c78959dae86ab0d43a1` |

The final test file includes the two job-policy cases added after the earlier three-case guard run. No claim is made that all five cases ran under that earlier identity.
