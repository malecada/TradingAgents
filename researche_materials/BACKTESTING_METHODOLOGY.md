# Backtesting Methodology: Hardening the Crypto Trading System Evaluation

**Status:** 2026-05-07. Companion to `IMPLEMENTATION_PLAN.md`, `QUANT_SYSTEM_RESEARCH.md`, and `LLM_LIMITATIONS_AND_RESEARCH_GAPS.md`.

**Problem statement:** The system's headline results (V2 quant Sharpe 3.31, mixed hybrid Sharpe 2.94, pure LLM Sharpe 1.46) are all evaluated on a single 88-bar window (2026-01-16 → 2026-04-15), with hybrid sizing parameters tuned on the same window. Multiple strategy variants (P1-P5) were tested sequentially, creating unreported selection bias. No statistical inference is performed — all claims are descriptive point estimates. This document specifies the methodology needed to convert these results from "interesting empirical observations" to "statistically defensible findings."

---

## 1. The core problems with the current evaluation

### 1.1 Single-window bias

All LLM-phase results are conditioned on one 88-bar bear-to-sideways regime. This means:

- No evidence of regime robustness (the most important external-validity gap per §3.1 of `LLM_LIMITATIONS_AND_RESEARCH_GAPS.md`)
- The Sharpe ratio is a single draw from an unknown distribution — we cannot distinguish signal from luck
- Any parameter tuned on this window (hybrid sizing `aw`, `cap`, `dw`) is in-sample by definition

### 1.2 Unreported multiple testing

Across P1-P5 plus parameter sweeps, the system has undergone at minimum ~15-20 distinct strategy configurations. The best result was selected and reported. Without adjusting for the number of trials, the reported Sharpe is inflated by the expected maximum of N correlated draws from the Sharpe ratio distribution.

### 1.3 No confidence intervals

A Sharpe ratio of 3.31 over 88 bars has wide sampling uncertainty. Without confidence intervals, we cannot determine whether the difference between V2 quant (3.31) and mixed hybrid (2.94) is statistically significant, or whether both are distinguishable from zero after correcting for non-normality and autocorrelation.

### 1.4 Lookahead risks in LLM evaluation

GPT-5.4-mini's training cutoff (August 2025) is five months before the backtest window start. While PIT data infrastructure is solid, the model's *priors* about crypto news → price relationships are from the pre-cutoff training distribution. No placebo test with a pre-cutoff model has been performed.

---

## 2. Combinatorial Purged Cross-Validation (CPCV)

### 2.1 Why CPCV, not walk-forward

Standard walk-forward validation evaluates the model on a single chronological sequence of test sets. This produces a single performance trajectory — a high-variance estimator that is path-dependent.

CPCV (López de Prado 2018, *Advances in Financial Machine Learning*, Ch. 12) constructs multiple train/test splits combinatorially, producing a **distribution** of out-of-sample performance metrics. Arian, Norouzi & Seco (2024, *Knowledge-Based Systems*) empirically demonstrate CPCV's marked superiority:

- Lower Probability of Backtest Overfitting (PBO)
- Superior Deflated Sharpe Ratio (DSR) test statistic
- Outperforms K-Fold, Purged K-Fold, and Walk-Forward across synthetic controlled environments

### 2.2 Implementation specification

**Data:** Full available price + feature history (ideally 2017-01 to 2026-04, ~3,400 daily bars for BTC/ETH).

**Group structure:**
- Divide the full history into N = 10 sequential groups (~340 bars each)
- Select k = 2 groups as the test set per split
- This yields C(10,2) = 45 unique train/test combinations
- Each combination produces a complete backtest path on 2 groups (~680 bars of test data)

**Purging:**
- For each train/test split, remove from the training set any observation whose label window (h=7 or h=14 bars forward) overlaps with the start of the test set
- This prevents information leakage from forward-looking labels

**Embargo:**
- After purging, additionally remove `embargo_bars` = max(h=7, h=14) = 14 bars from the end of the training set immediately before the test set
- This prevents autocorrelation in features from leaking test-period information into the last training observations

**Per-split procedure:**
1. Train LightGBM (and optionally XGBoost, CatBoost) on the training set
2. Generate signals on the test set
3. Simulate the full trading strategy (signal → position sizing → P&L) on the test set
4. Record: Sharpe ratio, cumulative return, maximum drawdown, hit rate, average win/loss ratio

**Output:**
- 45 independent Sharpe ratio estimates
- Distribution statistics: mean, median, std, 5th/95th percentiles
- The key question: what fraction of CPCV paths produce Sharpe > 0? Sharpe > 1? Sharpe > 2?
- PBO = fraction of paths where the in-sample-optimal strategy underperforms out-of-sample

### 2.3 For the LLM stack specifically

CPCV cannot be directly applied to the LLM system (you cannot retrain GPT-5.4-mini per split). Instead:

- Generate LLM signals once across the full available window
- Apply CPCV to the **downstream combination** of LLM signals + quant signals + hybrid sizing
- This tests whether the signal-combination and sizing layer is robust, even though the LLM signals are fixed
- The quant LGB models are retrained per split

This is a legitimate partial CPCV — it tests everything except the LLM signal generation, which is documented as a fixed component.

---

## 3. Deflated Sharpe Ratio (DSR)

### 3.1 Why it is necessary

When you test N strategy variants and report the best, the expected maximum Sharpe ratio under the null hypothesis (no skill) is:

```
E[max(SR)] ≈ √(2 · ln(N)) · σ_SR
```

For N = 20 variants (conservative estimate for P1-P5 + param sweeps), E[max(SR)] ≈ 2.55 · σ_SR. If σ_SR ≈ 0.5 over 88 bars, the expected maximum is ~1.28 — meaning a reported Sharpe of 1.46 (pure LLM hybrid) could easily be a selection artifact.

### 3.2 Formula

The DSR (Bailey & López de Prado 2014, *J. Portfolio Management* 40(5):94-107) is:

```
DSR = Φ((SR* - SR₀) / σ_{SR₀})
```

Where:
- `SR*` is the observed (best) Sharpe ratio
- `SR₀ = √(V[SR]) · ((1 - γ) · z⁻¹(1 - 1/N) + γ · z⁻¹(1 - 1/N · e⁻¹))` is the expected maximum SR under the null, with γ ≈ 0.5772 (Euler-Mascheroni constant)
- `V[SR]` is the variance of Sharpe ratios across trials
- `σ_{SR₀}` is the standard error of SR* adjusted for skewness (γ₃) and kurtosis (γ₄):

```
σ_{SR₀} = √((1 - γ₃ · SR* + (γ₄ - 1)/4 · SR*²) / (T - 1))
```

Where T is the number of return observations.

### 3.3 What to compute and report

For each strategy class (V2 quant, mixed hybrid, pure LLM hybrid, pure LLM), compute:

1. **Probabilistic Sharpe Ratio (PSR):** probability that the true SR exceeds a benchmark (e.g., SR₀ = 0 or SR₀ = 1), adjusted for non-normality
2. **Deflated Sharpe Ratio (DSR):** PSR further adjusted for the number of trials conducted
3. **Minimum Backtest Length (MinBTL):** the minimum number of observations needed for the observed SR to be statistically significant at 95% confidence, given skewness and kurtosis

For your 88-bar window with crypto-typical skewness (~-0.5) and excess kurtosis (~3-5), the MinBTL for a Sharpe of 3.31 (annualized) is likely ~60-80 bars — meaning the V2 quant result may barely clear significance, while the 1.46 LLM hybrid almost certainly does not.

### 3.4 Practical implementation

```python
import numpy as np
from scipy.stats import norm

def deflated_sharpe_ratio(sr_observed, sr_variance, n_trials, T, skew, excess_kurt):
    """
    sr_observed: annualized Sharpe ratio of the selected strategy
    sr_variance: variance of SRs across all N trials
    n_trials: number of strategy variants tested
    T: number of return observations
    skew: skewness of returns
    excess_kurt: excess kurtosis of returns
    """
    # Expected maximum SR under the null (Euler-Mascheroni approx)
    gamma_em = 0.5772156649
    sr_0 = np.sqrt(sr_variance) * (
        (1 - gamma_em) * norm.ppf(1 - 1/n_trials)
        + gamma_em * norm.ppf(1 - 1/(n_trials * np.e))
    )

    # Standard error of SR adjusted for non-normality
    se_sr = np.sqrt(
        (1 - skew * sr_observed + (excess_kurt - 1) / 4 * sr_observed**2)
        / (T - 1)
    )

    # DSR
    dsr = norm.cdf((sr_observed - sr_0) / se_sr)
    return dsr, sr_0
```

**Reporting:** Present a table like:

| Strategy | SR (ann.) | N trials | T bars | PSR(SR>0) | DSR | MinBTL |
|---|---|---|---|---|---|---|
| V2 quant | 3.31 | 5 | 88 | ? | ? | ? |
| Mixed hybrid | 2.94 | 15 | 88 | ? | ? | ? |
| Pure LLM hybrid | 1.46 | 20 | 88 | ? | ? | ? |
| Pure LLM | 0.21 | 20 | 88 | ? | ? | ? |

---

## 4. Block bootstrap confidence intervals for Sharpe ratios

### 4.1 Why block bootstrap, not standard bootstrap

Crypto daily returns exhibit:
- Autocorrelation in squared returns (volatility clustering)
- Fat tails (excess kurtosis 3-10)
- Occasional regime-dependent serial correlation in returns themselves

Standard i.i.d. bootstrap destroys the temporal dependence structure, producing anti-conservative confidence intervals. Ledoit & Wolf (2008, *J. Empirical Finance* 15(5):850-859) demonstrate that the circular block bootstrap with studentized intervals provides correct coverage even under heavy tails and serial dependence.

### 4.2 Implementation specification

**For each strategy's daily return series:**

1. Choose block size `b`. Rule of thumb: `b = max(5, int(T^(1/3)))`. For T=88: b ≈ 5. For longer series, b ≈ 10-20. Optionally, use the Politis & White (2004) automatic block length selection.

2. Generate B = 10,000 circular block bootstrap resamples:
   - Draw `ceil(T/b)` blocks of length `b` with replacement from the return series (wrapping around circularly)
   - Concatenate and trim to length T
   - Compute SR_boot from the resample

3. For **each bootstrap resample**, also compute the bootstrap SE of the Sharpe ratio (studentized bootstrap requires a nested bootstrap or analytical SE estimate):
   ```
   se_boot = sqrt((1 - skew_boot * SR_boot + (kurt_boot - 1)/4 * SR_boot²) / (T-1))
   ```

4. Compute the studentized pivot: `t_boot = (SR_boot - SR_observed) / se_boot`

5. Build the 95% confidence interval:
   ```
   CI = [SR_observed - q_97.5 * se_original, SR_observed - q_2.5 * se_original]
   ```
   where `q_2.5` and `q_97.5` are the 2.5th and 97.5th percentiles of the t_boot distribution.

### 4.3 Comparing two Sharpe ratios

To test whether V2 quant (SR=3.31) is significantly different from mixed hybrid (SR=2.94):

- Compute the paired daily return difference series: `d_t = r_quant_t - r_mixed_t`
- Apply the block bootstrap to the **difference series**
- The Sharpe ratio of the difference series tests whether the strategies are distinguishable
- Alternatively, bootstrap the SR difference directly: in each resample, compute `SR_quant_boot - SR_mixed_boot` and check whether the 95% CI contains zero

### 4.4 What to report

For each strategy:

| Strategy | SR (ann.) | 95% CI (bootstrap) | p-value (SR > 0) | p-value (SR > 1) |
|---|---|---|---|---|
| V2 quant | 3.31 | [?, ?] | ? | ? |
| Mixed hybrid | 2.94 | [?, ?] | ? | ? |
| Pure LLM hybrid | 1.46 | [?, ?] | ? | ? |

For strategy comparisons:

| Comparison | SR difference | 95% CI | Significant at 5%? |
|---|---|---|---|
| V2 quant vs Mixed hybrid | 0.37 | [?, ?] | ? |
| Mixed hybrid vs Pure LLM hybrid | 1.48 | [?, ?] | ? |
| V2 quant vs Pure LLM | 3.10 | [?, ?] | ? |

---

## 5. Walk-forward validation with embargo

### 5.1 Why still needed despite CPCV

CPCV tests the model's statistical robustness across many splits but uses future data for training (test groups can precede training groups). Walk-forward validation is the only protocol that is strictly causal — training always precedes testing. Both should be reported.

### 5.2 Implementation specification

**Expanding-window walk-forward:**

```
Window structure (example for daily data 2020-01 to 2026-04):

Step 1: Train 2020-01 → 2023-12  |  Embargo 14d  |  Test 2024-01 → 2024-03
Step 2: Train 2020-01 → 2024-03  |  Embargo 14d  |  Test 2024-04 → 2024-06
Step 3: Train 2020-01 → 2024-06  |  Embargo 14d  |  Test 2024-07 → 2024-09
...continuing with 3-month (63-bar) test blocks...
Step N: Train 2020-01 → 2025-12  |  Embargo 14d  |  Test 2026-01 → 2026-04
```

**Parameters:**
- Minimum training window: 756 bars (3 years) — enough for LGB to fit without overfitting
- Test window: 63 bars (one quarter) — long enough for Sharpe estimation to be meaningful
- Embargo: 14 bars (your longest prediction horizon, h=14)
- Expanding, not sliding — more training data is always beneficial for tree models
- Step size: 63 bars (non-overlapping test windows for clean aggregation)

**Per-step procedure:**
1. Retrain LGB on the training window (with hyperparameters fixed or optimized via inner CPCV on the training set only)
2. Generate signals on the test window
3. Simulate full strategy on the test window
4. Record per-step metrics

**Output:**
- Time series of quarterly Sharpe ratios, returns, and drawdowns
- Aggregate OOS Sharpe = annualized SR on concatenated test-window returns
- Regime breakdown: which HMM regime was each test window in? Do metrics differ by regime?

### 5.3 Hyperparameter handling

**Critical decision:** Are hyperparameters (number of trees, learning rate, max depth, feature count) fixed across walk-forward steps, or re-optimized per step?

**Recommended approach:** Fix hyperparameters using a single inner optimization on the first training window only. This avoids the combinatorial explosion of re-optimizing at each step and prevents the walk-forward from becoming a stealth multiple-testing exercise. If you want to demonstrate robustness to hyperparameters, run the walk-forward twice with two different fixed hyperparameter sets and show that results are qualitatively similar.

For the hybrid sizing parameters (`aw`, `cap`, `dw`): these should be re-estimated at each step using only the training window. This directly addresses the in-sample-tuned objection from §3.5 of `LLM_LIMITATIONS_AND_RESEARCH_GAPS.md`.

---

## 6. Regime-conditional evaluation

### 6.1 Why regime breakdown matters

A Sharpe of 3.31 across 88 bars in a single regime tells us nothing about performance in other regimes. Since the hybrid architecture's core thesis is regime-conditional LLM weighting, the backtesting must evaluate each regime separately.

### 6.2 Implementation specification

**Using the HMM-3 regime detector:**

After fitting the HMM (§4 of `QUANT_SYSTEM_RESEARCH.md`), label each bar with its most-probable regime state. Then compute all metrics conditional on regime:

| Regime | # Bars | Strategy SR | Strategy Return | MaxDD | Hit Rate |
|---|---|---|---|---|---|
| Bull | ? | ? | ? | ? | ? |
| Sideways | ? | ? | ? | ? | ? |
| Bear | ? | ? | ? | ? | ? |

Do this for every strategy variant (V2 quant, mixed hybrid, pure LLM, etc.). The key hypothesis to test: **Does the LLM modulator add value in sideways regimes (where the literature predicts it should) and not destroy value in trending regimes?**

### 6.3 Regime-conditional bootstrap

Standard block bootstrap may mix bars from different regimes, producing confidence intervals that don't respect regime structure. Use **regime-conditional bootstrap:**

1. Separate the return series into regime-specific subsequences
2. Block-bootstrap within each regime
3. Reconstruct the full series by concatenating regime-specific bootstraps in the original regime order
4. Compute metrics on the reconstructed series

This produces confidence intervals that respect the regime structure of the data.

---

## 7. Synthetic data augmentation

### 7.1 Purpose

When the real evaluation window is short (88 bars), generate synthetic extensions to estimate the distribution of performance metrics under the detected regime structure.

### 7.2 Implementation specification

1. Fit the HMM-3 to the full price history (2017-2025)
2. Extract the emission distributions (mean, variance, skewness, kurtosis) per regime state and the transition matrix
3. Simulate K = 10,000 synthetic return paths of length 88 bars:
   - Start from the regime state distribution observed at 2026-01-16
   - At each step, draw the regime from the transition matrix
   - Draw the return from the regime's emission distribution (use a skewed-t or mixture of normals, not just Gaussian, to capture fat tails)
4. Run the **fixed** strategy (signals frozen, sizing parameters frozen) on each synthetic path
5. Record Sharpe ratio, return, MaxDD for each path
6. Report the distribution: median, 5th/25th/75th/95th percentiles

### 7.3 Interpretation

If the strategy's observed Sharpe (3.31) falls above the 95th percentile of synthetic-path Sharpe ratios, the strategy is likely overfit to the specific path. If it falls near the median, the strategy's performance is consistent with the regime structure — a much stronger claim.

**Caution:** Synthetic data cannot reveal alpha that depends on specific event sequences (e.g., a particular ETH upgrade narrative). It only tests whether the strategy's performance is consistent with the statistical regime structure. For the quant engine this is appropriate; for the LLM modulator it is less informative.

---

## 8. Placebo tests

### 8.1 Training-cutoff placebo (for LLM stack)

**Purpose:** Determine whether LLM alpha comes from genuine reasoning or memorized pre-cutoff patterns.

**Protocol:**
1. Re-run the P4 prompt + hybrid sizing pipeline using `gpt-4o-mini` (October 2023 cutoff)
2. Same PIT-correct data feeds, same window (2026-01-16 → 2026-04-15)
3. Compare ETH leg Sharpe and signal distribution against GPT-5.4-mini result
4. If ETH alpha persists with the older model → the signal reflects genuine analytical capability, not memorization
5. If ETH alpha collapses → the P4 result is at least partly attributable to GPT-5.4-mini having internalized post-August-2025 market patterns

**Cost:** Trivial — `gpt-4o-mini` pricing is minimal and P1-P3 wiring already exists.

### 8.2 Shuffled-signal placebo (for quant engine)

**Purpose:** Confirm that the LGB signal ordering matters — that performance isn't an artifact of position sizing or market beta.

**Protocol:**
1. Take the LGB signal series (88 bars of direction + magnitude predictions)
2. Randomly permute the signal series (destroying temporal structure)
3. Run the full strategy on the permuted signals
4. Repeat 1,000 times
5. The observed Sharpe should be in the far right tail (>95th percentile) of the shuffled distribution

If the observed Sharpe is NOT in the tail, the "alpha" is coming from the sizing/risk management layer rather than from the signal — important to know.

### 8.3 Random-entry placebo (for position sizing)

**Purpose:** Determine how much of the Sharpe comes from position sizing vs. signal quality.

**Protocol:**
1. Replace LGB signals with random direction calls (50/50 long/short, matching the empirical frequency)
2. Keep the position sizing exactly as-is (vol targeting, regime adjustment, etc.)
3. Run 1,000 simulations
4. Compare the distribution of random-entry Sharpe to the observed Sharpe

If the random-entry Sharpe is surprisingly high (e.g., >1.0), the sizing layer is contributing significantly to performance independent of signal quality — not necessarily bad, but must be disclosed.

---

## 9. Transaction cost modeling

### 9.1 Why it matters

A Sharpe of 3.31 before costs can be a Sharpe of 1.5 after costs if turnover is high. Crypto trading costs include:

- **Maker/taker fees:** Binance 0.02%/0.04% (VIP0 with BNB); lower at higher tiers
- **Slippage:** Size-dependent; for BTC/ETH daily on Binance spot, typically 0.01-0.05% per side for position sizes under $100K
- **Funding costs:** If using perpetual futures, the 8h funding rate creates a directional carry cost/benefit
- **Spread crossing:** Bid-ask spread on BTC perpetual ≈ 0.01%; ETH ≈ 0.02%

### 9.2 Implementation specification

Apply costs conservatively:

```python
cost_per_trade = maker_fee + slippage_estimate  # e.g., 0.02% + 0.03% = 0.05% per side
turnover_cost = abs(position_change) * cost_per_trade * 2  # round-trip for full position change
daily_cost = turnover_cost  # per rebalancing day
net_return = gross_return - daily_cost
```

### 9.3 Sensitivity analysis

Report Sharpe at multiple cost assumptions:

| Cost per side (bps) | V2 quant Sharpe | Mixed hybrid Sharpe |
|---|---|---|
| 0 (gross) | 3.31 | 2.94 |
| 3 | ? | ? |
| 5 | ? | ? |
| 10 | ? | ? |
| 20 (conservative) | ? | ? |

Also report the **break-even cost** — the per-side cost at which Sharpe drops to 0. This gives the thesis reader a clear sense of how much execution quality matters.

### 9.4 Turnover analysis

Report daily portfolio turnover as a percentage of NAV. A daily turnover of >100% signals a high-frequency strategy where costs dominate. For a daily h=7/h=14 signal, turnover should be moderate (20-50% daily).

---

## 10. Ablation studies

### 10.1 Purpose

Ablation studies decompose the total Sharpe into contributions from each component. They answer: "If I remove X, how much does performance degrade?"

### 10.2 Required ablations

| Ablation | What is removed | Expected result |
|---|---|---|
| No regime filter (SMA30 off) | Strategy always active, no trend gate | Quantify SMA30 contribution |
| SMA30 → HMM-3 replacement | Test whether HMM improves on SMA30 | HMM should improve if regime detection matters |
| Single-horizon (h=7 only) | Drop h=14 from consensus | Quantify multi-horizon consensus value |
| Single-horizon (h=14 only) | Drop h=7 from consensus | Same |
| No hybrid sizing | LLM direction only, equal-weight positions | Quantify LGB-magnitude sizing contribution |
| Asset-name anonymization ON vs OFF | For LLM stack: replace coin names with Asset X/Y | Quantify debiasing effect on BTC |
| No LLM modulator (quant only) | Remove Layer 2 entirely; pure quant execution | Quantify LLM modulator value |
| No quant base (LLM only) | Remove Layer 1; LLM generates standalone signal | Quantify quant engine's contribution |
| Feature group ablation | Remove one feature group at a time (technicals, microstructure, derivatives, macro, on-chain) | Rank feature group importance |

### 10.3 Reporting format

Present ablation results with bootstrap CIs so readers can judge whether differences are significant:

| Configuration | Sharpe (95% CI) | Return | MaxDD | vs Full System Δ |
|---|---|---|---|---|
| Full system | 3.31 [2.1, 4.5] | +36.59% | 6.16% | — |
| No SMA30 | ? [?, ?] | ? | ? | ? |
| HMM-3 replacing SMA30 | ? [?, ?] | ? | ? | ? |
| h=7 only | ? [?, ?] | ? | ? | ? |
| ... | ... | ... | ... | ... |

---

## 11. Implementation checklist and timeline

Ordered by priority for thesis defense readiness.

### Must-have (before defense, ~5 days total)

| # | Task | Time | Depends on |
|---|---|---|---|
| BT1 | Block bootstrap CIs for all strategy Sharpe ratios (Ledoit-Wolf studentized) | 0.5 day | — |
| BT2 | Block bootstrap CI for strategy *comparisons* (quant vs mixed vs LLM) | 0.5 day | BT1 |
| BT3 | Deflated Sharpe Ratio table (all strategies, N≈20 trials) | 0.5 day | — |
| BT4 | Shuffled-signal placebo test (1,000 permutations) | 0.5 day | — |
| BT5 | Transaction cost sensitivity table (5 cost levels) | 0.5 day | — |
| BT6 | Training-cutoff placebo (gpt-4o-mini re-run) | 0.5 day | — |
| BT7 | Core ablation table (at minimum: no SMA30, single-horizon, no hybrid sizing) | 1 day | — |

### Should-have (strengthens the thesis, ~5 days total)

| # | Task | Time | Depends on |
|---|---|---|---|
| BT8 | Walk-forward validation (expanding window, quarterly test blocks) | 1.5 days | — |
| BT9 | CPCV framework (N=10, k=2, 45 splits) | 1.5 days | — |
| BT10 | Regime-conditional evaluation (HMM-3 per-regime metrics) | 1 day | HMM implementation |
| BT11 | Random-entry placebo (1,000 sims) | 0.5 day | — |
| BT12 | Regime-conditional bootstrap CIs | 0.5 day | BT10 |

### Nice-to-have (for strongest possible defense)

| # | Task | Time | Depends on |
|---|---|---|---|
| BT13 | Synthetic data augmentation (10,000 HMM-simulated paths) | 1 day | HMM implementation |
| BT14 | Full feature-group ablation (5 groups × full pipeline) | 1.5 days | — |
| BT15 | Bull-regime OOS window (2025-Q4 backtest) | 1 day | data backfill |
| BT16 | Cross-model validation (Claude Haiku 4.5) | 1-2 days | Anthropic API key |

---

## 12. Common pitfalls to avoid

### 12.1 Lookahead bias in features

Every feature computed from the full dataset before train/test splitting introduces lookahead. This includes:
- Normalization (Z-scores, min-max) computed on the full series — always compute on the training set only and apply the training-set parameters to the test set
- Rolling features (e.g., 21d vol) at the start of the test window that use training-period data — this is generally acceptable (it's causal), but document it explicitly
- HMM regime labels computed on the full series — use online posterior updating only (forward algorithm), never the backward algorithm (which uses future data)

### 12.2 Survivorship bias in the coin universe

BTC and ETH survive the full sample period. Many altcoins don't. If you expand to a larger universe, you must include delisted/dead coins in the backtest to avoid survivorship bias.

### 12.3 Point-in-time violations in external data

Per Look-Ahead-Bench (Benhenda 2026, arXiv 2601.13770), LLMs memorize pre-cutoff financial data perfectly. Ensure all external data feeds (Alpaca, GDELT, CoinMetrics, CryptoQuant) are queried with `as_of_date < decision_date` filters. Document the PIT discipline for each data source.

### 12.4 Overfitting the evaluation itself

Running BT1-BT16 and then changing the strategy based on the results creates a new layer of overfitting. The honest protocol:

1. **Pre-register** the strategy configuration before running the backtesting battery
2. Run all tests on the pre-registered configuration
3. If you then iterate based on results, clearly delineate the pre-registered result from the post-hoc improvements
4. Report both

---

## 13. Key references

| Reference | What it provides |
|---|---|
| López de Prado (2018), *Advances in Financial Machine Learning*, Ch. 7, 12 | Purged K-Fold CV, CPCV, backtesting pitfalls |
| Bailey & López de Prado (2014), *J. Portfolio Mgmt* 40(5):94-107, SSRN 2460551 | Deflated Sharpe Ratio derivation and formula |
| Bailey, Borwein, López de Prado & Zhu (2014), *Notices AMS* 61(5):458-471 | Probability of Backtest Overfitting (PBO) |
| Ledoit & Wolf (2008), *J. Empirical Finance* 15(5):850-859 | Robust Sharpe ratio testing via studentized block bootstrap |
| Lo (2002), *Financial Analysts Journal* 58(4):36-52 | Statistics of Sharpe Ratios; autocorrelation adjustment |
| Arian, Norouzi & Seco (2024), *Knowledge-Based Systems* | CPCV empirically superior to alternatives; lower PBO |
| López de Prado & Lipton & Zoonekynd (2025), SSRN 5520741 | How to Use the Sharpe Ratio: closed-form sampling distribution |
| arXiv 2602.00080 (GT-Score, 2026) | Anti-overfitting objective; 98% generalization ratio improvement |
| Benhenda (2026), arXiv 2601.13770 (Look-Ahead-Bench) | LLMs memorize pre-cutoff financial data; PIT non-negotiable |
| Varma (2025), *J. Portfolio Management* (CDAP) | Simple drawdown rules often hurt; condition on regime |
