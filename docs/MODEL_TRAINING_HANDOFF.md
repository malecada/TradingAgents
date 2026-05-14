# Model Training Handoff — Crypto Price Prediction Pipeline

Self-contained reference for the LightGBM price-prediction models used in the
TradingAgents crypto quant stack. Written for reuse in other projects.

---

## 1. What the model does

Predicts the **future close price** of a crypto asset at a fixed horizon
(`h` days ahead). One model is trained per horizon. Predictions feed a
sizing/strategy layer (Section 6) that converts price forecasts into positions.

- **Task**: regression — target is the absolute price `h` days ahead, not a return or a class.
- **Algorithm**: LightGBM (`LGBMRegressor`), single-threaded.
- **Pooling**: one model per horizon trained across *all coins at once* (BTC+ETH pooled), with coin identity as a categorical integer feature. ~2× the data of per-coin models; lets the model learn cross-asset patterns.
- **Horizons used in production**: h=7 and h=14. Shorter horizons (h=1, h=3) are too noisy — directional accuracy rises monotonically with horizon (h=1 ≈ 68-72%, h=14 ≈ 78-84%).

**Why regression not classification**: a continuous price forecast gives the
sizing layer a magnitude signal (expected move size → position size). A
classification-based variant ("V3") was tested and systematically
underperformed — see `THESIS_FINDINGS.md` §15.

---

## 2. Core files

| File | Role |
|------|------|
| `tradingagents/models/model_utils.py` | Feature engineering: OHLCV → model frame, technical indicators, cross-asset, on-chain, pooling, the `data_transform` causal-shift pipeline |
| `tradingagents/models/lgb_model.py` | LightGBM training: `walk_forward_pooled` (eval), `fit_pooled_full` (single fit for live inference), `predict_pooled` |
| `tradingagents/dataflows/onchain_features.py` | PIT-correct on-chain feature builder (`build_pit_onchain_features`) — extended feature set |
| `tradingagents/dataflows/onchain_store.py` | Bitemporal parquet store (event_ts + as_of_ts) for look-ahead-safe on-chain data |
| `tradingagents/strategies/v2_sizing.py` | Sizing primitives — converts predictions into positions |
| `scripts/evaluate_models_multi.py` | CLI entrypoint — builds dataset, runs walk-forward eval, writes prediction CSVs |
| `scripts/baseline_strategy_v2.py` | CLI — runs the sizing/backtest layer on prediction CSVs |

---

## 3. Feature sets

Two feature sets exist. Both start from the same OHLCV base; the extended set
adds a point-in-time on-chain/derivatives layer.

### 3.1 Canonical set — 78 features

Built by `build_pooled_dataset(..., add_onchain_pit=False)` + `data_transform`.

| Group | Count | Detail |
|-------|:-----:|--------|
| OHLC + derived prices | 8 | `prices` (close), `open`, `high`, `low`, `total_volumes`, `daily_return`, `high_low_spread`, `open_close_spread` |
| Rolling MA + stdev | 8 | `ma_7/14/30`, `vol_7/14/30` (price stdev), `vol_ma_7/30` (volume MA) |
| Technical indicators | 14 | stockstats: `ti_rsi_14`, `ti_rsi_30`, `ti_macd`, `ti_macds`, `ti_macdh`, `ti_boll`, `ti_boll_ub`, `ti_boll_lb`, `ti_atr_14`, `ti_adx`, `ti_cci_20`, `ti_kdjk`, `ti_kdjd`, `ti_wr_14` |
| Cross-asset | 3 | `xa_btc_return`, `xa_eth_btc_ratio`, `xa_btc_dom` (BTC volume as dominance proxy) |
| On-chain (legacy) | 3 | `oc_funding_rate` (Binance funding), `oc_tvl_delta` (DefiLlama TVL pct-change), `oc_stable_delta` (stablecoin mcap pct-change) |
| Price lags | 7 | `lag1`..`lag7` (prior close prices) |
| Calendar | 35 | `Day`, `Month`, `Year` + `day_1`..`day_31` one-hot day-of-month dummies |
| Coin identity | 1 | `coin_int` (categorical integer, added at fit time) |

### 3.2 Extended set — ~193 features

`build_pooled_dataset(..., add_onchain_pit=True)` joins the full
`build_pit_onchain_features()` output (~115 `oc_*` columns) on top of the
canonical set, replacing the 3 legacy `oc_*` columns.

Added groups (point-in-time correct, see Section 5):
- **CoinMetrics Community on-chain** (BTC/ETH only): active addresses, address balance count, MVRV, market cap, exchange flows (in/out, USD + native), hash rate, issuance, supply, supply-on-exchanges, ROI, transfer count, spot volume — plus derived MVRV Z-score (1y + 4y), Puell multiple, net exchange flow + z-score, exchange supply ratio, holder growth.
- **Coinglass derivatives** (Hobbyist tier): aggregated open interest (OHLC), liquidations (long/short/total/asymmetry), long/short ratios (global retail + top-trader by position + by account), taker buy/sell volume + asymmetry, OI-weighted funding — plus derived OI momentum/z-score, OI/market-cap, liquidation z-score, smart-money divergence (top-trader vs retail), taker asymmetry z, funding z, basis z.
- **Deribit DVOL** (BTC/ETH only): implied-volatility index close + 7d change.
- **Perp-spot basis**: `(perp_close − spot_close) / spot_close × 365`.
- **DefiLlama**: per-stablecoin market caps (USDT/USDC/DAI/USDe), multi-chain TVL (Ethereum/BSC/Arbitrum/Solana/Polygon/Base/Optimism), aggregate DEX volume — plus derived 7d/30d changes, USDT dominance, per-chain stablecoin shares.

**Empirical note**: the extended set helps some coins and hurts others. In the
TradingAgents thesis it doubled ETH's risk-adjusted return but slightly hurt
BTC (BTC's canonical baseline was already at its signal ceiling — extra
features added variance via dilution). Production uses **per-coin feature-set
routing**: BTC → 78f canonical, ETH → 193f extended. See `THESIS_FINDINGS.md`
§17-18. Treat the choice of feature set as a per-asset hyperparameter.

### 3.3 The `data_transform` causal shift

`model_utils.data_transform` is critical for look-ahead safety:

1. Adds target columns `prices_h{h}` = `prices.shift(-h)` (price `h` days ahead).
2. **`.shift(1)` on the entire frame** — so the row dated `t` contains only feature values observed strictly *before* `t`. No same-day information leaks into the prediction.
3. Forward-fills then zero-fills residual NaN.
4. Adds lag features, calendar dummies, coin dummy.

Always call `data_transform` **per coin** (not on the pooled frame) so the
`.shift()` respects coin boundaries.

---

## 4. Training protocol

### 4.1 Walk-forward evaluation (`walk_forward_pooled`)

For each unique date at position ≥ `min_train_window`:
1. Train on **all** pooled coin-rows with `date < current_date` (expanding window).
2. Predict all coin-rows with `date == current_date`.
3. Features = every column except `coin_id` and `prices_h*` targets, plus `coin_int`.
4. Fit a fresh `MinMaxScaler` on the training rows; transform train + test with it.
5. Fit a fresh LightGBM; predict.

Output: a long-format DataFrame `[date, coin_id, prediction, actual, ref_price]`
plus metrics (R², MAE, RMSE, MAPE, directional accuracy).

This retrains the model on every bar — expensive but the correct protocol for
fixed-hyperparameter walk-forward. A 4.5-year 2-coin walk-forward on the
193-feature set takes ~4 hours; the 78-feature set is substantially faster.

### 4.2 Single fit for live inference (`fit_pooled_full`)

Fits **one** model on all available rows. Returns a bundle with the booster,
feature names, fitted scaler, and `coin_id → int` map. `predict_pooled(bundle,
feature_row)` applies it to a single new row. Used by the live trading cycle's
daily retrain step.

### 4.3 LightGBM hyperparameters (`_build_lgb`)

```python
LGBMRegressor(
    n_estimators=500,
    max_depth=-1,          # unbounded
    learning_rate=0.05,
    num_leaves=31,
    min_child_samples=20,
    random_state=42,
    verbose=-1,
    n_jobs=1,              # single-threaded — walk-forward trains hundreds of
                           # small models; threading overhead dominates otherwise
)
```

All overridable via `config["prediction_models"]` keys
(`lgb_n_estimators`, `lgb_max_depth`, `lgb_learning_rate`, `lgb_num_leaves`,
`lgb_min_child`).

### 4.4 Pooling universe

**Use a 2-coin pool (BTC+ETH)** as the core. For trading a target altcoin, use
a "2+1" pool `{BTC, ETH, target}` — preserves BTC/ETH signal quality while
giving near-optimal accuracy for the target. **Do not** pool more than ~3 coins:
adding altcoins degrades pooled directional accuracy by 12-22 percentage points
(altcoin noise). This is the single most important pooling rule.

---

## 5. Point-in-time (look-ahead) safety

The extended on-chain features come from a **bitemporal store**
(`onchain_store.py`): every row carries `event_ts` (when the metric refers to)
and `as_of_ts` (when the value became available — includes publication lag,
e.g. CoinMetrics flow metrics get a wider lag for revision risk).

`build_pit_onchain_features(coin, dates)` aligns each query date `t` to the
value whose `as_of_ts ≤ t` (via `pandas.merge_asof`, direction=backward).
Rolling derived features (z-scores, Puell multiple) are computed on the
PIT-aligned series so long windows stabilize without leaking future data.

If reusing in another project: any feature with a publication lag (on-chain,
fundamentals, anything revised after the fact) must go through a bitemporal
store or the backtest will be optimistically biased.

---

## 6. From predictions to positions (sizing layer)

`tradingagents/strategies/v2_sizing.py` — the production sizing layer. Treats
LGB predictions as the raw signal:

1. **Term-structure consensus**: h=7 and h=14 predictions must agree on
   direction (both up or both down) to take a position. Magnitude of agreement
   → confidence.
2. **Vol-targeted Kelly sizing**: position scaled to a 10% annualized vol
   target, half-Kelly fraction, confidence-weighted.
3. **Conditional leverage**: 1-3× depending on signal strength.
4. **SMA30 trend filter**: 1.5× position when aligned with the 30-day SMA
   trend, 0.5× when against. This single filter is empirically ~90% of the
   strategy's risk-adjusted return — the LGB direction signal is a smaller
   contributor than the sizing mechanics.
5. **Risk controls**: 7-day minimum hold with adaptive early exit, 3% stop-loss,
   15% portfolio circuit breaker, 95th-percentile vol cap.

**Key lesson for reuse**: the prediction model is necessary but not sufficient.
Most of the realized edge came from the sizing/trend-filter layer, not raw
forecast accuracy. Budget effort accordingly.

---

## 7. Reproduction commands

```bash
# Canonical 78-feature walk-forward eval (2-coin pool)
python scripts/evaluate_models_multi.py \
    --coins bitcoin ethereum --horizons 7 14 \
    --days 2200 --min-train 365 --models lgb \
    --output-dir data/multi_2coins_v2

# Extended 193-feature walk-forward eval (adds PIT on-chain)
python scripts/evaluate_models_multi.py \
    --coins bitcoin ethereum --horizons 7 14 \
    --days 2200 --min-train 365 --models lgb --onchain-pit \
    --output-dir data/multi_2coins_pit_wf

# 2+1 pool for a target altcoin
python scripts/evaluate_models_multi.py \
    --coins bitcoin ethereum binancecoin --horizons 7 14 \
    --days 2200 --min-train 365 --models lgb \
    --output-dir data/multi_3coins_bnb

# Run the sizing/backtest layer on prediction CSVs
python scripts/baseline_strategy_v2.py --pred-dir data/multi_2coins_v2 --symmetric
```

Output per run: `preds_lgb_h{7,14}.csv` (columns: `date, coin_id, prediction,
actual, ref_price`) + `summary.csv` (R², MAE, RMSE, MAPE, dir_acc per horizon).

---

## 8. Empirical accuracy reference (TradingAgents thesis, 4.5-yr walk-forward)

Pooled directional accuracy (BTC+ETH mixed). R² is ~0.997-0.999 everywhere and
is **not informative** — price-level autocorrelation. Always evaluate on
directional accuracy and downstream PnL, never R².

| Horizon | 78f canonical | 193f extended |
|:-------:|:-------------:|:-------------:|
| h=1  | ~72% | — |
| h=3  | ~74% | — |
| h=7  | ~76% | 78.1% |
| h=14 | ~79% | 83.8% |

Directional accuracy rises with horizon; absolute error (MAPE) also rises with
horizon (h=1 ≈ 2.7%, h=14 ≈ 5-7%). Direction and magnitude are different axes.

---

## 9. Dependencies

- `lightgbm`, `scikit-learn` (MinMaxScaler), `pandas`, `numpy`
- `stockstats` — technical indicators
- `duckdb` — bitemporal on-chain store queries
- Data sources (all free-tier or one cheap key):
  - Binance public API — OHLCV, funding rates, perp klines
  - CoinMetrics Community API — on-chain (no key, BTC/ETH only on free tier)
  - DefiLlama — TVL, stablecoins, DEX volume (no key)
  - Deribit public API — DVOL implied vol (no key, BTC/ETH only)
  - Coinglass — OI, liquidations, long/short ratios, taker volume (Hobbyist
    tier key; full multi-year history available even on Hobbyist)
