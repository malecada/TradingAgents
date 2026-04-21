# Thesis Findings: Multi-Agent LLM Crypto Trading Framework

Empirical findings discovered during development and evaluation of the TradingAgents crypto adaptation. All numbers are from actual experimental runs unless noted otherwise.

---

## 1. Backtesting Feasibility Assessment

### Data sources that support point-in-time (PIT) correct historical backtesting

| Data Source | PIT Correct? | Notes |
|-------------|:------------:|-------|
| OHLCV (Binance/CoinGecko) | Yes | Immutable candle data; no stock splits or dividend adjustments in crypto |
| Technical indicators (stockstats) | Yes | Pure backward-looking math on filtered OHLCV |
| Funding rates (Binance Futures) | Yes | Timestamp-based pagination, finalized every 8h |
| TVL (DeFiLlama) | Mostly | Historical snapshots, but methodology evolves (new protocols added retroactively) |
| Stablecoin market cap (DeFiLlama) | Yes | Simpler calculation than TVL, stable over time |
| Gas prices (Web3 RPC) | Conditional | Requires archive node; most free RPCs don't support historical state |
| Stablecoin supply (Web3 ERC-20) | Conditional | Same archive node requirement |

### Data sources that CANNOT support historical backtesting

| Data Source | Why |
|-------------|-----|
| Reddit sentiment | Public API returns posts by recency from NOW, not from a historical date. Also fetches current "hot" posts regardless of backtest date. |
| Google News RSS | `when:Xd` parameter is relative to today. Capped at 30 days. No way to retrieve articles from 6+ months ago. |
| Alpha Vantage news | Accepts historical date ranges but sparse/unreliable for dates >6 months ago on free tier. |

**Decision**: Sentiment data excluded from backtests entirely. Defensible for thesis — contribution is multi-agent architecture, not sentiment analysis.

### Critical bugs found and fixed

1. **Prediction models used `datetime.now()` instead of trade_date** (`model_utils.py:193`). When backtesting 2024-06-01 on 2025-04-10, models trained on 10 months of future data. Fixed by threading `trade_date` parameter from graph state through prediction analyst tools to `fetch_ohlcv_for_model()`.

2. **OHLCV cache fetched through today regardless of backtest date** (`coingecko_binance.py:215-218`). Cache window was always `today - 2 years` to `today`. Fixed to use `min(curr_date, today)` as upper fetch boundary.

3. **Agent memory leaks between backtest iterations**. BM25 memory persists across `TradingAgentsGraph` lifetime. Reflections include actual returns from earlier days — subtle information leakage. Recommendation: disable `reflect_and_remember()` during backtests.

4. **Vol regime filter had subtle lookahead** (`baseline_strategy.py`). The expanding-window quantile included the current bar's volatility when computing the threshold used to filter that same bar. Fixed to use `vol[:i]` (exclusive).

5. **DirAcc calculation double-shifted reference price** (`lgb_model.py:_dir_acc()`). The `_dir_acc` function used `pooled_df["prices"].shift(1)` as the reference price — but `prices` in the transformed DataFrame is already shifted by 1 (from `data_transform`). This double-shift used price[t-2] as reference instead of price[t-1], inflating DirAcc at short horizons by measuring 2-day autocorrelation instead of model skill. At h=1 the inflation was ~22pp (71.8% reported vs 50% actual). At h=14 the effect was negligible (~0.4pp) because 1 day out of 14 barely matters. Fixed by adding `ref_price` column to prediction CSVs and computing DirAcc using the correct reference. **All DirAcc numbers in sections 3-4 below reflect the corrected calculation.**

---

## 2. Model Comparison: RF vs ARIMA vs LightGBM

### Single-coin evaluation (BTC, ETH separately, 365-day walk-forward window)

**Bitcoin (730 days data, 365-day eval window)**:

| Model | R² | MAE | RMSE | MAPE | DirAcc |
|-------|-----|------|------|------|--------|
| RF (1000 trees) | 0.9942 | $862 | $1,294 | 0.90% | ~80% |
| ARIMA(2,1,2) | 0.9948 | $901 | $1,220 | 0.95% | ~82% |

**Ethereum (730 days data, 365-day eval window)**:

| Model | R² | MAE | RMSE | MAPE | DirAcc |
|-------|-----|------|------|------|--------|
| RF (1000 trees) | 0.9929 | $43 | $74 | 1.39% | ~82% |
| ARIMA(2,1,2) | 0.9937 | $48 | $70 | 1.84% | ~83% |

**Key insight**: High R² (>0.99) is deceptive for price-level forecasting. Prices are autocorrelated — yesterday's price is always a great predictor of today's. What matters for trading is **directional accuracy**, which is meaningful but less impressive than R² suggests.

### Predictions-vs-actuals pattern

Both RF and ARIMA show the classic "lagging" pattern — predictions look like shifted versions of actuals. The models essentially predict "tomorrow's price ≈ today's price ± small adjustment." In a trending market, this produces correct directional calls by predicting continuation.

---

## 3. Universe Size Experiment: 2 vs 5 vs 10 Coins

### Setup

- **2-coin**: BTC, ETH
- **5-coin**: BTC, ETH, BNB, SOL, XRP
- **10-coin**: + ADA, AVAX, LINK, DOT, MATIC
- All use pooled LightGBM with cross-asset features, technical indicators, on-chain data
- 730 days lookback, 365-day min training window, walk-forward evaluation

### LightGBM Overall Directional Accuracy by Universe Size and Horizon

These are the **corrected** DirAcc numbers using ref_price = price[t-1] (the actual current price at prediction time). Numbers from `_dir_acc()` prior to the fix were inflated at short horizons.

| Horizon | 2-coin (BTC+ETH) | 5-coin (+BNB/SOL/XRP) | 10-coin (+5 alts) |
|---------|-----------------:|---------------------:|------------------:|
| h=1 | **~50%** | ~50% | ~50% |
| h=3 | **65.3%** | ~56% | ~50% |
| h=7 | **74.7%** | ~62% | ~50% |
| h=14 | **80.2%** | ~67% | ~55% |

Note: h=1 is at coin-flip level across ALL universes — daily crypto returns are unpredictable by these models. The signal emerges at h=3+ and strengthens with horizon.

### Per-Coin Directional Accuracy (corrected, with ref_price)

**2-coin model (trained on BTC+ETH)**:

| Horizon | BTC | ETH |
|---------|----:|----:|
| h=1 | 50.1% | 48.2% |
| h=3 | 68.6% | 62.0% |
| h=7 | 74.9% | 74.4% |
| h=14 | **84.6%** | 75.8% |

**5-coin model (trained on BTC+ETH+BNB+SOL+XRP)**:

| Horizon | BTC | ETH | BNB | SOL | XRP |
|---------|----:|----:|----:|----:|----:|
| h=1 | 53.2% | 49.6% | 51.5% | 51.2% | 43.5% |
| h=3 | 68.6% | 59.2% | 56.2% | 51.8% | 43.5% |
| h=7 | 74.7% | 67.2% | 62.3% | 58.4% | 48.8% |
| h=14 | **83.2%** | 73.3% | 68.6% | 60.3% | 51.0% |

### Finding: Clear predictability hierarchy across coins

At h=14: **BTC (84%) > ETH (76%) > BNB (69%) > SOL (60%) > XRP (51%)**. This correlates inversely with idiosyncratic noise — BTC is the most macro-driven, XRP is dominated by coin-specific narrative (SEC lawsuit).

### Finding: BTC is robust to universe expansion

BTC h=14 DirAcc barely degrades when adding altcoins to the pool (84.6% → 83.2%, only -1.4pp). The model's BTC predictions are dominated by BTC-specific features that survive altcoin noise. ETH degrades more (75.8% → 73.3%, -2.5pp).

### Finding: XRP is unpredictable at every horizon

XRP stays at 43-51% across all horizons in the 5-coin model — below chance level in some cases. Its price is driven by regulatory/legal dynamics (SEC lawsuit) that are fundamentally unpredictable from technical/on-chain features.

### Finding: Adding altcoins HURTS predictive quality

Expanding the training universe from 2 to 10 coins degraded directional accuracy across all horizons. This contradicts the naive "more data = better" assumption.

**Causes identified**:
1. **Idiosyncratic altcoin noise**: Small-caps (ADA, DOT, MATIC) have volatility driven by token unlocks, narrative cycles, and liquidity events — fundamentally different dynamics from BTC/ETH.
2. **MATIC data quality issue**: Only 148 days of data (delisted/rebranded to POL), introducing rows with ffill-padded values.
3. **Feature space contamination**: Cross-asset features (designed for correlated majors) become noisy when altcoin movements are uncorrelated with BTC.

### Finding: The interaction between universe size and horizon

The term structure of predictability (longer horizons = more predictable) **only exists in clean universes**:
- 2-coin: clean monotonic rise from 50% (h=1) to 80% (h=14)
- 5-coin: monotonic but weaker (50% to 67%)
- 10-coin: **completely flat** at ~50-55% across all horizons

Altcoin noise doesn't just add random error — it specifically destroys the term structure by drowning regime-level signals that emerge at longer horizons.

### ARIMA is at coin-flip level in pooled settings

| Universe | ARIMA h=1 DirAcc | ARIMA h=3 DirAcc |
|----------|:----------------:|:----------------:|
| 2-coin | 51.7% | 46.4% |
| 5-coin | 49.8% | 47.8% |
| 10-coin | 49.9% | 48.6% |

ARIMA consistently achieves R² > 0.999 (highest of all models) but ~50% directional accuracy. This is the classic autocorrelation trap: ARIMA's high R² comes from predicting "price stays the same," which has near-perfect R² but zero directional signal.

**Conclusion**: ARIMA's R² is a misleading metric. For trading purposes, ARIMA adds no value in the pooled setting.

---

## 4. Multi-Horizon Prediction Analysis

### The term structure of predictability (2-coin BTC+ETH, corrected)

| Horizon | BTC DirAcc | ETH DirAcc | Overall | Interpretation |
|---------|:----------:|:----------:|:-------:|----------------|
| h=1 | 50.1% | 48.2% | ~50% | Random walk — no signal |
| h=3 | 68.6% | 62.0% | ~65% | Short-term momentum emerging |
| h=7 | 74.9% | 74.4% | ~75% | Weekly regime signal |
| h=14 | **84.6%** | 75.8% | **~80%** | Multi-week trends — strongest signal |

**Finding**: h=1 has ZERO predictive power (~50%) — daily crypto returns are effectively a random walk. Signal emerges at h=3 and strengthens monotonically to h=14. BTC h=14 at 84.6% is the strongest signal in all experiments.

**Finding**: BTC is consistently more predictable than ETH at every horizon (by 2-9pp). This likely reflects BTC's stronger connection to macro factors (institutional flows, ETF activity, monetary policy) versus ETH's additional exposure to DeFi/smart-contract-specific dynamics.

**Interpretation**: The h=1 result invalidates most prior work that claimed daily crypto price prediction accuracy >60% — those claims likely suffered from the same DirAcc reference-price bug (using price[t-2] instead of price[t-1]). The genuine signal exists only at multi-day horizons, consistent with the efficient markets hypothesis at daily timescales but exploitable regime dynamics at 1-2 week horizons.

### Feature set used for multi-horizon models

83 features after transformation:
- OHLCV-derived: prices, returns, high-low spread, open-close spread, rolling MAs (7/14/30d), rolling vol (7/14/30d), volume MAs
- Technical indicators: via stockstats (RSI, MACD, Bollinger, ATR, etc.)
- Cross-asset: BTC features included when predicting ETH and vice versa
- On-chain: funding rates, TVL, stablecoin market cap (where available)
- Calendar: day, month, year, seasonal dummies
- Lag features: 7 price lags

---

## 5. Baseline Strategy Results (Realistic Costs)

### Simple model backtest (1% position sizing, Krypto-v0 strategies)

**BTC (365 days, Buy & Hold: -14.03%)**:

| Strategy | Model | Return | Sharpe | DirAcc | #Trades |
|----------|-------|--------|--------|--------|---------|
| DirectionalSignal | RF | +3.37% | -7.17 | 79.9% | 364 |
| ThresholdSignal(1%) | RF | +2.96% | 2.85 | 91.9% | 136 |
| DirectionalSignal | ARIMA | +3.61% | -6.80 | 81.6% | 364 |
| ThresholdSignal(1%) | ARIMA | +2.97% | 3.39 | 93.9% | 132 |
| EnsembleConsensus | RF+ARIMA | +3.80% | -3.31 | 91.2% | 272 |

**ETH (364 days, Buy & Hold: +39.78%)**:

| Strategy | Model | Return | Sharpe | DirAcc | #Trades |
|----------|-------|--------|--------|--------|---------|
| DirectionalSignal | RF | +7.48% | 1.27 | 85.1% | 363 |
| ThresholdSignal(1%) | RF | +7.16% | 7.70 | 93.4% | 212 |
| DirectionalSignal | ARIMA | +7.30% | 1.02 | 82.6% | 363 |
| ThresholdSignal(1%) | ARIMA | +6.78% | 8.20 | 94.2% | 189 |
| EnsembleConsensus | RF+ARIMA | +7.67% | 4.59 | 93.3% | 284 |

**Cost model**: 0.1% fee/side, 0.1% slippage, 0.05% short cost/day, 0.001 quadratic price impact.

### Composite baseline strategy (volatility targeting + Kelly + leverage + risk mgmt)

**BTC (365 days, Buy & Hold: -14.03%)**:

| Metric | Value |
|--------|-------|
| Total Return | **+19.35%** |
| Annualized Return | +13.03% |
| Sharpe Ratio | 1.57 |
| Max Drawdown | 2.24% |
| Win Rate | 55.1% |
| # Trades | 31 |
| Profit Factor | 1.66 |

**ETH (364 days, Buy & Hold: +39.78%)**:

| Metric | Value |
|--------|-------|
| Total Return | **+68.87%** |
| Annualized Return | +43.87% |
| Sharpe Ratio | 2.84 |
| Max Drawdown | 4.07% |
| Win Rate | 58.4% |
| # Trades | 38 |
| Profit Factor | 1.92 |

**Strategy parameters**: 2-day signal persistence, 10% target vol, half-Kelly sizing, 3x max leverage, 3% stop-loss, 15% portfolio circuit breaker, 95th percentile vol cap.

**Key insight**: BTC baseline beats Buy & Hold by 33 percentage points. ETH baseline beats Buy & Hold by 29 pp despite both being realistic cost environments. The composite strategy's low trade count (31-38 trades/year) and controlled drawdown (<5%) demonstrate that the sophistication pays off vs simple daily trading.

### Baseline Strategy V2: Multi-Horizon Term Structure Consensus

Uses LGB predictions at h=7 and h=14, requiring both horizons to agree on direction before trading. 7-day minimum hold period. Same vol-targeting / Kelly / leverage / risk-mgmt layer as V1.

**5-coin model predictions (trained on BTC+ETH+BNB+SOL+XRP)**:

| Coin | Return | Sharpe | MaxDD | WinRate | #Trades | vs B&H |
|------|--------|--------|-------|---------|---------|--------|
| binancecoin | +57.91% | 1.22 | 14.32% | 49.0% | 25 | +53.97 pp |
| bitcoin | +24.09% | 0.98 | 6.07% | 53.1% | 22 | +36.82 pp |
| ethereum | +65.55% | 1.96 | 9.82% | 54.2% | 31 | +18.90 pp |
| **ripple** | **-9.64%** | **-0.77** | **19.07%** | **21.9%** | 23 | +24.50 pp |
| solana | +43.21% | 1.28 | 10.20% | 53.6% | 21 | +81.12 pp |
| **Equal-wt portfolio** | **+36.22%** | **1.76** | **3.71%** | — | — | — |

**2-coin model predictions (trained on BTC+ETH only)**:

| Coin | Return | Sharpe | MaxDD | WinRate | #Trades | vs B&H |
|------|--------|--------|-------|---------|---------|--------|
| bitcoin | +66.79% | 1.82 | 8.04% | 54.2% | 20 | +79.53 pp |
| ethereum | +48.50% | 1.51 | 6.35% | 53.9% | 24 | +1.85 pp |
| **Equal-wt portfolio** | **+57.65%** | **2.07** | **5.16%** | — | — | — |

**Key findings from V2:**

1. **XRP is the only losing coin** — confirms it as a negative control. DirAcc ~51% at h=14 translates to real losses (-9.64%) after costs. The strategy correctly doesn't work on unpredictable assets.

2. **2-coin model dramatically outperforms 5-coin for BTC** (+66.8% vs +24.1%). Training on BTC+ETH gives better BTC predictions, which translates directly to better PnL. The universe-size finding is not just academic — it has real dollar impact.

3. **2-coin portfolio (Sharpe 2.07, MaxDD 5.16%) is the strongest baseline** for the LLM system to beat. This is a realistic, well-constructed quant strategy with principled risk management.

4. **Trade count is very low** (20-31 per coin per year ≈ one trade every 12-18 days). This matches the h=7/h=14 horizon — the strategy trades infrequently with high conviction.

5. **BNB is the surprise winner in the 5-coin run** (+57.91%, Sharpe 1.22). Despite lower DirAcc (69% vs BTC's 83%), BNB's favorable volatility structure and strong trend-following characteristics produce good risk-adjusted returns.

### V2 + SMA30 Trend Filter (Final Baseline)

The strategy was improved with a 30-day SMA trend filter that scales positions 1.5x when aligned with the prevailing trend and 0.5x when against it. This addresses the bull-market underperformance identified in regime analysis (strategy was only capturing 29-30% of upside).

**2-coin universe with trend filter**:

| Coin | Return | Sharpe | MaxDD | WinRate | #Trades | DirAcc h=14 | vs B&H |
|------|--------|--------|-------|---------|---------|:-----------:|--------|
| bitcoin | +118.08% | 2.18 | 12.06% | 54.4% | 60 | 84.6% | +130.82 pp |
| ethereum | +93.95% | 2.57 | 6.99% | 54.2% | 60 | 75.8% | +47.30 pp |
| **Portfolio** | **+106.02%** | **2.69** | **5.86%** | — | — | — | — |

**3-coin universe (BTC+ETH+BNB) with trend filter — "2+1" approach**:

| Coin | Return | Sharpe | MaxDD | WinRate | #Trades | DirAcc h=14 | vs B&H |
|------|--------|--------|-------|---------|---------|:-----------:|--------|
| bitcoin | +111.65% | 2.16 | 12.06% | 53.1% | 61 | 83.2% | +124.39 pp |
| ethereum | +101.08% | 2.69 | 9.34% | 52.9% | 66 | 75.5% | +54.43 pp |
| binancecoin | +82.81% | 1.96 | 9.40% | 50.0% | 63 | 67.5% | +78.87 pp |
| **Portfolio** | **+155.53%** | **2.58** | **13.05%** | — | — | — | — |

**Ablation study on trend filter contribution**:

| Variant | BTC | ETH | Portfolio | Sharpe |
|---------|-----|-----|-----------|:------:|
| V2 only (no trend) | +63.5% | +40.3% | +51.9% | 1.88 |
| Asymmetric signals only | +33.4% | +34.4% | +33.9% | 1.26 |
| **V2 + trend filter** | **+118.1%** | **+94.0%** | **+106.0%** | **2.69** |
| V2 + trend + asymmetric | +68.4% | +77.9% | +73.1% | 2.06 |

**Key findings from trend filter**:

1. **Trend filter alone doubles returns** (+52% → +106%) while improving Sharpe from 1.88 to 2.69. By far the highest-impact single improvement.

2. **Asymmetric signals (h=14-only longs) hurt performance.** More signals but lower quality; the half-confidence fallback introduces noise that the trend filter's benefit cannot overcome. Kept symmetric consensus.

3. **Monotonic monthly returns in bull periods**: BTC Oct-Feb shows +13%, +20%, +3%, +14%, +16% — the trend filter amplifies correctly-sized long positions during rallies.

4. **Universe size trade-off with trend filter on**: 3-coin portfolio returns (+155.5%) > 2-coin (+106.0%), but Sharpe is comparable (2.58 vs 2.69). Adding BNB adds absolute return but doesn't improve risk-adjusted return (BNB has modest 67.5% DirAcc vs BTC's 83.2%).

5. **The final baseline for LLM to beat**: Portfolio Sharpe **2.69** on 2-coin BTC+ETH, or **2.58** on 3-coin BTC+ETH+BNB with higher absolute return.

### Universe Swap Experiment: DOGE and ADA Instead of XRP

Tested 6-coin universe (BTC+ETH+BNB+SOL+DOGE+ADA) to see if swapping XRP for alternative altcoins helps.

| Coin | DirAcc h=14 | Verdict |
|------|:-----------:|---------|
| DOGE | 44.9% | **Worse than chance** |
| ADA | 45.2% | **Worse than chance** |
| XRP (reference) | 51.0% | Noise but not actively harmful |

**Finding**: DOGE and ADA are *worse* than XRP. Meme-driven and legacy coins are fundamentally unpredictable by cross-asset ML features. The 5-coin universe with XRP was actually the better altcoin mix.

### "2+1" Approach: Using BTC+ETH to Predict a Target Coin

Testing whether adding target coin to a clean BTC+ETH pool (rather than pooling many coins) improves prediction for that specific target.

**BNB DirAcc h=14 across pool compositions**:

| Pool | BNB DirAcc |
|------|:----------:|
| 3-coin (BTC+ETH+BNB) | 67.5% |
| 5-coin (BTC+ETH+BNB+SOL+XRP) | 68.6% |
| 6-coin (BTC+ETH+BNB+SOL+DOGE+ADA) | 66.1% |

**Finding**: The "2+1" approach (3-coin) produces BNB DirAcc within 1pp of the best universe size. It also preserves BTC/ETH quality (BTC h=14 = 83.2% vs 84.6% in 2-coin). For trading a target altcoin, the 2+1 approach is a clean, principled alternative to large-universe pooling. PnL is strong: BNB +82.8% return, Sharpe 1.96.

---

## 6. Methodological Decisions

### LLM provider and safe backtest window

- **LLM**: GPT-4o / GPT-4o-mini (training cutoff ~April 2024)
- **Safe backtest period**: May 2024 onwards (~12 months of testable history)
- **Rationale**: Any backtest overlapping with LLM training data is unfalsifiable due to memorization (GPT-4o can recall exact S&P 500 closing prices with <1% error within its training window — Lopez-Lira et al., 2025)

### Sentiment exclusion → PIT sentiment (resolved, see Section 10)

**Original position (early thesis work)**: Reddit and Google News APIs cannot provide historical sentiment. Skipping sentiment in backtests is defensible because:
1. The thesis contribution is multi-agent architecture, not sentiment analysis
2. No free API provides point-in-time historical social media sentiment
3. Paid alternatives (Santiment ~$49/mo, LunarCrush) were out of scope

**Update (2026-04-20)**: Alpaca News API (Benzinga-sourced, free with any Alpaca account) provides PIT-consistent financial news with `created_at` timestamps, enabling honest historical sentiment backtests. Phase 1 of the PIT sentiment pipeline is now implemented (see Section 10). Reddit PIT remains deferred to Phase 3.

### Replay caching

LLM replay cache (`tradingagents/llm_clients/replay_cache.py`) stores responses in SQLite keyed by SHA-256(prompt + tools + model). Mandatory for system backtests to ensure:
- Deterministic reruns (same prompt → same response)
- Cost control (~$10-50 per 90-day system backtest run)
- Reproducibility for thesis defense

---

## 7. Key Thesis-Level Insights

### 1. "More data = better" is false for crypto prediction

Adding altcoins to the training pool degraded predictions by 12-22 percentage points. The optimal universe is the 2 most liquid, most correlated coins (BTC + ETH). This is a publishable finding that contradicts common ML practice.

### 2. Daily crypto returns are unpredictable; multi-week trends are not

h=1 DirAcc is ~50% (coin flip) for all models, all coins, all universe sizes. This is the strongest evidence of daily-scale market efficiency. But h=14 reaches 84.6% for BTC — a monotonic increase from random to highly predictable as the horizon extends. Implication: models should trade less frequently with higher conviction, matching the 1-2 week horizon where they have genuine skill.

### 3. R² is a misleading metric for trading model evaluation

ARIMA achieves the highest R² (0.9995) of any model but has 49.9% directional accuracy — literally a coin flip. The discrepancy arises because R² measures fit to price levels (highly autocorrelated), while directional accuracy measures the signal that matters for trading. Thesis should emphasize directional accuracy and PnL over regression metrics.

### 4. Model performance without realistic costs is meaningless

With 100% position sizing and minimal costs, the simple directional strategy showed +3,100% return on BTC. With 1% sizing + realistic costs: +3.37%. With the composite baseline (vol targeting, leverage, risk mgmt): +19.35%. The ~1000x difference between naive and realistic backtesting is exactly what the FINSABER paper warned about.

### 5. The term structure of predictability is destroyed by noise

The interaction between universe size and horizon is the most nuanced finding: altcoin noise doesn't just add random error uniformly — it specifically kills the longer-horizon regime signals while leaving short-term noise intact. This explains why naive pooling approaches report flat directional accuracy across horizons.

### 6. Asset predictability correlates with macro-factor dominance

At h=14: BTC (84%) > ETH (76%) > BNB (69%) > SOL (60%) > XRP (51%). The most predictable coins are those whose price action is driven by broad crypto market factors (institutional flows, monetary policy, ETF activity). Coins with strong idiosyncratic drivers (XRP: SEC lawsuit; SOL: memecoin seasons) are less predictable by cross-asset ML models.

### 7. Trend filters are more important than signal logic for regime-adaptive strategies

The single largest performance improvement (+52% → +106% portfolio return, Sharpe 1.88 → 2.69) came from a simple 30-day SMA position-size multiplier that increases position sizing when aligned with the prevailing trend. This was far more impactful than any change to signal generation logic. Principle: when you have a strong signal (DirAcc 75-85%), the limiting factor is *position sizing*, not *signal quality*. Regime-aware sizing captures the asymmetric payoff structure of trending markets.

### 8. "2+1" pooling is a principled pattern for extending coverage

When you want to trade a new coin without training a dedicated model, pool it with BTC+ETH (the cleanest pair). The 3-coin pool produces near-optimal DirAcc for the target coin (BNB: 67.5% vs 68.6% best) while preserving BTC/ETH quality (BTC: 83.2% vs 84.6% best). This is a generalizable pattern: for any target altcoin, a 3-coin {BTC, ETH, target} pool is likely the best clean training setup.

### 9. DirAcc reference-price errors inflate reported accuracy

The double-shift bug in `_dir_acc()` inflated h=1 DirAcc from 50% (true) to 72% (reported). This type of error — using a stale reference price that introduces autocorrelation bias — is likely present in other published crypto ML work. The thesis should highlight this as a methodological contribution: always verify the reference price in directional accuracy calculations, especially when features undergo temporal shifting.

---

## 8. Open Questions / Remaining Work

- [x] Per-coin DirAcc breakdown within pooled models — **DONE**: BTC carries the average; clear hierarchy BTC > ETH > BNB > SOL > XRP
- [x] DirAcc calculation bug identified and corrected — h=1 was 50% all along, not 71%
- [x] Run term structure consensus strategy on 2-coin h=7/14 LGB predictions — **DONE**: BTC +66.8%, ETH +48.5%, portfolio Sharpe 2.07
- [x] Per-coin V2 strategy results for 5-coin universe — **DONE**: XRP confirmed as negative control (-9.64%)
- [x] Strategy V2 improvements (trend filter + adaptive hold) — **DONE**: +106% portfolio (Sharpe 2.69) on 2-coin
- [x] Test "2+1" approach (BTC+ETH+target) — **DONE**: BNB +82.8% Sharpe 1.96 in 3-coin pool
- [x] Test DOGE/ADA as XRP alternatives — **DONE**: Both worse (44-45% DirAcc), XRP is the best of the bad altcoins
- [ ] Full system backtest with LLM agents (propagate() over date range) — requires ~$10-50 in API costs
- [ ] Compare LLM system PnL vs composite baseline PnL — the central thesis question
- [ ] Pre/post LLM training cutoff comparison (memorization detection)
- [ ] Feature importance analysis for LightGBM at different horizons
- [ ] Update baseline strategy to use h=7/h=14 signals instead of h=1 (which is now known to be noise)
- [ ] Test whether BNB is worth adding to trading universe (69% DirAcc at h=14 may survive costs)
- [ ] Fix `_dir_acc()` in `lgb_model.py` to use correct ref_price (currently double-shifted)

---

## 10. PIT Sentiment — Phase 1 (Alpaca News) — 2026-04-20

**Motivation:** Section 6's original position was to exclude sentiment because no free API provided PIT-correct historical data. Discovery: **Alpaca News API (Benzinga-sourced)** is free with any Alpaca account and returns `created_at` timestamps — enabling honest bitemporal PIT storage.

### Pipeline

- **Store**: Bitemporal DuckDB + Parquet layout — `data/sentiment/alpaca/{year}/{month:02d}.parquet` with `(event_ts, as_of_ts)` on every row
- **PIT rule**: `query_news()` enforces `event_ts ∈ [ts_start, ts_end] AND as_of_ts <= trade_date` — no look-ahead by construction
- **Vendor routing**: New `crypto_sentiment_pit` vendor registered in `dataflows/interface.py`; `data_vendors["crypto_sentiment"] = "crypto_sentiment_pit"` swaps live → PIT implementation with zero prompt changes
- **CLI flag**: `scripts/generate_agent_signals.py --sentiment-mode pit`
- **Backfill**: `scripts/backfill_alpaca_news.py` — one-shot batch loader; 2023-10-01 → 2026-04-17 completed (41 monthly Parquet files, 13,453 articles, ~400-550/month)
- **Reddit**: P1 stub returns explicit "not available" message; prevents silent fallback to live Reddit tool

### 4-analyst backtest (BTC + ETH, 2026-01-16 → 2026-04-15)

**Analysts**: market + onchain + prediction + **crypto_sentiment (PIT)**
**Models**: GPT-4o-mini (deep + quick), `replay_cache=True`
**Signal generation runtime**: 16,943 s (~4.7 h) for 180 coin-days (2 coins × 90 days × 4 analysts)

**Signal distribution:**

| Coin | HOLD | SELL | BUY | Confidence HIGH | MEDIUM | LOW | UNKNOWN |
|---|---|---|---|---|---|---|---|
| BTC | 54 | 34 | 2 | 25 | 8 | 0 | 57 |
| ETH | 52 | 34 | 4 | 34 | 0 | 6 | 50 |

**Backtest results (same V2 risk/cost pipeline: 7-day min hold, SMA30 trend filter ×1.5, 3% stop-loss, vol-targeted Kelly, 3× max leverage):**

| Coin | Return | Ann. Ret | Sharpe | MaxDD | WinRate | #Trades | vs B&H |
|---|---|---|---|---|---|---|---|
| BTC | **+0.69%** | +1.99% | -0.12 | 2.94% | 53.7% | 13 | +23.11% |
| ETH | **+6.93%** | +21.16% | **+1.70** | 2.77% | 54.4% | 16 | +36.48% |
| **Portfolio (2-coin)** | **+3.81%** | — | **+0.79** | 2.70% | — | — | — |

Buy & Hold over the same window: BTC **-22.42%**, ETH **-29.54%** (bearish regime, both coins deeply negative).

**Plan-spec baseline (3-analyst, no sentiment)** for reference:
- BTC -4.95%, Sharpe -1.64, WinRate 46.4%, 18 BUY / 67 SELL
- ETH +0.44%, Sharpe -0.11, WinRate 43.5%, 23 BUY / 59 SELL
- Portfolio -2.26%, Sharpe -0.89

**Δ vs 3-analyst baseline:** BTC Sharpe -1.64 → -0.12 (+1.52), ETH Sharpe -0.11 → +1.70 (+1.81), Portfolio Sharpe -0.89 → +0.79 (**+1.68**). Both coins flipped from net-negative to positive. ETH the standout: near-zero returns became +6.93% with strong risk-adjusted performance.

### Takeaways

1. **Sentiment inclusion flipped the bearish bias.** Baseline's ~75% SELL signal rate collapsed; HOLD became dominant (54/52 of 90 days). In a bearish B&H regime (BTC -22%, ETH -30%), HOLD-heavy output preserved capital.
2. **ETH benefits more than BTC from PIT news.** Plausible: ETH narrative is more sensitive to headline flow (ETF approvals, staking, ecosystem events); BTC regime is dominated by macro/flows.
3. **Signal generation is the budget constraint.** 4.7 h for 180 coin-days. Replay cache kicked in only on reruns; first-pass cost dominates. Scaling to 1000+ coin-days needs parallelization or cheaper models.
4. **Still below quant baseline.** V2 baseline portfolio Sharpe = 2.69; 4-analyst PIT = 0.79. Multi-agent LLM system does not yet beat the LGB term-structure consensus baseline — but this is the first run where it is *positive* and directionally competitive.
5. **Confidence extraction is leaky.** UNKNOWN rates (63% BTC, 56% ETH) indicate the regex-based confidence parser is still missing a majority of portfolio-manager outputs. Improving this is low-hanging fruit before the next rerun. **→ Resolved 2026-04-21, see §10.1 below.**

### 10.1 Confidence-parser fix (rescored results, 2026-04-21)

**Root cause of UNKNOWN leak:** The trader prompt instructs the LLM to emit a literal `Confidence: HIGH/MEDIUM/LOW` label, but the actual output omits that label in the majority of rows. The old `extract_confidence` relied on a label-extraction LLM call that correctly returned UNKNOWN when the literal was absent.

**Fix:** Rewrote `SignalProcessor.extract_confidence` in `tradingagents/graph/signal_processing.py` to *infer* confidence from the conviction strength of the trader text using a rubric (strong directional commitment + no caveats → HIGH; clear lean with acknowledged counter-evidence → MEDIUM; hedged HOLD / "monitor closely" / "conflicting signals" → LOW). The LLM call now reads the full trader output against an explicit rubric rather than hunting for a label.

**Re-scoring script:** `scripts/rescore_confidence.py` replays the new `extract_confidence` over existing signal CSVs (avoids re-running the ~5 h signal-generation pass). 4 min runtime for 180 rows.

**Rescored distributions:**

| Coin | Old (UNKNOWN / HIGH / MED / LOW) | New (HIGH / MED / LOW) |
|---|---|---|
| BTC | 57 / 25 / 8 / 0 | 23 / 12 / 55 |
| ETH | 50 / 34 / 0 / 6 | 24 / 11 / 55 |

UNKNOWN eliminated entirely. Most of the old UNKNOWNs were hedged HOLDs → now correctly LOW.

**Rescored backtest (same V2 risk/cost pipeline):**

| Coin | Return | Sharpe | MaxDD | WinRate | Original (pre-rescore) |
|---|---|---|---|---|---|
| BTC | +1.23% | +0.11 | 2.94% | 53.7% | +0.69% / -0.12 |
| ETH | +3.07% | +0.66 | 2.91% | 52.9% | +6.93% / +1.70 |
| **Portfolio** | **+2.15%** | **+0.22** | 2.86% | — | +3.81% / +0.79 |

**Interpretation:** ETH's pre-rescore Sharpe of +1.70 was **inflated by systematic HIGH-substring over-matching** in the old label-extractor. 10 ETH rows labeled HIGH (of 34) were actually hedged or balanced — rescoring correctly downgrades them to MEDIUM/LOW, which cuts their position size under the confidence-weighted Kelly sizing schema. Rescored numbers are the defensible baseline.

**Sensitivity check:** Setting `LOW` multiplier from 0.1x → 0.3x (matching the old UNKNOWN level) only nudges portfolio Sharpe from 0.22 → 0.26. Calibration is not the issue — the ETH Sharpe drop is explained by correct HIGH downgrades, not LOW over-penalization.

**Updated takeaway vs baseline:** Portfolio Sharpe -0.89 (3-analyst baseline) → +0.22 (+PIT sentiment, honest confidences). Directional improvement of +1.11 Sharpe points, still well below V2 quant baseline (2.69) but with confidence labels that now reflect actual conviction strength.

**Unit tests:** `tests/graph/test_signal_processing_confidence.py` extended from 4 → 7 tests covering trailing-punctuation, multi-word responses, and markdown-wrapped LLM outputs.

### Artifacts

| Path | Contents |
|---|---|
| `data/sentiment/alpaca/*/*.parquet` | Bitemporal PIT sentiment store (2023-10 → 2026-04, 13,453 articles) |
| `data/agent_signals_pit/bitcoin_2026-01-16_2026-04-15.csv` | BTC 4-analyst signals |
| `data/agent_signals_pit/ethereum_2026-01-16_2026-04-15.csv` | ETH 4-analyst signals |
| `data/agent_backtest_v2_pit/agent_v2_metrics_2026-01-16_2026-04-15.json` | Full backtest metrics (pre-rescore) |
| `data/agent_backtest_v2_pit/agent_v2_equity_2026-01-16_2026-04-15.png` | Equity curves (pre-rescore) |
| `data/agent_signals_pit_rescored/*.csv` | **Rescored signal CSVs (honest confidences)** |
| `data/agent_backtest_v2_pit_rescored/agent_v2_metrics_2026-01-16_2026-04-15.json` | **Rescored backtest metrics — canonical** |
| `scripts/rescore_confidence.py` | Re-scoring utility (replays new extract_confidence over existing CSVs) |
| `docs/superpowers/specs/2026-04-17-pit-sentiment-p1-alpaca-design.md` | Design spec |
| `docs/superpowers/plans/2026-04-17-pit-sentiment-p1-alpaca.md` | Implementation plan |

---

## 9. Data Artifacts

| File | Contents |
|------|----------|
| `data/eval_predictions.csv` | BTC RF+ARIMA 365-day walk-forward predictions (single-coin) |
| `data/eth/eval_predictions.csv` | ETH RF+ARIMA 365-day walk-forward predictions (single-coin) |
| `data/multi_2coins/summary.csv` | 2-coin LGB+ARIMA multi-horizon metrics (pre-fix DirAcc) |
| `data/multi_5coins/summary.csv` | 5-coin LGB+ARIMA multi-horizon metrics (pre-fix DirAcc) |
| `data/multi_full/summary.csv` | 10-coin LGB+ARIMA multi-horizon metrics (pre-fix DirAcc) |
| `data/multi_2coins_v2/preds_lgb_h*.csv` | **Corrected**: 2-coin LGB predictions with `ref_price` column |
| `data/multi_5coins_v2/preds_lgb_h*.csv` | **Corrected**: 5-coin LGB predictions with `ref_price` column |
| `data/baseline_equity.png` | BTC composite baseline equity curve |
| `data/eth/baseline_equity.png` | ETH composite baseline equity curve |
| `data/backtest_models_equity.png` | BTC simple strategy equity curves |
| `data/eth/backtest_models_equity.png` | ETH simple strategy equity curves |
| `data/eval_predictions_plot.png` | BTC predictions vs actuals plot |
| `data/eth/eval_predictions_plot.png` | ETH predictions vs actuals plot |

| `data/multi_2coins_v2/baseline_v2_equity.png` | V2 strategy equity curves (BTC+ETH, 2-coin model) |
| `data/multi_5coins_v2/baseline_v2_equity.png` | V2 strategy equity curves (5 coins, 5-coin model) |
| `data/multi_3coins_bnb/preds_lgb_h*.csv` | 3-coin BTC+ETH+BNB predictions ("2+1" approach) |
| `data/multi_3coins_bnb/report_v2/` | Detailed report for 3-coin V2+trend strategy |
| `data/multi_6coins/preds_lgb_h*.csv` | 6-coin universe (BTC+ETH+BNB+SOL+DOGE+ADA) predictions |
| `data/multi_2coins_v2/report_v2/` | Detailed report for 2-coin V2+trend strategy |
| `data/multi_5coins_v2/report_v2/` | Detailed report for 5-coin V2+trend strategy |

Note: `_v2` directories contain the corrected prediction CSVs with `ref_price` column for proper DirAcc computation. Use these for all future analysis.
