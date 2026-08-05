# Champion System Specification — Low-Volatility Cross-Sectional Long-Short

**System ID:** Phase-O final champion (`predlab_opt.final_champion`, chain seq 2+3)
**Config:** `ewma_20` low-vol quintile long-short, top-200 PIT universe, daily rebalance, `vt15_naive20_b100` vol-target overlay
**Status:** frozen 2026-08-04 (commit chain seq 3, "FINAL FREEZE"); forward one-shot registered, earliest evaluation 2027-01-02
**Headline (full window 2021-01-01 → 2026-07-01, net of costs):** overlaid SR **+1.89**, MaxDD **17.6%**, total return **+409%**; raw book SR +1.93, MaxDD 46.3%

This document describes the complete system: data, universe, signal, portfolio
construction, cost model, risk overlay, evaluation methodology, selection
history, validation evidence, and forward-tracking infrastructure.

---

## 1. Overview

The strategy is a market-neutral cross-sectional bet on the **low-volatility
anomaly** in crypto perpetual futures: within a liquid universe, recently calm
coins outperform recently volatile coins on a risk-adjusted basis. Each day the
system ranks the ~200 most liquid Binance USDT-M perpetuals by a slow-moving
volatility estimate, buys the calmest quintile, shorts the most volatile
quintile, and scales the whole book to a 15% annualized volatility target.

There is **no fitted model anywhere in the pipeline** — no regression, no
gradient boosting, no learned parameters. Every component is a deterministic
transform of past data, which makes the daily simulation loop walk-forward by
construction: every position depends only on information available before the
bar it trades.

Pipeline in one line:

```
daily klines (799 perps) → Parkinson variance → EWMA(span 20), lag 1
  → monthly PIT top-200 universe → quintile long-short, equal weight, gross 2
  → 5 bp taker costs + funding carry
  → vol-target overlay: scale = clip(0.15 / realized 20d book vol, 0, 2),
    forced to 0 while universe breadth < 100 names
```

## 2. Data layer

| Store | Contents | Notes |
|---|---|---|
| `data/xsect/klines/` (799 parquet) | daily OHLCV + quote volume per USDT-M perpetual, 2019-09 → 2026-07 | **survivorship-safe**: includes delisted contracts (e.g. FTT); a symbol enters panels when listed and leaves when delisted |
| `data/xsect/funding/` (799 parquet) | 8-hourly funding rates per symbol | aggregated to daily sums per UTC day (`pp.build_funding_daily`); cached at `data/predlab/opt_funding_daily.parquet` |

Panels (close, quote volume, Parkinson proxy) are built by
`scripts/predlab_t7.build_panels` and truncated at 2026-07-01 for all Phase-O
work; data after 2026-07-02 is physically absent from the panels and reserved
for the sealed forward window (§10).

Sources are Binance public endpoints (klines, funding); no paid data enters the
system.

## 3. Universe construction — monthly, point-in-time

Membership for calendar month *m* is decided entirely from month *m−1*:

1. For every symbol, compute the **median daily quote volume over month m−1**
   (`qv.resample("MS").median()`).
2. Keep the **top 200** symbols by that median.
3. The membership set is fixed for all of month *m*.

Implementation: `tradingagents/predlab/opt.py::monthly_universe` (parity-pinned
against the original `predlab_t7` implementation). Because ranking uses only
prior-month data, universe membership is point-in-time and replicable live —
the same rule runs in the daily paper trader.

Universe breadth is not constant: early 2021 has as few as 78 listed perps with
signal; the median day has the full 200. A trading day requires at least 25
names with valid signal (`MIN_NAMES`), otherwise it is skipped. Breadth also
feeds the overlay guard (§7).

## 4. Signal — slow per-name volatility estimate

**Feature.** The daily Parkinson (1980) range-based variance proxy:

```
park_t = ln(high_t / low_t)^2 / (4 ln 2)
```

Range-based estimators are markedly less noisy than squared close-to-close
returns for the same horizon, and high/low data is available for every listed
perp from listing day.

**Signal.** An exponentially weighted moving average of the Parkinson proxy
with span 20, lagged one day:

```
sig_t = EWMA_span20(park)_{t-1}
```

The one-day shift means the ranking that trades day *t* uses information
through day *t−1* only. Implementation:
`opt.build_signal(park, close, "ewma_20")` — `park.ewm(span=20).mean().shift(1)`.

**Why this estimator.** The Phase-O signal sweep (stage O1, 11 alternatives +
incumbent) showed slow estimators dominate: the prior champion `park_5`
(5-day rolling mean) produces twitchier ranks, more quintile churn, and lower
net SR. `ewma_20` improved full-window net SR from +1.657 to +1.928
(Δ +0.27) with essentially unchanged turnover (0.25/day), and its advantage
is consistent across the design/validation split and all four registered
sub-periods. Interpretation: quintile membership is driven by the *persistent*
component of relative volatility; a slower filter estimates it with less noise
without hurting timeliness, because relative vol ranks move slowly.

## 5. Portfolio construction — quintile long-short

Daily, within the current month's universe members that have a signal value:

1. Sort by `sig_t` ascending.
2. **Long the bottom quintile** (lowest recent vol, ~40 names): weight +1/n_long each.
3. **Short the top quintile** (highest recent vol, ~40 names): weight −1/n_short each.
4. Each leg sums to ±1 → **gross exposure 2.0, net exposure 0** (dollar-neutral).
5. Rebalance every day (cadence 1, no smoothing, no buffer band).

Implementation: `opt.leg_weights` (weighting `"eq"`, `q_frac 0.2`) inside
`opt.run_ls`. Phase-O stage O2/O3 swept the portfolio axes (quantile width,
rank/ivol weighting, holding smoothing, rebalance cadence, buffer bands,
universe depth, ADV floors) and found the incumbent eq-quintile-daily top-200
configuration to be a flat optimum — no variant cleared the adoption gates, so
the simple construction stands.

Timing convention (verified by parity pins and a canary test): the weight
vector formed from signal row *t* (which contains information through *t−1*)
is applied to the day-*t* log return. Turnover is charged on `|w_t − w_{t−1}|`.

## 6. Cost model

Applied inside every reported number (nothing is gross-of-cost unless labeled):

- **Taker fees / slippage:** 5 bp per side per unit turnover
  (`cost_t = 5e-4 × Σ|w_t − w_{t−1}|`). Average underlying turnover is
  0.25/day, so base-book fee drag is ≈ 1.25 bp/day.
- **Funding carry:** daily funding sum per symbol; long positions pay positive
  funding, shorts receive it (`carry_t = −Σ w_i f_i`). The book is typically
  short high-vol alts, which tend to have positive funding — carry is a net
  tailwind on average, and it is real perp economics, not an assumption.
- **Cost stress:** at 2× taker costs the raw book retains SR +1.85 (chain
  seq 1, `sr_net_2x_costs`), so the result is not a cost-model artifact.

## 7. Risk overlay — `vt15_naive20_b100`

The raw book earns a high SR but with crypto-sized drawdowns (46.3% max). A
deterministic vol-target overlay converts vol into a controlled quantity:

```
sigma_hat_t = std(net book returns over last 20 days, through t−1) × sqrt(365)
scale_t     = clip(0.15 / sigma_hat_t, 0, 2.0)
scale_t     = 0  while universe breadth < 100 names        # b100 guard
overlay_net_t = scale_t × net_t − 5e-4 × (scale_t × turnover_t + |Δscale_t| × 2)
```

- **Target 15% ann. vol, cap 2.0×.** Chosen by the pre-registered O4 grid
  (12 configs: targets 10/15/20%, estimators naive20/ewma20/HAR, cap and
  breadth variants); gates were frozen before the run (MaxDD reduction ≥ 25%
  AND net SR ≥ 0.9× raw AND validation-consistency; one adoption maximum).
- **Breadth guard (`b100`).** Scale is forced to zero while fewer than 100
  names have signal. This is a point-in-time quantity (a *t−1*
  signal-availability count). Motivation: stage O3 identified thin-2021
  breadth as the drawdown driver — with < 100 names the quintiles hold ~15
  concentrated positions each and idiosyncratic blowups dominate. The guard
  *adds* SR as well as cutting DD; it keeps the system flat for roughly the
  first months of 2021 until the perp universe matures.
- **Effect:** MaxDD 46.3% → **17.6%** (−62%), SR +1.93 → +1.89 (−2%,
  within the ≥0.9× gate). Average scale 0.32 — the book typically deploys
  about a third of nominal gross, leaning in when the book is calm and cutting
  when realized vol spikes.
- Overlay scale changes are themselves charged 5 bp on `|Δscale| × gross 2`.

The overlay is a deterministic transform of the already-audited book (no new
signal information), so placebo tests are inherited from the raw book and the
overlay carries its own do-no-harm gates instead.

## 8. Evaluation methodology

- **Window:** 2021-01-01 → 2026-07-01 (2,008 traded days; every calendar day
  trades).
- **Walk-forward by construction:** no fitted parameters exist, so there is no
  refit schedule to cross-validate; every daily position uses only lagged
  data. Calendar-year segments are therefore honest out-of-sample folds under
  the frozen configuration.
- **Design/validation discipline:** all Phase-O selection compared candidates
  on a design window **D = 2021-01-01 → 2025-03-31** with confirmation on
  **V = 2025-04-01 → 2026-07-01** (adoption required V-consistency:
  SR_V ≥ 0.5 × SR_D). Four registered sub-periods (2021-22, 2023-24, 2025H1,
  2025H2+2026H1) all had to be positive.
- **Pre-registration:** every stage froze its grid and gates in
  `data/predlab/gates.json` *before* running; every configuration evaluated
  is a ledgered trial; results files refuse overwrite (stop rule). Adoption
  chain recorded in `data/predlab/opt_champion_chain.jsonl`.
- **Multiplicity control:** Deflated Sharpe Ratio over the full ledgered
  selection pool (§9).

## 9. Selection history and validation evidence

### 9.1 Lineage

| Stage | Question | Outcome |
|---|---|---|
| Phase P (S1) | is the low-vol LS real money after costs? | **PASS on locked strategy holdout: net SR +2.20** (gross +3.31), placebos p = .025/.005 — first validated strategy post-rebuild |
| O1 signal sweep (12 configs) | better vol estimator? | **ADOPT `ewma_20`** (+0.27 SR vs `park_5`; slow estimators dominate) |
| O2/O3 portfolio + universe sweeps | better construction? | no adoption — eq-quintile-daily top-200 is a flat optimum; thin-2021 breadth identified as DD driver |
| O4 overlay re-tune (12 configs) | better risk overlay? | **ADOPT `vt15_naive20_b100`** (DD −62%, SR kept, guard adds SR) |
| O5 funding tilt | carry tilt inside legs? | no — real mechanism, premium too thin at 5 bp |
| O6 volume weighting + oracle-dominance test | would within-leg weighting (incl. per-name return models) help? | closed by dominance: all six volume-weighting variants fail their gates, and two never-adoptable *oracle* probes — weighting legs by perfect next-1/7-day return foresight — score net SR **−4.5 / −3.6 outright** (weight tilts break leg balance and multiply turnover). If perfect foresight loses money in this slot, no fitted per-alt model can win it → model build avoided |
| O7 momentum tilt | momentum overlay inside legs? | no |
| O8 final | tercile knob + freeze | tercile rejected (+1.764 < required +1.992); **seq-2 system frozen as final champion** |

Book saturated: four within-leg tilt families all negative at 5 bp costs.

### 9.2 Evidence on the frozen champion

| Check | Result |
|---|---|
| Placebo, circular time-shift of signal (200 draws) | p = 0.005 (real SR exceeds every draw; null max +1.68 vs real +1.93) |
| Placebo, cross-sectional shuffle (200 draws) | p = 0.005 (null max −1.15) |
| Deflated Sharpe Ratio, strictest selectable pool (n = 86 ledgered trials) | **0.913 PASS** (0.917 at n = 89; 0.096 only when never-adoptable oracle diagnostics are included — disclosed, gate basis is the selectable pool) |
| Alignment canary (unshifted signal) | SR flips +1.93 → −1.91: alignment drives the result; mechanical no-look-ahead pinned in `tests/test_opt.py` |
| Sub-periods | 4/4 positive mean net return |
| Single-name concentration | max name share 1.2% of absolute PnL (FTM) — no single-name artifact |
| Cost stress 2× | raw SR +1.85 |
| Coverage forensics | 2,008/2,008 calendar days traded; names/day min 78, median 200 |
| Engine parity | Phase-O engine reproduces Phase-P `pp.run_s1` exactly with default config (pinned in tests) |

### 9.3 Historical performance (walk-forward, net, overlaid book)

Reproduced by `scripts/predlab_champion_backtest.py` (report-only rerun of the
frozen configs; matches the chain to the third decimal):

| Year | Old champion (park_5 + vt10) | **New champion (ewma_20 + vt15_b100)** |
|---|---|---|
| 2021 | SR +0.23, +1.9%, DD 9.5% | SR +1.09, +15.0%, DD 12.6% |
| 2022 | SR +2.66, +35.9%, DD 5.0% | SR +2.51, +55.3%, DD 7.9% |
| 2023 | SR +0.75, +8.1%, DD 9.9% | SR +1.03, +17.6%, DD 16.2% |
| 2024 | SR +0.84, +8.7%, DD 8.8% | SR +1.20, +19.6%, DD 10.5% |
| 2025 | SR +2.04, +23.9%, DD 5.8% | SR +2.80, +56.4%, DD 6.7% |
| 2026 H1 | SR +3.52, +20.7%, DD 3.8% | SR +3.29, +29.4%, DD 6.4% |
| **Full** | **SR +1.53, +143%, DD 9.9%** | **SR +1.89, +409%, DD 17.6%** |

The new champion wins 5 of 6 calendar-year folds and every fold is positive.
It runs a hotter overlay target (15% vs 10%), hence roughly double the return
and double the drawdown of the old book; the D/V split reads SR 1.71 / 2.51.
Artifacts: `data/predlab/champion_backtest.json`,
`champion_backtest_equity.png`, `champion_backtest_yearly.png`.

## 10. Forward tracking

Two independent forward records exist; they are deliberately kept separate:

1. **Sealed forward one-shot (the untainted claim).** Panels end 2026-07-02;
   data beyond that date never entered any selection. Registered criteria
   (gates `predlab_opt.final_champion`): evaluate window F = 2026-07-02 → open
   no earlier than **2027-01-02**; pass requires SR_F ≥ 0.946 (half the
   full-window SR), same sign, placebo p < 0.10. One evaluation, no retries.
2. **Daily paper journal.** `scripts/predlab_s1_paper.py` (cron, ~00:10 UTC)
   rebuilds the live book from Binance public data and journals weights,
   membership hash, realized close-to-close return of the previous book,
   turnover, and overlay scale — no orders are placed. Two journals:
   `journal.jsonl` (old Phase-P config, frozen for the separate pp2 vt10
   confirmation) and `journal_champion.jsonl` (this system). Champion journal
   starts 2026-08-03; rows for 2026-07-31 → 2026-08-02 are intentionally
   absent (the scheduler was not active; the gap is disclosed rather than
   backfilled, because a forward journal is a point-in-time record).

## 11. Assumptions and limitations

- **Execution model.** Fills at daily close, 5 bp per side flat. No market
  impact model; the 2× cost stress (SR +1.85) bounds moderate slippage but
  not large size. Turnover is low (0.25/day on gross 2), which helps.
- **Capacity.** Long leg holds liquid majors; the short leg holds the most
  volatile members of the top-200 — liquid enough for perps at research size,
  but shorting ~40 volatile alts at scale concentrates borrow-free but
  funding-sensitive exposure. Funding is charged from realized data, but
  realized funding at larger size would differ.
- **Non-virgin validation window.** The D+V window (through 2026-07) was
  visited repeatedly across Phase P and Phase O; DSR and pre-registered gates
  control selection bias, but the only fully untainted evidence is the sealed
  forward one-shot (§10.1) and the paper journal.
- **Regime dependence.** The overlay stands aside below 100-name breadth, so
  the system assumes a mature perp universe; a structural break in the
  low-vol anomaly (e.g. persistent junk-coin melt-ups, as in parts of 2021
  for the raw book) is the main economic risk. 2021 remains the weakest year.
- **Single venue.** Binance USDT-M only; venue concentration and USDT
  denomination risk are unhedged.

## 12. Reproduction

```bash
cd TradingAgents-predlab

# full champion-vs-incumbent walk-forward comparison (report-only)
uv run python scripts/predlab_champion_backtest.py

# original pre-registered stage runs (refuse to overwrite existing results)
uv run python scripts/predlab_opt_o1.py run     # signal sweep
uv run python scripts/predlab_opt_o4.py run     # overlay grid
uv run python scripts/predlab_opt_o8.py run     # final freeze

# daily paper journal (also runs from cron)
uv run python scripts/predlab_s1_paper.py
```

## 13. File map

| Path | Role |
|---|---|
| `tradingagents/predlab/opt.py` | engine: signal builder, PIT universe, quintile weights, LS backtest, D/V metrics |
| `tradingagents/predlab/pp.py` | Phase-P engine, SR/DD/DSR metrics, funding aggregation, placebo machinery |
| `scripts/predlab_opt_o1.py … o8.py` | pre-registered Phase-O stages (grids frozen in `gates.json` before each run) |
| `scripts/predlab_champion_backtest.py` | champion-vs-incumbent historical comparison + plots |
| `scripts/predlab_s1_paper.py` | daily dual-journal paper trader |
| `data/predlab/gates.json` | frozen grids, gates, final-champion registration |
| `data/predlab/opt_champion_chain.jsonl` | adoption chain (seq 1 signal, seq 2 overlay, seq 3 freeze) |
| `data/predlab/cards/opt_o1..o8_final` | per-stage result cards |
| `data/predlab/champion_backtest.json` + PNGs | historical results in this document |
| `THESIS_FINDINGS.md` §54–59 | thesis record of the Prediction Lab program |
