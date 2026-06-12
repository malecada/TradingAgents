# Monitor UI v2 — React rewrite with dual-strategy (quant vs hybrid) tracking

**Date**: 2026-06-12
**Status**: Approved design
**Base**: `live-v2.3.3` (branch `feature/monitor-react-ui`)

## Goal

Rebuild the live-bot monitor frontend as a React SPA and extend the backend so the
dashboard tracks BOTH live strategies — the V5 MIX quant bot and the hybrid
(quant × LLM-modulator) A/B bot — side by side, with live positions, unrealized
PnL, holdings distribution, an upgraded performance chart, and trade analytics.

## Scope (user-confirmed)

1. **Unified dual-strategy UI** — every view knows both strategies; comparison is
   first-class, not a bolt-on tab.
2. **Positions + uPnL panel** — per-strategy live positions (side, qty, entry,
   mark, leverage, notional, uPnL $/%, liq price) + total-uPnL cards.
3. **Holdings distribution** — allocation donut per strategy (per-coin |notional|
   + free USDT).
4. **Performance chart upgrade** — both equity lines indexed to 100, drawdown
   subplot, rolling 30-bar Sharpe, time-range selector (7d/30d/90d/all),
   backtest-anchor reference.
5. **Trade analytics** — realized PnL per coin, win rate, fees/funding, slippage
   stats, per strategy.
6. **Hybrid modulator insight** — per-coin modulator panel in cycle detail
   (multiplier, effective_weight, base→final size delta). Rationale text out of
   scope.

## Architecture

### Frontend

- **Stack**: React 18 + TypeScript + Vite, located at
  `tradingagents/monitor/frontend/`.
- **Build artifact policy**: `npm run build` output (`frontend/dist/`) is
  **committed to the repo**. The VPS needs no Node toolchain; deploy flow
  (tag + rsync/systemd) is unchanged. FastAPI serves `dist/` as static files.
- **Charts**: TradingView `lightweight-charts` v5 (multi-pane: equity pane +
  drawdown pane + optional rolling-Sharpe pane, shared crosshair/time scale)
  for the performance chart; `Recharts` for donuts and small analytic bars.
- **Data layer**: TanStack Query (react-query) — 30s polling, cache, stale
  flags. No router lib; active tab kept in URL hash (parity with old SPA).
- **Auth/UX parity**: existing password gate, GitHub-dark theme, 30s refresh.
- The legacy `static/app.js` SPA is deleted once the React build reaches feature
  parity (same release).

### Backend (FastAPI, read-only)

- **Dual journals**: monitor opens BOTH SQLite journals read-only using existing
  env contract `QUANT_DATA_DIR` / `HYBRID_DATA_DIR` (same envs `/api/compare`
  already uses). Missing hybrid DB ⇒ `hybrid: null` in every payload; UI
  degrades to quant-only. Dev machines work with no creds (journal fallback).
- **Dual exchange clients**: second `ExchangeClient` constructed from the hybrid
  account credentials (same config source as `hybrid_runner` /
  `load_hybrid_account`) for live positions/uPnL; 30s TTL cache per account,
  journal-snapshot fallback with stale badge (existing v2.3.1 pattern).

### Endpoints

| Endpoint | Change | Payload essentials |
|---|---|---|
| `GET /api/performance` | extend | per-strategy `{cards{equity, sharpe, maxdd, total_upnl, open_positions}, equity[], drawdown[], rolling_sharpe[]}` for `quant` + `hybrid\|null`; `compare` delta block (reuses `compare_quant_hybrid`); `anchors` from env |
| `GET /api/positions` | new | per-strategy `{positions[{coin, side, qty, entry, mark, leverage, notional, upnl_usd, upnl_pct, liq_price}], totals{upnl, notional, equity}, allocation[{label, usd}], stale, as_of, error}` |
| `GET /api/trades?strategy=` | extend | executions list + analytics `{realized_pnl_per_coin, win_rate, fees_total, funding_total, slippage{mean, p95}, n_trades}` |
| `GET /api/cycles?strategy=` | extend | unchanged shape, source journal switched |
| `GET /api/cycle/{id}?strategy=` | extend | hybrid adds `modulator[{coin, multiplier, effective_weight, base_size, final_size, fallback}]` |
| `GET /api/health` | extend | aggregates quant + hybrid runner JSONL logs, each entry labeled with strategy |
| `GET /api/compare` | keep | as-is |

- **Chart series semantics**: server returns RAW equity series per strategy;
  client rebases both to 100 at the start of the visible range, so the range
  selector re-indexes correctly. Drawdown and rolling Sharpe computed
  server-side (pandas, in `monitor/metrics.py`). Rolling Sharpe omitted until
  ≥30 cycles exist.
- **Anchors**: `TA_MONITOR_ANCHOR_SR_QUANT` (default 3.18, V5 baseline drift
  value) and `TA_MONITOR_ANCHOR_SR_HYBRID` (optional, unset by default) drawn
  as dashed reference lines on the rolling-Sharpe pane and shown as deltas on
  cards.
- **Trade analytics source**: Binance futures income-history API
  (`REALIZED_PNL`, `COMMISSION`, `FUNDING_FEE`) per account, cached 5 min;
  win rate = share of profitable nonzero `REALIZED_PNL` records. Slippage from
  journal `trades.slippage`. Income API unavailable ⇒ analytics block `null`
  with reason, executions table still renders from journal.

### Journal/runner change (only write-path touch)

New additive table:

```sql
CREATE TABLE IF NOT EXISTS modulator_outputs (
  cycle_id TEXT NOT NULL,
  coin TEXT NOT NULL,
  multiplier REAL NOT NULL,
  effective_weight REAL NOT NULL,
  llm_direction TEXT,
  llm_confidence REAL,
  PRIMARY KEY (cycle_id, coin)
);
```

- `journal.log_modulator(...)` + one call in `hybrid_runner` right after
  `extract_modulator_outputs` (hybrid_runner.py:231). When the modulator
  degraded to pure quant `(1.0, 0.0)`, the row is still written so the UI can
  label it "pure quant fallback" honestly.
- Backward compatible: table auto-created; cycles predating it show "n/a" in
  the modulator panel.

## UI structure (layout "C" — lean Performance + dedicated Positions tab)

1. **Performance** — card row (Quant | Hybrid | Δ hybrid−quant) → multi-pane
   chart with range selector → compare table (SR / return / MaxDD / Δ over
   common window).
2. **Positions** (new) — total-uPnL cards per strategy → positions table grouped
   by strategy → two allocation donuts.
3. **Executions** — strategy filter pills (All / Quant / Hybrid) → analytics
   strip (recomputed for filter) → executions table.
4. **Decisions** — cycle picker + strategy toggle; quant view = existing panels
   (predictions, sizing, risk checks, shadow); hybrid view adds modulator panel.
5. **Health** — cycle timeline + pipeline steps + errors for both runners,
   strategy-labeled.

## Error handling

- Per-strategy degradation: any hybrid-side failure (no DB, no creds, API error)
  nulls only the hybrid block; quant rendering unaffected, badge shows reason.
- Live-query failures fall back to journal snapshots with amber STALE badge +
  `as_of` timestamp (existing pattern, now per strategy).
- Income-API analytics failures degrade to journal-only stats with notice.

## Testing

- **Backend**: pytest fixtures build tiny quant+hybrid journals; tests for every
  endpoint shape incl. hybrid-missing degradation; unit tests for rolling
  Sharpe, drawdown, win-rate aggregation.
- **Runner**: unit test that `log_modulator` writes rows incl. fallback case.
- **Frontend**: vitest for pure utils (rebase-to-100, formatters); component
  smoke tests optional.
- **Integration**: FastAPI TestClient asserts built `dist/` is served at `/`.
- Existing 54-test live suite must stay green.

## Open checks (resolve during implementation)

1. Hybrid runner JSONL log filename pattern for `/api/health` labeling.
2. Whether `modulated_position` dict exposes direction/confidence fields worth
   persisting (nullable columns already planned).
3. Hybrid account credential env/config names as consumed by monitor process
   (`load_hybrid_account`).

## Out of scope

- LLM rationale/debate text in the UI.
- Realized-PnL parity vs backtest (weekly parity script owns that).
- Any write/control actions from the monitor (stays read-only).
- Alerting/notifications.
