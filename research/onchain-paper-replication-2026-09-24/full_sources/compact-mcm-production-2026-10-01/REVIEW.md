# Independent final review

Accepted for bounded current-owner required-graph MCM production from an actual admitted compact dictionary. No remaining material blocker was identified in the reviewed implementation and cleanup corrections. This acceptance supersedes the withheld disposition in `REVIEW_INITIAL.md`; that note and all preceding failed evidence remain applicable historical records.

Review consisted of independent source, diff, test, raw log and hash inspection. No test, empirical job, numerical artifact replay or financial experiment was run by the reviewer.

## Accepted contract

`compact_mcm.produce` holds the actual owner's nonblocking transition lock, checks the actual `compact_dictionary.Produced` chain, derives the selected required graph from Training ancestry, and binds graph/node order, dictionary identity, ordered motifs, matching configuration and backend to the same workload hash used by the admitted array-neighborhood kernel and score stream. Registered MCM numeric, cell, metadata, pair and output reservations are checked before the MCM attempt/stage is consumed.

The actual kernel calls the durable score stream wrapping CompactMatcher and the unchanged numerical checkpoint engine. The producer requires exact row, cell, stream/log comparison-count and float32 byte accounting. It pins the kernel matrix before external completion/seal callbacks, seals using the stream terminal reference, publishes through the registered output route and compares every saved float32 byte with the resident matrix. Final checks rejoin original ancestry, resident matrix, completed stage identity/inode/exact inventory, producer receipts and saved output evidence after external callbacks.

The publication refactor preserves public locking and moves the same bodies into private lock-held helpers. The important callback-free wrapper verification still occurs after the nested mapped-reader exit. The producer holds the required lock for the private helper calls.

## CMCM1 and associated outer cleanup paths resolved

The shared score-storage `CleanupFailure` derives directly from `BaseException`. Independent owned closes are attempted once; uncertainty is fatal, primary failures are retained as causes, and terminal state does not imply successful cleanup. Tail and batch construction/terminal paths use this contract. Stream construction, callback failure, finish and close preserve it while attempting remaining children/root cleanup.

PairLog construction/terminal/close now applies the same contract. Rotation removes the old chunk descriptor from owned state before its single close attempt, so ambiguous descriptor integers are not retried and no next chunk is opened after failure. The producer retains fatal log-terminal errors even if subsequent close is a no-op.

The producer's final own descriptor close is fatal, cannot skip transition-lock release, and poisons the owner on success-path cleanup failure. Best-effort failure marking uses a newly opened descriptor joined to the original attempt inode; it does not retry the ambiguous old descriptor. Existing completion/output evidence is retained if this produces a complete-plus-failed conflict. The fresh failure-marker descriptor and other explicit new-producer descriptor closes use the fatal helper as well.

The injected tests deliberately leave specified descriptors unreleased and clean them only in the fixture teardown. The final log-terminal integration case instead raises the fatal signal after real log close: it proves propagation, not a leaked-log integration fault. Generic I/O helpers and all predecessor producer cleanup paths were not broadly redesigned or exhaustively fault-injected. This acceptance does not claim universal cleanup coverage across the whole future pipeline.

## Saved evidence inspected

| Evidence | Observed result | Interpretation |
| --- | --- | --- |
| `check01.log` | 9 passed, 499.50 s | Initial producer suite before cleanup corrections. |
| `publication-check01.log` | 3 passed, 3 deselected, 79.54 s | Public publication positive and both nested-exit regression paths. |
| `red02.log` | 8 failed, 1.03 s | Tail/batch/stream cleanup defects reproduced. Original regression fixture retained; later fixture tracks descriptor ownership intervals rather than conflating reused integers. |
| `cleanup-check01.log` | 45 passed, 4.97 s | First cleanup correction and existing primitive suites. |
| `check02.log` | 3 passed, 7 deselected, 188.46 s | Actual MCM parity, ordinary second-pair failure preservation and fatal nested tail cleanup through producer. |
| `red03.log` | 6 failed, 18 deselected, 123.92 s | Four PairLog cleanup paths and final producer-root close on success/failure reproduced. |
| `cleanup-check02.log` | 59 passed, 1.44 s | Twelve cleanup cases plus existing pair-log/tail/batch/stream checks on corrected primitives. |
| `check03.log` | 4 passed, 9 deselected, 258.46 s | Final actual MCM positive, both producer-root close cases and fatal log-terminal propagation. |

There was no combined final 13-case producer run. Earlier refusals and mutation tests remain evidence for their recorded versions, alongside the inspected narrow cleanup changes. The positive compares each actual MCM float32 cell with the scalar reference using the produced dictionary and original graph. Saved mapping equality is checked by the producer itself. These small fresh registered fixtures use mocked guard surfaces and inherited supplied-population limitations; they are not full-size or independent financial observations.

## Limits

This component does not select a native producer, append native feature events, admit a complete representation, provide cold/successor reuse or grant empirical execution. Existing sampler/sample/dictionary provenance is consumed through its actual predecessor chain; complete calendar/exclusion coverage and reconstructed price/label validity remain separate obligations.

The numeric allowance covers the kernel array-neighborhood buffer and resident float32 matrix. Parent/sample/dictionary arrays and dictionary readback, matching and stream scratch, Python/validation/clustering objects, mapped-page residency and process RSS are excluded. Logical metadata/pair/output reservations are not physical quotas, runtime feasibility or full-workflow storage admission. No full-fold scaling or economic result was tested.

## Independently checked final SHA-256

| File | SHA-256 |
| --- | --- |
| `compact_mcm.py` | `21128e2f01a005ccc4de61da6d90c844c8eb9e2931f5ed34065a82146afbf7aa` |
| `compact_mcm_publication.py` | `068707321e7b2b05213e2dc0aeb06ea5f56e865eff5c2b2e03ea7dbd33828688` |
| `compact_pair_log.py` | `de8f5544d1689029b05e9e7978506dd8597da5e930308d1f1ae1c2788fffe860` |
| `score_batches.py` | `69f6551049e6220f327177f9379e0ddb1144fb66da2fac24814fbb367a0041a2` |
| `score_tail.py` | `9e3cffff04c6e6186aa04f7da66443007b84b9174756671dcb11d9a6c95bc8ad` |
| `mcm_score_stream.py` | `c70b23d4f8d16aa418109647bdba7ccd2139a2c1ef910b5acad8535aeebde1d7` |
| `test_compact_mcm.py` | `340886b53717d7575e02e4222aa88a38e6539fc728e423a450845bf035b8ed0f` |
| `test_score_cleanup.py` | `e23505209a4a19a5c6482792c6ad97b5923ac5141313f712787d5289ee767721` |
| `check03.log` | `2d945a190575e4f275b7be93b3a7d9ccc6ac4c66318b8e78131e5b60858f7d71` |
| `cleanup-check02.log` | `76a4e7af1b2a85547754d40d9983b854deb835dd12506dbb5f42cffe0e4d2560` |

These are direct reviewed-file bindings, not a claim of a complete transitive execution-source manifest.
