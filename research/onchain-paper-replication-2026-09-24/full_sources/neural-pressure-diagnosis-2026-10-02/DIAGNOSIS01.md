# Neural pressure diagnosis — 2026-10-02

Read-only diagnosis of closed `eth-paper-neural-resource-20261002-02`. This document neither admits a follow-up nor changes production source, numerical policy or historical dispositions. Exact source, metadata and receipt pins and all nine cells' allocation arithmetic are in [refs01.json](refs01.json). Source pins match failed launch commit `78b5a0ecc401f6688068b8d9bd0612db1a9d44b0`.

## Established termination and limits of attribution

The exact owned unit `onchain-replication-68f9e97c20ef445494594db81063cac1.service` was killed by systemd-oomd after 298.890 seconds. Its journal records the user service ancestor's memory pressure of 71.13%, above 50% for more than 20 seconds with reclaim activity. Five processes were killed. The retained counters are `high=34646`, `max=0`, `oom=0`, `oom_kill=0`, `oom_group_kill=0`; sampled peak memory.current was 3,600,752,640 bytes. The recorded cause is userspace pressure policy, not a kernel memory.max OOM. Cleanup verified the owned cgroup and original processes absent.

Controls were memory.max=4,026,531,840 bytes (3.75 GiB), memory.high=3,489,660,928 bytes (3.25 GiB), and swap.max=0. Numerous high events are consistent with throttling and reclaim above the soft limit. They do not establish that this limit was the sole cause of ancestor pressure, nor that removing its earlier threshold would permit completion. The last memory composition was sampled after termination/reclaim began: approximately 309 MB unit anonymous memory and zero file memory at that instant do not describe peak composition. Ancestor file memory, other processes, allocator reservations and workload allocations cannot be causally apportioned from these receipts. Host available memory alone does not measure pressure stalls.

## Durable progress boundary

`produce_registered_neural_resource` publishes `producer/intent.json` before importing/configuring Torch and entering the cell loop. It creates and fsyncs `cell-00`, then performs active/source/input checks, mapped graph validation, default graph loading and `run_cell`. Per-cell JSON is published only after that body returns or a catchable exception is handled. SIGKILL cannot publish that disposition.

The complete retained tree contains the intent and an empty `cell-00` directory, with no subsequent cell directories, cell result or checkpoint. This establishes entry into the first cell's setup, not completion of its validation or entry into forward/backward. No durable phase receipt distinguishes mapped validation, resident loading, model construction, GAT forward, backward or optimizer step. All nine postmortem cells remain unavailable; zero checkpoints and zero financial fits are retained. Assertions that this attempt failed specifically in GAT or backward would exceed the evidence.

## Allocation and lifetime path

The graph is already reused. `run_cell` constructs one item and supplies `[[item] * 28 for _ in range(16)]`. `ReplicationModel.forward` caches encoded graphs by `id(graph)` within that forward, so all 448 references cause one graph encoder invocation. This preserves shared autograd contributions; it does not cache learned embeddings across updates. The stacked 16×28×32 float32 graph embeddings occupy only 57,344 bytes. Adding another repeat cache is not an identified improvement.

The initial MCM is N×32 float32 generated through NumPy and shared by `torch.from_numpy`. The edge tensor is constructed from `graph.edge_index.copy()` and then copied into a Torch int64 tensor: final 16E bytes plus a transient NumPy copy of the same size. The graph object remains live through `run_cell`. The model, optimizer and forward autograd graph retain necessary inputs and intermediate activations through loss.backward; explicit deletion of output/loss/item/prices/labels occurs after the optimizer update and before checkpoint serialization. Graph activation checkpointing is false in the frozen plan.

In `gat.py`, existing self edges are removed, duplicate directed edges are checked using `torch.unique` on stacked indices, then one self edge per valid node is added. Let L be this resulting edge count: N ≤ L ≤ E+N. The first layer has four heads of width 16. Its projection is N×4×16; advanced indexing and message construction create L×4×16 bodies. Attention intermediates have L×4 elements. Autograd can retain gather/multiplication inputs, and duplicate checks, masks, concatenation and reductions add temporary allocations. Pooling occurs after the graph layers, so it does not eliminate their node/edge-sized working sets. Layer two has one head of width 32.

`open_mapped_graph` preflights complete file sizes, headers and hashes and uses a specialized noncopying mapped snapshot. Validation includes graph hashing and repeated invariant checks. After this context closes, `load_graph` reopens and rehashes arrays. Its default `resident=False` does not make the returned `GraphSnapshot` zero-copy: Unicode IDs become a Python list and tuple of strings, and the ordinary snapshot constructor copies numerical arrays and constructs immutable byte-backed storage through `array.tobytes()`. Original mappings, an intermediate numeric copy and the immutable byte body can overlap during member construction. Python string/object overhead is additional and was not measured.

The first graph's saved array files total 562,558,280 bytes, including 344,248,088 bytes for node IDs; the remaining numeric array files total 218,310,192 bytes including headers. Mapping closure does not guarantee immediate eviction of file cache touched by hashing and reading. Validation also creates finite/log1p/allclose buffers and an edge sort index. Existing edge validation already uses an 8E-byte lexsort index with blocks rather than millions of Python edge tuples; graph hashing already streams rows rather than building one giant JSON array. These existing improvements must not be presented as missing work.

## Conservative shape arithmetic, not measured peak memory

The following are literal float32/int64 tensor body sizes, using E+N as an upper bound on L. They exclude framework/object/allocator overhead. Exact existing self-edge counts were not read. No array bodies were loaded for this diagnosis.

| Quantity | First cell 2022-01-03 | Largest N, 2022-07-25 |
|---|---:|---:|
| N / E | 2,049,095 / 3,182,055 | 2,764,221 / 3,504,159 |
| L upper bound | 5,231,150 | 6,268,380 |
| MCM, 128N bytes | 262,284,160 | 353,820,288 |
| Final edge indices, 16E bytes | 50,912,880 | 56,066,544 |
| One MLP-64 / first GAT projection, 256N bytes | 524,568,320 | 707,640,576 |
| One first GAT gather/message, ≤256L bytes | 1,339,174,400 | 1,604,705,280 |
| One four-head attention body, ≤16L bytes | 83,698,400 | 100,294,080 |
| One second GAT gather/message, ≤128L bytes | 669,587,200 | 802,352,640 |

A named-local expression for layer one is 672N+320L bytes: clean input 128N; projection and output 256N each; maxima and denominator 16N each; messages 256L; e, numerator and attention 16L each; source/target indices 16L. Evaluated at L=E+N this is 3,050,959,840 bytes for the first cell and 3,863,438,112 for the largest-N cell. This expression is neither a measured peak nor a guaranteed exact simultaneous allocation. It excludes input/MCM, graph storage, saved MLP/autograd tensors, temporary gathers/masks/sorts, interpreter and allocator. Some local lifetimes overlap and some expression temporaries have other lifetimes. It therefore motivates investigation but does not prove a required RAM minimum or identify the phase that actually died. Multiplying graph working memory by 448 would be incorrect.

## Prospective resource-only variant

The existing job/resource contract accepts memory.high ≤ memory.max. A prospective high=max=4,026,531,840-byte variant is expressible without a code change. The installed systemd.resource-control manual describes MemoryHigh as a throttling/reclaim threshold; its exact installed bytes are pinned in refs01. Raising only high would remove the 3.25-to-3.75 GiB early throttle interval while retaining the same hard cap. It may reduce pressure from early reclaim, but that benefit is unmeasured. Hard-cap OOM, ancestor pressure and systemd-oomd termination remain possible. This change neither lowers demand nor guarantees that any of the nine cells can finish.

An admissible proposal must retain the fixed 3 GiB host reserve, zero worker swap, 6.75 GiB startup condition, 7 GiB scheduling threshold and existing readiness behavior, all nine cells, complete graphs, MCM width 32, 16×28 repeats, architecture, seeds, checkpointing=false, physical isolation and CPU/time/output/disk limits. No OOMD disablement, ancestor/global setting change, sampling, model shrink or test-result tuning is implied. Success would show capacity only under the newly admitted controls; failure would not establish failure of the unexecuted 4.5/5/6 GiB preparations or the paper's method.

The closed 02 identity is spent and cannot be relaunched. Updated history is exactly 27 complete + 7 failed = 34 spent (17 legacy lineage + 17 current mechanism claims), with ceiling 62 adopted. Existing remaining allocations are 12 body + 15 financial + 1 other resource = 28. Preserving them and adding one neural attempt requires a prospective ceiling of 63: 34+12+15+1+1. It requires a new unused identity, explicit cumulative amendment/allocation/extension, independent machine-budget review, frozen charter/job/source gate/caller and fresh admission/readiness/control evidence. This document creates none of those permissions and refunds nothing.

## Concrete faithful next action and unresolved engineering evidence

Before assigning a failing phase or repeatedly varying limits, prepare bounded durable phase markers around graph validation, graph loading, model construction, forward, backward, optimizer update and checkpoint, with finite memory.current/memory.stat/PSI readbacks. This is a prospective engineering change requiring separate ownership, tiny offline verification and source review; it was not implemented here. Such diagnostics must fit the existing output bound and not introduce a model operation or extra update. A single high=max resource probe could then be considered under the new cumulative registration, with the original failed source/receipts preserved and any diagnostic source delta explicit.

A separate numerically preserving investigation could test whether redundant validation and mapped-to-resident copies can be avoided while retaining complete hashing, adversarial validation and safe mapping lifetime. GAT temporary lifetimes or bounded message computation may also be worth investigating. Their memory benefit is unmeasured; forward values, gradients, RNG use and reduction order require independent checks before acceptance. Activation checkpointing is an existing option but changes the registered execution policy and cannot be silently enabled. None of these hypotheses supports substituting a smaller graph, fewer motifs, shorter sequence or simpler model.

Only source, JSON metadata and retained receipts were inspected. No Torch/model import, array-body read, empirical run, network action or production mutation was performed for this diagnosis. The companion reference JSON supplies exact hashes for independent reconstruction; no new test was appropriate for these documentation-only findings.
