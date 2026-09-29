# Independent graph-production increment review

Status: **changes required** on the initial reviewed source snapshot. Review is
static and read-only except for this report. No tests, retained raw bodies,
empirical decoders, financial experiments, network requests or jobs were run by
the reviewer. The repository instructions, study state and September25
`RAW_GRAPH_REVIEW.md` were read before assessing implementation and tests.

Scope: the uncommitted aggregation/graph-production increment above base
`97e1b2b9` on `research/onchain-paper-replication-2026-09-24`. Existing helper
contracts were inspected where necessary to establish the actual admission path.

## Actionable findings

1. **P1 — declared weeks are accepted without complete source coverage.**
   `tradingagents/research/onchain_replication/graph_production.py:140–164`
   verifies that an ETH source interval lies inside declared coverage and decodes
   a BTC source for its own declared day. Neither branch verifies that the union
   of admitted source intervals/days covers every required day of every week.
   `_plan` validates the asserted plan coverage, while both builders merely
   reject a week with no transactions. A source on one day of each week therefore
   suffices to publish complete weekly graphs. The current integration fixture
   itself supplies BTC files dated `2023-12-31` and `2024-01-01`
   (`tests/research/onchain_replication/test_graph_production.py:35–54`) and
   expects two complete weekly graphs at lines64–85, leaving twelve required
   source days absent. ETH manifests narrowed to those two daily intervals pass
   the same containment check. This permits incomplete graph populations and
   unrecorded missing-source denominators to enter subsequent claims. Before
   decoding, validate an explicit full source-date/member inventory and exact
   coverage against the week denominator; retain unavailable dispositions for
   gaps. Add a within-week missing-day case with at least one surviving event
   in each week, and use complete source calendars in positive fixtures.

2. **P2 — reuse does not check the graph's ending boundary.**
   `tradingagents/research/onchain_replication/graph_production.py:104–106`
   checks asset, start, config and source identities, but omits `end_utc`.
   `load_graph` delegates to `validate_graph`, which only requires
   `start_utc < end_utc <= available_at`; it does not enforce a seven-day span.
   Consequently an internally consistent, hash-bound graph starting Monday and
   ending Tuesday is accepted as a complete registered weekly output. The
   population admission path also matches the start without checking its end.
   Require the reused end to equal the registered start plus seven days. Preserve
   the original `available_at`, including later publication, rather than
   rewriting it. Add short/long graph-interval rejection and unchanged late
   publication tests through the actual reuse path.

## Implementation observations and test assessment

- Exclusive producer/workspace directory creation and lifecycle active/source
  checks prevent ordinary same-identity restart. Both assets share one SQLite
  ledger across every supplied week, retaining duplicate transaction/spend,
  overlapping prevout, observed creator-order and coinbase-maturity checks.
  No new narrowing of those checks to weekly partitions was found.
- Source checkpoint membership and ingested rows commit together under SQLite
  FULL synchronization. The receipt follows the commit. A crash in that gap
  leaves unsealed evidence; no continuation loader claims it reusable. Normal
  exceptions roll back the uncommitted suffix and retain an explicitly failed
  workspace. Generator close propagates `GeneratorExit` to that failure path.
- BTC publication and reuse use the exact outer store, preserving rational edge
  and incident sidecars, integer fees and chain-order qualification. Reuse loads
  original members through their hash-validating stores and does not invoke a
  decoder. Publication failure leaves partial output files for indexing.
- The new tests meaningfully inspect retained database contents after decoder
  failure, exclusive reopening refusal, cross-week duplicates across a committed
  boundary, generator interruption, raw-body hash refusal, original-manifest
  reuse and interrupted publication. The population test calculates the tiny
  train/test/exclusion denominator and scaler expectation explicitly.
- Test coverage is incomplete for conflicting creator/prevout evidence and
  chain-order/maturity failures specifically across a committed source boundary;
  existing BTC unit cases cover these constraints without that boundary. The new
  BTC sidecar fixture uses an integer seven-satoshi transfer; noninteger rational
  coverage exists in earlier builder/store tests, not this production path.
  There is no injected failure exactly between SQLite commit and boundary-receipt
  publication, nor after a later graph publishes successfully. These are coverage
  limits, not additional demonstrated implementation defects.
- The fresh-process neural-free assertion imports the producer only. Static
  inspection of the source dispatch confirms lazy fit imports and source jobs
  requesting `include_torch=False`; no new neural runtime import was found in
  the inspected graph path. No fresh process was executed by this reviewer.

## Claims not tested or admitted

The review does not verify test-run success, full-history source completeness,
canonical chain truth, unavailable prevout history, historical publication
availability, external recoverability, power-loss filesystem behavior, process
kill recovery, full-sized RAM/disk/wall requirements, GPU execution, full-node
MCM feasibility, empirical accuracy or profitability. No partial-database
continuation protocol is implemented or admitted. Existing stopped identities
remain stopped; no rerun, revised registration or ledger write follows from
this report. Financial return, funding and fee-accounting claims are outside
this source-only increment. Implementation, full-paper completion and numerical
agreement remain separate claims.

## Initial source identities

| File | SHA256 |
|---|---|
| aggregation.py | `768c2ca743b2146fcc6bf606e4fa0bf41273ac15d06344d3a25a6aac78e8038f` |
| graph_production.py | `632b224867b598ab39ce4d3d8b9962610f312812471419d0fdc33354ab0a47ae` |
| weekly.py | `079a427f212738759109b31da23933549a8b7751851e3033703cdd03dc5f054a` |
| btc_weekly.py | `6d52650e2bc6225c73da9841e51ab03be33ba8f3dd32a5ae504d6b76908c4aed` |
| job.py | `6a7a163e0d862a0fca700bcd2aba402953274f0320bfb8cab1ea6fbb2684709a` |
| test_aggregation_workspace.py | `8d6a28f9087abc6bd406b566bbec5818b7bbd9a6d8f3c67d6a4021d5f9a249dc` |
| test_graph_production.py | `df856e5f78a90e2f8b56ff54a03b591eb5a4c4ca5bb8b3f3ab63f0c627f2cf92` |
