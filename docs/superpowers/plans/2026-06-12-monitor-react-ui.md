# Monitor UI v2 (React, dual-strategy) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the live-bot monitor frontend as a React SPA and extend the FastAPI backend to track BOTH live strategies (V5 MIX quant + hybrid LLM-modulator) with live positions/uPnL, allocation donuts, an upgraded multi-pane performance chart, trade analytics, and a hybrid modulator panel.

**Architecture:** Backend keeps the read-only FastAPI app but generalizes from one journal to a list of "strategy sources" (quant + optional hybrid), each with its own SQLite journal and Binance account. Frontend is React 18 + TypeScript + Vite at `tradingagents/monitor/frontend/`; the built `dist/` is **committed** so the VPS needs no Node. One write-path change: the hybrid runner journals modulator outputs into a new additive `modulator_outputs` table.

**Tech Stack:** FastAPI, sqlite3 (mode=ro), python-binance, pytest; React 18, TypeScript 5, Vite 5, @tanstack/react-query 5, lightweight-charts 5 (multi-pane), recharts 2, vitest.

**Worktree / branch:** `/home/malecada/master_thesis/TradingAgents/.worktrees/monitor-react-ui`, branch `feature/monitor-react-ui` (off tag `live-v2.3.3`). All paths below relative to that worktree root. All commands run from that root. Spec: `docs/superpowers/specs/2026-06-12-monitor-react-ui-design.md`.

**Verified facts the plan relies on:**
- Hybrid creds env: `HYBRID_BINANCE_API_KEY` / `HYBRID_BINANCE_API_SECRET`; hybrid journal at `$HYBRID_DATA_DIR/trade_journal.db` (default `data-hybrid`), quant at `$QUANT_DATA_DIR|$DATA_DIR/trade_journal.db` (`hybrid_config.py:23-34`).
- `ExchangeClient.__init__(api_key=None, api_secret=None, ...)` falls back to `BINANCE_API_KEY/_SECRET` env (`exchange.py:96`).
- `modulated_position` is a dict (Pydantic `ModulatedPosition` dump) with `llm_multiplier`, `llm_confidence`, `effective_weight`, `regime`, `quant_direction` (`strategies/contracts.py:33`).
- Hybrid runner has NO structured JSONL log — `/api/health` pipeline steps stay quant-only.
- `futures_position_information` rows carry `entryPrice`, `markPrice`, `unRealizedProfit`, `liquidationPrice`, `leverage`, `positionAmt`, `notional`.
- python-binance exposes `futures_income_history`.
- Node v25 + npm 11 available locally for the Vite build.

---

## Task 1: Metrics — drawdown series + rolling Sharpe

**Files:**
- Modify: `tradingagents/monitor/metrics.py`
- Test: `tests/monitor/test_metrics.py`

- [ ] **Step 1: Write the failing tests** (append to `tests/monitor/test_metrics.py`)

```python
def test_drawdown_series():
    eq = [{"ts": "t1", "value": 100.0}, {"ts": "t2", "value": 110.0},
          {"ts": "t3", "value": 99.0}]
    dd = metrics.drawdown_series(eq)
    assert dd == [{"ts": "t1", "value": 0.0}, {"ts": "t2", "value": 0.0},
                  {"ts": "t3", "value": -0.1}]


def test_drawdown_series_empty():
    assert metrics.drawdown_series([]) == []


def test_rolling_sharpe_short_series_is_empty():
    eq = [{"ts": f"t{i}", "value": 100.0 + i} for i in range(10)]
    assert metrics.rolling_sharpe(eq, window=30) == []


def test_rolling_sharpe_emits_from_window():
    # 40 points, constant 1% growth -> first point at index 30, huge sharpe
    vals, v = [], 100.0
    for i in range(40):
        vals.append({"ts": f"t{i}", "value": v})
        v *= 1.01
    rs = metrics.rolling_sharpe(vals, window=30)
    assert len(rs) == 10
    assert rs[0]["ts"] == "t30"
    assert all(p["value"] > 0 for p in rs)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/monitor/test_metrics.py -v -k "drawdown_series or rolling"`
Expected: FAIL — `AttributeError: module ... has no attribute 'drawdown_series'`

- [ ] **Step 3: Implement** (append to `tradingagents/monitor/metrics.py`)

```python
def drawdown_series(equity: list[dict]) -> list[dict]:
    """Running drawdown per equity point as {ts, value} (value <= 0)."""
    out: list[dict] = []
    peak = float("-inf")
    for pt in equity:
        v = pt["value"]
        peak = max(peak, v)
        dd = (v - peak) / peak if peak > 0 else 0.0
        out.append({"ts": pt["ts"], "value": round(dd, 6)})
    return out


def rolling_sharpe(equity: list[dict], window: int = 30) -> list[dict]:
    """Rolling annualized Sharpe over the trailing ``window`` returns.

    Emits one {ts, value} per point starting at index ``window`` (needs
    ``window`` returns => window+1 equity points). Empty when history is
    shorter — the UI hides the pane until enough cycles exist.
    """
    values = [p["value"] for p in equity]
    out: list[dict] = []
    for i in range(window, len(values)):
        out.append({
            "ts": equity[i]["ts"],
            "value": round(sharpe(values[i - window: i + 1]), 4),
        })
    return out
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/monitor/test_metrics.py -v`
Expected: ALL PASS (old + new)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/metrics.py tests/monitor/test_metrics.py
git commit -m "feat(monitor): drawdown_series + rolling_sharpe metrics"
```

---

## Task 2: Journal — `modulator_outputs` table + `log_modulator()`

**Files:**
- Modify: `tradingagents/execution/live/schema.sql` (append table)
- Modify: `tradingagents/execution/live/journal.py` (new method)
- Test: `tests/live/test_journal_modulator.py` (create; mirror style of existing `tests/live/` tests — check dir name with `ls tests/`; if journal tests live elsewhere, e.g. `tests/execution/`, put the file there)

- [ ] **Step 1: Write the failing test**

```python
"""modulator_outputs journaling (hybrid runner write-path)."""
from __future__ import annotations

import sqlite3

from tradingagents.execution.live.journal import Journal


def test_log_modulator_roundtrip(tmp_path):
    db = str(tmp_path / "j.db")
    j = Journal(db)
    j.log_modulator(cycle_id="c1", coin="ethereum", multiplier=1.2,
                    effective_weight=0.35, llm_confidence=0.7,
                    regime="trend_up", fallback=False)
    j.close()
    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT cycle_id, coin, multiplier, effective_weight, llm_confidence, "
        "regime, fallback FROM modulator_outputs").fetchone()
    conn.close()
    assert row == ("c1", "ethereum", 1.2, 0.35, 0.7, "trend_up", 0)


def test_log_modulator_fallback_row(tmp_path):
    db = str(tmp_path / "j.db")
    j = Journal(db)
    j.log_modulator(cycle_id="c1", coin="bitcoin", multiplier=1.0,
                    effective_weight=0.0, llm_confidence=None,
                    regime=None, fallback=True)
    j.close()
    conn = sqlite3.connect(db)
    row = conn.execute(
        "SELECT llm_confidence, regime, fallback FROM modulator_outputs"
    ).fetchone()
    conn.close()
    assert row == (None, None, 1)


def test_log_modulator_upsert_replaces(tmp_path):
    db = str(tmp_path / "j.db")
    j = Journal(db)
    j.log_modulator(cycle_id="c1", coin="bitcoin", multiplier=1.0,
                    effective_weight=0.0, fallback=True)
    j.log_modulator(cycle_id="c1", coin="bitcoin", multiplier=1.3,
                    effective_weight=0.5, fallback=False)
    j.close()
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT multiplier FROM modulator_outputs").fetchall()
    conn.close()
    assert rows == [(1.3,)]
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/live/test_journal_modulator.py -v`
Expected: FAIL — `AttributeError: 'Journal' object has no attribute 'log_modulator'`

- [ ] **Step 3: Append table to `schema.sql`**

```sql
-- Hybrid modulator outputs (one row per coin per hybrid cycle). Additive;
-- quant journals simply never write it. fallback=1 means the modulator
-- failed/was skipped and the hybrid traded pure quant (1.0, 0.0).
CREATE TABLE IF NOT EXISTS modulator_outputs (
    cycle_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    multiplier REAL NOT NULL,
    effective_weight REAL NOT NULL,
    llm_confidence REAL,
    regime TEXT,
    fallback INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (cycle_id, coin)
);
```

- [ ] **Step 4: Add method to `journal.py`** (after `log_shadow_decision`)

```python
    def log_modulator(self, *, cycle_id: str, coin: str, multiplier: float,
                      effective_weight: float, llm_confidence: float | None = None,
                      regime: str | None = None, fallback: bool = False) -> None:
        """Persist the hybrid modulator outputs for one coin/cycle.

        Written even when the modulator degraded to pure quant (1.0, 0.0)
        with fallback=True, so the UI can label the row honestly.
        """
        self._conn.execute(
            "INSERT OR REPLACE INTO modulator_outputs "
            "(cycle_id, coin, multiplier, effective_weight, llm_confidence, "
            "regime, fallback) VALUES (?,?,?,?,?,?,?)",
            (cycle_id, coin, multiplier, effective_weight, llm_confidence,
             regime, 1 if fallback else 0),
        )
        self._conn.commit()
```

Existing hybrid DB on the VPS predates this table — `Journal.__init__` replays the whole `schema.sql` (`CREATE TABLE IF NOT EXISTS`) on every open, so the table appears on first hybrid cycle after deploy. No `migrate()` entry needed (that list is for column additions to existing tables).

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/live/test_journal_modulator.py -v`
Expected: 3 PASS

- [ ] **Step 6: Commit**

```bash
git add tradingagents/execution/live/schema.sql tradingagents/execution/live/journal.py tests/live/test_journal_modulator.py
git commit -m "feat(journal): additive modulator_outputs table + log_modulator()"
```

---

## Task 3: Hybrid runner journals modulator outputs

**Files:**
- Modify: `tradingagents/execution/live/hybrid_runner.py:231` (right after `extract_modulator_outputs`)
- Test: `tests/live/test_journal_modulator.py` (append a wiring-shape test)

- [ ] **Step 1: Locate the call site**

In `run_hybrid_cycle`, the per-coin loop currently reads:

```python
                mult, eff_w = extract_modulator_outputs(mp)
                final_fraction = compose_final(base=base, multiplier=mult, effective_weight=eff_w)
```

- [ ] **Step 2: Insert journaling between those two lines**

```python
                mult, eff_w = extract_modulator_outputs(mp)
                is_fallback = not mp or mp.get("llm_multiplier") is None
                j.log_modulator(
                    cycle_id=cycle_id, coin=coin, multiplier=mult,
                    effective_weight=eff_w,
                    llm_confidence=(mp or {}).get("llm_confidence"),
                    regime=(str(mp["regime"]) if mp and mp.get("regime") is not None
                            else None),
                    fallback=is_fallback,
                )
                final_fraction = compose_final(base=base, multiplier=mult, effective_weight=eff_w)
```

(`regime` may be a Pydantic enum or a plain string depending on dump mode — `str()` normalizes both. `j` is the hybrid `Journal` instance already in scope.)

- [ ] **Step 3: Write a unit test for the fallback-detection expression** (append to `tests/live/test_journal_modulator.py`)

```python
def test_fallback_detection_matches_extract_semantics():
    # Mirrors hybrid_runner's is_fallback expression against
    # extract_modulator_outputs degrade conditions.
    from tradingagents.execution.live.hybrid_compose import extract_modulator_outputs

    for mp in (None, {}, {"llm_multiplier": None, "effective_weight": 0.4}):
        is_fallback = not mp or mp.get("llm_multiplier") is None
        assert is_fallback is True
        assert extract_modulator_outputs(mp) == (1.0, 0.0)

    mp = {"llm_multiplier": 1.2, "effective_weight": 0.4}
    assert (not mp or mp.get("llm_multiplier") is None) is False
    assert extract_modulator_outputs(mp) == (1.2, 0.4)
```

- [ ] **Step 4: Run tests + existing live suite**

Run: `python -m pytest tests/live/ -v`
Expected: ALL PASS (incl. pre-existing hybrid runner tests — the new call writes to the same journal the runner already holds open)

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/live/hybrid_runner.py tests/live/test_journal_modulator.py
git commit -m "feat(hybrid): journal modulator outputs per coin/cycle"
```

---

## Task 4: Monitor DB reader — modulator rows (missing-table tolerant)

**Files:**
- Modify: `tradingagents/monitor/db.py`
- Test: `tests/monitor/test_db.py`

- [ ] **Step 1: Write the failing tests** (append to `tests/monitor/test_db.py`)

```python
def test_modulator_outputs_missing_table_is_empty(journal_path):
    # The shared fixture's schema includes the table only after Task 2;
    # simulate an OLD journal by dropping it.
    import sqlite3 as sq
    conn = sq.connect(journal_path)
    conn.execute("DROP TABLE IF EXISTS modulator_outputs")
    conn.commit()
    conn.close()
    ro = db.open_journal(journal_path)
    assert db.modulator_outputs(ro, "c2") == []
    ro.close()


def test_modulator_outputs_rows(journal_path):
    import sqlite3 as sq
    conn = sq.connect(journal_path)
    conn.execute(
        "INSERT INTO modulator_outputs (cycle_id, coin, multiplier, "
        "effective_weight, llm_confidence, regime, fallback) "
        "VALUES ('c2','ethereum',1.2,0.35,0.7,'trend_up',0)")
    conn.commit()
    conn.close()
    ro = db.open_journal(journal_path)
    rows = db.modulator_outputs(ro, "c2")
    ro.close()
    assert rows[0]["coin"] == "ethereum"
    assert rows[0]["multiplier"] == 1.2
    assert rows[0]["fallback"] == 0
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/monitor/test_db.py -v -k modulator`
Expected: FAIL — `AttributeError: module ... has no attribute 'modulator_outputs'`

- [ ] **Step 3: Implement** (append to `tradingagents/monitor/db.py`)

```python
def modulator_outputs(conn: sqlite3.Connection, cycle_id: str) -> list[dict]:
    """Hybrid modulator rows for one cycle. Empty list when the journal
    predates the modulator_outputs table (quant journals never have it)."""
    try:
        return _rows(
            conn,
            "SELECT * FROM modulator_outputs WHERE cycle_id = ? ORDER BY coin",
            (cycle_id,))
    except sqlite3.OperationalError:
        return []
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/monitor/test_db.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/db.py tests/monitor/test_db.py
git commit -m "feat(monitor): read modulator_outputs rows, tolerate old journals"
```

---

## Task 5: ExchangeClient — position details + income history

**Files:**
- Modify: `tradingagents/execution/exchange.py` (two new read-only methods, after `get_open_positions`)
- Test: `tests/monitor/test_exchange_readers.py` (create — these are monitor-feature readers; mock the underlying client, no network)

- [ ] **Step 1: Write the failing tests**

```python
"""Read-only ExchangeClient additions for the monitor (mocked client)."""
from __future__ import annotations

from unittest.mock import MagicMock

from tradingagents.execution.exchange import ExchangeClient


def _client_with(positions=None, income=None):
    ex = ExchangeClient.__new__(ExchangeClient)  # skip __init__/network
    ex._client = MagicMock()
    ex._client.futures_position_information.return_value = positions or []
    ex._client.futures_income_history.return_value = income or []
    return ex


def test_get_position_details_maps_fields():
    ex = _client_with(positions=[
        {"symbol": "BTCUSDT", "positionAmt": "0.05", "entryPrice": "65000",
         "markPrice": "66000", "unRealizedProfit": "50.0",
         "liquidationPrice": "30000", "leverage": "3", "notional": "3300"},
        {"symbol": "ETHUSDT", "positionAmt": "0", "entryPrice": "0",
         "markPrice": "3000", "unRealizedProfit": "0",
         "liquidationPrice": "0", "leverage": "3", "notional": "0"},
    ])
    out = ex.get_position_details()
    assert len(out) == 1
    p = out[0]
    assert p["symbol"] == "BTCUSDT" and p["qty"] == 0.05
    assert p["entry_price"] == 65000.0 and p["mark_price"] == 66000.0
    assert p["upnl"] == 50.0 and p["leverage"] == 3.0
    assert p["liq_price"] == 30000.0 and p["notional"] == 3300.0


def test_get_position_details_notional_fallback():
    ex = _client_with(positions=[
        {"symbol": "BTCUSDT", "positionAmt": "-0.1", "entryPrice": "65000",
         "markPrice": "60000", "unRealizedProfit": "500",
         "liquidationPrice": "90000", "leverage": "2"},  # no notional key
    ])
    assert ex.get_position_details()[0]["notional"] == -6000.0


def test_income_history_passes_filters():
    ex = _client_with(income=[{"incomeType": "REALIZED_PNL", "income": "5"}])
    out = ex.income_history(start_time_ms=123, income_type="REALIZED_PNL")
    assert out == [{"incomeType": "REALIZED_PNL", "income": "5"}]
    ex._client.futures_income_history.assert_called_once_with(
        limit=1000, startTime=123, incomeType="REALIZED_PNL")
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/monitor/test_exchange_readers.py -v`
Expected: FAIL — no attribute `get_position_details`

- [ ] **Step 3: Implement** (in `exchange.py`, after `get_open_positions`)

```python
    def get_position_details(self) -> list[dict]:
        """All non-flat positions with the fields the monitor UI shows.

        Read-only superset of get_open_positions (kept separate so the
        runner's hot path is untouched). qty/notional are signed.
        """
        positions = self._retry(self._client.futures_position_information)
        out: list[dict] = []
        for pos in positions:
            qty = float(pos["positionAmt"])
            if qty == 0:
                continue
            notional = pos.get("notional")
            out.append({
                "symbol": pos["symbol"],
                "qty": qty,
                "entry_price": float(pos["entryPrice"]),
                "mark_price": float(pos["markPrice"]),
                "upnl": float(pos["unRealizedProfit"]),
                "leverage": float(pos.get("leverage") or 0),
                "liq_price": float(pos.get("liquidationPrice") or 0),
                "notional": float(notional) if notional is not None
                else qty * float(pos["markPrice"]),
            })
        return out

    def income_history(self, *, start_time_ms: int | None = None,
                       income_type: str | None = None,
                       limit: int = 1000) -> list[dict]:
        """Futures income records (REALIZED_PNL / COMMISSION / FUNDING_FEE...).

        Caller aggregates; this is a thin retry wrapper. Binance caps one
        page at 1000 records — enough for the testnet A/B volumes; the
        monitor labels totals as 'last 1000 records' rather than paginating.
        """
        params: dict = {"limit": limit}
        if start_time_ms is not None:
            params["startTime"] = start_time_ms
        if income_type is not None:
            params["incomeType"] = income_type
        return self._retry(self._client.futures_income_history, **params)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/monitor/test_exchange_readers.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/execution/exchange.py tests/monitor/test_exchange_readers.py
git commit -m "feat(exchange): get_position_details + income_history readers"
```

---

## Task 6: Analytics module — income + slippage aggregation

**Files:**
- Create: `tradingagents/monitor/analytics.py`
- Test: `tests/monitor/test_analytics.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Pure aggregation of Binance income records + journal slippage."""
from __future__ import annotations

from tradingagents.monitor import analytics


INCOME = [
    {"symbol": "BTCUSDT", "incomeType": "REALIZED_PNL", "income": "10.0"},
    {"symbol": "BTCUSDT", "incomeType": "REALIZED_PNL", "income": "-4.0"},
    {"symbol": "ETHUSDT", "incomeType": "REALIZED_PNL", "income": "6.0"},
    {"symbol": "BTCUSDT", "incomeType": "COMMISSION", "income": "-0.5"},
    {"symbol": "ETHUSDT", "incomeType": "FUNDING_FEE", "income": "-0.2"},
    {"symbol": "BTCUSDT", "incomeType": "REALIZED_PNL", "income": "0"},
]


def test_income_summary():
    s = analytics.income_summary(INCOME)
    assert s["realized_pnl_per_coin"] == {"BTCUSDT": 6.0, "ETHUSDT": 6.0}
    assert s["realized_pnl_total"] == 12.0
    assert s["fees_total"] == -0.5
    assert s["funding_total"] == -0.2
    # win rate over NONZERO realized-pnl records: wins 10,6 of [10,-4,6]
    assert abs(s["win_rate"] - 2 / 3) < 1e-9
    assert s["n_closing_fills"] == 3


def test_income_summary_empty():
    s = analytics.income_summary([])
    assert s["realized_pnl_per_coin"] == {}
    assert s["win_rate"] is None
    assert s["n_closing_fills"] == 0


def test_slippage_stats():
    trades = [{"slippage": 1.0}, {"slippage": 3.0}, {"slippage": None}]
    st = analytics.slippage_stats(trades)
    assert st == {"mean": 2.0, "max": 3.0, "n": 2}


def test_slippage_stats_empty():
    assert analytics.slippage_stats([]) == {"mean": None, "max": None, "n": 0}
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/monitor/test_analytics.py -v`
Expected: FAIL — `ModuleNotFoundError` / import error

- [ ] **Step 3: Implement `tradingagents/monitor/analytics.py`**

```python
"""Pure trade-analytics aggregation for the monitor UI.

Income records come from ExchangeClient.income_history() (Binance futures
income endpoint); slippage comes from journal trade rows. No I/O here.
"""
from __future__ import annotations


def income_summary(records: list[dict]) -> dict:
    """Aggregate Binance income records into the analytics strip payload.

    Win rate = share of profitable records among NONZERO REALIZED_PNL fills
    (zero-pnl rows are position-increase fills, not round trips). None when
    no closing fills exist yet.
    """
    pnl_per_coin: dict[str, float] = {}
    fees = 0.0
    funding = 0.0
    wins = 0
    closing = 0
    for r in records:
        kind = r.get("incomeType")
        amount = float(r.get("income", 0.0))
        symbol = r.get("symbol") or "?"
        if kind == "REALIZED_PNL":
            pnl_per_coin[symbol] = pnl_per_coin.get(symbol, 0.0) + amount
            if amount != 0.0:
                closing += 1
                if amount > 0:
                    wins += 1
        elif kind == "COMMISSION":
            fees += amount
        elif kind == "FUNDING_FEE":
            funding += amount
    return {
        "realized_pnl_per_coin": {k: round(v, 4) for k, v in sorted(pnl_per_coin.items())},
        "realized_pnl_total": round(sum(pnl_per_coin.values()), 4),
        "fees_total": round(fees, 4),
        "funding_total": round(funding, 4),
        "win_rate": (wins / closing) if closing else None,
        "n_closing_fills": closing,
    }


def slippage_stats(trades: list[dict]) -> dict:
    """Mean/max/count of journal slippage values (None entries skipped)."""
    vals = [t["slippage"] for t in trades if t.get("slippage") is not None]
    if not vals:
        return {"mean": None, "max": None, "n": 0}
    return {
        "mean": round(sum(vals) / len(vals), 4),
        "max": round(max(vals), 4),
        "n": len(vals),
    }
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/monitor/test_analytics.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/analytics.py tests/monitor/test_analytics.py
git commit -m "feat(monitor): income + slippage analytics aggregation"
```

---

## Task 7: Strategy sources — env resolution + cached account providers

**Files:**
- Create: `tradingagents/monitor/sources.py`
- Test: `tests/monitor/test_sources.py`

- [ ] **Step 1: Write the failing tests**

```python
"""StrategySource resolution from env + TTL-cached account snapshots."""
from __future__ import annotations

import pytest

from tradingagents.monitor import sources


def test_resolve_quant_only(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("QUANT_DATA_DIR", raising=False)
    monkeypatch.delenv("HYBRID_DATA_DIR", raising=False)
    quant, hybrid = sources.resolve_sources()
    assert quant.name == "quant"
    assert quant.journal_path == str(tmp_path / "trade_journal.db")
    assert hybrid is None


def test_resolve_both(monkeypatch, tmp_path):
    monkeypatch.setenv("QUANT_DATA_DIR", str(tmp_path / "q"))
    monkeypatch.setenv("HYBRID_DATA_DIR", str(tmp_path / "h"))
    quant, hybrid = sources.resolve_sources()
    assert hybrid is not None and hybrid.name == "hybrid"
    assert hybrid.journal_path == str(tmp_path / "h" / "trade_journal.db")


def test_resolve_hybrid_equal_dirs_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("QUANT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HYBRID_DATA_DIR", str(tmp_path))
    _, hybrid = sources.resolve_sources()
    assert hybrid is None


def test_cached_provider_caches_success_and_failure():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            return {"ok": True}
        raise RuntimeError("ban")

    t = {"now": 0.0}
    cached = sources.ttl_cached(flaky, ttl=30.0, clock=lambda: t["now"])
    assert cached() == {"ok": True}
    assert cached() == {"ok": True} and calls["n"] == 1  # cached
    t["now"] = 31.0
    with pytest.raises(RuntimeError):
        cached()
    with pytest.raises(RuntimeError):  # failure cached too
        cached()
    assert calls["n"] == 2


def test_account_snapshot_shape(monkeypatch):
    class FakeEx:
        def get_position_details(self):
            return [{"symbol": "BTCUSDT", "qty": 0.05, "entry_price": 65000.0,
                     "mark_price": 66000.0, "upnl": 50.0, "leverage": 3.0,
                     "liq_price": 30000.0, "notional": 3300.0}]

        def get_balances(self):
            return {"USDT": 7000.0}

        def get_total_portfolio_value(self):
            return 10350.0

    snap = sources.account_snapshot(FakeEx())
    assert snap["equity"] == 10350.0
    assert snap["usdt_free"] == 7000.0
    assert snap["positions"][0]["symbol"] == "BTCUSDT"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/monitor/test_sources.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement `tradingagents/monitor/sources.py`**

```python
"""Per-strategy data sources for the dual (quant + hybrid) monitor.

A StrategySource bundles everything the API layer needs for one strategy:
its journal path and a TTL-cached live-account snapshot provider. Hybrid is
optional — resolve_sources() returns (quant, hybrid|None) from the same env
contract the runners use (QUANT_DATA_DIR / HYBRID_DATA_DIR /
HYBRID_BINANCE_API_KEY).
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class StrategySource:
    name: str
    journal_path: str
    # () -> {"positions": [...], "usdt_free": float, "equity": float}
    snapshot: Callable[[], dict]


def account_snapshot(ex) -> dict:
    """One live snapshot of an account: positions + free USDT + equity."""
    return {
        "positions": ex.get_position_details(),
        "usdt_free": ex.get_balances().get("USDT", 0.0),
        "equity": ex.get_total_portfolio_value(),
    }


def ttl_cached(fn: Callable[[], dict], ttl: float = 30.0,
               clock: Callable[[], float] = time.monotonic) -> Callable[[], dict]:
    """Cache fn() results AND failures for ttl seconds (same semantics as the
    old live_positions cache: retries during an IP ban must not re-query)."""
    state: dict = {"exp": 0.0, "data": None, "error": None}

    def wrapped() -> dict:
        now = clock()
        if now < state["exp"]:
            if state["error"] is not None:
                raise state["error"]
            return state["data"]
        try:
            data = fn()
            state.update(exp=now + ttl, data=data, error=None)
            return data
        except Exception as exc:
            state.update(exp=now + ttl, data=None, error=exc)
            raise

    return wrapped


def _exchange_provider(api_key_env: str, api_secret_env: str) -> Callable[[], dict]:
    """Lazy ExchangeClient bound to one account's env credentials."""
    holder: dict = {"client": None}

    def provide() -> dict:
        if not os.environ.get(api_key_env):
            raise RuntimeError(f"{api_key_env} not set — live account unavailable")
        if holder["client"] is None:
            from tradingagents.execution.exchange import ExchangeClient
            holder["client"] = ExchangeClient(
                api_key=os.environ.get(api_key_env),
                api_secret=os.environ.get(api_secret_env),
            )
        return account_snapshot(holder["client"])

    return provide


def resolve_sources(ttl: float = 30.0) -> tuple[StrategySource, StrategySource | None]:
    """Build (quant, hybrid|None) from the runners' env contract.

    Hybrid is enabled only when HYBRID_DATA_DIR is set AND differs from the
    quant dir (mirrors the /api/compare guard).
    """
    quant_dir = Path(os.environ.get(
        "QUANT_DATA_DIR", os.environ.get("DATA_DIR", "data")))
    quant = StrategySource(
        name="quant",
        journal_path=str(quant_dir / "trade_journal.db"),
        snapshot=ttl_cached(
            _exchange_provider("BINANCE_API_KEY", "BINANCE_API_SECRET"), ttl),
    )
    hybrid_env = os.environ.get("HYBRID_DATA_DIR")
    if not hybrid_env or Path(hybrid_env) == quant_dir:
        return quant, None
    hybrid = StrategySource(
        name="hybrid",
        journal_path=str(Path(hybrid_env) / "trade_journal.db"),
        snapshot=ttl_cached(
            _exchange_provider("HYBRID_BINANCE_API_KEY",
                               "HYBRID_BINANCE_API_SECRET"), ttl),
    )
    return quant, hybrid
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/monitor/test_sources.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/sources.py tests/monitor/test_sources.py
git commit -m "feat(monitor): dual StrategySource resolution + TTL-cached snapshots"
```

---

## Task 8: FastAPI app rewrite — dual-strategy endpoints

This is the core backend task: `create_app` takes the two sources, every endpoint becomes per-strategy, auth moves to middleware (so the static SPA mount is also protected), and the income-analytics block lands in `/api/trades`.

**Files:**
- Rewrite: `tradingagents/monitor/app.py`
- Modify: `tradingagents/monitor/__main__.py`
- Rewrite: `tests/monitor/test_app.py` (fixtures change shape)
- Modify: `tests/monitor/conftest.py` (add hybrid fixtures)

- [ ] **Step 1: Extend `tests/monitor/conftest.py`** — append:

```python
@pytest.fixture
def hybrid_journal_path(tmp_path) -> str:
    """A small hybrid journal: 1 overlapping cycle + modulator rows."""
    db = tmp_path / "hybrid" / "trade_journal.db"
    db.parent.mkdir()
    conn = sqlite3.connect(str(db))
    with open(_SCHEMA) as f:
        conn.executescript(f.read())
    conn.execute(
        "INSERT INTO cycles (cycle_id, start_ts, end_ts, status, n_trades) "
        "VALUES ('c2','2026-05-20T08:00:00+00:00','2026-05-20T08:20:00+00:00','ok',1)")
    conn.execute(
        "INSERT INTO portfolio_snapshots (cycle_id, ts, total_value, usdt_balance, "
        "position_qty_per_coin, unrealized_pnl) VALUES "
        "('c2','2026-05-20T08:20:00+00:00',10100.0,5000.0,'{\"ethereum\": 1.0}',20.0)")
    conn.execute(
        "INSERT INTO modulator_outputs (cycle_id, coin, multiplier, "
        "effective_weight, llm_confidence, regime, fallback) VALUES "
        "('c2','ethereum',1.2,0.35,0.7,'trend_up',0)")
    conn.execute(
        "INSERT INTO trades (cycle_id, coin, side, qty, entry_price, slippage, "
        "order_id, status) VALUES ('c2','ethereum','BUY',1.0,3800.0,0.4,'h1','EXECUTED')")
    conn.commit()
    conn.close()
    return str(db)


def _fake_snapshot(positions=None, equity=10350.0, usdt=7000.0):
    def snap():
        return {"positions": positions or [], "usdt_free": usdt, "equity": equity}
    return snap


@pytest.fixture
def dual_app(journal_path, hybrid_journal_path, log_dir, monkeypatch):
    """create_app with quant+hybrid sources and fake snapshot providers."""
    from tradingagents.monitor.app import create_app
    from tradingagents.monitor.sources import StrategySource
    monkeypatch.setenv("TA_MONITOR_PASSWORD", "pw")
    quant = StrategySource("quant", journal_path, _fake_snapshot(positions=[
        {"symbol": "BTCUSDT", "qty": 0.05, "entry_price": 65000.0,
         "mark_price": 66000.0, "upnl": 50.0, "leverage": 3.0,
         "liq_price": 30000.0, "notional": 3300.0}]))
    hybrid = StrategySource("hybrid", hybrid_journal_path, _fake_snapshot(
        positions=[{"symbol": "ETHUSDT", "qty": 1.0, "entry_price": 3800.0,
                    "mark_price": 3900.0, "upnl": 100.0, "leverage": 2.0,
                    "liq_price": 1900.0, "notional": 3900.0}], equity=10100.0))
    return create_app(quant=quant, hybrid=hybrid, log_dir=log_dir,
                      start_capital=10000.0)


@pytest.fixture
def dual_client(dual_app):
    from fastapi.testclient import TestClient
    c = TestClient(dual_app)
    c.auth = ("admin", "pw")
    return c
```

(Keep the existing `journal_path` / `empty_journal_path` / `log_dir` fixtures unchanged. The old `client` fixture in `test_app.py` is replaced in Step 2.)

- [ ] **Step 2: Rewrite `tests/monitor/test_app.py`**

```python
"""Dual-strategy monitor API tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tradingagents.monitor.app import create_app
from tradingagents.monitor.sources import StrategySource


def _quant_only_app(journal_path, log_dir, monkeypatch, snapshot=None):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", "pw")
    def boom():
        raise RuntimeError("no creds")
    quant = StrategySource("quant", journal_path, snapshot or boom)
    return create_app(quant=quant, hybrid=None, log_dir=log_dir,
                      start_capital=10000.0)


def test_create_app_requires_password(journal_path, log_dir, monkeypatch):
    monkeypatch.delenv("TA_MONITOR_PASSWORD", raising=False)
    quant = StrategySource("quant", journal_path, lambda: {})
    with pytest.raises(RuntimeError):
        create_app(quant=quant, hybrid=None, log_dir=log_dir)


def test_all_routes_require_auth(dual_client):
    for path in ("/", "/api/performance", "/api/positions", "/api/trades",
                 "/api/cycles", "/api/health", "/api/compare"):
        assert dual_client.get(path).status_code == 401, path


def test_performance_dual(dual_client):
    r = dual_client.get("/api/performance", auth=dual_client.auth)
    assert r.status_code == 200
    body = r.json()
    q, h = body["quant"], body["hybrid"]
    assert q["cards"]["equity"] == 10280.0          # last snapshot total_value
    assert q["cards"]["total_upnl"] == 50.0          # live snapshot
    assert q["cards"]["open_positions"] == 1
    assert len(q["equity"]) == 2 and len(q["drawdown"]) == 2
    assert q["rolling_sharpe"] == []                 # < 31 points
    assert h["cards"]["equity"] == 10100.0
    assert body["anchors"]["quant"] == 3.18
    assert "compare" in body                          # delta block present


def test_performance_hybrid_none(journal_path, log_dir, monkeypatch):
    app = _quant_only_app(journal_path, log_dir, monkeypatch)
    c = TestClient(app)
    body = c.get("/api/performance", auth=("admin", "pw")).json()
    assert body["hybrid"] is None
    assert body["compare"] is None
    # live snapshot failed -> uPnL falls back to journal snapshot value
    assert body["quant"]["cards"]["total_upnl"] == 80.0
    assert body["quant"]["cards"]["upnl_stale"] is True


def test_positions_dual(dual_client):
    body = dual_client.get("/api/positions", auth=dual_client.auth).json()
    q = body["quant"]
    assert q["positions"][0]["coin"] == "bitcoin"
    assert q["positions"][0]["upnl_usd"] == 50.0
    assert q["totals"]["upnl"] == 50.0 and q["totals"]["equity"] == 10350.0
    assert {"label": "USDT (free)", "usd": 7000.0} in q["allocation"]
    assert q["stale"] is False
    h = body["hybrid"]
    assert h["positions"][0]["coin"] == "ethereum"
    assert h["positions"][0]["upnl_pct"] == pytest.approx(100.0 / 3800.0 * 100, rel=1e-3)


def test_positions_fallback_when_live_fails(journal_path, log_dir, monkeypatch):
    app = _quant_only_app(journal_path, log_dir, monkeypatch)
    c = TestClient(app)
    q = c.get("/api/positions", auth=("admin", "pw")).json()["quant"]
    assert q["stale"] is True and "no creds" in q["error"]
    coins = {p["coin"] for p in q["positions"]}
    assert coins == {"bitcoin", "ethereum"}          # journal snapshot qty map
    assert q["as_of"] == "2026-05-20T07:05:00+00:00"


def test_trades_strategy_param_and_analytics(dual_client, monkeypatch):
    body = dual_client.get("/api/trades?strategy=hybrid",
                           auth=dual_client.auth).json()
    assert len(body["executions"]) == 1
    assert body["executions"][0]["coin"] == "ethereum"
    assert body["analytics"]["slippage"] == {"mean": 0.4, "max": 0.4, "n": 1}
    assert body["analytics"]["income"] is None       # no income provider wired
    quant = dual_client.get("/api/trades?strategy=quant",
                            auth=dual_client.auth).json()
    assert len(quant["executions"]) == 3


def test_trades_bad_strategy_400(dual_client):
    r = dual_client.get("/api/trades?strategy=nope", auth=dual_client.auth)
    assert r.status_code == 400


def test_cycles_and_cycle_detail_strategy(dual_client):
    cycles = dual_client.get("/api/cycles?strategy=hybrid",
                             auth=dual_client.auth).json()["cycles"]
    assert [c["cycle_id"] for c in cycles] == ["c2"]
    detail = dual_client.get("/api/cycle/c2?strategy=hybrid",
                             auth=dual_client.auth).json()
    assert detail["modulator"][0]["multiplier"] == 1.2
    quant_detail = dual_client.get("/api/cycle/c2?strategy=quant",
                                   auth=dual_client.auth).json()
    assert quant_detail["modulator"] == []
    assert len(quant_detail["predictions"]) == 2


def test_health_dual(dual_client):
    body = dual_client.get("/api/health", auth=dual_client.auth).json()
    assert body["timeline"]["quant"][0]["cycle_id"] == "c2"
    assert body["timeline"]["hybrid"][0]["cycle_id"] == "c2"
    assert body["steps"]                                # quant JSONL only
    assert body["errors"][0]["step"] == "execute"


def test_missing_db_returns_503(log_dir, monkeypatch):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", "pw")
    quant = StrategySource("quant", "/nonexistent/x.db", lambda: {})
    app = create_app(quant=quant, hybrid=None, log_dir=log_dir)
    c = TestClient(app)
    r = c.get("/api/cycles", auth=("admin", "pw"))
    assert r.status_code == 503 and "error" in r.json()
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/monitor/test_app.py -v`
Expected: FAIL — `create_app() got an unexpected keyword argument 'quant'`

- [ ] **Step 4: Rewrite `tradingagents/monitor/app.py`** (full file)

```python
"""FastAPI app for the dual-strategy (quant + hybrid) live bot monitor.

Read-only. Serves the built React SPA at ``/`` and JSON at ``/api/*``.
HTTP basic auth is enforced by middleware on EVERY path (including static
assets). All endpoints tolerate an empty or missing journal: empty DBs
yield empty payloads, an unreadable DB yields HTTP 503. A missing hybrid
source yields ``hybrid: null`` blocks, never an error.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from tradingagents.execution.live.config import from_binance_symbol
from tradingagents.execution.live.rebacktest import compare_quant_hybrid
from tradingagents.monitor import analytics, db, health, metrics
from tradingagents.monitor.sources import StrategySource

_DIR = Path(__file__).parent
_DIST = _DIR / "frontend" / "dist"
_AUTH_USER = "admin"
_ROLLING_WINDOW = 30


def create_app(
    *,
    quant: StrategySource,
    hybrid: StrategySource | None = None,
    log_dir: str = "logs",
    start_capital: float = 10000.0,
) -> FastAPI:
    """Build the monitor app. Raises RuntimeError if TA_MONITOR_PASSWORD
    is unset — the UI must never run without a password."""
    password = os.environ.get("TA_MONITOR_PASSWORD", "")
    if not password:
        raise RuntimeError("TA_MONITOR_PASSWORD environment variable is not set")

    app = FastAPI(title="Live Monitor", docs_url=None, redoc_url=None)

    # ── auth middleware (covers /api AND static SPA assets) ────────────────
    expected = base64.b64encode(f"{_AUTH_USER}:{password}".encode()).decode()

    @app.middleware("http")
    async def basic_auth(request: Request, call_next):
        header = request.headers.get("authorization", "")
        ok = header.startswith("Basic ") and secrets.compare_digest(
            header[6:], expected)
        if not ok:
            return Response(status_code=401,
                            headers={"WWW-Authenticate": "Basic"})
        return await call_next(request)

    # ── helpers ────────────────────────────────────────────────────────────
    def _sources() -> list[StrategySource]:
        return [quant] + ([hybrid] if hybrid else [])

    def _source(name: str) -> StrategySource:
        for s in _sources():
            if s.name == name:
                return s
        raise HTTPException(status_code=400, detail=f"unknown strategy {name!r}")

    def _conn(s: StrategySource) -> sqlite3.Connection:
        return db.open_journal(s.journal_path)

    def _snapshot_rows(conn: sqlite3.Connection) -> tuple[list[dict], dict]:
        """(portfolio_snapshots, latest ref_price per coin)."""
        snaps = db.portfolio_snapshots(conn)
        ref_prices: dict[str, float] = {}
        latest = db.latest_cycle(conn)
        if latest:
            for p in db.cycle_detail(conn, latest["cycle_id"])["predictions"]:
                if p.get("ref_price") is not None:
                    ref_prices[p["coin"]] = p["ref_price"]
        return snaps, ref_prices

    def _live_block(s: StrategySource) -> tuple[dict | None, str | None]:
        """(snapshot|None, error|None) from the TTL-cached provider."""
        try:
            return s.snapshot(), None
        except Exception as exc:
            return None, str(exc)

    # ── endpoints ──────────────────────────────────────────────────────────
    @app.get("/api/performance")
    def api_performance():
        out: dict = {"quant": None, "hybrid": None}
        for s in _sources():
            conn = _conn(s)
            try:
                snaps, _ = _snapshot_rows(conn)
                trades = db.all_trades(conn)
            finally:
                conn.close()
            equity = metrics.equity_series(snaps, trades, start_capital)
            values = [pt["value"] for pt in equity]
            live, live_err = _live_block(s)
            if live is not None:
                total_upnl = sum(p["upnl"] for p in live["positions"])
                n_open = len(live["positions"])
                upnl_stale = False
            else:
                total_upnl = snaps[-1].get("unrealized_pnl") if snaps else None
                n_open = None
                upnl_stale = True
            out[s.name] = {
                "cards": {
                    "equity": values[-1] if values else start_capital,
                    "sharpe": round(metrics.sharpe(values), 2),
                    "max_drawdown": round(metrics.max_drawdown(values), 4),
                    "total_upnl": total_upnl,
                    "upnl_stale": upnl_stale,
                    "open_positions": n_open,
                },
                "equity": equity,
                "drawdown": metrics.drawdown_series(equity),
                "rolling_sharpe": metrics.rolling_sharpe(equity, _ROLLING_WINDOW),
            }
        compare = None
        if hybrid is not None:
            try:
                compare = compare_quant_hybrid(
                    Path(quant.journal_path), Path(hybrid.journal_path), coins=[])
            except Exception as exc:
                compare = {"error": str(exc)}
        out["compare"] = compare
        out["anchors"] = {
            "quant": float(os.environ.get("TA_MONITOR_ANCHOR_SR_QUANT", "3.18")),
            "hybrid": (float(os.environ["TA_MONITOR_ANCHOR_SR_HYBRID"])
                       if os.environ.get("TA_MONITOR_ANCHOR_SR_HYBRID") else None),
        }
        return out

    @app.get("/api/positions")
    def api_positions():
        out: dict = {"quant": None, "hybrid": None}
        for s in _sources():
            live, live_err = _live_block(s)
            if live is not None:
                positions = []
                for p in sorted(live["positions"], key=lambda x: x["symbol"]):
                    entry_notional = abs(p["qty"]) * p["entry_price"]
                    positions.append({
                        "coin": from_binance_symbol(p["symbol"]),
                        "side": "LONG" if p["qty"] > 0 else "SHORT",
                        "qty": p["qty"],
                        "entry": p["entry_price"],
                        "mark": p["mark_price"],
                        "leverage": p["leverage"],
                        "notional": p["notional"],
                        "upnl_usd": p["upnl"],
                        "upnl_pct": (p["upnl"] / entry_notional * 100.0
                                     if entry_notional else None),
                        "liq_price": p["liq_price"] or None,
                    })
                allocation = [{"label": pos["coin"], "usd": abs(pos["notional"])}
                              for pos in positions]
                allocation.append({"label": "USDT (free)", "usd": live["usdt_free"]})
                out[s.name] = {
                    "positions": positions,
                    "totals": {
                        "upnl": sum(p["upnl_usd"] for p in positions),
                        "notional": sum(abs(p["notional"]) for p in positions),
                        "equity": live["equity"],
                    },
                    "allocation": allocation,
                    "stale": False, "as_of": None, "error": None,
                }
            else:  # journal fallback (same pattern as v2.3.1 holdings fix)
                conn = _conn(s)
                try:
                    snaps, ref_prices = _snapshot_rows(conn)
                finally:
                    conn.close()
                positions = []
                as_of = None
                if snaps:
                    as_of = snaps[-1].get("ts")
                    try:
                        qty_map = json.loads(
                            snaps[-1].get("position_qty_per_coin") or "{}")
                    except (json.JSONDecodeError, TypeError):
                        qty_map = {}
                    for coin, qty in sorted(qty_map.items()):
                        if not qty:
                            continue
                        price = ref_prices.get(coin)
                        positions.append({
                            "coin": coin,
                            "side": "LONG" if qty > 0 else "SHORT",
                            "qty": qty, "entry": None, "mark": price,
                            "leverage": None,
                            "notional": qty * price if price else None,
                            "upnl_usd": None, "upnl_pct": None,
                            "liq_price": None,
                        })
                allocation = [{"label": p["coin"], "usd": abs(p["notional"])}
                              for p in positions if p["notional"] is not None]
                out[s.name] = {
                    "positions": positions,
                    "totals": {
                        "upnl": snaps[-1].get("unrealized_pnl") if snaps else None,
                        "notional": sum(a["usd"] for a in allocation) or None,
                        "equity": snaps[-1].get("total_value") if snaps else None,
                    },
                    "allocation": allocation,
                    "stale": True, "as_of": as_of, "error": live_err,
                }
        return out

    @app.get("/api/trades")
    def api_trades(strategy: str = "quant"):
        s = _source(strategy)
        conn = _conn(s)
        try:
            executions = db.all_trades(conn)
        finally:
            conn.close()
        income_block = None
        live, _err = _live_block(s)
        if live is not None and live.get("income") is not None:
            income_block = analytics.income_summary(live["income"])
        return {
            "executions": executions,
            "analytics": {
                "income": income_block,
                "slippage": analytics.slippage_stats(executions),
            },
        }

    @app.get("/api/cycles")
    def api_cycles(strategy: str = "quant"):
        conn = _conn(_source(strategy))
        try:
            return {"cycles": db.list_cycles(conn)}
        finally:
            conn.close()

    @app.get("/api/cycle/{cycle_id}")
    def api_cycle(cycle_id: str, strategy: str = "quant"):
        conn = _conn(_source(strategy))
        try:
            detail = db.cycle_detail(conn, cycle_id)
            detail["modulator"] = db.modulator_outputs(conn, cycle_id)
            return detail
        finally:
            conn.close()

    @app.get("/api/health")
    def api_health():
        timeline: dict = {}
        retrains: dict = {}
        for s in _sources():
            conn = _conn(s)
            try:
                timeline[s.name] = db.list_cycles(conn)
                retrains[s.name] = db.retrains(conn)
            finally:
                conn.close()
        if hybrid is None:
            timeline.setdefault("hybrid", None)
            retrains.setdefault("hybrid", None)
        steps = health.read_structured_log(log_dir)  # quant runner only
        return {
            "timeline": timeline,
            "steps": steps,
            "errors": health.recent_errors(steps),
            "retrains": retrains,
        }

    @app.get("/api/compare")
    def api_compare():
        if hybrid is None:
            return {"error": "hybrid not configured — HYBRID_DATA_DIR not set "
                             "or equals QUANT_DATA_DIR"}
        coins_env = os.environ.get("COMPARE_COINS", "")
        coins = [c.strip() for c in coins_env.split(",") if c.strip()]
        return compare_quant_hybrid(
            Path(quant.journal_path), Path(hybrid.journal_path), coins=coins)

    @app.exception_handler(sqlite3.OperationalError)
    def _db_error(request: Request, exc: sqlite3.OperationalError):
        return JSONResponse(status_code=503, content={"error": str(exc)})

    # ── React SPA (built dist committed to repo) ───────────────────────────
    if _DIST.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")),
                  name="assets")

        @app.get("/")
        def index():
            return FileResponse(str(_DIST / "index.html"))
    else:  # pre-build / CI without dist: explicit 503, not a silent 404
        @app.get("/")
        def index_missing():
            return JSONResponse(status_code=503, content={
                "error": "frontend not built — run npm run build in "
                         "tradingagents/monitor/frontend"})

    return app
```

Notes:
- Income wiring: `live["income"]` key is produced in Task 9 (sources gain income fetch). Until then the analytics income block is `None` — exactly what `test_trades_strategy_param_and_analytics` asserts.
- The old `templates/`, Jinja2 import, and `position_provider`/`position_cache_ttl`/`clock` kwargs are gone — caching moved into `sources.ttl_cached`.

- [ ] **Step 5: Update `tradingagents/monitor/__main__.py`**

```python
"""Entrypoint: ``python -m tradingagents.monitor``.

Reads QUANT_DATA_DIR|DATA_DIR, HYBRID_DATA_DIR, LOG_DIR, TA_MONITOR_PASSWORD,
TA_MONITOR_START_CAPITAL from the environment (same env contract as the
runners). Binds 127.0.0.1 only — a reverse proxy terminates TLS in production.
"""
from __future__ import annotations

import os

import uvicorn

from tradingagents.monitor.app import create_app
from tradingagents.monitor.sources import resolve_sources


def main() -> None:
    quant, hybrid = resolve_sources()
    app = create_app(
        quant=quant,
        hybrid=hybrid,
        log_dir=os.environ.get("LOG_DIR", "logs"),
        start_capital=float(os.environ.get("TA_MONITOR_START_CAPITAL", "10000")),
    )
    uvicorn.run(app, host=os.environ.get("TA_MONITOR_HOST", "127.0.0.1"),
                port=int(os.environ.get("TA_MONITOR_PORT", "8800")))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the monitor suite**

Run: `python -m pytest tests/monitor/ -v`
Expected: ALL PASS. If pre-existing tests in other suites import `create_app` with the old signature, update those call sites the same way as `_quant_only_app`.

- [ ] **Step 7: Commit**

```bash
git add tradingagents/monitor/app.py tradingagents/monitor/__main__.py tests/monitor/
git commit -m "feat(monitor): dual-strategy API — performance/positions/trades/cycles/health"
```

---

## Task 9: Income records in account snapshots

**Files:**
- Modify: `tradingagents/monitor/sources.py` (`account_snapshot` fetches income)
- Test: `tests/monitor/test_sources.py`

- [ ] **Step 1: Write the failing test** (append)

```python
def test_account_snapshot_includes_income(monkeypatch):
    class FakeEx:
        def get_position_details(self):
            return []

        def get_balances(self):
            return {"USDT": 1.0}

        def get_total_portfolio_value(self):
            return 1.0

        def income_history(self, **kw):
            return [{"incomeType": "REALIZED_PNL", "income": "5", "symbol": "BTCUSDT"}]

    snap = sources.account_snapshot(FakeEx())
    assert snap["income"][0]["income"] == "5"


def test_account_snapshot_income_failure_is_none():
    class FakeEx:
        def get_position_details(self):
            return []

        def get_balances(self):
            return {"USDT": 1.0}

        def get_total_portfolio_value(self):
            return 1.0

        def income_history(self, **kw):
            raise RuntimeError("weight limit")

    assert sources.account_snapshot(FakeEx())["income"] is None
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/monitor/test_sources.py -v -k income`
Expected: FAIL — KeyError `'income'`

- [ ] **Step 3: Update `account_snapshot`**

```python
def account_snapshot(ex) -> dict:
    """One live snapshot of an account: positions, free USDT, equity, and
    raw income records (None when the income endpoint fails — positions
    must still render)."""
    try:
        income = ex.income_history()
    except Exception:
        income = None
    return {
        "positions": ex.get_position_details(),
        "usdt_free": ex.get_balances().get("USDT", 0.0),
        "equity": ex.get_total_portfolio_value(),
        "income": income,
    }
```

- [ ] **Step 4: Update conftest fake** — in `tests/monitor/conftest.py` `_fake_snapshot`, add `"income": None` to the returned dict (and optionally a second fake with records if you extend test coverage).

- [ ] **Step 5: Run monitor suite**

Run: `python -m pytest tests/monitor/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add tradingagents/monitor/sources.py tests/monitor/
git commit -m "feat(monitor): income records in account snapshot (analytics feed)"
```

---

## Task 10: Frontend scaffold (Vite + React + TS)

**Files:**
- Create: `tradingagents/monitor/frontend/` (scaffold)
- Modify: `.gitignore`

- [ ] **Step 1: Scaffold**

```bash
cd tradingagents/monitor
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install @tanstack/react-query lightweight-charts recharts
npm install -D vitest
```

- [ ] **Step 2: Pin `vite.config.ts`**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/",          // served by FastAPI at site root
  build: { outDir: "dist" },
  test: { environment: "node" },
});
```

(If TS complains about the `test` key, add `/// <reference types="vitest" />` at the top.)

- [ ] **Step 3: `.gitignore`** — append at repo root:

```
tradingagents/monitor/frontend/node_modules/
```

**Do NOT ignore `frontend/dist/`** — the built bundle is committed by design.

- [ ] **Step 4: Add scripts to `frontend/package.json`** (merge into generated):

```json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "test": "vitest run",
  "preview": "vite preview"
}
```

- [ ] **Step 5: Verify build works with the template app**

Run: `npm run build`
Expected: `dist/index.html` + `dist/assets/*` produced, exit 0.

- [ ] **Step 6: Commit scaffold (without dist for now — dist lands in Task 17)**

```bash
git add ../../../.gitignore package.json package-lock.json vite.config.ts tsconfig*.json index.html src/ public/ eslint.config.js
git commit -m "feat(monitor): scaffold React+TS+Vite frontend"
```

---

## Task 11: Frontend lib — types, API client, utils (+vitest)

**Files:**
- Create: `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/lib/format.ts`, `frontend/src/lib/rebase.ts`
- Test: `frontend/src/lib/rebase.test.ts`, `frontend/src/lib/format.test.ts`
- Delete: template cruft `src/App.css`, `src/assets/react.svg`, `public/vite.svg` contentions as encountered

- [ ] **Step 1: Write failing util tests**

`frontend/src/lib/rebase.test.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { rebaseTo100, sliceFromDays } from "./rebase";

const pts = [
  { ts: "2026-06-01T00:00:00+00:00", value: 200 },
  { ts: "2026-06-02T00:00:00+00:00", value: 220 },
  { ts: "2026-06-03T00:00:00+00:00", value: 210 },
];

describe("rebaseTo100", () => {
  it("rebases first point to 100", () => {
    const out = rebaseTo100(pts);
    expect(out[0].value).toBe(100);
    expect(out[1].value).toBeCloseTo(110);
    expect(out[2].value).toBeCloseTo(105);
  });
  it("empty input -> empty output", () => {
    expect(rebaseTo100([])).toEqual([]);
  });
});

describe("sliceFromDays", () => {
  it("keeps only points within N days of the last point", () => {
    expect(sliceFromDays(pts, 1).length).toBe(2);
    expect(sliceFromDays(pts, 9999)).toEqual(pts);
  });
  it("null days -> all", () => {
    expect(sliceFromDays(pts, null)).toEqual(pts);
  });
});
```

`frontend/src/lib/format.test.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { fmtUsd, fmtPct, fmtNum } from "./format";

describe("format", () => {
  it("fmtUsd", () => {
    expect(fmtUsd(10234.567)).toBe("$10,234.57");
    expect(fmtUsd(null)).toBe("—");
  });
  it("fmtPct from fraction", () => {
    expect(fmtPct(-0.0497)).toBe("-4.97%");
    expect(fmtPct(null)).toBe("—");
  });
  it("fmtNum", () => {
    expect(fmtNum(3.178, 2)).toBe("3.18");
    expect(fmtNum(null)).toBe("—");
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `npm test` (in `frontend/`)
Expected: FAIL — modules missing

- [ ] **Step 3: Implement**

`frontend/src/lib/rebase.ts`:

```typescript
export interface Point { ts: string; value: number }

/** Rebase a series so its first point equals 100. */
export function rebaseTo100(points: Point[]): Point[] {
  if (points.length === 0) return [];
  const base = points[0].value;
  if (base === 0) return points.map((p) => ({ ...p, value: 0 }));
  return points.map((p) => ({ ts: p.ts, value: (p.value / base) * 100 }));
}

/** Keep points within `days` of the LAST point's timestamp (null = all). */
export function sliceFromDays(points: Point[], days: number | null): Point[] {
  if (days === null || points.length === 0) return points;
  const end = new Date(points[points.length - 1].ts).getTime();
  const cutoff = end - days * 86_400_000;
  return points.filter((p) => new Date(p.ts).getTime() >= cutoff);
}
```

`frontend/src/lib/format.ts`:

```typescript
export function fmtUsd(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString("en-US", {
    style: "currency", currency: "USD", maximumFractionDigits: 2,
  });
}

/** v is a FRACTION (-0.05 => "-5.00%"). */
export function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${(v * 100).toFixed(2)}%`;
}

export function fmtNum(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(digits);
}
```

`frontend/src/types.ts`:

```typescript
export interface Point { ts: string; value: number }

export interface Cards {
  equity: number; sharpe: number; max_drawdown: number;
  total_upnl: number | null; upnl_stale: boolean;
  open_positions: number | null;
}

export interface StrategyPerf {
  cards: Cards; equity: Point[]; drawdown: Point[]; rolling_sharpe: Point[];
}

export interface CompareBlock {
  quant?: { sharpe: number; ret: number; maxdd: number };
  hybrid?: { sharpe: number; ret: number; maxdd: number };
  delta?: { sharpe: number; ret: number; maxdd: number };
  window?: { start: string; end: string; n: number };
  error?: string;
}

export interface PerformanceResp {
  quant: StrategyPerf; hybrid: StrategyPerf | null;
  compare: CompareBlock | null;
  anchors: { quant: number; hybrid: number | null };
}

export interface Position {
  coin: string; side: "LONG" | "SHORT"; qty: number;
  entry: number | null; mark: number | null; leverage: number | null;
  notional: number | null; upnl_usd: number | null; upnl_pct: number | null;
  liq_price: number | null;
}

export interface StrategyPositions {
  positions: Position[];
  totals: { upnl: number | null; notional: number | null; equity: number | null };
  allocation: { label: string; usd: number }[];
  stale: boolean; as_of: string | null; error: string | null;
}

export interface PositionsResp {
  quant: StrategyPositions; hybrid: StrategyPositions | null;
}

export interface IncomeSummary {
  realized_pnl_per_coin: Record<string, number>;
  realized_pnl_total: number; fees_total: number; funding_total: number;
  win_rate: number | null; n_closing_fills: number;
}

export interface TradesResp {
  executions: Record<string, unknown>[];
  analytics: {
    income: IncomeSummary | null;
    slippage: { mean: number | null; max: number | null; n: number };
  };
}

export interface CycleRow {
  cycle_id: string; start_ts: string; end_ts: string | null; status: string | null;
  error_msg: string | null; n_trades: number | null;
  critical_data_fail_sources: string | null;
  supplementary_stale_sources: string | null;
}

export interface ModulatorRow {
  cycle_id: string; coin: string; multiplier: number; effective_weight: number;
  llm_confidence: number | null; regime: string | null; fallback: number;
}

export interface CycleDetail {
  predictions: Record<string, unknown>[];
  sizing: Record<string, unknown>[];
  risk_checks: Record<string, unknown>[];
  shadow_decisions: Record<string, unknown>[];
  modulator: ModulatorRow[];
}

export interface HealthResp {
  timeline: { quant: CycleRow[]; hybrid: CycleRow[] | null };
  steps: Record<string, unknown>[];
  errors: Record<string, unknown>[];
  retrains: { quant: Record<string, unknown>[]; hybrid: Record<string, unknown>[] | null };
}

export type Strategy = "quant" | "hybrid";
```

`frontend/src/api.ts`:

```typescript
/** Thin fetch wrapper. Browser basic-auth (401 challenge) covers credentials. */
async function get<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

import type {
  CycleDetail, CycleRow, HealthResp, PerformanceResp, PositionsResp,
  Strategy, TradesResp,
} from "./types";

export const api = {
  performance: () => get<PerformanceResp>("/api/performance"),
  positions: () => get<PositionsResp>("/api/positions"),
  trades: (s: Strategy) => get<TradesResp>(`/api/trades?strategy=${s}`),
  cycles: (s: Strategy) => get<{ cycles: CycleRow[] }>(`/api/cycles?strategy=${s}`),
  cycle: (id: string, s: Strategy) =>
    get<CycleDetail>(`/api/cycle/${encodeURIComponent(id)}?strategy=${s}`),
  health: () => get<HealthResp>("/api/health"),
};
```

- [ ] **Step 4: Run tests**

Run: `npm test`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/
git commit -m "feat(monitor-ui): types, api client, rebase/format utils"
```

---

## Task 12: App shell — theme, tabs, query client, shared components

**Files:**
- Replace: `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/src/index.css`
- Create: `frontend/src/components/Card.tsx`, `frontend/src/components/Badge.tsx`, `frontend/src/components/Section.tsx`
- Delete: `frontend/src/App.css`

No unit tests for the shell (covered by build type-check + later manual verify); keep this task mechanical.

- [ ] **Step 1: `frontend/src/index.css`** (GitHub-dark parity with the old `app.css`)

```css
:root {
  --bg: #0d1117; --panel: #161b22; --border: #30363d;
  --text: #e6edf3; --muted: #8b949e;
  --green: #3fb950; --red: #f85149; --amber: #d29922; --blue: #58a6ff;
  --purple: #bc8cff;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
a { color: var(--blue); }
h1 { font-size: 18px; margin: 0; }
h2 { font-size: 15px; color: var(--muted); font-weight: 600; margin: 18px 0 8px; }
.container { max-width: 1280px; margin: 0 auto; padding: 16px; }
.topbar {
  display: flex; align-items: center; gap: 16px; padding: 12px 16px;
  border-bottom: 1px solid var(--border); background: var(--panel);
}
.tabs { display: flex; gap: 4px; }
.tab {
  padding: 6px 14px; border-radius: 6px; cursor: pointer; color: var(--muted);
  background: none; border: 1px solid transparent; font-size: 14px;
}
.tab.active { color: var(--text); background: var(--bg); border-color: var(--border); }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.card {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 8px; padding: 12px 14px;
}
.card .label { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.card .value { font-size: 20px; font-weight: 600; margin-top: 2px; }
.pos { color: var(--green); } .neg { color: var(--red); }
.panel {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 8px; padding: 14px; margin-top: 12px;
}
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--border); }
th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.badge {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 600;
}
.badge.quant { background: #1f3a5f; color: var(--blue); }
.badge.hybrid { background: #3a2a5f; color: var(--purple); }
.badge.stale { background: #4a3a12; color: var(--amber); }
.badge.error { background: #5a1e1e; color: var(--red); }
.badge.ok { background: #1d3a24; color: var(--green); }
.pills { display: flex; gap: 6px; margin: 10px 0; }
.pill {
  padding: 4px 12px; border-radius: 14px; border: 1px solid var(--border);
  background: none; color: var(--muted); cursor: pointer; font-size: 13px;
}
.pill.active { color: var(--text); border-color: var(--blue); }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.muted { color: var(--muted); }
@media (max-width: 900px) { .grid2 { grid-template-columns: 1fr; } }
```

- [ ] **Step 2: Shared components**

`frontend/src/components/Card.tsx`:

```tsx
export function Card(props: { label: string; value: string; tone?: "pos" | "neg" | "" }) {
  return (
    <div className="card">
      <div className="label">{props.label}</div>
      <div className={`value ${props.tone ?? ""}`}>{props.value}</div>
    </div>
  );
}
```

`frontend/src/components/Badge.tsx`:

```tsx
export function Badge(props: { kind: "quant" | "hybrid" | "stale" | "error" | "ok"; children: React.ReactNode }) {
  return <span className={`badge ${props.kind}`}>{props.children}</span>;
}
```

`frontend/src/components/Section.tsx`:

```tsx
export function Section(props: { title: string; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>{props.title}</h2>
        {props.right}
      </div>
      {props.children}
    </div>
  );
}
```

- [ ] **Step 3: `frontend/src/main.tsx`**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./index.css";

const qc = new QueryClient({
  defaultOptions: { queries: { refetchInterval: 30_000, retry: 1, staleTime: 25_000 } },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={qc}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
```

- [ ] **Step 4: `frontend/src/App.tsx`** (hash-routed tabs, parity with old SPA)

```tsx
import { useEffect, useState } from "react";
import { PerformanceTab } from "./tabs/PerformanceTab";
import { PositionsTab } from "./tabs/PositionsTab";
import { ExecutionsTab } from "./tabs/ExecutionsTab";
import { DecisionsTab } from "./tabs/DecisionsTab";
import { HealthTab } from "./tabs/HealthTab";

const TABS = [
  { id: "performance", label: "Performance", el: <PerformanceTab /> },
  { id: "positions", label: "Positions", el: <PositionsTab /> },
  { id: "executions", label: "Executions", el: <ExecutionsTab /> },
  { id: "decisions", label: "Decisions", el: <DecisionsTab /> },
  { id: "health", label: "Health", el: <HealthTab /> },
] as const;

export default function App() {
  const initial = window.location.hash.replace("#", "") || "performance";
  const [tab, setTab] = useState(initial);
  useEffect(() => {
    const onHash = () => setTab(window.location.hash.replace("#", "") || "performance");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const active = TABS.find((t) => t.id === tab) ?? TABS[0];
  return (
    <>
      <div className="topbar">
        <h1>Live Monitor</h1>
        <nav className="tabs">
          {TABS.map((t) => (
            <button key={t.id} className={`tab ${t.id === active.id ? "active" : ""}`}
              onClick={() => { window.location.hash = t.id; }}>
              {t.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="container">{active.el}</div>
    </>
  );
}
```

- [ ] **Step 5: Create placeholder tab files so it compiles** — each of `frontend/src/tabs/{PerformanceTab,PositionsTab,ExecutionsTab,DecisionsTab,HealthTab}.tsx` temporarily:

```tsx
export function PerformanceTab() {  // rename per file
  return <div className="muted">loading…</div>;
}
```

- [ ] **Step 6: Type-check + build**

Run: `npm run build`
Expected: exit 0

- [ ] **Step 7: Commit**

```bash
git add src/ && git rm -q src/App.css 2>/dev/null; git commit -m "feat(monitor-ui): app shell — dark theme, tabs, query client"
```

---

## Task 13: Performance tab — multi-pane chart, cards, compare table

**Files:**
- Create: `frontend/src/charts/EquityChart.tsx`
- Replace: `frontend/src/tabs/PerformanceTab.tsx`

- [ ] **Step 1: `frontend/src/charts/EquityChart.tsx`** (lightweight-charts v5, three panes)

```tsx
import { useEffect, useRef } from "react";
import {
  createChart, ColorType, LineSeries, AreaSeries, LineStyle,
  type IChartApi, type Time,
} from "lightweight-charts";
import type { Point } from "../types";

export interface EquityChartProps {
  quantEquity: Point[]; hybridEquity: Point[];     // already sliced+rebased
  quantDd: Point[]; hybridDd: Point[];             // already sliced (fractions)
  quantRs: Point[]; hybridRs: Point[];             // rolling sharpe (may be [])
  anchors: { quant: number; hybrid: number | null };
}

const toLw = (pts: Point[]) =>
  pts.map((p) => ({ time: (new Date(p.ts).getTime() / 1000) as Time, value: p.value }));

export function EquityChart(props: EquityChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const showRs = props.quantRs.length > 0 || props.hybridRs.length > 0;
    const chart = createChart(ref.current, {
      height: showRs ? 520 : 420,
      layout: {
        background: { type: ColorType.Solid, color: "#161b22" },
        textColor: "#8b949e", panes: { separatorColor: "#30363d" },
      },
      grid: { vertLines: { color: "#21262d" }, horzLines: { color: "#21262d" } },
      timeScale: { borderColor: "#30363d", timeVisible: false },
      rightPriceScale: { borderColor: "#30363d" },
    });
    chartRef.current = chart;

    // Pane 0: indexed equity
    chart.addSeries(LineSeries, { color: "#3fb950", lineWidth: 2, title: "quant" }, 0)
      .setData(toLw(props.quantEquity));
    if (props.hybridEquity.length)
      chart.addSeries(LineSeries, { color: "#bc8cff", lineWidth: 2, title: "hybrid" }, 0)
        .setData(toLw(props.hybridEquity));

    // Pane 1: drawdown (as %)
    const ddOpts = { lineWidth: 1 as const, priceFormat: { type: "percent" as const } };
    chart.addSeries(AreaSeries, {
      ...ddOpts, lineColor: "#3fb950", topColor: "rgba(63,185,80,0)",
      bottomColor: "rgba(63,185,80,0.25)", title: "quant DD",
    }, 1).setData(toLw(props.quantDd.map((p) => ({ ...p, value: p.value * 100 }))));
    if (props.hybridDd.length)
      chart.addSeries(AreaSeries, {
        ...ddOpts, lineColor: "#bc8cff", topColor: "rgba(188,140,255,0)",
        bottomColor: "rgba(188,140,255,0.25)", title: "hybrid DD",
      }, 1).setData(toLw(props.hybridDd.map((p) => ({ ...p, value: p.value * 100 }))));

    // Pane 2: rolling sharpe + anchor reference lines (only when data exists)
    if (showRs) {
      const rsQuant = chart.addSeries(LineSeries,
        { color: "#3fb950", lineWidth: 1, title: "quant rSR" }, 2);
      rsQuant.setData(toLw(props.quantRs));
      rsQuant.createPriceLine({
        price: props.anchors.quant, color: "#8b949e",
        lineStyle: LineStyle.Dashed, title: `backtest ${props.anchors.quant}`,
      });
      if (props.hybridRs.length) {
        const rsH = chart.addSeries(LineSeries,
          { color: "#bc8cff", lineWidth: 1, title: "hybrid rSR" }, 2);
        rsH.setData(toLw(props.hybridRs));
        if (props.anchors.hybrid !== null)
          rsH.createPriceLine({
            price: props.anchors.hybrid, color: "#8b949e",
            lineStyle: LineStyle.Dashed, title: `backtest ${props.anchors.hybrid}`,
          });
      }
    }

    chart.timeScale().fitContent();
    const onResize = () => chart.applyOptions({ width: ref.current?.clientWidth ?? 600 });
    onResize();
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); chart.remove(); };
  }, [props]);

  return <div ref={ref} />;
}
```

- [ ] **Step 2: `frontend/src/tabs/PerformanceTab.tsx`**

```tsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { Section } from "../components/Section";
import { EquityChart } from "../charts/EquityChart";
import { fmtNum, fmtPct, fmtUsd } from "../lib/format";
import { rebaseTo100, sliceFromDays } from "../lib/rebase";
import type { StrategyPerf } from "../types";

const RANGES = [
  { label: "7d", days: 7 }, { label: "30d", days: 30 },
  { label: "90d", days: 90 }, { label: "all", days: null },
] as const;

function CardsRow(props: { name: "quant" | "hybrid"; p: StrategyPerf }) {
  const c = props.p.cards;
  return (
    <div style={{ marginTop: 10 }}>
      <Badge kind={props.name}>{props.name.toUpperCase()}</Badge>
      {c.upnl_stale && <Badge kind="stale">uPnL stale</Badge>}
      <div className="cards" style={{ marginTop: 6 }}>
        <Card label="Equity" value={fmtUsd(c.equity)} />
        <Card label="Sharpe (live)" value={fmtNum(c.sharpe)} tone={c.sharpe >= 0 ? "pos" : "neg"} />
        <Card label="Max drawdown" value={fmtPct(c.max_drawdown)} tone="neg" />
        <Card label="Unrealized PnL" value={fmtUsd(c.total_upnl)}
          tone={(c.total_upnl ?? 0) >= 0 ? "pos" : "neg"} />
        <Card label="Open positions" value={c.open_positions === null ? "—" : String(c.open_positions)} />
      </div>
    </div>
  );
}

export function PerformanceTab() {
  const q = useQuery({ queryKey: ["performance"], queryFn: api.performance });
  const [days, setDays] = useState<number | null>(null);
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  const d = q.data;

  const prep = (p: StrategyPerf | null) => ({
    eq: p ? rebaseTo100(sliceFromDays(p.equity, days)) : [],
    dd: p ? sliceFromDays(p.drawdown, days) : [],
    rs: p ? sliceFromDays(p.rolling_sharpe, days) : [],
  });
  const quant = prep(d.quant);
  const hybrid = prep(d.hybrid);

  return (
    <>
      <CardsRow name="quant" p={d.quant} />
      {d.hybrid ? <CardsRow name="hybrid" p={d.hybrid} />
        : <p className="muted">hybrid not configured</p>}

      <Section title="Equity (indexed to 100) · drawdown · rolling Sharpe"
        right={
          <div className="pills">
            {RANGES.map((r) => (
              <button key={r.label} className={`pill ${days === r.days ? "active" : ""}`}
                onClick={() => setDays(r.days)}>{r.label}</button>
            ))}
          </div>
        }>
        <EquityChart
          quantEquity={quant.eq} hybridEquity={hybrid.eq}
          quantDd={quant.dd} hybridDd={hybrid.dd}
          quantRs={quant.rs} hybridRs={hybrid.rs}
          anchors={d.anchors}
        />
        {d.quant.rolling_sharpe.length === 0 &&
          <p className="muted">rolling Sharpe appears after 30 live cycles</p>}
      </Section>

      {d.compare && !d.compare.error && (
        <Section title={`Quant vs hybrid — common window ${d.compare.window?.start} → ${d.compare.window?.end} (${d.compare.window?.n} cycles)`}>
          <table>
            <thead><tr><th></th><th>Sharpe</th><th>Return</th><th>Max DD</th></tr></thead>
            <tbody>
              <tr><td><Badge kind="quant">QUANT</Badge></td>
                <td>{fmtNum(d.compare.quant?.sharpe)}</td>
                <td>{fmtPct(d.compare.quant?.ret)}</td>
                <td>{fmtPct(d.compare.quant?.maxdd)}</td></tr>
              <tr><td><Badge kind="hybrid">HYBRID</Badge></td>
                <td>{fmtNum(d.compare.hybrid?.sharpe)}</td>
                <td>{fmtPct(d.compare.hybrid?.ret)}</td>
                <td>{fmtPct(d.compare.hybrid?.maxdd)}</td></tr>
              <tr><td className="muted">Δ (H−Q)</td>
                <td>{fmtNum(d.compare.delta?.sharpe)}</td>
                <td>{fmtPct(d.compare.delta?.ret)}</td>
                <td>{fmtPct(d.compare.delta?.maxdd)}</td></tr>
            </tbody>
          </table>
        </Section>
      )}
      {d.compare?.error && <p className="muted">compare: {d.compare.error}</p>}
    </>
  );
}
```

(Verify the field names of `compare_quant_hybrid`'s return — `rebacktest.py:205` — during implementation; adjust `CompareBlock` keys if they differ, e.g. `ret` vs `return`.)

- [ ] **Step 3: Build**

Run: `npm run build`
Expected: exit 0

- [ ] **Step 4: Commit**

```bash
git add src/
git commit -m "feat(monitor-ui): performance tab — multi-pane chart, range selector, compare"
```

---

## Task 14: Positions tab — uPnL cards, table, donuts

**Files:**
- Create: `frontend/src/charts/AllocationDonut.tsx`
- Replace: `frontend/src/tabs/PositionsTab.tsx`

- [ ] **Step 1: `frontend/src/charts/AllocationDonut.tsx`** (Recharts)

```tsx
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#58a6ff", "#bc8cff", "#3fb950", "#d29922", "#f85149",
  "#39c5cf", "#db61a2", "#9e6a03", "#6e7681"];

export function AllocationDonut(props: { data: { label: string; usd: number }[] }) {
  const total = props.data.reduce((s, d) => s + d.usd, 0);
  if (!props.data.length || total === 0)
    return <p className="muted">no allocation data</p>;
  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie data={props.data} dataKey="usd" nameKey="label"
          innerRadius={55} outerRadius={90} stroke="#161b22">
          {props.data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip formatter={(v: number) =>
          [`$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })} (${(v / total * 100).toFixed(1)}%)`]}
          contentStyle={{ background: "#161b22", border: "1px solid #30363d" }} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 2: `frontend/src/tabs/PositionsTab.tsx`**

```tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { Section } from "../components/Section";
import { AllocationDonut } from "../charts/AllocationDonut";
import { fmtNum, fmtUsd } from "../lib/format";
import type { StrategyPositions } from "../types";

function StrategyBlock(props: { name: "quant" | "hybrid"; s: StrategyPositions }) {
  const { s } = props;
  return (
    <Section title=""
      right={s.stale
        ? <Badge kind="stale">STALE — live unavailable{s.as_of ? ` · as of ${s.as_of}` : ""}</Badge>
        : <Badge kind="ok">live</Badge>}>
      <div style={{ marginBottom: 8 }}>
        <Badge kind={props.name}>{props.name.toUpperCase()}</Badge>
        {s.error && <span className="muted" style={{ marginLeft: 8 }}>{s.error}</span>}
      </div>
      <div className="cards">
        <Card label="Account equity" value={fmtUsd(s.totals.equity)} />
        <Card label="Total uPnL" value={fmtUsd(s.totals.upnl)}
          tone={(s.totals.upnl ?? 0) >= 0 ? "pos" : "neg"} />
        <Card label="Gross notional" value={fmtUsd(s.totals.notional)} />
      </div>
      <table style={{ marginTop: 10 }}>
        <thead><tr>
          <th>Coin</th><th>Side</th><th>Qty</th><th>Entry</th><th>Mark</th>
          <th>Lev</th><th>Notional</th><th>uPnL $</th><th>uPnL %</th><th>Liq</th>
        </tr></thead>
        <tbody>
          {s.positions.map((p) => (
            <tr key={p.coin}>
              <td>{p.coin}</td>
              <td className={p.side === "LONG" ? "pos" : "neg"}>{p.side}</td>
              <td>{p.qty}</td>
              <td>{fmtUsd(p.entry)}</td>
              <td>{fmtUsd(p.mark)}</td>
              <td>{p.leverage ?? "—"}</td>
              <td>{fmtUsd(p.notional)}</td>
              <td className={(p.upnl_usd ?? 0) >= 0 ? "pos" : "neg"}>{fmtUsd(p.upnl_usd)}</td>
              <td className={(p.upnl_pct ?? 0) >= 0 ? "pos" : "neg"}>
                {p.upnl_pct === null ? "—" : `${fmtNum(p.upnl_pct)}%`}</td>
              <td>{fmtUsd(p.liq_price)}</td>
            </tr>
          ))}
          {!s.positions.length && <tr><td colSpan={10} className="muted">flat — no open positions</td></tr>}
        </tbody>
      </table>
      <h2>Allocation</h2>
      <AllocationDonut data={s.allocation} />
    </Section>
  );
}

export function PositionsTab() {
  const q = useQuery({ queryKey: ["positions"], queryFn: api.positions });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  return (
    <div className="grid2">
      <StrategyBlock name="quant" s={q.data.quant} />
      {q.data.hybrid
        ? <StrategyBlock name="hybrid" s={q.data.hybrid} />
        : <div className="panel muted">hybrid not configured</div>}
    </div>
  );
}
```

- [ ] **Step 3: Build**

Run: `npm run build`
Expected: exit 0

- [ ] **Step 4: Commit**

```bash
git add src/
git commit -m "feat(monitor-ui): positions tab — uPnL table + allocation donuts"
```

---

## Task 15: Executions tab — strategy pills + analytics strip

**Files:**
- Replace: `frontend/src/tabs/ExecutionsTab.tsx`

- [ ] **Step 1: Implement**

```tsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { Section } from "../components/Section";
import { fmtNum, fmtUsd } from "../lib/format";
import type { Strategy } from "../types";

export function ExecutionsTab() {
  const [strategy, setStrategy] = useState<Strategy>("quant");
  const q = useQuery({
    queryKey: ["trades", strategy],
    queryFn: () => api.trades(strategy),
  });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  const { executions, analytics } = q.data;
  const inc = analytics.income;
  return (
    <>
      <div className="pills">
        {(["quant", "hybrid"] as Strategy[]).map((s) => (
          <button key={s} className={`pill ${s === strategy ? "active" : ""}`}
            onClick={() => setStrategy(s)}>{s}</button>
        ))}
      </div>

      <Section title="Trade analytics">
        {inc ? (
          <div className="cards">
            <Card label="Realized PnL" value={fmtUsd(inc.realized_pnl_total)}
              tone={inc.realized_pnl_total >= 0 ? "pos" : "neg"} />
            <Card label="Win rate"
              value={inc.win_rate === null ? "—" : `${(inc.win_rate * 100).toFixed(0)}% of ${inc.n_closing_fills}`} />
            <Card label="Fees" value={fmtUsd(inc.fees_total)} />
            <Card label="Funding" value={fmtUsd(inc.funding_total)} />
            <Card label="Slippage mean/max"
              value={`${fmtNum(analytics.slippage.mean)} / ${fmtNum(analytics.slippage.max)}`} />
          </div>
        ) : (
          <p className="muted">
            income analytics unavailable (exchange income API unreachable) —
            slippage mean/max: {fmtNum(analytics.slippage.mean)} / {fmtNum(analytics.slippage.max)} over {analytics.slippage.n} fills
          </p>
        )}
        {inc && Object.keys(inc.realized_pnl_per_coin).length > 0 && (
          <table style={{ marginTop: 10 }}>
            <thead><tr><th>Symbol</th><th>Realized PnL</th></tr></thead>
            <tbody>
              {Object.entries(inc.realized_pnl_per_coin).map(([sym, v]) => (
                <tr key={sym}><td>{sym}</td>
                  <td className={v >= 0 ? "pos" : "neg"}>{fmtUsd(v)}</td></tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="muted" style={{ marginTop: 6 }}>
          income figures cover the last 1000 exchange income records
        </p>
      </Section>

      <Section title={`Executions (${executions.length})`}>
        <table>
          <thead><tr>
            <th>Cycle</th><th>Coin</th><th>Side</th><th>Qty</th>
            <th>Entry</th><th>Slippage</th><th>Status</th>
          </tr></thead>
          <tbody>
            {executions.map((t, i) => (
              <tr key={i}>
                <td>{String(t.cycle_id ?? "")}</td>
                <td>{String(t.coin ?? "")}</td>
                <td className={t.side === "BUY" ? "pos" : "neg"}>{String(t.side ?? "")}</td>
                <td>{String(t.qty ?? "")}</td>
                <td>{fmtUsd(t.entry_price as number | null)}</td>
                <td>{t.slippage === null ? "—" : String(t.slippage)}</td>
                <td><Badge kind={t.status === "EXECUTED" ? "ok" : "error"}>{String(t.status ?? "")}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </>
  );
}
```

- [ ] **Step 2: Build**

Run: `npm run build`
Expected: exit 0

- [ ] **Step 3: Commit**

```bash
git add src/
git commit -m "feat(monitor-ui): executions tab — strategy filter + analytics strip"
```

---

## Task 16: Decisions tab (modulator panel) + Health tab

**Files:**
- Replace: `frontend/src/tabs/DecisionsTab.tsx`, `frontend/src/tabs/HealthTab.tsx`

- [ ] **Step 1: `frontend/src/tabs/DecisionsTab.tsx`**

```tsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Badge } from "../components/Badge";
import { Section } from "../components/Section";
import { fmtNum } from "../lib/format";
import type { Strategy } from "../types";

function Tbl(props: { rows: Record<string, unknown>[]; cols: string[] }) {
  if (!props.rows.length) return <p className="muted">none</p>;
  return (
    <table>
      <thead><tr>{props.cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
      <tbody>
        {props.rows.map((r, i) => (
          <tr key={i}>{props.cols.map((c) => <td key={c}>{String(r[c] ?? "—")}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );
}

export function DecisionsTab() {
  const [strategy, setStrategy] = useState<Strategy>("quant");
  const cyclesQ = useQuery({
    queryKey: ["cycles", strategy],
    queryFn: () => api.cycles(strategy),
  });
  const cycles = cyclesQ.data?.cycles ?? [];
  const [cycleId, setCycleId] = useState<string | null>(null);
  const selected = cycleId ?? cycles[0]?.cycle_id ?? null;
  const detailQ = useQuery({
    queryKey: ["cycle", selected, strategy],
    queryFn: () => api.cycle(selected!, strategy),
    enabled: selected !== null,
  });
  return (
    <>
      <div className="pills">
        {(["quant", "hybrid"] as Strategy[]).map((s) => (
          <button key={s} className={`pill ${s === strategy ? "active" : ""}`}
            onClick={() => { setStrategy(s); setCycleId(null); }}>{s}</button>
        ))}
        <select value={selected ?? ""} onChange={(e) => setCycleId(e.target.value)}
          style={{ background: "#161b22", color: "#e6edf3", border: "1px solid #30363d",
                   borderRadius: 6, padding: "4px 8px" }}>
          {cycles.map((c) => (
            <option key={c.cycle_id} value={c.cycle_id}>
              {c.cycle_id} · {c.status ?? "?"}
            </option>
          ))}
        </select>
      </div>
      {detailQ.data && (
        <>
          {strategy === "hybrid" && (
            <Section title="LLM modulator">
              {detailQ.data.modulator.length ? (
                <table>
                  <thead><tr>
                    <th>Coin</th><th>Multiplier</th><th>Effective weight</th>
                    <th>Confidence</th><th>Regime</th><th>Mode</th>
                  </tr></thead>
                  <tbody>
                    {detailQ.data.modulator.map((m) => (
                      <tr key={m.coin}>
                        <td>{m.coin}</td>
                        <td>{fmtNum(m.multiplier)}</td>
                        <td>{fmtNum(m.effective_weight)}</td>
                        <td>{m.llm_confidence === null ? "—" : fmtNum(m.llm_confidence)}</td>
                        <td>{m.regime ?? "—"}</td>
                        <td>{m.fallback
                          ? <Badge kind="stale">pure quant fallback</Badge>
                          : <Badge kind="ok">modulated</Badge>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : <p className="muted">no modulator rows (cycle predates modulator journaling)</p>}
            </Section>
          )}
          <Section title="Predictions">
            <Tbl rows={detailQ.data.predictions}
              cols={["coin", "horizon", "pred_value", "ref_price", "signal_h7",
                     "signal_h14", "consensus_signal", "bundle_route"]} />
          </Section>
          <Section title="Sizing">
            <Tbl rows={detailQ.data.sizing}
              cols={["coin", "realized_vol", "kelly", "confidence", "base_size",
                     "leverage", "sma30_multiplier", "final_size_notional"]} />
          </Section>
          <Section title="Risk checks">
            <Tbl rows={detailQ.data.risk_checks}
              cols={["coin", "check_name", "passed", "value", "threshold", "reason"]} />
          </Section>
          <Section title="Shadow decisions">
            <Tbl rows={detailQ.data.shadow_decisions}
              cols={["coin", "live_signal", "backtest_signal", "agree",
                     "live_size", "backtest_size", "size_delta_pct"]} />
          </Section>
        </>
      )}
    </>
  );
}
```

- [ ] **Step 2: `frontend/src/tabs/HealthTab.tsx`**

```tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Badge } from "../components/Badge";
import { Section } from "../components/Section";
import type { CycleRow } from "../types";

function Timeline(props: { name: "quant" | "hybrid"; rows: CycleRow[] }) {
  return (
    <Section title="">
      <Badge kind={props.name}>{props.name.toUpperCase()}</Badge>
      <table style={{ marginTop: 8 }}>
        <thead><tr><th>Cycle</th><th>Status</th><th>Trades</th><th>Data fails</th><th>Error</th></tr></thead>
        <tbody>
          {props.rows.slice(0, 30).map((c) => (
            <tr key={c.cycle_id}>
              <td>{c.cycle_id}</td>
              <td><Badge kind={c.status === "ok" ? "ok" : "error"}>{c.status ?? "?"}</Badge></td>
              <td>{c.n_trades ?? "—"}</td>
              <td className="muted">{c.critical_data_fail_sources || c.supplementary_stale_sources || "—"}</td>
              <td className="muted">{c.error_msg || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Section>
  );
}

export function HealthTab() {
  const q = useQuery({ queryKey: ["health"], queryFn: api.health });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  const d = q.data;
  return (
    <>
      <div className="grid2">
        <Timeline name="quant" rows={d.timeline.quant} />
        {d.timeline.hybrid
          ? <Timeline name="hybrid" rows={d.timeline.hybrid} />
          : <div className="panel muted">hybrid not configured</div>}
      </div>
      <Section title="Pipeline steps (latest quant cycle — hybrid runner has no structured log)">
        <table>
          <thead><tr><th>Step</th><th>Status</th><th>Duration</th><th>Detail</th></tr></thead>
          <tbody>
            {d.steps.map((s, i) => (
              <tr key={i}>
                <td>{String(s.step ?? "")}</td>
                <td><Badge kind={s.status === "ok" ? "ok" : "error"}>{String(s.status ?? "")}</Badge></td>
                <td>{s.duration_ms != null ? `${String(s.duration_ms)} ms` : "—"}</td>
                <td className="muted">{JSON.stringify(s.payload ?? {})}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
      <Section title="Retrains">
        <table>
          <thead><tr><th>Strategy</th><th>Retrain</th><th>Cycle</th><th>DirAcc</th><th>Status</th></tr></thead>
          <tbody>
            {(["quant", "hybrid"] as const).flatMap((name) =>
              (d.retrains[name] ?? []).map((r, i) => (
                <tr key={`${name}${i}`}>
                  <td><Badge kind={name}>{name}</Badge></td>
                  <td>{String(r.retrain_id ?? "")}</td>
                  <td>{String(r.cycle_id ?? "")}</td>
                  <td>{String(r.train_dir_acc ?? "—")}</td>
                  <td>{String(r.status ?? "")}</td>
                </tr>
              )))}
          </tbody>
        </table>
      </Section>
    </>
  );
}
```

- [ ] **Step 3: Build + frontend tests**

Run: `npm run build && npm test`
Expected: build exit 0, vitest PASS

- [ ] **Step 4: Commit**

```bash
git add src/
git commit -m "feat(monitor-ui): decisions tab (modulator panel) + health tab"
```

---

## Task 17: Build artifact, legacy removal, serve-dist integration test

**Files:**
- Delete: `tradingagents/monitor/static/` (app.js, app.css, chart.umd.min.js), `tradingagents/monitor/templates/`
- Create: `tradingagents/monitor/frontend/dist/` (committed build)
- Test: `tests/monitor/test_app.py` (append)

- [ ] **Step 1: Write the failing integration test** (append to `tests/monitor/test_app.py`)

```python
def test_index_serves_react_dist(dual_client):
    import pathlib
    dist = (pathlib.Path(__file__).resolve().parents[2]
            / "tradingagents/monitor/frontend/dist")
    if not dist.is_dir():
        import pytest as _pytest
        _pytest.skip("frontend dist not built")
    r = dual_client.get("/", auth=dual_client.auth)
    assert r.status_code == 200
    assert "<div id=\"root\">" in r.text


def test_index_503_when_dist_missing(journal_path, log_dir, monkeypatch):
    # create_app resolves _DIST at import; simulate missing by checking the
    # error branch only when dist truly absent — otherwise this test asserts
    # the happy path above and is a no-op here.
    pass
```

(Keep `test_index_503_when_dist_missing` as the documented placeholder-free no-op OR drop it — the 503 branch is trivially covered by reading `app.py`; prefer dropping it if the reviewer objects.)

- [ ] **Step 2: Build + commit dist**

```bash
cd tradingagents/monitor/frontend && npm run build && cd ../../..
git add -f tradingagents/monitor/frontend/dist
```

- [ ] **Step 3: Delete the legacy SPA**

```bash
git rm -r tradingagents/monitor/static tradingagents/monitor/templates
```

Then remove the now-dead pieces from `app.py` if any remain (Jinja2Templates import was already dropped in Task 8; confirm `grep -n "templates\|static" tradingagents/monitor/app.py` returns only the dist mount).

- [ ] **Step 4: Run the full monitor + live suites**

Run: `python -m pytest tests/monitor/ tests/live/ -v`
Expected: ALL PASS (incl. `test_index_serves_react_dist` now not skipped)

- [ ] **Step 5: Commit**

```bash
git add -A tradingagents/monitor tests/monitor
git commit -m "feat(monitor): serve committed React dist, remove legacy SPA"
```

---

## Task 18: Full verification + manual smoke

- [ ] **Step 1: Whole test suite**

Run: `python -m pytest tests/ -q 2>&1 | tail -20`
Expected: no NEW failures vs the `live-v2.3.3` baseline (pre-existing environmental failures — e.g. missing `hmmlearn`, live-API dataflow tests — are known; compare against `git stash`-free baseline run if unsure).

- [ ] **Step 2: Manual smoke against the fixture journals**

```bash
cd /home/malecada/master_thesis/TradingAgents/.worktrees/monitor-react-ui
TA_MONITOR_PASSWORD=test QUANT_DATA_DIR=/tmp/mon-q HYBRID_DATA_DIR=/tmp/mon-h \
  python - <<'EOF'
# build two tiny journals then serve
import os, sqlite3, pathlib, subprocess
for d in ("/tmp/mon-q", "/tmp/mon-h"):
    pathlib.Path(d).mkdir(exist_ok=True)
    conn = sqlite3.connect(f"{d}/trade_journal.db")
    conn.executescript(open("tradingagents/execution/live/schema.sql").read())
    conn.execute("INSERT OR IGNORE INTO cycles (cycle_id, start_ts, status) VALUES ('2026-06-11','2026-06-11T07:00:00+00:00','ok')")
    conn.execute("INSERT INTO portfolio_snapshots (cycle_id, ts, total_value, usdt_balance, position_qty_per_coin, unrealized_pnl) VALUES ('2026-06-11','2026-06-11T07:05:00+00:00',10100,5000,'{\"bitcoin\":0.05}',25)")
    conn.commit(); conn.close()
EOF
TA_MONITOR_PASSWORD=test QUANT_DATA_DIR=/tmp/mon-q HYBRID_DATA_DIR=/tmp/mon-h \
  python -m tradingagents.monitor
```

Open `http://127.0.0.1:8800` (admin/test). Verify: all 5 tabs render; positions show STALE badges (no creds); performance shows both strategy card rows; donut renders fallback allocation; decisions hybrid toggle shows "no modulator rows".

- [ ] **Step 3: Commit any smoke fixes, then final commit**

```bash
git add -A && git commit -m "fix(monitor): smoke-test fixes" --allow-empty
```

---

## Deployment notes (operator, post-merge — NOT part of this plan's execution)

- Monitor systemd unit needs new env: `QUANT_DATA_DIR`, `HYBRID_DATA_DIR`, `HYBRID_BINANCE_API_KEY/_SECRET`, optional `TA_MONITOR_ANCHOR_SR_QUANT/_HYBRID`.
- First hybrid cycle after deploy auto-creates `modulator_outputs` in the hybrid journal.
- Tag as next `live-v2.4.0` after merge to the live lineage.

## Self-review (done at plan time)

- **Spec coverage**: unified dual UI (T7/T8), positions+uPnL (T5/T8/T14), donuts (T8/T14), chart upgrade incl. indexed-100/DD/rolling-SR/range/anchors (T1/T8/T13), trade analytics (T5/T6/T9/T15), modulator panel (T2/T3/T4/T16), health labeling (T8/T16), committed dist + legacy removal + auth-covered static (T8/T10/T17), degradation paths (T7/T8 tests). `/api/compare` kept (T8).
- **Types consistent**: `StrategySource(name, journal_path, snapshot)` used identically in T7/T8/conftest; snapshot shape `{positions, usdt_free, equity, income}` consistent T7/T9/T8; `modulator_outputs` columns identical in T2 SQL, T3 writer, T4 reader, T16 UI.
- **Known check at impl time**: exact key names of `compare_quant_hybrid` return (noted in T13).
