# Branch B7 — feature and target engineering on the hourly on-chain tables

Status: design approved in conversation 2026-10-22 ("go with the recommended order … keep
working autonomously", "you have full permission"). Branch
`research/onchain-replication-b-2026-10-12`. No new chain data: B7 re-engineers the hourly
series B4 and B6 already produced and adds tail and jump targets.

## 1. Decisions

1. Exploratory with a pre-declared plan (`PLAN.md`); both sealed windows are spent.
2. Items in the recommended order: (1) multi-scale, deseasonalised temporal features with
   early-stopped tree models; (2) tail and jump targets. Item (3), the per-token hourly
   panel, is a separate study (B8) if time allows.
3. One baseline for every comparison, as strong as the price data allows: B4's price
   features, B5's intraday features and two range-based volatility features from
   1-minute closes.

## 2. Questions

- **Q1 engineering.** Do multi-scale, deseasonalised features of the same 15 B4 series
  beat B4's two transforms (Y1 vs X1)? Do B6's 39 series add under the new engineering
  (Y2 vs Y1)? Does early stopping with larger trees beat the fixed B4 tree settings
  (trees_es vs trees_fixed on Y2)?
- **Q2 targets.** Do on-chain features forecast tail moves (J6, J24) and the size of the
  largest 5-minute move (M6, M24), beyond volatility levels (V6, V24)?

## 3. Inputs (all on disk)

| Input | Source |
|---|---|
| 15 B4 raw hourly series (`eth_*`, `stable_*`, `act_*`) | `research_artifacts/onchain-b4/features/hourly_raw.parquet` |
| B4's 22 transformed flow columns (X1 reference) | `research_artifacts/onchain-b4/features/hourly.parquet` |
| 39 B6 raw hourly series (`gs_*`, `tk_*`, `cl_*`, `is_*`) | `research_artifacts/onchain-b6/features/hourly_raw.parquet` |
| Large-transfer records (event times) | `research_artifacts/onchain-b6/large/*.parquet` |
| ETH hourly close and quote volume | B4 `market/hourly_dev.json` + `sealed/hourly_sealed.json` |
| ETH 1-minute closes 2019-01-01 → 2026-10-12 | `research_artifacts/onchain-b6/market/minutes_ETH.parquet` |
| DVOL and hourly near-expiry implied volatility | B5 files via B6 `dataset6.market_hourly` |

## 4. Features

### 4.1 New engineering per raw series (6 per series; x → log1p(x))

| Name | Definition |
|---|---|
| `__ex1` | log1p(x) − log1p(profile), where profile = median of the same weekday-hour slot over the previous 8 weeks (causal; NaN until 4 earlier occurrences) |
| `__z1` | z-score against the previous 168 hours (min 120), clip ±10 |
| `__s6z` | log1p(6-hour sum) z-scored against the previous 720 hours of that sum (min 480) |
| `__s24z` | log1p(24-hour sum) z-scored against the previous 720 hours (min 480) |
| `__s168z` | log1p(168-hour sum) z-scored against the previous 2,160 hours (min 1,440) |
| `__burst` | log1p(x) − log1p(mean over the previous 24 hours) |

All windows end at hour h (the hour's own value included), as B4.

### 4.2 Event-time and interactions (Y sets only)

- `ev_since_10m`, `ev_since_50m`: log1p(hours since the last stablecoin deposit of
  ≥ $10M / ≥ $50M, capped at 168), from the large-transfer records.
- `ix_stable_val_rv6` = `stable_in_val__ex1` × `px_rv6`; `ix_stable_cnt_rv24` =
  `stable_in_cnt__ex1` × `h0_rv24`; `ix_eth_val_rv6` = `eth_in_val__ex1` × `px_rv6`.

### 4.3 Baseline

`h0_` (8, B4), `px_` (5, B5 intraday), `rg_range1` = log(max / min of the hour's 1-minute
closes), `rg_range24` = mean of the last 24 hourly log ranges. Track B adds `mk_dvol`,
`mk_dvol_chg24`, `mk_iv`.

### 4.4 Sets

| Set | Columns |
|---|---|
| X0 | baseline |
| X1 | X0 + B4's 22 transformed flow columns |
| Y1 | X0 + new engineering of the 15 B4 series (90) + event-time (2) + interactions (3) |
| Y2 | Y1 + new engineering of the 39 B6 series (234) |

## 5. Targets (decision at the end of hour h)

| ID | Definition | Loss |
|---|---|---|
| V6, V24 | log realised volatility of hourly log returns over the next 6 / 24 h (B4) | MSE |
| J6, J24 | 1 if the absolute log return over the next 6 / 24 h exceeds 3·σ̂·√k, σ̂ = √(mean r² over the previous 720 h) | log loss |
| M6, M24 | log of the largest absolute 5-minute log return (minute closes, 5-minute spacing, evaluated every minute) within the next 6 / 24 h | MSE |

## 6. Models

- **ridge:** B2 `fit_predict` linear family (alpha grid, inner window 8,760 h, fallback
  100); logistic for J targets.
- **trees_es:** HistGradientBoosting, learning_rate 0.05, max_leaf_nodes 15,
  min_samples_leaf 50, l2 1.0, random_state 11, up to 600 iterations; the iteration
  count is chosen on the time-ordered last 10 % of the training window from staged
  predictions (minimum 20), then the model is refitted on the whole training window
  with that count. Classifier for J targets.
- **trees_fixed:** B4's settings (100 iterations, 7 leaves, min leaf 30), on Y2 only.

## 7. Comparisons and criteria

Tracks: A′ 2019-04-01 → 2024-12-31 (test years 2020–2024, group 2020–24), B
2021-04-01 → 2026-10-12 (test years 2022–2026, groups 2022–24 and 2025–26). Purge =
horizon; walk-forward expanding; min_train 2,000 rows.

Per track, target and family (ridge, trees_es): Y1 vs X1, Y2 vs Y1, X1 vs X0, Y2 vs X0;
plus trees_es(Y2) vs trees_fixed(Y2). Bootstrap: circular 168-row blocks, 2,000 draws,
seed 20261022. Criteria: A′ — interval upper end < 0 and better in ≥ 3 of 5 years;
B — upper end < 0 in 2022–24 and mean < 0 in 2025–26. Every row also reports the loss
against a constant forecast (training mean / base rate).

## 8. Compute

Features: minutes. Forecasts: ≈ 1,200 tree fits of ≤ 600 iterations on ≤ 54k × 329
(≈ 5 s each) plus ridge → about 2 h as a systemd unit. Disk < 1 GB.

## 9. Layout

```
tradingagents/research/onchain_b7/
  config.py, features7.py (seasonal profile, multi-scale, event-time, interactions),
  targets7.py (range features, J and M targets), models7.py (families), forecast7.py
  (runner, criteria, report), cli.py (features, forecast, report)
tests/research/onchain_b7/
research/onchain-b7-2026-10-22/   # CHARTER.md, PLAN.md, config/b7.json, STATE.md, RESULTS.md
research_artifacts/onchain-b7/     # gitignored
```

## 10. Testing

Seasonal profile causal and NaN before 4 occurrences; multi-scale windows end at h;
event-time from toy records; interactions; range features from toy minutes; J and M
targets on toy series with known answers; early-stopping iteration choice on a
time-ordered tail; runner counts, criteria and report.

## 11. Checkpoints

B7-CP1 features and targets built; B7-CP2 comparisons; B7-CP3 `RESULTS.md`.
