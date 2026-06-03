# §31. Intraday Triple-Barrier SL/TP Sweep (1h fills)

> **Integration note:** This is a standalone draft of THESIS_FINDINGS.md §31. It was kept
> out of `THESIS_FINDINGS.md` only because that file had uncommitted §30 (carry-sleeve) WIP
> at the time of writing and non-interactive git cannot stage part of a file. Paste this
> section into `THESIS_FINDINGS.md` after §30 when committing the carry work, and add the
> CLAUDE.md pointer (bottom of this file).
>
> Branch: `feature/intraday-sltp-sweep`. All numbers below are reproducible (commands at end).

## 31.1 Motivation

The §29 SL/TP sweep ran on a **close-to-close daily engine** (`baseline_strategy_v2.run_coin_backtest`):
a stop/target was tested only against each day's *closing* P&L, never against the intraday path. A
day that wicked through the stop but recovered to close flat was treated as a hold; a day whose
intraday high spiked through a take-profit but closed lower never booked the TP. §29 itself flagged
this as a look-ahead limitation and explicitly declined to recommend a tuned cell.

§31 re-runs the sweep with an **intraday (1h) triple-barrier** model (López de Prado): SL = lower
barrier, TP = upper barrier, an optional trailing stop, and the V2 signal/min-hold as the vertical
barrier. Each day's 1h bars are walked in chronological order and the **first** barrier touched fills
the trade at the barrier level. Barriers fire on **equity-since-entry** (so leverage is already baked
in, matching the daily engine's stop semantics). Critically, the cost model, funding, circuit
breaker and metrics are **byte-identical** to the daily engine — a regression test
(`test_intraday_fills.py::test_equivalence_when_no_intraday_excursion`, plus a 100-seed randomized
stress at max abs equity diff = 0.0) proves that when intraday high==low==close the intrabar engine
reduces exactly to `run_coin_backtest`. **The sole behavioral difference is *when within a day* a
barrier fills.** This isolates fill-timing as the only moving part.

## 31.2 Data & design

- **Bars:** 1h Binance klines, 4-coin V5 MIX core (BTC, ETH, BNB, SOL), 2021-11-07 → 2026-04-15,
  ~38,904 bars/coin, hourly coverage 0.99997 (one missing hour, the 2023-03-24 Binance maintenance
  outage, tolerated by the engine). Fetched by `scripts/fetch_intraday_1h.py`.
- **No LLM in the loop** (pure LGB signals + price barriers) → the training-cutoff constraint that
  bounds LLM backtests does **not** apply; the full 2021-2026 window is a fair evaluation.
- **Grid (192 cells):** SL ∈ {0, 1, 2, 3, 4, 5, 7, 10}% × TP ∈ {0, 2, 3, 5, 8, 12}% ×
  trailing ∈ {0, 3, 5, 8}%. Early-exit is fixed **off** (§29 settled that EE deteriorates).
- **Multiple-testing / overfit controls:** Deflated Sharpe Ratio over all 192 cells (Bailey &
  López de Prado), a stationary block bootstrap 95% CI, a paired best-vs-3% bootstrap, an
  IS-select / OOS-validate split, and a split-date / per-coin / neighborhood robustness probe.
- **Sanity gate (passed):** the *daily* 3%/EE-off cell reproduces §29's **+3.332** exactly,
  confirming the data pipeline and daily engine are unchanged. (Note the *production* baseline is
  3%/EE=1.5% = **+3.178**; this sweep's apples-to-apples baseline is 3%/EE-off.)

## 31.3 Headline 1 — the look-ahead bias is real

At the 3% cell (EE off, no TP), the close-to-close daily engine reports **SR +3.332**; the
intraday-fill engine reports **SR +3.059**. The daily engine **overstates** the production-style
configuration by **ΔSR −0.273** (`bias.json`). The bias is **concentrated in ETH**
(intrabar−daily ΔSR **−0.92**); BTC, BNB and SOL each shift only ~−0.03 to −0.10. Equal-weighting
dampens ETH's drop to −0.27 at portfolio level — so the close-to-close correction is mainly an ETH
phenomenon, the *same* coin that carries the take-profit benefit in §31.6 (ETH is the active coin in
both directions). *§29's landscape was optimistic by ~0.27 SR at the portfolio stop level, almost
entirely via ETH.* (Figure F-31.2.)

## 31.4 Headline 2 — intrabar evaluation flips §29's "TP hurts"

§29 (close-only) found take-profit strictly harmful — no TP cell reached its top-20. Under intrabar
fills the result **reverses**: the best cell is **SL 4% / TP 8% / no-trail → SR +3.377**, DD 4.1%
(`summary.json`; Figure F-31.1). Trailing never wins (best trail = 0).

**Mechanism:** a take-profit is a *resting limit order* — it fills at the limit price whenever the
intraday high touches it, which the close-only engine cannot see. §29 fired TP only on days that
*closed* ≥8% up (rare) and then paid re-entry costs; the intrabar engine harvests intraday spikes
that revert by the close. So intrabar evaluation reveals take-profit alpha that close-to-close
masked. (Stop fills at the exact stop level are by contrast mildly *optimistic* — market-order
slippage is unmodeled — but the best-vs-3% comparison largely cancels this, since both legs carry a
stop; the differentiator is the realistically-fillable TP limit.) A second-order modelling caveat:
within a single 1h bar the trailing peak ratchets on the favorable extreme before the trailing stop
is measured against the adverse extreme (an implicit favorable-then-adverse intrabar order) — but
trailing never wins any cell (best trail = 0 throughout), so this has no effect on any result.

## 31.4b Headline 3 — intrabar also overturns §29's *stop* conclusion (the robust finding)

§29 (close-only) found SL ∈ {3,5,7,10}% clustered within <0.001 SR — a flat plateau giving no
reason to move off 3%. Under intrabar fills the **pure stop axis** (TP=0, trail=0; `sl_axis.json`)
instead shows a clear **monotonic gradient** — tight stops bleed from intraday wick-outs the
close-only engine never saw:

| SL | 0% | 1% | 2% | 3% | 4% | 5% | 7% | 10% |
|----|----|----|----|----|----|----|----|-----|
| intrabar SR | −10.1 (circuit-broke) | 3.00 | 3.04 | **3.06** | 3.11 | 3.12 | **3.34** | 3.34 |

A stop is essential (SL=0 → −10 SR, 15% DD halt), but **3% is too tight**: 7% beats 3% by **ΔSR
+0.32** (full window, CI [+0.13, +0.53], P(7>3)=0.999) at the same 3.5% drawdown, and the 5–10%
region is a flat top plateau. Crucially this **holds out-of-sample across ALL FOUR split dates**
(P(7>3) = 0.993 / 0.982 / 0.955 / 0.997; ΔSR +0.51 to +0.65) — far more robust than the SL4%/TP8%
take-profit cell, which shipped only 2/4. The looser-stop edge is also *conservative*: intrabar
stops fill at the exact stop level (no slippage), and tight stops trigger far more often, so real
market-order slippage would penalise 3% more than 7% — widening the true gap.

**Per-coin, the effect is again overwhelmingly ETH:** 3%→7% takes ETH from SR +0.89 to +1.82
(**ΔSR +1.05, P=1.000**); BNB +0.10 (P=0.998), BTC +0.04 (P=0.87), SOL +0.06 (P=0.80) — all
non-negative, none hurt. ETH's 3% stop is uniquely wick-prone; for BTC/BNB/SOL the 3–7% range is
effectively stop-insensitive. This is the same ETH-backbone asymmetry seen in §23.11 and §31.3.

## 31.5 In-sample statistics (full window)

- **DSR** (n_trials = 192): value ≈ **1.000** (raw SR 0.213 vs E[max|null] 0.059, SE 0.0216) —
  survives multiple-testing correction. *Caveat:* the 192 cells share positions and are highly
  correlated, so the effective number of independent trials ≪ 192; treating them as independent
  makes the DSR null bar conservatively high, so DSR ≈ 1.0 is if anything an under-statement of
  significance — but it says nothing about out-of-sample stability, which §31.6 tests.
- **Paired best-vs-3% (EE-off)** bootstrap: ΔSR **+0.332**, 95% CI **[+0.073, +0.622]**,
  P(best > 3%) = **0.993** (`stats.json`).

These are *in-sample* on the data used to select the best cell — suggestive, not decisive. The OOS
holdout and robustness probe below are the real arbiters.

## 31.6 Out-of-sample & robustness — the honest verdict

**Single OOS split (IS = …→2025-04-15, OOS = 2025-04-15→2026-04-15, 365 bars):** the IS-selected
SL4%/TP8% cell scores OOS SR **3.81** vs 3% baseline **3.12**, ΔSR **+0.74**, CI [+0.13, +1.42],
p = 0.007 → "SHIP" on this window (`stats_oos.json`).

**But a robustness probe (`robustness.json`, Figure F-31.3) shows this single window oversells it:**

1. **Split-date sensitivity — SHIP holds only 2 of 4 splits.** 2024-10-15 (p=.018) and 2025-04-15
   (p=.007) pass; 2024-07-15 (p=.088) and 2025-01-15 (p=.160) fail (CI includes 0). The IS-selected
   cell is itself **unstable** across splits: SL3/TP5, SL7/no-TP, SL10/TP5, SL4/TP8 respectively.
   There is no single robust optimum — the "best" wanders.
2. **Per-coin attribution — the benefit is almost entirely ETH** (ΔSR **+1.04**). BTC (−0.03) and
   BNB (−0.14) are slightly hurt, SOL +0.17. The portfolio-level TP gain is an ETH story, echoing
   the §23.11 LOO finding that ETH is the prediction backbone and per-coin behaviour is asymmetric.
3. **Neighborhood — the *direction* is robust even though the exact cell is not.** 8 of the top-10
   in-sample cells use TP > 0, and **all 10 beat the 3% cell out-of-sample**. The robust pattern is
   "a wider stop (4–10%) plus a take-profit cap beats the tight 3% no-TP stop," with SL4%/TP8% merely
   the #1 representative of a healthy plateau.
4. Seed-stable (p = .0066 vs .0048 across bootstrap seeds) — rules out a selection/bootstrap bug.

## 31.7 Conclusion & production stance

- **§29's stop conclusion is OVERTURNED — 3% is too tight.** §29's flat 3–10% plateau was an
  artifact of the daily engine, which cannot stop a position out on an intraday wick. Intrabar, a
  looser stop (~5–7%) beats 3% by **ΔSR +0.32**, and this is the **most robust result in §31**:
  it holds out-of-sample across **all four** split dates (P(7>3) ≥ 0.955), versus the take-profit
  cell's 2/4. The actionable production change is to **widen the stop from 3% toward the 5–7%
  region** (the 5–10% plateau is flat, so the exact value is not critical — this is a region, not a
  tuned point, which avoids the single-value SL selection bias §29 worried about).
- **The benefit is concentrated in ETH** (3%→7%: ΔSR +1.05, P=1.000). BTC/BNB/SOL are
  stop-insensitive in 3–7% (all non-negative, none hurt), so widening is **safe portfolio-wide** and
  **most impactful for ETH** — whose tight 3% stop bleeds badly from intraday wick-outs.
- **§29's take-profit conclusion is also overturned, but the TP lever is weaker/fragile:** a TP cap
  adds alpha the close-only engine masked, directionally robust (top-10 ridge all beat 3% OOS) but
  **ETH-only and window-unstable** (SHIP 2/4). Treat an **intraday TP limit for ETH** as future work
  — it needs resting intraday limit orders (the bot currently checks SL/TP only at daily rebalance)
  and a forward A/B.
- **Recommended stance:** (1) widen ETH's stop to ~5–7% (robust, large, OOS-validated); (2) widening
  BTC/BNB/SOL is harmless and marginally positive — optional; (3) never tighten below 3% (worse) or
  remove the stop (SL=0 → −10 SR / DD halt); (4) TP/trailing = future work, ETH-focused, pending
  intraday execution. None of this contradicts the user's original anti-overfit instinct: 3% was a
  reasonable a-priori, the daily sweep gave no reason to move, and only the **bias-corrected**
  intrabar evaluation supplies a principled, OOS-robust reason to loosen it.
- **Bias correction for the thesis record:** the production-style 3% config's *true* (intrabar)
  Sharpe is ≈ **+3.06**, not the §29 daily +3.33 — close-to-close evaluation overstated it by ~0.27
  SR (almost entirely via ETH). All future SL/TP claims should cite intrabar numbers, and add
  `scripts/intraday_sl_axis.py` to the §31.8 reproduce list.

## 31.8 Reproduce

```bash
# 1. fetch 1h klines (idempotent)
python scripts/fetch_intraday_1h.py --start 2021-11-07 --end 2026-04-15
# 2. sweep (192 cells) + daily-vs-intrabar bias
python scripts/intraday_sltp_sweep.py --start 2021-11-07 --end 2026-04-15 --kelly 0.5
# 3. DSR + bootstrap + paired-vs-3% (in-sample)
python scripts/intraday_sltp_stats.py --sweep-dir data/intraday_sltp_sweep --n-iter 5000
# 4. IS-select / OOS-validate
python scripts/intraday_sltp_stats.py --oos --split 2025-04-15 --sweep-dir data/intraday_sltp_sweep
# 5. robustness (split / seed / per-coin / neighborhood)
python scripts/intraday_sltp_robustness.py
# 5b. stop-loss axis: is any SL level robustly better than 3%? (the §31.4b finding)
python scripts/intraday_sl_axis.py
# 6. figures
python scripts/intraday_sltp_report.py --sweep-dir data/intraday_sltp_sweep
```

Engine: `scripts/intraday_fills.py` (`run_coin_backtest_intrabar`, `group_intraday_by_day`).
Outputs: `data/intraday_sltp_sweep/{results.csv,summary.json,bias.json,stats.json,stats_oos.json,robustness.json,figures/}`.

---

**CLAUDE.md pointer to add** (under the §29-adjacent risk/sweep notes, when committing):

```
- **Intraday SL/TP (§31)**: 1h triple-barrier sweep corrects §29's close-to-close fill bias
  (daily overstates the 3% config by ~0.27 SR). Intrabar evaluation flips §29's "TP hurts":
  a TP limit harvests intraday spikes (best cell SL4%/TP8% +3.377) — but the gain is
  ETH-concentrated and window-unstable (SHIP 2/4 splits), so keep the 3% stop; treat an ETH
  intraday TP limit as future work pending intraday-execution infra. Reproduce:
  scripts/fetch_intraday_1h.py → intraday_sltp_sweep.py → intraday_sltp_stats.py [--oos]
  → intraday_sltp_robustness.py → intraday_sltp_report.py. See THESIS_FINDINGS.md §31.
```
