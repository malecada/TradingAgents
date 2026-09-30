# Independent terminal review — package offline01

Accepted as a successful single invocation of the named offline engineering target on source commit `5619467d558f2ff698a8e3084f04920a950245ee`. No source, outcome-count or ownership mismatch was found. This closes verification of the maintained pair component; registered matching integration and empirical admission remain separate.

The raw child log reports 261 reviewed modules, split into 186 standard and 75 neural modules. Standard execution passed 2,774 tests plus 97 subtests in 1,059.65 seconds. Neural execution passed 785 tests with two skips in 520.74 seconds. Thus the result is **3,559 passed, 97 subtests passed, two skipped**; subtests are not counted again in the 3,559 total. The log explicitly excludes legacy/unreviewed modules. This is the named reviewed target, not an unrestricted legacy-suite result.

`offline01/final.json` reports phase complete, child exit 0, cleanup verified, no limit reason and elapsed time 1,583.9885179120029 seconds. `child_exit.json` independently records workload exit 0 and no terminal snapshot error. The sampled cgroup peak is 2,952,790,016 bytes. There were **243 memory.high events**, with zero memory.max, OOM, OOM-kill or group-kill events, from an all-zero initial counter baseline. This was a successful run with throttling, not a zero-pressure run. The sampled cgroup peak is neither process RSS nor a cold-cache requirement or universal peak bound.

The recorded command is the repository `.venv/bin/python -B scripts/verify_offline.py`. Guard ownership binds kind `matching-package-offline01`, the exact source commit and manifest SHA-256 `2262884a7c96159779cfae45b2c4b2707852471dfed63f8ce25f41b04e355697`. Final controls retain 3 GiB memory.max, 2.75 GiB memory.high, zero swap, 3 GiB host reserve, 6 GiB startup RAM, 10 GiB free-disk floor, 3,600 seconds and CPUs 0 and 1. The prior independent live review observed the exact monitor start ticks `10208897` and live CPU/kernel readback; the terminal review does not fabricate a new live observation after exit.

At the independent closure check on 2026-09-30 at 13:53:34 UTC, `/proc/1226864` (monitor) and `/proc/1227063` (workload) were absent. The recorded cgroup was absent. Unit `onchain-replication-0005b04fe8cc429586fb46e8a233ac5f.service` reported inactive/dead, and no active or activating replication unit was listed. The retained final and live receipts agree on terminal phase and ownership.

All 178 current file hashes were independently checked against the manifest and against committed bytes at the unchanged actual HEAD. The manifest itself equals its committed bytes. All six compact evidence hashes listed in `closure01.json` were reconstructed and matched, including the raw test log, final, child exit, dispatch and earlier live review. The closure's aggregate values agree with the original receipts. `dispatch01.json` records matching remote commit and a successful runtime check; no network query or runtime rerun was performed in this review.

The exact retained hashes are:

| Evidence | SHA-256 |
|---|---|
| `source-bindings.json` | `2262884a7c96159779cfae45b2c4b2707852471dfed63f8ce25f41b04e355697` |
| `offline01/final.json` | `a6aa4aff5b108b46dcd4ccb1feb2a97e4e2e2a1749101a4a2164ad3db4887872` |
| `offline01/child_exit.json` | `74af6036d72fb13730da162dfc971ffbf7802470c266c052157a911be636d1ab` |
| `offline01/child.log` | `d8226fce45ef7893313bfcbb0227f23224a04a23272225806810d7ced9415278` |
| `closure01.json` | `9cee514b1cadd466ea616d31ac4006acd0ea96f21feb04b67284a29dc34118a7` |

The maintained modules preserve the accepted scalar implementation and have normal-import synthetic verification. This result does not establish actual claim-derived pair ownership, journal publication recovery, dictionary directional continuation, MCM partial rows, Torch numerical equivalence, full real-neighborhood feasibility or financial performance. The open requirements in `REGISTERED_INTEGRATION_REVIEW.md` remain open. Graph10 still requires its independently reviewed complete-package source closure before admission; this offline run does not consume or adopt its proposed empirical allowance.

Only compact receipts, logs, source hashes, committed bytes and process/cgroup metadata were read. No tests, financial experiment, profile or numerical artifact verification was repeated; no raw, SQLite or array body was opened. Only this review was written.
