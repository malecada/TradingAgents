# Independent failed offline01 closure review

Accepted as a fully terminated FAILED engineering verification with cleanup and preservation verified. The source freeze may safely release for subsequent engineering. This decision is not a suite pass, numerical/empirical release or permission to reuse offline01. Only this review was written; no tests/jobs, source edits, commits, empirical array/raw-body or SQLite reads were performed.

## Actual outcomes and retained failures

The raw child.log contains both completed summaries:

| Batch | Failed | Passed | Skipped | Passed subtests | Seconds |
|---|---:|---:|---:|---:|---:|
| Standard | 35 | 2739 | none reported | 97 | 1096.39 |
| Neural | 18 | 855 | 2 | 12 | 798.71 |

All53 failed node IDs and all53 trace sections remain in child.log. `closure01.json` retains exactly those53 failed IDs in their original order and the correct summaries. Its six receipt hashes independently match the saved files. No failures were omitted from the closure denominator, reclassified as unavailable or excused by the successful cases.

The35 standard failures share the historical hash-audit20GiB-plus-margin refusal, as independently reviewed in the separate fixture diagnosis. Seventeen neural trace sections show `weight workspace breaches disk reserve`, including one test that instead expected a neighborhood-capacity message. The remaining neural failure is `KeyError: 'proposed-11'` in the registered sampler-forwarding test. The latter is a downstream missing-result symptom; this closure does not establish its underlying cause or claim the proposed disk fixtures resolve it. Each failure remains subject to diagnosis and corrected admitted tests. Neither focused owner tests nor isolated candidate acceptance substitutes for this failed broad outcome.

## Source and terminal ownership

At2026-09-30 18:17:27UTC, HEAD was `f6aa6d006f026e2d994181fe8beef9b14ea7b6b3`. All1217 frozen bindings independently matched both current bytes and that commit. The raw source-bindings manifest matched its committed bytes and SHA-256 `ad1669e2a2fce5354c5ef1b4961bc6e3c8635ba7cc3e0599c1acca5121b74c6a`. Filesystem/AST reconstruction independently confirmed exact86 package-source and265 named-test inventories. These checks precede release of the freeze; later deliberate engineering changes must be recorded under a new closure rather than changing this historical assertion.

Final and live receipts are byte-identical terminal snapshots. Their owner identity names `matching-owner-integration-offline01`, the actual source above and exact manifest hash. The command is the reviewed repository `.venv/bin/python -B scripts/verify_offline.py`. The final phase is failed, child_exit_code1 and cleanup_verified true. child_exit.json reports workload_pid457456, exit_code1, reason `workload exited` and no snapshot error; its terminal memory snapshot equals the final receipt's snapshot. cpu_ready identifies wrapper457453 and CPUs0–1; release records kernel controls verified. These identities match the independently observed live review.

The actual monitor456207/start tick789130 is dead: its /proc directory is absent, as are known wrapper457453, verifier457456 and standard child457457. The host boot ID still matches the receipts. The exact cgroup for `onchain-replication-75a7d87c61cb47a7b3ec3eb4c8eb91d7.service` is absent, and an independent systemd query returns no active or activating replication units. Final cleanup records stop return0, empty ControlGroup and failed/exit-code unit state. A retained failed unit status is consistent with workload exit1 and does not imply a remaining worker.

Elapsed guard time is1898.525613349seconds, below3,600seconds. Peak sampled cgroup memory is2,887,884,800bytes. Terminal high/max/OOM/OOM-kill/group-kill counters are all zero, with no elapsed-time kill; failure is the child/unit exit, not a reported resource limit. Retained kernel controls are3GiBmax,2.75GiBhigh and zero worker swap; the two-CPU affinity policy is unchanged. The terminal memory snapshot retains2,390,646,784bytes before cleanup, including cache; cgroup absence establishes subsequent cleanup rather than interpreting that snapshot as current live usage. Final available disk19,870,089,216bytes and host RAM10,169,872,384bytes exceed the active10GiB/3GiB floors. This does not make the historical20GiB fixture checks pass or erase their failures.

## Exact retained closure

| Artifact | SHA-256 |
|---|---|
| `closure01.json` | `885ddd81f421bebca53b47d33eb908f6861c1f55fc952534b21ccbd31ddbb00a` |
| `offline01/child.log` | `1637cfb0215dc2a791536ce1a4163edeca9aeb9b9cb71e60d8b3b954c3d96518` |
| `offline01/final.json` and `live.json` | `a54075360c93cec8381740d5c4882b1e0629f8ce3e2061c90d0acf275a1f49c7` |
| `offline01/child_exit.json` | `8c7540ca67a94d6709fdac6a99fbb16585aaf0311061741e63001db2ae7f69c1` |
| `offline01/cpu_ready.json` | `9994dba8bd84c9050e402ffe4b9bc22fa5c164b9cb3fc1e73b9a6157be5d429f` |
| `offline01/release.json` | `82560e2694628ad002f9cc4b76fe2cd7b1b545cc825269f01057f04c6fe268b5` |

Preserve these receipts and the original source/binding/review records unchanged. A later corrected broad verification requires a new unused identity, reviewed exact source closure, commit/push and fresh owner/resource checks. Historical resource policies, empirical budgets and failed identities remain intact. No numerical continuation, strategy validation or financial-fit claim is established by this closure.
