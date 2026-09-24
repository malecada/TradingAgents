# Paper-faithful transaction-graph replication implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task in the later execution session. Use
> superpowers:subagent-driven-development only if that execution method is
> separately selected. Steps use checkbox syntax for tracking. This session is
> planning only; no implementation or empirical run has been authorized here.

**Goal:** Implement the published transaction-graph method as closely as available
evidence permits, evaluate the full declared paper scope, and independently
establish implementation fidelity and the degree of numerical agreement.

**Architecture:** Separate immutable source adapters, weekly attributed graphs,
reference/accelerated matching, learned dictionaries, neural modules, chronological
datasets, fitting and independent review. Use content-addressed intermediate
artifacts with explicit fold/configuration dependencies. Keep paper reconstruction
and any necessary causal audit as named, separate protocols.

**Tech stack:** Existing pinned Python 3.13.13 research environment for admission,
source verification and offline checks; NumPy/SciPy/PyArrow for graph preparation;
an explicitly locked PyTorch environment for neural code, with CUDA only after
compatibility/resource verification. A graph library is optional and must pass
the same numerical oracle as a direct implementation. Do not upgrade the existing
environment or assume binary compatibility to obtain GPU support.

**Spec:** [REPLICATION_SPEC.md](../../../research/onchain-paper-replication-2026-09-24/REPLICATION_SPEC.md).
Read this with the [session handoff](../../../research/onchain-paper-replication-2026-09-24/START_NEXT_SESSION.md).
The older root specification is context, not the controlling design.

## Global constraints

- Current status: **plan prepared; all execution tasks below are pending**.
- The user will start execution in another session; do not create that task now.
- Existing lifecycle history remains cumulative17/17. This document grants no
  new attempt and resets no family.
- Preserve raw stores, completed graphs, old criteria, original failures and
  exposed samples. Never rerun old launchers or overwrite old artifacts.
- The new objective is faithful replication. The previous negative feature
  screen does not veto this objective and must not be relabeled positive.
- Follow repository AGENTS.md, docs/RESEARCH_START.md and applicable governance,
  provenance and research-cycle skills. No credentials, author/provider messages,
  paid resources, orders, deployment or new monitor follow from preparation.
- No outcome-dependent model selection. Freeze each empirical contract, exact
  configuration, sources, input bindings and finite cells before that run.
- Use the spec's C01–C18 completion criteria. Low accuracy is not incomplete
  implementation; an omitted core component is.
- Research prose uses impersonal attribution. No edits to the unrelated options
  state in docs/research/STATE.md or to the separate thesis repository are needed.

## Review focus

1. A weekly graph contains later transactions than a daily decision. Expected:
   the causal lane rejects it, and reconstruction-lane use is explicitly labeled.
   Owned by Tasks 3 and 7; test future-input mutation and boundary instants.
2. High-degree hubs, empty/zero-edge neighborhoods and unequal graph sizes break
   assignment or exhaust memory. Expected: finite declared semantics or explicit
   rejection, with no silent truncation. Owned by Tasks 4, 5 and 8.
3. Cached graphs/embeddings leak held-out data or stale trainable weights.
   Expected: provenance-key rejection and training-only fitted preprocessing.
   Owned by Tasks 2, 5, 6 and 7.
4. Restarted jobs duplicate fits or lose optimizer/random state. Expected:
   immutable completed cells and a tested, explicit continuation protocol.
   Owned by Tasks 7 and 8.
5. Metric averages or changing date masks create apparent agreement. Expected:
   per-date retained predictions, fixed masks and independent reconstruction.
   Owned by Tasks 9, 12 and 13.

## Current starting point

Active checkout: `/home/malecada/master_thesis/TradingAgents-audit-fixes`.
At planning, branch `research/strategy-search-2026-09-11` was clean before these
documents. Recheck at execution; another task may have advanced it.

The completed ETH 2022–2024 reconstruction and matched LightGBM screen are linked
in the spec. Reuse immutable raw inputs through their manifests, not the old
20-feature panel as a substitute for neural graph inputs. The screen's 2024
results were 53.01% market, 55.19% activity and 50.27% motif accuracy; they answer
a different question. Do not rerun them to recreate context.

## File map and responsibility boundaries

Paths below are proposed new files unless marked existing. Create only as the
owning task reaches implementation. `P` denotes
`tradingagents/research/onchain_replication/`; `R` denotes
`research/onchain-paper-replication-2026-09-24/`; `T` denotes
`tests/research/onchain_replication/`. These are exact path prefixes, not separate
checkouts. Runtime/source manifests must expand them to actual relative paths.

| Task | Files and responsibility |
|---|---|
| 1 | `R/SOURCE_AUDIT.md`, `R/fidelity.json`, `R/DECISIONS.md`, `R/PROTOCOL.md`, `R/config/`, `R/TABLE_COVERAGE.md`: evidence, definitions and configuration |
| 2 | `P/__init__.py`, `P/contracts.py`, `P/provenance.py`, `P/cache.py`, `P/environment.py`; `T/test_contracts.py`, `T/test_cache.py`: pure interfaces and artifact identity |
| 3 | `P/eth_source.py`, `P/prices.py`, `P/weekly.py`; `T/test_eth_source.py`, `T/test_weekly.py`, `T/test_prices.py`: source adapters and graph generation |
| 4 | `P/matching_reference.py`, `P/matching.py`; `T/test_matching_reference.py`, `T/test_matching_accelerated.py`: mathematical reference and accelerator |
| 5 | `P/neighborhoods.py`, `P/dictionary.py`, `P/mcm.py`; `T/test_neighborhoods.py`, `T/test_dictionary.py`, `T/test_mcm.py`: structural representations |
| 6 | `P/gat.py`, `P/pooling.py`, `P/temporal.py`, `P/model.py`; `T/test_gat.py`, `T/test_temporal.py`, `T/test_model.py`: learned neural path |
| 7 | `P/calendar.py`, `P/dataset.py`, `P/training.py`, `P/checkpoints.py`; `T/test_calendar.py`, `T/test_training.py`, `T/test_checkpoints.py`: chronology and fits |
| 8 | `R/pilot/charter.md`, `R/pilot/config.json`, `R/pilot/gates.json`, `R/pilot/launch.py`, `P/resources.py`; `T/test_resources.py`: bounded measured feasibility |
| 9 | `P/price_baselines.py`, `P/metrics.py`, `R/eth_initial/`, `T/test_price_baselines.py`, `T/test_metrics.py`: first complete comparison |
| 10 | `P/btc_source.py`, `R/full_sources/`, `T/test_btc_source.py`: extended history and Bitcoin semantics |
| 11 | `P/graph_baselines.py`, `P/variants.py`, `T/test_graph_baselines.py`, `T/test_variants.py`: other graph models and paper treatments |
| 12 | `P/experiment_grid.py`, `P/run.py`, `R/full_evaluation/`, `T/test_experiment_grid.py`: complete experiment execution |
| 13 | `P/check_independent.py`, `P/report.py`, `T/test_independent.py`, `R/review/`, `R/RESULT.md`, `R/REPRODUCE.md`, `R/STATE.md`: independent closure and handoff |

`R/config/` contains `graph.json`, `matching.json`, `dictionary.json`,
`model.json`, `training.json`, `calendar.json`, `baselines.json` and
`resources.json`, created and frozen in Task 1 or the relevant pre-result
refinement. Every later empirical directory contains `CHARTER.md`, `gates.json`,
`config.json`, `inputs.json`, `history.json`, `launch.py`, `RUNBOOK.md` and a
result/manifest after execution. Use existing lifecycle schema; do not invent a
parallel run registry. Large model/data blobs live in declared external artifact
storage with JSON manifest bindings, not inline in lifecycle outputs or Git.

Existing files that may need narrow changes: `pyproject.toml`/`uv.lock` only if
compatible optional dependencies are justified; otherwise an isolated locked
runtime under `R/runtime/`. The named `scripts/verify_offline.py` already collects
`tests/research/` recursively; do not duplicate test registration. If the new
runtime is separate, preserve the original offline suite and add an explicitly
named neural offline command and receipt. No global import may require CUDA.

## Dependency order and review gates

Tasks 1–2 establish contracts. Task 3 and the synthetic work in Tasks 4–6 can then
progress independently. Task 7 integrates them. Task 8 is required before any
large graph transform/training. Task 9 completes the first ETH evaluation.
Tasks 10–11 extend scope and Task 12 runs the complete grid. Task 13 performs
final review, with incremental independent checks at each earlier gate.

Every task ends with focused tests, evidence-to-spec reconciliation and a scoped
commit. Before every empirical launch: named offline verification, independent
release review, immutable source/input bindings and the applicable registration.
Review means separately checking the mathematical/data claims; reusing the
production function to compute its own expected answer is insufficient.

## Task 1: Recover the experiment and freeze explicit choices

**Owns:** Task 1 files. **Produces:** `fidelity.json`, exact JSON configuration,
table/arm inventory and a protocol with no implicit scientific defaults.

- [ ] Read the publisher PDF, including rendered Algorithm 1 and Figures 2–4;
  preserve URL/version/hash and a licensed local reference or retrievable copy.
  Inspect the first-author repository, branches/tags/history and linked artifacts
  without running notebooks. Record provenance, license and whether each artifact
  actually implements the paper's experiment. Search public author/lab artifacts
  and supplements; do not contact anyone automatically.
- [ ] Populate F01–F20 and U01–U14 from the spec. For each unresolved choice,
  write the evidence checked, contradictory descriptions and its precise impact.
  In particular distinguish an unsupervised fixed dictionary from learned MLP/GAT
  parameters and identify the graph-to-time-series pooling operation.
- [ ] Resolve author-supported settings first. For remaining omissions, select
  one explicit independent implementation configuration, explain the rationale,
  and freeze it **before real fitted outcomes**. Do not represent guessed numbers
  as published hyperparameters. All settings below must be present:

```text
graph: event universe, filters, direction, edge aggregation, self loops,
       feature names/units, value precision, week anchor and partial-week rule
matching: s1/s2, alpha, initialization, beta schedule, normalization iterations,
          convergence/iteration caps, unmatched/zero-edge rules, tie ordering
dictionary: hop depth, neighborhood definition, sample count, size, weighting,
            linkage, representative selection, large-sample partition rule
model: input sizes, MLP widths/activation, GAT heads/layers/width/dropout,
       pooling, LSTM depth/width, additive-attention width, lookback, output heads
training: losses, optimizer/rate/weight decay, batch unit/size, epochs,
          validation/early-stopping policy, clipping, precision, seeds
calendar: price instrument/field, timezone, prediction decision, horizon,
          ties, graph/price availability, warmup, exact folds and masks
baselines: each baseline's implementation/version and complete settings
resources: RAM/swap/CPU/GPU/disk limits, startup reserves, checkpoint intervals
```

- [ ] Use these proposed **replication controls**, unless recovered evidence
  requires a separately named author-exact lane: seeds `[11, 23, 37, 51, 71]`,
  no hyperparameter search, and no best-seed selection. This proposal is not yet
  an empirical registration. Validation, if required, stays inside each training
  window; never use the annual test for stopping or feature/dictionary choices.
- [ ] Resolve the inconsistent fold description. If exact folds remain
  unavailable, enumerate rolling `[2016,2018)→2018`, through
  `[2022,2024)→2024` as an independent reconstruction (seven folds), with boundary
  inputs/warmup explicitly admitted. Do not claim these recover the paper's folds.
- [ ] Prepare the new history/budget amendment using the old 17 claims and sample
  exposures. Separate source, engineering and prediction claims; count planned
  fits as well as lifecycle claims. No existing allowance is reusable.
- [ ] Publish a concrete author-question list for unrecoverable details. Keep
  unresolved external dependencies separate from implementable assumptions.
  Review C01/F coverage; commit the specification and protocol artifacts.

**Acceptance:** M0; all dependent settings have evidence or explicit assumption,
and no experiment is launched. This task must resolve design choices rather than
passing an empty configuration to the implementer.

## Task 2: Establish data contracts, provenance and cache isolation

**Owns:** Task 2 files. **Consumes:** Task 1 schemas. **Produces:** contracts used
by all later modules. Use frozen dataclasses and explicit serialization:

```text
GraphSnapshot: asset, start_utc, end_utc, available_at, source_hashes,
               graph_config_hash, node_ids, node_features, edge_index,
               edge_features, raw_count, admitted_count, exclusion_counts
Fold: id, train_start, train_end, validation_start, validation_end,
      test_start, test_end, member_hash
Prediction: lane, asset, arm, fold_id, seed, decision_at, label_start,
            label_end, max_input_available_at, y_true, probability_up,
            predicted_price, checkpoint_hash
ArtifactKey: source_hashes, schema_version, transform_commit, config_hash,
             fold_id, train_member_hash, dictionary_hash, seed, weight_hash
cache_key(fields: Mapping[str, object]) -> str
validate_graph(snapshot: GraphSnapshot) -> None  # raises ValueError on violation
```

- [ ] Add failing contract tests for invalid dimensions, duplicate identities,
  invalid endpoints, nonfinite attributes, UTC-naive clocks and unknown fields.
- [ ] Pin identity sensitivity and stable serialization with this test:

```python
def test_cache_changes_with_training_or_weights():
    from tradingagents.research.onchain_replication.cache import cache_key
    base = dict(source_hashes=["a" * 64], config_hash="b" * 64,
                fold_id="2018", train_member_hash="c" * 64,
                dictionary_hash="d" * 64, seed=11, weight_hash="e" * 64)
    assert cache_key(base) == cache_key(dict(reversed(list(base.items()))))
    assert cache_key(base) != cache_key({**base, "train_member_hash": "f" * 64})
    assert cache_key(base) != cache_key({**base, "weight_hash": "0" * 64})
```

- [ ] Implement content hashing, immutable atomic publication, manifest validation
  and an explicit missing/corrupt-member error. No cache key may omit a dependency
  simply to improve reuse. Retain source-to-output lineage.
- [ ] Inventory available CPU/GPU and dependency compatibility read-only; create
  a lock without changing the old runtime. Imports and CPU synthetic tests must
  work without network/GPU. Commit contracts after focused tests pass.

**Acceptance:** C01, C07 foundations; corruption and cross-fold cache reuse rejected.

## Task 3: Build admitted weekly graphs and daily prices

**Owns:** Task 3 files. **Interfaces:**
`decode_eth(manifest, schema) -> Iterator[Transaction]`,
`build_weekly(events, graph_config) -> Iterator[GraphSnapshot]`,
`read_prices(manifest, price_config) -> PricePanel`.
Define `Transaction` and `PricePanel` in `P/contracts.py` using Task 1's field
types; source values retain their precision/unit metadata.

- [ ] Add synthetic fixtures spanning week/year boundaries, repeated edges,
  self-transfers, null recipients, failed/zero-value events and duplicate hashes.
  Pin one retained/excluded outcome for each category from the frozen graph rule.
- [ ] Verify boundary ownership explicitly through
  `week_start(timestamp: str, anchor: str) -> str`:

```python
def test_monday_utc_boundary():
    from tradingagents.research.onchain_replication.weekly import week_start
    assert week_start("2024-01-07T23:59:59Z", "MON") == "2024-01-01T00:00:00Z"
    assert week_start("2024-01-08T00:00:00Z", "MON") == "2024-01-08T00:00:00Z"
```

- [ ] Implement a streaming reader and sparse weekly output. Bound sort/join
  memory and publish per-week manifests; never construct a whole-chain dense
  adjacency matrix. Do not silently cap degree or drop large neighborhoods.
- [ ] Independently aggregate fixtures using simple dictionaries/counters and
  compare identity sets, counts, attributes and exclusions. Reconcile counts at
  raw, admitted-event, edge and node levels; they are different denominators.
- [ ] Audit retained source fields without rerunning closed jobs. Float transfer
  values may be used only under their declared precision; reacquire exact units
  under a new source contract if the adopted method requires them.
- [ ] Implement the admitted Yahoo price adapter with captured response bytes,
  instrument identity, provider timezone, revisions, missing dates and boundary
  prices. A provider failure returns an explicit unavailable source cell.
  Public market capture still requires its source contract before acquisition.
- [ ] Run focused synthetic tests and review schemas/provenance; commit. Actual
  multiweek extraction waits for the resource pilot contract in Task 8.

**Acceptance:** C03–C04, C10; no hidden temporal-motif inheritance in graph semantics.

## Task 4: Implement and verify attributed graph matching

**Owns:** Task 4 files. **Interfaces:**
`score_assignment(left, right, assignment, config) -> float`,
`match_reference(left, right, config) -> MatchResult`,
`match_batch(pairs, config, device) -> list[MatchResult]`.
`MatchResult` includes assignment, score, convergence state and iteration counts.
Use `GraphSnapshot`-compatible bounded attributed graph slices.

- [ ] Transcribe the paper's objective/normalization and Algorithm 1 into an
  auditable float64 scalar reference with equations/line-number comments.
  Validate the transcription against rendered equations, not garbled PDF text.
- [ ] Write independent exhaustive feasible-assignment enumeration for graphs
  with at most four nodes. Compare scores for supplied assignments exactly under
  C05; check the approximate solver never exceeds the exhaustive optimum beyond
  tolerance. Do not require the approximation to always find that optimum.
- [ ] Test hardening directly using
  `harden(matrix: ndarray) -> ndarray`, with the frozen tie rule:

```python
def test_hard_assignment_is_injective():
    import numpy as np
    from tradingagents.research.onchain_replication.matching_reference import harden
    out = harden(np.array([[.9, .8, .0], [.7, .6, .1]], dtype=np.float64))
    assert out.shape == (2, 3)
    assert set(np.unique(out)) <= {0, 1}
    assert (out.sum(axis=0) <= 1).all()
    assert (out.sum(axis=1) <= 1).all()
    assert out[0, 0] == 1
```

- [ ] Add fixtures for unequal sizes, isolated nodes, zero-edge denominators,
  asymmetric directed edges, identical attributes, ties and extreme softmax
  inputs. Explicitly reject any undefined mathematical case not resolved in U07.
- [ ] Implement bounded batched tensor matching, stable normalization and
  deterministic hardening. Add custom CUDA only if necessary after profiling;
  keep the reference callable. Avoid materializing unbounded four-index tensors.
- [ ] Compare CPU/GPU scores under C06. Compare tied hard assignments through
  feasibility/objective, and tie-free assignments directly. Run stress fixtures
  within declared bounds; commit with the numerical review report.

**Acceptance:** C05–C06; acceleration cannot conceal a changed objective.

## Task 5: Implement neighborhood sampling, dictionary and MCM

**Owns:** Task 5 files. **Interfaces:**
`sample_neighborhoods(graphs, config, seed) -> SampleManifest`,
`fit_dictionary(samples, matching_config, dictionary_config) -> Dictionary`,
`mcm_features(graph, dictionary, matching_config) -> ndarray[N, K]`.
`SampleManifest` records centers, graph hashes, probabilities and RNG state;
`Dictionary` records representatives, memberships, training provenance and hash.

- [ ] Add deterministic fixtures for the specified overlap-weight update,
  disconnected components, vertex relabeling and heavily repeated structures.
  Verify selection probabilities independently; a uniform sampler cannot pass.
- [ ] Implement the declared linkage, representative selection and large-sample
  procedure. Use small hand-computed distance/linkage examples with stable ties.
  Log sample/cluster counts and actual neighborhood-size distributions.
- [ ] Add `fit_dictionary` future-invariance tests: changing held-out graph bytes
  must not alter the training sample, representatives, preprocessing or hash.
  Same source/config/seed must reconstruct the identical dictionary manifest.
- [ ] Implement MCM one vertex and one motif at a time as an oracle, then the
  batched version. Compare all entries on bounded fixtures. A reordered dictionary
  must reorder output columns correspondingly; an altered motif must affect the
  appropriate similarity values on a deliberately nondegenerate fixture.
- [ ] Cache fixed dictionary similarity vectors only under complete dependency
  keys. Keep the learned MLP outside fixed feature caches. Test hub-size limits
  produce an explicit capacity outcome rather than an unnoticed sampler change.
- [ ] Run focused tests, independent dictionary/MCM review and commit.

**Acceptance:** C05–C07, F04–F09; fixed temporal motif counts do not satisfy this task.

## Task 6: Implement the complete neural graph-to-sequence model

**Owns:** Task 6 files. **Interfaces:** `GraphEncoder(config)` maps a weekly graph
plus MCM values to a graph vector; `TemporalHead(config)` maps padded chronological
sequences to logits or a scalar; `ReplicationModel(config)` composes both and
exposes named trainable parameter groups. All are ordinary PyTorch modules.

- [ ] Pin GAT equations on a three-node directed fixture using an independent
  dense calculation. Verify self-neighbor policy, head concatenation/averaging,
  normalization domain and padding with known weights.
- [ ] Implement pooling from U08, with a documented fallback assumption if the
  source remains silent. Test address relabeling, variable graph sizes and
  batched versus unbatched equality. Do not pool away graph structure before GAT.
- [ ] Implement LSTM plus the specified additive attention. Test exact attention
  normalization and zero weight on padded timesteps. Future padding/noise must
  not alter the output for a fixed valid prefix.
- [ ] Implement separate regression and binary-classification heads/losses; the
  direction model is trained for classification, not silently obtained from the
  sign of a regressor. Record the label-to-logit convention.
- [ ] Backpropagate on a synthetic temporal graph task requiring structure and
  time order. Require finite nonzero gradients in MLP, GAT, temporal and output
  blocks and the C08 loss reduction. Fix the synthetic seed/data before testing.
- [ ] Confirm learned graph embeddings are not cached across weight updates.
  If full end-to-end gradients exceed resources, investigate recomputation or
  checkpointing; a detached/frozen substitute is a different variant, not a pass.
- [ ] Run CPU reference tests and required GPU parity checks, review F09–F13 and
  commit. Large real-graph training remains unlaunched.

**Acceptance:** C08–C09 and all core architecture interfaces present and exercised.

## Task 7: Implement chronological datasets, fitting and recovery

**Owns:** Task 7 files. **Interfaces:**
`eligible(available_at: str, decision_at: str) -> bool`,
`build_folds(calendar_config, source_coverage) -> list[Fold]`,
`build_examples(graphs, prices, fold, config) -> ExampleManifest`,
`fit_cell(cell, examples, model_config, training_config) -> CheckpointManifest`,
`predict_cell(checkpoint, examples) -> list[Prediction]`.

- [ ] Pin the clock inequality independently:

```python
def test_future_graph_is_ineligible():
    from tradingagents.research.onchain_replication.calendar import eligible
    assert not eligible("2024-01-08T00:00:00Z", "2024-01-04T00:00:00Z")
    assert eligible("2024-01-08T00:00:00Z", "2024-01-08T00:00:00Z")
```

- [ ] Write boundary fixtures for leap day, exact close time, late source
  availability, overlapping label intervals, warmup and missing weeks. Enforce
  identical test masks in each comparison. Repeating the last available weekly
  representation must be an explicit join rule, never an implicit forward fill.
- [ ] Implement fold-local fitted transforms, dictionary binding and validation
  membership. A test-label mutation must leave all training artifacts unchanged.
  An observed test graph may be transformed at inference with the frozen training
  dictionary; it may not become a training sample.
- [ ] Implement fixed finite training with complete epoch/loss/seed logs and
  optimizer state. Write atomic checkpoints containing source/config/input
  hashes, epoch/batch cursor, model, optimizer, scheduler and all RNG states.
- [ ] In a synthetic interrupted-training fixture, compare uninterrupted and
  resumed same-environment outputs under C06. Reject config/source mismatch,
  missing RNG state, corrupted checkpoints and duplicate completed fit cells.
- [ ] Adapt the existing lifecycle/continuation pattern without changing old
  receipts: a live job is never duplicated; a terminal failed claim is never
  relaunched under the same identity. Test the proposed continuation policy before
  admitting it. An actual interruption consumes the registered attempt.
- [ ] Independently review clock and training provenance, run focused tests and
  commit. Epoch selection may depend only on registered training/validation data.

**Acceptance:** C07, C10–C11; reproducible, resumable implementation, no fit yet.

## Task 8: Measure full-size feasibility under bounded resources

**Owns:** Task 8 files and pilot results. **Consumes:** Tasks 1–7. **Produces:**
measured phase costs, resource configuration, capacity forecast and M1 review.

- [ ] Write and independently review a source-only/engineering pilot charter
  using existing admitted ETH inputs. Proposed fixed weeks begin
  `2022-01-03`, `2022-06-13`, `2022-11-07`, `2023-06-05`, `2024-01-01`,
  `2024-03-11`, `2024-08-05`, `2024-12-23` UTC; bind actual complete coverage.
  Dates are selected for calendar dispersion, not price outcomes. Record this
  selection rationale; do not replace inconvenient weeks after measurement.
- [ ] Profile decode, graph build, neighborhoods, matching, clustering, MCM,
  GAT forward/backward and checkpoint I/O separately. Use synthetic labels for
  resource training, not real forecasting outcomes. Also select the largest
  admitted training-week workload from label-free size metadata for a stress
  check; capacity extrapolation cannot rely only on average weeks.
- [ ] Start from a proposed aggregate 6 GiB host-process cap, two CPU workers,
  at least 3 GiB additional host reserve and 20 GiB disk floor per used volume.
  These are cautious engineering starting limits, not paper requirements or a
  change to any old run. Read actual cgroup limits; include subprocesses and
  page cache where applicable. GPU allocations are separately measured/bounded.
- [ ] Register an explicit device budget leaving at least 20% measured free VRAM
  at startup and capacity for peak allocations. Check competing workloads;
  do not terminate them. If the laptop cannot run the faithful graph, record
  measured needs and a concrete local/external resource proposal. No paid rental
  is authorized by this plan, and “52 GB memory” is not a device specification.
- [ ] Test low-space refusal, SIGTERM cleanup, lost monitor/parent, checkpoint
  corruption and simulated OOM in isolated synthetic subprocesses. Never force a
  real host OOM. Publish checkpoints often enough to bound lost work: after each
  graph artifact, and at least every 10 minutes during long training where safe.
- [ ] Estimate storage as preserved raw + new raw + weekly graphs + dictionary
  samples + fixed MCM features + models/logs + temporary peak + backup. Account
  for per-fold dictionary-dependent features and five seeds. Use a 1.5× planning
  margin on measured unmaterialized storage/work, explicitly an estimate.
- [ ] Run the registered pilot once, retain every attempted week and all resource
  receipts. Review numerical parity and fit the capacity forecast. Do not reduce
  neighborhood scope/dictionary size to force a pass without a declared deviation.

**Acceptance:** M1/C15. If inadequate capacity, complete independent software work,
report the measured dependency and leave empirical milestones visibly pending.

## Task 9: Complete the first ETH experiment and price baselines

**Owns:** Task 9 files and `R/eth_initial/`. **Interfaces:**
`make_price_baseline(name, task, config)` exposes `fit`/`predict`;
`classification_metrics(y, probability, convention) -> dict` and
`regression_metrics(y, prediction) -> dict` are pure functions.

- [ ] Implement the four price models from the recovered settings. Audit the
  hierarchical-LSTM definition against its cited method; stacking two ordinary
  LSTMs without evidence is not sufficient. Use SVC/SVR appropriately for the
  separate tasks. Train any normalization only on training inputs.
- [ ] Verify metrics with independent hand calculations, including:

```python
def test_binary_metrics_have_explicit_positive_class():
    import pytest
    from tradingagents.research.onchain_replication.metrics import classification_metrics
    m = classification_metrics([0, 0, 1, 1], [.1, .8, .7, .9], "binary_up")
    assert m["accuracy"] == .75
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["recall"] == 1.0
    assert m["f1"] == pytest.approx(.8)
```

- [ ] Register the full ETH 2022–2023 training/2024 testing reconstruction with
  the resolved boundaries. Initial direction scope: full architecture plus four
  price baselines, five fixed seeds, **25 fit cells** and the complete predeclared
  date denominator. If an identical lane/cell later appears in the full study,
  reuse its immutable artifact only when all input/config/provenance hashes match.
- [ ] Add zero-fit training-majority and last-observed-direction controls. Add
  four diagnostic direction arms using the same five seeds: constant graph
  input, MCM without GAT, GAT on admitted attributes without MCM, and a
  training-label permutation control. These are **20 additional fits**, separately
  labeled diagnostic, never replacements for a paper row. Permute training labels
  only; preserve true held-out labels and use a fixed permutation seed.
- [ ] Independently release-review and commit the exact charter/gate/grid/runtime
  before real fitting. Run price baselines first for interpretability, then the
  full graph model and diagnostics. Baseline accuracy failure is not permission
  to stop before the full model; a demonstrated code/timing defect is.
- [ ] Report all dates, exclusions, five seed results, baseline gaps and C10–C13
  checks. Avoid real-label overfitting experiments outside these registered cells.
  Close and preserve M2 before broadening data coverage.

**Acceptance:** M2 with all 45 fits accounted for and verified; an unavailable
mandatory fit means an incomplete M2, even if the lifecycle ledger closes.

## Task 10: Extend source coverage and implement Bitcoin projection

**Owns:** Task 10 files and `R/full_sources/`. **Consumes:** resolved U01–U04,
pilot capacity evidence. **Produces:** admitted long-history manifests/graphs.

- [ ] Inventory public or already retained historical sources and exact fields
  for BTC/ETH 2016–2024 plus necessary boundary history. Prefer verified reusable
  bytes. Register explicit public endpoints, date/byte/request limits and failure
  handling before new acquisition; no paid source is an assumed dependency.
- [ ] Implement `project_btc(transaction, projection_config) -> list[EdgeEvent]`.
  Define `EdgeEvent` in contracts. Test multiple inputs/outputs, shared source
  addresses, change outputs, coinbase, script types, spent-output lookup and fees
  using exact integer satoshis. A complete input-output projection must be labeled
  a modeling construction, not observed bilateral flows.
- [ ] Freeze the actual mapping selected in U03, with a worked example and
  evidence. If original semantics cannot be recovered, classify this as a
  material dataset assumption; do not quietly switch to a transaction-node graph.
- [ ] Estimate full storage/download cost from measured schemas and ranges.
  Register acquisition in finite auditable batches with immutable completed
  members. Interrupted recovery must reconcile existing bytes before continuation.
- [ ] Admit every required asset/week/price cell and independent bounded overlaps;
  identify gaps and source-vintage limits. No interpolation of missing chain
  transactions or fabricated pre-2016 training periods.
- [ ] Re-run only the **new** graph transform for new/admitted inputs; verify its
  outputs, preserve source manifests and commit the source admission report.

**Acceptance:** C03–C04 for M3, plus actual storage/backup paths. Missing asset or
history is a reported scope blocker; existing ETH work remains valid and retained.

## Task 11: Implement the remaining paper comparisons and treatments

**Owns:** Task 11 files. **Interfaces:**
`make_graph_baseline(name, config)` returns an encoder with explicit fit/transform
boundaries; `apply_variant(graph, variant_config) -> GraphSnapshot` preserves a
parent graph hash and a complete inclusion/exclusion ledger.

- [ ] Implement or verify primary-source implementations of Node2Vec, GraphWave,
  GIN and WatchYourStep. Freeze graph-to-vector and downstream sequence alignment.
  Unsupervised node embeddings may have independently rotated coordinate systems
  across snapshots; recover or declare the alignment/pooling strategy explicitly.
- [ ] Test each encoder on a topology-sensitive synthetic pair and permutation
  cases consistent with its algorithm. Compare any imported library against a
  primary reference; a returned matrix of the right shape is insufficient.
- [ ] Implement whale removal exactly under the U13 rule; test threshold equality,
  direction/aggregation of volume and edge/node deletions on a hand-calculated
  graph. Recompute derived features after filtering and preserve the control.
- [ ] Recover the fund cohort and historical/list-vintage evidence. Distinguish
  entity labels from addresses, membership date and whether the graph is induced
  on the cohort or includes external neighbors. Do not invent 65 addresses from a
  claim about 65 entities. Test exact membership and edge inclusion semantics.
- [ ] Treat unavailable cohort bytes as a blocker for Tables 5–6; implement and
  test the filtering path synthetically while continuing unrelated whole-chain
  work. A contemporary substitute is a separate exploratory variant.
- [ ] Review comparator identity, fair training inputs and F17–F19; commit.

**Acceptance:** All comparison software verified. M4 empirical scope still requires
the actual sources and runs; synthetic fixtures cannot satisfy it.

## Task 12: Run the full finite experiment matrix

**Owns:** Task 12 files and `R/full_evaluation/`. **Interface:**
`enumerate_cells(config) -> list[CellSpec]` emits unique immutable cell IDs,
input/config hashes and dependencies. `CellSpec` is defined in contracts and
includes lane, asset, fold, seed, task, arm, variant and expected output manifest.

- [ ] Build `TABLE_COVERAGE.md` from a literal table-to-cell mapping. Tables 2 and
  3 share their proposed-model row; reuse the same fit/predictions rather than
  presenting two independent trials. Table 4's unchanged control likewise reuses
  the appropriate baseline experiment.
- [ ] Freeze the proposed maximum grid below after Task 1 confirms supported
  folds. Counts are a planning ceiling for one protocol lane, not a currently
  granted experiment budget:

| Scope | Per asset/fold/seed | Assets | Folds | Seeds | Fit cells |
|---|---:|---:|---:|---:|---:|
| Table 1 regression: proposed + four price models | 5 | 2 | 7 | 5 | 350 |
| Tables 2–3 direction: proposed + four price + four graph models | 9 | 2 | 7 | 5 | 630 |
| Table 4 extra whale-filtered regression | 1 | 2 | 7 | 5 | 70 |
| Tables 5–6 fund regression and direction | 10 | 1 | 7 | 5 | 350 |
| Total distinct paper fit cells | | | | | **1,400** |

  Initial ETH paper cells may supply 25 of these, leaving 1,375 new paper fits
  when identities match. With the 20 initial diagnostic fits, one-lane work is
  at most 1,420 distinct model fits. A necessary second protocol lane can add up
  to 1,400 paper fits; it must have its own explicit cell grid and allowance, not
  emerge as a hidden doubling. Fewer supported folds reduce the enumerated count
  with an explicit fidelity qualification. These counts exclude source/engineering
  claims and forbid uncounted tuning fits. Actual runtime must be measured.
- [ ] Freeze a separate finite lifecycle claim budget by stage/batch before
  launching; derive it from this grid and source contracts, retaining prior17.
  A fit count is not a lifecycle allowance. Failures/continuations remain counted.
- [ ] Register accuracy, balanced accuracy, precision/recall/F1 conventions,
  confusion counts, Brier/log loss, and regression metrics in original price
  units. Report per-fold/per-seed, pooled predictions and annual averaging
  separately. Include inverse scaling and percentage units in regression tests.
- [ ] For uncertainty, preregister 2,000 paired moving-block resamples of 14
  consecutive daily observations, seed 20260924, sampled within test years;
  compare aligned models on identical indices and report seed dispersion
  separately. Treat this as conditional prediction uncertainty, not a guarantee
  about retraining or the paper's sampling uncertainty. Missing daily runs make
  that interval unavailable until a pre-result gap-aware rule is registered.
- [ ] Review full-run resource forecasts and finite storage. Execute checkpoints
  by cell under an admitted source HEAD. Never allow a batch to write outside its
  declared artifact root. Do not optimize hyperparameters against partial results.
- [ ] Mark every registered cell complete or unavailable with reason. Require
  actual complete mandatory cells for M3/M4 success; a closed ledger containing
  failures is not scientific completion. Preserve all checkpoints/predictions.

**Acceptance:** M3/M4 empirical coverage as actually achieved, with no silent
baseline, asset, year, seed or treatment omission.

## Task 13: Independent verification, reproducibility and final closure

**Owns:** Task 13 files. **Interfaces:**
`verify_evidence(manifest, protocol) -> ReviewReport`,
`render_report(review, table_mapping) -> str`.
The independent checker must not import production matching, calendar, labels,
metric or report calculations as its expected-value implementation.

- [ ] Reconstruct a bounded raw-to-weekly-to-prediction example independently,
  verify all artifact hashes, and review every fit's membership/lineage metadata.
  Check assignment feasibility/reference scores, model structure and saved weights.
- [ ] Recompute all labels, masks and final metrics from retained prices/predictions.
  Replay saved models on a declared bounded subset covering every architecture,
  both assets and all protocol lanes. Verify full prediction-file hashes for all
  cells. State the scope: bounded replay is not an independent refit of all models.
- [ ] Supply the exact locked environment, machine/runtime record, synthetic
  fixtures, a small legally redistributable admitted example and inference script.
  Demonstrate fresh-environment reproduction offline under C14. Keep original
  prediction inputs and outputs rather than regenerating them in the checker.
- [ ] Complete C01–C18 in `R/review/completion.json` with status, evidence and
  reviewer disposition. Reject false completion mechanically using
  `completion_status(records, mandatory_ids) -> dict`:

```python
def test_blocked_mandatory_item_prevents_full_completion():
    from tradingagents.research.onchain_replication.report import completion_status
    records = {"F09": "verified_match", "F19": "blocked"}
    assert completion_status(records, {"F09", "F19"})["paper_scope_complete"] is False
```

- [ ] Write `RESULT.md` with the separate completion flags, all table comparisons,
  signed accuracy differences and uncertainty, material assumptions, failed cells,
  and whether the reported baseline level was recovered. Discuss high accuracy
  only with its target, dates and protocol. No accuracy-to-profitability inference.
- [ ] Commit source, compact results and manifests; preserve large inputs/models
  externally. Verify remote commit and retrieve/hash the bounded replay members.
  Report full raw backup status independently; same-device copies do not qualify.
- [ ] Update this study's `STATE.md` and the evidence index with the achieved
  milestone, blockers and next action. Leave old results and unrelated state
  untouched. Resolve all critical review findings before declaring completion.

**Acceptance:** C01–C18 for the claimed milestone, honest partial closure where
external dependencies remain, and an independently usable reproduction package.

## Test and run command policy

Preparation begins with read-only source/state checks. No empirical command is
valid merely because a path appears in this plan. At implementation time, run
focused synthetic modules as they are created:

```bash
.venv/bin/python -B -m pytest -q --import-mode=importlib tests/research/onchain_replication/test_contracts.py
.venv/bin/python -B scripts/research_runtime.py --check
.venv/bin/python -B scripts/verify_offline.py
```

Use the separately locked neural interpreter for neural tests if the original
runtime cannot support them. Record its exact command in `R/REPRODUCE.md`; no
generic `python` invocation may select an unpinned environment. Never import
legacy experiment mains or run the entire unreviewed historical test tree.
Empirical launch commands are written only after the exact registration and
source commit exist, in that stage's `RUNBOOK.md`.

## Resource, duration and persistence expectations

No defensible full-run time/storage quote exists yet. Task 8 measures the graph
cost, Task 9 measures a complete fit, and Task 10 measures additional source
requirements. Cache fixed numerical representations safely, but count dictionary
and seed differences. Thousands of fits may be materially more expensive than
the previous feature extraction; a successful single training batch is not a
full-study capacity estimate.

For staffing only, an initial planning allowance is several weeks of engineering
and verification: source/specification audit, numerical/neural implementation,
resource integration, then comparative evaluation and independent closure.
Author artifacts could shorten this; unresolved definitions, GPU compatibility,
source gaps and acquisition could lengthen it substantially. Re-estimate after
Tasks 1, 8 and 9; do not turn this allowance into a promised completion date.

At each session end update `R/STATE.md` with completed task/criteria IDs, exact
source/environment/manifest references, active process identity if any, last
durable checkpoint and the next safe action. User interruptions and unavailable
resources should not erase the remaining scope. Do not automatically restart a
terminal run, reduce scope, or stop permanently because one result is negative.

## Plan self-review

- [x] F01–F20 mapped to Tasks 1–13 and C01–C18.
- [x] Original fixed-summary screen preserved; no success-conditioned veto on
  implementing the requested neural architecture.
- [x] Full asset/history/table scope distinguished from the first ETH milestone.
- [x] Missing author details assigned concrete resolution tasks; no invented
  hyperparameters represented as paper facts.
- [x] Five review-focus failure modes have explicit owning tasks/tests.
- [x] Core numerical, chronology, gradient, resource, recovery and metric checks
  have stated pass conditions and evidence.
- [x] Finite model-fit counts and separately required lifecycle budgets specified.
- [x] Planning is separated from execution; the next-session prompt starts with
  source recovery and admission, not an old launcher.

