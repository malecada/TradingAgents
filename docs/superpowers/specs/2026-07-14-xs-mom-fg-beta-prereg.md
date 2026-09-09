# Pre-registration: Cross-Sectional Momentum (P1) + Sentiment-Beta Overlay (D1)

**Date:** 2026-07-14  
**Status:** Frozen gates; P1 + D1 grids closed before any experiment.

---

## Frozen Gate Definitions

Both experiments are frozen verbatim in `data/rebuild/gates.json`:

```json
"xs_mom_p1": {
  "registered": "2026-07-14",
  "dev_window": ["2021-01-01", "2025-03-31"],
  "holdout_window": ["2025-04-01", "2026-07-01"],
  "universe_rule": "PIT daily eligibility: USDT-M perp with kline on day D, first kline <= D-30, 30d median quote-volume >= 5000000 USD; rank by 30d median quote-volume, keep top 100; snapshot at each weekly rebalance (Monday close) using data <= that close",
  "portfolio_rule": "EW long-only top-K by momentum at Monday close, held to next Monday close; returns accrue from the bar AFTER the decision bar; momentum = sum of daily log-returns over L days ending S days before the decision close; costs 10bps per side on turnover; benchmark = EW full eligible universe, same mechanics",
  "grid": { "L": [7, 14, 28], "skip": [0, 1], "K": [10, 20] },
  "bootstrap": { "block": 21, "n": 2000 },
  "placebo": "N=500 within-rebalance random rank permutations of the momentum scores, identical mechanics; p=(1+#{placebo SR >= real SR})/(N+1)",
  "dev_select": {
    "net_sr_min": 0.8,
    "delta_sr_vs_benchmark_min": 0.0,
    "p_pos_min": 0.85,
    "placebo_p_max": 0.05,
    "dsr_min": 0.9,
    "tiebreak": "highest DSR, then lowest placebo p"
  },
  "holdout_deploy": { "net_sr_min": 0.5, "delta_sr_vs_benchmark_min": 0.0, "p_pos_min": 0.85, "placebo_p_max": 0.05, "one_shot": true }
},
"fg_beta_d1": {
  "registered": "2026-07-14",
  "dev_window": ["2021-01-01", "2025-03-31"],
  "holdout_window": ["2025-04-01", "2026-07-01"],
  "beta_rule": "rolling 90d OLS beta of coin daily log-return on delta F&G (value diff), min 60 overlapping obs, inputs shift(1)-causal at the decision close",
  "grid_desc": "exactly 2 configs: (a) standalone = EW long the MIDDLE F&G-beta quintile of the eligible universe, weekly, same mechanics/costs as P1; (b) overlay = P1 dev-selected portfolio excluding coins in the extreme (top+bottom) beta quintiles; if P1 selects NONE, only (a) runs",
  "dev_select_standalone": { "net_sr_min": 0.8, "delta_sr_vs_benchmark_min": 0.0, "p_pos_min": 0.85, "placebo_p_max": 0.05, "dsr_min": 0.9 },
  "dev_select_overlay": { "delta_sr_vs_p1_min": 0.0, "p_pos_min": 0.85 },
  "holdout_deploy": { "same_as_dev": true, "net_sr_min_holdout": 0.5, "one_shot": true }
}
```

## Grid Closure Statement

**P1 grid is closed at 12 configurations**: 3 lookback lengths (L ∈ {7, 14, 28}) × 2 skip offsets (skip ∈ {0, 1}) × 2 portfolio sizes (K ∈ {10, 20}).

**D1 grid is closed at 2 configurations**: (a) standalone F&G-beta quintile long, and (b) overlay excluding extreme-beta quintiles.

**Validity rule:** Any configuration evaluated outside these grids voids the respective experiment (P1 or D1). Results outside the frozengrids are ineligible for holdout reporting or thesis acceptance.

---

## Evidence Basis — Mechanism Level

### P1: Cross-Sectional Momentum

**Verified claim (PIVOT_RESEARCH_2026-07-12.md, verified 3-0, high confidence):**

Borri, Liu, Tsyvinski, and Wu (arXiv 2510.14435, survivorship-controlled 16,468-coin universe) document that post-2020 crypto momentum — specifically 2-week cross-sectional momentum long-short — persists at t = 3.70 (Newey-West robust), with economic magnitude 0.026→0.021 USD/week, undecayed by institutionalization. Independently verified (JFQA 2025, "Trend Factor for the Cross-Section of Cryptocurrency Returns"): machine-learned trend factors reliably price 3,000+ coins at weekly-scale on Binance universes.

**Mechanism:** High-momentum coins outperform low-momentum coins on a weekly basis in the cross-section, controlled for survivorship bias (coins delisted mid-sample included in historical returns up to delisting date). The effect is robust to post-2020 regime changes and institutionalization pressure observed in spot markets.

**Central caveat (from PIVOT_RESEARCH_2026-07-12.md):** All external headline Sharpes are **gross of trading costs**. Retail-venue net-of-cost survival must be established in-house — which is precisely what this pre-registered evaluation tests. The literature's own admitted gap is: does published wide-universe crypto momentum survive realistic retail costs on the tradable subuniverse?

### D1: Sentiment-Beta Cross-Sectional Pricing

**Verified claim (SENTIMENT_EARLY_WARNING_RESEARCH_2026-07-14.md, verified 3-0 / 2-1, from peer review):**

Journal of Behavioral and Experimental Finance (2025, *S2214635025000243*): on 1,100+ coins over 2018–2024, F&G-change beta (rolling 90d OLS of coin return on delta Fear & Greed) is priced **nonlinearly** in cross-section. Intermediate-beta coins (β ≈ 0 to +1, i.e., neutral-to-moderate sensitivity to F&G swings) earn +3.57%/week risk-adjusted excess return vs extreme-beta coins (β >> 1, i.e., high sensitivity, or β << 0, i.e., reverse sensitivity). This is the strongest sentiment-related cross-sectional effect found in the literature, using only free F&G index + price data, weekly frequency, wide universe.

**Mechanism:** Coins with intermediate sentiment beta neither panic-sell on F&G dips nor rally exuberantly on F&G spikes; they provide stable relative value. Extreme-positive-beta coins (high-vol altcoins that move 2–3x with fear swings) are overpriced; extreme-negative-beta coins are underpriced (anti-correlated with sentiment regime). The pricing is nonlinear: the premium accrues to the middle, not the extremes.

**Caveat:** This is one peer-reviewed paper, gross of costs, on a 2018–2024 sample. Net-of-cost validity on current Binance futures, under weekly rebalance with 10bps fees + funding costs, is unknown and is the subject of this pre-registered test.

---

## Validity Precondition

Both P1 and D1 require **survivorship-safe universe construction**: the PIT (permanent, immutable ledger) must include delisted symbols with their full trading history, up to delisting date. Any symbol added mid-sample must have its historical returns recomputed as missing-not-at-random (not backfilled, not forward-filled). Failure to observe survivorship safety voids both experiments' validity.

This is non-negotiable because all external evidence (Borri et al. 16,468-coin study, JFQA trend factor study) controls for survivorship; any in-house replication that does not is not a replication but a different (biased) experiment.

---

## References

- PIVOT_RESEARCH_2026-07-12.md (internal; Borri et al. arXiv 2510.14435, JFQA 2025 CTREND, Schmeling et al. BIS WP 1087, Fieberg et al. IRFA 2024)
- SENTIMENT_EARLY_WARNING_RESEARCH_2026-07-14.md (internal; JBEF 2025 S2214635025000243, arXiv 2602.07018, ScienceDirect corpus)
