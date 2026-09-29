# Full-neighborhood matching readiness

September 29, 2026. Read-only source assessment while graph-residency offline01
owns the frozen implementation. This document changes no configuration, claim,
sample, model or active job. Source identities are those in source-bindings.json.
The operative stable matching configuration is
[`config/matching-stable.json`](../../config/matching-stable.json), with its
[`matching-precision-v2.md`](../../matching-precision-v2.md) amendment. The older
`config/matching.json` remains preserved historical evidence.

## What remains after mapped graph integration

Mapped graph loading and sampling scratch reduce specific allocations. They do
not make the complete dictionary/MCM computation bounded or demonstrate that it
finishes within available resources. The next implementation must preserve the
full weak one-hop induced neighborhood, directed edges, attributes, center/order,
literal Algorithm 1 schedule, objective and greedy row-major hardening.

The following facts follow from the frozen source, without opening raw data:

| Stage | Current behavior | Remaining requirement |
| --- | --- | --- |
| Neighborhood selection | Python sets expand complete frontiers; a 10,000-node ceiling rejects large neighborhoods after expansion. Induced edges and attributes are copied. | Account for adjacency, frontier, index and attribute memory before enabling larger neighborhoods. Preserve every selected node/edge and ordering; no truncation. |
| Dictionary distances | `fit_dictionary` calls the scalar reference in both directions for each unordered sample pair. The configured 512 samples are below the 2,048 partition threshold. | A complete dictionary entails 130,816 unordered pairs and 261,632 directional solves. Benchmark this actual route, or prospectively declare and verify a different backend. Accelerated MCM alone does not accelerate dictionary fitting. |
| Pair admission | Both solvers reject more than 4,000,000 node-pair entries. | An explicit prospective capacity policy is required for larger pairs; removing the check is insufficient. Bound bytes, scratch and lifetime for all simultaneously live matrices. |
| Accelerated solve | Dense float64 node agreement, soft assignment, update and log-normalization matrices; node affinity initially broadcasts an attribute dimension. Edge compatibility is streamed in chunks of at most 65,536 right edges per left edge. | Chunk node affinity and matrix operations as necessary while preserving declared reduction order/tolerance. Edge chunking does not eliminate the edge-pair computational product. |
| Hardening/results | `harden` copies the full matrix to float64, allocates a dense int8 assignment, and repeatedly scans for the global maximum. Each accelerated result retains a float32 soft matrix as well as its hard assignment. MCM retains a list of results before extracting scores. | A score-only route can avoid retaining diagnostic matrices across motifs, but must verify identical scores, hardening decisions and iteration semantics. It does not by itself remove peak memory inside one solve. |
| Checkpoints | Dictionary persistence is checked after two directional solves; MCM persistence is checked after all motifs for one center. | A single large pair/center can exceed the nominal 600-second checkpoint interval. Add safe solver progress checkpoints or establish a registered upper bound on each atomic unit. Preserve partially completed pair/center work through explicit lineage. |

The largest verified graph contains 2,764,221 nodes. At 32 motifs this implies
88,455,072 logical MCM scores and 353,820,288 bytes for float32 outputs alone.
These are arithmetic workload/output sizes, not runtime or peak-RAM forecasts.
The saved graph measurement does not provide the sizes of every neighborhood or
dictionary representative, so it cannot size all matching matrices in advance.

## Prospective implementation order

1. Close the exact active offline01 verification and independent release review
   before modifying any frozen module or test. Preserve all retained failures.
2. Implement a bounded, optional score-only matching consumer first. Test against
   the existing scalar and accelerated oracles on rectangular, tied, zero-edge
   and directed examples. Prove it releases each result before the next motif;
   preserve the existing diagnostic API and default scientific behavior.
   Exact parity means the same backend/device/precision and shape batching.
   Scalar-to-accelerated comparisons retain the registered tolerance and
   tied-assignment feasibility/objective policy: accelerated scores and soft
   outputs round to float32, and GPU index-add is not promised bit stability.
3. Implement full-neighborhood and single-pair capacity handling with explicit
   allocation accounting, exclusive scratch ownership, failure cleanup and
   deterministic checkpoint continuation. Test above the former synthetic
   capacity limits, including interruption during a pair, without empirical data.
   Mapped arrays alone do not prove RSS bounds; an outer resource guard remains
   required. Preserve literal row-then-column normalization and hardening ties.
4. Integrate only through hash-admitted execution policies. Preflight every job
   before population production, bind policies in claims, and reject incomplete
   or stale checkpoint identities before numerical work.
5. Prepare and independently review a finite resource registration and cumulative
   budget amendment. Measure complete dictionary fitting, full MCM, neural
   forward/backward and checkpoint I/O on the declared resource-only inputs.
   Reuse admitted completed graphs and samples; do not rerun terminal identities.

## Identity and preservation constraint

The existing sample identity includes the dictionary configuration; the dictionary
identity includes both matching and dictionary configurations. Capacity ceilings
are currently inside those configurations. Changing a ceiling therefore changes
scientific cache identities even if successful numerical outputs would be equal.
Do not edit old configurations, rehash old samples under new labels, silently
exclude fields from existing hashes or claim that an execution override is already
supported. A prospective compatibility design must explicitly choose between a
new configuration lineage and a separately admitted execution allowance, retain
the original identities, and prove allowed continuation before empirical use.

Current accounting remains 25 consumed claims out of 52; the remaining 27 are
allocated to 12 body-capture batches and 15 financial-fit batches. A resource
extension or reviewed reassignment is needed before the next empirical claim.
All 1,420 fits remain pending. Missing BTC/early-ETH bodies, original fund/cohort
membership and CUDA evidence remain independent requirements. None is resolved
by this source assessment or the running engineering suite.
