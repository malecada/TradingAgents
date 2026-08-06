# Live Bot Monitoring UI

Read-only FastAPI dashboard for forecast-quality research and live strategy
monitoring. Reads structured research books (weights-and-returns journals),
live bot journals, and cycle logs. Never writes to any data source.

## Quick Start

### Run locally (predlab mode)

```bash
PREDLAB_DATA_DIR=data/predlab \
TA_MONITOR_PASSWORD=somepw \
  python -m tradingagents.monitor
# open http://127.0.0.1:8800  (user: admin)
```

### Include legacy V5 archives (optional)

```bash
PREDLAB_DATA_DIR=data/predlab \
QUANT_DATA_DIR=data/quant \
HYBRID_DATA_DIR=data/hybrid \
HYBRID_BINANCE_API_KEY=xxx \
HYBRID_BINANCE_API_SECRET=yyy \
TA_MONITOR_PASSWORD=somepw \
  python -m tradingagents.monitor
```

## Tabs

### Predlab-first tab set

- **Performance** — equity curve reconstruction from realized book returns,
  Sharpe, drawdown, rolling Sharpe, uPnL cards. Champion backtest anchor shown
  alongside live performance. Multi-strategy comparison panels available when
  additional books are loaded.

- **Book** — weighted portfolio composition, entry/exit signals, realized
  returns per position. Displays book-level metadata (holdout DSR, phase, gate
  status), position history, and factor contribution to total realized return.

- **Gate** — pass/fail thresholds (Sharpe, DSR, equity curve shape) for the
  champion model and experimental candidates. Shows gate status (`OPEN` / `CLOSED`),
  historical progression, and degradation contract (null when gate data
  unavailable).

- **Ops** — cycle timeline, pipeline-step timings, recent errors, data freshness.
  Displays book-level metadata changes, update frequency, and system health.

- **Legacy** — read-only archive of decommissioned V5 live-bot journals (quant +
  hybrid). Includes Performance (equity, Sharpe, drawdown), Positions (open holdings
  with entry/mark/leverage/uPnL), Executions (order logs), Decisions (per-cycle
  predictions and sizing), and Health tabs. Legacy data is never recomputed;
  updates stopped when the dual-strategy bot was decommissioned.

## Predlab Research Books

Research books are organized under `PREDLAB_DATA_DIR/predlab/` as:

```
predlab-data/
├── predlab/
│   ├── champion_backtest.json       # backtest metadata for anchor Sharpe
│   ├── gates.json                   # gate thresholds and status
│   └── books/
│       ├── book_1.jsonl             # weights-and-returns journal
│       ├── book_2.jsonl
│       └── ...
└── ...
```

### Journal semantics

Each `.jsonl` file in `books/` contains one JSON object per line:

- **Weights record**: `{"symbol": "BTC", "weight": 0.5, "timestamp": "2026-01-01T00:00:00Z"}`
  — allocation at rebalance or end-of-bar
- **Return record**: `{"realized_book_ret": 0.0123, "timestamp": "2026-01-01T01:00:00Z"}`
  — realized P&L since last close, used to compound equity curve
- **Equity reconstruction**: equity = starting_capital × product(1 + realized_book_ret)
  — computed after warm-up of 21 realized returns for volatility target scaling

### Book metadata

- `champion_backtest.json`: backtest Sharpe, return stream, and performance
  metrics displayed as anchor reference on the Performance tab.
- `gates.json`: threshold configuration and current pass/fail status for each gate
  (Sharpe threshold, DSR threshold, etc.). Shown on the Gate tab.

## API Endpoints

### Predlab endpoints

- `GET /api/predlab/health` — book refresh status, available books, known data gaps
- `GET /api/predlab/performance` — equity curve, Sharpe, drawdown, rolling Sharpe
- `GET /api/predlab/book` — weighted composition, position history, realized returns
- `GET /api/predlab/gate` — gate status, threshold values, pass/fail progression

### Degradation contract

- **Missing books**: if `PREDLAB_DATA_DIR` is unset or unreachable, all predlab
  endpoints return `{"status": "degraded", "books": []}` and the Performance/Book/Gate/Ops
  tabs render null (grayed out). Legacy tab continues serving from `QUANT_DATA_DIR`
  and `HYBRID_DATA_DIR` if available.
- **Per-book isolation**: a missing or unreadable journal for one book yields `null`
  for that book only. Other books continue serving normally.
- **Legacy pane**: if `QUANT_DATA_DIR` and `HYBRID_DATA_DIR` are unset, the Legacy
  tab is hidden (no dual-strategy archives to display).

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `PREDLAB_DATA_DIR` | — (optional) | Root directory holding `predlab/` (books, gates, champion metadata); required for predlab tabs |
| `TA_MONITOR_PASSWORD` | — (required) | Basic-auth password; app refuses to start if unset |
| `QUANT_DATA_DIR` | `$DATA_DIR` → `data` | Directory holding the quant bot's `trade_journal.db` (legacy V5 archive) |
| `HYBRID_DATA_DIR` | — (optional) | Directory holding the hybrid bot's `trade_journal.db` (legacy V5 archive) |
| `DATA_DIR` | `data` | Fallback data directory when `QUANT_DATA_DIR` is not set |
| `LOG_DIR` | `logs` | Directory holding `cycle_*.jsonl` (quant runner only) |
| `BINANCE_API_KEY` / `BINANCE_API_SECRET` | — | Quant bot live-account credentials (follow quant runner's `LIVE_MODE` config) |
| `HYBRID_BINANCE_API_KEY` / `HYBRID_BINANCE_API_SECRET` | — | Hybrid bot testnet credentials (always queries testnet, regardless of quant `LIVE_MODE`) |
| `TA_MONITOR_ANCHOR_SR_QUANT` | `3.18` | Backtest Sharpe anchor for the legacy quant strategy (shown on Legacy Performance tab) |
| `TA_MONITOR_ANCHOR_SR_HYBRID` | — (optional) | Backtest Sharpe anchor for the legacy hybrid strategy (shown on Legacy Performance tab) |
| `TA_MONITOR_HOST` | `127.0.0.1` | Bind host (keep loopback; proxy terminates TLS) |
| `TA_MONITOR_PORT` | `8800` | Bind port |
| `TA_MONITOR_START_CAPITAL` | `10000` | Starting capital for equity reconstruction when no snapshots exist |

## Authentication

Basic HTTP authentication (user `admin`, password from `TA_MONITOR_PASSWORD`) is
required on all endpoints. The password is checked once per session; requests
without valid credentials receive a 401 Unauthorized response.

## React build workflow

The built React SPA is committed to the repo as `tradingagents/monitor/frontend/dist/`.
The VPS does **not** need Node.js installed — the dist is served directly by FastAPI.

To rebuild after frontend changes:

```bash
cd tradingagents/monitor/frontend
npm install          # first time only
npm run build        # writes to dist/; commit the result
```

## Deployment

`deploy/systemd/ta-monitor.service` runs it as a persistent service;
`deploy/Caddyfile` provides public HTTPS. See `deploy/deploy.sh`.

Secrets are loaded from `EnvironmentFile=/opt/tradingagents/secrets/.env.trading`
(quant Binance keys) and optionally
`EnvironmentFile=-/opt/tradingagents/secrets/.env.monitor` (monitor-specific
vars including `TA_MONITOR_PASSWORD`, `PREDLAB_DATA_DIR`, `QUANT_DATA_DIR`,
`HYBRID_DATA_DIR`, and hybrid credentials).

On the VPS, `PREDLAB_DATA_DIR` should be set to `/opt/tradingagents/predlab-data`,
and reference files (`gates.json`, `champion_backtest.json`) should be copied
alongside the research books:

```
/opt/tradingagents/predlab-data/predlab/
├── champion_backtest.json
├── gates.json
└── books/
    ├── book_1.jsonl
    └── ...
```
