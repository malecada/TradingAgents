# Task H2 — Holdout One-Shot: Report

**Status:** COMPLETE. **Verdict: deploy = ∅ (NO-GO on both sleeves).**
**Date:** 2026-07-09 · **Branch:** `rebuild/honest-2026-07` · **Contract:** `data/rebuild/frozen_portfolio.json` @ **fc33cd5** (verified unmodified before run).

---

## 1. Execution log summary

1. Verified contract provenance: `git log -1 … frozen_portfolio.json` → `fc33cd5`; working-tree status of the file clean. Branch `rebuild/honest-2026-07`, HEAD `fc33cd5`.
2. Read the frozen contract, task brief, `gates.json`, `factor_baselines.py`, `carry_audit_costs.py`, `compare.py` (placebo algorithm), `ledger.py`, `carry_sleeve.py`, `run_coin_backtest`, `costs_for_coin`, `fetch_spot_close`.
3. Built `scripts/holdout/carry_stressed_holdout.py` — a pass-through copy of `carry_audit_costs.py` with only authorized edits (see §5). Ran it → carry stressed holdout series + `costs.json` under `data/rebuild/holdout/carry_audit/`. All three frozen sanity checks passed (all-zero==asbuilt; waterfall non-increasing; rebalance counts plausible = BTC 15 / ETH 40 of 456 days).
4. Verified dev `data/rebuild/carry_audit/` untouched (`git diff --stat` empty) — contract check PASS.
5. Built `scripts/holdout/run_holdout.py` — imports the frozen factor path verbatim, runs the factor sleeve (two-stage warm-up + fresh-latch), combines sleeves with the frozen allocation rule, runs the N=500 placebo, evaluates the `holdout_deploy` gate, writes `result.json`, logs 3 ledger rows (`allow_holdout=True`).
6. Ran it. Placebo runtime ≈29 s (well under 60 min). Wrote `result.json`, `placebo_distribution.json`, daily-return CSVs. Confirmed 4 total `holdout_oneshot` ledger rows (carry + factor + portfolio + placebo).
7. Appended THESIS_FINDINGS §41. Committed.

## 2. Per-sleeve holdout metrics (2025-04-01 → 2026-07-01, standalone)

| sleeve | net SR | total return | maxDD | n_bars |
|--------|-------:|-------------:|------:|-------:|
| factor (EW BTC+ETH) | +0.389 | +6.67% | −14.43% | 456 |
| — bitcoin | −0.339 | — | — | (halted: 15% latch tripped) |
| — ethereum | +0.620 | — | — | (survived) |
| carry (stressed 50/50) | −1.477 | −1.14% | −1.97% | 456 |

Carry waterfall (holdout): as_built +7.531 → +turnover +6.004 → +rebalance +1.934 → **+margin_cost −1.477** → +boundary_basis −1.477. Margin drag flips it negative (dev bottomed at +3.75).

## 3. Portfolio & weight schedule

Frozen rule: 50/50 freeze, monthly inverse-vol on trailing-90d vol, carry cap 0.5, zero-vol guard. **Cap binds every rebalance** (carry ann-vol ~0.003–0.005 vs factor ~0.06–0.13 → raw inverse-vol wants carry ~95%, clipped to 0.5). Book is a constant 50/50 across all 15 rebalances.

| portfolio | net SR | total return | maxDD | n_bars |
|-----------|-------:|-------------:|------:|-------:|
| factor+carry | **+0.380** | +3.42% | −7.17% | 455 |

## 4. Placebo (factor sleeve, N=500)

Real factor SR +0.389; 82/500 placebos ≥ real → **p = 83/501 = 0.166**. Placebo SR: mean −0.458, p95 +0.987. Real signal not distinguishable from a persistence-matched random signal.

## 5. Gate evaluation — `holdout_deploy`

| criterion | scope | threshold | measured | verdict |
|-----------|-------|----------:|---------:|:-------:|
| portfolio_net_sharpe_min | portfolio | ≥ 0.50 | 0.380 | **FAIL** |
| max_drawdown_max | portfolio | ≤ 0.15 | 0.072 | PASS |
| sleeve_contribution_min (carry) | sleeve | ≥ 0.0 | −0.0114 | **FAIL** |
| sleeve_contribution_min (factor) | sleeve | ≥ 0.0 | +0.0667 | PASS |
| placebo_p_max (factor) | sleeve | < 0.05 | 0.166 | **FAIL** |

2/5 pass. **VERDICT: deploy = ∅.** Carry NO-GO (negative contribution); factor NO-GO (placebo insignificant + drags portfolio SR below floor). Nothing advances to Phase 4 as deployable.

## 6. Contract friction encountered (flagged loudly)

Three items required interpretation. None is an economic/parameter change; all are documented in-code and in §41. I judged none severe enough to BLOCK — the contract's *intent* was unambiguous in every case and every reasonable reading yields the same NO-GO — but each is surfaced verbatim below.

### 6a. Carry window is hardcoded in TWO places (the load-bearing one is not the one the contract names)
The contract authorizes editing carry `START`/`END`:

> "H2 is permitted to change EXACTLY three things in scripts/carry_audit_costs.py … START -> "2025-04-01", END -> "2026-07-01", and the output directory"

But module-level `START, END` (line 42) are used **only** for `out["window"]` metadata and the ledger window. The **actual data fetch window** is a *second*, separate hardcoding inside `build_symbol` (line 74): `start, end = date(2021, 11, 8), date(2025, 3, 31)`. Changing only the module constants would have run carry on **dev** data while labelling it holdout — directly contradicting step 2's prose:

> "Run the C2 stressed construction … over the holdout window ONLY -- START/END set directly to the holdout bounds (2025-04-01 / 2026-07-01)"

**Resolution:** set the window to the holdout bounds in *both* places (module constants + `build_symbol`). This is a window edit (same authorized category as START/END), touches no cost parameter, and is the only reading consistent with "over the holdout window ONLY." The dev-artifact-untouched check (`git diff --stat data/rebuild/carry_audit/` empty) still passed.

### 6b. Pass-through copy needed a PROJECT_ROOT depth fix
The copy lives in `scripts/holdout/` (one level deeper than the original in `scripts/`). `PROJECT_ROOT = Path(__file__).resolve().parent.parent` therefore resolved to `scripts/` instead of the repo root, breaking the `from scripts.…` imports and all output paths. Changed to `.parent.parent.parent`. Purely mechanical path resolution forced by the file's authorized location (the execution note explicitly blesses "make scripts/holdout/carry_stressed_holdout.py as a copy"); no economic change.

### 6c. Per-sleeve deploy composition is under-specified
The gate mixes portfolio-level criteria (SR, maxDD on the combined book) with sleeve-level criteria (per-sleeve contribution; placebo for factor only), while the verdict is `{"deploy": [sleeves that passed]}`. The exact mapping from the mixed gate to the per-sleeve deploy list is not spelled out. **Resolution (documented in `result.json` `deploy_composition_rule`):** portfolio SR & maxDD are a global precondition; a sleeve deploys iff the precondition holds AND its contribution ≥ 0 AND (factor also) placebo p < 0.05. Immaterial to the outcome: carry fails contribution and factor fails placebo under *any* reasonable reading, and the portfolio SR precondition fails independently → deploy = ∅ regardless.

Also noted (non-blocking): the stage-1 signal was obtained by **importing `ma_cross_signal`** and computing on full-history closes (the contract's explicitly stated method), rather than by shelling out `factor_baselines.py --end 2026-07-01` (which would trip the ledger holdout guard and whose CSVs the contract says are "NOT the signal artifact"). The signal is deterministic, so the two are identical; the import path avoids an unnecessary guard-passage edit to the frozen script.

## 7. Files changed / created

- `scripts/holdout/carry_stressed_holdout.py` — new (pass-through copy; diff vs original = window×2 + outdir + ledger flag + PROJECT_ROOT depth).
- `scripts/holdout/run_holdout.py` — new (factor sleeve + combination + placebo + gates orchestrator).
- `data/rebuild/holdout/result.json` — new (per-sleeve + portfolio metrics, weight schedule, placebo, gate table, verdict).
- `data/rebuild/holdout/carry_audit/{costs.json,sleeve_stressed_daily.csv}` — new.
- `data/rebuild/holdout/factor_floor/daily_returns.csv`, `data/rebuild/holdout/portfolio_daily_returns.csv`, `data/rebuild/holdout/placebo_distribution.json` — new.
- `data/rebuild/trial_ledger.jsonl` — +4 rows (`holdout_oneshot`, `allow_holdout=True`).
- `THESIS_FINDINGS.md` — §41 appended.
- `data/rebuild/carry_audit/` (dev) — UNTOUCHED (verified).

## 8. Reproduce

```bash
uv run python scripts/holdout/carry_stressed_holdout.py   # carry sleeve, holdout window
uv run python scripts/holdout/run_holdout.py              # factor + portfolio + placebo + gates
```
