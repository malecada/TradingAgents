# Live Bot Monitoring UI — Design

**Date:** 2026-05-21
**Status:** Approved
**Target branch:** `feature/live-monitor-ui`

## Purpose

A simple read-only web UI to monitor the V5 MIX live bot running on the Hetzner
VPS. Tracks performance, trades, per-cycle model predictions/decisions, and
system health. Single-user (thesis author), also usable as a thesis-demo
artifact.

## Constraints

- The live bot and its forensic SQLite journal (`trade_journal.db`) run on the
  Hetzner VPS. The UI runs **on the same VPS** and reads the journal directly.
- The UI is strictly **read-only** — it must never write to or lock the journal
  DB, and must never interfere with the bot's cycle.
- Production live strategy is **V5 MIX quant** (no LLM agents in production).
  "Predictions and decisions" therefore means the quant pipeline output:
  LGB predictions, consensus signals, bundle routing, sizing, risk checks,
  shadow decisions.
- The bot may be pre-trade (journal can contain zero trades). Every view must
  render a meaningful empty state.

## Data sources

| Source | Location | Used for |
|--------|----------|----------|
| SQLite journal | `$DATA_DIR/trade_journal.db` (default `data/trade_journal.db`) | trades, predictions, sizing, risk checks, portfolio snapshots, retrains, shadow decisions, cycles |
| Structured log | `$LOG_DIR/cycle_*.jsonl` (default `logs/`) | per-step timing + status for the System health timeline |

Journal tables (from `tradingagents/execution/live/schema.sql`): `cycles`,
`predictions`, `sizing`, `risk_checks`, `trades`, `portfolio_snapshots`,
`feature_snapshots`, `model_artifacts`, `retrains`, `shadow_decisions`.

The journal is opened via the SQLite read-only URI
(`file:<path>?mode=ro`, `uri=True`). The structured-log directory is read by
tailing the newest `cycle_*.jsonl` file.

## Stack

- **FastAPI** single process, server-rendered HTML (Jinja2) + JSON API.
- **Chart.js** for the equity curve, **vendored locally** in `static/` (no CDN
  — keeps the VPS UI self-contained and offline-safe).
- No build step, no Node. Python only, matching the repo.
- Runs as a `systemd` unit `ta-monitor.service`, mirroring `ta-cycle.service`.

## Architecture

New package `tradingagents/monitor/`:

| File | Responsibility |
|------|----------------|
| `app.py` | FastAPI app, basic-auth dependency, route + API registration, startup |
| `db.py` | Read-only journal connection + one query function per view |
| `metrics.py` | Derived stats: equity series, cumulative PnL, live Sharpe, max drawdown |
| `health.py` | Parse newest `cycle_*.jsonl` into cycle/step status records |
| `templates/base.html` | Page shell: header + tab nav |
| `templates/_performance.html`, `_trades.html`, `_decisions.html`, `_health.html` | Per-tab partials |
| `static/app.js` | Tab switching + 30s poll loop (`fetch` per active tab) |
| `static/app.css` | Dark theme (matches approved mockup) |
| `static/chart.min.js` | Vendored Chart.js |
| `__main__.py` | `python -m tradingagents.monitor` entrypoint (uvicorn) |

Each unit has a single purpose and is independently testable: `db.py` functions
take a connection and return plain dicts/lists; `metrics.py` functions take
those rows and return numbers; routes in `app.py` compose them into JSON.

## Endpoints

| Route | Returns |
|-------|---------|
| `GET /` | HTML shell (header + tabs); tab content loaded via API |
| `GET /api/performance` | equity series (live + backtest anchor), stat cards, per-coin PnL |
| `GET /api/trades` | trade rows + open positions |
| `GET /api/cycles` | list of cycle ids + start ts + status |
| `GET /api/cycle/{cycle_id}` | per-coin predictions, sizing, risk checks, shadow decisions for one cycle |
| `GET /api/health` | cycle/step timeline, data-source staleness, retrain history, recent errors |

All `/api/*` routes return JSON. All routes (including `/`) require basic auth.

## Views

### Performance
- Stat cards: current equity, live annualized Sharpe, max drawdown, open
  position count.
- Equity curve: live equity vs. the backtest anchor line (V5 MIX SR 3.18).
  Live equity series derived from `portfolio_snapshots.total_value`; if absent,
  reconstructed from cumulative realized + unrealized PnL.
- Per-coin PnL table: coin, bundle route, current position, unrealized PnL,
  realized PnL.

### Trades
- Sortable trade log: ts (cycle), coin, side, qty, entry price, exit price,
  PnL, fees, slippage, status.
- Open positions (status not closed) pinned at the top.

### Predictions & decisions
- Cycle picker (defaults to most recent cycle).
- For the selected cycle, per coin: LGB prediction h7 / h14 with quantile
  low/high, reference price, consensus signal, bundle route, sizing breakdown
  (realized vol, target vol, kelly, confidence, leverage, sma30 multiplier,
  final notional), risk-check pass/fail with reasons, shadow decision
  (live vs backtest signal agreement + size delta).

### System health
- Cycle status timeline: per cycle a ok/fail marker with start/end ts and
  error message if any.
- Data-source freshness: `critical_data_fail_sources` and
  `supplementary_stale_sources` from the latest cycle.
- Retrain history: rows from `retrains` (retrain id, ts, train rows, dir acc,
  status, routes).
- Recent errors: non-`ok` step records from the newest structured log file.

## Auth & deployment

- HTTP basic auth. Single password read from env `TA_MONITOR_PASSWORD`.
  Username fixed (`admin`). If the env var is unset the app refuses to start.
- The app binds `127.0.0.1` only. A reverse proxy (Caddy preferred for
  automatic HTTPS; reuse an existing nginx if the VPS already has one)
  terminates TLS and forwards to the app port.
- `deploy/systemd/ta-monitor.service` — long-running unit, `Restart=always`,
  `DATA_DIR` / `LOG_DIR` / `TA_MONITOR_PASSWORD` from the deploy environment.
  No timer (unlike `ta-cycle`); it is a persistent service.
- Deployment steps appended to `deploy/deploy.sh` / documented in the deploy
  notes. Reverse-proxy config committed under `deploy/`.

## Error handling & empty states

- Missing journal file or `OperationalError: database is locked` → API routes
  return HTTP 503 with a short JSON error; the UI shows a non-blocking banner
  and keeps polling. The app never crashes on DB issues.
- Empty tables → each view renders an explicit empty state ("No trades yet",
  "No cycles logged yet", "No retrains yet") rather than a blank panel or error.
- Staleness: if the latest cycle start is older than 2 hours, the header status
  dot turns amber with the age shown; on a logged cycle failure it turns red.
- Read-only enforcement: the journal connection uses `mode=ro`; any accidental
  write attempt fails fast rather than corrupting the bot's DB.

## Testing

Pytest, under `tests/monitor/`.

- Shared fixture builds a temporary SQLite journal from `schema.sql` and inserts
  representative rows (a couple of cycles, predictions, sizing, risk checks,
  trades, portfolio snapshots, retrains, shadow decisions).
- `db.py`: each query function returns expected rows from the fixture DB.
- `metrics.py`: Sharpe / max-drawdown / cumulative-PnL computed on a known
  equity series match hand-calculated values.
- `health.py`: parses a sample `cycle_*.jsonl` into the expected timeline.
- Each `/api/*` route: returns HTTP 200 with valid JSON for the fixture DB.
- Auth: request without / with wrong credentials → 401; correct → 200.
- Empty DB: routes return 200 and views render empty states (no 500s).
- DB-locked / missing-file simulation → 503, app stays up.

## Out of scope

- No control actions (no start/stop/flatten from the UI — read-only).
- No LLM-agent decision views (production strategy is pure quant).
- No multi-user accounts or roles (single shared password).
- No alerting — Telegram notifications already exist (`notify.py`).
- No historical backtest browser — the UI shows live data only.
