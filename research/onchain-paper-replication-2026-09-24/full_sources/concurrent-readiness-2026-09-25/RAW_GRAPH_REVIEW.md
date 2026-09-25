# Raw-to-graph execution integration review

Status: static source review and preparation only. No decoder, graph builder,
model, test or historical job was executed. The active backup contract remains
unchanged. This report refines existing assembly requirements against actual
interfaces; it does not release a new research claim or report an empirical result.
Source identities are recorded in `evidence.json` beside this report.

## Findings and concrete implementation requirements

1. **The generic registered job has no raw-to-graph operation.** `job.py:67`
   accepts only fit, ranges, prices and coinmetrics_prices; its source dispatch
   does not invoke the graph builders. `pilot_successor_02/phase.py:47` provides
   a one-week ETH engineering path, tied to a now-closed pilot. Reusing that
   terminal launcher is not a production integration. A new registered producer
   must bind an exact asset/week denominator, source schema/member hashes,
   coverage, graph config, expected outputs, owner, scratch volume and resources.
   Add a source-only graph execution kind/dispatch after synthetic verification;
   do not hide graph production inside a fit or start it from reading a manifest.

2. **Builder scratch is temporary, not a durable resumable producer.**
   `weekly.py:40` and `btc_weekly.py:51` enter TemporaryDirectory and use local
   SQLite files. Normal context exit, including handled errors, removes that
   directory. This is a static failure-path risk, not evidence that historical
   retained scratch was deleted. A killed process can leave scratch behind, as
   in the preserved pilot; that accidental retention does not constitute a
   checkpoint contract. Introduce an exclusively owned persistent workspace,
   explicit sealed progress records and retained failure state. Source-member
   boundaries, transaction counts and committed SQLite state must agree before
   a prefix can be reused. A successor has a new identity; a terminal claim is
   never reopened. Keep immutable completed graph outputs separate from working
   database state. Do not delete the existing 5.305 GB pilot artifact inventory.

3. **Partitioning must preserve cross-partition validation.** BTC currently
   checks observed duplicate spends, conflicting prevouts, creator order and
   coinbase maturity (when chain positions are supplied) across its entire supplied
   stream before yielding graphs
   (`btc_weekly.py:56–110`). Calling it independently for each week would narrow
   these checks. Before adopting week-sized execution, bind a persistent/global
   validation ledger or equivalently verified cross-partition evidence, including
   unobserved-history qualifications. ETH transaction-identity checks likewise
   cover the supplied stream, not arbitrary unsupplied history. Complete weeks
   across December/January require all constituent source days. No silent gap
   fill, missing-week deletion, or weakening of duplicate checks is admissible.

4. **Both existing graph stores must participate in production admission.**
   `graph_store.py:11` already writes exclusive arrays and publishes its manifest
   after members. `btc_store.py:42` additionally preserves rational edge/incident
   sidecars, integer fees and chain-order qualification. A BTC producer must use
   and bind that outer exact manifest; publishing only the embedded float graph
   discards essential conservation and whale-filter evidence. Reuse the stores'
   hash checks; do not substitute pickle, rounded satoshis or unverified arrays.
   Publication failures need explicit unavailable outputs and retained partials.

5. **The metadata population producer is available, but consumes admitted graph
   inputs.** `population_assembly.py:138` requires graph references through
   `run.read_input`; it does not automatically adopt graphs just written by that
   same run. Two legitimate routes exist: separately admit sealed graph outputs
   as inputs to a following claim, or implement explicitly registered same-claim
   graph-output references with publication/hash validation. Select and review
   one route before assigning claims. The former needs finite claim allocation;
   the latter needs additional integration tests. The current 24/51 accounting
   cannot be assumed to absorb unspecified extra preparation claims.

6. **Completed pilot graphs are reuse candidates, not new workloads.** The
   closed pilot retains complete ETH graphs for 2022-01-03 and 2022-06-13 and
   independently checked closure evidence. Admit exact original manifests,
   source/config identities and array bytes before reuse in a new preparation;
   do not recompute these closed outputs for convenience. Other attempted source
   windows remain exposed even when source-day finalization is unavailable.
   The Storage Box backup preserves bytes but does not itself admit them as
   canonical-chain research inputs.

## Verification required after the active transfer

Run synthetic raw→graph→population integration through the actual registration
boundary, with independently calculated raw/admitted/excluded/edge/node counts.
Cover a year boundary, missing week, late graph, changed source/array hash,
interrupted SQLite commit/publication, retained failure scratch, exclusive owner
collision, reuse of a completed graph without decoder invocation, and forbidden
terminal-identity restart. BTC cases must place duplicate spends and conflicting
creator/prevout evidence on opposite sides of the chosen partition boundary and
round-trip exact rational sidecars. Verify no neural import for source-only work.
No synthetic test has been run during this active backup.

## Admission still required before real execution

- Exact full-history source/field/week denominator and explicit unavailable cells.
- Selected preparation/fit staging with prospective cumulative claim allocation.
- Source-bound implementation and independent review of preservation/reuse paths.
- Measured peak RAM, local working disk, temporary peak and finite wall limits.
- Separate resource-pilot successor accounting for the closed 109-cell pilot.
- Full-size MCM/neural feasibility and largest-week completion; greater current
  free RAM alone does not resolve the 10,000-node neighborhood capacity refusal.

No GPU or host size is inferred as sufficient by this static review. The existing
407.184 GB initial ETH graph/five-seed MCM projection is an artifact-storage
estimate with margin, not a RAM requirement or full-paper storage quote.
