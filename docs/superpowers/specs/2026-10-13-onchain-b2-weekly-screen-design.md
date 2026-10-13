# Branch B2 — weekly on-chain graph screen with a sealed 2025–26 holdout

Status: design 2026-10-13, written before any B2 data capture or outcome.
Branch `research/onchain-replication-b-2026-10-12` (Branch B continues; B2 is
its second stage). Branch B's M2 result and forensics
(`research/onchain-replication-b-2026-10-12/RESULT.md`, `FORENSICS.md`) motivate
every change below. The paper is no longer the constraint: the goal is to find
out whether transaction-graph features, motif-based or not, carry usable signal.

## 1. Decisions taken with the user (2026-10-13)

1. Stream new public data: a sealed holdout 2025-01 → 2026-10 and extended
   history 2017–2021, from the free AWS public-blockchain dataset; no raw
   storage beyond what is already retained.
2. Targets: next-week return, realised volatility and volume (recommended), plus
   next-day and next-week direction ("just to try").
3. Use a free exchange-address label list for role-split features.
4. Follow the five-step plan: 0 sealed window · 1 weekly targets · 2 information-
   preserving features · 3 simple-model screen · 4 neural model only if step 3
   passes · 5 one-shot holdout confirmation.

## 2. Questions the stage answers

- Q1. Does on-chain activity (F1) improve on price-only (F0) forecasts?
- Q2. Do exchange/whale role flows (F3a) add to activity?
- Q3. Do motif features (F2) add to activity, alone and on top of role flows?
- Each for five targets (§6) and two model families (§8).

## 3. Approaches considered

- **A (chosen): weekly feature table + simple models.** One row per week (and per
  day for T1), nested feature sets, walk-forward over 2017–2024, sealed
  2025–26 confirmation. Minutes of model time; answers Q1–Q3 directly; a null
  here makes a neural model pointless with ~400 weekly samples.
- B: retrain the joint neural model with new pooling and weekly targets. Rejected
  for now: no evidence yet that any graph feature carries signal, and ~400
  labelled weeks cannot train a GAT end-to-end. It is step 4, conditional on A.
- C: exchange flows only, no motifs. Not a separate approach: it is feature set
  S2 inside A, so motifs are tested against it.

## 4. Data

### 4.1 Sources (all free, public)

| Data | Source | Window | Notes |
|---|---|---|---|
| ETH transactions | AWS public blockchain `s3://aws-public-blockchain/v1.0/eth/transactions/date=D/`, anonymous, columns `hash, block_timestamp, from_address, to_address, value, receipt_status` | 2017-01-01 → 2021-12-31 and 2025-01-01 → 2026-10-11 streamed; 2022-01-01 → 2024-12-31 from the retained hash-verified spans (`onchain_b.sources`) | ≈ 8 s per streamed day measured; nothing raw is kept |
| Daily close | Coin Metrics community API, ETH `PriceUSD`, 1d | 2016-12-01 → 2026-10-12 | CC BY-NC 4.0; same provider as Branch B |
| Daily volume | Binance spot ETHUSDT 1d klines (public REST), quote volume (USDT) | 2017-08-17 → 2026-10-12 | single venue; declared |
| Exchange labels | Union of Dune Spellbook `cex_evms_addresses` (4,957 addresses, BSL 1.1, research use) and dawsbot/eth-labels `mainnet/exchange` (372, MIT) | snapshot 2026-10-13 | stored in gitignored artifacts; commit records source URLs, commit IDs and sha256 |

Every streamed day records object key, size, ETag, row count and the admission
counters of `onchain_b.weekly.admitted_events`. Each API response is stored
with its sha256. A day that fails three attempts (30 s, 120 s backoff) is marked
unavailable; its week is then unavailable and every sample needing it is
excluded and listed, never filled.

Labels are a static 2026 snapshot applied to all years: an address labelled in
2024 is treated as an exchange in 2018 too. This is a declared look-ahead in
address identity (not in prices or targets); `added_date` is kept so a
date-restricted sensitivity can be reported.

### 4.2 Windows

Weeks are Monday-anchored UTC (`onchain_b.calendar` rules). A week's features
are usable from the end of the Monday after it (one-day lag, unchanged).

| Window | Weekly samples (decision Monday *m*) | Daily samples (decision day *d*) |
|---|---|---|
| Feature history only | weeks from 2017-01-02 | — |
| Development | 2017-10-02 ≤ *m*, target end *m*+7 ≤ 2024-12-31 | 2017-10-02 ≤ *d*, *d*+1 ≤ 2024-12-31 |
| Embargo | decision 2024-12-30 (target spans the boundary) | — |
| **Sealed holdout** | 2025-01-06 ≤ *m*, *m*+7 ≤ 2026-10-12 (92 weeks) | 2025-01-01 ≤ *d*, *d*+1 ≤ 2026-10-12 |

The dev start leaves 6 weeks of Binance volume and ≥ 8 weeks of on-chain history
for the trailing transforms (§5.4).

**Sealing.** Prices and volumes after 2024-12-31 are written to
`research_artifacts/onchain-b2/sealed/` at capture time. Dev loaders raise if
asked for any date after 2024-12-31. The holdout stage refuses to run unless
`research/onchain-b2-2026-10-13/selection.json` exists in a commit and its hash
matches. Holdout graph features are built label-free alongside the rest.

## 5. Weekly features

All are computed per week from the seven days' admitted events.

### 5.1 F0 — price and volume (at the decision time)

Log returns over 1, 7, 28 days; realised volatility (root sum of squared daily
log returns) over 7 and 28 days; log Binance quote volume over the last 7 days
and its ratio to the trailing 28-day mean. For daily samples, the same set at
day *d*.

### 5.2 F1 — activity (full week, all admitted transfers)

Admitted transfer count; failed share, zero-value share and null-recipient share
(from the day counters); active addresses (unique senders ∪ receivers), unique
senders, unique receivers; total ETH moved; median and 90th-percentile transfer
size; share of value moved by the top 100 addresses; self-transfer share;
full-graph edges and mean degree.

### 5.3 F2 / F3 — graph roles and motifs

- **F3a role flows (full week).** E = labelled exchange set. Exchange inflow and
  outflow (ETH and count; intra-exchange transfers excluded); net flow.
  *Deposit-like* addresses: non-exchange addresses with ≥ 1 transfer to E and
  ≥ 90 % of their outgoing ETH that week sent to E; their count and the ETH they
  received from other non-exchange addresses. *Whales*: the 100 non-exchange
  addresses with the largest ETH moved that week; their net flow to E and their
  share of all ETH moved. Distinct senders to E ∪ deposit-like.
- **Top-K graph and MCM.** `onchain_b.weekly.top_k_subgraph` with K = 5,000 and
  `onchain_b.mcm` with n_max = 32, unchanged. One dictionary, seed 11, built from
  weeks 2017-01-02 … 2018-12-24 only (inside every walk-forward training window).
- **F2 motif features (top-K graph).** Per motif k = 1…32: share of nodes whose
  best-matching motif is k; mean score; ETH-volume-weighted mean score (96).
- **F3b role-split motifs.** Mean score per motif over exchange nodes and over
  whale nodes present in the top-K graph (64), and the counts of each (2).

### 5.4 Transforms (causal, per series)

Counts and volumes → log1p; signed flows → sign·log1p(|x|); shares unchanged.
Each series enters the models only as (a) its z-score against the previous 8
weeks and (b) its one-week change. Raw levels are excluded (Branch B forensics:
out-of-range levels). Model-side standardisation is fit on the training fold.

## 6. Targets

Close = Coin Metrics `PriceUSD` of the UTC day; decision at close of day *m* or *d*.

| ID | Sample | Definition | Loss for the screen |
|---|---|---|---|
| T1 | daily | next-day direction: close[*d*+1] > close[*d*] | log loss |
| T2 | weekly | next-week direction: close[*m*+7] > close[*m*] | log loss |
| T3 | weekly | next-week log return log(close[*m*+7]/close[*m*]) | MSE |
| T4 | weekly | next-week log realised volatility: log √Σ r², the 7 daily log returns of *m*+1…*m*+7 | MSE |
| T5 | weekly | next-week log Binance quote volume over *m*+1…*m*+7 | MSE |

## 7. Feature sets (nested)

| Set | Contents | Answers |
|---|---|---|
| S0 | F0 | baseline |
| S1 | F0 + F1 | Q1 (S1 vs S0) |
| S2 | S1 + F3a | Q2 (S2 vs S1) |
| S3 | S1 + F2 | Q3a (S3 vs S1) |
| S4 | S2 + F2 + F3b | Q3b (S4 vs S2) |

## 8. Screen (development window only)

- **Folds:** expanding walk-forward; test years 2019, 2020, 2021, 2022, 2023,
  2024; train on all dev samples before the test year minus a purge of one
  target length (7 days weekly, 1 day daily).
- **Models (fixed; no search on test data).**
  - Linear: logistic regression (T1, T2) / ridge (T3–T5) on fold-standardised
    features; L2 strength chosen per fold from {0.1, 1, 10, 100, 1000} by an inner
    split (last 52 weeks / 365 days of the training window).
  - Trees: scikit-learn `HistGradientBoosting{Classifier,Regressor}` with
    max_iter 300, learning_rate 0.03, max_leaf_nodes 7, min_samples_leaf 20,
    l2_regularization 1.0, random_state 11.
- **Metrics:** pooled out-of-fold loss (§6), plus accuracy and Brier (T1, T2) and
  out-of-sample R² relative to S0 (T3–T5). Per-fold losses reported.
- **Gate for a comparison** (target × model × {S1 vs S0, S2 vs S1, S3 vs S1, S4 vs
  S2}): pooled loss difference < 0 with its 95 % circular block-bootstrap interval
  entirely below 0 (blocks of 4 weeks for weekly targets, 14 days for T1; 2,000
  draws; seed 20261013), **and** lower loss in ≥ 4 of the 6 test years.
  40 comparisons are screened; about two false passes are expected at this
  level, which is why the holdout exists.
- **Selection for the holdout:** at most 3 passing configurations, ranked by the
  upper end of their interval (most negative first); ties prefer graph sets
  (S3, S4) over S1/S2. If none pass, the screen is negative and the holdout stays
  unused. The selection is written to `selection.json` and committed before
  any holdout read.

## 9. Holdout (step 5)

Each selected configuration is refitted once on all development samples and
predicts the sealed window once. Gate per configuration: loss difference
against its comparator < 0 with the one-sided bootstrap interval below 0 at
α = 0.05 / m (Holm across the m selected). Everything else is reported
descriptively. No refit after the read.

## 10. Step 4 (conditional neural model)

Only if a graph set (S3 or S4) passes the screen for some target. Then a separate
spec, registered before training: weekly sequences of 8–12 graph vectors,
pooling by role or attention instead of the mean, a label-free pretrained
encoder (predict next week's motif histogram), class-balanced losses, early
stopping inside the development window. It reuses the same holdout rule.

## 11. Compute, storage, failure handling

- Streaming ≈ 2,475 days × 8–10 s; two weeks in parallel → about 3–4 h. Local
  2022–2024 spans ≈ 40 min. Peak RSS per worker ≈ 4 GB (2025 weeks, ~10M rows);
  two workers under a 10 GiB unit cap.
- MCM seed 11 for ~510 weeks ≈ 23 s each → about 2 h with two in parallel.
- Storage ≈ 360 MB graphs + 330 MB MCM + < 50 MB features/receipts.
- Every stage is idempotent per week or per fold and logs JSON lines with RSS
  (as in Branch B). Torch threads 2.

## 12. Package layout

```
tradingagents/research/onchain_b2/
  s3source.py   # stream one day from S3 (pyarrow anonymous) or local spans; receipts
  labels.py     # fetch/freeze label union; exchange set
  weekbuild.py  # one week: admitted events → pairs → F1, F3a, top-K graph (reuses onchain_b.weekly)
  motiffeat.py  # F2, F3b from MCM + graph + roles
  market.py     # Coin Metrics close, Binance volume; sealed split
  targets.py    # T1–T5
  dataset.py    # transforms, sample assembly, feature sets S0–S4
  screen.py     # folds, models, metrics, gate, selection
  holdout.py    # sealed one-shot evaluation
  cli.py        # stages: labels, market, weeks, dictionary, mcm, features, screen, holdout
tests/research/onchain_b2/
research/onchain-b2-2026-10-13/   # CHARTER.md, config/*.json, gates.json, STATE.md, SCREEN.md, selection.json
research_artifacts/onchain-b2/    # gitignored: weeks/, graphs/, mcm/, features/, sealed/, logs/
```

`onchain_b` modules are reused unchanged (sources, weekly, neighborhoods,
matching, dictionary, mcm).

## 13. Testing

Each feature function on hand-built weeks with known answers (exchange in/out,
deposit-like rule at the 90 % boundary, whale top-100 ties, motif histogram);
transforms (no future values in z-scores); targets on toy prices; fold
construction with purge; gate arithmetic and selection ranking; sealing (dev
loader raises on 2025 dates; holdout refuses without a committed selection);
S3 reader through an injected filesystem with a local parquet file; one real-day
smoke read.

## 14. Checkpoints

- **B2-CP1:** all weeks 2017-01-02 → 2026-10-05 built, with the exclusion list.
- **B2-CP2:** features S0–S4 complete; dictionary and MCM done.
- **B2-CP3:** screen table and selection committed.
- **B2-CP4:** holdout result, or the recorded decision not to open it.
