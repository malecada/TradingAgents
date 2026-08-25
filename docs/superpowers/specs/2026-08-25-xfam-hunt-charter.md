# xfam — five untested signal families (deep hunt), umbrella charter

Registered 2026-08-25 BEFORE any results. User directive: thorough autonomous
hunt across the previously-unattacked "testable now" families. Program context:
zero validated strategies program-wide ([[state-aug24-research-closed]] +
rviv_p0 FAIL); these are the last on-disk-testable untried families.

## Families and cells (frozen)

| Key | Family | Data | P0 kill-test |
|---|---|---|---|
| xfam_cal | Calendar effects | daily 799-sym + 1h 333-sym | 11 pre-named bucket tests, BH-FDR |
| xfam_amx | Amihud illiquidity XS premium | daily 799-sym | monthly IC t-test |
| xfam_llg | BTC/ETH→alt lead-lag | daily + 1h | predictive regression on alt index |
| xfam_pos | Positioning extremes (Coinglass L/S) | 8-sym daily | pooled signal-weighted return test |
| xfam_prx | Pairs / cointegration MR | daily top-50 | OOS cointegration persistence |

Execution order: cal → amx → llg → pos → prx (cheap→expensive). Each family's
P0 gate is one-shot: FAIL ⇒ family closed, no re-tuning, no window changes.

## Shared protocol

- **Windows**: dev 2021-01-01 → 2025-03-31. All P0/P1 evaluations use data
  ≤ 2025-03-31 only; last signal date chosen so every target/holding completes
  by then. Holdout 2025-04-01 → 2026-07-01, **CONTAMINATION-DISCLOSED**: the
  window was observed by prior programs' evaluations (S1 strategy spend, P5
  forecast spends, corrected recomputes) but is virgin for every xfam signal;
  any holdout claim carries this disclosure. F window 2026-07-02+ untouched.
- **Returns**: simple `close.pct_change()`, never log, for all position PnL
  (house rule). Convention-swap kill-test mandatory on every P1.
- **Costs**: taker 5bp per side × turnover + realized funding carry (longs pay
  positive funding) for held perp positions. Cost-stress 2× reported.
- **Universe** (unless family overrides): monthly PIT top-200 by prior-month
  median quote volume — existing parity-pinned builder
  (`tradingagents.predlab.opt.monthly_universe`).
- **Engine**: `opt.run_ls` (corrected, tested) where breadth ≥ MIN_NAMES=25;
  bespoke thin-panel/pair engines get their own unit tests before first use.
- **Ledger**: every evaluated config = one row in `trial_ledger.jsonl`,
  experiment `predlab_xfam_<fam>`.
- **Multiplicity**: within-family as specified per family. Any champion claim
  additionally needs DSR > 0.5 with n_trials = all xfam ledger rows + 16 prior
  strategy trials + predlab_opt/opt2 ledgered configs (house denominator).
- **P1 promotion gates (all families identical)**: dev net SR ≥ 1.0 AND
  circular-shift placebo (≥200 draws) p < 0.10 AND exposure-pattern placebo
  reported AND cost-stress 2× keeps sign AND max single-name |PnL| share ≤ 50%
  AND convention-swap no verdict flip. All pass ⇒ family becomes holdout
  candidate.
- **Holdout spend rule (pre-registered, autonomous)**: one-shot per family
  candidate on 2025-04-01→2026-07-01 with the contamination disclosure.
  PASS = net SR ≥ 0.5 × dev net SR AND same sign AND holdout circular-shift
  placebo p < 0.10. The spend script refuses to run twice per family.
- **Descriptives**: per-family per-year effect tables written regardless of
  verdict (thesis content).

## xfam_cal — calendar effects (11 pre-named tests, no others)

Cells: BTC, ETH, XSM = equal-weight daily mean return of PIT top-100 universe.

- **H1 weekend**: mean(Sat+Sun) − mean(Mon–Fri), daily simple returns.
  Cells: BTC, ETH, XSM. (3 tests)
- **H2 turn-of-month**: mean(last 2 + first 2 calendar days of month) − rest.
  Cells: BTC, ETH, XSM. (3 tests)
- **H3 Deribit monthly expiry**: expiry = last Friday of month. Mean of the 4
  trading days up to and including expiry Friday minus mean of the 4 days
  after. Cells: BTC, ETH, XSM. (3 tests)
- **H4 funding-window hours** (1h store): mean return of UTC hours {7, 15, 23}
  (hour bar preceding the 08/16/00 funding settlement) minus all other hours.
  Cells: BTC, ETH. (2 tests)

Inference: HAC t-stat (Newey-West, lag 5 daily / lag 24 hourly), two-sided.
**P0 gate**: any test surviving BH-FDR q < 0.10 across the 11. Survivors go
to P1 timing strategies (one config each, direction from dev sign, net 5bp per
side per trade). Honest pre-statement: H4 trades ≥3×/day ⇒ ~30bp/day cost
floor ⇒ needs >10bp mean effect per traded hour; H1-H3 trade weekly/monthly.

## xfam_amx — Amihud illiquidity premium

- Signal: `amihud_i(t) = mean_21d(|r_i|/qv_i)`, `shift(1)`. Universe top-200
  PIT + ADV floor: prior-month median qv ≥ $1M.
- **P0**: monthly Spearman IC — signal on the first trading day of each month
  vs the next-21-traded-day return, within-universe. Mean IC, NW-lag-1 t-stat
  on the monthly IC series. Gate: p < 0.05 two-sided AND same IC sign in ≥3 of
  4 calendar years 2021-2024.
- **P1**: `run_ls`, direction = P0 sign (long high-Amihud if IC+),
  q_frac 0.2, eq weight, cadence 21, smooth 1, buffer 0. ONE config.

## xfam_llg — BTC/ETH → alt lead-lag

- Follower index: equal-weight daily simple return of PIT top-200 universe
  excluding BTCUSDT and ETHUSDT.
- **P0 cells (4)**: (a) daily BTC ret t → follower index ret t+1; (b) daily
  ETH ret t → follower index t+1; (c) hourly BTC ret h → hourly follower index
  (top-100 of the 1h store by prior-month median qv, ex BTC/ETH) h+1;
  (d) hourly ETH → follower h+1. OLS slope, NW lag 5 (daily) / 24 (hourly).
  Gate: p < 0.01 two-sided AND same slope sign in ≥3 of 4 years, any cell;
  BH-FDR q < 0.10 across the 4 cells.
- **P1**: TS follow/fade on the follower basket: w(t) = sign(slope) ×
  sign(leader ret t−1), ±1 gross on equal-weight basket, daily (or hourly
  hold-1-bar for hourly cells). Costs 5bp/side on turnover. ONE config per
  surviving cell, no threshold tuning.

## xfam_pos — positioning extremes (8-sym Coinglass panel)

- Symbols: exactly the 8 with `*_cg_ls_*` parquets on disk (enumerated in the
  run script header at first run; frozen there).
- Signals (both `shift(1)`, z-scored on rolling 90d, min 60 obs):
  - S1 retail-contrarian: z(ls_global ratio); hypothesis: crowded retail long
    ⇒ NEGATIVE next-day return (one-sided).
  - S2 smart-follow: z(ls_top_position ratio); hypothesis: POSITIVE (one-sided).
- **P0**: daily portfolio r_sig(t+1) = mean_i( sgn_hyp × z_i(t) × r_i(t+1) )
  (signal-weighted return, hypothesis-signed); test mean > 0, NW lag 5,
  one-sided p < 0.05 AND positive in ≥3 of 4 years. BH-FDR q < 0.10 across 2.
- **P1**: thin-panel LS (bespoke, MIN_NAMES=4): long 2 best / short 2 worst
  by surviving signal, equal weight, daily, 5bp + funding. ONE config per
  surviving signal. Bespoke engine unit-tested before first use.

## xfam_prx — pairs / cointegration MR

- Universe: top-50 by prior-90d median qv, monthly PIT.
- Formation (month M, data through last day of M−1): Engle-Granger (OLS hedge
  ratio β on 90d log closes, ADF on residual). Keep ADF p < 0.05 AND spread
  AR(1) half-life ∈ [2, 20] trading days; rank by ADF p ascending, cap 20
  pairs.
- Trading (month M): spread s = log P_a − β log P_b; z = (s − mean_90d)/std_90d
  with all rolling stats `shift(1)`. Enter |z| ≥ 2 (short rich / long cheap,
  dollar-neutral via β), exit |z| ≤ 0.5, stop |z| ≥ 4 or 20 trading days.
  Capital 1/20 per pair. Costs 5bp/side per leg trade + funding on held legs.
- **P0 persistence kill-test**: for each formation month, fraction of selected
  pairs whose NEXT-month spread (formation β frozen) has ADF p < 0.10 vs the
  same fraction for 20 random same-universe pairs/month. Gate: selected rate ≥
  1.5 × random rate AND paired binomial/Wilcoxon p < 0.05 across months. If
  cointegration does not persist OOS, family dies before any backtest.
- Sub-cell ETHBTC: single pair (log ETH − β log BTC, 90d), same z-rules; its
  P0 = half-life ∈ [2, 40]d in ≥3 of 4 dev years.
- **P1**: ONE grid point exactly as above (no parameter sweep) + ETHBTC = 2
  configs total.

## Stop rules

- Per-family P0 FAIL ⇒ family CLOSED this program; recorded in gates; no
  revival without a new registered cycle with a new mechanism argument.
- All five fail ⇒ hunt closes negative; thesis records the five-family
  falsification sweep.
- Any survivor of P1 gates ⇒ pre-registered holdout one-shot (above). Holdout
  PASS ⇒ champion-candidate; report to user with full forensics — live/paper
  deployment decisions remain the user's (not autonomous).

## Mechanics

Branch research/prediction-lab. Shared lib `scripts/predlab_xfam_lib.py`
(+ `tests/predlab/test_xfam_lib.py`), per-family scripts
`scripts/predlab_xfam_<fam>.py`, outputs `data/predlab/xfam/`, gates key
`predlab_xfam` (this registration), ledger rows per config. 1h store read
read-only from `TradingAgents/data/xsect/klines_1h`; Coinglass parquets from
`TradingAgents/data/derivatives_raw` (both outside this worktree, read-only).
