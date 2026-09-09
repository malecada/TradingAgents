# Liquidation-Cascade Mean-Reversion (8 majors, time-series fade) — Design

Date: 2026-07-28
Status: approved (autonomous design session 2026-07-28, house pre-registration methodology)
Registration: gates.json entry `liq_mr_t1` (written BEFORE any experiment run)

## Background and provenance

Executes lead #6 of the post-§44 go-forward menu (SUPERVISOR_REPORT_2026-07-28 §6),
after lead #1 dropped pre-registration (Guo = minute-frequency HFT), lead #2 wide
trend closed dev-negative (§45), lead #3 CS conditional carry closed dev-negative
(§46). Leads #4 (intraday) disk-blocked, #5 (RV overlay) needs a winning base
strategy first, #7 (value factor) data-blocked.

Hypothesis: liquidation cascades are forced, price-insensitive flow. A spike in
long liquidations means longs were force-sold into a falling market → temporary
undershoot → fade by buying; symmetrically a short-liquidation spike → temporary
overshoot → fade by shorting. Exploratory: **no external study**; the closest
internal anchor is BIS WP 1087's carry→sell-liquidation asymmetry (monthly,
calendar futures — motivation only, different hypothesis). This is the only lead
exploiting the Coinglass liquidation history (retail-rare data moat, 10-exchange
aggregate from 2020-12).

Prior-art constraints honored: §43 vol-selection mechanism (no vol-based sizing),
§45 dual-family placebo (item 7 of house methodology), §41 rf convention mandate
(decided upfront, below), §44 power lesson (event-count diagnostic recorded).

## Universe (fixed, non-PIT — documented limitation)

The 8 coins with full Coinglass derivatives history in `data/derivatives/`:
BTC, ETH, BNB, SOL, ADA, DOGE, XRP, TRX (klines symbols BTCUSDT … TRXUSDT from
the survivorship-safe xsect store). **Limitation recorded at registration:** this
universe is the set fetched under the Coinglass Hobbyist plan in 2026-05 — i.e.
selected as majors *ex post*, not by a PIT rule. All 8 listed on Binance USDT-M
before 2021 and never delisted, so no delisting holes exist inside the windows;
the residual bias is that today's majors survived — a time-series fade result on
them cannot claim breadth robustness. Accepted for an exploratory lead; a pass
would mandate a PIT-universe re-test before any deploy claim.

## Signal

Per coin i, UTC day t (Coinglass daily rows are stamped at UTC day open; the
day-t aggregate is complete at close t — convention verified empirically during
build via the contemporaneity probe, see Testing):

```
x_long_i(t)  = liq_long_usd_i(t)  / oi_close_i(t)
x_short_i(t) = liq_short_usd_i(t) / oi_close_i(t)
z_long_i(t)  = (x_long_i(t)  − mean_90d(x_long_i))  / std_90d(x_long_i)
z_short_i(t) = (x_short_i(t) − mean_90d(x_short_i)) / std_90d(x_short_i)
```

- Rolling window 90 days, min_periods 60, trailing and inclusive of day t
  (all inputs known at close t → point-in-time safe). ddof=1.
- Normalization by same-day aggregated OI close makes the cascade measure a
  fraction of open positioning, comparable across coins and across the 5-year
  growth in market size. oi_close = 0 or missing → x = NaN → no signal that day.
- Fixed, not gridded: 90d window, OI normalization, z-score form.

**Events and positions (symmetric fade, both directions always on):**

- z_long_i(t) ≥ thr → LONG coin i for the next H bars (t+1 … t+H).
- z_short_i(t) ≥ thr → SHORT coin i for the next H bars.
- A new event while a same-direction hold is active resets the hold timer
  (position extends). Opposite events overlap → positions net (sum of the two
  direction states, ∈ {−1, 0, +1} per coin).
- Per-coin unit weight = 1/8 (equal notional, N=8 fixed): w_i(t) ∈ {−1/8, 0, +1/8}.
  Gross ≤ 1.0 by construction. **No vol targeting, no vol scaling** (clean
  hypothesis; avoids re-introducing the §43 vol-selection mechanism).

Rejected alternatives: cross-sectional rank of liq intensity (only 8 names —
too thin for sorts, and CS momentum family already closed 0/12 §43); liq_asym_24h
composite (mixes both directions into one number, loses the direction-specific
fade semantics); vol-targeted sizing (§43 mechanism risk); long-fade-only
(halves the hypothesis for no prior reason; direction split is a diagnostic).

## P&L, execution, costs

Decision at close t → weights apply to bar t+1 (causal next-bar accrual,
corrected-harness convention). Daily portfolio return:

```
r_p(t+1) = Σ_i w_i(t) · r_i(t+1)            price leg, klines-store simple returns
         − 0.0010 · Σ_i |Δw_i|              10 bps per side on turnover
         − rf_daily                          3M T-bill on full capital
```

- rf convention (§41 mandate, decided upfront): flat rf_annual = 4.5%,
  rf_daily = 1.045^(1/365) − 1 ≈ 1.2060e-4, deducted every day on full capital —
  identical to carry_xs_t1. Harshest honest convention: the portfolio is flat
  most days and idle Binance USDT margin earns nothing, so a pass means the
  episodic edge clears T-bills on the whole capital base. A margin-efficiency
  diagnostic (SR without rf drag, % days active) is recorded either way — as
  diagnostic, NOT a gate.
- Funding accrual on held perp positions is deliberately EXCLUDED from t1 P&L:
  holds are ≤ 5 days and episodic, funding sign is ambiguous across events, and
  including it would entangle this test with the closed carry family. Recorded
  as a known simplification; a holdout run would add realized funding accrual
  as a robustness line (not a gate).
- Missing kline return for a held coin: contributes 0 that day (store
  convention, matches trend_wide/carry_xs).

## Grid (frozen before first run — 6 configs)

- thr ∈ {1.5, 2.5} (z-score event threshold)
- H ∈ {1, 3, 5} (hold bars after event)

Nothing else varies (90d window, 1/8 weight, both directions, N=8 all fixed).
No second pass, no added axes after seeing results (house methodology;
violations void the run).

## Windows

- Dev: 2021-01-01 → 2025-03-31 (liq history nonzero from 2020-12-23; the 90d/60
  warmup means signals go live ~2021-03; weights 0 until then — inside-window
  warmup, identical across configs, so grid-level comparability holds).
- Holdout: 2025-04-01 → 2026-07-01 — sealed, one-shot, spent only if dev passes.
  Derivatives store currently ends 2026-05-21/26; a holdout run would first
  extend the store via `scripts/fetch_coinglass_history.py` tail-append
  (idempotent, house cache rule).

## Gates (`liq_mr_t1`, registered in data/rebuild/gates.json before any run)

dev_select (winning config must clear ALL):

- net SR ≥ 1.0 (net of turnover costs and rf deduction; √252, ddof=1;
  zero-variance SR := 0)
- placebo p ≤ 0.05 under BOTH families (gate on the WORSE p), 500 draws each,
  p = (1 + #{placebo SR ≥ real SR}) / (N + 1), costs and rf re-applied to
  shifted weights:
  - (a) per-coin independent circular time-shifts of the final daily weight
    matrix;
  - (b) shared-offset circular shift (one offset, all columns).
- DSR ≥ 0.9 over the 6-config grid with ledger-cumulative n_trials
  (`log_trial()` before reading each result; n_trials = unique config_hash
  count from the ledger, never from memory)
- tiebreak: highest DSR, then lowest placebo p

No relative benchmark gate: the portfolio is flat-by-default and episodic; the
natural benchmark is cash, embedded via the rf deduction.

holdout_deploy (one-shot, only if dev_select passes):

- net SR ≥ 0.5, placebo p ≤ 0.05 (worse-of families)
- fresh halt-latch semantics per house rule; SR := 0 on zero variance
- funding-accrual robustness line reported alongside (not a gate)

Any dev failure → honest negative recorded in THESIS §47; holdout stays sealed.

## Diagnostics (recorded either way, NOT gates)

1. Event counts per config (per coin and total; §44 power lesson — a negative on
   < ~30 total events is "underpowered", not "signal absent", and is labeled so).
2. Direction decomposition: long-fade vs short-fade contribution to net SR.
3. Vol-selection check: correlation of event days with 30d realized vol regime.
4. % days with any active position; margin-efficiency (SR gross of rf).
5. Continuation-vs-reversal profile: mean next-1/3/5-day return after events
   (the signed raw effect the strategy monetizes).

## Build approach

New module `tradingagents/xsect/liq_mr.py` on branch `feature/xs-momentum`
(same branch — shares the xsect infra; separate commits). Reuse: klines store +
`build_matrices` returns (trend.py), `run_daily_portfolio` cost path pattern
(extended with rf like carry_xs's `run_ls_portfolio`), dual-family placebo
(`circular_shift_weights`, `shared_shift_weights`, `placebo_srs` pattern with
rf re-applied), `paired_bootstrap`/DSR helpers, rebuild ledger + holdout guard.
New code is only: derivatives loader (8 parquets → liq/OI matrices), z-score
event signal, event→hold weight builder, thin runner script.

Rejected: extending carry_xs.py (different signal family, no funding leg here);
new standalone script without module/tests (violates TDD house discipline).

## Testing (TDD, house discipline)

- Signal: z-score windowing causal (day-t signal uses only ≤ t), min_periods
  respected, NaN propagation on missing OI/liq.
- Weight builder: event trigger at exact threshold, H-bar hold, same-direction
  timer reset, opposite-event netting, 1/8 unit weight, weights start t+1 (the
  decision bar never holds its own event's return).
- Engine: causal t+1 accrual, turnover cost on |ΔW|, rf deduction wiring
  (fixture-pinned arithmetic).
- Stamp-convention probe (forensic, pre-run): liquidation spikes must be
  contemporaneous with same-day large |returns| and NOT better-aligned with
  next-day |returns| — validates bar-open stamping of the Coinglass rows
  before any backtest is trusted.
- Placebo kill-test: planted reversal signal survives both families; shuffled
  signal does not.
- Forensic pass on any zero/negative result per house discipline (probes,
  mutation kill-tests, honest denominators).

## Deliverables

1. `tradingagents/xsect/liq_mr.py` + tests
2. `liq_mr_t1` gates.json entry + trial-ledger rows
3. Dev-run results + forensic report; THESIS §47 section either way
