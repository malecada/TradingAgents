# Graph production and resource integration

Base: 97e1b2b9. Engineering continuation of Tasks3/7/8/10/12; all existing
empirical identities remain closed. No new acquisition or fitting is launched.

Ruling: keep the existing isolated research worktree and pinned environment.
Ruling: graph production is a separate source operation. Sealed outputs become
explicit inputs to later population/fit claims; extra claims must be allocated
and reviewed before empirical launch. This avoids implicit same-run admission.
Ruling: BTC validation spans the whole registered source stream, across all weeks;
no independent per-week validation that would miss duplicate spends or creators.
Ruling: add explicitly owned retained aggregation workspaces without changing
legacy temporary-workspace behavior. Completed source boundaries receive SQLite
commits and receipts. A closed identity is never reopened. Unsealed/active
scratch is evidence, not automatically reusable input.

Execution order: durable aggregation and graph producer; bounded graph/feature
loading and GAT activation work; large-neighborhood feasibility; independently
reviewed pilot/configuration and cumulative budget; measured empirical admission.

Current: implementation started; only synthetic verification is authorized by
this engineering increment. Full data and compute/storage constraints remain.

## Implemented increment

- `aggregation.py`: exclusive persistent SQLite directory, FULL synchronous
  source-boundary commits, immutable boundary receipts, terminal database hash,
  retained rollback state and no same-directory restart. Normal temporary mode
  remains available to existing pure library callers. Generator abandonment is
  a failed terminal, never a completed graph-production claim.
- `weekly.py` / `btc_weekly.py`: opt-in retained workspace and source boundaries;
  all supplied weeks still share duplicate/prevout/chain validation. The exact
  graph mathematics and BTC rational sidecars are unchanged.
- `graph_production.py` / `job.py`: explicit `graphs` source-job kind bound to an
  admitted plan, complete source/week cells, ETH/BTC streaming source adapters,
  immutable graph publication, retained partial artifacts and verified reuse.
  Reuse does not decode or assert new cross-graph source validation.
- Synthetic Parquet → registered source claim → sealed graph → separately
  registered population works over a year boundary. Four train and four test
  examples plus one purged label are independently expected in the tiny fixture.
  This fixture is not a change to the frozen scientific folds or lookback.

Verification: red01 showed six missing-feature failures plus23 passing existing
weekly tests; green01 passed29 tests. red02 showed seven missing-producer
failures; green02 passed48 producer/controller tests. red03 showed two rejected
reuse modes, with the changed-body negative check passing; green03 passed10.
Integration01 passed12 producer tests, including interrupted publication and
actual separately registered population assembly. Every guard cleaned up.
Named offline suite and independent source review are in progress.

Remaining requirements: a separately reviewed successor protocol for adopting
sealed SQLite prefixes, explicit cross-cohort validation when reusing graphs,
bounded graph/feature/sampler residency, GAT activation and device integration,
large-neighborhood matching, sufficient declared working disk and measured
resource pilots. No partial database is admitted for continuation by this change.
No empirical claim, provider request, transaction decode on retained real data,
model fit on real data, or historical rerun occurred.

## Independent review corrections

The initial independent review found two defects, preserved in REVIEW.md.
P1: declared week coverage did not prove every source day/member was present.
P2: reuse did not explicitly enforce seven-day intervals. Four regression cases
failed before correction in review-red01; the corrected producer passed16 tests
in review-green01. BTC positive fixtures now contain all14 daily partitions,
including12 explicitly empty, distinctly hashed synthetic files. No real source
was altered or treated as empty. ETH validates the union of member intervals;
BTC validates the union of daily partitions before decoding.

Coverage evidence is now separately bound to each graph manifest. Graph source
hashes derived from observed transactions alone omit empty files, so reuse also
requires the registered coverage proof. Coverage-red01 demonstrated missing proof
outputs; coverage-green01 passed22 combined producer/workspace tests. Additional
reuse cases reject a gap in that proof or a proof bound to a different graph.
Early publication is rejected; later publication is retained, not rewritten.

The pre-fix named offline01 run was explicitly stopped after review findings;
operator-stop.json and guard cleanup are retained. It is not a passed suite.
The fresh offline02 run binds source-bindings.json and is currently in progress.

## Final verification

The named offline02 target completed: 2,747 standard tests and97 subtests,
473 neural tests and one CUDA skip; 3,220 tests passed in total. Standard test
time1111.60s; neural362.40s. Guard elapsed1477.888s, peak sampled
2633498624bytes, child0, no memory-limit events,
cleanup verified. All seven source bindings still match. The separately
prepared activation-checkpointing module was added after neural collection and
is excluded from these57 neural modules; its own verification is separate.

REVIEW_CORRECTIONS.md independently closes P1/P2 with no new critical defect in
the correction delta. The final suite executes all26 current graph-production
and aggregation cases. No empirical release follows.
