# V5 MIX 8-coin — Production Deployment Design

**Date:** 2026-05-30
**Branch:** `feature/v5-8coin-live` (off `fix/c1-portfolio-weight` = deployed `9cf436d` + 9 P0/P1 fix commits)
**Author:** session handoff
**Status:** approved (design); pending implementation plan

## 1. Goal / End-State

Deploy the hardened **V5 MIX 8-coin** strategy (BTC/ETH/BNB/SOL core + XRP/DOGE/ADA/TRX satellite) to the Hetzner live bot, replacing the current 4-coin deployment. All P0 capital-safety and P1 parity fixes — including a newly-implemented stateful 7-day min-hold — are integrated so the live system reproduces the validated 8-coin backtest (portfolio SR **+3.97** / +1053% / -4.8% MaxDD over the 4.5-yr walk-forward, `data/v5_8coin_production/summary.json`). A fresh 90-day live acceptance window starts after deploy.

Deployment drives up to the classifier-blocked VPS boundary; `.env.trading` and systemd writes are surfaced as exact operator commands (per `feedback_prod_systemd_writes_blocked`).

## 2. Why this is safe to do now (context)

- **8 of the P0/P1 fixes** already exist as a clean, tested stack on `fix/c1-portfolio-weight`, branched directly off the deployed commit `9cf436d`: C1 (`58d8254`), L1+R4 (`dafb5ce`), R2/R3 (`c2a645b`), R1/R5 (`aba6909`), P2/P3 (`0c26f15`), P5 (`5f2c98c`), P4 (`26e780e`), S1 (`e4fefdb`).
- **Discovered during planning (2026-05-30): the following P0/P1 items are NOT on the branch and are added here as Phase 1.5** — `S3265` (portfolio_before=0 book-wipe floor, **P0**), `J1` (WAL/busy_timeout), `PF1` (preflight `set -e`), `AL1` (alert hardening / dead-man). These were assumed present in the original design; code inspection proved otherwise. The spec goal ("all P0/P1 fixes integrated") requires them, especially with 8 coins (8× the over-leverage C1 guards against) and the extra journal writes min-hold introduces.
- The C1 over-leverage fix is **already 8-coin-aware**: `_V5_PORTFOLIO_WEIGHTS` holds core 0.15×4 + satellite 0.10×4; `compute_portfolio_weights(universe)` renormalizes over the active universe (4-coin → 0.25 each, 8-coin → 0.15/0.10). Both cases have passing tests.
- **Live retrains its own models daily from OHLCV** (`retrain.py` fits every route in the `routing` config; `predict.py` routes per coin). No pre-generated walk-forward prediction directories are needed for the live runtime — only the 8-coin routing config plus OHLCV cache for the 4 new coins on the box. The heavy WF dirs (`data/multi_3coins_{xrp,doge,ada,trx}_wf`, already present locally) are only for the parity-replay / re-validation harness.

## 3. Branch & Integration Strategy

- All work on `feature/v5-8coin-live` (isolated worktree `.worktrees/v5-8coin-live`).
- Merge to `main` → tag `live-v2.2.0` → deploy.
- Rollback path: retag / redeploy previous `live-v2.1.5`.

## 4. Phases

### Phase 1 — Review/verify the existing P0/P1 stack
The 9 commits guard live capital and were never merge-reviewed:
`58d8254` C1, `dafb5ce` L1+R4, `c2a645b` R2/R3, `aba6909` R1/R5, `0c26f15` P2/P3, `5f2c98c` P5, `26e780e` P4, `e4fefdb` S1, `35f0462` docs.

- Independent code review (`requesting-code-review`) of each fix against its audit finding.
- Run the existing test suite; confirm green.
- Fix any review findings before building on the stack.

### Phase 1.5 — Remaining unfixed P0/P1 items (discovered in planning)
- **S3265 (P0):** `tradingagents/execution/exchange.py:161` `get_total_portfolio_value` returns `float(account.get("totalMarginBalance", 0.0))` — a missing key yields 0.0, and `runner.py` then sizes every coin to 0 and flattens the book. Fix: raise on a missing `totalMarginBalance` key (treat as a fetch failure), and add a `min_capital_floor` guard in the runner immediately after `portfolio_before = ex.get_total_portfolio_value()` (abort + alert if `portfolio_before <= floor`).
- **J1:** `journal.py:__init__` sets only `PRAGMA foreign_keys=ON`. Add `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=10000`. One-liner; needed because min-hold adds `hold_state` writes and the monitor/rebacktest open the same DB.
- **PF1:** `deploy/preflight.sh` runs `set -euo pipefail` + `set -e`, so a supplementary-source (DefiLlama/Coinglass/Deribit) or ping failure aborts the whole trading day. Demote supplementary checks to warnings; keep hard-fail only for genuinely critical conditions (V5 imports, kelly band, universe routing, OHLCV/CoinMetrics availability).
- **AL1 (minimal):** alerts are best-effort and swallowed (`notify.py`), and the drawdown check only runs in the success path. Add: a dead-man heartbeat (a missing cycle is itself alerted), move the DD/heartbeat check into the cycle `finally`, and log alert-send failures loudly to the structured log rather than silently `pass`. (Richer second channels — email/SMS — are a follow-up.)

### Phase 2 — P1 min-hold (stateful sizing) — new code
Replicate backtest `build_positions_with_hold(min_hold=7, early_exit_loss=0.015)` (`tradingagents/strategies/v2_sizing.py:135`) in the live daily loop, which currently uses the stateless `sizer.compute_size`.

- **New journal table `hold_state`**: `coin TEXT PK, current_dir INT, bars_held INT, entry_price REAL, entry_cycle TEXT, updated_ts TEXT`.
- **New stateful sizing wrapper** (own module/unit) around `compute_size`:
  - Load prior per-coin state from `hold_state`.
  - Apply the single-bar transition matching `build_positions_with_hold`:
    - Early exit allowed when `current_dir != 0 and 3 <= bars_held < min_hold and pnl < -early_exit_loss and signal_changed`.
    - Flip / new entry allowed only when `bars_held >= min_hold and vol_ok`.
    - Otherwise hold (carry prior direction, increment `bars_held`).
  - Emit the resulting target direction/size; persist updated state.
- Runner reads/writes state each cycle. WAL (J1 fix) covers the extra writes.
- **Failure isolation:** if hold-state load/transition raises for a coin, fall back to the stateless size for that coin and emit an alert — never block the cycle.

### Phase 3 — 8-coin live config
`tradingagents/execution/live/config.py`:
- `_V5_DEFAULT_ROUTING` += 4 entries (feature sets + 2+1 pools, from backtest `baseline_v5_mix.DEFAULT_ROUTING`):
  - `ripple`:   `78f`,  pool `[bitcoin, ethereum, ripple]`
  - `dogecoin`: `78f`,  pool `[bitcoin, ethereum, dogecoin]`
  - `cardano`:  `193f`, pool `[bitcoin, ethereum, cardano]`
  - `tron`:     `78f`,  pool `[bitcoin, ethereum, tron]`
- `BINANCE_BASES` += `ripple→XRP, dogecoin→DOGE, cardano→ADA, tron→TRX`.
- `COIN_UNIVERSE` default → 8 coins; `MAX_OPEN_POSITIONS` default → 8.
- `data_refresh.py`: the fetch loop is already `cfg.coin_universe`-driven, but two hardcoded 4-coin maps must gain the 4 satellites: `coin_to_sym` (line ~379) and `_BASIS_SYM_TO_COIN` (line ~233) — `ripple↔XRPUSDT, dogecoin↔DOGEUSDT, cardano↔ADAUSDT, tron↔TRXUSDT`.
- `predict.py`: critical-failure threshold `max(3, n-1)` already scales (8-coin → critical at ≥7 coins failing); confirm with a test.
- Cost tiers / satellite haircut remain backtest-only (live pays real exchange fees); noted for validation parity, not wired into the live runtime.

### Phase 4 — Tests + re-validation
- Full `pytest` green. Extend config/routing tests to the 8-coin universe. New `hold_state` + stateful-sizer unit tests written TDD (RED first).
- **Parity gate (S1 harness):** run the fixed `compare()` over the 8-coin universe; live replay must track the 8-coin backtest equity (SR ~3.97). This confirms the corrected params (confidence_ref 0.05, asymmetric, min-hold, portfolio weights) reproduce the validated result.
- Local 8-coin backtest re-run sanity-checked against `data/v5_8coin_production/summary.json`.
- **No live capital until the parity gate is green.**

### Phase 5 — Deploy + acceptance window
- Merge `feature/v5-8coin-live` → `main`; tag `live-v2.2.0`.
- Surface exact operator VPS commands (classifier-blocked): stop `ta-cycle.timer` + `ta-monitor` + `ta-rebacktest.timer`; `git pull`; edit `/opt/tradingagents/secrets/.env.trading` to set `COIN_UNIVERSE`=8 coins, `MAX_OPEN_POSITIONS`=8, `CONFIDENCE_REF_RETURN`=0.05, `SYMMETRIC`=false; run preflight; restart timers.
- Verify first live cycle on box: 8 coins predicted, portfolio weights sum to 1.0, aggregate leverage bounded ≤ 3×, hold-state rows written.
- Start fresh 90-day acceptance window.

## 5. Confirmed Decisions

1. **P3 symmetric:** live → `SYMMETRIC=false` (asymmetric=True) to match the validated 8-coin backtest. (The "symmetric better" ablation was V2-2coin context and does not apply here.)
2. **Acceptance gate:** keep the hard floor at **SR ≥ +2.86** (do not move goalposts mid-deploy); report performance against the 8-coin backtest 3.97 aspirationally. Secondary gates unchanged (return ≥ +6.5%, MaxDD ≤ -4%).
3. **Cost tiers:** not wired into live runtime (live pays real fees).

## 6. Error Handling / Rollback

- Per-coin predict isolation already exists (`CriticalPredictFailure` at ≥ `max(3,n-1)` coins).
- New min-hold state failure → stateless fallback for that coin + alert; never blocks the cycle.
- Every phase is gated; do not proceed on red. Parity gate blocks deploy.
- Deploy rollback = redeploy `live-v2.1.5`.

## 7. Testing Strategy

- TDD for min-hold (failing tests first).
- 8-coin config/routing/weights tests (drift-guard test already links live weights ↔ `baseline_v5_mix.PORTFOLIO_WEIGHTS`).
- S1 parity harness is the integration gate before any live deploy.

## 8. Out of Scope (explicit)

- Carry sleeve and Hybrid ETH LLM modulator (separate future deployments; require their own venue/branch work and validation).
- Refitting NH-HMM / V4 regime overlay.
- Any change to the validated 8-coin backtest itself.
