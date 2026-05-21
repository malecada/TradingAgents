# Live Bot Monitoring UI

Read-only FastAPI dashboard for the V5 MIX live bot. Reads the bot's
`trade_journal.db` (SQLite, `mode=ro`) and structured cycle logs. Never
writes to the bot's data.

## Run locally

```bash
TA_MONITOR_PASSWORD=somepw python -m tradingagents.monitor
# open http://127.0.0.1:8800  (user: admin)
```

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `TA_MONITOR_PASSWORD` | — (required) | Basic-auth password; app refuses to start if unset |
| `DATA_DIR` | `data` | Directory holding `trade_journal.db` |
| `LOG_DIR` | `logs` | Directory holding `cycle_*.jsonl` |
| `TA_MONITOR_HOST` | `127.0.0.1` | Bind host (keep loopback; proxy terminates TLS) |
| `TA_MONITOR_PORT` | `8800` | Bind port |
| `TA_MONITOR_START_CAPITAL` | `10000` | Starting capital for equity reconstruction when no snapshots exist |

## Deployment

`deploy/systemd/ta-monitor.service` runs it as a persistent service;
`deploy/Caddyfile` provides public HTTPS. See `deploy/deploy.sh`.

## Tabs

- **Performance** — equity curve vs backtest anchor (SR 3.18), Sharpe, drawdown, per-coin PnL
- **Trades** — full trade log + open positions
- **Predictions & decisions** — per-cycle LGB predictions, sizing, risk checks, shadow decisions
- **System health** — cycle timeline, pipeline-step timings, recent errors, retrain history
