# LLM Trading System — Findings, Limitations, and Research Gaps

**Status:** Working summary as of 2026-05-05. Companion to `THESIS_FINDINGS.md` (full empirical record). This document distils what is settled, what is unresolved, and what still needs investigation before defense.

Cross-references throughout point to the relevant section of `THESIS_FINDINGS.md` (e.g. §10.7 = Phase 4).

---

## 1. Headline result

| Strategy | Window | Return | Sharpe | MaxDD |
|---|---|---:|---:|---:|
| V2 quant baseline (BTC+ETH) | 2026-01-16 → 2026-04-15 (88 bars) | +36.59% | **+3.31** | 6.16% |
| **Mixed (BTC=quant, ETH=LLM hybrid)** | same | +34.31% | **+2.94** | 6.55% |
| Pure LLM hybrid P4 (BTC+ETH) | same | +21.17% | +1.46 | 10.44% |
| Pure LLM, no hybrid sizing (P4) | same | +0.86% | +0.21 | 4.81% |

**Thesis claim (revised after §10.9):** the multi-agent LLM stack does *not* dominate the quant baseline on the tested window. The defensible contribution is **per-coin augmentation** — routing ETH through the LLM hybrid while keeping BTC on the V2 quant strategy — which captures ~89% of the quant Sharpe and 94% of the return, with no MaxDD penalty.

The "LLM beats quant" framing is unsupported by the current evidence. The "LLM contributes a measurable, regime-relevant edge on at least one asset" framing is supported.

---

## 2. What is settled

These conclusions are stable across multiple ablations and should be reported as findings, not hypotheses.

### 2.1 BTC is structurally hard for the LLM stack
Across five phases (P1 → P5), every model upgrade, prompt rewrite, and sizing tweak failed to make BTC LLM signals beat the V2 quant term-structure-consensus baseline. P4 produced the only positive BTC Sharpe (+1.18, hybrid sizing), and even there the win rate was 50% (chance level) — the gain came from larger position scaling on a roughly correct-on-average direction call, not from sharper signal. The V2 quant strategy hits Sharpe 2.42 on the same coin and window. (§10.9 finding 2)

**Hypothesis (untested):** BTC's price action in this regime is dominated by macro flows (rate expectations, ETF inflow/outflow, spot-Bitcoin correlation with NDX) that the LLM analysts do not model directly. The Alpaca news firehose for BTC is also saturated relative to information content, producing high-volume but low-signal sentiment input. (§10.9)

### 2.2 ETH is where LLM contribution is genuine
P4 ETH hybrid: +27.21% return, Sharpe 1.89. P3 ETH hybrid: +19.23% return, Sharpe 1.56. Across phases the ETH leg consistently produced positive risk-adjusted returns under hybrid sizing. The V2 quant ETH leg in the same window is Sharpe 3.38 — the LLM does not match it but is in the same regime. (§10.9 finding 3)

The proposed mechanism: ETH's price is more narrative-driven (ETF approvals, Dencun, restaking, rollup competition) than BTC's, and the multi-source sentiment + on-chain reasoning the LLM stack performs is genuinely additive in that regime.

### 2.3 LGB-magnitude hybrid sizing is the single largest LLM-side improvement
Pure LLM 5-level signals (no hybrid sizing) deliver near-zero portfolio Sharpe in every phase tested. The hybrid layer multiplies LLM directional confidence by an LGB-derived expected-magnitude prior, with a disagreement penalty (`dw`). Across P3–P4, switching from pure to hybrid sizing moved portfolio Sharpe from −0.48 to +1.42 (P4). (§10.5, §10.7)

This is a methodologically important point: **the LLM does not produce a complete trading signal on its own.** It produces a directional-confidence signal that requires a quantitative magnitude prior to be tradeable. This should be stated explicitly in the thesis.

### 2.4 Format compliance is not the same as alpha (P5 ablation)
Phase 5 hardened the PM prompt to force `Confidence: NN/100` numeric output. Numeric extraction rate jumped 54% → **100%**. Portfolio Sharpe fell 1.42 → 0.98. ETH Sharpe regressed 1.89 → −0.85. (§10.8)

The hardened prompt apparently shifted LLM attention toward output-format compliance and away from analytical depth, while simultaneously pushing the PM into more granular OVERWEIGHT/UNDERWEIGHT calls that the hybrid sizing then amplified in the wrong direction. The bucket fallback (HIGH/MEDIUM/LOW) on the original 25% of non-compliant rows was *protective*, not lossy. (§10.8 finding 1)

This is a clean negative result and should be reported as such — it bounds the "fix the prompt to be more strict" lever and supports a more nuanced view of the format-vs-content tradeoff.

### 2.5 Phase progression: model + tool-use mechanics > prompt content
P3 → P4 changed the model (`gpt-4o-mini` → `gpt-5.4-mini`), reordered prompts for OpenAI cache compatibility, and replaced 5–10 sequential indicator calls with a single batch call. **No prompt content changed.** Portfolio return jumped 7.56% → 20.55% (≈2.7×). (§10.7 finding 1)

Suggests that, at this stage of the system's maturity, gains are in the engineering of the model interaction (decisiveness, tool-call discipline, cost structure) rather than the analytical wording of prompts.

### 2.6 PIT data infrastructure is solid
The point-in-time sentiment and on-chain pipelines are bitemporally correct, audited, and reproducible:
- PIT sentiment: 4-analyst rescored (P1) + GDELT/F&G/HF (P2). (§10.1, §10.3)
- PIT on-chain: CoinMetrics + DefiLlama, 5.5-year backfill, 11,277 rows, regime-conditional Sharpe gain documented with bootstrap CI. (§11.6, §11.7, §11.9)

This work is the strongest quantitative foundation in the thesis and is not the source of any of the LLM-side limitations below.

---

## 3. Hard limitations of the LLM evaluation

These are the points where current evidence does not support strong conclusions, and which should either be addressed before defense or explicitly framed as scope limitations.

### 3.1 Single-regime evaluation
**The entire LLM evaluation runs on one 88-bar window: 2026-01-16 → 2026-04-15.** This is a bear-to-sideways regime for BTC (drift down ≈10%) with a divergent ETH path. All Phase 4 / Phase 5 / mixed-strategy conclusions are conditioned on this regime. (§10.9 next-step 3)

The thesis cannot claim regime robustness for the LLM stack. It can claim per-window performance only. A bull-regime validation window is the single most important missing experiment.

### 3.2 Single model family at the canonical result
The P4 result (and therefore the mixed-strategy result) is generated entirely by `gpt-5.4-mini` for deep_think and `gpt-5.4-nano` for quick_think. There is no cross-model validation — Claude Haiku 4.5, DeepSeek V4-Flash, and Llama 4 Scout all support the function-calling stack but have not been run. The Anthropic key was not provisioned in time. (§10.7 next-step, §10.9 next-step 4)

Without cross-model validation, we cannot distinguish "the LLM stack with appropriate prompts captures ETH narrative alpha" from "GPT-5.4-mini specifically has internalized post-Aug-2025 ETH news patterns." The lookahead concern from §3.3 amplifies this risk.

### 3.3 Training-cutoff lookahead is not formally tested
GPT-5.4-mini's training cutoff is August 2025. The backtest window starts 2026-01-16 — five months after cutoff, so direct memorization is technically ruled out. **However**, post-cutoff news events that the LLM reasons about during the backtest are fed in via the (PIT-correct) Alpaca/GDELT/F&G pipeline, and the model's *priors* about how crypto news translates to price action are entirely from the pre-cutoff training distribution.

The placebo cross-check recommended in `llm_provider_analysis.md` — run the same window on a model with a pre-2024 cutoff (Claude 3 Haiku, Aug 2023; GPT-4o-mini, Oct 2023) and look for signal collapse or signal preservation — has not been performed. This is the canonical robustness test for LLM trading work and its absence is a real limitation. (§10.7 next-step)

### 3.4 No statistical significance test on the mixed-strategy gain
The Sharpe difference between V2 quant 2-coin (3.31) and Mixed BTC-quant + ETH-LLM (2.94) is 0.37 over 88 daily bars. The on-chain work in §11.9 used block-bootstrap CI for a comparable Sharpe difference; this has not been done for the LLM mixed-strategy comparison.

Without a significance test, the claim "mixed achieves 89% of quant Sharpe" is descriptive, not inferential. A 95% bootstrap CI on the Sharpe ratio of each leg, and on the Sharpe difference, is a one-day analysis and should be added.

### 3.5 Hybrid sizing parameter search may be overfit
P4 hybrid params (`aw=2.0, cap=2.0, dw=0.5`) and the §10.9 update (`dw=0.3`) were selected by sweep on the same 88-bar window used to report final Sharpe. There is no held-out validation set for the sizing parameters. (§10.9 table)

The portfolio gain from the `dw=0.5 → dw=0.3` switch is 0.04 Sharpe, which is plausibly within the in-sample noise floor. The mixed-strategy result is robust to this (since `aw=2.0 cap=2.0` is the dominant lever), but the parameter search itself is methodologically weak. The honest framing: "we report the best in-sample-tuned hybrid params; out-of-sample stability is untested."

### 3.6 BNB destabilises every multi-coin run
Adding BNB to a 2-coin portfolio in P3 and P5 consistently degraded portfolio metrics (P5: Sharpe 0.98 (2c) → 0.50 (3c)). The on-chain pool can include BNB cleanly (§11.8 BNB-mask fix), but the LLM signals on BNB remain noisier than on BTC/ETH. Phase 2 documented thinner Alpaca news coverage for BNB as the likely cause. (§10.3, §10.8 finding 4)

The mixed strategy is therefore reported as 2-coin only. Whether a `BNB=quant` leg added to the mix would help is open (§10.9 next-step 2) and worth a one-script test.

### 3.7 No live-money / forward-paper validation of the mixed strategy
The live-testnet deployment work targets the V2 quant strategy on Hetzner with Binance demo. The mixed strategy specifically (BTC quant + ETH LLM hybrid) has not been deployed forward, even on testnet. All mixed-strategy claims are backtest-only. (Memory: live testnet deploy work)

### 3.8 The LLM stack as evaluated does not reach `Buy` calls on BTC frequently enough
P4 BTC signal distribution: 53 SELL / 19 BUY / 17 HOLD / 1 OW (across 90 bars). The systematic-bearish bias inherited from P1–P3 was reduced but not eliminated. The strategy is consistently more comfortable shorting BTC than going long, even as BTC trended sideways-to-modestly-up in parts of the window. This is a model-level behavior we did not fully diagnose. (§10.7 finding 3)

### 3.9 Cost is not yet reconciled against the optimisation projections
Cumulative spend is approximately $11–15 across all P1–P5 runs. The `llm_provider_analysis.md` projections (e.g. Haiku 4.5 with 80% cache + Batch ≈ $1/run) are theoretical — `prompt_cache_hit_tokens` and per-agent cost histograms have been logged but not formally reconciled in the thesis. For a defense that includes cost arguments, this needs a clean table.

---

## 4. Specific items requiring further research

Ordered by estimated impact on the thesis claims, not by effort.

### 4.1 Cross-model validation (P4 prompt + hybrid, second model cohort)
**Why it matters:** §3.2 + §3.3. Without it, the P4/mixed result is single-model and unverifiable.
**What to do:** Provision Anthropic key. Re-run the P4 prompt + `aw=2 cap=2 dw=0.5` hybrid pipeline using `claude-haiku-4-5-20251001` for deep_think and quick_think. Compare ETH leg Sharpe and signal distribution against the GPT-5.4-mini result. If ETH alpha persists, the mixed strategy is model-robust. If it collapses, the GPT-5.4-mini result is suspect for lookahead/specificity reasons.
**Estimated cost:** ≈ $11–15 with cache + Batch (per `llm_provider_analysis.md` §75).
**Estimated time:** 1–2 days for fresh signals + analysis.

### 4.2 Pre-cutoff placebo run
**Why it matters:** §3.3. Standard methodological control for LLM-on-finance work.
**What to do:** Re-run P4 prompt with `gpt-4o-mini` (Oct 2023 cutoff) — already used in P1–P3 so the wiring exists. Compare ETH leg Sharpe. If ETH alpha is preserved with the older, lookahead-clean model, the mixed-strategy claim is methodologically sound. If the alpha disappears, the P4 result is at least partly memorisation.
**Estimated cost:** trivial — gpt-4o-mini is already cached for this window for P1–P3, only the new P4-style prompt run is needed.
**Estimated time:** half a day.

### 4.3 Bull-regime out-of-sample window
**Why it matters:** §3.1 — the most important external-validity gap.
**What to do:** Identify a ≥60-bar bull-regime window after the GPT-5.4-mini Aug 2025 cutoff but outside the current 2026-01 → 2026-04 set. A reasonable candidate is 2025-09-01 → 2025-12-31 (BTC trended up through Q4 2025 in the actual market). Run the P4 prompt + hybrid sizing + mixed strategy on this window. Report whether the BTC=quant / ETH=LLM split still wins.
**Estimated cost:** ≈ $5 with cache + Batch.
**Estimated time:** 1 day; requires backfilling Alpaca news + on-chain features for the window if not already present.

### 4.4 Block-bootstrap Sharpe CI for the mixed-strategy comparison
**Why it matters:** §3.4. Promotes the headline result from descriptive to inferential.
**What to do:** Apply the §11.9 bootstrap pattern to the mixed-strategy daily PnL series. Report 95% CI on Sharpe of (a) V2 quant 2-coin, (b) pure LLM P4 hybrid, (c) Mixed. Test whether (c) ≥ (b) is significant at 95%.
**Estimated cost:** zero.
**Estimated time:** half a day.

### 4.5 Walk-forward parameter selection for hybrid sizing
**Why it matters:** §3.5. Removes the in-sample-tuned objection.
**What to do:** Split the 88-bar window into rolling train/test windows (e.g. 30-day train, 14-day test). Re-fit `aw, cap, dw` on each train window, evaluate on the immediately-following test window. Aggregate test-window metrics. Report whether the held-out hybrid Sharpe matches the in-sample Sharpe.
**Estimated cost:** zero (no LLM calls — sizing operates on existing signals).
**Estimated time:** 1 day.

### 4.6 BTC LLM signal post-mortem
**Why it matters:** §3.8 — the biggest model-behaviour gap and the reason the thesis claim has to fall back to per-coin policy.
**What to do:** Take the P4 BTC SELL calls. For each, log the analyst sub-reports (market, on-chain, sentiment, prediction). Cluster the wrong-direction SELL calls by cause (e.g. "macro-driven SELL on a sideways trend day", "sentiment-driven SELL on noise"). Identify the one or two dominant failure modes. If the failure is concentrated, a targeted prompt fix (or analyst removal — e.g. drop sentiment for BTC) is testable.
**Estimated cost:** zero — uses existing logs.
**Estimated time:** 1–2 days, mostly reading.

### 4.7 BNB-leg integration into the mixed strategy
**Why it matters:** §3.6, §10.9 next-step 2.
**What to do:** Run two variants — Mixed{BTC=quant, ETH=LLM, BNB=quant} and Mixed{BTC=quant, ETH=LLM, BNB=LLM} — equal-weighted. Compare to current 2-coin mixed and to V2 quant 3-coin. Decide whether 3-coin mixed is reportable.
**Estimated cost:** zero (BNB signals already exist from P5).
**Estimated time:** half a day.

### 4.8 Forward paper validation of mixed strategy on testnet
**Why it matters:** §3.7. Demonstrates the system survives outside-of-backtest reality (data feeds, latency, slippage, signal-to-execution lag).
**What to do:** Add the LLM ETH leg to the existing live-testnet deployment (per the `live_testnet_deploy` memory). Run for 30 days. Report cumulative PnL alongside the testnet quant baseline.
**Estimated cost:** ≈ $30/month in LLM API for a 30-day forward run.
**Estimated time:** 1 day to wire, 30 days to observe.

### 4.9 Cost reconciliation table
**Why it matters:** §3.9. Required if the thesis makes any cost-of-operation claim.
**What to do:** Pull `prompt_cache_hit_tokens` from the SQLite replay cache + per-agent histograms (`scripts/analyze_replay_cache.py`). Build a single table: per-phase realised cost vs. sticker, vs. optimised projection from `llm_provider_analysis.md`.
**Estimated cost:** zero.
**Estimated time:** half a day.

---

## 5. What the thesis can and cannot claim

A defensible scope, given current evidence:

**Can claim**
- A multi-agent LLM stack with PIT-correct sentiment, on-chain, and price-prediction analysts can produce tradeable directional signals on at least one major asset (ETH).
- LLM signals require a quantitative magnitude prior (LGB-derived hybrid sizing) to be portfolio-tradeable; pure LLM signals produce near-zero risk-adjusted return.
- A per-coin policy that routes BTC through the quant baseline and ETH through the LLM hybrid captures most of the quant baseline's risk-adjusted return while adding interpretable, narrative-aware decision-making to the ETH leg.
- Output-format compliance and analytical alpha can trade off against each other (P5 ablation).
- The point-in-time data infrastructure (sentiment Phase 1+2, on-chain Phase 1) is an independent contribution validated across 5.5 years and three coins.

**Cannot claim, given current evidence**
- That the LLM stack is regime-robust (only one regime tested, §3.1).
- That the LLM stack is model-robust (single model family, §3.2).
- That the result is not partly attributable to lookahead in the training data (no placebo run, §3.3).
- That the mixed-strategy improvement over alternatives is statistically significant (no bootstrap CI, §3.4).
- That the LLM stack would survive forward live trading (no forward validation, §3.7).

---

## 6. Recommended path to defense-ready

If time-constrained, the minimum bar is items §4.2 (placebo, half-day), §4.4 (bootstrap CI, half-day), §4.6 (BTC post-mortem, 1–2 days). These three together turn the thesis from "an interesting empirical result on one window" into "an empirically validated, lookahead-checked, statistically annotated result with a documented model-level limitation."

Items §4.1 and §4.3 (cross-model + bull regime) materially strengthen the claim and should be added if time permits — together they are the difference between "supports the per-coin LLM augmentation thesis" and "supports the per-coin LLM augmentation thesis as model-and-regime-robust."

Items §4.5, §4.7, §4.8, §4.9 are valuable additions but not gating.
