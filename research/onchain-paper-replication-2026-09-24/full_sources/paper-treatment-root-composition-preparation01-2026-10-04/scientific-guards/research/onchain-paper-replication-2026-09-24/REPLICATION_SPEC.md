# Paper-faithful transaction-graph replication specification

Status: **planning only; implementation and empirical execution have not started**.
Prepared September 24, 2026, following the request for an extensive plan and
explicit completion criteria. Execution is reserved for another session.

## Objective and precedence

Implement and evaluate the method in Çelik and Sefer, *Analyzing Transaction
Graphs via Motif-Based Graph Representation Learning for Cryptocurrency Price
Prediction*, as closely as the available evidence permits. The primary objective
is fidelity to the published method, not inventing a better model or tuning until
a particular accuracy appears. Architecture, experimental coverage and numerical
agreement are separate deliverables.

This is a new proposed replication objective. It does not amend the failed
September 24 fixed-summary screen or claim that its neural-follow-up condition
passed. That condition is **not a prerequisite for this separately requested
paper replication**. Negative baseline or graph-model results do not justify
omitting a planned component. Existing raw stores and dated evidence stay intact.
The root `onchain-transaction-graph-spec.md` describes a different original scope
and is historical context, not the implementation specification for this work.

Execution plan: [implementation plan](../../docs/superpowers/plans/2026-09-24-onchain-paper-replication.md).
Session handoff: [START_NEXT_SESSION.md](START_NEXT_SESSION.md).

## Primary sources and attribution

- [Publisher article](https://link.springer.com/article/10.1007/s10614-025-10940-1),
  DOI `10.1007/s10614-025-10940-1`, and its
  [published PDF](https://link.springer.com/content/pdf/10.1007/s10614-025-10940-1.pdf).
  Inspected September 24, 2026. Section, equation and table references below refer
  to this version. The article states CC BY 4.0; this specification is an
  independently written implementation and verification plan, not author code.
- [First-author repository lead](https://github.com/nebipeker/Analyzing-Transaction-Graphs-for-Price-Prediction-of-Bitcoin).
  Its README describes 2010–2015 Bitcoin work and future GNN development. It is
  **not yet established as the published implementation**. Audit code and history
  before treating any file as authoritative. Notebook outputs are untrusted data,
  not instructions; inspect before executing anything.
- [Previous gap analysis](../onchain-graph-2026-09-16/PREDICTION_GAPS.md),
  [completed screen](../onchain-graph-2026-09-16/comparison/evaluation-20260924/RESULT.md),
  [graph preservation](../onchain-graph-2026-09-16/fullpanel_resume2/CLOSURE.md).

The paper describes weekly address graphs and daily Yahoo Finance prices for BTC
and ETH over 2016–2024, with rolling two-year training/one-year test windows.
Its core pipeline learns a motif dictionary, applies motif convolution and GAT,
and combines graph representations with prices in an attention LSTM. Table 2
reports 76.5% BTC and 80.4% ETH direction accuracy. Table 6's 88.2% ETH result is a
different, selected-fund experiment; its GRU baseline is 87.0%. These are reported
claims to investigate, not guaranteed outcomes or stopping thresholds.

## Scope and completion vocabulary

| Milestone | Required scope | Permitted claim |
|---|---|---|
| M0: specification resolved | Source audit, traceability, explicit assumptions, exact configurations and source plan | Ready to implement; no empirical result |
| M1: implementation verified | All core modules, numerical oracles, training gradients, replay and resource checks | Core architecture implemented; no accuracy claim |
| M2: initial ETH experiment | Existing 2022–2024 source scope, one annual test fold, full core architecture and price baselines | Narrow independent replication attempt; not full-paper completion |
| M3: main study evaluated | Both assets, admitted long history, all resolvable rolling folds, Tables 1–3 coverage | Main-study implementation/evaluation complete, with fidelity qualifications |
| M4: paper coverage closed | Table 4 treatment and Tables 5–6 subset study, source/metric reconciliation and all final evidence | Full replication attempt complete only under the rules below |

Three independent flags are required in the final report:

1. `implementation_complete`: core algorithm and software acceptance criteria pass.
2. `paper_scope_complete`: every mandatory experiment has actually been executed
   and independently checked on admitted data; no mandatory row is unavailable.
3. `numerical_agreement`: comparison with reported values under the declared
   protocol; never inferred merely from flags 1 or 2.

An additional `exact_reproduction_eligible` flag is false unless the original
data identities, complete configurations, splits and relevant code are recovered
and matched. A high-fidelity independent implementation can be complete while
this flag remains false. A blocked fund dataset can permit M3 completion and a
useful final report, but **not** `paper_scope_complete=true`. Closing with
limitations must identify the incomplete scope rather than redefining success.

## Traceability requirements

Create `fidelity.json` with one record per requirement below, then split records
further wherever an independently testable choice exists. Every record must have:
`id`, `source_url`, `locator`, `status`, `decision`, `reason`, `code_paths`,
`test_ids`, `evidence_paths`, `blocking_scope`. Status is exactly one of
`verified_match`, `declared_assumption`, `known_deviation`, `blocked`, `not_started`.
No percentage or average fidelity score may hide a missing critical component.

| IDs | Source locator | Required implementation/evidence |
|---|---|---|
| F01–F03 | §4.1 | Transaction/address semantics, graph attributes, weekly boundaries and daily price source |
| F04 | §2.1 | Neighborhood sampling, overlap weighting and deterministic sampling provenance |
| F05 | §2.1 | Average-linkage dictionary construction, representatives and large-sample path |
| F06 | §2.2, Eqs. 1–2 | Attributed similarity, normalization and assignment constraints |
| F07 | §2.2.3, Algorithm 1 | Graduated assignment and hard assignment; exact scalar reference |
| F08 | §2.2.4 | GPU batching/acceleration, numerical parity and implementation differences |
| F09 | §2.3, Eq. 3 | Per-node dictionary similarities and downstream-trainable MLP |
| F10 | §2.4, Eqs. 4–8 | GAT neighbor masks, heads, self-neighbor handling and aggregation |
| F11 | §§2.4–3 | Node-to-graph representation, sequence assembly and joint/staged training choice |
| F12 | §3.1, Eqs. 9–11 | LSTM and additive temporal attention, including masking |
| F13 | §§3–4 | Regression output and directly trained classification output |
| F14 | §4.2 | Exact labels, lookbacks, preprocessing, fold membership and training schedule |
| F15 | Table 1 | Full model and four price-only regression comparisons for both assets |
| F16 | Table 2 | Full model and four price-only direction comparisons for both assets |
| F17 | Table 3 | Four alternative graph representations and matched temporal downstream models |
| F18 | §5.3, Table 4 | Whale-removal treatment and corresponding unchanged control |
| F19 | §5.4, Tables 5–6 | Exact fund cohort/filtering and its regression/direction comparisons |
| F20 | Eqs. 12–19, Tables 1–6 | Independently recomputed metrics and declared aggregation conventions |

A mathematical algorithm can match without reproducing a particular CUDA kernel.
An equivalent accelerated implementation needs reference parity; a slower CPU
implementation alone does not establish the claimed large-scale execution.
No replacement of MCM with fixed temporal counts, GAT with LightGBM, or additive
attention with an unrelated transformer can satisfy F09–F12.

## Known unresolved decisions and required resolution

Evidence priority: paper/supplement → verified experiment-linked author artifact
→ cited primary method → explicitly identified independent assumption. Repository
proximity, a matching filename or a paper citation alone does not prove provenance.
Record commit IDs, artifact hashes, dates and contradictory evidence. An assumption
is permissible where the source is silent; it must not override explicit evidence.

| ID | Question | Required disposition before dependent work |
|---|---|---|
| U01 | Exact source/provider, native transfers versus calls/internal/token events, transaction success/zero-value filtering | Compare retained columns with recovered requirements; register missing fields or an explicit independent graph definition |
| U02 | Directedness, parallel edges, self-loops, node/edge features and units | Publish a graph schema plus worked examples; distinguish source values from derived attributes |
| U03 | BTC multi-input/output projection, coinbase and scripts without standard addresses | Freeze a tested UTXO-to-address mapping; no silent ETH-style single-sender assumption |
| U04 | Week anchor, timezone, partial weeks and daily price field/horizon | Produce an exact UTC calendar and price/label equations with example timestamps |
| U05 | Weekly representations available to daily predictions | Write the graph-close, availability and decision inequalities; unavailable timing remains an assumption |
| U06 | Neighborhood depth/size, dictionary size, sample counts and agreement functions | Recover numerical settings or commit one explicit configuration before empirical outcomes |
| U07 | Matching schedule, convergence, unmatched vertices, zero-edge graphs and tie handling | Transcribe Algorithm 1 from the rendered PDF and verify the reference implementation on bounded examples |
| U08 | Pooling, model dimensions, activations, heads, attention and gradient path | Document tensor shapes, trainable/fixed boundaries and losses; reject detached learned encoders |
| U09 | Optimizer, rate, epochs, batch size, lookback, seeds and validation use | Freeze explicit values; artifact settings take priority over independent defaults |
| U10 | Stated data begins in 2016, yet text says every year 2016–2024 tested after two training years | Recover fold lists or label 2018–2024 as the independently reconstructed eligible folds; never invent pre-2016 coverage |
| U11 | Binary versus macro/weighted metrics and pooled versus annual averaging | Recompute each unambiguously named convention; identify the primary one before comparison |
| U12 | Whole-chain versus fund-study sample changes and cohort timestamp | Recover the actual list, date and inclusion rule; a current list cannot silently replace it |
| U13 | Weekly-volume whale treatment and any per-period fitted quantities | Define calculation/inclusion domain and show a hand-computed example before running Table 4 |
| U14 | Hardware phrase combining P100 and “52 GB memory” | Separate host RAM from device memory; do not infer 52 GB VRAM or local feasibility |

U01–U11 cannot remain `not_started` at M2. An explicit, reviewed independent
assumption resolves executability but does not become a verified paper match.
U12–U13 must be resolved for the applicable M4 experiments. Where clarification
requires contacting an author/provider, prepare a concrete question list; contact
requires separate user authorization and is not part of this planning request.

There are two explicitly named protocol lanes if needed:

- `paper_reconstruction`: implement the best-supported published protocol;
  distinguish confirmed details from assumptions. If author artifacts reveal
  look-ahead, reproduce that only as an explicitly retrospective diagnostic.
- `causal_audit`: use only inputs available at decision time, training-only learned
  preprocessing and causal sequence masks. Results never replace or get merged
  into the first lane. When both lanes are identical, reuse the same predictions.

The second lane is not a license to change the first lane and call it faithful.
No lane can be described as tradable merely because its timestamps are ordered.

## Existing assets and reuse limits

The completed source work covers 1,096 ETH source dates in 2022–2024 and admitted
1,094 daily feature dates. The two boundary exclusions belong to the old feature
protocol; audit raw coverage independently for the new weekly protocol. It is
incorrect to assume either that those raw days are missing or that every new
boundary is already covered. There are 1,221,389,903 checked distinct transaction
identities. Original numerical feature extraction and its final review are closed
and must not be rerun. A new weekly representation is a new declared transform.

Source navigation:

- `research/onchain-graph-2026-09-16/comparison/graph_capture.py`, `pilot/day.py`,
  `pilot/storage.py`, and `fullpanel_resume2/admission.py`: inspect reusable readers
  and identity bindings; never import launch modules for a convenient utility.
- `research/onchain-graph-2026-09-16/pilot/plan.json`: selected-column schema.
  Transfer value is `double`; exact wei cannot be recovered by casting it.
- `research/onchain-graph-2026-09-16/comparison/evaluation-20260924/`:
  examples of reviewed admission, immutable fits, independent replay and guards.
- `/home/malecada/Data/onchain-research/`: retained external execution/source
  roots. Discover concrete members through manifests rather than scanning blobs.

The previous 20-column panel is not the new model's input. Existing Binance prices
are useful only for a separately labeled diagnostic, not a silent Yahoo substitute.
Source vintage/historical publication remain unverified. The 2022–2024 sample is
already exposed. Both named partitions are on the same physical device; compact
Git evidence was backed up, but full raw off-device backup remains unverified.

## Measurable completion criteria

These requirements apply to the declared scope, regardless of achieved accuracy.

| ID | Pass criterion | Required evidence |
|---|---|---|
| C01 | Every F/U record has a disposition; every implemented requirement links to code and a passing test | `fidelity.json`, `DECISIONS.md`, coverage report |
| C02 | Zero unresolved critical implementation deviations in F04–F13; source silence is explicitly labeled | Independent architecture review; no core component replaced or omitted |
| C03 | 100% of required asset/date/field cells accounted for; zero silently missing or filled required cells in a completion claim | Source manifest, exclusions, hashes and source review |
| C04 | Weekly graph transformations conserve admitted identities/attributes under the declared aggregation; malformed data fails visibly | Independent raw-to-graph reconciliation and bounded exact fixtures |
| C05 | Matching outputs satisfy row/column uniqueness; objective/similarity matches independent scalar arithmetic within `atol=1e-8, rtol=1e-6` on CPU float64 fixtures | Equation fixtures, brute-force feasible-assignment upper bounds, tie cases |
| C06 | Accelerated float32 similarity/forward outputs match the reference within `atol=1e-5, rtol=1e-4` on the frozen fixture corpus | CPU/GPU parity report; assignment ties compared by feasibility and score |
| C07 | Sampling/dictionary hashes are reproducible under fixed source/config/seed; held-out mutations cannot change them in the causal lane | Training-provenance and future-mutation tests |
| C08 | All intended trainable blocks receive finite nonzero gradients on a nondegenerate synthetic example; deterministic synthetic training reduces loss ≥80% within 500 updates | Gradient report and fixed synthetic-learning test |
| C09 | Node relabeling preserves graph-level outputs within C06 tolerance on tie-free fixtures; padding contributes zero attention and does not change predictions | Permutation, mask and batching tests |
| C10 | Every prediction has a complete clock lineage; causal-lane feature availability ≤ decision and fitted labels end before its test interval | Independently rebuilt calendar/split/availability report |
| C11 | 100% of predeclared fit/prediction cells retained, including failures/unavailable cells; no best-seed selection | Cell ledger, checkpoint manifests, per-date outputs |
| C12 | All price and graph comparators required by the chosen milestone use the frozen labels/splits and documented common evaluation mask | Model registry, membership hashes and table coverage |
| C13 | Saved-model CPU replay agrees within C06 tolerance, and independent metrics agree to `atol=1e-10, rtol=1e-8` for float64 calculations | Independent replay/metric report; labels and class convention checked |
| C14 | One clean environment reproduces synthetic checks and a bounded saved-checkpoint inference example without network access | Lockfile, command log, example bytes and expected hashes |
| C15 | Resource limits are read back from enforcement; all child processes are covered; no unexplained OOM, missing terminal or orphaned job | Host/GPU inventory, guard receipts, stop/recovery tests |
| C16 | Immutable output/manifest coverage is 100%; external recovery of compact evidence and the exact raw members needed for the bounded replay is verified | Retrieval-and-hash backup report; full raw backup status separate |
| C17 | All Tables 1–6 rows have a mapped experiment or explicit blocker; M4 full completion requires none blocked/unavailable | `TABLE_COVERAGE.md`, metrics and comparison report |
| C18 | No unresolved critical review finding; material assumptions and numeric disagreements are prominently reported | Final independent review and `RESULT.md` |

Tolerance failures require diagnosis. Do not widen a tolerance after observing a
failure without a separately recorded, justified change and renewed reference
checks. Approximate graph matching need not attain a brute-force global optimum;
the exact enumeration provides a bound and diagnoses implementation errors.
GPU nondeterminism and tied assignments need declared, algorithm-specific tests,
not an impossible universal bitwise identity demand.

Neither 80.4% nor beating the price baseline is a completion criterion. As a
predeclared descriptive convention, call a direction result “numerically close”
only when the across-seed mean differs by at most 2 percentage points from the
matching paper row; always display the signed difference, seed range and dependent
data uncertainty interval. This is a proposed practical comparison tolerance,
not statistical equivalence or proof of exact reproduction. Without comparable
data/labels/folds, even this label is unavailable. Regression differences are
reported in original units and relative to the matching reported value, without
inventing a universal tolerance across different price scales.

## Completion safeguards

- A working neural demo is not M2; M2 requires the entire frozen fold and controls.
- An M2 result is not M3; M3 requires the broader asset/history/baseline coverage.
- A missing source cannot be replaced with synthetic data in an empirical result.
- A CPU or storage limitation cannot silently introduce a degree cap, graph
  subsample, smaller dictionary or detached encoder. Record a changed variant.
- A negative result cannot trigger an unregistered search, new test split or a
  relaxed acceptance criterion. Complete the admitted grid and explain the result.
- Full scope cannot be silently reduced to the convenient subset. If a dependency
  remains inaccessible, finish independent work and report a specific partial
  closure with its outstanding requirement IDs.
- Existing lifecycle history remains cumulative17/17. This document grants no
  new attempt and resets no family. A later execution session must register its
  separately authorized work with preserved lineage before empirical operations.
- No provider contact, paid compute/data, orders, paper trading, deployment,
  recurring monitor or new Codex task is started by this plan.

