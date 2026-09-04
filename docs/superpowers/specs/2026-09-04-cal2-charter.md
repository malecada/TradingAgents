# cal2 — Session and macro-day effects at 1 h (registered 2026-09-04)

Status: **REGISTERED pre-result.** Gates key `predlab_cal2` in
`data/predlab/gates.json` written in the same commit as this file, before any
session mean is computed. Source: `master_thesis/LEADS_SCOPE_2026-09-02.md`
Lead 11; parent §72 xfam_cal (11 calendar tests, 0/11). Protocol: xfam P0
(HAC lag 24, BH-FDR q < 0.10). Decisions under the afk autonomy grant: 12
tests as listed; the hourly-bar approximations of the clock windows below are
declared now.

## Tests (12, pre-named; hourly simple returns of the 1 h store, dev 2021-01-01 → 2025-03-31)

Windows are approximated by bar open hours (UTC), declared:
- **H1 US session** 13:30–20:00 ⇒ bars opening 13–19 (7 bars) vs all other
  bars — cells BTC, ETH, XSM (equal-weight mean of the monthly top-100 PIT
  universe with 1 h data) — 3 tests.
- **H2 Asia session** 00:00–08:00 ⇒ bars 0–7 vs other — 3 tests.
- **H3 first hour after the US equity open** 13:30–14:30 ⇒ bar 13 vs other —
  BTC, ETH — 2 tests.
- **H4 FOMC decision days**, 18:00–20:00 UTC ⇒ bars 18–19 on scheduled FOMC
  statement days vs the same bars on other days — BTC, ETH — 2 tests. Dates:
  Federal Reserve FOMC calendars (federalreserve.gov/monetarypolicy/fomccalendars.htm),
  8 scheduled meetings per year 2021–2024 and 2025-01-29, 2025-03-19; the
  18–19 window covers the 14:00 ET release under both EST and EDT.
- **H5 US CPI release days**, 12:30–14:30 UTC ⇒ bars 12–13 on CPI release days
  vs the same bars on other days — BTC, ETH — 2 tests. Dates: BLS CPI news
  release archive (bls.gov/bls/news-release/cpi.htm), 2021-01-13 through
  2025-03-12 (51 releases); the 12–13 window covers the 08:30 ET release under
  both EST and EDT.

Statistic per test: OLS of the hourly return on the indicator (0/1), HAC lag
24, two-sided p (`predlab_xfam_cal.hac_slope`); effect = mean difference;
per-year effects reported. Family: BH-FDR q < 0.10 across the 12. A survivor
must also have the same sign in ≥ 3 of 4 years 2021–2024.

## P1 (one survivor ⇒ one session-holding config)

Long (or short, by the dev sign — a declared one-bit fit) during the window,
flat otherwise, 5 bp taker per side (2 trades/day ⇒ 10 bp/day floor; the
pre-statement: needs ≥ 10 bp mean effect per session). Reported also through
the exec_pf LTM overlay (§77). House gates: net SR ≥ 1.0, circular-shift
placebo 500 draws p < 0.10, 2× cost-stress sign, convention swap. Holdout H2,
stop-and-decide.

## Stop rule

0/12 ⇒ family CLOSED; no window, hour or date-list changes. One-shot P0
(script refuses if verdicts exist). Ledger `predlab_cal2`; result
`data/predlab/xfam/cal2_result.json`; THESIS §86. Effort < 1 day; cost $0.
