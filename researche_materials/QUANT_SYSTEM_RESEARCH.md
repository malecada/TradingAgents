# Improving the Quant Engine: Research Report for the Crypto Trading System

**Status:** 2026-05-06. Companion to `IMPLEMENTATION_PLAN.md` (hybrid architecture) and `LLM_LIMITATIONS_AND_RESEARCH_GAPS.md`.

**Baseline being improved:** LightGBM term-structure consensus (h=7, h=14 ensemble) + SMA30 trend filter. Sharpe 3.31, +36.59% return, 6.16% MaxDD on 88-bar bear-to-sideways window (2026-01-16 → 2026-04-15). BTC+ETH, daily frequency.

---

## Executive summary

Your V2 quant baseline is already strong — Sharpe 3.31 puts it in the top decile of published OOS crypto quant results. The literature suggests the biggest gains come not from swapping LightGBM for a fancier model, but from three orthogonal improvements: (1) adding features the current model cannot see (microstructure, cross-asset derivatives, on-chain factors that survive multiple-testing), (2) formalizing regime detection so the model adapts its behavior structurally rather than via a single SMA30 gate, and (3) hardening the backtesting methodology to ensure the 3.31 Sharpe survives scrutiny. Model architecture changes (CatBoost, TFT, stacking) offer incremental gains at best — gradient boosted trees remain the consensus winner for tabular financial data.

The report is organized into seven areas, each with findings, practical recommendations, and a difficulty/impact assessment. A consolidated implementation roadmap is at the end.

---

## 1. Model architecture: gradient boosting is still king, but the details matter

### What the literature says

Gradient boosted decision trees (GBDT) consistently match or beat deep learning on tabular financial data. The 2025 Fang et al. comprehensive crypto trading survey (Springer, Blockchain, Crypto Assets, and Financial Innovation) confirms GBDT and MLP as the two dominant model families. The 2024 ScienceDirect crypto trading mapping study (Int'l J. Information Management Data Insights) finds historical market data + technical indicators as the dominant feature class for ML models, with gradient boosting and random forests leading classification performance.

LightGBM vs XGBoost vs CatBoost: performance differences are marginal and data-dependent. LightGBM's leaf-wise growth is faster on larger datasets; CatBoost handles categorical features natively and has built-in ordered boosting that reduces target leakage — potentially useful when you have categorical regime labels as features. The practical recommendation: **ensemble all three** rather than pick one. A simple average of LGB + XGB + CatBoost predictions reduces variance with near-zero additional complexity.

### Deep learning alternatives

**Temporal Fusion Transformer (TFT):** Lee (2025, MDPI Systems 13/6/474) applies TFT with on-chain + technical features to multi-crypto trading. The attention mechanism provides interpretable feature importance. Peik et al. (arXiv 2509.10542) propose adaptive TFT with dynamic subseries segmentation for crypto, reporting improved short-term forecasting. However, TFT's advantage over GBDT is primarily at longer horizons and with rich static covariates — for daily BTC/ETH with ~50 features, the gap is marginal and the engineering cost is high.

**LSTM+XGBoost hybrids:** Gautam (arXiv 2506.22055) shows LSTM capturing temporal dependencies + XGBoost handling nonlinear cross-sectional features outperforms either alone. This maps directly to your setup: LSTM on the raw return series feeding latent states into the LGB feature vector.

**Practical recommendation:** Stay on LightGBM as the primary model. Add CatBoost and XGBoost as ensemble members (simple average or stacked with logistic regression meta-learner). Consider TFT only if you move to multi-horizon joint estimation (see §3). The marginal Sharpe gain from model switching is typically +0.1-0.2; the gain from better features is +0.3-0.8.

---

## 2. Feature engineering: what actually survives OOS in crypto

This is the highest-impact area. Your current feature set likely covers standard technicals (momentum, volatility, moving averages). The literature identifies several feature classes that add genuine incremental alpha.

### 2.1 The crypto factor zoo: what survives disciplined testing

Mercik, Zaremba & Demir (2026, "Crypto factor zoo (.Zip)", International Review of Financial Analysis 113) apply the Swade et al. (2024) iterative factor selection methodology to 36 candidate factors across 565 cryptocurrencies. **Key finding: just 2-3 factors eliminate all significant portfolio alphas.** The survivors are:

- **Turnover volatility** (volatility of volume/market-cap ratio) — the single most robust factor
- **Bid-ask spreads** (liquidity proxy) — consistently appears across weighting schemes
- **New-address-to-price ratio** — the only blockchain-native metric that survives

Liquidity-related variables dominate the selection. This implies your feature set should prioritize liquidity and microstructure over on-chain "fundamentals."

Borri, Liu, Tsyvinski & Wu (2026, "Cryptocurrency as an Investable Asset Class", Annual Review of Financial Economics 18) establish seven stylized facts. The cross-section is summarized by market, size, and momentum factors (Liu, Tsyvinski & Wu 2022, JF), but they note increasing integration with traditional markets — equity-industry factors (technology, profitability) now have nonzero loadings.

Brigida (2026, "Crypto Pricing with Hidden Factors", arXiv 2601.07664) uses the Giglio-Xiu three-pass approach and finds crypto returns load on both crypto-specific factors AND selected equity-industry factors, plus nontradable sentiment variables (Fear & Greed, Altcoin Season Index). **Implication: add macro/equity features to the LGB feature vector** — SPX momentum, VIX level, DXY change, BTC dominance.

### 2.2 Microstructure features: the highest-Sharpe academic signals

Anastasopoulos & Gradojevic (2026, J. Financial Markets) report **annualized Sharpe 3.52** on long-short portfolios sorted by ML-conditioned order flow across 11 cryptocurrencies, with 0.76%/day alpha and break-even costs of 0.48%/day. Weekly-aggregated order flow explains more return variation than daily (R² = 3.1% weekly vs 1.2% daily), because aggregation mitigates microstructure noise.

Bieganowski & Ślepaczuk (2026, "Explainable Patterns in Cryptocurrency Microstructure", arXiv 2602.00776) document **stable cross-asset patterns** in LOB features: the same engineered features (order flow imbalance, bid-ask spreads, VWAP deviations) exhibit similar SHAP importance across BTC, LTC, ETC, ENJ, ROSE. They use CatBoost with a direction-aware objective.

Easley, O'Hara et al. (2026, "Microstructure and Market Dynamics in Crypto Markets", ScienceDirect) find VPIN levels in crypto (0.45-0.47) are roughly double traditional markets (0.22-0.23), indicating much higher information-based trading. Roll measures and VPINs show strong cross-effects between BTC and ETH. **VPIN is predictive of future volatility and return direction.**

Kitvanitphasu et al. (2026, Research in Int'l Business & Finance 81) confirm VPIN significantly predicts BTC price jumps with persistent serial correlation.

**Practical recommendation:** Build VPIN and order-flow imbalance features from Binance tick data (free WebSocket). Use López de Prado volume bucketing for VPIN construction. Aggregate at daily frequency (volume-weighted) for your h=7/h=14 models. These features are orthogonal to price-based technicals and represent the single largest expected feature-engineering gain.

### 2.3 Derivatives / term-structure features

Your system already uses "term-structure consensus" — this is your strongest feature class and the literature validates it.

Schmeling, Schrimpf & Todorov (2023/2025, BIS WP 1087 "Crypto Carry") document that perpetual futures carry averages 6-8% p.a. and frequently exceeds 20%. The carry is driven by retail leverage demand. **Funding rate, basis, and their term structures are first-order features.**

The CF Benchmarks research (2025) demonstrates that Bitcoin basis is driven by momentum + sentiment, creating exploitable technical divergences between spot and futures. Cross-asset basis trades (BTC vs ETH vs SOL basis) are now feasible.

**Features to add:** funding rate (8h) as level + Z-score + slope (current vs 7d avg); CME basis annualized; perpetual vs spot premium; open interest change (momentum proxy); liquidation volume asymmetry (long/short ratio).

### 2.4 Cross-asset and macro features

Brigida (2026) shows crypto returns now load on equity factors. Practically, add:

- SPX/NDX 5d and 21d momentum
- VIX level and VIX term structure (VIX/VIX3M ratio — contango vs backwardation)
- DXY (dollar index) 5d change — strong inverse correlation with BTC since 2020
- US 2Y yield change (rate expectations proxy)
- BTC dominance (BTC.D) — when BTC.D rises, altcoins underperform
- Total crypto market cap momentum (TOTAL)
- Gold 5d momentum (safe-haven competition)

These are free (Yahoo Finance, FRED) and add a macro regime dimension the model currently lacks.

---

## 3. Multi-horizon ensemble: improving the h=7/h=14 consensus

### Current approach and its strengths

Your h=7 + h=14 LGB consensus is well-motivated: it captures the empirically demonstrated horizon where crypto signal emerges (h=1 ≈ 50% DirAcc, h=7+ shows signal). The consensus between two horizons provides implicit regime filtering — agreement means stronger signal.

### Improvements from the literature

**Add h=3 and h=21 horizons.** The TFT literature (Lee 2025) shows multi-horizon joint estimation improves calibration. h=3 captures short-term momentum exhaustion; h=21 captures monthly mean-reversion (the strongest documented cross-sectional effect in crypto after momentum). A 4-horizon consensus (h=3, h=7, h=14, h=21) with majority voting or weighted average provides richer signal.

**Horizon-specific feature selection.** Different features matter at different horizons. At h=3, microstructure features (VPIN, order flow) dominate. At h=7, momentum and funding rate dominate. At h=14-21, on-chain and macro features matter more. Run SHAP analysis per-horizon and use horizon-specific feature sets rather than a shared feature vector.

**Consensus weighting by regime.** In trending markets (Hurst > 0.55), upweight the longer-horizon models (h=14, h=21). In mean-reverting markets (Hurst < 0.45), upweight shorter-horizon models (h=3, h=7). This is a direct extension of the regime-conditional architecture from the hybrid implementation plan.

**Probability calibration.** Instead of averaging raw LGB predictions, calibrate each model's output using isotonic regression on a holdout period, then average the calibrated probabilities. This ensures the consensus output is well-calibrated, which directly improves position sizing downstream.

---

## 4. Regime detection: replacing SMA30 with a proper statistical framework

The SMA30 is doing two jobs: (1) detecting trend direction and (2) gating the strategy. The literature provides much better tools for both.

### 4.1 HMM for crypto: current state of the art

Yamaguchi (2026, Preprints.org) develops a regime-switching framework for BTC with non-homogeneous HMMs + Bayesian estimation, extending standard HMMs to capture dynamic transition probabilities. The methodology classifies BTC into distinct latent states with different return/volatility properties.

Machimbo et al. (2025, Asian J. Probability & Statistics 27/7) compare HMMs, Markov Switching Models, and Threshold Models for BTC regime detection. **HMMs outperform** the alternatives in forecasting regime shifts, particularly transitions among bullish/bearish/neutral states.

A 2025 paper (MDPI Mathematics 13/10/1577) integrates Bayesian MCMC covariate selection within HMMs, testing 16 macroeconomic + BTC-specific factors from 2016-2024. The non-homogeneous HMM (NH-HMM) with time-varying transition probabilities captures structural breaks better.

### 4.2 BOCPD for changepoint detection

Bayesian Online Change Point Detection (BOCPD) is the standard for real-time changepoint detection. The 2025 ACM symposium paper on BOCPD applied to Hong Kong stock market data identifies 6 major regime changes across 2020-2025, aligning with known events (COVID, Russia-Ukraine, 2024 election).

**BOCPD complements HMM:** HMM provides smooth regime probabilities; BOCPD provides sharp changepoint alerts. The combination (from the implementation plan) is well-supported.

### 4.3 GMM-VAR: a promising alternative

A 2025 paper (Data Science in Finance & Economics, 5(3)) proposes Gaussian Mixture Model VAR (GMM-VAR) for crypto regime detection, arguing it handles "abrupt, non-sequential, and overlapping regime shifts" better than HMM because it doesn't enforce Markovian temporal dependencies. This may be worth testing as an alternative to HMM-3.

### 4.4 Regime-switching RL

Agakishiev, Härdle, Becker et al. (2025, Digital Finance 7:107-131) apply regime-switching RL to crypto portfolio management. Three regimes defined by volatility and return quantiles. Key finding for crypto: **volatility and return have low negative correlation**, unlike equities — meaning separate regime definitions for volatility and return are needed.

### Practical recommendation

Replace SMA30 with a 3-state HMM (bull/sideways/bear) trained on (returns, realized_vol_21d, ADX_14, funding_rate_8h). Add BOCPD as a changepoint alert layer. Use Hurst exponent (rolling 63-bar) as a trending/mean-reverting filter orthogonal to HMM. Output: `{regime_label, regime_confidence, hurst, changepoint_alert}`.

**Critical implementation detail:** Train the HMM on a long history (2017-2025) and use online Bayesian updating for the posterior during the backtest. Do NOT refit the HMM at each step — this introduces severe lookahead bias. The HMM parameters (emission means/variances, transition matrix) should be fixed from training; only the posterior state probabilities update online via the forward algorithm.

---

## 5. Position sizing and risk management

### 5.1 Kelly criterion for crypto

The academic consensus is clear: **use fractional Kelly, specifically quarter-Kelly to half-Kelly for crypto.** Full Kelly maximizes geometric growth but produces gut-wrenching drawdowns in crypto's fat-tailed environment. Half-Kelly captures ~75% of optimal growth with ~50% less drawdown. Quarter-Kelly is recommended when probability estimates are uncertain (they always are in crypto).

Your current hybrid sizing (`aw=2.0, cap=2.0, dw=0.5`) is effectively a heuristic position scaler. The improvement is to replace it with a principled Kelly-based framework:

```
position_size = fraction * kelly_fraction * regime_adjustment * volatility_scalar
```

Where `kelly_fraction = (expected_return / variance)`, `fraction = 0.25-0.50`, `regime_adjustment` comes from the HMM (reduce size in uncertain regimes), and `volatility_scalar` normalizes by recent realized volatility (inverse vol targeting).

### 5.2 Volatility targeting

Instead of fixed position sizes, target a constant portfolio volatility (e.g., 15% annualized). When realized vol is low, lever up; when high, reduce. This is the single most robust risk management technique in the literature — it improves Sharpe mechanically by reducing exposure during vol spikes (which coincide with drawdowns).

Implementation: `target_vol / realized_vol_21d * base_position = actual_position`, capped at 2x leverage.

### 5.3 CVaR-based risk management

A 2026 MDPI paper (IJFS 14/3/53, "Regime- and Tail-Dependent Performance of CVaR-Based Portfolio Strategies in Cryptocurrencies") evaluates CVaR strategies on crypto 2018-2025. Key finding: **regime-dependent CVaR optimization** outperforms static CVaR, but all CVaR strategies face the risk-return tradeoff — lower tail risk comes with lower returns. The practical recommendation is to use CVaR as a constraint (max allowed CVaR per position) rather than as the optimization objective.

### 5.4 Drawdown control

Varma (2025, J. Portfolio Management, "The False Promise of Drawdown Rules") presents a surprising finding: **simple drawdown stop-loss rules frequently hurt performance** because they trigger on noise and miss recoveries. The evidence doesn't generalize across markets. Instead, Varma proposes the CDAP (Conditional Drawdown Action Protocol) framework that conditions drawdown actions on regime classification — only cut when the drawdown coincides with a confirmed regime shift, not on arbitrary percentage thresholds.

This aligns perfectly with your architecture: the HMM regime detector should gate the drawdown response. A 10% drawdown in a confirmed bear regime triggers de-leveraging; the same drawdown in a sideways regime with high HMM uncertainty does not.

---

## 6. Backtesting methodology: hardening the 3.31 Sharpe

Your 88-bar single-window evaluation is the most serious methodological weakness. The literature provides specific tools to address this.

### 6.1 Combinatorial Purged Cross-Validation (CPCV)

López de Prado's CPCV (Advances in Financial Machine Learning, 2018) is the gold standard for financial ML backtesting. Key insight: standard k-fold CV fails in finance because observations are not IID — temporal dependencies cause information leakage.

Arian, Norouzi & Seco (2024, Knowledge-Based Systems) empirically compare CV methods and find **CPCV markedly superior** in mitigating overfitting, outperforming K-Fold, Purged K-Fold, and Walk-Forward, as evidenced by lower Probability of Backtest Overfitting (PBO) and superior Deflated Sharpe Ratio (DSR).

**Implementation:** Split your full available history into N=8 groups. Use k=2 test groups per split. This gives C(8,2)=28 train/test combinations, yielding a distribution of OOS Sharpe ratios rather than a single point estimate. Apply purging (remove training samples overlapping with test labels) and embargo (gap between train and test) of h=14 bars (your longest prediction horizon).

### 6.2 Deflated Sharpe Ratio

Given that you've tested multiple strategy variants (P1-P5, various hybrid params), the reported Sharpe is inflated by selection bias. The Deflated Sharpe Ratio (DSR, Bailey & López de Prado 2014) adjusts for the number of trials:

```
DSR = (SR_observed - SR_expected_under_null) / SE(SR)
```

Where `SR_expected_under_null` accounts for the number of strategy variants tested. Report DSR alongside raw Sharpe in the thesis.

### 6.3 Walk-forward with proper embargo

For the current 88-bar window, a minimum credible walk-forward is:

- Training: expanding window starting from at least 252 bars of history
- Test: 14-bar forward blocks (one h=14 prediction cycle)
- Embargo: 14 bars between train end and test start
- Report: distribution of Sharpe ratios across all walk-forward test blocks

The GT-Score approach (arXiv 2602.00080) is worth adopting: embed an anti-overfitting structure into the objective function itself. They report 98% improvement in generalization ratio (validation/training return) versus baseline objectives.

### 6.4 Synthetic data augmentation

When the real data window is short (88 bars), generate synthetic extensions via regime-conditional bootstrapping: fit the HMM, then simulate thousands of synthetic return paths conditioned on the detected regime sequence. Test the strategy on synthetic paths to estimate the distribution of performance metrics under the regime structure observed.

---

## 7. Alternative approaches worth monitoring

### 7.1 Reinforcement learning for portfolio management

The RL literature for crypto has matured considerably. The best recent result is from a 2026 MDPI paper (Mathematics 14/5/794): an Adaptive Risk Control reward function achieves **Sharpe 2.47, 26.4% return, 16.8% MaxDD** on a bearish 2022 test period — competitive with GBDT but with built-in regime-conditional risk management.

A factor-based deep RL paper (PMC 2025/12753089) reports Dynamic-β PPO achieving 38-43% annual returns on crypto with regime sensitivity. Key insight: β-based reward designs (exposures to momentum, volatility, and volume factors) produce more interpretable RL policies than raw return rewards.

**Assessment for your system:** RL is not a replacement for LGB at the signal generation stage, but it may be worth exploring for the portfolio construction/execution layer — specifically for learning optimal position sizing and rebalancing as a function of regime state. The FDRL framework's factor-based reward design integrates naturally with your multi-factor quant engine.

### 7.2 Online / incremental learning

Non-stationarity is the binding constraint in crypto. Qian (2025, PLoS ONE) proposes IL-ETransformer with continual normalization and time-series elastic weight consolidation (TSEWC) for incremental training. The crypto-specific ASTIF framework (arXiv 2512.18661) uses adaptive meta-learning to shift between semantic and temporal channels during regime transitions.

**Practical recommendation:** Rather than full online learning (complex, fragile), use periodic retraining with an expanding window and a forgetting factor. Retrain LGB weekly with an exponential decay weighting on older samples (half-life of ~90 days). This captures distribution shift without the stability risks of full online learning.

### 7.3 Order flow / VPIN as a standalone signal

VPIN-based strategies are the highest-Sharpe academically validated approach. Building a VPIN module from Binance tick data is free and provides a signal orthogonal to your price-based LGB. Even at daily frequency (aggregated from intraday), VPIN adds value as a feature. At higher frequencies (4h, 1h), it becomes a standalone alpha source.

---

## 8. Prioritized implementation roadmap

Items are grouped by expected impact and difficulty. All are for the quant engine (Layer 1 in the hybrid architecture).

### Tier 1 — High impact, moderate effort (weeks 1-3)

| # | Change | What to build | Difficulty | Cost | Expected Δ Sharpe |
|---|---|---|---|---|---|
| Q1 | **Regime detector (HMM-3 + BOCPD + Hurst)** | 3-state HMM on (returns, vol_21d, ADX_14, funding). BOCPD changepoint alerts. Hurst exponent filter. Train on 2017-2025, online Bayesian update during backtest. Replace SMA30. | Medium | $0 | +0.3–0.5 |
| Q2 | **Microstructure features (VPIN + order flow)** | Build VPIN from Binance WebSocket tick data using López de Prado volume bucketing. Add order flow imbalance (buy-sell volume ratio). Aggregate to daily frequency. Feed as features to LGB. | Medium | $0 | +0.3–0.5 |
| Q3 | **Derivatives feature pack** | Funding rate (level, Z-score, 7d slope), perpetual basis, OI change, liquidation asymmetry. All free from Coinglass/Binance API. | Low | $0 | +0.2–0.3 |
| Q4 | **CPCV backtesting framework** | Implement Combinatorial Purged Cross-Validation with N=8 groups, k=2 test, embargo=14 bars. Report Sharpe distribution + DSR. Apply to all subsequent evaluations. | Medium | $0 | robustness |

### Tier 2 — Medium impact, lower effort (weeks 3-5)

| # | Change | Difficulty | Cost | Expected Δ Sharpe |
|---|---|---|---|---|
| Q5 | **GBDT ensemble (LGB + XGB + CatBoost)** — simple average of three models, each with optimized hyperparams via CPCV | Low | $0 | +0.1–0.2 |
| Q6 | **Multi-horizon expansion** — add h=3 and h=21 to the consensus; horizon-specific feature selection via SHAP; regime-conditional horizon weighting | Medium | $0 | +0.1–0.3 |
| Q7 | **Cross-asset / macro features** — SPX momentum, VIX/VIX3M, DXY, 2Y yield, BTC.D, gold | Low | $0 | +0.1–0.2 |
| Q8 | **Volatility-targeted position sizing** — inverse-vol targeting to 15% annual, capped at 2x; replaces fixed position sizing | Low | $0 | +0.1–0.2 (via drawdown reduction) |
| Q9 | **Kelly-based sizing framework** — fractional Kelly (0.25-0.50) with regime adjustment and vol scalar; replace heuristic `aw/cap/dw` params | Medium | $0 | +0.1–0.2 |

### Tier 3 — Important for thesis defense, not alpha-generating

| # | Change | Difficulty | Cost | Expected Δ |
|---|---|---|---|---|
| Q10 | **Deflated Sharpe Ratio** — compute DSR adjusting for all strategy variants tested (P1-P5 + param sweeps) | Low | $0 | methodological rigor |
| Q11 | **Synthetic data augmentation** — regime-conditional bootstrap to generate 10,000+ synthetic paths; test strategy on distribution | Medium | $0 | robustness estimate |
| Q12 | **Walk-forward with proper embargo** — expanding-window train, 14-bar test blocks, 14-bar embargo; report Sharpe distribution | Low | $0 | out-of-sample credibility |
| Q13 | **Feature importance analysis** — SHAP values per horizon, per regime; publish as thesis appendix | Low | $0 | interpretability |

### Tier 4 — Long-term / post-thesis

| # | Change | Difficulty | Cost | Expected Δ |
|---|---|---|---|---|
| Q14 | **VPIN as standalone intraday signal** — move to 4h or 1h frequency for VPIN-based sub-strategy | High | compute | new alpha source |
| Q15 | **RL for portfolio construction** — PPO/SAC for position sizing as function of regime + signal strength | High | compute | improved sizing |
| Q16 | **Online learning with forgetting** — weekly retraining with exponential decay weighting, half-life 90d | Medium | $0 | adaptiveness |
| Q17 | **TFT for joint multi-horizon estimation** — single model outputting h=3/7/14/21 simultaneously with attention-based feature importance | High | compute | potential improvement |

---

## 9. Key academic references

| Short cite | Source | Finding |
|---|---|---|
| Crypto factor zoo | Mercik, Zaremba & Demir 2026, Int'l Rev Fin Analysis 113 | 2-3 factors explain crypto cross-section; turnover vol, spreads, new-address-to-price survive |
| Crypto as asset class | Borri, Liu, Tsyvinski & Wu 2026, ARFE 18, arXiv 2510.14435 | 7 stylized facts; market+size+momentum span cross-section; increasing equity integration |
| Crypto hidden factors | Brigida 2026, arXiv 2601.07664 | Crypto loads on equity-industry factors + sentiment variables via Giglio-Xiu 3-pass |
| Order flow & returns | Anastasopoulos & Gradojevic 2026, J. Financial Markets | Sharpe 3.52 on ML-conditioned order flow; weekly aggregation outperforms daily |
| LOB microstructure | Bieganowski & Ślepaczuk 2026, arXiv 2602.00776 | Universal cross-asset LOB patterns in crypto; CatBoost + SHAP |
| Crypto microstructure | Easley, O'Hara et al. 2026, ScienceDirect | VPIN 0.45-0.47 in crypto (2x traditional); Roll + VPIN predictive |
| VPIN & BTC jumps | Kitvanitphasu et al. 2026, Research Int'l Bus & Fin 81 | VPIN predicts price jumps; persistent serial correlation |
| Crypto carry | Schmeling, Schrimpf & Todorov 2023/2025, BIS WP 1087 | 6-8% avg carry; retail leverage demand driven |
| BTC regime HMM | Yamaguchi 2026, Preprints.org | NH-HMM with Bayesian estimation for BTC regimes |
| HMM regime comparison | Machimbo et al. 2025, Asian J. Prob & Stats 27/7 | HMMs outperform MSMs and Threshold Models for BTC |
| BTC regime Bayesian | MDPI Mathematics 13/10/1577, 2025 | Bayesian MCMC covariate selection within HMM; 16 factors tested |
| GMM-VAR regimes | DSFE 5(3), 2025 | GMM-VAR handles non-sequential regime shifts better than HMM |
| Regime-switching RL | Agakishiev et al. 2025, Digital Finance 7 | Vol and return weakly correlated in crypto — separate regime definitions needed |
| CPCV superiority | Arian, Norouzi & Seco 2024, Knowledge-Based Systems | CPCV markedly superior; lower PBO and higher DSR |
| GT-Score | arXiv 2602.00080, 2026 | Anti-overfitting objective improves generalization ratio by 98% |
| Drawdown rules fail | Varma 2025, J. Portfolio Management | Simple drawdown stops frequently hurt; CDAP framework conditions on regime |
| RL reward functions | MDPI Mathematics 14/5/794, 2026 | Adaptive Risk Control: Sharpe 2.47 in bearish 2022; regime-conditional |