# Quant V3 Design — Tier-1 + Selected Tier-2 Improvements

**Status:** Draft, 2026-05-08. Author: brainstorming session w/ Claude Code.

**Companion docs:**
- `TradingAgents/researche_materials/QUANT_SYSTEM_RESEARCH.md` — research report driving these changes.
- `docs/superpowers/specs/2026-04-29-live-testnet-deployment-design.md` — production deployment surface that V3 must remain compatible with.
- Existing `feature/hybrid-modulator` branch — Layer 1 / Layer 2 contracts that V3 must continue to satisfy.

**Goal:** Lift the quant baseline from V2 (Sharpe 3.31, +36.59%, 6.16% MaxDD on the 88-bar 2026-01-16 → 2026-04-15 window) to a target Sharpe ≈ 3.5–4.5 by adding orthogonal feature classes (microstructure, derivatives), upgrading the regime detector, formalizing the multi-horizon ensemble, and hardening the backtesting methodology. V3 must (a) ship as a standalone strategy comparable to V2, and (b) drop in as the Layer 1 quant signal of the hybrid modulator system.

---

## 1. Scope

**In scope (Tier 1 + selected Tier 2 from research roadmap):**

| ID | Change | Module |
|---|---|---|
| Q1 | HMM-3 + BOCPD + Hurst regime detector (NH-HMM extension) | `regime/` |
| Q2 | VPIN + order-flow imbalance microstructure features | `features/microstructure.py` |
| Q3 | Derivatives feature pack (funding, basis, OI, liquidation asymmetry) | `features/derivatives.py` |
| Q4 | CPCV backtesting + Deflated Sharpe Ratio | `backtest/cpcv.py`, `backtest/dsr.py` |
| Q5 | LGB + XGB + CatBoost ensemble | `models/ensemble.py` |
| Q6 | Multi-horizon expansion (h=3, 7, 14, 21) with regime-conditional weighting | `models/multi_horizon.py` |
| Q8 | Volatility-targeted position sizing (15% annual, capped 2x) | `sizing/vol_target.py` |

**Deferred:**

- Q7 macro/cross-asset features (SPX, VIX, DXY, 2Y, BTC.D) — additional dependency, deferred to post-thesis.
- Q9 Kelly-rework — vol-target sizing subsumes for current scope.
- Tier 3 thesis-rigor extras: DSR ✓ kept (Q4 bundles it with CPCV), walk-forward ✓ kept as sanity-check track in §6, synthetic-data augmentation deferred, full SHAP appendix deferred.
- Tier 4 (RL portfolio, online learning, TFT, intraday VPIN) — long-term / post-thesis.

**Branch strategy:** All work lands on `feature/hybrid-modulator`. V3 modules are additive; V2 path remains reachable via `--quant-version v2` flag.

---

## 2. Architecture

```
tradingagents/strategies/v3/
├── __init__.py
├── config.py                 # V3Config dataclass
├── contracts.py              # Pydantic: V3Signal, RegimeState, FeatureBundle
├── features/
│   ├── __init__.py
│   ├── microstructure.py     # VPIN + OFI from Binance aggTrades
│   └── derivatives.py        # funding rate (level, Z, slope), basis, OI Δ, liq asymmetry
├── regime/
│   ├── __init__.py
│   ├── hmm_v2.py             # NH-HMM extension w/ Bayesian online posterior update
│   ├── ensemble.py           # combines HMM + BOCPD + Hurst → RegimeState
│   └── train.py              # extended training script (incl. NH-HMM transition covariates)
├── models/
│   ├── __init__.py
│   ├── ensemble.py           # LGB + XGB + CatBoost simple-average + isotonic calibration
│   ├── multi_horizon.py      # h=3/7/14/21 consensus + regime-conditional weights
│   └── calibration.py        # isotonic regression on holdout fold
├── sizing/
│   ├── __init__.py
│   └── vol_target.py         # inverse-vol targeting + CDAP regime-gated drawdown control
└── backtest/
    ├── __init__.py
    ├── cpcv.py               # combinatorial purged CV (N=8, k=2, embargo=14)
    ├── dsr.py                # deflated Sharpe ratio (Bailey & López de Prado 2014)
    └── runner_v3.py          # orchestrator: features → regime → models → sizing → trades

scripts/
├── baseline_strategy_v3.py            # standalone V3 entry point (mirrors V2 CLI)
├── build_microstructure_features.py   # one-shot Binance aggTrades fetch + VPIN parquet
├── build_derivatives_features.py      # one-shot funding/OI/liquidation parquet
└── evaluate_v3_cpcv.py                # CPCV evaluation, outputs Sharpe distribution + DSR
```

**Promote-from-hybrid:** the existing `tradingagents/strategies/regime.py` (HMM-3 + BOCPD + Hurst) on `feature/hybrid-modulator` is the seed for `tradingagents/strategies/v3/regime/`. The NH-HMM extension and ensemble dataclass are net-new; the heuristic fallback path is kept.

**Reuse from V2:** V3 calls `tradingagents/strategies/v2_sizing.py` primitives (`compute_realized_vol`, `apply_leverage`, `apply_trend_filter`) where appropriate. `vol_target.py` replaces `vol_targeted_size` + the `aw/cap/dw` heuristic params, but the trend filter primitive is reused as a fallback when HMM confidence is low.

---

## 3. Data flow

```
OHLCV + aggTrades + funding/OI history (per coin, daily)
        │
        ▼
  FeatureBundle ── price techs (V2) ⊕ microstructure (VPIN, OFI) ⊕ derivatives (funding-Z, basis, OI Δ, liq-asym)
        │
        ▼
  RegimeState  ── HMM-3 posterior + Hurst-conditioned confidence + BOCPD changepoint flag
        │
        ▼
  Per-horizon ensemble (LGB + XGB + CatBoost; h ∈ {3, 7, 14, 21})
        │
        ▼
  Calibrated probabilities per horizon (isotonic on holdout fold)
        │
        ▼
  Consensus    ── regime-conditional weights:
                    bull (Hurst > 0.55) → up-weight h=14, h=21
                    bear (Hurst > 0.55) → up-weight h=14, h=21
                    sideways / Hurst < 0.45 → up-weight h=3, h=7
        │
        ▼
  V3Signal    ── direction ∈ {-1, 0, +1}, confidence ∈ [0, 1], horizon, regime
        │
        ▼
  Sizing      ── inverse-vol target 15% annual, capped 2x leverage, CDAP regime-gated
                    drawdown response (de-lever only when DD coincides with confirmed
                    regime shift, not on arbitrary % threshold — Varma 2025)
        │
        ▼
  Position
```

---

## 4. Component specs

### 4.1 `features/microstructure.py`

**Inputs:** Binance `aggTrades` REST endpoint (`/api/v3/aggTrades`) at daily granularity. Configurable lookback (default 730 d). Cached to `data/microstructure_raw/{coin}_aggtrades_{date}.parquet`.

**Outputs (parquet `data/microstructure/{coin}.parquet`):**
- `vpin_50` — VPIN computed via López de Prado volume bucketing with 50-bucket window
- `vpin_50_z` — rolling 30-day Z-score of VPIN
- `ofi_d` — order flow imbalance: `(buy_volume − sell_volume) / total_volume` for the day
- `ofi_d_w` — 7-day volume-weighted OFI (research §2.2 — weekly aggregation outperforms daily)
- `aggressor_ratio` — share of trades flagged as taker-buy

**Look-ahead guard:** all features are bar-close-aligned; bucketing uses past trades only. `as_of: pd.Timestamp` parameter slices `df[df.index <= as_of]` before any rolling op.

**Failure modes:**
- 429 rate limit → exponential backoff (base 1s, cap 60s, max 5 retries)
- Date range > 6 months from now → Binance free tier may return empty; emit warning, mark feature as `NaN` for that range
- Partial response → forward-fill ≤2 bars, longer gap drops the row with logged warning
- Network outage → fall back to klines-derived crude OFI (volume × sign(close-open) / total_volume), feature flag `mode=proxy`

**Config:**
```python
@dataclass
class MicrostructureConfig:
    bucket_count: int = 50
    z_window: int = 30
    weekly_window: int = 7
    cache_dir: Path = Path("data/microstructure_raw")
    out_parquet: Path = Path("data/microstructure")
    proxy_mode: bool = False
```

### 4.2 `features/derivatives.py`

**Inputs:**
- Binance Futures REST `/fapi/v1/fundingRate`, `/fapi/v1/openInterestHist` (free)
- Binance Futures `/fapi/v1/premiumIndex` for basis
- Coinglass for liquidation history (free tier sufficient at daily granularity)

**Outputs (parquet `data/derivatives/{coin}.parquet`):**
- `funding_8h_level` — most recent 8h funding rate
- `funding_z_30` — 30-day Z-score of funding rate
- `funding_slope_7` — current 8h funding − 7-day SMA
- `basis_annual` — annualized perpetual − spot basis
- `oi_change_1d` — log change in open interest
- `oi_change_7d` — 7-day log change
- `liq_asym_24h` — `(long_liquidations − short_liquidations) / total_liquidations` over rolling 24h

**Look-ahead guard:** Funding rate is settled every 8h; the bar-close timestamp uses the most recent settled value strictly less than the bar close. OI uses end-of-day snapshot.

**Failure modes:**
- Coinglass rate limit → use Binance liquidation websocket archive if available, otherwise zero-out `liq_asym_24h` with staleness counter
- Funding API stale > 24h → forward-fill with staleness flag; if > 72h, set funding-derived features to `NaN`

### 4.3 `regime/`

**Promote from `feature/hybrid-modulator`:** existing `tradingagents/strategies/regime.py` already implements HMM-3 + BOCPD + Hurst. V3 extends rather than rewrites.

**`hmm_v2.py` — NH-HMM extension:**
- Transition probabilities depend on `(realized_vol_21d, funding_rate_8h)` covariates per Yamaguchi 2026
- Posterior updated **online** via forward algorithm with frozen emission/transition params (look-ahead-safe)
- Bayesian estimation of emission means/variances during training only (`scripts/v3_train_regime.py`)

**`ensemble.py` — combines signals:**
- HMM posterior → primary label (bull/sideways/bear) + confidence
- Hurst rolling 63-bar → directional reinforcement (H > 0.55) or sideways pull (H < 0.45)
- BOCPD changepoint → if changepoint flag fires within 5 bars, dampen confidence by 0.5×
- Output: `RegimeState(label, confidence, hurst, changepoint_alert, posterior: dict)`

**Training:** Single offline fit on 2017-01 → 2024-12 per coin, pickled to `data/checkpoints/regime_hmm_v3_{coin}.pkl`. Refit only on manual trigger (concept drift detection out of scope).

### 4.4 `models/`

**`ensemble.py`:**
- `EnsembleModel` wraps three estimators (`LGBMClassifier`, `XGBClassifier`, `CatBoostClassifier`)
- Same hyperparams as V2's LGB for LGB; defaults from research for XGB/CatBoost; tuned per-horizon via CPCV
- Predict path: average raw probabilities, then apply per-model isotonic calibration fitted on holdout fold
- Optional dependencies — if `xgboost` or `catboost` missing, drop from average and log warning. LGB always required.

**`multi_horizon.py`:**
- Trains four `EnsembleModel` instances per coin for h ∈ {3, 7, 14, 21}
- Per-horizon SHAP analysis selects features for that horizon (microstructure heavy at h=3, momentum + funding at h=7, on-chain/macro at h=14-21 — note: macro deferred so h=14-21 use derivatives + technicals only)
- Consensus: regime-conditional horizon weights returned by `RegimeState`-aware combiner. Default weights:
  - Trending (Hurst > 0.55): `{3: 0.10, 7: 0.20, 14: 0.35, 21: 0.35}`
  - Sideways / Hurst < 0.45: `{3: 0.35, 7: 0.35, 14: 0.20, 21: 0.10}`
  - Otherwise (uncertain): equal weights `{3: 0.25, 7: 0.25, 14: 0.25, 21: 0.25}`

**`calibration.py`:** isotonic regression per `(model, horizon)` fitted on the last 20% of the train fold (held out from main training).

### 4.5 `sizing/vol_target.py`

```
target_annual_vol = 0.15
realized_vol_21d  = compute_realized_vol(prices, lookback=21) * sqrt(252)
base_size         = target_annual_vol / max(realized_vol_21d, 0.01)
position          = clip(base_size * direction * confidence, -2.0, +2.0)
```

**CDAP drawdown control (Varma 2025):**
```
if portfolio_dd_pct > 5% AND regime in {bear} AND regime.confidence > 0.6:
    de-lever to 0.5× position
elif portfolio_dd_pct > 10% AND regime.confidence > 0.7:
    flat
# No action on arbitrary % threshold without regime confirmation
```

### 4.6 `backtest/cpcv.py`

- N = 8 groups, k = 2 test groups → C(8,2) = 28 splits
- Purging: drop training samples whose label horizon overlaps test range
- Embargo: 14 bars (longest prediction horizon) gap between train end and test start
- Output: list of `(train_idx, test_idx)` index arrays + per-split metric record

### 4.7 `backtest/dsr.py`

```
DSR = (SR − E[max SR | null]) / SE(SR)
```
- `E[max SR | null]` accounts for # strategy variants tested (P1-P5 + V2 + V3 sweeps)
- Variance-of-SR adjusted for skew + kurtosis of returns
- Reproduces Bailey & López de Prado (2014) worked example as test fixture

### 4.8 `backtest/runner_v3.py`

End-to-end orchestrator:
1. Load OHLCV, microstructure parquet, derivatives parquet, regime pickle
2. For each bar in eval window:
   - Build `FeatureBundle` (look-ahead-guarded)
   - Update `RegimeState` via online HMM forward + BOCPD + Hurst
   - Predict per-horizon probabilities (calibrated)
   - Compute regime-weighted consensus → `V3Signal`
   - Apply vol-target sizing + CDAP
3. Apply V2-style trade execution (fees, slippage, hold logic, stop-loss, circuit breaker — all reused from `tradingagents/backtesting/engine.py`)
4. Output: equity curve, metrics dict, per-bar `V3Signal` log

---

## 5. Hybrid integration

**New abstraction:** `tradingagents/strategies/quant_signal_provider.py`

```python
class QuantSignalProvider(Protocol):
    def signal(self, coin: str, as_of: pd.Timestamp) -> QuantSignal: ...

class V2QuantSignalProvider:
    """Wraps existing V2 baseline_strategy_v2 logic."""

class V3QuantSignalProvider:
    """Wraps v3.backtest.runner_v3.predict_one(coin, as_of)."""
```

Both emit the existing `QuantSignal` pydantic contract used by the modulator. No modulator code changes.

**Hybrid CLI surface:**
- `scripts/generate_hybrid_signals.py --quant-version v3` (default v3)
- `scripts/generate_hybrid_signals.py --quant-version v2` (legacy reproducibility)
- `scripts/backtest_hybrid.py` accepts the same flag, threaded through to its provider construction

**Existing rolling-edge + Skeptic-Quant + FinCon CVRF logic** continues working unchanged because they consume `QuantSignal` not raw V2 internals.

---

## 6. Backtest evaluation

### Track 1 — Headline A/B (88-bar window)

- Window: 2026-01-16 → 2026-04-15 (matches V2 baseline)
- Universes: 2-coin (BTC+ETH), 3-coin (BTC+ETH+BNB), 5-coin
- Metrics: Sharpe, return, MaxDD, hit rate, # trades, avg hold
- Output: `data/multi_*_v3/baseline_v3_equity.png` + `metrics.json`

### Track 2 — CPCV thesis rigor

- Window: 2024-05-01 → 2026-04-15 (~720 bars per coin)
- N=8 groups, k=2 test → 28 splits → distribution of OOS Sharpe
- Walk-forward sanity check: 252-bar expanding train, 14-bar test, 14-bar embargo, ~33 test blocks
- Report: Sharpe distribution boxplot, DSR (vs # trials = 12 — P1-P5 + V2 + V3 + 4 sweep variants), PBO (probability of backtest overfitting)
- Output: `data/v3_cpcv/{coin}/sharpe_distribution.parquet` + summary table

### Per-Tier-2 ablation

To validate research's "+0.1-0.3 Sharpe" claims, run V3 with each component ablated:
- V3 − Q2 (no microstructure)
- V3 − Q3 (no derivatives)
- V3 − Q5 (LGB-only, no XGB/CatBoost)
- V3 − Q6 (h=7+h=14 only, no h=3, h=21)
- V3 − Q8 (V2 sizing, no vol-target)
- V3 baseline regime (V2 SMA30 instead of HMM)

Reports per ablation in `THESIS_FINDINGS.md`.

---

## 7. Error handling & graceful degradation

| Component | Failure | Behavior |
|---|---|---|
| Binance aggTrades 429 | Rate limit | Exponential backoff base=1s cap=60s max=5; on persistent fail → `proxy_mode` |
| Microstructure feature missing | Partial date range | Forward-fill ≤2 bars; longer gap → drop row, log warning |
| HMM pickle missing | Train script not run | Heuristic fallback (existing hybrid-branch behavior) |
| CatBoost / XGB import fail | Optional dep missing | Drop from ensemble, log; LGB always required |
| Funding/OI API down | Coinglass / Binance Futures rate limit | Last known + staleness counter; > 24h → `NaN` derivatives features |
| CPCV split too small | Bug guard | Assert min train ≥ 252 bars, abort with actionable error |
| Calibration holdout empty | Wrong fold config | Skip calibration, raw probs, warning |
| Live-mode feature build fail | Cron job error | Reuse last available parquet, alert via existing P14.3 monitoring path |

**Look-ahead invariants (asserted in tests):**
- All `build_*_features(prices, as_of)` slice `df[df.index <= as_of]` before rolling ops
- VPIN bucketing uses past trades only, never current bar's close
- HMM posterior updates online via forward algorithm with frozen params (research §4.4)
- CPCV embargo enforced via index gap check, asserted in `test_cpcv_no_overlap`

---

## 8. Testing

| Layer | Test | Mechanism |
|---|---|---|
| Feature builders | Golden parquet input → bit-exact feature output | pytest + parquet fixtures in `tests/v3/fixtures/` |
| HMM | Posterior sums to 1.0; states monotonic in mean return | pytest |
| BOCPD | Synthetic regime change at known bar → flag fires within 5 bars | pytest synthetic |
| CPCV | Embargo gap respected; no train/test overlap (assert) | pytest |
| DSR | Reproduce Bailey & López de Prado worked example | pytest |
| Vol-target sizing | Constant target, varying vol → position scales inversely | pytest |
| CDAP | DD threshold without regime confirmation → no action; with confirmation → de-lever | pytest |
| Ensemble | Stub LGB+XGB+CatBoost preds → average correct, calibration monotonic | pytest |
| Multi-horizon weighting | Trending regime → h=14/21 weighted up; sideways → h=3/7 weighted up | pytest |
| Integration | V3 on 88-bar window — metrics file produced, schema valid | pytest end-to-end |
| Regression | V2 outputs unchanged after V3 lands (golden CSV) | pytest golden |
| Hybrid integ | `--quant-version v3` produces same `QuantSignal` schema as v2 | pytest |
| Look-ahead | Inject future-leaking sample; assert builder rejects | pytest |

**Skip mocking models** — train tiny LGB on synthetic data inside test fixtures. Avoids mock/prod divergence (per saved feedback `feedback_testing.md`).

---

## 9. Training & ops

- **HMM-3 NH-HMM:** trained once 2017-01 → 2024-12 per coin via `scripts/v3_train_regime.py`, pickled to `data/checkpoints/regime_hmm_v3_{coin}.pkl`. Refit on manual trigger.
- **Per-horizon ensembles:** retrained inside CPCV per fold (no leakage) for thesis evaluation. For headline 88-bar A/B, trained once on `< window_start − 14d embargo`.
- **Microstructure / derivatives parquets:** one-shot batch via `build_microstructure_features.py` + `build_derivatives_features.py`. Strategy reads from parquet — no live API during backtest.
- **Live mode:** features rebuilt nightly via cron (extends existing P14.2/P14.3 cron from live-testnet-deployment design). Failure mode: stale parquet alert, fall back to V2 quant signal.

---

## 10. Research alignment & expected impact

| Research item | V3 module | Expected Δ Sharpe (research) | Risk-adjusted estimate |
|---|---|---|---|
| Q1 HMM-3 + BOCPD + Hurst (NH-HMM) | `regime/` | +0.3 to +0.5 | +0.15 to +0.25 |
| Q2 VPIN + OFI | `features/microstructure.py` | +0.3 to +0.5 | +0.15 to +0.25 |
| Q3 derivatives pack | `features/derivatives.py` | +0.2 to +0.3 | +0.10 to +0.15 |
| Q4 CPCV + DSR | `backtest/` | robustness only | (methodological) |
| Q5 LGB+XGB+CatBoost ensemble | `models/ensemble.py` | +0.1 to +0.2 | +0.05 to +0.10 |
| Q6 multi-horizon h=3/7/14/21 | `models/multi_horizon.py` | +0.1 to +0.3 | +0.05 to +0.15 |
| Q8 vol-target sizing | `sizing/vol_target.py` | +0.1 to +0.2 (DD reduction) | +0.05 to +0.10 |

**Headline target:** V2 Sharpe 3.31 → V3 Sharpe 3.5–4.5 on the 88-bar window (assuming 30–50% of research deltas materialize and partial overlap between Q1/Q6 regime gains).

**Failure tolerance:** if CPCV distribution median is below V2 median by more than 0.3 Sharpe, the V3 path is rolled back to v2-flag default and the offending component is bisected per ablation results.

---

## 11. Open questions / risks

1. **Binance free-tier aggTrades historical limit** — if depth is < 6 months, microstructure features are NaN for early CPCV folds. Mitigation: proxy-mode klines OFI for historical periods, real VPIN for recent.
2. **NH-HMM convergence** — non-homogeneous HMMs are slower to fit and can fail to converge with covariate sparsity. Mitigation: fall back to standard HMM if `hmmlearn` does not converge in 200 iter.
3. **CatBoost categorical handling** — current feature set is fully numeric, so CatBoost's categorical advantage is not realized. May want to expose regime label as categorical feature (V3.1 follow-up).
4. **CPCV compute cost** — 28 splits × 4 horizons × 3 models × 720 bars × 2-3 coins = O(50k) tree fits. Estimate ~1-2h on dev box; budget allows.
5. **Hybrid modulator regression** — V3 signals have richer confidence distribution than V2 (per-horizon calibrated probabilities). Modulator's `effective_weight` formula was tuned on V2 confidence; may need re-tuning. Tracked as follow-up in implementation plan.

---

## 12. Out of scope / explicit non-goals

- Online / continual learning (research §7.2) — periodic retrain only.
- TFT (Temporal Fusion Transformer) — research notes "marginal advantage at daily freq with ~50 features"; deferred.
- RL portfolio construction — research notes "not a replacement for LGB"; deferred.
- Intraday / 4h / 1h frequency — daily only for V3.
- Macro features (Q7) — deferred to V3.1.
- Kelly rework (Q9) — vol-target sizing is the chosen substitute.
- Cross-asset basis trades — single-coin position sizing only.
