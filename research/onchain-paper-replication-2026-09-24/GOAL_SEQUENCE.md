# Current goal order

Requested on 2026-10-12: prioritize computation of at most one week, preferably less, and retain the existing real-data pilot as the following milestone. This changes work priority, not the scientific protocol or empirical allowance.

**App status:** the user cleared the old paused goal, and the prepared runtime goal was successfully created with status ACTIVE. [Actual activation](RUNTIME_GOAL_ACTIVATION_2026-10-12.json) records the tool result. The original unfinished pilot objective/status/usage remain preserved in GOAL_PRIORITY_REQUEST_2026-10-12.json; the earlier creation refusal is historical. The pilot is the documented next goal, not a second concurrently active native goal.

**Scope:** the activated prepared definition covers the representative pilot: all seven full required graphs, 415,968,128 motif cells and the genuine joint update/checkpoint. No larger workload was specified during activation. The initial Ethereum fits and all 1,420 paper fits remain separately accounted; their computation within one week is not claimed.

## First: computation within 168 hours

Make the paper-faithful representative Ethereum pipeline feasible within **168 hours of total wall-clock computation**, preferably less, on an explicitly recorded resource configuration. This is a runtime target, not a deadline for the optimization work.

Working workload: all seven WHOLE required weekly graphs, all 415,968,128 motif cells, and the genuine GAT → attention-LSTM joint update/checkpoint. Include graph and feature generation, required validation, storage/offload/recovery and training. Reuse already completed admitted work; do not rerun spent jobs or sampling/clustering.

Success requires:

1. Implemented optimizations of the measured dominant costs, preserving the original algorithm, graph population, motif dictionary, schedule, provenance and numerical criteria.
2. Representative registered real-data measurements of throughput, storage/transport and training, with measured memory and storage feasibility. Preserve slow, failed and unavailable cases; account for the actual workload distribution and startup/checkpoint/recovery costs.
3. An independently reviewed, conservative end-to-end projection of at most 168 hours on the recorded configuration, with explicit uncertainty and no unmeasured critical stage. A component benchmark or an optimistic best-case rate is insufficient.
4. An executable, reviewed configuration for the following complete pilot. Until that pilot finishes, an achieved engineering projection remains distinct from an observed end-to-end completion time.

For scale, 415,968,128 cells divided by 604,800 seconds requires about **687.78 MCM cells/second** if the entire week were available only for MCM. Graph construction, training, verification and storage consume part of that week, so the required MCM rate would be higher. This is arithmetic, not measured throughput or a feasibility claim.

Prioritize large measured costs, safe reuse, batching, bounded parallelism and compiled kernels where justified. Each changed seam receives focused numerical/failure checks and a bounded baseline comparison; reuse accepted evidence and avoid repeated historical matrices, generic frameworks and speculative minor changes. Synthetic performance checks alone cannot close this goal. A failure to meet the target must remain explicit; a hardware recommendation by itself does not constitute achievement.

The existing 16 GB physical RAM ceiling, 10 GiB disk floor, frozen native job limits, original 32 motifs/512 spent samples, registrations and cumulative accounting remain in force. Additional paid compute, author/provider contact, trading and deployment require separate authorization. No scope reduction, simplification, resampling, test tuning, cap ladder, budget transfer or reopening a terminal identity is permitted.

## Next: complete the existing real-data pilot

The original unfinished native objective is preserved verbatim:

> Complete one representative end-to-end Ethereum real-data pilot of the paper-faithful motif dictionary → MCM → GAT → attention LSTM pipeline using preserved original raw inputs and frozen protocol. Measure feature-generation throughput, peak memory, storage usage and training time; independently verify the results and determine whether this 16GB machine can finish the initial Ethereum experiment and what additional compute would accomplish. Prioritize functional implementation and measurements, reuse accepted evidence, preserve spent/reserved identities, and obtain the necessary committed registration and cumulative allowance before empirical execution.

After the runtime engineering target is met, complete the genuine full pilot, measure its actual end-to-end duration and check the projection. If measurement reveals a bottleneck that invalidates the estimate, retain the outcome and reopen the performance requirement without relaunching a spent identity.

The broader all-13-task/C01–C18 replication, both assets/history/comparisons and all 1,420 financial fits remain subsequent study requirements. This ordering neither completes them nor promises their runtime.
