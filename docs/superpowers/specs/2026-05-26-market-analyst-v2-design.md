# Market Analyst v2 — Asset-Agnostic "Do No Harm" Refactor (Spec)

**Date:** 2026-05-26
**Branch:** `feature/market-analyst-v2` (off `feature/sentiment-analyst-v3`)
**Plan:** [`docs/superpowers/plans/2026-05-26-market-analyst-v2.md`](../plans/2026-05-26-market-analyst-v2.md)

## Background

The existing free-text market analyst harms ETH and is statistically indistinguishable from no-analyst on BTC. A previously-run leave-one-out (LOO) ablation on the hybrid V5 stack showed:

| Coin | ΔSharpe of dropping market analyst | p-value (paired) |
|---|---|---|
| ETH | +0.69 (drop **helps**) | 0.997 |
| BTC | +0.08 (drop ~neutral)   | 0.080 |

Reference: `project_loo_ablation` memory and §23.11 of the thesis. This reproduces three independent findings in the LLM-trading literature:

- **FS-ReasoningAgent** (Persdre et al., ICLR 2025 workshop, arXiv:2410.12464): "in cryptocurrency trading, stronger LLMs work worse than weaker LLMs often."
- **FINSABER** (Li, Kim, Cucuringu, Ma; arXiv:2505.07078, KDD 2026): LLM agents are "overly conservative in bull markets, underperforming passive benchmarks, and overly aggressive in bear markets."
- **FinCon** (Yu et al., NeurIPS 2024, arXiv:2407.06567): noise tolerance is the dominant LLM-agent failure mode under mixed market data.

The current fork's market analyst feeds 150+ technical indicators in free-text form. Upstream TradingAgents (`market_analyst.py`, commit `4641c033`) caps at 8 of 12 with explicit anti-redundancy. The fork lost that constraint.

## Failure Mode (one sentence)

Indicator overload + unconstrained free-text output + ticker priors → confidently directional LLM signals when category indicators disagree → average position regresses to zero alpha (BTC) or to harm (ETH, where pretrained narrative priors compound).

## Design Principles

1. **Asset-agnostic.** Single architecture, single prompt, single code path across all coins. Per-coin behaviour emerges from data (calibration, conflict_score, indicator distribution), never from `if coin == "ETH"` branching.
2. **Do no harm floor.** When uncertain, the analyst contributes ~0 to modulator output. Mechanism: FLAT-by-default under conflict + endogenous per-coin weight collapse via calibrated conviction.
3. **Deterministic core, narrow LLM.** All indicator computation, regime tagging, category voting, and conflict scoring are deterministic Python (no LLM). The LLM is invoked only to refine or confirm the deterministic default with a structured JSON output.
4. **Pydantic gates the interface.** LLM output is schema-validated. Failure to parse → fallback to deterministic default with conviction = 0.
5. **Anonymised asset name.** Glasserman & Lin (arXiv:2309.17322) and the existing sentiment-v3 anonymizer infrastructure: the prompt never sees the literal ticker, eliminating pretrained narrative bias as a confound.

## Mechanism Stack (M1-M6)

### M1 — Conflict-gated FLAT
Pydantic-enforced output `{direction, conviction, conflict_score, indicators_used, dissenting_indicators, rationale}`.

Asymmetric default direction:
- LONG: ≥ 2 of 4 category votes are +1 AND 0 categories are -1.
- SHORT: ≥ 3 of 4 category votes are -1 AND 0 categories are +1.
- FLAT otherwise.

The 2-vs-3 asymmetry implements the FINSABER bear-aggression correction.

### M2 — Calibrated conviction (endogenous per-coin weight)
Each `(verbalized_conviction, realised_direction)` pair is logged per coin. Fit `IsotonicRegression(out_of_bounds="clip")` on rolling history → calibrator collapses convictions toward ~0.5 on coins where the LLM has no edge. Modulator multiplies the effective weight by `(1 - conflict_score) × calibrated_conviction`, so a coin with no LLM edge endogenously sees weight → 0.

### M3 — Anonymization (removes coin priors)
Reuse `tradingagents.agents.utils.anonymizer` (Asset_A, Asset_B, ... per propagate run). The LLM never sees "Bitcoin" or "Ethereum"; only "Asset_X" plus a metadata struct (regime tag, ATR percentile, 30-day return). Glasserman-Lin distraction effect eliminated by construction.

### M4 — Regime conditioning (not coin conditioning)
Deterministic 4-state regime tag from ADX, ATR percentile, 30-day return:
- TREND_UP / TREND_DOWN / RANGE / HIGH_VOL.

The regime label is passed in the prompt as a string. Every coin in HIGH_VOL is treated identically; no coin-specific routing.

### M5 — Indicator cap (13-name whitelist)
Whitelist: `close_30_sma`, `close_50_sma`, `close_200_sma`, `close_10_ema`, `macd`, `macds`, `macdh`, `rsi`, `boll`, `boll_ub`, `boll_lb`, `atr`, `vwma`. Computed deterministically; the LLM does not pick or compute.

### M6 — Third-person ("Andrew") persona
SYCON-Bench (arXiv:2505.23840, Findings of EMNLP 2025): third-person persona reduces multi-turn sycophantic flips by up to 63.8% in debate scenarios. The v2 system prompt begins "You are Andrew, a conservative technical analyst." applied uniformly across coins.

## Do-No-Harm Theorem (informal)

Per-bar contribution to portfolio return:

```
contribution = effective_weight × signal_correctness − effective_weight × signal_error
```

With M1 + M2:
- `effective_weight = (1 − conflict_score) × calibrated_conviction`
- When LLM has no edge on coin X: empirically `calibrated_conviction → 0.5` and `conflict_score` distribution is high → `effective_weight → 0`.
- → `contribution → 0`.

Floor at 0 contribution requires:
- M1 conflict score is honest (enforced by Pydantic + prompt audit; dissenting_indicators is a required field).
- M2 calibration buffer is warm (cold-start: ≥ 30 conviction-vs-outcome pairs per coin).

## File / Module Layout

New under `tradingagents/market/`:
- `snapshot.py` — Pydantic schemas (`MarketSnapshot`, `MarketAnalystOutput`).
- `indicators.py` — 13-name whitelist + direction rules.
- `regime_tag.py` — deterministic regime classifier.
- `category_vote.py` — aggregation + conflict score + asymmetric default.
- `build_snapshot.py` — orchestrator.
- `_stockstats_utils.py` — shared column-rename helper.

New under `tradingagents/strategies/`:
- `market_calibration.py` — per-coin isotonic wrapper (reuses `IsotonicCalibrator` from `calibration.py`).

Modified:
- `tradingagents/agents/analysts/market_analyst.py` — dual-mode (legacy default + v2 branch under `market_mode == "v2"`).
- `tradingagents/agents/modulator.py` — consumes `market_features` mirroring `sentiment_features`.
- `tradingagents/agents/utils/agent_states.py` — `market_features: dict`.
- `tradingagents/graph/propagation.py` — initializes `market_features: {}`.
- `tradingagents/default_config.py` — `market_mode`, `market_anonymize`, `market_skip_llm`, `market_horizon_days` config knobs + env hooks.
- `scripts/generate_hybrid_signals.py` — `--market-mode`, `--market-skip-llm`, `--market-anonymize`, `--market-horizon-days` CLI flags; persists `market_llm_conviction_raw`, `market_conflict_score`, `market_default_direction` in per-bar signal CSVs.

New scripts:
- `scripts/run_market_v2_ab.py` — 4-variant A/B harness.
- `scripts/fit_market_calibrator.py` — per-coin isotonic calibrator fitter.

## Validation Plan

4-variant A/B over the V5 4-coin universe (BTC / ETH / BNB / SOL), 2026-01-16 → 2026-04-15 (~90 bars), all gpt-4o-mini, paired-bootstrap 10k CI per (variant, coin) pair vs A_pure_quant and B_legacy_market.

| Variant | analysts | market_mode | market_skip_llm |
|---|---|---|---|
| A_pure_quant | onchain, prediction | legacy | False |
| B_legacy_market | market, onchain, prediction | legacy | False |
| C_v2_struct_only | market, onchain, prediction | v2 | True |
| D_v2_full | market, onchain, prediction | v2 | False |

## Acceptance Criteria

Do-no-harm gates (all three must hold to merge):

1. Per-coin ΔSharpe(D_v2_full − A_pure_quant) ≥ 0 for every coin in {BTC, ETH, BNB, SOL}.
2. Worst-coin paired-bootstrap 95% CI lower bound ≥ −0.15.
3. At least one coin with ΔSharpe > 0.3 and p_positive ≥ 0.9.

If any gate fails: iterate on the prompt or asymmetric thresholds, NOT per-coin overrides.

## Open Questions

- Cold-start behaviour: per-coin calibrator requires ≥ 30 (conviction, outcome) pairs before becoming non-identity. On first runs the calibrator is identity → effective weight = `(1 - conflict_score) × raw_conviction`. Is the conflict_score floor sufficient by itself? Empirical question, settled by the A/B.
- Forward-return computation: the calibrator fitter expects `forward_return` in signal CSVs. Generate_hybrid_signals does NOT currently compute it (look-ahead concern within the script). Plan: compute it at fit time by joining against price history. If the fitter consistently lacks data, add an explicit post-hoc forward-return computation step to the A/B harness.
- The `_extract_json_object` helper's greedy `{.*}` regex can fail on responses that include a stray closing brace in the rationale prose. Worst case → fallback to deterministic default with conviction = 0 (the safe direction). Acceptable.

## References

- Persdre et al., "FS-ReasoningAgent," ICLR 2025 Workshop on Advances in Financial AI, arXiv:2410.12464.
- Li, Kim, Cucuringu, Ma, "FINSABER," KDD 2026, arXiv:2505.07078.
- Hong et al., "SYCON-Bench," Findings of EMNLP 2025, arXiv:2505.23840.
- Glasserman & Lin, "Pretraining-induced ticker biases in language models for finance," arXiv:2309.17322.
- "FinCoT" (structured CoT in finance), arXiv:2506.16123.
- "Just Ask for Calibration" (isotonic recalibration), arXiv:2305.14975.
- López de Prado, "Advances in Financial Machine Learning," 2018 (Ch. 7 CPCV; deferred to Task 15 if needed).
