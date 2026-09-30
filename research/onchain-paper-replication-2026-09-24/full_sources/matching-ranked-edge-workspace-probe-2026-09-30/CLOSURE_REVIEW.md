# Independent directed-chain profile terminal review

Accepted as a completed single synthetic profile at source `e6417c6f2f59c1ccf9fdb9ffd2af4c5b59020977`. No inconsistency was found in the compact terminal evidence. This review performed source/JSON/log hashing, metadata arithmetic and file-stat checks only. It did not open NPY bodies, replay the algorithm, rerun tests or launch a job.

All 100 bound files independently match current bytes and their recorded committed versions; HEAD remains unchanged. All 11 top-level evidence hashes and 30 nested checkpoint metadata hashes in `closure01.json` match. The raw child log contains exactly the 14 ordered checkpoint records plus the final result, each matching its saved receipt and `result.json`. The closure receipt SHA-256 is `1df7961a67e44ff3deb29b9bbc895b27f4a9717e36450b53f63bac81e5329d27`.

## Ownership and guard closure

The saved preflight and live review identify one invocation, monitor 1163863 with start ticks 9655861, worker 1163870, session 50890 and unit `onchain-replication-9e948629b8e94d198f10af289ec6eadc.service`. The monitor, worker and exact cgroup are now absent. Independent unit readback is inactive/dead. Saved guard and child-exit receipts report zero child exit, verified cleanup, complete phase and no limit reason. The command is the reviewed pinned-runtime worker invocation.

Guard elapsed time was 895.351093906 seconds. Sampled peak cgroup memory was 805,543,936 bytes, with **625 memory.high events**, zero memory.max events and zero OOM/group-kill events. This was not an event-free run. The saved kernel controls remained 1 GiB maximum, 768 MiB high and zero swap, with two-CPU affinity readback, 3 GiB host reserve, 4 GiB startup, 10 GiB disk floor and a 1,800-second wall limit. Throttling is retained resource evidence, not a failed terminal or permission to enlarge a later allowance.

The peak is a sampled whole-profile cgroup observation including retained checkpoint page cache, validation/diagnostic temporaries and runtime overhead. It is not an exact process RSS peak, isolated ranking requirement, cold-cache lower bound or worst-case graph estimate.

## Independent result and checkpoint reconciliation

The result has 2,000 nodes and 1,999 directed edges per graph, 4,000,000 pair entries, 48 iterations and temperature termination. The retained 195,820,096 annealing operations, 191,808,048 edge-pair updates and 49 calls match independent arithmetic from the frozen schedule. For all 12 intermediate checkpoints, the recorded annealing phase, iteration and edge cursor were independently reconstructed from the call count and operation sequence; this checks counters without repeating any numerical update.

The initial hardening checkpoint is at cursor 65,536 with 39 selected pairs. Final hardening is complete at cursor 3,976,042 with 2,000 pairs. Both outer/component phase and identity joins are consistent with the result. The final compact pair list is a complete bijection and maps each node to itself, though this was an observed result rather than a prescribed assignment. Independent counting of forward chain edges gives 1,999 conserved edges. The objective is therefore `(1999/(2*1999)+1)/2 = 0.75`, matching both reported scalar values. This is a fixture-specific objective check, not a general optimality or independent annealing proof.

The final column-normalization error is `8.79296635503124e-14`, below the registered diagnostic tolerance. The worker's soft-matrix SHA-256 is `2e2466f839d80c1e8c6041065fb6242c25cc80edc9bcdb31960f0f4c76afab8e`; both ranked checkpoints join that identity, and their recorded order-body hashes agree.

There are exactly 12 five-file annealing snapshots and two seven-file ranked snapshots. Independent stat checks cover all 44 NPY extents, each 32,000,128 bytes, and exact member denominators. Every checkpoint is below its 128 MiB logical allowance. Their combined logical size is 1,408,042,757 bytes, below the 2 GiB aggregate cap. Checkpoint01 and checkpoint02 total 128,002,285 and 128,023,746 bytes respectively. These are logical file lengths, not filesystem allocation measurements.

All outer-to-inner manifest hashes and checkpoint receipt/log joins were independently verified. Guarded-worker assertions provide the full array hash checks, restoration, unchanged matrix identity and explicit restored-map closure. Independent review verifies the compact relationships and extents, not a second array-body audit. The prior map-close receipt for checkpoint02 and final result closure flag are true; null entries for earlier checkpoints correctly indicate no prior mapping to close.

Annealing, atomic ranking and periodic checkpointing together took 888.554824573 seconds. Prefix hardening took 0.063060082 seconds and the remainder 4.579272785 seconds. These timings include the recorded checkpoints, host state and throttling; no controlled speedup relative to earlier profiles is established.

Principal evidence SHA-256 values:

- `result.json`: `b109870b1c4721ebdc13dbf4796845f92e78e86ec119b98d55906331601878d9`
- `guard01/final.json`: `463a205758cd7c656c1ae9b915816e4665074178d005158c5fc449e6350aadcd`
- `guard01/child.log`: `c93e5cafba557e4620f0d495677dd780cf3eb598585e891712290a4da90061be`
- final outer manifest: `d5fd03fdae4d7cd6c97fb70f8b0ff41cedbb861e19fa285ddbbfa5d6a29ec305`

This closes the complete schedule, pair hardening, scalar scoring and checkpoint-restoration measurement for one fresh constant-feature directed-chain fixture under the unchanged capacity. It does not establish arbitrary nonzero-edge or real-hub feasibility, production backend/cache integration, dictionary/MCM/neural throughput, GPU precision, financial results or Graph 10 admission. The separate integration audit remains applicable; original resource and fit denominators are unchanged.
