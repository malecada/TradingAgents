# Independent terminal review — closed graph06 ledger preservation

Decision: accepted. The successful terminal and compact restoration evidence consistently support preservation and eviction of the exact single closed graph06 aggregation ledger. This is an independent reconciliation of the guarded producer's full-body checks, not an independent remote download or body rehash. No raw, graph-array or SQLite body was opened during review; no job, test, transfer or retry was executed.

## Identity and source closure

The frozen HEAD remains `34babb067f65794fbc8c67ed007a836c17cdfb5a`. All 30 original and 37 contextual bindings, comprising 63 unique paths, were independently checked and matched. The connection entry was checked by hash only. The original graph06 claim, terminal, owner, guard and artifact-index hashes in the manifest remain unchanged. In particular, the index retains SHA-256 `de5d8cd7872125580119710590a0d64426eede3c40279e5fd690f10900adcacd`.

The sole body is `research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-graph-resource-20260930-06/aggregation/ledger.sqlite`, 3,208,413,184 bytes, SHA-256 `b74170043c357dc5ccf3e40c5ca9aa4be49d73ec28c326e84d0284e2678dd7f2`. Its recorded original stat identity is identical across the manifest and per-file records. The remote object is `research-backups/onchain-paper-replication-2026-09-24/closed-ledger-offload-2026-09-30-04/00.bin`, with restoration metadata in the same prefix.

## Receipt reconciliation

The manifest and recovered manifest are byte-identical. The four per-file verified, evicted, restoration and recovered-restoration records are byte-identical, and the original-path `.remote.json` sidecar contains those same bytes. Each agrees with the exact manifest row and records successful full-body roundtrip verification. The retained body transport receipt independently records the expected and received 3,208,413,184 bytes, return code 0 and complete status. Under the unchanged reviewed helper, the verification record is published only after body size/hash agreement and successful restoration-metadata roundtrip; source removal follows durable verification and sidecar publication plus source revalidation.

The completion candidate, recovered completion and local completion are byte-identical. Their denominator is exactly one file, totaling 3,208,413,184 bytes. The recovered completion transport receipt records all 1,160 expected bytes received successfully. Local `complete.json` publication follows that metadata roundtrip. The original source path is absent, including no dangling symlink; the successful `00-recovered.bin` scratch is absent. Original graph arrays, raw stores and the historical artifact index were not altered by this preservation scope.

| Evidence | SHA-256 |
| --- | --- |
| `manifest.json` and recovered manifest | `3b97e8e627a72a25bd640156fc22d8e5110ae2faf8079b0c9625c3c4ee2519fb` |
| `guard01/final.json` | `41493f0d5897b6480bf270176f6f1a1a4e6b52b28b078e937f63abdfd9c8d207` |
| Completion candidate, recovered and final completion | `ffd04e684b1d2374919cb08caebd5fab8a943c1a9ae7d0fb2c65e46b873fd08e` |
| Four per-file records and original-path sidecar | `ec62d2bc9734a9990df7e358d725bc2f0cd72c9a0f43529997599de1a0b1a664` |
| `closure01.json` | `dadb1cd20767f43c7ac9511c403c7abb3f3612c85db382eaa2ff21f683331723` |

## Guard and ownership

The final receipt identifies the exact reviewed `offload.py --worker` command, monitor 947069 and unit `onchain-replication-ec563a3ff94d4c4b85fc2a58d8c7ac6f.service`. It reports complete, child exit 0, cleanup verified, no limit reason and 1,978.642813917002 seconds elapsed. Independent `/proc` and cgroup checks confirm the monitor and exact cgroup are absent. The saved child-exit receipt also reports exit 0 without a snapshot error; the empty child log is not used as success evidence.

Sampled peak memory was 203,157,504 bytes. There were 48,402 high-throttle events and zero max/OOM/OOM-kill events, not zero memory events overall. The guard retained 256 MiB maximum, 192 MiB high, zero swap, 3 GiB reserve, 3.5 GiB startup, 10 GiB disk floor and 14,400-second wall limit, with two-CPU affinity. The transport deadlines and exclusive remote attempt remained those previously reviewed. The peak is sampled cgroup evidence, not a cold-cache requirement or a universal memory bound.

## Consequences and limits

The observed closure free-space snapshot was 22,151,974,912 bytes; this is historical host state, not a future capacity reservation. Graph08 gate generation may now bind this actual accepted preservation closure, but admission, commit/source verification, owner checks and fresh resource checks remain separate prerequisites. No new scientific claim, empirical budget expenditure, financial result or graph-content verification follows from this storage action.

Future consumers that need the original ledger body must restore to a new temporary file, verify the recorded byte count and SHA-256, then restore the absent original path without rerunning the historical job. Compact receipts establish the producer's successful remote recovery at this attempt; this review did not re-query current remote availability or independently repeat that transfer. The original manifest's preparation wording remains immutable historical text and is superseded operationally by the actual terminal evidence, not rewritten.
