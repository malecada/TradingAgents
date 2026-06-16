# Ad-hoc prediction runner

Run a **quant** or **hybrid** prediction for a chosen coin + date from the monitor's
**Run** tab and study the final decision plus every agent / partial output.
**Display-only — it never places a trade** (the "Trade this prediction" button is a
disabled future-seam).

## How it works

```
React "Run" tab ──POST /api/adhoc/run──▶ FastAPI (insert run row, spawn worker)
      │                                         │
      │◀──GET /api/adhoc/status/{id}──poll──────┤ (reads adhoc store)
      │                                         ▼
      │                              worker subprocess
      │                              ├─ quant:  build_features → checkpoint → predict_pooled → term-structure sizing
      │                              └─ hybrid: TradingAgentsGraph.propagate_with_modulator
      │                                         │ writes stage progress + each output as it lands
      ▼                                         ▼
  results view  ◀──GET /api/adhoc/result/{id}── adhoc_runs.db (SQLite)
```

The worker reproduces the **live cycle's** prediction path for an arbitrary date by
reusing the production entry points — there is **no engine fork**: `predict.run_predict`
→ `hybrid_compose.stage_quant_preds` → `quant_engine.get_quant_signal` (quant) or
`TradingAgentsGraph.propagate_with_modulator` with `quant_pred_dir` pointed at the staged
CSVs (hybrid, exactly like `hybrid_runner.py`).

## Pieces

| File | Role |
|---|---|
| `store.py` | Read-write SQLite store at `${QUANT_DATA_DIR\|DATA_DIR}/adhoc/adhoc_runs.db` (isolated from the trade journals). `runs` + `outputs` tables. |
| `service.py` | Pure `run_quant` / `run_hybrid` generators that yield `(key, label, kind, content)` per stage. Engine imported lazily as `module.attr`. |
| `worker.py` | Subprocess entry `python -m tradingagents.monitor.adhoc.worker --run <id>`. Drives the generator, writes progress + outputs incrementally, always resolves to `done`/`error`. |
| `runner.py` | `launch(run_id)` spawns the worker; `can_start(conn)` enforces the single-job lock + reaps stale runs. |
| `api.py` | `register_adhoc_routes(app)` — the 5 routes below (the monitor's only writing routes; they touch only `adhoc_runs.db`). |

## Routes

- `GET  /api/adhoc/meta` — coin universe, default analysts/model, `job_running`.
- `POST /api/adhoc/run` — `{coin, date, strategy, analysts?, model?}` → `{run_id}`. 400 on bad coin/strategy/date, 409 if a job is already running.
- `GET  /api/adhoc/status/{id}` — lightweight poll: status/stage/progress + output keys (no content).
- `GET  /api/adhoc/result/{id}` — full run row + all outputs with content.
- `GET  /api/adhoc/runs` — recent runs (history).

All behind the monitor's existing HTTP Basic auth.

## Defaults & guardrails

- **Model:** default `gpt-4o-mini` (cheap for exploration); selectable.
- **Analysts:** default `market, onchain, prediction` — `crypto_sentiment` omitted for BTC/ETH by policy.
- **Single-job lock:** one run at a time (protects the shared Binance IP + LLM budget). A `running` run with no heartbeat for `STALE_SECONDS` (10 min), or a `queued` run whose worker never started, is reaped so the lock can't wedge.
- **Pre-run confirm (hybrid):** the UI warns about cost (~$0.002, gpt-4o-mini) + ~90–120s latency before firing.
- **No-trade:** the package imports no exchange/order code.

## Preconditions & limitations

- **Model checkpoint required.** Both paths need a recent `${data_root}/checkpoints/composite_*.pkl` (features are point-in-time as-of the chosen date; the model is trained as-of-latest, no retrain). Without one the run fails fast with a clear `FileNotFoundError` and `status=error` — produce one by running a live cycle/retrain first.
- **On-chain backfill.** Historical dates outside the backfilled PIT on-chain range get zero/NaN-filled on-chain features (the run still completes). One-click backfill is not built (run the backfill harness manually).
- **Single-job lock is best-effort.** `can_start` + `create_run` are not one atomic transaction; two truly simultaneous POSTs could both pass the check. Acceptable for a single-operator monitor.

## Run it locally

```bash
TA_MONITOR_PASSWORD=devpw DATA_DIR=data LOG_DIR=logs python -m tradingagents.monitor
# open http://127.0.0.1:8800/#run  (user: admin)
```
