# Live Bot Monitoring UI

Read-only FastAPI dashboard for forecast-quality research and live strategy
monitoring. Reads structured research journals (weights-and-returns), live bot
trade journals, and cycle logs. Never writes to any data source.

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

- **Book** — weighted portfolio composition (long/short allocations), position
  entry/exit signals, realized returns per position. Displays book-level
  metadata (universe size, membership hash, scale), position history, and
  factor contribution to total realized return.

- **Gate** — sealed one-shot evaluation tracker (informational only). Displays
  window start date (2026-07-02), earliest evaluation date (2027-01-02), days
  elapsed/remaining, Sharpe threshold (0.946 or 0.5x dev ovl SR), pass/fail
  criteria, and running proxy (paper journal SR and realized-return count).
  The official evaluation stays sealed and uses the backtest harness on the
  forward window.

- **Ops** — cycle timeline, pipeline-step timings, recent errors, data freshness.
  Displays book-level metadata changes, last update timestamp, and system health
  (data staleness tracked via written_utc; threshold 36 hours).

- **Legacy** — read-only archive of decommissioned V5 live-bot journals (quant +
  hybrid). Includes Performance (equity, Sharpe, drawdown), Positions (open
  holdings with entry/mark/leverage/uPnL), Executions (order logs), Decisions
  (per-cycle predictions and sizing), and Health tabs. Legacy data is never
  recomputed; updates stopped when the dual-strategy bot was decommissioned.

## Predlab Research Books

Research books are organized under `PREDLAB_DATA_DIR/predlab/` as:

```
predlab-data/
├── predlab/
│   ├── champion_backtest.json       # backtest metadata for anchor Sharpe
│   ├── gates.json                   # gate thresholds and sealed one-shot status
│   └── s1_paper/
│       ├── journal_champion.jsonl   # champion (Phase-O frozen) weights-and-returns
│       └── journal.jsonl            # vt10 (legacy S1 book) weights-and-returns
└── ...
```

### Journal semantics

Each `.jsonl` file in `s1_paper/` contains one JSON object per line (one per day):

- `asof` (string, ISO date YYYY-MM-DD) — the bar date
- `written_utc` (string, ISO timestamp) — when the row was written; used to
  detect staleness (threshold 36 hours)
- `weights` (dict, symbol → float ±0.025) — allocation at close
- `realized_book_ret` (float | null) — realized P&L since last close; used to
  compound equity curve; rows with null return are excluded from warmup count
- `n_universe` (int) — size of eligible universe on this date
- `membership_hash` (string) — hash of current membership set
- `est_turnover` (float | null) — estimated portfolio turnover
- `est_cost` (float | null) — estimated transaction cost
- `vt15_b100_scale` or `vt10_scale` (float | null) — volatility target scaling
  factor; used to compute position sizes
- `breadth` (int | null, optional) — champion rows only; number of unique
  securities held

**Equity reconstruction**: equity = starting_capital × product(1 + realized_book_ret)
  — computed after warm-up of 21 realized returns for volatility target scaling
  to stabilize the equity curve.

### Reference files

- `champion_backtest.json`: backtest Sharpe and yearly return streams displayed
  as anchor reference on the Performance tab.
- `gates.json`: sealed one-shot configuration; contains `predlab_opt.forward_one_shot`
  (gate thresholds) and `predlab_opt.final_champion` (reference metrics for threshold
  derivation). Shown on the Gate tab.

## API Endpoints

### Predlab endpoints

- `GET /api/predlab/performance` — equity curve, Sharpe, drawdown, rolling
  Sharpe for champion and vt10 books; reference metrics and backtest yearly
  returns
- `GET /api/predlab/book?book=champion|vt10` — latest-row weighted composition,
  position history, and realized returns
- `GET /api/predlab/gate` — sealed one-shot tracker (window dates, days elapsed,
  threshold, pass/fail criteria, running proxy)
- `GET /api/predlab/health` — data freshness, malformed-row counts, known data
  gaps, heartbeat note (journal backup timing)

### Degradation contract

All predlab endpoints return HTTP 200 with null/empty blocks when data is missing
or PREDLAB_DATA_DIR is unset:

- `GET /api/predlab/performance` returns `{"books": {"champion": null, "vt10": null}, "reference": null, "backtest_yearly": null}`
- `GET /api/predlab/book?book=<name>` returns `{"book": "<name>", "detail": null}` (or HTTP 400 if book name is unknown)
- `GET /api/predlab/gate` returns a normal gate_status object with empty champion
  rows (informational: true, running SR null)
- `GET /api/predlab/health` returns `{"books": {"champion": null, "vt10": null}, "heartbeat_note": "..."}`

Per-book isolation applies: a missing or unreadable journal for one book yields
`null` for that book only; the other book continues serving normally.

### Known data gaps

The VPS scheduler was offline 2026-07-31 through 2026-08-02 (documented, not an
incident). These dates appear in the health payload with `known: true`.

### Legacy pane

If `QUANT_DATA_DIR` and `HYBRID_DATA_DIR` are unset, the Legacy tab is hidden.
The legacy `/api/performance`, `/api/positions`, `/api/health`, and `/api/compare`
endpoints degrade per-strategy; a missing or unreadable journal for one strategy
yields `null` for that strategy only.

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

## UI Removal Notes

- **Run Prediction tab** was removed (V5 checkpoint evaluation retired). The backend
  `/api/adhoc/*` routes remain mounted for backward compatibility but have no UI
  integration.

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

On the VPS, `PREDLAB_DATA_DIR` should be set to `/opt/tradingagents/predlab-data`.
Reference files and journals must be in place before the service starts:

```
/opt/tradingagents/predlab-data/predlab/
├── champion_backtest.json
├── gates.json
└── s1_paper/
    ├── journal_champion.jsonl
    └── journal.jsonl
```

The journals are populated by the S1 paper-trader process running independently.
The `predlab-journal-backup` branch on origin pushes daily journal snapshots
(approximately 00:45 UTC).
