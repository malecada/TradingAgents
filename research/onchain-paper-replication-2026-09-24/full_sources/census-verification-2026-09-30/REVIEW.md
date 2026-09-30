# Independent census artifact verifier plan review

September 30, 2026. Source-only review during the census owner's active execution. No census array, graph body, test or job was opened/executed. This is prospective engineering artifact verification, not a census rerun or independent raw-transaction audit.

## Findings before execution

**V1 — pin the complete metadata/file denominator before mapping or allocating.** `main` currently trusts nodes, edges, file paths and identities from the same producer result it is checking, iterates arbitrary `s['files']` entries, and allocates an `n+1` array without joining the values to the reviewed census plan/claim and lifecycle artifact index. The planned compact bindings should be checked before any mapping. Require the exact four safe array filenames, complete successful cell/output denominator, exact claim/plan/manifest identity linkage, and expected node/edge counts and file-size bounds. Validate the retained summary and final checkpoint against their pinned bytes/identity as well. A successful unrelated terminal plus internally self-consistent result is not sufficient ancestry evidence. Reject unsupported file kinds/NPY headers before opening mappings and enforce a finite aggregate byte/shape envelope before numeric allocation.

**V2 — success is published before cleanup, and cleanup can stop at the first error.** `verification01.json` is written with status complete inside the try block. The finally loop closes mappings without individual exception handling. A first close failure can skip later handles and replace a primary verification assertion, leaving a misleading complete-looking result. Track a primary exception, attempt all closes independently, preserve it with cleanup notes or raise cleanup failure, then durably publish success only after cleanup succeeds. File flush/fsync and directory fsync should make the success receipt's retention contract explicit. A failed verifier identity must not silently overwrite or rerun its existing evidence.

## Supported assertions and memory scope

The chunked scans correctly check finite integer cardinality bounds, minimum/maximum, the >10,000 count, complete histogram and stable global maxima indices. Sorted-key assertions include cross-block ordering, the -1 self-loop sentinel, endpoint domain and canonical low<high orientation. Cross-block duplicate counting excludes sentinels correctly. Python accumulation of chunk cardinality sums avoids a whole-population int64 sum; the reviewed N and chunk size also keep each chunk sum well inside int64 range. `sum(counts)=N+2*unique_pairs` is a useful independent conservation identity.

These checks do not currently reconstruct per-node cardinalities from the retained sorted keys. Wrong assignments of degrees among non-maximal nodes could preserve histogram, maxima and total. The receipt therefore supports aggregate artifact consistency only unless an independent bounded key-to-count reconstruction is added. Even that reconstruction would not establish that every original graph edge was encoded correctly; no source graph is read in this scope.

Visible numeric scratch comprises an N+1 int64 bin array, up to N nonzero histogram indices and an up-to-N gathered bin comparison, plus bounded chunk masks/index arrays. Thus the comment 'one n+1 array and bounded chunk temporaries' understates additional linear histogram-comparison arrays. For the pinned 2,764,221-node/3,504,159-edge case, these arrays and the four retained mapped census artifacts appear compatible with the proposed 512 MiB maximum, but this is not a measured peak or page-cache guarantee. Bind expected dimensions first and state all linear allocations explicitly. The prospective guard is 512 MiB max / 384 MiB high / 3 GiB runtime reserve / 3.5 GiB startup / 10 GiB disk reserve / 180 seconds; execution still awaits a reviewed exact launcher and closed census bindings.

Initial verdict: await V1/V2 corrections and terminal-bound metadata before execution. No empirical census conclusion or successful verifier result is inferred.

Initial verifier SHA-256: `29a1ea5bd70354077a84f8bfa4e5fa815304f5caf97c718d75bdb643e4832cc5`.

## First correction inspection

The revised verifier adds frozen HEAD and byte checks, exact four numeric names, a 128 MiB aggregate file bound, hard-pinned N/E, claim-to-terminal-to-result identity checks, registered plan/config/order identity checks, complete lifecycle output-hash checks, artifact-index binding checks, and exact summary/final-checkpoint joins. All 21 compact files among its 25 bindings independently match; the four array bodies were not read or rehashed by this review. Their retained metadata totals 50,158,248 bytes. Census guard metadata records complete/child 0/cleanup verified at 135.082445635 seconds with a sampled peak of 899,379,200 bytes. Monitor 3750963 and its exact cgroup are absent. These are closure metadata observations, not completed array verification.

V2 is corrected in source: every memmap close is attempted independently, primary exceptions receive cleanup notes, standalone cleanup failure raises, and the success receipt is published only afterward with file and directory fsync. No injected cleanup test was run by this review.

Two final preparation details remain. The all-file NPY format/header/extent preflight requested in V1 is not yet present before the first np.load; a container returned for an unexpected file kind would not be covered by the memmap-only cleanup loop. Add that refusal before mapping. The new launcher itself is not yet included among the frozen bindings; bind its exact bytes. The array-memory comment should acknowledge nonzero histogram indices and gathered bin comparisons as additional linear allocations.

The inspected launcher uses the stated 512 MiB max, 384 MiB high, zero swap, 3 GiB runtime reserve, 3.5 GiB startup, 10 GiB disk floor and 180-second wall cap through the existing guard. It has an exclusive guard01 receipt identity and the verifier has an exclusive verification01 output. Initial corrected verifier SHA: `70cb33956a09ac4e95302e5debaecdf1bf0e782c870e45887d967213978e8bd7`; launcher SHA: `768fbb79ff1f7b4c03c6c685e16a11d738a42e079c273515a7d934c218b0a5a2`. Await the narrow final updates before execution.

## Final pre-execution acceptance

The final verifier preflights all four files before opening any mapping: exact NPY v1 magic, bounded header length, native int64 dtype, C order, expected/bounded dimensions and exact header-plus-payload extent. Shape products are bounded by the pinned dimensions before multiplication. This closes the remaining wrong-container/extent path in V1. The linear histogram comparison arrays are now accurately documented. The launcher is included in the refreshed 26 bindings; all 22 non-array bindings independently rehash correctly. The four array hashes remain unverified by this source review and are reserved for the bounded worker.

**V1 and V2 are resolved for the exact frozen verification workload. Accept one execution through the reviewed finite launcher after fresh host/ownership checks.** The limits and aggregate-consistency qualifications above remain; there is no per-node reconstruction from keys, source-graph replay, census rerun or empirical fit. No reviewer test, array read or launch occurred.

Final identities:

- `verify_arrays.py`: `bbf800990975514f8f9383a3ba5883b25424be466d131ffd620dbd6600b6cbbd`
- `run_verify.py`: `768fbb79ff1f7b4c03c6c685e16a11d738a42e079c273515a7d934c218b0a5a2`
- `bindings.json`: `fa21d5424b456da01af13939bf17d253c93624dee5607c1d9efab4c7fc6d4699`
- Frozen source HEAD: `29b0e94b870ad0bcc29aa57a481384074e0a451a`.

## Census and verifier terminal assessment

Independent compact-evidence inspection confirms the registered census completed its exact one-cell denominator under committed source `29b0e94b870ad0bcc29aa57a481384074e0a451a` and gate-v2. The terminal links the exact claim and three output hashes, with zero unavailable cells. All 80 source and 10 compact input pins independently match. The eight previous claim/terminal pairs in the extension snapshot also retain their hashes: 17 historical + eight earlier current claims + this census = **26 consumed of 53**, leaving the previously allocated 27 slots (12 body and 15 fit batches), not a spare resource successor grant.

Census guard closure reports **135.082445635 seconds**, child exit 0, cleanup verified, sampled peak **899,379,200 bytes**, and zero recorded memory events. The exact census monitor 3750963 and cgroup are absent. A separate metadata/stat-only reconstruction confirms the declared 14-file artifact denominator and both storage totals: **50,171,896 logical bytes / 50,233,344 allocated bytes**, including the declared producer/output directory blocks and excluding guard/claim/terminal telemetry as documented. No array body was opened for this review.

The bounded verifier also completed once, with child exit 0 and cleanup verified: **0.635730934 seconds**, sampled peak **26,112,000 bytes**, zero recorded memory events, and the exact reviewed 512 MiB/384 MiB/zero-swap/180-second guard profile. Monitor **3776069** and its cgroup are independently absent. All **22 compact bindings** match. The worker's saved result and raw child-log JSON are identical, and its four reported array hashes equal the frozen array bindings. These are audited worker hash results, not an independent reviewer array rehash. The very short worker and 0.25-second sampling cadence mean the sampled peak is not the true instantaneous maximum or a cold-cache/standalone memory requirement.

Saved consistency assertions cover all **2,764,221 nodes** and **3,504,159 directed-edge keys**, with minimum cardinality 1, maximum **701,309**, **35 nodes above 10,000**, one maximum, and **3,443,147 distinct nonself pairs**. Histogram count sums to 2,764,221; cardinalities sum to **9,650,515 = 2,764,221 + 2*3,443,147**. The complete histogram, maxima indices, sorted-key canonical/order invariants and retained identities passed the reviewed verifier. The earlier empirical-closure metadata document's 'numeric consistency pending' status is a retained pre-verification snapshot, superseded for this narrow question by this completed verifier evidence.

**Verdict: accept the closed census resource measurement and its bounded aggregate artifact-consistency verification.** This establishes that the measured neighborhood sizes exceed the unchanged 10,000-node ceiling for 35 centers; it does not authorize truncation, a capacity/configuration change, another resource claim, or declare full matching feasible. It does not independently reconstruct each node's count from retained keys or replay original source edges, and does not establish all broader graph/population, dictionary/MCM/neural or financial requirements. All 1,420 financial fits remain pending. Neither job was repeated by the reviewer.

Closure identities:

- Census terminal: `9dd3c180f2e772a6b9216f7c39e17cb0fa5cb2a1ac5f39cd880f095037ad7f27`
- Census empirical-closure01: `7ea08cb3755aa4525a46a0f8ff03debedf9824821e83268481ca53e0d6650adc`
- Verifier result: `527a3f13483f75c67e0b48b4fe7de65cc9028d9baf3dda9b2f5be6e8081c901a`
- Verifier final: `8c964eed3e4c5b2b7159b5326c9493a6c3bc4313df0b66cdb20a9abc1a3bc719`
- Verifier child log: `8c50f32456a2da80cf81568a0c22e85ba924f5fc1a542e3fe267837b6f0b3704`
- Verifier closure01: `99641e6b8d0e57f60c42cac9a843408a6cf03a2c82288c4a753affc4d91c40a9`
