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

The SL=0 cell is **not** "no stop": `stop_loss=0.0` is a degenerate *always-firing* stop (any
adverse excursion ≥ 0 triggers, exiting at entry equity), which forgoes all gains and bleeds costs
until the 15% circuit breaker halts — the −0.150 total return is exactly the breaker. The true
no-stop end of this axis is SL=10% (0 fires over the whole window), and it is near-best (3.34).
On this axis **3% is too tight**: 7% beats 3% by **ΔSR +0.32** (full window, CI [+0.13, +0.53],
P(7>3)=0.999) at the same 3.5% drawdown, and the 5–10% region is a flat top plateau. This holds
out-of-sample with P(7>3) ≥ 0.955 on all four split dates (ΔSR +0.51 to +0.65), individually
significant on three (the 2025-01-15 split's CI [−0.08, +1.17] includes 0) — still far more robust
than the SL4%/TP8% take-profit cell, which shipped only 2/4. The looser-stop edge is also *conservative*: intrabar
stops fill at the exact stop level (no slippage), and tight stops trigger far more often, so real
market-order slippage would penalise 3% more than 7% — widening the true gap.

**Per-coin, the effect is again overwhelmingly ETH:** 3%→7% takes ETH from SR +0.89 to +1.82
(**ΔSR +1.05, P=1.000**); BNB +0.10 (P=0.998), BTC +0.04 (P=0.87), SOL +0.06 (P=0.80) — all
non-negative, none hurt. ETH's 3% stop is uniquely wick-prone; for BTC/BNB/SOL the 3–7% range is
effectively stop-insensitive. This is the same ETH-backbone asymmetry seen in §23.11 and §31.3.

> **Units caveat — §31.4b is in EQUITY-stop terms and does NOT translate to a live config change.**
> See §31.4c: the live bot uses a PRICE stop, which is a different variable, and is already near
> the optimum. Do not read "loosen to ~7%" as a live `STOP_LOSS_PCT` change.

## 31.4c Reconciliation to the LIVE stop — NO production change warranted

§31.4b fires on **equity-since-entry**. The live bot places a Binance `STOP_MARKET` at
`entry_price*(1 − STOP_LOSS_PCT)` — a **PRICE** stop ([live/runner.py:534](../tradingagents/execution/live/runner.py)).
These are different variables: `equity_stop ≈ price_stop × leverage`. Re-running the SL axis with the
engine's `stop_mode="price"` (`scripts/intraday_sl_axis_price.py` → `sl_axis_price.json`) gives a
**different landscape in the live units**:

| price-stop | 1.5% | 2% | **3% (live)** | 4% | 5% | 7% | 10% |
|------------|------|----|---------------|----|----|----|-----|
| portfolio SR | 2.83 | 3.02 | **3.178** | 3.214 | 3.179 | 3.130 | 3.062 |

The price-stop curve **peaks at ~3–4% and declines for looser stops** — the *opposite* shape of the
equity axis. The nominal best (4%) beats the live 3% by only **+0.036 SR** full-window (CI
[−0.089, +0.170], P=0.70, not significant) and is *worse* than 3% in **all four** OOS splits,
significantly so in three (ΔSR −0.12 to −0.21; P(4>3) = 0.001 / 0.003 / 0.017; the fourth, 0.060,
has a CI including 0). **0/4 splits ship.** Per-coin, no coin robustly benefits; ETH is marginally
*hurt* by a looser price stop.

**Why the two axes disagree — measured, not assumed.** An earlier draft reconciled them as "a 3%
price stop at the strategy's realized ~2× leverage *is* a ~6–7% equity stop". That is **wrong**:
the sweep's realized gross exposure averages **~0.21×** (per-coin mean |pos| 0.19–0.27, max-ever
1.43×, zero days ≥ 2×), and an engine-exact replay counts the 7% *equity* stop firing **once** in
4.5 yr × 4 coins (10%: never) versus **1,125 fires** for the 3% *price* stop (4%: 857). The two
stops are not equivalent in any units. At sub-1× leverage the equity axis tested *near-inactive*
stops — its "optimum" 7% is effectively a disarmed stop — while the price axis tests a
frequently-binding constraint. The equity-axis gradient therefore mainly says "binding stops hurt
on that axis"; the **price axis is the only deployable experiment**, and it independently favors
the existing 3–4% region.

*Caveat (model-vs-live parity):* this axis was swept with early-exit OFF, while live also runs
`EARLY_EXIT_LOSS=0.015`. The EE-off price-3% SR (3.1777) matching the EE-on production anchor
(3.178) is numeric coincidence, not a parity check. EE fires before the stop on slow bleeds, so the
interaction should make the price stop *less* binding rather than move the optimum, but a live
config with EE off was not what this table models.

**VERDICT — keep live `STOP_LOSS_PCT = 3%`; no deploy.** Changing it (looser or tighter) does not
robustly help and degrades OOS. Note that naively shipping §31.4b's "7%" as `STOP_LOSS_PCT=0.07`
(a 7% *price* stop) would score **+3.13 < the current +3.18** and worse OOS — an active regression.
Re-deriving in the live variable before deploying prevented degrading a live bot off a backtest
result expressed in the wrong units. (General lesson: a stop optimum is only meaningful in the
units the executor actually uses.)

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

- **§29's stop conclusion is overturned IN EQUITY-STOP UNITS — but this does NOT mean change the
  live stop.** Intrabar, a looser *equity* stop (~5–7%) beats a 3% *equity* stop by **ΔSR +0.32**,
  OOS P(7>3) ≥ 0.955 on all four splits (three individually significant). BUT the equity result is
  not deployable: at the realized ~0.21× leverage the equity stops barely fire (7%: once over
  4.5 yr × 4 coins), so the equity "optimum" is effectively a disarmed stop — not an equivalent of
  the live price stop. The live variable is the *price* stop, and §31.4c shows it is already
  near-optimal at 3% on its own evidence. **So there is no live config change to make.** The
  takeaway is methodological: §29's flat daily plateau was a close-to-close artifact, and stop
  optima must be read in the executor's units — and validated by firing behaviour, not unit
  conversion.
- **The benefit is concentrated in ETH** (3%→7%: ΔSR +1.05, P=1.000). BTC/BNB/SOL are
  stop-insensitive in 3–7% (all non-negative, none hurt), so widening is **safe portfolio-wide** and
  **most impactful for ETH** — whose tight 3% stop bleeds badly from intraday wick-outs.
- **§29's take-profit conclusion is also overturned, but the TP lever is weaker/fragile:** a TP cap
  adds alpha the close-only engine masked, directionally robust (top-10 ridge all beat 3% OOS) but
  **ETH-only and window-unstable** (SHIP 2/4). Treat an **intraday TP limit for ETH** as future work
  — it needs resting intraday limit orders (the bot currently checks SL/TP only at daily rebalance)
  and a forward A/B.
- **Recommended LIVE stance (after the §31.4c price-units check): KEEP `STOP_LOSS_PCT = 3%` — no
  deploy.** The price-stop axis peaks at ~3–4% and the nominal 4% best fails 0/4 OOS splits (worse
  than 3%), so the live 3% price stop is already at/near the optimum. Never set it to 0 — live,
  `STOP_LOSS_PCT=0` arms a STOP_MARKET at the execution price itself, triggering immediately (and
  in the backtest SL=0 is a degenerate always-firing stop, not "no stop"). The §31.4b equity-axis
  "loosen to 5–7%" is *not* a live instruction — that axis's stops were effectively inactive at the
  realized ~0.21× leverage. TP/trailing remain future work
  (ETH-focused, fragile, and needing intraday limit-order execution). This vindicates the original
  anti-overfit instinct: 3% was a good a-priori and stays.
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
# 5b. stop-loss axis (EQUITY units): is any SL level better than 3%? (§31.4b)
python scripts/intraday_sl_axis.py
# 5c. stop-loss axis (PRICE units = live STOP_LOSS_PCT): deployable answer (§31.4c)
python scripts/intraday_sl_axis_price.py
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
