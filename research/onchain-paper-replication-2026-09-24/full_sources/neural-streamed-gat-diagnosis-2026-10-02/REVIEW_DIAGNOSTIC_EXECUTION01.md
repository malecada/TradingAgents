# Independent review of closed diagnostic01

Disposition: **accepted as complete retained four-arm observations with a failed parent release check**. The numerical evidence supports a narrowly scoped attention-scoring diagnosis. The original parent terminal remains failed and the identity `neural-streamed-gat-diagnostic-20261002-01` permanently closed. This is not a GREEN pass, full-size capacity result or empirical admission.

Read-only review inspected source, raw JSON, original filesystem metadata, Git blobs and archive bodies using standard-library tools, with local Git lazy fetching disabled. Current process/cgroup/unit state was also inspected. No numerical imports, tests, jobs, content execution, extraction or source mutation occurred. Only this new review file was written.

## Source, raw and collection integrity

All 12 outer references matched their recorded sizes and hashes. All **255 released source pins, totaling 1,956,644 bytes**, matched canonical single-link regular current files and the Git blobs at original commit `dba18089034416baadfa0019dfd03eb1c8ee38f2`. The concrete release selects `diagnostic01.py`; unused `diagnostic02.py` and its alternate envelope were not silently substituted. Original reservation, native worker command, release hash, coordinator and terminal identity join.

Key independent hashes:

- `execution-result01.json`: `6e323d47b10dd0bf90ee6e2982d30a2cebb06af449b245f7a43a85a41579154d`.
- `diagnostic-release02.json`: `5688a9ed58e73fcd8c4f29c74c4d1d67b10e1739a1dab7e88eec52218b9c7568`.
- `diagnostic01.py`: `f28c343dc4d4d0249f85ce434842d321680b41042a2d1ed3a6b2774b5ba45c25`.
- `diagnostic_launcher02.py`: `6f5ba9ddf57ac4a44c339cc2f51d5909ffe8b82282dbb069640a3d13ee7701f1`.
- `retained-tree01.json`: `51f5f3e0b07f051f2078247a62ae36b864b9a9a51ceb8c92d9fe01c7c4dc44f9`.
- `retained-tree01.tar.gz`: `6a07f94b42d9d1ad672ed760189d6870ab1c0ccdda829fbadb986fe3860f0e40`, 12,528 bytes.

Collector01's preserved source hash is `65f4793b80e3bb6e857f140c7b03f3726b307bc630a884603f22bf1c0529bb07`. Independent AST parsing confirms its unterminated string literal at line137, which prevents execution of the module body. Collector02 differs by removal of one adjacent quote and parses successfully; its hash is `e914eef312e1fa3c4776f255387ff4ef426d5d87f094be86d462c539bbe5f69f`. The preserved preparation-failure record hashes to `3e7fbda4f707e905816141e4634e542d339fdd4d058c8766864394549476c179`. This was a collection-source correction, not a repeated diagnostic. No old failure or raw object was overwritten.

## Observed numerical result

The raw report is 158,330 bytes and the child log 92 bytes. All four prescribed arms were observed in the registered order, with 124 tensor-comparison records and 20 named optimizer parameter IDs per arm. Exact initial-state and recorded RNG agreement hold in each arm. All floating comparison records report finite values. The comparison denominator covers initial tensors, outputs/loss, input/parameter gradients, updated parameters and named Adam state under the frozen source traversal.

| Arm | Comparison records with mismatches | Mismatching elements | Records with nonzero maximum error |
|---|---:|---:|---:|
| eager scoring / eager aggregation | 0 | 0 | 0 |
| einsum scoring / eager aggregation | 3 | 3 | 80 |
| eager scoring / streamed aggregation | 0 | 0 | 0 |
| einsum scoring / streamed aggregation | 3 | 3 | 80 |

The two einsum arms have identical retained comparison records. Their three failing updated-parameter coordinates are:

- `temporal.lstm.weight_ih_l0[136,9]`: absolute error `2.4221837520599365e-05`.
- `temporal.lstm.weight_hh_l0[191,57]`: absolute error `1.6167759895324707e-06`.
- `temporal.alignment.weight[0,11]`: absolute error `1.3373792171478271e-06`.

Independent scalar reconstruction from each retained coordinate confirms every listed absolute difference and that it exceeds `1e-6 + 1e-5 * abs(actual)`, the unchanged original reference-side convention. The first parameter attribution is now explicit raw evidence rather than the earlier GREEN shape inference.

The mixed-arm source diffs change only the declared attention score expression: the baseline edge-wise multiply/sum becomes two node-wise einsums and an indexed sum in `einsum_eager.py`; the inverse replacement appears in `eager_streamed.py`. Under this one fixed tiny workload, the observed discrepancy follows the einsum-scoring choice for either aggregation implementation. Streamed aggregation with the original scoring has zero recorded maximum error throughout this comparison. This supports preserving the original score arithmetic while investigating a bounded implementation; it does not prove arbitrary-graph equivalence or memory reduction.

Important limitation: the eager/eager reference is executed **once and compared with itself** (`diagnostic01.py:152–153`). It is not an independent baseline-repeat determinism experiment. The four arms are single observations in fixed order, not repetitions or randomized trials. Raw tensor bodies and detailed per-operation attention scores are not retained, so the report does not locate a specific floating-point instruction or prove repeatability across environments. The 80 nonzero-error rows are not 80 tolerance failures; only three updated tensors exceed the frozen tolerance.

## Fixed-coordinate Adam evidence

For `temporal.lstm.weight_ih_l0[136,9]`, all arms retain initial value `-0.09038814902305603`, optimizer parameter ID10, first step1, learning rate0.001, betas `[0.9,0.999]` and unchanged epsilon `1e-8`.

| Scoring group | Gradient | Updated value | Actual delta |
|---|---:|---:|---:|
| Original eager | `2.750311978161335e-09` | `-0.09060385078191757` | `-0.00021570175886154175` |
| Node-wise einsum | `2.368324203416705e-09` | `-0.09057962894439697` | `-0.00019147992134094238` |

Raw reconstructed first moments equal their observed Adam moments, reconstructed second moments equal observed second moments, and the float32 replay's updated value equals the actual updated value in every arm. This review independently joins those retained values and recomputes the binary64 formula `p0 - lr*g/(abs(g)+eps)` exactly as recorded. Binary64 differs from the stored float32 update by approximately `-3.70645e-09` for eager scoring and `-3.10938e-09` for einsum scoring, so it is explanatory rather than a bit-identical float32 replay performed by this reviewer.

The observed gradient difference is only about `3.82e-10`, while the update difference is about `2.42e-5`; with gradients below the frozen Adam epsilon this explains why a small, tolerated gradient discrepancy can become an unacceptable updated-parameter discrepancy. It does not justify modifying epsilon, optimizer, dtype, seed or tolerance. Exact float32 replay is retained child evidence supported by the reviewed source; no numerical replay was executed during this review.

## Worker completion versus parent failure

The worker exited0 and guard completed after 5.110612969001522 seconds with no limit reason. The coordinator exited1 after 6.216901522999251 seconds at 18:24:53.517624 UTC. Native terminal and cleanup properties are success/status0, inactive/dead and empty ControlGroup. `cleanup_verified` is true, but the recorded stop command returned **5**.

The parent fails specifically at `diagnostic_launcher02.py:101`, which requires both verified cleanup and stop return0. Its error text `descendant cleanup unverified` is therefore broader than the actual evidence: the nonzero stop status triggered rejection even though the guard independently verified cleanup. The validator rejects early, so later validation clauses were not all reached in that parent invocation; the raw joins below were inspected independently. Stop stderr is not retained, so the exact cause of code5 is not independently known. A successfully exited transient unit disappearing before the stop request is consistent with the evidence, not a conclusively recorded causal event.

Current inspection confirms original monitor1110285, supervisor1110560 and workload1110564 absent, and the original cgroup absent. The current unit is `LoadState=not-found`, inactive/dead, MainPID0, empty ControlGroup, Result success/status0. The original failed parent terminal must remain unchanged. Any future acceptance of a nonzero stop result needs a prospective narrow rule requiring the full independently verified terminal/unit/cgroup/process closure evidence and rejecting other cleanup uncertainty; it must not merely ignore arbitrary stop errors or retroactively pass this identity.

## Native controls and retained denominator

Worker and guard agree on actual 1 GiB memory maximum/high, zero swap, CPUs `[0,1]` and original cgroup. Active native unit evidence records 4 MiB hard/soft file limits and a two-minute unit deadline, joining MainPID1110560 with supervisor readiness; worker RLIMIT readback agrees. The last per-thread map contains the supervisor only. CPU quota controller availability is false despite the unit's `2s` property; CPU enforcement is the affinity/readback claim. Initial and terminal memory events are all present and zero, including high/max/OOM. Sampled peak is 372,998,144 bytes and terminal memory9,265,152 bytes; no full-lifetime kernel peak is claimed. Child/guard terminal snapshots agree.

The unchanged 3 GiB reserve, 4 GiB startup threshold, 120-second guard/unit envelope, 15-second lease and 10 GiB floor are recorded. Last observed disk free is20,210,171,904 bytes. Retry and elapsed-time kill are false. No storage error/breach, cleanup-error or truncation flag appears. Storage limits remain sampled64 MiB, not a hard aggregate quota; file limits remain per file and the unit deadline is not a whole-controller deadline.

Independent original-tree enumeration verified **10 regular single-link files, five directories including root, 15 total entries, 175,021 logical bytes and 225,280 allocated bytes including directory blocks**. Exact membership, modes, body hashes, sizes and original-root device/inode all match. No extra member, symlink, surviving hardlink or special type was admitted. All 15 archive members were streamed without extraction, independently checking exact unique membership, types, modes and all ten body hashes. Original allocation is not tar-media allocation or an off-machine backup claim.

The last guard sample is212,992 allocated bytes,166,121 logical bytes and12 non-root entries. Complete closure adds12,288 allocated bytes,8,900 logical bytes and two non-root entries, consistent with final/terminal publication and live rewrite. The overwritten intermediate live body is not separately recoverable. Complete closure totals, not the earlier sample, are the final denominator.

## Reporting correction and next requirement

The preserved execution summary's opening phrase, “All four prescribed tiny arms observed disagreement”, is imprecise: **all four were observed; only the two einsum arms disagree**. Correct current reporting or add a separate clarification while preserving the original summary bytes. This review supplies that clarification. The subsequent source-specific explanation must remain scoped to this finite diagnostic, with the baseline self-comparison limitation above.

The next implementation may address the isolated scoring choice while preserving the model and original acceptance tolerances. It still requires exact new source review and a fresh complete GREEN oracle, including all gradient, block-bound and saved-storage checks that are absent here. No empirical04, original-dictionary bridge, full-size capacity, financial accuracy, asset/history coverage or paper numerical agreement is established. This diagnostic does not consume an empirical fit claim; the entire historical budget ledger was not recounted. Preserve the failed terminal, all raw, the collector syntax failure and the fixed source lineage; never rerun diagnostic01.
