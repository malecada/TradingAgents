# Independent score-only matching review

September 29, 2026. Focused implementation accepted for frozen-source offline verification. No material correctness finding was identified in the inspected delta. This review used source, diff and saved synthetic receipts only; no test, financial experiment, raw artifact, remote request or new job was executed.

`matching.py:47–89` routes both public consumers through the original solver kernel. Inspection against HEAD confirms unchanged validation, shape grouping, batch capacity, affinity construction, annealing, normalization, greedy hardening, edge/node objective and float32 score conversion. The new branch occurs after scalar score production and retains only score, convergence label and iteration count. The legacy diagnostic branch still constructs its original assignment and copied soft-assignment result. This supports exact same-backend CPU parity without replacing the scalar reference or relaxing its comparison tolerances.

At `matching.py:84–86`, each score-only hard assignment and its torch tensor are explicitly released before the next pair is hardened. Under the existing `torch.no_grad()` block the retained scalar score has no gradient graph holding those arrays. The soft diagnostic copy is omitted. The weak-reference test checks NumPy assignment release between pairs and after return; the `MatchResult` sentinel checks diagnostic-result omission. Tensor-reference release follows directly from source inspection, not a measured allocator/RSS reduction. Dense batch matrices, node-affinity broadcasts, hardening workspace, input graph references and the per-batch arithmetic remain. Retained score records still grow linearly with pair count. No claim of constant memory, arbitrary pair feasibility or a tighter total process bound is supported.

`mcm.py` preserves the default consumer and exposes only an explicit optional boolean. Nonboolean options and reference-plus-score-only fail before graph access. Same solver/grouping yields the same features, dictionary-column order and output dtype. Existing completed-prefix validation and checkpoint callback positions are unchanged; the option does not shorten a single center's solve or establish a hard 600-second checkpoint deadline. Search of the production package found no registered caller enabling the option. Admission, execution-policy binding and producer integration remain future work; scientific hashes are not amended by this component.

Saved red01 has eight missing-feature failures. Green01 reports **19 passed, 1 CUDA skip in 2.56 seconds**, across the new and related matching/MCM checks. The cases exercise two batch capacities, rectangular/directed/tied/zero-edge/singleton pairs, empty input, precision/capacity refusal, iteration-cap labeling, dictionary reordering, supplied output and resumed checkpoint parity. The existing CUDA check is for the legacy consumer; it does not establish new score-only CUDA parity even if executed elsewhere.

The pre-edit snapshot contains twelve pair results (six each at capacities8 and4,000,000). Its recorded old matching-source SHA independently matches HEAD's source bytes, and its SHA matches the parity receipt. The post-edit receipt reports exact legacy diagnostics and score-only scores for all twelve cases. This is saved author-run evidence supported by the source delta and executable regression assertions, not a reviewer rerun or an independently recomputed numerical result. General GPU bit identity and scalar-reference bit identity are not claimed.

Inspected identities:

- `matching.py`: `e5a4cb7966a53522532158a13ef7293d4d081a26cffba56c2eb0761a628c72a6`
- `mcm.py`: `db94fa2304b69f9d62779f22c08d4d2dba8e69d661553c55aecc111733a9fe23`
- `test_matching_scores.py`: `f61ba89b87b60d5d8d0fd6ed6e9527e8b8039e7e1b9ab4a61e652b7d3afe4efc`
- Pre-edit snapshot: `949b2415141b9dd5a5638223085e906fa8d4e8043f5cb4a6ff36cb05a55fa835`
- Parity receipt: `3409479082898626786ba3324905fd6dfc561b9bfdf7ee38eff3456017164996`
- Green01: `8910327e374cdb5eaaccdd063cdcbb872fc3bdae8b0639cdf3853a1a5d8c7b78`

Broad verification is pending for these bytes. This focused acceptance does not authorize changes to the active cold-offload's bindings or HEAD, does not attest that job's progress, and does not enable a registered empirical producer or financial fit.

## Expanded focused verification addendum

The production matching/MCM hashes above remain unchanged. Updated test SHA is `3f96f3e9a01dac07d46f64ae165eb15adf41f2573d573402ff9b3d13115a8c78`. The lifetime test now wraps the real `torch.tensor`, identifies the int8 hard-assignment source arrays and weakly records each resulting tensor. It checks previous tensor release before the next hardening call and requires all six recorded tensors to be gone at return. Consequently the earlier source-only qualification for tensor object release is superseded by this meaningful saved regression; allocator reservation, GPU asynchronous reclamation and RSS remain outside the assertion.

Saved green02 (`77c56f105cba2981770e88d676277b4099679ef77866fafe4a1c708695d5e59e`) reports **69 passed, 1 CUDA skip in 39.64 seconds**, including the related producer, pipeline and resource-guard checks. Focused acceptance is reaffirmed for source freezing and the named offline target. The prepared launcher checks HEAD and all declared bindings before invoking `scripts/verify_offline.py` under 3 GiB maximum/2.75 GiB high, zero swap, 3 GiB runtime reserve, 6 GiB startup reserve, 10 GiB disk floor and 3,600-second wall limit. Frozen binding completeness and any broad result require their own saved evidence; no broad success is inferred here. All other scope limitations remain.

## Terminal named-offline verification

The retained `offline01/child.log` contains terminal summaries of **2,768 standard passes plus 97 subtest passes in 1,187.64 seconds**, then **641 neural passes and 2 skips in 592.31 seconds**. The total is **3,409 passes plus 97 subtest passes, with 2 CUDA skips**. The log explicitly identifies the reviewed profile and withheld historical files; this is the named offline target, not unrestricted execution of all legacy tests.

Guard final and live receipts agree: phase **complete**, child exit **0**, cleanup verified, elapsed **1,784.188358 seconds**, sampled cgroup memory peak **2,221,502,464 bytes**, no limit reason and zero high/max/OOM events. The recorded command is the pinned Python interpreter with `-B scripts/verify_offline.py` in this checkout. Controls retain 3 GiB maximum, 2.75 GiB high, zero swap, 3 GiB runtime host reserve, 6 GiB startup reserve, 10 GiB disk floor, two-CPU affinity and 3,600-second limit. The cleanup stop return code5 is accompanied by inactive/dead unit state and verified cgroup removal, not a workload failure. At independent review, monitor PID1300385, the last recorded workload PID1300390 and the recorded cgroup are absent.

All **135 frozen file hashes independently match** current bytes. HEAD still equals frozen `8465d7f7ef565d959c0af836ac449fc5612748c7`. The reviewed matching/MCM/test identities are therefore covered by this completed run. Evidence hashes:

- Source bindings: `c24e71f927ad1af137cf778c81d7b776e24adc74978c504cfd68e7f49be49ecd`
- Final receipt: `75e5e1c03e4d70e2e1b572eeab02ec3e7f3e523f1f6f1c2ca3d81bb898da58b6`
- Child log: `5eb1ce8556fb60e4ee5ae4d7ba66e4d250ac1d440681cca6008518cf46c7fb12`
- Launcher: `3ea7297d3f8db7cf2d653a87e54338c37b896ffa598877ed4fa67625bf061d6d`

Engineering closure is accepted for these frozen sources, including the guard edit covered by the named target. This replaces the earlier pending broad-verification disposition only. The sampled peak describes this synthetic verification process and cache state, not a cold-cache production requirement or whole-host bound. GPU parity, large matching-pair feasibility, shorter checkpoint latency and admitted registered score-only integration remain unresolved. No empirical claim or fit is enabled. This review did not rerun any check or alter source/HEAD; the separately active cold-offload's outcome is not inferred from this suite.
