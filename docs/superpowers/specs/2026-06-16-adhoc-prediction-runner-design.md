# Ad-hoc Prediction Runner — Design Spec

**Date:** 2026-06-16
**Status:** Approved (brainstorming), pending implementation plan
**Target repo:** `TradingAgents` (live-deploy monitor)
**Branch:** `feature/adhoc-prediction-runner`

## 1. Problem & Goal

The live monitor (`tradingagents/monitor/`) is a read-only FastAPI + React dashboard
showing what the *automated* quant and hybrid bots have already decided (from their trade
journals). There is no way to trigger a fresh, on-demand prediction and inspect how it was
reached.

**Goal:** Add a module to the existing monitor that lets a user run an ad-hoc prediction for
a chosen coin + date, pick **quant** or **hybrid**, and study the **final decision** plus all
**partial / intermediate predictions and agent outputs**. Display-only — it must never place a
trade. A future phase may add a "trade from this prediction" action; the design leaves a clean
seam for it but does not build it (YAGNI).

### Success criteria
- From the dashboard, pick coin + date + strategy and click Run.
- Quant run returns a real signal for any date (not a flat CSV-miss fallback).
- Hybrid run streams stage-level progress, then shows every agent's output and the final decision.
- Runs persist and are re-viewable later (the point of "study").
- No code path in the runner can place an order.

## 2. Decisions (settled during brainstorming)

| Fork | Decision |
|---|---|
| Where it lives | Inside the existing monitor web app; display-only, no auto-trade; clean seam for a future trade button |
| Execution model | Background job + poll; stage-level progress; partials revealed as they land |
| Date scope | Any date. Price/OHLCV auto-pulls + caches on demand; quant reuses the live inference path; on-chain degrades-and-warns when not backfilled |
| Server architecture | Subprocess worker + SQLite run-store; runs persist; new dedicated "Run" tab |

## 3. Feasibility findings (from codebase exploration)

- **Quant signal for arbitrary dates:** `get_active_quant_signal` /
  `quant_engine.get_quant_signal` read **precomputed** `preds_lgb_h7.csv` / `preds_lgb_h14.csv`
  only; a missing date returns a **flat** signal. The live bot instead computes a fresh signal
  each cycle via `execution/live/predict.py: build_features_asof()` → checkpoint
  `data/checkpoints/composite_*.pkl` → `predict_pooled()` →
  `strategies/v2_sizing.py: generate_term_structure_signals()`. **The ad-hoc runner reuses this
  live path** (~1–2s/coin) so it produces a real signal for any date. Requires a model
  checkpoint to be present (the live deploy has one).
- **Price/OHLCV:** `dataflows/coingecko_binance.py: _load_crypto_ohlcv()` has a two-layer cache;
  a missing date is fetched from Binance/CoinGecko and appended to the disk cache. True
  on-demand auto-pull; repeat dates are free.
- **Hybrid analysts are point-in-time correct:** `propagate_with_modulator(coin, date)` threads
  `trade_date` to all analyst tools; on-chain summaries mask to `as_of_ts <= trade_date`. No
  look-ahead on historical dates.
- **On-chain gap:** PIT on-chain features come from a pre-backfilled DuckDB/parquet store
  (`data/onchain/`); CoinMetrics is a paid API and is **not** auto-pulled. A date outside the
  backfilled range yields zero/NaN-filled on-chain features (run still completes, mildly
  degraded). The UI surfaces this rather than hiding it.

## 4. Architecture

```
React "Run" tab ──POST /api/adhoc/run──▶ FastAPI (insert run row, spawn worker)
      │                                         │
      │◀──GET /api/adhoc/status/{id}──poll──────┤ (reads adhoc store)
      │                                         ▼
      │                              worker subprocess
      │                              ├─ quant:  build_features_asof + checkpoint + predict_pooled + term-structure sizing
      │                              └─ hybrid: TradingAgentsGraph.propagate_with_modulator (stream per node)
      │                                         │ writes stage progress + each output as it lands
      ▼                                         ▼
  results view  ◀──GET /api/adhoc/result/{id}── adhoc_runs.db (SQLite)
```

Everything the worker needs already exists; the monitor only gains new routes + one tab. The
worker is the source of truth — it writes all state to the store; the API only reads it (plus
the single insert + spawn on `POST /run`).

### Reused engine entry points
- **Quant:** `tradingagents/execution/live/predict.py: build_features_asof()` →
  `data/checkpoints/composite_*.pkl` → `predict_pooled()` →
  `tradingagents/strategies/v2_sizing.py: generate_term_structure_signals()` → `QuantSignal`.
- **Hybrid:** `tradingagents/graph/trading_graph.py:324 propagate_with_modulator(coin, date)` →
  `final_state` containing: `market_report`, `onchain_report`, `prediction_report`,
  `sentiment_report`, `investment_debate_state{bull_history, bear_history, judge_decision}`,
  `factual_report`, `subjective_report`, `regime_reflector_note`, `trader_investment_plan`,
  `modulated_position`, `modulator_narrative`, `risk_debate_state{judge_decision}`,
  `final_trade_decision`.

### One required core touch
Ad-hoc computes the `QuantSignal` on-demand and **injects it** into the hybrid modulation step
(add an optional `quant_signal_override` parameter to the propagate/modulator path), so hybrid
modulates a *real* signal on arbitrary dates instead of the CSV's flat fallback. Implementation
must **first verify how live-hybrid currently sources its signal** and match that exactly, so
ad-hoc hybrid output is at parity with production.

## 5. Backend — `tradingagents/monitor/adhoc/`

A new self-contained package. Four modules, each with one purpose:

### `store.py` — persistence
SQLite at `${DATA_DIR}/adhoc/adhoc_runs.db` (isolated from the trade journals). Two tables:

```
runs(
  run_id TEXT PK, created_ts, coin, date, strategy,        -- strategy: quant|hybrid
  analysts_json, model, status,                            -- status: queued|running|done|error
  stage, progress, error_msg, started_ts, finished_ts, est_cost
)
outputs(
  run_id, key, label, kind, content, ordinal, ts           -- kind: text|json|table
)
```

`outputs.key` values: `quant_signal, sizing, regime, market_report, onchain_report,
prediction_report, sentiment_report, bull, bear, research_manager, factual, subjective,
regime_note, trader, modulator, risk_debate, pm_decision, final`. One row inserted per
partial/final as the worker reaches it.

### `service.py` — pure run logic
- `run_quant(coin, date) -> Iterator[Output]`
- `run_hybrid(coin, date, analysts, model) -> Iterator[Output]`

Wrap the reused entry points and **yield** `(key, label, kind, content)` per stage. Hybrid drives
the graph via `.stream()` to emit per-node progress and capture partials as they land; falls back
to coarse `queued→running→done` progress if streaming is unavailable for a node. Imports only read
fetchers + the graph — **never** `execution.exchange` order methods.

### `worker.py` — subprocess entry
`python -m tradingagents.monitor.adhoc.worker --run <id>`. Loads the run row, calls the matching
service function, writes each yielded output + a stage/progress heartbeat to the store, and sets a
terminal status. Wraps the whole run in try/except → on failure writes `status=error` +
`error_msg`. Inherits the monitor process env (API keys, checkpoints, data dirs).

### `runner.py` — spawn + lock
- `launch(run_id)` spawns the worker with `subprocess.Popen` (fire-and-forget; the store is the
  channel).
- **Single-job lock:** reject a new run while any run is `queued|running` (guard query on the
  `runs` table). Protects the shared Binance IP and LLM budget from concurrent hammering.
- **Stale-run reaper:** a run in `running` with no heartbeat update for N minutes is marked
  `error` (so a killed worker can't wedge the lock).

## 6. API — new routes in `tradingagents/monitor/app.py`

Same HTTP Basic auth as every existing route.

| Route | Method | Returns |
|---|---|---|
| `/api/adhoc/meta` | GET | valid coin universe, default analysts + model, `job_running` bool, on-chain backfill coverage range |
| `/api/adhoc/run` | POST | body `{coin, date, strategy, analysts?, model?}` → `{run_id}`; **409** if a job is already running; **400** on invalid coin/date |
| `/api/adhoc/status/{run_id}` | GET | `{status, stage, progress, est_cost, outputs:[{key,label,kind,ordinal}]}` (keys only — lightweight poll) |
| `/api/adhoc/result/{run_id}` | GET | full run row + all `outputs` with `content` |
| `/api/adhoc/runs` | GET | recent runs, newest first (history list) |

`POST /run` is the only writing route, and it writes only to the isolated `adhoc_runs.db` —
never the trade journal, never the exchange.

## 7. Frontend — new "Run" tab

New `tradingagents/monitor/frontend/src/tabs/RunTab.tsx`, registered as the 6th tab in `App.tsx`
(`#run`). Reuses `components/{Card,Section,Badge}` and the Decisions-tab table style. One view,
three states:

- **Form:** coin dropdown (universe from `/meta`), date picker (default latest), strategy toggle
  `quant|hybrid`. When hybrid: analyst multiselect + model dropdown. Run button.
- **Progress** (polls `/status` ~2s while `queued|running`): stage list with pending/running/done
  badges, progress bar, elapsed timer.
- **Results:**
  - **Headline card:** final direction · position size · PM rating · modulator multiplier +
    effective weight.
  - **Quant block:** Decisions-style tables — predictions (lgb_h7/h14, consensus signal), sizing
    (vol, kelly, leverage, final notional), regime.
  - **Hybrid agent panels** (collapsible, markdown-rendered): each analyst report; **bull vs bear
    side-by-side**; research-manager synthesis; factual/subjective; regime note; trader plan;
    modulator narrative; risk debate; PM decision. Long prose collapses.
  - **Disabled "Trade this prediction" button** — the visible seam for the future execute step
    (no handler yet).
- **History strip:** `/runs` list; clicking reloads a persisted past run's results.

Add `adhocMeta/adhocRun/adhocStatus/adhocResult/adhocRuns` to `api.ts` and
`AdhocRun/AdhocOutput/AdhocMeta/AdhocStatus` to `types.ts`. React Query stops polling on terminal
status. Frontend `dist/` is rebuilt + committed (production serves static files, no Node).

## 8. Defaults & guardrails

- **Model:** default `gpt-4o-mini` (cheap for exploration); selector exposes the production model.
  Estimated cost shown pre-run.
- **Coins:** configured universe (8-coin set) via `/meta`.
- **Analysts:** default `market, onchain, prediction`; **omit `crypto_sentiment` for BTC + ETH**
  (three independent runs converged that it hurts) — toggleable, with a tooltip noting the caveat.
- **Single-job lock:** one ad-hoc run at a time → protects the shared Binance IP + LLM budget;
  `POST /run` → 409, UI disables Run while a job is active.
- **Pre-run confirm (hybrid):** shows estimated cost + "hits live Binance + LLM APIs" + on-chain
  coverage note before firing.
- **On-chain gap:** `/meta` reports backfill coverage; a date outside it shows an "on-chain not
  backfilled (features zeroed)" badge. A one-click backfill trigger is **phase-2 / optional**
  (default = warn + proceed degraded).
- **No-trade guarantee:** the worker imports only read fetchers + the graph, never
  `execution.exchange` order methods. Reuses the OHLCV disk cache so repeat dates cost nothing.

## 9. Error handling

- Worker wraps the run in try/except → terminal `status=error` + `error_msg`.
- Missing checkpoint → explicit "no model checkpoint; run a live cycle first."
- On-demand compute failure → surfaced as an error, **never a silent flat signal**.
- Invalid coin/date → 400 from `/run`.
- Stale-run reaper marks a heartbeat-less `running` job as `error`.
- React Query retries the poll; an unknown `run_id` (404) is surfaced.

## 10. Testing

- **Backend (pytest):** store CRUD; service quant path (mocked checkpoint/predict); service
  hybrid path (mocked `graph.stream`); single-job lock; stale-run reaper; `/meta` coverage calc.
- **API (FastAPI TestClient):** run→status→result lifecycle; 409 on concurrent run; auth enforced;
  **assert zero exchange-order calls** in the worker path.
- **Frontend (Vitest):** RunTab form state; poll→results render; collapsible panels; history
  reload (mirrors existing tab tests).
- **Manual e2e:** one real quant run + one real hybrid run (gpt-4o-mini) on a known date; check
  parity of the numbers against a real journal cycle for the same date.

## 11. Out of scope (future phases)

- Executing a trade from a prediction (the disabled button is the only footprint now).
- One-click on-chain backfill (default is warn-and-degrade).
- Live per-token streaming of agent text (stage-level reveal is enough for now).

## 12. Risks / open items for the plan

- **Quant-signal injection into hybrid:** must verify how live-hybrid sources its signal and match
  it, or ad-hoc hybrid diverges from production. This is the one non-additive core touch.
- **Streaming granularity:** confirm `propagate_with_modulator` can be driven via `graph.stream()`
  to emit per-node progress; if not, fall back to coarse progress + reveal partials at the end.
- **Checkpoint dependency:** ad-hoc quant needs a recent `composite_*.pkl`; document the
  precondition and fail loudly if absent.
- **VPS rate-limit/ban:** if this instance runs on the live VPS, ad-hoc hybrid shares the bot's
  Binance IP; the single-job lock + OHLCV cache mitigate, but heavy use during a live cycle could
  still risk a -1003 ban. Consider gating ad-hoc runs to off-cycle windows in a later phase.
