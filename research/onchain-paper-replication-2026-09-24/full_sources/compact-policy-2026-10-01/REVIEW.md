# Independent compact policy review

Acceptance withheld pending two validation corrections. Review was read-only except for this note; no tests, numerical jobs or empirical runs were executed.

## Material findings

**CPOL1 — Capacity validation can spend an effectively unbounded time reducing an already invalid count.** `tradingagents/research/onchain_replication/compact_policy.py:27–35` checks accumulated overflow only after the loop. All initial integer checks admit `sample_count=2**41-1`, `size=partition_threshold=2**40-1`, `partition_size=2**40`. The first iteration already produces pair/matrix counts beyond the final bound; subsequent reductions mostly remove one item, requiring approximately `2**40` iterations before rejection. Check accumulated bounds inside the loop, and establish a bounded depth or equivalent arithmetic reduction for slow valid-count cases. A prospective metadata validator must refuse without performing a workload-sized loop. This counterexample is reconstructed from the recurrence, not executed.

**CPOL2 — Policy validation omits the score writer's chunk-count limit.** At `compact_policy.py:69–73`, the computed MCM chunk count is never checked against `score_batches._shape`'s `10**12` filename capacity. For example, keep the test candidate's pair/schedule settings, use `pairs=10**12+1`, `score_chunk_cells=1`, and log limits `chunk_events=10000`, `max_events=2*pairs+10`, `max_pairs=pairs`, `max_logical_bytes=max_events*168+16384`; set `max_retained_logical_bytes=10**18`. These quantities satisfy the displayed policy/log arithmetic, but construction of ScoreBatches rejects the resulting `10**12+1` chunks. Enforce the same chunk-count limit before accepting the policy and retain a targeted regression. This is a policy-to-primitive compatibility error, not a missing empirical resource allowance.

## Checks that are supported

The directional recurrence matches the workload's partition sizes and reduction count: seven samples, size two, partition four gives 30 directional occurrences and 41 matrix entries over two levels, before any identical-subset reuse. Both directions are counted by `n*(n-1)`. The explicit backend differs from the existing native selector, and returned `execution_admitted=False` correctly limits scope.

The per-pair reservation matches CompactMatcher's constructor. Global checkpoint bytes reserve each permitted checkpoint body plus its two compact metadata records. Log allowance delegates to the actual fixed-record validator. For MCM, 80 tail bytes plus 8 batch bytes per occurrence, four metadata caps per chunk, and four stage metadata caps agree with the currently retained stream structure. The combined total includes log and checkpoint budgets; numerical workspace, filesystems and outer execution costs remain excluded. These are logical upper allowances, not measured bytes, RSS or completion guarantees.

The saved red log reports ten missing-module failures in 0.34s; the saved green log reports ten passes in 0.30s. The tests cover one hierarchy count example, an unpartitioned example, reservation arithmetic and eight malformed/underreserved variants. There is no explicit zero-pair dictionary case, multi-level count reconstruction, slow-reduction bound or excessive-score-chunk regression in this version. Static inspection indicates the one-sample/size-one dictionary case has zero pairs and one matrix entry, with conservative positive log/checkpoint allowances, but it was not established by the saved test run.

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| `compact_policy.py` | `81c7b28e1736410ec170453d102b5dab0700e1d51b0e9dfc415ee7a133675e22` |
| `test_compact_policy.py` | `dd468bc786d0f401795c25a80c16edee78cb5a4e703f6a7624a26b0b75452074` |
| `red01.log` | `2e73a115c7c9b90fe06b70a568cb955de890de6d587c071c0902319f0944988a` |
| `check01.log` | `9d6385e37c1136c7d5a183f08b3fb0422b229c37d60fcdfe1ba24b87abebacf6` |

These identify reviewed current files and saved logs, not a complete execution-time dependency freeze. No registered selection, scientific outcome, successor reuse or resource-pilot admission is established.
