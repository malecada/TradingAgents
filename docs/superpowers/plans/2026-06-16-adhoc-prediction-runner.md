# Ad-hoc Prediction Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Commits:** end every commit message with the standard trailer:
> `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

**Goal:** Add a module to the existing live monitor that runs an on-demand quant or hybrid prediction for a chosen coin + date and lets the user study the final decision plus every partial/agent output — display-only, no trade.

**Architecture:** A new `tradingagents/monitor/adhoc/` package: a read-write SQLite run-store, a pure service that reproduces the live cycle's predict→stage→(quant signal | modulator graph) path for an arbitrary date, a subprocess worker that writes progress + outputs incrementally, and a single-job lock. Five new read/write FastAPI routes on the existing `create_app` factory, and a new React "Run" tab that polls status and renders results, reusing existing components.

**Tech Stack:** Python 3.9+ (FastAPI, sqlite3, subprocess), React 19 + Vite + TanStack Query (TypeScript), pytest + Vitest.

**Spec:** `docs/superpowers/specs/2026-06-16-adhoc-prediction-runner-design.md`

**Key reused entry points (verbatim-verified):**
- `tradingagents/execution/live/config.py: load_config()` → `cfg.coin_universe`, `cfg.routing`, `cfg.horizons`, `cfg.data_root`
- `tradingagents/execution/live/predict.py: run_predict(coin_universe, routing, ckpt_path, asof, store_root, ohlcv_cache, horizons) -> pd.DataFrame` (cols: `coin, horizon, prediction, ref_price, bundle_route`)
- `tradingagents/execution/live/hybrid_compose.py: stage_quant_preds(rows, *, date, out_dir) -> Path`, `build_hybrid_config(*, quant_pred_dir) -> dict`, `extract_modulator_outputs(mp) -> (mult, eff_w)`, `HYBRID_ANALYSTS = ["market","onchain","prediction"]`
- `tradingagents/strategies/quant_engine.py: get_quant_signal(coin, date, base_dir=None) -> QuantSignal` (reads `preds_lgb_h{7,14}.csv` from `base_dir`)
- `tradingagents/graph/trading_graph.py: TradingAgentsGraph(selected_analysts, debug, config, callbacks).propagate_with_modulator(coin, date) -> (final_state, modulated_position, quant_signal, narrative)`
- `QuantSignal` fields: `coin, direction, magnitude, regime, regime_confidence, hurst, deterministic_signals, as_of_date`
- `final_state` keys: `market_report, onchain_report, prediction_report, investment_debate_state{bull_history,bear_history,judge_decision}, trader_investment_plan, risk_debate_state{judge_decision}, final_trade_decision, modulated_position, quant_signal, modulator_narrative`

**Design notes baked in:**
- **No engine modification.** Ad-hoc stages quant preds to CSV and points the graph's `quant_pred_dir` at them — exactly like `hybrid_runner.py`. The modulator reads the staged signal; no `quant_signal_override` param is added.
- **Checkpoint:** ad-hoc uses the newest existing `data/checkpoints/composite_*.pkl` (no retrain). Features are PIT-as-of-date; the model is trained as-of-latest. For historical dates this is acceptable for study; the UI surfaces a note. (Future: optional retrain-as-of-date.)
- **Single coin per run:** `run_predict` is called with `coin_universe=[coin]` (uses that coin's routing pool) for speed.
- **Hybrid progress is coarse** (compute → "running agents (~90s)" → results burst). Per-node streaming is out of scope (spec §11).

---

## Phase 1 — Backend run-store

### Task 1: Create the `adhoc` package + run-store schema and CRUD

**Files:**
- Create: `tradingagents/monitor/adhoc/__init__.py`
- Create: `tradingagents/monitor/adhoc/store.py`
- Test: `tests/monitor/adhoc/__init__.py` (empty), `tests/monitor/adhoc/test_store.py`

- [ ] **Step 1: Write the failing test**

Create `tests/monitor/adhoc/__init__.py` (empty file) and `tests/monitor/adhoc/test_store.py`:

```python
from __future__ import annotations

import time

import pytest

from tradingagents.monitor.adhoc import store


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    c = store.connect()
    yield c
    c.close()


def test_create_and_get_run(conn):
    rid = store.create_run(conn, coin="bitcoin", date="2026-05-01",
                           strategy="quant", analysts=["market"], model="gpt-4o-mini")
    run = store.get_run(conn, rid)
    assert run["coin"] == "bitcoin"
    assert run["strategy"] == "quant"
    assert run["status"] == "queued"
    assert run["analysts"] == ["market"]  # decoded from analysts_json


def test_add_and_get_outputs(conn):
    rid = store.create_run(conn, coin="bitcoin", date="2026-05-01",
                           strategy="quant", analysts=[], model="m")
    store.add_output(conn, rid, key="quant_signal", label="Quant signal",
                     kind="json", content={"direction": "long"}, ordinal=0)
    store.add_output(conn, rid, key="note", label="Note", kind="text",
                     content="hello", ordinal=1)
    outs = store.get_outputs(conn, rid)
    assert [o["key"] for o in outs] == ["quant_signal", "note"]
    assert outs[0]["content"] == {"direction": "long"}   # json decoded
    assert outs[1]["content"] == "hello"


def test_set_status_and_heartbeat(conn):
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    store.set_status(conn, rid, "running", started_ts=time.time())
    store.heartbeat(conn, rid, stage="working", progress=0.5)
    run = store.get_run(conn, rid)
    assert run["status"] == "running"
    assert run["stage"] == "working"
    assert run["progress"] == 0.5
    assert run["heartbeat_ts"] is not None


def test_active_run_lock(conn):
    assert store.active_run(conn) is None
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    assert store.active_run(conn)["run_id"] == rid
    store.set_status(conn, rid, "done")
    assert store.active_run(conn) is None


def test_list_runs_newest_first(conn):
    r1 = store.create_run(conn, coin="b", date="d", strategy="quant",
                          analysts=[], model="m")
    r2 = store.create_run(conn, coin="e", date="d", strategy="hybrid",
                          analysts=[], model="m")
    runs = store.list_runs(conn, limit=10)
    assert [r["run_id"] for r in runs[:2]] == [r2, r1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/malecada/master_thesis/TradingAgents && python -m pytest tests/monitor/adhoc/test_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.monitor.adhoc'`

- [ ] **Step 3: Write minimal implementation**

Create `tradingagents/monitor/adhoc/__init__.py` (empty file).

Create `tradingagents/monitor/adhoc/store.py`:

```python
# tradingagents/monitor/adhoc/store.py
"""Read-write SQLite store for ad-hoc prediction runs.

Isolated from the trade journals (its own db file). The worker writes; the
API reads. One row per run in `runs`, one row per partial/final in `outputs`.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, created_ts REAL, coin TEXT, date TEXT, strategy TEXT,
  analysts_json TEXT, model TEXT, status TEXT, stage TEXT, progress REAL,
  error_msg TEXT, started_ts REAL, finished_ts REAL, est_cost REAL, heartbeat_ts REAL
);
CREATE TABLE IF NOT EXISTS outputs (
  run_id TEXT, key TEXT, label TEXT, kind TEXT, content TEXT, ordinal INTEGER, ts REAL
);
CREATE INDEX IF NOT EXISTS idx_outputs_run ON outputs(run_id, ordinal);
"""

_RUN_COLS = ("run_id", "created_ts", "coin", "date", "strategy", "analysts_json",
             "model", "status", "stage", "progress", "error_msg", "started_ts",
             "finished_ts", "est_cost", "heartbeat_ts")


def db_path() -> Path:
    data_dir = Path(os.environ.get("QUANT_DATA_DIR", os.environ.get("DATA_DIR", "data")))
    out = data_dir / "adhoc"
    out.mkdir(parents=True, exist_ok=True)
    return out / "adhoc_runs.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path()))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _run_to_dict(row: sqlite3.Row) -> dict:
    d = {k: row[k] for k in _RUN_COLS}
    d["analysts"] = json.loads(d.pop("analysts_json") or "[]")
    return d


def create_run(conn, *, coin, date, strategy, analysts, model, est_cost=0.0) -> str:
    run_id = uuid.uuid4().hex[:12]
    conn.execute(
        "INSERT INTO runs (run_id, created_ts, coin, date, strategy, analysts_json, "
        "model, status, stage, progress, est_cost) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', 'queued', 0.0, ?)",
        (run_id, time.time(), coin, date, strategy, json.dumps(analysts), model, est_cost),
    )
    conn.commit()
    return run_id


def set_status(conn, run_id, status, **fields) -> None:
    cols = ["status = ?"]
    vals = [status]
    for k, v in fields.items():
        cols.append(f"{k} = ?")
        vals.append(v)
    vals.append(run_id)
    conn.execute(f"UPDATE runs SET {', '.join(cols)} WHERE run_id = ?", vals)
    conn.commit()


def heartbeat(conn, run_id, *, stage, progress) -> None:
    conn.execute(
        "UPDATE runs SET stage = ?, progress = ?, heartbeat_ts = ? WHERE run_id = ?",
        (stage, progress, time.time(), run_id),
    )
    conn.commit()


def add_output(conn, run_id, *, key, label, kind, content, ordinal) -> None:
    stored = json.dumps(content) if kind == "json" else str(content)
    conn.execute(
        "INSERT INTO outputs (run_id, key, label, kind, content, ordinal, ts) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_id, key, label, kind, stored, ordinal, time.time()),
    )
    conn.commit()


def get_run(conn, run_id) -> dict | None:
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    return _run_to_dict(row) if row else None


def get_outputs(conn, run_id) -> list[dict]:
    rows = conn.execute(
        "SELECT key, label, kind, content, ordinal, ts FROM outputs "
        "WHERE run_id = ? ORDER BY ordinal", (run_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if d["kind"] == "json":
            d["content"] = json.loads(d["content"])
        out.append(d)
    return out


def list_runs(conn, limit=50) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY created_ts DESC LIMIT ?", (limit,)).fetchall()
    return [_run_to_dict(r) for r in rows]


def active_run(conn) -> dict | None:
    row = conn.execute(
        "SELECT * FROM runs WHERE status IN ('queued', 'running') "
        "ORDER BY created_ts DESC LIMIT 1").fetchone()
    return _run_to_dict(row) if row else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/monitor/adhoc/test_store.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/adhoc/__init__.py tradingagents/monitor/adhoc/store.py tests/monitor/adhoc/
git commit -m "feat(monitor): ad-hoc run-store (SQLite CRUD + single-job lock)"
```

---

## Phase 2 — Backend prediction service

### Task 2: Quant service path (compute → stage → QuantSignal)

**Files:**
- Create: `tradingagents/monitor/adhoc/service.py`
- Test: `tests/monitor/adhoc/test_service_quant.py`

- [ ] **Step 1: Write the failing test**

Create `tests/monitor/adhoc/test_service_quant.py`:

```python
from __future__ import annotations

import types

import pandas as pd
import pytest

from tradingagents.monitor.adhoc import service


class _FakeSignal:
    def model_dump(self):
        return {"coin": "bitcoin", "direction": "long", "magnitude": 0.42,
                "regime": "bull", "regime_confidence": 0.7, "hurst": 0.55,
                "deterministic_signals": {"lgb_h7": 0.01}, "as_of_date": "2026-05-01"}
    direction = "long"
    magnitude = 0.42
    regime = "bull"


@pytest.fixture
def patched(tmp_path, monkeypatch):
    # fake live config
    cfg = types.SimpleNamespace(
        coin_universe=["bitcoin", "ethereum"],
        routing={"bitcoin": {"feature_set": "78f", "pool": ["bitcoin", "ethereum"]}},
        horizons=[7, 14], data_root=str(tmp_path))
    monkeypatch.setattr("tradingagents.execution.live.config.load_config", lambda: cfg)
    # fake checkpoint
    ckpt_dir = tmp_path / "checkpoints"
    ckpt_dir.mkdir()
    (ckpt_dir / "composite_20260501.pkl").write_text("x")
    # fake run_predict
    df = pd.DataFrame([
        {"coin": "bitcoin", "horizon": 7, "prediction": 0.011, "ref_price": 60000.0,
         "bundle_route": "78f"},
        {"coin": "bitcoin", "horizon": 14, "prediction": 0.020, "ref_price": 60000.0,
         "bundle_route": "78f"},
    ])
    monkeypatch.setattr("tradingagents.execution.live.predict.run_predict",
                        lambda **kw: df)
    # capture staging + return a dir; bypass real CSV write
    staged_dir = tmp_path / "staged"
    staged_dir.mkdir()
    monkeypatch.setattr(
        "tradingagents.execution.live.hybrid_compose.stage_quant_preds",
        lambda rows, *, date, out_dir: staged_dir)
    monkeypatch.setattr("tradingagents.strategies.quant_engine.get_quant_signal",
                        lambda coin, date, base_dir=None: _FakeSignal())
    return cfg


def test_run_quant_yields_signal_and_final(patched):
    outs = list(service.run_quant(coin="bitcoin", date="2026-05-01", run_id="r1"))
    keys = [k for (k, _l, _kind, _c) in outs]
    assert "quant_signal" in keys
    assert "final" in keys
    final = [c for (k, _l, _kind, c) in outs if k == "final"][0]
    assert final["direction"] == "long"
    assert final["magnitude"] == 0.42


def test_run_quant_errors_on_empty_preds(patched, monkeypatch):
    monkeypatch.setattr("tradingagents.execution.live.predict.run_predict",
                        lambda **kw: __import__("pandas").DataFrame())
    with pytest.raises(RuntimeError, match="no prediction"):
        list(service.run_quant(coin="bitcoin", date="2026-05-01", run_id="r1"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/monitor/adhoc/test_service_quant.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.monitor.adhoc.service'`

- [ ] **Step 3: Write minimal implementation**

Create `tradingagents/monitor/adhoc/service.py`:

```python
# tradingagents/monitor/adhoc/service.py
"""Pure ad-hoc prediction logic. Reproduces the live cycle's predict path for
an arbitrary date, yielding (key, label, kind, content) tuples per stage.

Engine modules are imported lazily and referenced as `module.attr` so tests can
monkeypatch the source symbols. A yield with kind == "progress" is a stage
marker only (the worker updates progress; it is not stored as an output).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple

Output = Tuple[str, str, str, object]   # (key, label, kind, content)


def _staging_root(data_root: str, run_id: str) -> Path:
    return Path(data_root) / "adhoc" / run_id


def _latest_checkpoint(data_root: str) -> Path:
    ckpt_dir = Path(data_root) / "checkpoints"
    cands = sorted(ckpt_dir.glob("composite_*.pkl"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not cands:
        raise FileNotFoundError(
            f"no composite_*.pkl checkpoint in {ckpt_dir}; run a live cycle first")
    return cands[0]


def _compute_and_stage(cfg, coin: str, date: str, run_id: str) -> Path:
    """run_predict for the single coin + stage CSVs the engine can read back."""
    from tradingagents.execution.live import predict
    from tradingagents.execution.live import hybrid_compose

    preds_df = predict.run_predict(
        coin_universe=[coin],
        routing=cfg.routing,
        ckpt_path=_latest_checkpoint(cfg.data_root),
        asof=date,
        store_root=Path(cfg.data_root) / "onchain",
        ohlcv_cache=Path(cfg.data_root) / "cache",
        horizons=cfg.horizons,
    )
    if preds_df is None or len(preds_df) == 0:
        raise RuntimeError(f"no prediction produced for {coin} @ {date}")
    rows = preds_df[["coin", "horizon", "prediction", "ref_price"]].to_dict("records")
    staged = _staging_root(cfg.data_root, run_id) / "cycle_preds" / date
    return hybrid_compose.stage_quant_preds(rows, date=date, out_dir=staged)


def run_quant(*, coin: str, date: str, run_id: str) -> Iterator[Output]:
    from tradingagents.execution.live import config as live_config
    from tradingagents.strategies import quant_engine

    yield ("_p", "Computing quant signal", "progress", "")
    cfg = live_config.load_config()
    staged = _compute_and_stage(cfg, coin, date, run_id)
    sig = quant_engine.get_quant_signal(coin, date, base_dir=str(staged))
    yield ("quant_signal", "Quant signal", "json", sig.model_dump())
    yield ("final", "Final decision", "json", {
        "strategy": "quant", "direction": sig.direction, "magnitude": sig.magnitude,
        "regime": sig.regime})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/monitor/adhoc/test_service_quant.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/adhoc/service.py tests/monitor/adhoc/test_service_quant.py
git commit -m "feat(monitor): ad-hoc quant service (run_predict + stage + QuantSignal)"
```

---

### Task 3: Hybrid service path (modulator graph + agent partials)

**Files:**
- Modify: `tradingagents/monitor/adhoc/service.py` (add `run_hybrid`)
- Test: `tests/monitor/adhoc/test_service_hybrid.py`

- [ ] **Step 1: Write the failing test**

Create `tests/monitor/adhoc/test_service_hybrid.py`:

```python
from __future__ import annotations

import types

import pandas as pd
import pytest

from tradingagents.monitor.adhoc import service


class _FakeGraph:
    def __init__(self, **kw):
        self.kw = kw

    def propagate_with_modulator(self, coin, date):
        final_state = {
            "market_report": "MKT report text",
            "onchain_report": "ONCHAIN report text",
            "prediction_report": "PRED report text",
            "investment_debate_state": {
                "bull_history": "bull says buy",
                "bear_history": "bear says sell",
                "judge_decision": "manager: lean buy"},
            "trader_investment_plan": "trader: BUY 0.5",
            "risk_debate_state": {"judge_decision": "risk: ok"},
            "final_trade_decision": "OVERWEIGHT",
            "modulated_position": {"llm_multiplier": 1.2, "effective_weight": 0.3,
                                   "llm_confidence": 0.8, "regime": "bull"},
            "modulator_narrative": "scaled up on bull regime",
        }
        mp = final_state["modulated_position"]
        return final_state, mp, {"direction": "long"}, "scaled up on bull regime"


@pytest.fixture
def patched(tmp_path, monkeypatch):
    cfg = types.SimpleNamespace(
        coin_universe=["bitcoin"], routing={"bitcoin": {"pool": ["bitcoin"]}},
        horizons=[7, 14], data_root=str(tmp_path))
    monkeypatch.setattr("tradingagents.execution.live.config.load_config", lambda: cfg)
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "checkpoints" / "composite_x.pkl").write_text("x")
    df = pd.DataFrame([
        {"coin": "bitcoin", "horizon": 7, "prediction": 0.01, "ref_price": 60000.0},
        {"coin": "bitcoin", "horizon": 14, "prediction": 0.02, "ref_price": 60000.0}])
    monkeypatch.setattr("tradingagents.execution.live.predict.run_predict",
                        lambda **kw: df)
    monkeypatch.setattr(
        "tradingagents.execution.live.hybrid_compose.stage_quant_preds",
        lambda rows, *, date, out_dir: tmp_path / "staged")
    monkeypatch.setattr(
        "tradingagents.execution.live.hybrid_compose.build_hybrid_config",
        lambda *, quant_pred_dir: {"deep_think_llm": "gpt-4o-mini",
                                   "quick_think_llm": "gpt-4o-mini"})
    monkeypatch.setattr("tradingagents.graph.trading_graph.TradingAgentsGraph",
                        _FakeGraph)
    return cfg


def test_run_hybrid_emits_all_partials(patched):
    outs = list(service.run_hybrid(coin="bitcoin", date="2026-05-01",
                                   analysts=["market", "onchain", "prediction"],
                                   model="gpt-4o-mini", run_id="r1"))
    keys = [k for (k, _l, _kind, _c) in outs]
    for expected in ["market_report", "onchain_report", "prediction_report",
                     "bull", "bear", "research_manager", "trader", "risk_debate",
                     "modulator", "pm_decision", "final"]:
        assert expected in keys, expected
    final = [c for (k, _l, _kind, c) in outs if k == "final"][0]
    assert final["pm"] == "OVERWEIGHT"
    assert final["multiplier"] == 1.2


def test_run_hybrid_applies_model_override(patched, monkeypatch):
    captured = {}
    orig = _FakeGraph

    class _Capture(_FakeGraph):
        def __init__(self, **kw):
            captured.update(kw)
            super().__init__(**kw)

    monkeypatch.setattr("tradingagents.graph.trading_graph.TradingAgentsGraph",
                        _Capture)
    list(service.run_hybrid(coin="bitcoin", date="2026-05-01",
                            analysts=["market"], model="gpt-4o", run_id="r1"))
    assert captured["config"]["deep_think_llm"] == "gpt-4o"
    assert captured["config"]["quick_think_llm"] == "gpt-4o"
    assert captured["selected_analysts"] == ["market"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/monitor/adhoc/test_service_hybrid.py -v`
Expected: FAIL with `AttributeError: module ... has no attribute 'run_hybrid'`

- [ ] **Step 3: Write minimal implementation**

Append to `tradingagents/monitor/adhoc/service.py`:

```python
_REPORT_KEYS = [
    ("market_report", "Market analyst"),
    ("onchain_report", "On-chain analyst"),
    ("prediction_report", "Prediction analyst"),
    ("sentiment_report", "Sentiment analyst"),
]


def run_hybrid(*, coin: str, date: str, analysts, model: str | None,
               run_id: str) -> Iterator[Output]:
    from tradingagents.execution.live import config as live_config
    from tradingagents.execution.live import hybrid_compose
    from tradingagents.graph import trading_graph

    yield ("_p", "Computing quant base", "progress", "")
    cfg = live_config.load_config()
    staged = _compute_and_stage(cfg, coin, date, run_id)

    gcfg = hybrid_compose.build_hybrid_config(quant_pred_dir=str(staged))
    if model:
        gcfg["deep_think_llm"] = model
        gcfg["quick_think_llm"] = model

    yield ("_p", "Running agent graph (~90s)", "progress", "")
    graph = trading_graph.TradingAgentsGraph(
        selected_analysts=list(analysts) if analysts else list(hybrid_compose.HYBRID_ANALYSTS),
        config=gcfg)
    final_state, mp, _qs, narrative = graph.propagate_with_modulator(coin, date)

    for key, label in _REPORT_KEYS:
        text = final_state.get(key)
        if text:
            yield (key, label, "text", text)

    debate = final_state.get("investment_debate_state", {}) or {}
    if debate.get("bull_history"):
        yield ("bull", "Bull researcher", "text", debate["bull_history"])
    if debate.get("bear_history"):
        yield ("bear", "Bear researcher", "text", debate["bear_history"])
    if debate.get("judge_decision"):
        yield ("research_manager", "Research manager", "text", debate["judge_decision"])

    if final_state.get("trader_investment_plan"):
        yield ("trader", "Trader plan", "text", final_state["trader_investment_plan"])

    risk = final_state.get("risk_debate_state", {}) or {}
    if risk.get("judge_decision"):
        yield ("risk_debate", "Risk debate", "text", risk["judge_decision"])

    mult, eff_w = hybrid_compose.extract_modulator_outputs(mp)
    yield ("modulator", "Modulator", "json", {
        "multiplier": mult, "effective_weight": eff_w, "narrative": narrative,
        "modulated_position": mp})

    if final_state.get("final_trade_decision"):
        yield ("pm_decision", "Portfolio manager", "text",
               final_state["final_trade_decision"])

    yield ("final", "Final decision", "json", {
        "strategy": "hybrid", "pm": final_state.get("final_trade_decision"),
        "multiplier": mult, "effective_weight": eff_w, "modulated_position": mp})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/monitor/adhoc/test_service_hybrid.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/adhoc/service.py tests/monitor/adhoc/test_service_hybrid.py
git commit -m "feat(monitor): ad-hoc hybrid service (modulator graph + agent partials)"
```

---

## Phase 3 — Worker + launcher

### Task 4: Worker subprocess entry

**Files:**
- Create: `tradingagents/monitor/adhoc/worker.py`
- Test: `tests/monitor/adhoc/test_worker.py`

- [ ] **Step 1: Write the failing test**

Create `tests/monitor/adhoc/test_worker.py`:

```python
from __future__ import annotations

import pytest

from tradingagents.monitor.adhoc import store, worker


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    c = store.connect()
    yield c
    c.close()


def test_worker_runs_generator_and_marks_done(conn, monkeypatch):
    rid = store.create_run(conn, coin="bitcoin", date="2026-05-01",
                           strategy="quant", analysts=[], model="m")

    def fake_quant(*, coin, date, run_id):
        yield ("_p", "working", "progress", "")
        yield ("quant_signal", "Quant signal", "json", {"direction": "long"})
        yield ("final", "Final decision", "json", {"direction": "long"})

    monkeypatch.setattr("tradingagents.monitor.adhoc.service.run_quant", fake_quant)
    worker.execute(rid)

    run = store.get_run(conn, rid)
    assert run["status"] == "done"
    assert run["progress"] == 1.0
    outs = store.get_outputs(conn, rid)
    keys = [o["key"] for o in outs]
    assert keys == ["quant_signal", "final"]          # progress marker not stored


def test_worker_records_error(conn, monkeypatch):
    rid = store.create_run(conn, coin="bitcoin", date="2026-05-01",
                           strategy="quant", analysts=[], model="m")

    def boom(*, coin, date, run_id):
        raise RuntimeError("kaboom")
        yield  # pragma: no cover

    monkeypatch.setattr("tradingagents.monitor.adhoc.service.run_quant", boom)
    worker.execute(rid)

    run = store.get_run(conn, rid)
    assert run["status"] == "error"
    assert "kaboom" in run["error_msg"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/monitor/adhoc/test_worker.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.monitor.adhoc.worker'`

- [ ] **Step 3: Write minimal implementation**

Create `tradingagents/monitor/adhoc/worker.py`:

```python
# tradingagents/monitor/adhoc/worker.py
"""Subprocess entry: ``python -m tradingagents.monitor.adhoc.worker --run <id>``.

Loads a run row, drives the matching service generator, and writes progress +
outputs incrementally. Never raises out of execute(): a failure is recorded as
status=error on the run.
"""
from __future__ import annotations

import argparse
import time

from tradingagents.monitor.adhoc import service, store


def execute(run_id: str) -> None:
    conn = store.connect()
    try:
        run = store.get_run(conn, run_id)
        if run is None:
            return
        store.set_status(conn, run_id, "running", started_ts=time.time(),
                         stage="starting", progress=0.0)
        store.heartbeat(conn, run_id, stage="starting", progress=0.0)

        if run["strategy"] == "hybrid":
            gen = service.run_hybrid(coin=run["coin"], date=run["date"],
                                     analysts=run["analysts"], model=run["model"],
                                     run_id=run_id)
        else:
            gen = service.run_quant(coin=run["coin"], date=run["date"], run_id=run_id)

        ordinal = 0
        for key, label, kind, content in gen:
            if kind == "progress":
                store.heartbeat(conn, run_id, stage=label, progress=run["progress"] or 0.1)
                continue
            store.add_output(conn, run_id, key=key, label=label, kind=kind,
                             content=content, ordinal=ordinal)
            ordinal += 1
            store.heartbeat(conn, run_id, stage=label, progress=0.5)

        store.set_status(conn, run_id, "done", finished_ts=time.time(),
                         stage="done", progress=1.0)
    except Exception as exc:  # noqa: BLE001 — terminal error is the contract
        store.set_status(conn, run_id, "error", finished_ts=time.time(),
                         error_msg=f"{type(exc).__name__}: {exc}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    execute(args.run)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/monitor/adhoc/test_worker.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/adhoc/worker.py tests/monitor/adhoc/test_worker.py
git commit -m "feat(monitor): ad-hoc worker (incremental progress + terminal status)"
```

---

### Task 5: Launcher with single-job lock + stale reaper

**Files:**
- Create: `tradingagents/monitor/adhoc/runner.py`
- Test: `tests/monitor/adhoc/test_runner.py`

- [ ] **Step 1: Write the failing test**

Create `tests/monitor/adhoc/test_runner.py`:

```python
from __future__ import annotations

import time

import pytest

from tradingagents.monitor.adhoc import runner, store


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    c = store.connect()
    yield c
    c.close()


def test_can_start_when_idle(conn):
    ok, blocker = runner.can_start(conn)
    assert ok is True and blocker is None


def test_blocked_when_active(conn):
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    store.set_status(conn, rid, "running", heartbeat_ts=time.time())
    ok, blocker = runner.can_start(conn)
    assert ok is False and blocker == rid


def test_stale_run_reaped(conn, monkeypatch):
    rid = store.create_run(conn, coin="b", date="d", strategy="quant",
                           analysts=[], model="m")
    store.set_status(conn, rid, "running",
                     heartbeat_ts=time.time() - runner.STALE_SECONDS - 1)
    ok, blocker = runner.can_start(conn)
    assert ok is True and blocker is None
    assert store.get_run(conn, rid)["status"] == "error"


def test_launch_spawns_worker(conn, monkeypatch):
    calls = {}
    monkeypatch.setattr(runner.subprocess, "Popen",
                        lambda argv, **kw: calls.setdefault("argv", argv))
    runner.launch("abc123")
    assert "tradingagents.monitor.adhoc.worker" in calls["argv"]
    assert "abc123" in calls["argv"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/monitor/adhoc/test_runner.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.monitor.adhoc.runner'`

- [ ] **Step 3: Write minimal implementation**

Create `tradingagents/monitor/adhoc/runner.py`:

```python
# tradingagents/monitor/adhoc/runner.py
"""Spawn the ad-hoc worker subprocess and enforce a single-job lock.

One run at a time protects the shared Binance IP and LLM budget. A run stuck in
`running` with no heartbeat for STALE_SECONDS is reaped to `error` so a killed
worker cannot wedge the lock.
"""
from __future__ import annotations

import subprocess
import sys
import time

STALE_SECONDS = 600  # 10 min without a heartbeat → reap (spec §12)


def can_start(conn) -> tuple[bool, str | None]:
    from tradingagents.monitor.adhoc import store
    active = store.active_run(conn)
    if active and active["status"] == "running":
        hb = active.get("heartbeat_ts")
        if hb is not None and (time.time() - hb) > STALE_SECONDS:
            store.set_status(conn, active["run_id"], "error",
                             finished_ts=time.time(),
                             error_msg="stale: no heartbeat")
            active = None
    if active is not None:
        return False, active["run_id"]
    return True, None


def launch(run_id: str) -> None:
    subprocess.Popen(
        [sys.executable, "-m", "tradingagents.monitor.adhoc.worker", "--run", run_id])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/monitor/adhoc/test_runner.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/adhoc/runner.py tests/monitor/adhoc/test_runner.py
git commit -m "feat(monitor): ad-hoc launcher with single-job lock + stale reaper"
```

---

## Phase 4 — API routes

### Task 6: Meta endpoint + run/status/result/runs routes

**Files:**
- Create: `tradingagents/monitor/adhoc/api.py` (route-registration helper)
- Modify: `tradingagents/monitor/app.py` (call `register_adhoc_routes(app)` inside `create_app`, before the SPA mount)
- Test: `tests/monitor/adhoc/test_api.py`

- [ ] **Step 1: Write the failing test**

Create `tests/monitor/adhoc/test_api.py`:

```python
from __future__ import annotations

import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tradingagents.monitor.adhoc import api, store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    cfg = types.SimpleNamespace(
        coin_universe=["bitcoin", "ethereum"], routing={}, horizons=[7, 14],
        data_root=str(tmp_path))
    monkeypatch.setattr("tradingagents.execution.live.config.load_config", lambda: cfg)
    # never actually spawn a worker in API tests
    monkeypatch.setattr("tradingagents.monitor.adhoc.runner.launch",
                        lambda run_id: None)
    app = FastAPI()
    api.register_adhoc_routes(app)
    return TestClient(app)


def test_meta_lists_coins_and_defaults(client):
    body = client.get("/api/adhoc/meta").json()
    assert body["coins"] == ["bitcoin", "ethereum"]
    assert body["default_model"] == "gpt-4o-mini"
    assert "market" in body["default_analysts"]
    assert body["job_running"] is False


def test_run_creates_and_returns_id(client):
    r = client.post("/api/adhoc/run", json={
        "coin": "bitcoin", "date": "2026-05-01", "strategy": "quant"})
    assert r.status_code == 200
    rid = r.json()["run_id"]
    status = client.get(f"/api/adhoc/status/{rid}").json()
    assert status["status"] == "queued"


def test_run_rejects_unknown_coin(client):
    r = client.post("/api/adhoc/run", json={
        "coin": "dogecoin", "date": "2026-05-01", "strategy": "quant"})
    assert r.status_code == 400


def test_run_conflicts_when_job_active(client):
    client.post("/api/adhoc/run", json={
        "coin": "bitcoin", "date": "2026-05-01", "strategy": "quant"})
    r2 = client.post("/api/adhoc/run", json={
        "coin": "ethereum", "date": "2026-05-01", "strategy": "quant"})
    assert r2.status_code == 409


def test_result_returns_outputs(client):
    rid = client.post("/api/adhoc/run", json={
        "coin": "bitcoin", "date": "2026-05-01", "strategy": "quant"}).json()["run_id"]
    conn = store.connect()
    store.add_output(conn, rid, key="final", label="Final", kind="json",
                     content={"direction": "long"}, ordinal=0)
    conn.close()
    body = client.get(f"/api/adhoc/result/{rid}").json()
    assert body["run"]["coin"] == "bitcoin"
    assert body["outputs"][0]["content"] == {"direction": "long"}


def test_result_404_unknown(client):
    assert client.get("/api/adhoc/result/nope").status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/monitor/adhoc/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tradingagents.monitor.adhoc.api'`

- [ ] **Step 3: Write minimal implementation**

Create `tradingagents/monitor/adhoc/api.py`:

```python
# tradingagents/monitor/adhoc/api.py
"""Ad-hoc prediction routes, registered onto the monitor's FastAPI app.

The only writing routes in the monitor; they write solely to the isolated
adhoc_runs.db (never the trade journal, never the exchange).
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tradingagents.monitor.adhoc import runner, store

_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_ANALYSTS = ["market", "onchain", "prediction"]
_EST_COST = {"quant": 0.0, "hybrid": 0.002}


class AdhocRunBody(BaseModel):
    coin: str
    date: str
    strategy: str = "quant"
    analysts: list[str] | None = None
    model: str | None = None


def _coin_universe() -> list[str]:
    from tradingagents.execution.live import config as live_config
    return list(live_config.load_config().coin_universe)


def register_adhoc_routes(app: FastAPI) -> None:

    @app.get("/api/adhoc/meta")
    def adhoc_meta():
        conn = store.connect()
        try:
            return {
                "coins": _coin_universe(),
                "default_analysts": _DEFAULT_ANALYSTS,
                "default_model": _DEFAULT_MODEL,
                "job_running": store.active_run(conn) is not None,
            }
        finally:
            conn.close()

    @app.post("/api/adhoc/run")
    def adhoc_run(body: AdhocRunBody):
        if body.coin not in _coin_universe():
            raise HTTPException(status_code=400, detail=f"unknown coin: {body.coin}")
        if body.strategy not in ("quant", "hybrid"):
            raise HTTPException(status_code=400, detail="strategy must be quant|hybrid")
        try:
            import pandas as pd
            pd.Timestamp(body.date)
        except Exception:
            raise HTTPException(status_code=400, detail=f"bad date: {body.date}")
        conn = store.connect()
        try:
            ok, blocker = runner.can_start(conn)
            if not ok:
                raise HTTPException(status_code=409,
                                    detail=f"a run is already active: {blocker}")
            run_id = store.create_run(
                conn, coin=body.coin, date=body.date, strategy=body.strategy,
                analysts=body.analysts or _DEFAULT_ANALYSTS,
                model=body.model or _DEFAULT_MODEL,
                est_cost=_EST_COST.get(body.strategy, 0.0))
        finally:
            conn.close()
        runner.launch(run_id)
        return {"run_id": run_id}

    @app.get("/api/adhoc/status/{run_id}")
    def adhoc_status(run_id: str):
        conn = store.connect()
        try:
            run = store.get_run(conn, run_id)
            if run is None:
                raise HTTPException(status_code=404, detail="unknown run")
            outs = store.get_outputs(conn, run_id)
            return {
                "status": run["status"], "stage": run["stage"],
                "progress": run["progress"], "est_cost": run["est_cost"],
                "error_msg": run["error_msg"],
                "outputs": [{"key": o["key"], "label": o["label"],
                             "kind": o["kind"], "ordinal": o["ordinal"]} for o in outs],
            }
        finally:
            conn.close()

    @app.get("/api/adhoc/result/{run_id}")
    def adhoc_result(run_id: str):
        conn = store.connect()
        try:
            run = store.get_run(conn, run_id)
            if run is None:
                raise HTTPException(status_code=404, detail="unknown run")
            return {"run": run, "outputs": store.get_outputs(conn, run_id)}
        finally:
            conn.close()

    @app.get("/api/adhoc/runs")
    def adhoc_runs():
        conn = store.connect()
        try:
            return {"runs": store.list_runs(conn, limit=50)}
        finally:
            conn.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/monitor/adhoc/test_api.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/adhoc/api.py tests/monitor/adhoc/test_api.py
git commit -m "feat(monitor): ad-hoc API routes (meta/run/status/result/runs)"
```

---

### Task 7: Wire routes into the monitor app factory

**Files:**
- Modify: `tradingagents/monitor/app.py`
- Test: `tests/monitor/adhoc/test_app_wired.py`

- [ ] **Step 1: Write the failing test**

Create `tests/monitor/adhoc/test_app_wired.py`:

```python
from __future__ import annotations

import types

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    monkeypatch.setenv("TA_MONITOR_PASSWORD", "pw")
    cfg = types.SimpleNamespace(coin_universe=["bitcoin"], routing={},
                                horizons=[7, 14], data_root=str(tmp_path))
    monkeypatch.setattr("tradingagents.execution.live.config.load_config", lambda: cfg)
    # minimal quant journal so create_app's StrategySource resolves
    import sqlite3
    jp = tmp_path / "trade_journal.db"
    sqlite3.connect(str(jp)).close()
    from tradingagents.monitor.app import create_app
    from tradingagents.monitor.sources import StrategySource
    src = StrategySource(name="quant", journal_path=str(jp),
                         snapshot=lambda: {"positions": [], "usdt_free": 0.0,
                                           "equity": 0.0, "income": None})
    return create_app(quant=src, hybrid=None, log_dir=str(tmp_path))


def test_adhoc_meta_reachable_with_auth(app):
    c = TestClient(app)
    r = c.get("/api/adhoc/meta", auth=("admin", "pw"))
    assert r.status_code == 200
    assert r.json()["coins"] == ["bitcoin"]


def test_adhoc_meta_requires_auth(app):
    c = TestClient(app)
    assert c.get("/api/adhoc/meta").status_code == 401
```

> If the `StrategySource` constructor signature differs, mirror the construction used in `tests/monitor/conftest.py` instead — match the existing fixture exactly.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/monitor/adhoc/test_app_wired.py -v`
Expected: FAIL — `/api/adhoc/meta` returns 404 (routes not registered yet)

- [ ] **Step 3: Write minimal implementation**

In `tradingagents/monitor/app.py`, add the import near the other monitor imports (top of file):

```python
from tradingagents.monitor.adhoc.api import register_adhoc_routes
```

Inside `create_app(...)`, register the routes after the auth middleware is defined and **before** the React SPA mount (`if _DIST.is_dir():`). Add this line:

```python
    # ── ad-hoc prediction routes (only writing routes; isolated adhoc db) ──
    register_adhoc_routes(app)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/monitor/adhoc/test_app_wired.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Run the full monitor suite to confirm no regression**

Run: `python -m pytest tests/monitor/ -v`
Expected: PASS (all existing + new adhoc tests green)

- [ ] **Step 6: Commit**

```bash
git add tradingagents/monitor/app.py tests/monitor/adhoc/test_app_wired.py
git commit -m "feat(monitor): register ad-hoc routes on the app factory"
```

---

## Phase 5 — Frontend

### Task 8: Types + API client functions

**Files:**
- Modify: `tradingagents/monitor/frontend/src/types.ts` (append Adhoc types)
- Modify: `tradingagents/monitor/frontend/src/api.ts` (add `post` helper + adhoc fns)
- Test: `tradingagents/monitor/frontend/src/api.adhoc.test.ts`

- [ ] **Step 1: Write the failing test**

Create `tradingagents/monitor/frontend/src/api.adhoc.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

afterEach(() => vi.restoreAllMocks());

describe("adhoc api", () => {
  it("adhocRun posts body as JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ run_id: "abc" }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const r = await api.adhocRun({ coin: "bitcoin", date: "2026-05-01", strategy: "quant" });
    expect(r.run_id).toBe("abc");
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/adhoc/run");
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body)).toMatchObject({ coin: "bitcoin", strategy: "quant" });
  });

  it("adhocStatus GETs the run id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true, json: async () => ({ status: "done", outputs: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const r = await api.adhocStatus("abc");
    expect(r.status).toBe("done");
    expect(fetchMock.mock.calls[0][0]).toBe("/api/adhoc/status/abc");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/malecada/master_thesis/TradingAgents/tradingagents/monitor/frontend && npm run test -- api.adhoc`
Expected: FAIL — `api.adhocRun is not a function`

- [ ] **Step 3: Write minimal implementation**

Append to `tradingagents/monitor/frontend/src/types.ts`:

```typescript
export type AdhocStrategy = "quant" | "hybrid";

export interface AdhocMeta {
  coins: string[];
  default_analysts: string[];
  default_model: string;
  job_running: boolean;
}

export interface AdhocRunBody {
  coin: string;
  date: string;
  strategy: AdhocStrategy;
  analysts?: string[];
  model?: string;
}

export interface AdhocOutputMeta {
  key: string; label: string; kind: "text" | "json" | "table"; ordinal: number;
}

export interface AdhocStatus {
  status: "queued" | "running" | "done" | "error";
  stage: string | null; progress: number | null; est_cost: number | null;
  error_msg: string | null; outputs: AdhocOutputMeta[];
}

export interface AdhocOutput {
  key: string; label: string; kind: "text" | "json" | "table";
  content: unknown; ordinal: number; ts: number;
}

export interface AdhocRunRow {
  run_id: string; created_ts: number; coin: string; date: string;
  strategy: AdhocStrategy; model: string; status: string;
  stage: string | null; error_msg: string | null; est_cost: number | null;
}

export interface AdhocResult { run: AdhocRunRow; outputs: AdhocOutput[]; }
```

Modify `tradingagents/monitor/frontend/src/api.ts`. Add the imports to the existing import block:

```typescript
import type {
  CycleDetail, CycleRow, HealthResp, PerformanceResp, PositionsResp,
  Strategy, TradesResp,
  AdhocMeta, AdhocRunBody, AdhocStatus, AdhocResult, AdhocRunRow,
} from "./types";
```

Add a `post` helper directly below the existing `get` helper:

```typescript
async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json() as Promise<T>;
}
```

Add the adhoc functions inside the `api` object (after `health`):

```typescript
  adhocMeta: () => get<AdhocMeta>("/api/adhoc/meta"),
  adhocRun: (body: AdhocRunBody) => post<{ run_id: string }>("/api/adhoc/run", body),
  adhocStatus: (id: string) =>
    get<AdhocStatus>(`/api/adhoc/status/${encodeURIComponent(id)}`),
  adhocResult: (id: string) =>
    get<AdhocResult>(`/api/adhoc/result/${encodeURIComponent(id)}`),
  adhocRuns: () => get<{ runs: AdhocRunRow[] }>("/api/adhoc/runs"),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- api.adhoc`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/frontend/src/types.ts tradingagents/monitor/frontend/src/api.ts tradingagents/monitor/frontend/src/api.adhoc.test.ts
git commit -m "feat(monitor-ui): adhoc types + api client functions"
```

---

### Task 9: Pure status helper + test

**Files:**
- Create: `tradingagents/monitor/frontend/src/lib/adhoc.ts`
- Test: `tradingagents/monitor/frontend/src/lib/adhoc.test.ts`

- [ ] **Step 1: Write the failing test**

Create `tradingagents/monitor/frontend/src/lib/adhoc.test.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { isTerminal, pollInterval } from "./adhoc";

describe("adhoc status helpers", () => {
  it("isTerminal", () => {
    expect(isTerminal("done")).toBe(true);
    expect(isTerminal("error")).toBe(true);
    expect(isTerminal("running")).toBe(false);
    expect(isTerminal("queued")).toBe(false);
  });
  it("pollInterval stops on terminal", () => {
    expect(pollInterval("running")).toBe(2000);
    expect(pollInterval("done")).toBe(false);
    expect(pollInterval(undefined)).toBe(2000);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test -- lib/adhoc`
Expected: FAIL — cannot resolve `./adhoc`

- [ ] **Step 3: Write minimal implementation**

Create `tradingagents/monitor/frontend/src/lib/adhoc.ts`:

```typescript
export function isTerminal(status: string | undefined): boolean {
  return status === "done" || status === "error";
}

/** React Query refetchInterval: poll every 2s until the run is terminal. */
export function pollInterval(status: string | undefined): number | false {
  return isTerminal(status) ? false : 2000;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test -- lib/adhoc`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/frontend/src/lib/adhoc.ts tradingagents/monitor/frontend/src/lib/adhoc.test.ts
git commit -m "feat(monitor-ui): adhoc poll/terminal helpers"
```

---

### Task 10: The Run tab component

**Files:**
- Create: `tradingagents/monitor/frontend/src/tabs/RunTab.tsx`

> No unit test for the component (the frontend has no DOM-testing dep installed; matches the existing pure-function-only test style). It is verified by the build (Task 11) + manual e2e (Task 12).

- [ ] **Step 1: Create the component**

Create `tradingagents/monitor/frontend/src/tabs/RunTab.tsx`:

```typescript
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { Section } from "../components/Section";
import { pollInterval } from "../lib/adhoc";
import type { AdhocOutput, AdhocStrategy } from "../types";

function Panel(props: { o: AdhocOutput }) {
  const { o } = props;
  const text = o.kind === "json"
    ? JSON.stringify(o.content, null, 2)
    : String(o.content ?? "");
  return (
    <details style={{ marginBottom: 8 }}>
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>{o.label}</summary>
      <pre style={{ whiteSpace: "pre-wrap", background: "#161b22",
                    border: "1px solid #30363d", borderRadius: 6, padding: 12,
                    marginTop: 8, overflowX: "auto" }}>{text}</pre>
    </details>
  );
}

export function RunTab() {
  const metaQ = useQuery({ queryKey: ["adhocMeta"], queryFn: api.adhocMeta });
  const meta = metaQ.data;

  const [coin, setCoin] = useState("bitcoin");
  const [date, setDate] = useState("");
  const [strategy, setStrategy] = useState<AdhocStrategy>("quant");
  const [runId, setRunId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const statusQ = useQuery({
    queryKey: ["adhocStatus", runId],
    queryFn: () => api.adhocStatus(runId!),
    enabled: runId !== null,
    refetchInterval: (q) => pollInterval(q.state.data?.status),
  });
  const status = statusQ.data;

  const resultQ = useQuery({
    queryKey: ["adhocResult", runId],
    queryFn: () => api.adhocResult(runId!),
    enabled: runId !== null && status?.status === "done",
  });

  const runsQ = useQuery({ queryKey: ["adhocRuns"], queryFn: api.adhocRuns,
                           refetchInterval: 10_000 });

  async function start() {
    setErr(null);
    if (!date) { setErr("pick a date"); return; }
    if (strategy === "hybrid" &&
        !window.confirm(
          "Hybrid run hits live Binance + LLM APIs and takes ~90–120s " +
          "(est. cost ~$0.002, gpt-4o-mini). Continue?")) return;
    try {
      const { run_id } = await api.adhocRun({ coin, date, strategy });
      setRunId(run_id);
    } catch (e) {
      setErr(String(e));
    }
  }

  const outputs = resultQ.data?.outputs ?? [];
  const final = outputs.find((o) => o.key === "final");
  const finalObj = (final?.content ?? {}) as Record<string, unknown>;
  const busy = status?.status === "queued" || status?.status === "running";

  return (
    <>
      <Section title="Run an ad-hoc prediction">
        <div className="pills" style={{ gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <select value={coin} onChange={(e) => setCoin(e.target.value)}
            style={{ background: "#161b22", color: "#e6edf3",
                     border: "1px solid #30363d", borderRadius: 6, padding: "4px 8px" }}>
            {(meta?.coins ?? ["bitcoin"]).map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
            style={{ background: "#161b22", color: "#e6edf3",
                     border: "1px solid #30363d", borderRadius: 6, padding: "4px 8px" }} />
          {(["quant", "hybrid"] as AdhocStrategy[]).map((s) => (
            <button key={s} className={`pill ${s === strategy ? "active" : ""}`}
              onClick={() => setStrategy(s)}>{s}</button>
          ))}
          <button className="pill active" disabled={busy || meta?.job_running}
            onClick={start}>{busy ? "running…" : "Run"}</button>
          {meta?.job_running && !runId &&
            <Badge kind="stale">another job is running</Badge>}
        </div>
        {err && <p style={{ color: "#f85149" }}>{err}</p>}
        <p className="muted" style={{ marginTop: 8 }}>
          Historical dates use the latest model checkpoint (features are
          point-in-time; model weights are as-of-latest). Display only — no trade
          is placed.
        </p>
      </Section>

      {status && (
        <Section title="Progress" right={
          <Badge kind={status.status === "error" ? "error"
            : status.status === "done" ? "ok" : "stale"}>{status.status}</Badge>}>
          <p>{status.stage ?? "…"}{status.error_msg ? ` — ${status.error_msg}` : ""}</p>
        </Section>
      )}

      {status?.status === "done" && (
        <>
          <Section title="Final decision">
            <div className="cards">
              <Card label="Direction" value={String(finalObj.direction ?? finalObj.pm ?? "—")} />
              {"magnitude" in finalObj &&
                <Card label="Magnitude" value={String(finalObj.magnitude)} />}
              {"multiplier" in finalObj &&
                <Card label="LLM multiplier" value={String(finalObj.multiplier)} />}
              {"effective_weight" in finalObj &&
                <Card label="Effective weight" value={String(finalObj.effective_weight)} />}
              {"regime" in finalObj && <Card label="Regime" value={String(finalObj.regime)} />}
            </div>
            <button className="pill" disabled title="coming soon"
              style={{ marginTop: 12, opacity: 0.5 }}>Trade this prediction</button>
          </Section>

          <Section title="Agent & partial outputs">
            {outputs.filter((o) => o.key !== "final").map((o) => <Panel key={o.ordinal} o={o} />)}
          </Section>
        </>
      )}

      <Section title="Recent runs">
        <table>
          <thead><tr><th>When</th><th>Coin</th><th>Strategy</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {(runsQ.data?.runs ?? []).map((r) => (
              <tr key={r.run_id}>
                <td>{new Date(r.created_ts * 1000).toLocaleString()}</td>
                <td>{r.coin}</td><td>{r.strategy}</td><td>{r.status}</td>
                <td><button className="pill" onClick={() => setRunId(r.run_id)}>view</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </>
  );
}
```

> `.cards` / `.pill` / `.pills` / `.muted` classes already exist in `index.css` (used by other tabs). If `.cards` is absent, wrap the `<Card>`s in `<div className="grid2">` instead — match whatever the existing tabs use for card rows (check `PerformanceTab.tsx`).

- [ ] **Step 2: Type-check (no test yet — verified by build)**

Run: `cd /home/malecada/master_thesis/TradingAgents/tradingagents/monitor/frontend && npx tsc -b`
Expected: no type errors. Fix any prop/type mismatches against the verbatim component signatures (`Card`, `Section`, `Badge`).

- [ ] **Step 3: Commit**

```bash
git add tradingagents/monitor/frontend/src/tabs/RunTab.tsx
git commit -m "feat(monitor-ui): RunTab component (form, progress, results, history)"
```

---

### Task 11: Register the tab + rebuild the SPA

**Files:**
- Modify: `tradingagents/monitor/frontend/src/App.tsx`
- Modify (generated): `tradingagents/monitor/frontend/dist/**` (committed build output)

- [ ] **Step 1: Add the tab**

In `tradingagents/monitor/frontend/src/App.tsx`, add the import:

```typescript
import { RunTab } from "./tabs/RunTab";
```

Add the entry to the `TABS` array (after `health`):

```typescript
  { id: "run", label: "Run", el: <RunTab /> },
```

- [ ] **Step 2: Run the frontend test suite**

Run: `cd /home/malecada/master_thesis/TradingAgents/tradingagents/monitor/frontend && npm run test`
Expected: PASS (all existing + new adhoc/format/lib tests)

- [ ] **Step 3: Build the SPA**

Run: `npm run build`
Expected: `tsc -b && vite build` completes; `dist/` updated with no errors.

- [ ] **Step 4: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tradingagents/monitor/frontend/src/App.tsx tradingagents/monitor/frontend/dist
git commit -m "feat(monitor-ui): register Run tab + rebuild SPA"
```

---

## Phase 6 — Integration & docs

### Task 12: Manual end-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Confirm a model checkpoint exists**

Run: `ls -t /home/malecada/master_thesis/TradingAgents/data/checkpoints/composite_*.pkl | head -1`
Expected: a path prints. If none, the ad-hoc quant/hybrid runs will error with a clear "run a live cycle first" message — note this precondition and (if needed) run a live retrain/cycle to produce one.

- [ ] **Step 2: Launch the monitor locally**

Run:
```bash
cd /home/malecada/master_thesis/TradingAgents
TA_MONITOR_PASSWORD=devpw DATA_DIR=data LOG_DIR=logs python -m tradingagents.monitor
```
Open `http://127.0.0.1:8800/#run` (user `admin`, password `devpw`).

- [ ] **Step 3: Run a quant prediction**

Pick `bitcoin`, a recent date, strategy `quant`, click Run. Expected: completes in a few seconds; "Final decision" shows direction/magnitude/regime; a "Quant signal" panel holds the full `QuantSignal` JSON.

- [ ] **Step 4: Run a hybrid prediction**

Same coin/date, strategy `hybrid`, confirm the cost prompt, click Run. Expected: progress shows "Running agent graph (~90s)"; after ~90–120s the agent panels (market/on-chain/prediction reports, bull, bear, research manager, trader, risk, modulator, PM decision) and the final modulated decision appear. Cross-check the numbers look sane vs a recent journal cycle for the same coin in the Decisions tab.

- [ ] **Step 5: Verify the single-job lock + history**

While a hybrid run is in progress, confirm the Run button is disabled and a second `POST /api/adhoc/run` returns 409. After completion, confirm the run appears in "Recent runs" and clicking "view" reloads it.

- [ ] **Step 6: Verify no-trade**

Run: `python -m pytest tests/monitor/adhoc/ -v`
Then confirm by inspection that `service.py` imports no `execution.exchange` order methods (`grep -n "exchange" tradingagents/monitor/adhoc/service.py` returns nothing). The ad-hoc path reads data + LLM only.

---

### Task 13: Document the feature + update THESIS_FINDINGS if relevant

**Files:**
- Modify: `tradingagents/monitor/README.md` if present, else create a short `tradingagents/monitor/adhoc/README.md`

- [ ] **Step 1: Write usage docs**

Create `tradingagents/monitor/adhoc/README.md`:

```markdown
# Ad-hoc prediction runner

Run a quant or hybrid prediction for a chosen coin + date from the monitor's
**Run** tab and study the final decision plus every agent/partial output.
Display-only — it never places a trade.

- **Store:** `${QUANT_DATA_DIR|DATA_DIR}/adhoc/adhoc_runs.db` (isolated from journals)
- **Worker:** `python -m tradingagents.monitor.adhoc.worker --run <id>` (spawned by the API)
- **Routes:** `GET /api/adhoc/meta`, `POST /api/adhoc/run`, `GET /api/adhoc/status/{id}`,
  `GET /api/adhoc/result/{id}`, `GET /api/adhoc/runs`
- **Engine reuse:** `predict.run_predict` → `stage_quant_preds` →
  `get_quant_signal` (quant) or `TradingAgentsGraph.propagate_with_modulator` (hybrid).
- **Checkpoint:** newest `data/checkpoints/composite_*.pkl` (no retrain). Historical
  dates: PIT features, as-of-latest model weights.
- **Guardrails:** one run at a time (single-job lock), default model `gpt-4o-mini`,
  sentiment omitted by default for BTC/ETH.
```

- [ ] **Step 2: Commit**

```bash
git add tradingagents/monitor/adhoc/README.md
git commit -m "docs(monitor): document the ad-hoc prediction runner"
```

---

## Self-Review

**Spec coverage:**
- §1 problem/goal → Tasks 2–10 (run quant/hybrid, study partials, display-only) ✓
- §2 decisions (monitor-integrated, background job + poll, any date, subprocess + SQLite) → Tasks 1,4,5,8–11 ✓
- §3 feasibility (reuse live path, OHLCV auto-pull, PIT analysts, on-chain degrade) → Task 2 `_compute_and_stage` (run_predict pulls/caches OHLCV; on-chain via store_root) ✓
- §4 architecture / reused entry points → Tasks 2,3 use verbatim signatures ✓
- §5 backend modules (store/service/worker/runner) → Tasks 1–5 ✓
- §6 API routes (meta/run/status/result/runs, 409, 400, auth) → Tasks 6,7 ✓
- §7 frontend Run tab (form/progress/results/history, collapsible panels, disabled Trade button) → Tasks 8–11 ✓
- §8 guardrails (gpt-4o-mini default, configured coins, sentiment omitted, single-job lock, pre-run confirm, no-trade) → Task 6 `_DEFAULT_*`/`_EST_COST`, Task 5 lock, Task 10 confirm, Task 12 no-trade ✓
- §9 errors (terminal error, missing checkpoint message, no silent flat, 400, stale reaper) → Task 2 empty-preds raise + `_latest_checkpoint` FileNotFoundError, Task 4 try/except, Task 5 reaper, Task 6 400s ✓
- §10 testing (store, service mocks, lock, reaper, API lifecycle/409/auth, frontend, manual e2e) → Tasks 1–9,11,12 ✓
- §11 out of scope (trade exec, one-click backfill, token streaming) → not built; disabled Trade button only ✓
- §12 risks → checkpoint precondition (Task 12 step 1), coarse hybrid progress (Task 3), single-job lock (Task 5) ✓
- **On-chain coverage in `/api/adhoc/meta`** — spec §8 mentioned it; deferred to keep meta light (the spec also marks backfill phase-2). Not a blocker; noted here as a known simplification.

**Placeholder scan:** no TBD/TODO; every code step shows full code; the two soft notes (StrategySource fixture shape in Task 7, `.cards` class in Task 10) point to a verbatim existing source to mirror, not a blank to fill.

**Type consistency:** `Output = (key, label, kind, content)` tuple used identically in service (yield), worker (unpack), store (`add_output` params). `run_quant(*, coin, date, run_id)` / `run_hybrid(*, coin, date, analysts, model, run_id)` signatures match worker call sites. API `AdhocRunBody` fields match the frontend `AdhocRunBody` type and `create_run` kwargs. `pollInterval`/`isTerminal` names match RunTab import.
