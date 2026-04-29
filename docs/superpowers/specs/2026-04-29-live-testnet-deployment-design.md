# Live Testnet Deployment — Design Spec

**Date**: 2026-04-29
**Status**: Approved (brainstorming complete)
**Owner**: Adam Maleček (master thesis)
**Target deploy**: Hetzner CX22, Binance Futures testnet
**Strategy under test**: V2 baseline (LGB h=7/h=14 consensus + V2 sizing) on 3-coin pool {BTC, ETH, BNB} with PIT on-chain features (CoinMetrics + DefiLlama)

## Goal

Deploy the production V2 quant strategy to a live Binance Futures testnet environment for 90 days and produce a thesis-defendable comparison between live execution and historical backtest performance. The deployment must be reproducible, fully logged, and engineered so that any divergence between live and backtest can be root-caused from journal data alone.

## Non-goals

- Real-money trading (testnet only for thesis window).
- LLM agent debate loop in live cycle (deferred — quant-only deploy).
- Web dashboard or external monitoring stack (Telegram is sufficient).
- Multi-region failover or HA.

## Decisions log

| # | Decision | Choice |
|---|----------|--------|
| 1 | Strategy | TradingAgents V2 LGB pooled + PIT On-Chain features |
| 2 | Hetzner machine | CX22 (€4.5/mo, 2 vCPU, 4GB RAM, 40GB) |
| 3 | Schedule | Daily 00:05 UTC, single cycle |
| 4 | Comparison method | Shadow replay (daily) + Re-backtest (weekly) |
| 5 | Monitoring | Telegram bot (daily summary + alerts) |
| 6 | Risk parameters | Port V2 sizing logic; max_lev=3.0, target_vol=10%, kelly=0.5, SMA30, daily_loss=15%, stop=3%, max_pos=3 |
| 7 | Coin universe | 3-coin {BTC, ETH, BNB} with PIT on-chain features |
| 8 | Retrain cadence | Daily walk-forward (matches backtest exactly) |
| 9 | Initial capital + duration | $10,000 USDT testnet, 90 days |
| 10 | Deployment style | Bare-metal cron (systemd timers + venv) |

## Architecture

```
Hetzner CX22 (Ubuntu 24.04 LTS, Falkenstein DE)
└── /opt/tradingagents/
    ├── repo/                          # git checkout, pinned tag live-v1.0
    ├── venv/                          # Python 3.11
    ├── data/
    │   ├── checkpoints/               # daily-retrained LGB models
    │   ├── onchain_store/             # bitemporal Parquet (CoinMetrics + DefiLlama)
    │   ├── ohlcv_cache/               # Binance daily bars
    │   ├── trade_journal.db           # SQLite live trades + 9 forensic tables
    │   ├── shadow_backtest.db         # SQLite shadow replay decisions
    │   ├── live_equity.csv            # daily portfolio snapshots
    │   ├── artifacts/YYYY-MM-DD/      # raw per-cycle predictions, features, model, API responses
    │   └── reports/rebacktest_YYYYWW.json
    ├── logs/                          # structured JSONL, rotated daily
    └── secrets/.env.trading           # 600 perms, owner tabot

systemd timers:
- ta-cycle.timer       → 00:05 UTC daily — full pipeline (RuntimeMaxSec=1800)
- ta-rebacktest.timer  → Sun 02:00 UTC — weekly re-backtest
```

### Pipeline (10 steps, single cycle)

1. **fetch_onchain** — CoinMetrics + DefiLlama → `onchain_store` (PIT append, upsert by `(metric, coin, valid_from)`)
2. **fetch_ohlcv** — Binance daily bars → `ohlcv_cache` (append yesterday's close)
3. **retrain_lgb** — `build_pooled_dataset(coins=[BTC,ETH,BNB], add_onchain_pit=True, asof=today-1d)` → `lgb_model.model_run_pooled(horizons=[7,14])` → `joblib.dump` checkpoint with sha256 logged
4. **predict** — load checkpoint, build PIT features asof=today-1d, predict h=7 + h=14 per coin
5. **size** — V2 logic ported verbatim from `baseline_strategy_v2.py`:
   - per coin, per horizon h ∈ {7,14}: `dir_h = sign(pred_h - ref_price)`
   - **symmetric mode** (matches thesis result Sharpe 2.69+): `signal = dir_7` if `dir_7 == dir_14` else 0 (both must agree, longs and shorts alike)
   - `confidence = min(1.0, mean(|pred_h - ref|/ref) / CONFIDENCE_REF_RETURN)`
   - `realized_vol = std(log_returns, lookback=20) * sqrt(252)`
   - `vol_regime_mask`: skip if vol > 95th percentile of historical vol
   - `vol_targeted_size = signal * 0.5 * (0.10 / realized_vol) * confidence`
   - `apply_leverage`: `size *= (1 + (3.0 - 1) * confidence)`, capped at ±3.0
   - `apply_trend_filter`: `*1.5` if aligned with SMA30, `/1.5` if against
   - `build_positions_with_hold`: 7-day min hold, early exit if cumulative loss >1.5% AND signal flipped/flat after ≥3 bars
6. **risk_check** — `|size| <= MAX_LEVERAGE`, `portfolio_pnl_today > -MAX_DAILY_LOSS_PCT` (else kill-all + halt 24h), `open_positions < MAX_OPEN_POSITIONS`, frequency_guard
7. **execute** — close existing position if direction flips, place market order, attach stop-loss at `entry*(1-0.03)` opp side; if SL fails → status=UNPROTECTED + immediate alert
8. **shadow_replay** — run baseline_strategy_v2 engine on identical data + date, diff into `shadow_decisions`
9. **snapshot** — total portfolio + per-coin positions → `portfolio_snapshots` + `live_equity.csv`
10. **notify** — Telegram daily summary with PnL, trades, agreement rate

## Components & modules

New code under `tradingagents/execution/live/`:

| Module | Purpose |
|--------|---------|
| `runner.py` | CLI entry; orchestrates pipeline; writes `cycles` row. Flags: `--once`, `--replay <date>`, `--kill-all`, `--dry-run` |
| `data_refresh.py` | Daily incremental fetch (CoinMetrics + DefiLlama + Binance OHLCV) |
| `retrain.py` | Daily walk-forward LGB retrain on 3-coin pool with PIT on-chain features |
| `predict.py` | Load latest checkpoint, build PIT features, return `PredictionFrame(coin, h7, h14, ref_price)` |
| `sizer.py` | Imports from `tradingagents/strategies/v2_sizing.py` (refactored from `scripts/baseline_strategy_v2.py`) |
| `risk.py` | Pre-trade gates; extends existing `tradingagents/execution/risk.py` |
| `exchange.py` | Reuses existing `tradingagents/execution/exchange.py` (Binance Futures testnet wrapper) |
| `journal.py` | SQLite writer for all 9 tables; one write per pipeline step |
| `shadow.py` | Re-runs V2 backtest decision on same data + date; writes `shadow_decisions` |
| `notify.py` | `python-telegram-bot` async; daily summary + immediate alerts on FAILED/UNPROTECTED |
| `rebacktest.py` | Weekly: re-run full V2 backtest from `live_start_date` through prior day; emit `rebacktest_YYYYWW.json` + Telegram |
| `config.py` | Env var loading + validation |

**Refactor**: extract V2 sizing functions (`vol_targeted_size`, `apply_leverage`, `apply_trend_filter`, `build_positions_with_hold`) from `scripts/baseline_strategy_v2.py` into `tradingagents/strategies/v2_sizing.py`. Backtest script imports it. Single source of truth — prevents live/backtest drift.

**Tests** (under `tests/execution/`):
- `test_v2_sizing.py` — golden-value tests vs current backtest output
- `test_live_predict.py` — checkpoint load + predict produces same values as backtest at same date
- `test_shadow_replay.py` — live decision == backtest decision on same data
- `test_journal.py` — schema + write round-trip
- `test_risk_gates.py` — each gate triggers correctly under synthetic conditions
- `test_data_refresh_idempotent.py` — re-running fetch produces no duplicate rows

## Logging & observability

**Per-cycle structured log** at `logs/cycle_YYYY-MM-DD.jsonl`, one JSON object per pipeline step:
```json
{"ts": "2026-05-12T00:05:13.221Z", "cycle_id": "2026-05-12", "step": "predict", "status": "ok", "duration_ms": 412, "payload": {...}}
```

**SQLite forensic tables** in `data/trade_journal.db`:

| Table | Key columns |
|-------|-------------|
| `cycles` | cycle_id, start_ts, end_ts, status, error_msg, git_commit_sha |
| `predictions` | cycle_id, coin, horizon, model_path_sha, pred_value, pred_quantile_low, pred_quantile_high, ref_price, signal_h7, signal_h14, consensus_signal |
| `sizing` | cycle_id, coin, realized_vol, target_vol, kelly, confidence, base_size, leverage, sma30_multiplier, final_size_notional |
| `risk_checks` | cycle_id, coin, check_name, passed, value, threshold, reason |
| `trades` | cycle_id, coin, side, qty, entry_price, exit_price, pnl, fees, slippage, order_id, stop_loss_id, status |
| `portfolio_snapshots` | cycle_id, ts, total_value, usdt_balance, position_qty_per_coin, unrealized_pnl |
| `feature_snapshots` | cycle_id, coin, feature_name, value, source (CM/DefiLlama/OHLCV) |
| `model_artifacts` | retrain_id, ts, model_path, train_window_start, train_window_end, train_rows, train_dir_acc_h7, train_dir_acc_h14, sha256 |
| `shadow_decisions` | cycle_id, coin, live_signal, backtest_signal, agree, live_size, backtest_size, size_delta_pct |

**Raw artifact archive** `data/artifacts/YYYY-MM-DD/`:
- `predictions.parquet`, `features.parquet`, `model.pkl` (symlink), `binance_responses.jsonl`

**stdout/stderr** → captured by systemd journal (`journalctl -u ta-cycle`, 30-day retention via `SystemMaxUse=2G`).

**Log rotation**: `logrotate` daily, 90-day retention, gzip after 7 days.

**Crash dump**: on uncaught exception → `logs/crash_YYYY-MM-DD_HHMMSS.txt` with traceback + last 100 cycle log lines + Telegram alert with first 500 chars.

**Reconstruction guarantee**: given any `cycle_id`, the live decision can be exactly replayed using `feature_snapshots` + `model_artifacts.model_path` + `shadow.py --date <cycle_id>`.

## Failure modes

| Failure | Detection | Response |
|---------|-----------|----------|
| CoinMetrics API down | HTTPError | Skip cycle, alert. Don't trade with stale features. |
| DefiLlama API down | HTTPError | Skip cycle, alert. |
| Binance OHLCV missing yesterday | `len(df) < expected` | Skip cycle, alert. |
| LGB retrain fails | Exception | Fall back to previous checkpoint, log warning, continue. |
| Prediction sanity (>50% deviation) | `_is_prediction_sane` | Skip that coin only. |
| Binance order rejected | `BinanceAPIException` | Log status=FAILED, alert, continue. |
| Stop-loss placement fails | Exception after market order | status=UNPROTECTED, **immediate** alert. |
| Daily loss > 15% | Pre-trade check | Kill-switch: cancel pending orders, no trades 24h, alert. |
| Disk > 90% | systemd ExecStartPre | Refuse start, alert. |
| Cycle exceeds 30min | `RuntimeMaxSec=1800` | Kill, alert. |
| Telegram delivery fails | aiohttp exception | Log to journal, retry 3x, fall back to logfile-only. |

**Idempotency**: `cycle_id = YYYY-MM-DD`. Re-runs are no-ops for execution (frequency_guard). `data_refresh` upserts on `(metric, coin, valid_from)`. `retrain` overwrites checkpoint atomically.

## Hetzner provisioning & security

**Provisioning** (`scripts/provision_hetzner.sh`, run once from local machine):
- SSH key-only auth, root password disabled
- UFW: deny incoming except port 22
- fail2ban for ssh
- Unattended-upgrades (security only, no auto-reboots)
- Create `tabot` user (no sudo, owns `/opt/tradingagents`)
- Install: `python3.11`, `python3.11-venv`, `git`, `sqlite3`

**App setup** (`scripts/deploy.sh`, idempotent):
- `git clone` TradingAgents → `/opt/tradingagents/repo` (pinned tag `live-v1.0`)
- Create venv, `pip install -e repo/`
- Create `data/`, `logs/`, `secrets/` (700 perms)
- Drop `secrets/.env.trading` (600 perms, owner `tabot`)
- Symlink systemd units → `/etc/systemd/system/`
- `systemctl enable --now ta-cycle.timer ta-rebacktest.timer`

**systemd unit** `/etc/systemd/system/ta-cycle.service`:
```ini
[Unit]
Description=TradingAgents daily cycle
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=tabot
WorkingDirectory=/opt/tradingagents/repo
EnvironmentFile=/opt/tradingagents/secrets/.env.trading
ExecStartPre=/opt/tradingagents/repo/scripts/preflight.sh
ExecStart=/opt/tradingagents/venv/bin/python -m tradingagents.execution.live.runner --once
RuntimeMaxSec=1800
Nice=10
```

**Timer** `ta-cycle.timer`:
```ini
[Unit]
Description=Daily 00:05 UTC

[Timer]
OnCalendar=*-*-* 00:05:00 UTC
Persistent=true
RandomizedDelaySec=60

[Install]
WantedBy=timers.target
```

(Same pattern for `ta-rebacktest.{service,timer}` at `Sun 02:00 UTC`.)

**`preflight.sh`** checks: disk >10% free, network reachable, secrets file present + 600 perms.

**Secrets** (`/opt/tradingagents/secrets/.env.trading`):
```
LIVE_MODE=false
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
BINANCE_BASE_URL=https://testnet.binancefuture.com
COINMETRICS_API_KEY=
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
MAX_LEVERAGE=3.0
MAX_DAILY_LOSS_PCT=0.15           # = backtest --max-portfolio-dd
STOP_LOSS_PCT=0.03                # = backtest --stop-loss
MAX_OPEN_POSITIONS=3
TARGET_VOL=0.10                   # = backtest --target-vol
KELLY_FRACTION=0.5                # = backtest --kelly-fraction
VOL_LOOKBACK=20                   # realized vol window (days)
VOL_CAP_PCT=0.95                  # vol regime mask percentile
CONFIDENCE_REF_RETURN=0.02        # confidence normalization (2% pred magnitude → conf=1.0)
EARLY_EXIT_LOSS=0.015             # cumulative loss threshold for early exit
MIN_HOLD=7                        # min bars to hold winning position
TREND_SMA=30
TREND_MULTIPLIER=1.5
HORIZONS=7,14
SYMMETRIC=true                    # both h7+h14 must agree for signal (matches thesis result)
ARIMA_FILTER=false                # no ARIMA veto in default V2 (would require ARIMA model in live too)
INITIAL_CAPITAL=10000
COIN_UNIVERSE=BTC,ETH,BNB
```

**Backup**: Hetzner snapshot weekly. `rsync` cron from local pulls `/opt/tradingagents/data/` Mon 03:00 UTC.

**No inbound services**. Telegram is outbound-only. No web dashboard.

**Cost**: ~€5/mo (CX22 + snapshot).

## Comparison methodology

### Layer 1 — Daily shadow replay (decision-level)

Each cycle, after live decision, run V2 backtest engine on identical input data and store both decisions. Diff metrics over rolling 30-day window:

| Metric | Definition | Target |
|--------|------------|--------|
| `signal_agreement_rate` | % cycles where `live_signal == backtest_signal` per coin | ≥98% |
| `size_delta_pct_p95` | 95th pct of `|live_size - bt_size|/|bt_size|` | ≤5% |
| `slippage_bps` | `(exec_price - decision_price)/decision_price × 10000` | ≤10 bps median |
| `fill_failure_rate` | % orders not filled at MARKET | <1% |

### Layer 2 — Weekly re-backtest (performance-level)

Every Sunday 02:00 UTC: re-run full V2 backtest from `live_start_date` through prior day on current data. Compare to live equity curve. Output `data/reports/rebacktest_YYYYWW.json`:
```json
{
  "week_end": "2026-W18",
  "live_days": 14,
  "live": {"sharpe": 2.41, "return_pct": 4.2, "max_dd": 3.1, "n_trades": 18, "win_rate": 0.61},
  "backtest": {"sharpe": 2.58, "return_pct": 4.7, "max_dd": 2.8, "n_trades": 18, "win_rate": 0.67},
  "delta": {"sharpe": -0.17, "return_pct": -0.5, "max_dd": +0.3},
  "per_coin": {"BTC": {...}, "ETH": {...}, "BNB": {...}},
  "explanation": "live underperforms by 0.5pp; primary driver: 6 bps avg slippage on entry"
}
```

Telegram weekly summary verdict: `CONVERGING` / `DIVERGING` / `BROKEN`.

### Acceptance criteria (90-day window)

Deployment is a **valid thesis instrument** if:

1. ≥85 of 90 cycles completed
2. `signal_agreement_rate ≥ 0.95` over full window
3. `|live_sharpe - backtest_sharpe| ≤ 0.5` (within statistical noise for 90-day window)
4. No `UNPROTECTED` trade left open >1 hour
5. Zero kill-switch trips from real bugs (legitimate market drawdowns acceptable)

Failure of (1-2) = engineering/infra problem. Failure of (3) with (1-2) passing = legitimate finding for thesis (live frictions matter).

### Thesis output

`THESIS_FINDINGS.md` Section 12 "Live Deployment vs Backtest" — table of weekly Sharpe/Return/DD deltas, slippage histogram, signal agreement chart, narrative analysis of any divergence sources.

## Manual recovery commands

```bash
python -m tradingagents.execution.live.runner --once                # re-run today
python -m tradingagents.execution.live.runner --replay 2026-05-12   # reconstruct from journal
python -m tradingagents.execution.live.runner --kill-all            # close all positions, halt
python -m tradingagents.execution.live.shadow --date 2026-05-12     # ad-hoc shadow check
python -m tradingagents.execution.live.rebacktest --week 2026-W18   # re-run weekly report
```

## Open questions

1. **PIT On-Chain features in V2 retrain**: PIT On-Chain Phase 1 (`feature/onchain-features-p1` branch, commit `b2531c7`) wires `add_onchain_pit=True` into `build_pooled_dataset`. Is that branch merged to main yet? If not, deployment must pin to that branch's commit. Verify pre-deploy.
2. **Sharpe target for acceptance criterion 3**: Backtest reference Sharpe is the **5.5yr 3-coin masked PIT On-Chain** value (≈3.10) — but a 90-day live window will not produce a stable Sharpe at that confidence. Propose: rebaseline the comparison Sharpe target against the **same 90-day window of the most recent backtest period** (computed at deploy time), not the 5.5yr value.
3. **`live-v1.0` git tag**: doesn't exist yet; create from main (or feature branch per #1) when implementation is complete and tests pass.
4. **CoinMetrics community API rate limits**: 32-metric daily fetch for 3 coins is well within community tier, but verify no auth required for current endpoints (per memory: base URL works without key as of 2026-04-21).

## References

- `scripts/baseline_strategy_v2.py` — V2 sizing source (to be refactored into `tradingagents/strategies/v2_sizing.py`)
- `scripts/backfill_onchain.py` — pattern for incremental on-chain fetch
- `tradingagents/execution/exchange.py` — existing Binance Futures wrapper
- `Krypto-v0/src_live/runner.py` — reference implementation pattern (cycle structure, frequency guard, sanity checks)
- `THESIS_FINDINGS.md` Section 11 — PIT On-Chain Phase 1 results (Sharpe 3.10, +2937% 5.5yr)
