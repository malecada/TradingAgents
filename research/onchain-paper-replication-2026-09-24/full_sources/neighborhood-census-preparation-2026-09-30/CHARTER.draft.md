# Prospective largest-week complete neighborhood census

Status: preparation only. The budget, exact registration/source/runtime and
independent release review must be completed and committed before any graph-body
measurement. This draft creates no lifecycle claim and authorizes no rerun.

## Question and preserved scope

Measure the exact weak one-hop cardinality (including its center) for every node
of the completed ETH graph for 2022-07-25 through 2022-08-01. Its retained producer
is eth-paper-graph-resource-20260929-03. The purpose is prospective resource sizing
for the full paper method, not accuracy/model selection. The graph is already
spent development material. No fresh confirmation or economic claim is made.

Reuse the exact completed graph and its independently verified metadata. Do not
rebuild the graph, resample neighborhoods, fit a dictionary, run MCM, train a
model or reopen a closed identity. All earlier failed pilots, completed samples,
44 paper rows, 1,420 unique fits and original nine-week/109-cell resource scope
remain. The census alone closes none of the dictionary/MCM/neural requirements.
Missing broader assets/history and fund membership remain outstanding.

## Frozen prospective measurement

For each global node index, report one plus its number of distinct other nodes
joined by at least one incoming or outgoing edge. Reciprocal edges count once;
self-loops do not add another node. Isolates have cardinality one. All nodes and
edges participate; no ceiling-based truncation or sampled approximation.

Retain an integer per-node array, exact cardinality histogram, total node count,
minimum/maximum cardinality and all maxima indices (stable global-index order),
and count exceeding the unchanged study ceiling of 10,000. Preserve the original
node-order/graph/configuration hashes. Report measured elapsed time, peak memory,
resource events, checkpoint I/O and output bytes separately from inferred sizes.
No labels, prices, test losses, matching outputs or financial results are read.
Any later capacity change requires a separate prospective policy/configuration
lineage review; the census does not silently raise existing ceilings.

Candidate implementation: canonicalize each non-self directed edge to its
unordered endpoint pair, deduplicate exact pairs, then count endpoint incidences.
Integer-key overflow and graph identity must be checked before allocation. A
separate small explicit-neighbor-set oracle must verify the implementation on
reciprocal, directed, isolated and self-loop synthetic fixtures. Buffer accounting,
checkpoint recovery and failure ownership need source review before admission.

## Proposed bounds and failure behavior

One new cumulative claim, ceiling 52 to 53, with 25 consumed preserved. The other
27 unspent slots remain allocated to 12 body batches and 15 fit batches. No new
financial fits, automatic retries, paid resources or network access. Proposed
outer limits: 6 GiB memory max/5 GiB high, zero swap, 3 GiB host reserve, 9 GiB
startup availability, 10 GiB free-disk reserve, two CPU affinity, 3,600 seconds.
New outputs and checkpoint scratch must fit a 512 MiB allowance, separately from
the retained mapped graph. These are proposed limits, not a measured feasibility
claim or release. Every atomic phase needs a measured/enforced bound below the
600-second checkpoint interval or finer durable resumable progress before release.

Any limit, invalid input or implementation failure is terminal under this identity;
retain all partial receipts and report the exact failed phase. A future successor
requires a new reviewed budget disposition and must not reset spent history.

## Remaining execution prerequisites

Implement/test the census and checkpoint path; freeze complete source/runtime and
all exact inputs/outputs in a lifecycle gate; independently review the cumulative
extension and resource/source release; commit them after the current engineering
freeze is lifted; pass admission and fresh owner/host/storage checks. An accepted
budget-only review is not a substitute for any of these steps.
