# Monitor Predlab-First Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the live monitor into a predlab-first dashboard: new JSONL-backed `/api/predlab/*` endpoints + four new tabs (Performance / Book / Gate / Ops), old V5 quant/hybrid tabs collapsed into a read-only Legacy section, Run Prediction tab removed.

**Architecture:** Extend the existing FastAPI monitor (`tradingagents/monitor/`) with a new pure-function module `predlab.py` (JSONL journal parsing + derived metrics) and a `PredlabSource` wired through `create_app(...)`. Frontend stays React 19 + TanStack Query + lightweight-charts; new tabs follow the existing tab pattern; existing V5 tabs are reused unchanged inside a Legacy wrapper.

**Tech Stack:** Python 3.9+ (`from __future__ import annotations`), FastAPI, pytest + TestClient; TypeScript, React 19, TanStack Query v5, lightweight-charts v5, Vite 8, vitest.

**Spec:** `docs/superpowers/specs/2026-08-06-monitor-predlab-overhaul-design.md`

## Global Constraints

- All new endpoints are read-only and sit behind the existing basic-auth middleware (no auth code changes).
- Degradation contract: missing/absent file → `null` block in a 200 response; malformed JSONL lines are skipped and counted, never fatal.
- Journal semantics: rows have NO equity/position fields; equity is compounded from `realized_book_ret` (null rows skipped). Warm-up = count of non-null `realized_book_ret`; vt scale needs ≥ 21.
- Books: `champion` → `journal_champion.jsonl`, scale key `vt15_b100_scale`; `vt10` → `journal.jsonl`, scale key `vt10_scale`. Champion is the primary book everywhere in the UI.
- Annualization √365 (reuse `tradingagents/monitor/metrics.py`); rolling Sharpe window 30.
- Staleness threshold 36 h from `written_utc`. Known gap dates 2026-07-31 … 2026-08-02 (scheduler off — intentional, both books).
- Sealed one-shot constants: forward window start 2026-07-02, earliest evaluation 2027-01-02, threshold SR = 0.5 × dev ovl SR (0.946 fallback). Gate tab is informational only — never present it as an evaluation.
- Backend adhoc module (`tradingagents/monitor/adhoc/`) stays untouched. Only frontend Run-tab code is deleted.
- `frontend/dist/` is committed (VPS has no Node) — rebuild before the final commit.
- Python code style: `from __future__ import annotations`, Google-style docstrings, pure functions separated from I/O (mirror `metrics.py` vs `sources.py` split).
- Commit messages end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

## Working branch

All tasks run on branch `feature/monitor-predlab` in `/home/malecada/master_thesis/TradingAgents`, created in Task 0. Tests run with `uv sync --all-extras` python or the project venv: `python -m pytest tests/monitor/ -q`.

---

### Task 0: Branch setup

**Files:** none (git only)

**Interfaces:**
- Produces: branch `feature/monitor-predlab` containing the spec commit; all later tasks commit here.

- [ ] **Step 1: Create branch off main and bring the spec commit over**

```bash
cd /home/malecada/master_thesis/TradingAgents
git stash --include-untracked   # only if working tree dirty; else skip
git checkout main
git checkout -b feature/monitor-predlab
git cherry-pick b17f56e   # docs: design spec for predlab-first monitor UI overhaul (on feature/value-unlock-xs)
```

- [ ] **Step 2: Verify baseline monitor tests are green**

Run: `python -m pytest tests/monitor/ -q`
Expected: all pass (baseline before any change).

---

### Task 1: `predlab.py` — journal parsing + derived metrics (pure functions)

**Files:**
- Create: `tradingagents/monitor/predlab.py`
- Test: `tests/monitor/test_predlab.py`

**Interfaces:**
- Consumes: `tradingagents.monitor.metrics` (`sharpe(values: list[float]) -> float`, `max_drawdown(values) -> float`, `drawdown_series(equity: list[dict]) -> list[dict]`, `rolling_sharpe(equity, window=30) -> list[dict]`).
- Produces (used by Tasks 2–3):
  - `BOOKS: dict[str, tuple[str, str]]` — book key → (journal filename, scale key). Keys: `"champion"`, `"vt10"`.
  - `KNOWN_GAPS: set[str]`, `WARMUP_RETURNS: int = 21`, `STALE_AFTER_HOURS: float = 36.0`, `FORWARD_START: date`, `EARLIEST_EVAL: date`, `FALLBACK_THRESHOLD_SR: float = 0.946`
  - `parse_journal(path: Path) -> tuple[list[dict], int]` — (rows sorted by asof, malformed line count); `([], 0)` when file missing.
  - `derive_book(rows: list[dict], scale_key: str) -> dict | None` — performance block or None when rows empty.
  - `book_detail(rows: list[dict], scale_key: str) -> dict | None` — latest-row book payload with longs/shorts/delta.
  - `book_health(rows: list[dict], malformed: int, now_utc: datetime) -> dict | None` — freshness/gaps payload.
  - `gate_status(champion_rows: list[dict], reference: dict | None, today_utc: date) -> dict` — gate-tracker payload.

- [ ] **Step 1: Write the failing tests**

Create `tests/monitor/test_predlab.py`:

```python
"""Unit tests for the predlab pure-function layer (no HTTP, no env)."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from tradingagents.monitor import predlab


def _row(asof, ret, scale=None, **over):
    row = {
        "asof": asof, "written_utc": f"{asof}T00:20:00+00:00",
        "n_universe": 523, "membership_hash": "4807428b5dab",
        "weights": {"BTCUSDT": 0.025, "ETHUSDT": 0.025,
                    "AKEUSDT": -0.025, "BANKUSDT": -0.025},
        "realized_book_ret": ret, "est_turnover": 0.10, "est_cost": 0.00005,
        "vt15_b100_scale": scale, "breadth": 200,
    }
    row.update(over)
    return row


def _write_journal(tmp_path, rows):
    p = tmp_path / "journal_champion.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


class TestParseJournal:
    def test_missing_file_returns_empty(self, tmp_path):
        rows, bad = predlab.parse_journal(tmp_path / "nope.jsonl")
        assert rows == [] and bad == 0

    def test_rows_sorted_and_malformed_counted(self, tmp_path):
        p = tmp_path / "j.jsonl"
        p.write_text(
            json.dumps(_row("2026-08-04", 0.01)) + "\n"
            + "{not json\n"
            + json.dumps(_row("2026-08-03", None)) + "\n")
        rows, bad = predlab.parse_journal(p)
        assert [r["asof"] for r in rows] == ["2026-08-03", "2026-08-04"]
        assert bad == 1


class TestDeriveBook:
    def test_empty_rows_none(self):
        assert predlab.derive_book([], "vt15_b100_scale") is None

    def test_equity_compounds_skipping_null_returns(self):
        rows = [_row("2026-08-03", None), _row("2026-08-04", 0.10),
                _row("2026-08-05", None), _row("2026-08-06", -0.05)]
        d = predlab.derive_book(rows, "vt15_b100_scale")
        # anchor at first row, then one point per non-null return
        assert [p["ts"] for p in d["equity"]] == [
            "2026-08-03", "2026-08-04", "2026-08-06"]
        assert d["equity"][0]["value"] == 100.0
        assert d["equity"][1]["value"] == pytest.approx(110.0)
        assert d["equity"][2]["value"] == pytest.approx(104.5)
        assert d["cards"]["cum_return"] == pytest.approx(0.045)
        assert d["cards"]["warmup"] == {"n": 2, "required": 21}
        assert d["cards"]["n_days"] == 4
        assert d["cards"]["last_asof"] == "2026-08-06"

    def test_scale_and_cost_cards(self):
        rows = [_row("2026-08-03", None, scale=None),
                _row("2026-08-04", 0.01, scale=0.5)]
        d = predlab.derive_book(rows, "vt15_b100_scale")
        assert d["cards"]["scale"] == 0.5
        assert d["cards"]["cum_cost"] == pytest.approx(0.0001)
        assert d["cards"]["avg_turnover"] == pytest.approx(0.10)

    def test_drawdown_and_rolling_sharpe_shapes(self):
        rows = [_row("2026-08-03", None)] + [
            _row(f"2026-09-{i:02d}", 0.001 * (1 if i % 2 else -1))
            for i in range(1, 29)]
        d = predlab.derive_book(rows, "vt15_b100_scale")
        assert len(d["drawdown"]) == len(d["equity"])
        assert isinstance(d["rolling_sharpe"], list)  # may be empty < window


class TestBookDetail:
    def test_latest_row_split_and_delta(self):
        prev = _row("2026-08-03", None,
                    weights={"BTCUSDT": 0.025, "AKEUSDT": -0.025})
        cur = _row("2026-08-04", 0.01,
                   weights={"ETHUSDT": 0.025, "AKEUSDT": -0.025}, scale=0.4)
        d = predlab.book_detail([prev, cur], "vt15_b100_scale")
        assert d["asof"] == "2026-08-04"
        assert d["longs"] == [{"symbol": "ETHUSDT", "weight": 0.025}]
        assert d["shorts"] == [{"symbol": "AKEUSDT", "weight": -0.025}]
        assert d["delta"] == {"entered": 1, "exited": 1}
        assert d["scale"] == 0.4
        assert d["breadth"] == 200

    def test_single_row_has_null_delta(self):
        d = predlab.book_detail([_row("2026-08-03", None)], "vt15_b100_scale")
        assert d["delta"] is None

    def test_empty_none(self):
        assert predlab.book_detail([], "vt15_b100_scale") is None


class TestBookHealth:
    NOW = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    def test_fresh(self):
        rows = [_row("2026-08-04", 0.01)]
        h = predlab.book_health(rows, 0, self.NOW)
        assert h["stale"] is False and h["rows"] == 1 and h["malformed"] == 0

    def test_stale_after_36h(self):
        rows = [_row("2026-08-01", 0.01)]
        h = predlab.book_health(rows, 2, self.NOW)
        assert h["stale"] is True and h["malformed"] == 2

    def test_gaps_flag_known(self):
        rows = [_row("2026-07-30", None), _row("2026-08-03", 0.01)]
        h = predlab.book_health(rows, 0, self.NOW)
        gaps = {g["date"]: g["known"] for g in h["gaps"]}
        assert gaps == {"2026-07-31": True, "2026-08-01": True,
                        "2026-08-02": True}

    def test_empty_none(self):
        assert predlab.book_health([], 0, self.NOW) is None


class TestGateStatus:
    def test_with_reference(self):
        rows = [_row("2026-08-03", None), _row("2026-08-04", 0.01)]
        ref = {"dev_metrics": {"ovl_sr_full": 1.892}}
        g = predlab.gate_status(rows, ref, date(2026, 8, 6))
        assert g["window_start"] == "2026-07-02"
        assert g["earliest_eval"] == "2027-01-02"
        assert g["days_elapsed"] == 35
        assert g["days_remaining"] == 149
        assert g["threshold_sr"] == pytest.approx(0.946)
        assert g["informational"] is True
        assert g["running"]["n_returns"] == 1

    def test_without_reference_uses_fallback_threshold(self):
        g = predlab.gate_status([], None, date(2026, 8, 6))
        assert g["threshold_sr"] == pytest.approx(0.946)
        assert g["running"]["sr"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/monitor/test_predlab.py -q`
Expected: FAIL — `ModuleNotFoundError` / `AttributeError` (predlab module absent).

- [ ] **Step 3: Implement `tradingagents/monitor/predlab.py`**

```python
"""Predlab paper-book journal parsing and derived metrics.

The S1 paper trader writes JSONL weights-and-returns journals (no equity
or position fields). This module is pure: functions take parsed rows and
return plain dicts for the API layer. Filesystem access is limited to
``parse_journal`` / ``load_reference``; both degrade to empty results on
missing files. See docs/superpowers/specs/2026-08-06-monitor-predlab-
overhaul-design.md.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from tradingagents.monitor import metrics

# book key -> (journal filename, scale key). Champion is the frozen
# Phase-O system; vt10 is the old S1 book kept for the pp2 confirmation.
BOOKS: dict[str, tuple[str, str]] = {
    "champion": ("journal_champion.jsonl", "vt15_b100_scale"),
    "vt10": ("journal.jsonl", "vt10_scale"),
}
WARMUP_RETURNS = 21          # paper trader needs >= 21 realized returns
STALE_AFTER_HOURS = 36.0
_ROLLING_WINDOW = 30
# VPS scheduler was off on these dates — documented, not an incident.
KNOWN_GAPS = {"2026-07-31", "2026-08-01", "2026-08-02"}
# Sealed one-shot (gates.json predlab_opt.forward_one_shot). The gate
# display is informational only; the evaluation itself stays sealed.
FORWARD_START = date(2026, 7, 2)
EARLIEST_EVAL = date(2027, 1, 2)
FALLBACK_THRESHOLD_SR = 0.946   # 0.5 x dev ovl SR 1.892


def parse_journal(path: Path) -> tuple[list[dict], int]:
    """(rows sorted by asof, malformed-line count); ([], 0) if missing."""
    if not path.is_file():
        return [], 0
    rows: list[dict] = []
    malformed = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if isinstance(row, dict) and "asof" in row:
            rows.append(row)
        else:
            malformed += 1
    rows.sort(key=lambda r: r["asof"])
    return rows, malformed


def _realized(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("realized_book_ret") is not None]


def derive_book(rows: list[dict], scale_key: str) -> dict | None:
    """Performance block for one book, or None when the journal is empty."""
    if not rows:
        return None
    equity = [{"ts": rows[0]["asof"], "value": 100.0}]
    for r in rows[1:]:
        ret = r.get("realized_book_ret")
        if ret is None:
            continue
        equity.append({"ts": r["asof"],
                       "value": equity[-1]["value"] * (1.0 + ret)})
    values = [p["value"] for p in equity]
    scales = [r.get(scale_key) for r in rows if r.get(scale_key) is not None]
    turnovers = [r["est_turnover"] for r in rows
                 if r.get("est_turnover") is not None]
    costs = [r["est_cost"] for r in rows if r.get("est_cost") is not None]
    return {
        "equity": equity,
        "drawdown": metrics.drawdown_series(equity),
        "rolling_sharpe": metrics.rolling_sharpe(equity, _ROLLING_WINDOW),
        "cards": {
            "cum_return": values[-1] / 100.0 - 1.0,
            "sharpe": round(metrics.sharpe(values), 2),
            "max_drawdown": round(metrics.max_drawdown(values), 4),
            "scale": scales[-1] if scales else None,
            "warmup": {"n": len(_realized(rows)), "required": WARMUP_RETURNS},
            "avg_turnover": (sum(turnovers) / len(turnovers)
                             if turnovers else None),
            "cum_cost": sum(costs) if costs else None,
            "last_asof": rows[-1]["asof"],
            "n_days": len(rows),
        },
    }


def book_detail(rows: list[dict], scale_key: str) -> dict | None:
    """Latest-row book composition, or None when the journal is empty."""
    if not rows:
        return None
    cur = rows[-1]
    weights: dict = cur.get("weights") or {}
    longs = sorted(
        ({"symbol": s, "weight": w} for s, w in weights.items() if w > 0),
        key=lambda x: x["symbol"])
    shorts = sorted(
        ({"symbol": s, "weight": w} for s, w in weights.items() if w < 0),
        key=lambda x: x["symbol"])
    delta = None
    if len(rows) >= 2:
        prev = set((rows[-2].get("weights") or {}))
        now = set(weights)
        delta = {"entered": len(now - prev), "exited": len(prev - now)}
    return {
        "asof": cur["asof"],
        "n_universe": cur.get("n_universe"),
        "breadth": cur.get("breadth"),
        "membership_hash": cur.get("membership_hash"),
        "scale": cur.get(scale_key),
        "est_turnover": cur.get("est_turnover"),
        "est_cost": cur.get("est_cost"),
        "longs": longs, "shorts": shorts, "delta": delta,
    }


def book_health(rows: list[dict], malformed: int,
                now_utc: datetime) -> dict | None:
    """Freshness + gap payload for one book; None when journal empty."""
    if not rows:
        return None
    last = rows[-1]
    stale = True
    written = last.get("written_utc")
    if written:
        try:
            # fromisoformat rejects a trailing "Z" before Python 3.11
            ts = datetime.fromisoformat(written.replace("Z", "+00:00"))
            age_h = (now_utc - ts).total_seconds() / 3600.0
            stale = age_h > STALE_AFTER_HOURS
        except ValueError:
            pass
    have = {r["asof"] for r in rows}
    first = date.fromisoformat(rows[0]["asof"])
    lastd = date.fromisoformat(rows[-1]["asof"])
    gaps = []
    d = first
    while d <= lastd:
        iso = d.isoformat()
        if iso not in have:
            gaps.append({"date": iso, "known": iso in KNOWN_GAPS})
        d += timedelta(days=1)
    return {
        "last_asof": last["asof"], "written_utc": written,
        "stale": stale, "rows": len(rows), "malformed": malformed,
        "gaps": gaps,
    }


def gate_status(champion_rows: list[dict], reference: dict | None,
                today_utc: date) -> dict:
    """Sealed one-shot tracker payload. Informational only — the forward
    evaluation is one-shot (earliest 2027-01-02) and stays sealed."""
    threshold = FALLBACK_THRESHOLD_SR
    if reference:
        sr_full = (reference.get("dev_metrics") or {}).get("ovl_sr_full")
        if sr_full is not None:
            threshold = round(0.5 * sr_full, 3)
    perf = derive_book(champion_rows, BOOKS["champion"][1])
    running_sr = None
    n_ret = len(_realized(champion_rows))
    if perf and n_ret >= 2:
        running_sr = perf["cards"]["sharpe"]
    return {
        "window_start": FORWARD_START.isoformat(),
        "earliest_eval": EARLIEST_EVAL.isoformat(),
        "days_elapsed": (today_utc - FORWARD_START).days,
        "days_remaining": max(0, (EARLIEST_EVAL - today_utc).days),
        "threshold_sr": threshold,
        "criteria": [
            "net overlaid SR_F >= 0.946 (0.5 x dev 1.892)",
            "same sign as dev",
            "time-shift placebo p < 0.10 on forward window",
            "ONE evaluation, earliest 2027-01-02",
        ],
        "running": {
            "sr": running_sr, "n_returns": n_ret,
            "note": "paper-journal proxy; official evaluation uses the "
                    "backtest harness on the sealed window",
        },
        "informational": True,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/monitor/test_predlab.py -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/predlab.py tests/monitor/test_predlab.py
git commit -m "feat(monitor): predlab journal parsing + derived metrics

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: `PredlabSource` + reference loading + payload assembly

**Files:**
- Modify: `tradingagents/monitor/predlab.py` (append)
- Test: `tests/monitor/test_predlab_source.py`

**Interfaces:**
- Consumes: Task 1 functions; `tradingagents.monitor.sources.ttl_cached(fn, ttl) -> Callable[[], dict]`.
- Produces (used by Task 3):
  - `class PredlabSource` with `__init__(self, data_dir: str, ttl: float = 30.0)` and method `payload(self) -> dict` (TTL-cached full payload).
  - `resolve_predlab_source() -> PredlabSource | None` — from env `PREDLAB_DATA_DIR`, None when unset.
  - Payload shape (exact — frontend types in Task 4 mirror this):

```
{
  "performance": {
    "books": {"champion": <derive_book|null>, "vt10": <derive_book|null>},
    "reference": <gates.json predlab_opt.final_champion dev_metrics dict | null>,
    "backtest_yearly": {"champion": {year: {sr, ret, maxdd, n_days}}|null,
                         "vt10": {...}|null} | null
  },
  "books": {"champion": <book_detail|null>, "vt10": <book_detail|null>},
  "gate": <gate_status dict>,
  "health": {"books": {"champion": <book_health|null>, "vt10": <book_health|null>},
              "heartbeat_note": "journal backup branch predlab-journal-backup pushes daily ~00:45 UTC"}
}
```

- [ ] **Step 1: Write the failing tests**

Create `tests/monitor/test_predlab_source.py`:

```python
"""PredlabSource: filesystem layout, reference files, degradation."""
from __future__ import annotations

import json
from pathlib import Path

from tradingagents.monitor.predlab import PredlabSource, resolve_predlab_source


def _mk_data(tmp_path: Path, champion_rows=None, vt10_rows=None,
             gates=None, backtest=None) -> Path:
    s1 = tmp_path / "predlab" / "s1_paper"
    s1.mkdir(parents=True)
    if champion_rows is not None:
        (s1 / "journal_champion.jsonl").write_text(
            "\n".join(json.dumps(r) for r in champion_rows) + "\n")
    if vt10_rows is not None:
        (s1 / "journal.jsonl").write_text(
            "\n".join(json.dumps(r) for r in vt10_rows) + "\n")
    if gates is not None:
        (tmp_path / "predlab" / "gates.json").write_text(json.dumps(gates))
    if backtest is not None:
        (tmp_path / "predlab" / "champion_backtest.json").write_text(
            json.dumps(backtest))
    return tmp_path


def _row(asof, ret):
    return {"asof": asof, "written_utc": f"{asof}T00:20:00+00:00",
            "n_universe": 500, "membership_hash": "abc",
            "weights": {"BTCUSDT": 0.025, "AKEUSDT": -0.025},
            "realized_book_ret": ret, "est_turnover": 0.1,
            "est_cost": 0.00005, "vt15_b100_scale": None,
            "vt10_scale": None, "breadth": 200}


GATES = {"predlab_opt": {"final_champion": {
    "dev_metrics": {"ovl_sr_full": 1.892, "ovl_maxdd": 0.176,
                    "raw_sr_full": 1.928,
                    "dsr_selection_pool": 0.913}}}}
BACKTEST = {"systems": {
    "new": {"yearly_ovl": {"2025": {"sr": 2.0, "ret": 0.24,
                                    "maxdd": 0.058, "n_days": 365}}},
    "old": {"yearly_ovl": {"2025": {"sr": 2.0, "ret": 0.24,
                                    "maxdd": 0.058, "n_days": 365}}}}}


def test_full_payload(tmp_path):
    root = _mk_data(tmp_path,
                    champion_rows=[_row("2026-08-03", None),
                                   _row("2026-08-04", 0.01)],
                    vt10_rows=[_row("2026-08-04", 0.02)],
                    gates=GATES, backtest=BACKTEST)
    p = PredlabSource(str(root)).payload()
    assert p["performance"]["books"]["champion"]["cards"]["n_days"] == 2
    assert p["performance"]["books"]["vt10"]["cards"]["n_days"] == 1
    assert p["performance"]["reference"]["ovl_sr_full"] == 1.892
    assert "2025" in p["performance"]["backtest_yearly"]["champion"]
    assert p["books"]["champion"]["asof"] == "2026-08-04"
    assert p["gate"]["threshold_sr"] == 0.946
    assert p["health"]["books"]["champion"]["rows"] == 2
    assert "predlab-journal-backup" in p["health"]["heartbeat_note"]


def test_missing_everything_degrades_to_nulls(tmp_path):
    p = PredlabSource(str(tmp_path)).payload()
    assert p["performance"]["books"] == {"champion": None, "vt10": None}
    assert p["performance"]["reference"] is None
    assert p["performance"]["backtest_yearly"] is None
    assert p["books"] == {"champion": None, "vt10": None}
    assert p["health"]["books"] == {"champion": None, "vt10": None}
    assert p["gate"]["threshold_sr"] == 0.946  # fallback


def test_payload_is_ttl_cached(tmp_path):
    root = _mk_data(tmp_path, champion_rows=[_row("2026-08-04", 0.01)])
    src = PredlabSource(str(root))
    first = src.payload()
    # rewrite journal; cached payload must not change within TTL
    (root / "predlab" / "s1_paper" / "journal_champion.jsonl").write_text(
        json.dumps(_row("2026-08-05", 0.5)) + "\n")
    assert src.payload() == first


def test_resolve_from_env(tmp_path, monkeypatch):
    monkeypatch.delenv("PREDLAB_DATA_DIR", raising=False)
    assert resolve_predlab_source() is None
    monkeypatch.setenv("PREDLAB_DATA_DIR", str(tmp_path))
    src = resolve_predlab_source()
    assert src is not None and src.data_dir == str(tmp_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/monitor/test_predlab_source.py -q`
Expected: FAIL — `ImportError: cannot import name 'PredlabSource'`.

- [ ] **Step 3: Append the source class to `tradingagents/monitor/predlab.py`**

Add imports `os`, `timezone` (extend the existing `datetime` import) and `from tradingagents.monitor.sources import ttl_cached`, then:

```python
HEARTBEAT_NOTE = ("journal backup branch predlab-journal-backup pushes "
                  "daily ~00:45 UTC")


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


class PredlabSource:
    """Read-only predlab data bundle rooted at PREDLAB_DATA_DIR.

    ``payload()`` assembles everything the /api/predlab endpoints serve,
    TTL-cached (30 s) so hammering the UI doesn't re-read files. Files are
    small JSONL/JSON; missing files degrade to None blocks.
    """

    def __init__(self, data_dir: str, ttl: float = 30.0) -> None:
        self.data_dir = data_dir
        self._cached = ttl_cached(self._build, ttl)

    def payload(self) -> dict:
        return self._cached()

    def _build(self) -> dict:
        root = Path(self.data_dir) / "predlab"
        parsed = {}
        for book, (fname, scale_key) in BOOKS.items():
            rows, malformed = parse_journal(root / "s1_paper" / fname)
            parsed[book] = (rows, malformed, scale_key)
        gates = _load_json(root / "gates.json") or {}
        reference = (gates.get("predlab_opt") or {}).get("final_champion")
        backtest = _load_json(root / "champion_backtest.json")
        backtest_yearly = None
        if backtest:
            systems = backtest.get("systems") or {}
            backtest_yearly = {
                "champion": (systems.get("new") or {}).get("yearly_ovl"),
                "vt10": (systems.get("old") or {}).get("yearly_ovl"),
            }
        now = datetime.now(timezone.utc)
        return {
            "performance": {
                "books": {b: derive_book(rows, sk)
                          for b, (rows, _m, sk) in parsed.items()},
                "reference": (reference or {}).get("dev_metrics")
                             if reference else None,
                "backtest_yearly": backtest_yearly,
            },
            "books": {b: book_detail(rows, sk)
                      for b, (rows, _m, sk) in parsed.items()},
            "gate": gate_status(parsed["champion"][0], reference, now.date()),
            "health": {
                "books": {b: book_health(rows, m, now)
                          for b, (rows, m, _sk) in parsed.items()},
                "heartbeat_note": HEARTBEAT_NOTE,
            },
        }


def resolve_predlab_source() -> PredlabSource | None:
    """PredlabSource from PREDLAB_DATA_DIR, or None when unset."""
    data_dir = os.environ.get("PREDLAB_DATA_DIR")
    return PredlabSource(data_dir) if data_dir else None
```

Note: `gate_status`'s `reference` parameter receives the whole `final_champion` block (it looks up `dev_metrics` itself) — pass `reference`, not `reference["dev_metrics"]`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/monitor/test_predlab_source.py tests/monitor/test_predlab.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/predlab.py tests/monitor/test_predlab_source.py
git commit -m "feat(monitor): PredlabSource with TTL-cached payload assembly

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: `/api/predlab/*` endpoints + entrypoint wiring

**Files:**
- Modify: `tradingagents/monitor/app.py` (signature + 4 routes)
- Modify: `tradingagents/monitor/__main__.py`
- Test: `tests/monitor/test_predlab_api.py`

**Interfaces:**
- Consumes: `PredlabSource`, `resolve_predlab_source` (Task 2); existing `create_app` and `_sanitize_floats` in `app.py`.
- Produces: `create_app(*, quant, hybrid=None, log_dir="logs", start_capital=10000.0, predlab: PredlabSource | None = None)`; routes `GET /api/predlab/performance`, `GET /api/predlab/book?book=champion|vt10`, `GET /api/predlab/gate`, `GET /api/predlab/health`.
  - `/book` response: `{"book": <name>, "detail": <book_detail|null>}`; unknown book name → HTTP 400.
  - When `predlab is None`: performance → `{"books": {"champion": null, "vt10": null}, "reference": null, "backtest_yearly": null}`, book → `{"book": ..., "detail": null}`, gate → `gate_status([], None, today)` (static tracker still renders), health → `{"books": {"champion": null, "vt10": null}, "heartbeat_note": ...}`.

- [ ] **Step 1: Write the failing tests**

First read `tests/monitor/conftest.py` and `tests/monitor/test_app.py` to reuse the existing app/client fixture pattern (TA_MONITOR_PASSWORD env + auth header helper). Then create `tests/monitor/test_predlab_api.py` following that pattern:

```python
"""HTTP contract for /api/predlab/* (auth, shapes, degradation)."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from tradingagents.monitor.app import create_app
from tradingagents.monitor.predlab import PredlabSource
from tradingagents.monitor.sources import StrategySource

# NOTE: adapt auth/env boilerplate to the existing conftest fixtures —
# reuse them if they already provide an authed client factory.
AUTH = ("admin", "testpw")


def _quant_source(tmp_path):
    return StrategySource(
        name="quant", journal_path=str(tmp_path / "missing.db"),
        snapshot=lambda: (_ for _ in ()).throw(RuntimeError("no exchange")))


def _client(tmp_path, monkeypatch, predlab):
    monkeypatch.setenv("TA_MONITOR_PASSWORD", "testpw")
    app = create_app(quant=_quant_source(tmp_path), hybrid=None,
                     log_dir=str(tmp_path), predlab=predlab)
    return TestClient(app)


def _mk_predlab(tmp_path):
    s1 = tmp_path / "pl" / "predlab" / "s1_paper"
    s1.mkdir(parents=True)
    row = {"asof": "2026-08-04", "written_utc": "2026-08-04T00:20:00+00:00",
           "n_universe": 500, "membership_hash": "abc",
           "weights": {"BTCUSDT": 0.025, "AKEUSDT": -0.025},
           "realized_book_ret": None, "est_turnover": 0.1,
           "est_cost": 0.00005, "vt15_b100_scale": None, "breadth": 200}
    (s1 / "journal_champion.jsonl").write_text(json.dumps(row) + "\n")
    return PredlabSource(str(tmp_path / "pl"))


def test_endpoints_require_auth(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, _mk_predlab(tmp_path))
    assert c.get("/api/predlab/performance").status_code == 401


def test_performance_shape(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, _mk_predlab(tmp_path))
    r = c.get("/api/predlab/performance", auth=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["books"]["champion"]["cards"]["n_days"] == 1
    assert body["books"]["vt10"] is None
    assert body["reference"] is None


def test_book_endpoint_and_unknown_book(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, _mk_predlab(tmp_path))
    r = c.get("/api/predlab/book?book=champion", auth=AUTH)
    assert r.json()["detail"]["asof"] == "2026-08-04"
    assert c.get("/api/predlab/book?book=nope", auth=AUTH).status_code == 400


def test_gate_and_health(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, _mk_predlab(tmp_path))
    g = c.get("/api/predlab/gate", auth=AUTH).json()
    assert g["informational"] is True
    h = c.get("/api/predlab/health", auth=AUTH).json()
    assert h["books"]["champion"]["rows"] == 1


def test_no_predlab_source_degrades(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, None)
    r = c.get("/api/predlab/performance", auth=AUTH)
    assert r.status_code == 200
    assert r.json()["books"] == {"champion": None, "vt10": None}
    g = c.get("/api/predlab/gate", auth=AUTH)
    assert g.status_code == 200 and g.json()["informational"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/monitor/test_predlab_api.py -q`
Expected: FAIL — `create_app() got an unexpected keyword argument 'predlab'`.

- [ ] **Step 3: Wire endpoints in `app.py` and env in `__main__.py`**

`app.py`: extend the signature (`predlab: "PredlabSource | None" = None` — import `from tradingagents.monitor.predlab import PredlabSource, BOOKS, gate_status` at the top with the other monitor imports) and add after the `/api/compare` route:

```python
    # ── predlab paper-book endpoints (JSONL journals, read-only) ───────────
    def _predlab_payload() -> dict | None:
        return predlab.payload() if predlab is not None else None

    @app.get("/api/predlab/performance")
    def api_predlab_performance():
        p = _predlab_payload()
        if p is None:
            return {"books": {b: None for b in BOOKS},
                    "reference": None, "backtest_yearly": None}
        return _sanitize_floats(p["performance"])

    @app.get("/api/predlab/book")
    def api_predlab_book(book: str = "champion"):
        if book not in BOOKS:
            raise HTTPException(status_code=400,
                                detail=f"unknown book {book!r}")
        p = _predlab_payload()
        detail = p["books"][book] if p is not None else None
        return _sanitize_floats({"book": book, "detail": detail})

    @app.get("/api/predlab/gate")
    def api_predlab_gate():
        p = _predlab_payload()
        if p is None:
            from datetime import datetime, timezone
            return gate_status([], None, datetime.now(timezone.utc).date())
        return _sanitize_floats(p["gate"])

    @app.get("/api/predlab/health")
    def api_predlab_health():
        p = _predlab_payload()
        if p is None:
            from tradingagents.monitor.predlab import HEARTBEAT_NOTE
            return {"books": {b: None for b in BOOKS},
                    "heartbeat_note": HEARTBEAT_NOTE}
        return _sanitize_floats(p["health"])
```

(Move the two local imports to module top instead — shown inline here only for placement clarity. Also update the module docstring's endpoint list.)

`__main__.py`: import `resolve_predlab_source` and pass it:

```python
from tradingagents.monitor.predlab import resolve_predlab_source
...
    app = create_app(
        quant=quant,
        hybrid=hybrid,
        log_dir=os.environ.get("LOG_DIR", "logs"),
        start_capital=float(os.environ.get("TA_MONITOR_START_CAPITAL", "10000")),
        predlab=resolve_predlab_source(),
    )
```

Update the `__main__.py` docstring env list to include `PREDLAB_DATA_DIR`.

- [ ] **Step 4: Run the full monitor suite**

Run: `python -m pytest tests/monitor/ -q`
Expected: PASS — new tests green, zero regressions.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/monitor/app.py tradingagents/monitor/__main__.py tests/monitor/test_predlab_api.py
git commit -m "feat(monitor): /api/predlab endpoints + PREDLAB_DATA_DIR wiring

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Frontend types + API client

**Files:**
- Modify: `tradingagents/monitor/frontend/src/types.ts` (append)
- Modify: `tradingagents/monitor/frontend/src/api.ts`

**Interfaces:**
- Consumes: Task 3 endpoint shapes.
- Produces (used by Tasks 6–9): types `PredlabBookName`, `PredlabCards`, `PredlabBookPerf`, `PredlabPerformanceResp`, `PredlabBookResp`, `PredlabGateResp`, `PredlabHealthResp`; api methods `api.predlabPerformance()`, `api.predlabBook(b)`, `api.predlabGate()`, `api.predlabHealth()`.

- [ ] **Step 1: Append predlab types to `types.ts`**

```typescript
// ── predlab paper-book (JSONL journals) ─────────────────────────────────

export type PredlabBookName = "champion" | "vt10";

export interface PredlabCards {
  cum_return: number; sharpe: number; max_drawdown: number;
  scale: number | null;
  warmup: { n: number; required: number };
  avg_turnover: number | null; cum_cost: number | null;
  last_asof: string; n_days: number;
}

export interface PredlabBookPerf {
  equity: Point[]; drawdown: Point[]; rolling_sharpe: Point[];
  cards: PredlabCards;
}

export interface PredlabYearlyRow {
  sr: number; ret: number; maxdd: number; n_days: number;
}

export interface PredlabPerformanceResp {
  books: Record<PredlabBookName, PredlabBookPerf | null>;
  reference: {
    ovl_sr_full: number; ovl_maxdd: number;
    raw_sr_full?: number; dsr_selection_pool?: number;
  } | null;
  backtest_yearly:
    Record<PredlabBookName, Record<string, PredlabYearlyRow> | null> | null;
}

export interface PredlabWeight { symbol: string; weight: number }

export interface PredlabBookDetail {
  asof: string; n_universe: number | null; breadth: number | null;
  membership_hash: string | null; scale: number | null;
  est_turnover: number | null; est_cost: number | null;
  longs: PredlabWeight[]; shorts: PredlabWeight[];
  delta: { entered: number; exited: number } | null;
}

export interface PredlabBookResp {
  book: PredlabBookName; detail: PredlabBookDetail | null;
}

export interface PredlabGateResp {
  window_start: string; earliest_eval: string;
  days_elapsed: number; days_remaining: number;
  threshold_sr: number; criteria: string[];
  running: { sr: number | null; n_returns: number; note: string };
  informational: true;
}

export interface PredlabBookHealth {
  last_asof: string; written_utc: string | null; stale: boolean;
  rows: number; malformed: number;
  gaps: { date: string; known: boolean }[];
}

export interface PredlabHealthResp {
  books: Record<PredlabBookName, PredlabBookHealth | null>;
  heartbeat_note: string;
}
```

- [ ] **Step 2: Add api methods in `api.ts`**

Extend the type import with the four `Predlab*Resp` types + `PredlabBookName`, and add to the `api` object:

```typescript
  predlabPerformance: () =>
    get<PredlabPerformanceResp>("/api/predlab/performance"),
  predlabBook: (b: PredlabBookName) =>
    get<PredlabBookResp>(`/api/predlab/book?book=${b}`),
  predlabGate: () => get<PredlabGateResp>("/api/predlab/gate"),
  predlabHealth: () => get<PredlabHealthResp>("/api/predlab/health"),
```

- [ ] **Step 3: Type-check**

Run: `cd tradingagents/monitor/frontend && npx tsc --noEmit`
Expected: clean.

- [ ] **Step 4: Commit**

```bash
git add tradingagents/monitor/frontend/src/types.ts tradingagents/monitor/frontend/src/api.ts
git commit -m "feat(monitor-ui): predlab API types + client methods

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: EquityChart series-label generalization

**Files:**
- Modify: `tradingagents/monitor/frontend/src/charts/EquityChart.tsx`

**Interfaces:**
- Consumes: existing `EquityChartProps`.
- Produces: optional prop `labels?: { a: string; b: string }` (default `{ a: "quant", b: "hybrid" }`); series titles become `labels.a`, `labels.b`, `${labels.a} DD`, `${labels.b} DD`, `${labels.a} rSR`, `${labels.b} rSR`. Existing callers unchanged.

- [ ] **Step 1: Add the prop and thread labels through**

In `EquityChartProps` add `labels?: { a: string; b: string };`. At the top of the effect: `const labels = props.labels ?? { a: "quant", b: "hybrid" };` and replace the six hardcoded `title:` strings (`"quant"`, `"hybrid"`, `"quant DD"`, `"hybrid DD"`, `"quant rSR"`, `"hybrid rSR"`) with the templated forms above. Add `props.labels` to the effect dependency array.

- [ ] **Step 2: Verify existing usage compiles and tests pass**

Run: `cd tradingagents/monitor/frontend && npx tsc --noEmit && npx vitest run`
Expected: clean, existing tests pass.

- [ ] **Step 3: Commit**

```bash
git add tradingagents/monitor/frontend/src/charts/EquityChart.tsx
git commit -m "refactor(monitor-ui): configurable series labels on EquityChart

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Predlab Performance tab

**Files:**
- Create: `tradingagents/monitor/frontend/src/tabs/PredlabPerformanceTab.tsx`

**Interfaces:**
- Consumes: `api.predlabPerformance()`, `EquityChart` with `labels={{ a: "champion", b: "vt10" }}`, `rebaseTo100`/`sliceFromDays` from `lib/rebase`, `fmtNum`/`fmtPct` from `lib/format`, `Card`/`Badge`/`Section`.
- Produces: `export function PredlabPerformanceTab()` (registered in Task 9).

- [ ] **Step 1: Implement the tab**

Follow `PerformanceTab.tsx` structurally (range pills, `prep` memo, cards row per book, chart section). Champion uses Badge kind `"quant"` (green, matches chart color slot A), vt10 uses `"hybrid"` (purple, slot B):

```tsx
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Card } from "../components/Card";
import { Badge } from "../components/Badge";
import { Section } from "../components/Section";
import { EquityChart } from "../charts/EquityChart";
import { fmtNum, fmtPct } from "../lib/format";
import { rebaseTo100, sliceFromDays } from "../lib/rebase";
import type { PredlabBookPerf, PredlabYearlyRow } from "../types";

const RANGES = [
  { label: "7d", days: 7 }, { label: "30d", days: 30 },
  { label: "90d", days: 90 }, { label: "all", days: null },
] as const;

function prep(p: PredlabBookPerf | null, days: number | null) {
  return {
    eq: p ? rebaseTo100(sliceFromDays(p.equity, days)) : [],
    dd: p ? sliceFromDays(p.drawdown, days) : [],
    rs: p ? sliceFromDays(p.rolling_sharpe, days) : [],
  };
}

function CardsRow(props: {
  name: string; kind: "quant" | "hybrid"; p: PredlabBookPerf;
}) {
  const c = props.p.cards;
  const warm = c.warmup.n < c.warmup.required;
  return (
    <div style={{ marginTop: 10 }}>
      <Badge kind={props.kind}>{props.name.toUpperCase()}</Badge>{" "}
      <span className="muted">as of {c.last_asof} · {c.n_days} rows</span>
      <div className="cards" style={{ marginTop: 6 }}>
        <Card label="Cumulative return" value={fmtPct(c.cum_return)}
          tone={c.cum_return >= 0 ? "pos" : "neg"} />
        <Card label="Sharpe (paper)" value={fmtNum(c.sharpe)}
          tone={c.sharpe >= 0 ? "pos" : "neg"} />
        <Card label="Max drawdown" value={fmtPct(c.max_drawdown)} tone="neg" />
        <Card label="VT scale"
          value={c.scale !== null ? fmtNum(c.scale)
            : `warming up (${c.warmup.n}/${c.warmup.required})`} />
        <Card label="Avg turnover" value={fmtPct(c.avg_turnover)} />
        <Card label="Cum est. cost" value={fmtPct(c.cum_cost)} tone="neg" />
      </div>
      {warm && <p className="muted">
        vol-target scale needs {c.warmup.required} realized returns —
        {" "}{c.warmup.required - c.warmup.n} to go</p>}
    </div>
  );
}

function YearlyTable(props: {
  years: Record<string, PredlabYearlyRow>; title: string;
}) {
  const keys = Object.keys(props.years).sort();
  return (
    <table>
      <thead><tr><th>{props.title}</th><th>SR</th><th>Return</th>
        <th>Max DD</th><th>Days</th></tr></thead>
      <tbody>
        {keys.map((y) => (
          <tr key={y}><td>{y}</td>
            <td>{fmtNum(props.years[y].sr)}</td>
            <td>{fmtPct(props.years[y].ret)}</td>
            <td>{fmtPct(props.years[y].maxdd)}</td>
            <td>{props.years[y].n_days}</td></tr>
        ))}
      </tbody>
    </table>
  );
}

export function PredlabPerformanceTab() {
  const q = useQuery({
    queryKey: ["predlab-performance"], queryFn: api.predlabPerformance,
  });
  const [days, setDays] = useState<number | null>(null);
  const d = q.data;
  const champ = useMemo(() => prep(d?.books.champion ?? null, days), [d, days]);
  const vt10 = useMemo(() => prep(d?.books.vt10 ?? null, days), [d, days]);
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !d) return <div className="badge error">failed: {String(q.error)}</div>;

  return (
    <>
      {d.books.champion
        ? <CardsRow name="champion" kind="quant" p={d.books.champion} />
        : <p className="muted">champion journal unavailable</p>}
      {d.books.vt10
        ? <CardsRow name="vt10 (old book)" kind="hybrid" p={d.books.vt10} />
        : <p className="muted">vt10 journal unavailable</p>}

      <Section title="Paper equity (indexed to 100) · drawdown · rolling Sharpe"
        right={
          <div className="pills">
            {RANGES.map((r) => (
              <button key={r.label} className={`pill ${days === r.days ? "active" : ""}`}
                onClick={() => setDays(r.days)}>{r.label}</button>
            ))}
          </div>
        }>
        <EquityChart
          quantEquity={champ.eq} hybridEquity={vt10.eq}
          quantDd={champ.dd} hybridDd={vt10.dd}
          quantRs={champ.rs} hybridRs={vt10.rs}
          anchors={{ quant: d.reference?.ovl_sr_full ?? 0, hybrid: null }}
          labels={{ a: "champion", b: "vt10" }}
        />
        {(d.books.champion?.rolling_sharpe.length ?? 0) === 0 &&
          <p className="muted">rolling Sharpe appears after 30 realized days</p>}
      </Section>

      {d.reference && (
        <Section title="Frozen dev reference (2021-01 → 2026-07, backtest)">
          <div className="cards">
            <Card label="Overlaid SR" value={fmtNum(d.reference.ovl_sr_full)} />
            <Card label="Overlaid MaxDD" value={fmtPct(d.reference.ovl_maxdd)} tone="neg" />
            <Card label="Raw SR" value={fmtNum(d.reference.raw_sr_full)} />
            <Card label="DSR (selection pool)" value={fmtNum(d.reference.dsr_selection_pool)} />
          </div>
        </Section>
      )}

      {d.backtest_yearly?.champion && (
        <Section title="Backtest (dev) yearly — overlaid, net">
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
            <YearlyTable years={d.backtest_yearly.champion} title="champion" />
            {d.backtest_yearly.vt10 &&
              <YearlyTable years={d.backtest_yearly.vt10} title="vt10" />}
          </div>
        </Section>
      )}
    </>
  );
}
```

- [ ] **Step 2: Type-check**

Run: `cd tradingagents/monitor/frontend && npx tsc --noEmit`
Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add tradingagents/monitor/frontend/src/tabs/PredlabPerformanceTab.tsx
git commit -m "feat(monitor-ui): predlab Performance tab

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: Predlab Book tab

**Files:**
- Create: `tradingagents/monitor/frontend/src/tabs/PredlabBookTab.tsx`

**Interfaces:**
- Consumes: `api.predlabBook(b)`, types `PredlabBookName`, `PredlabBookDetail`.
- Produces: `export function PredlabBookTab()` (registered in Task 9).

- [ ] **Step 1: Implement the tab**

```tsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Card } from "../components/Card";
import { Section } from "../components/Section";
import { fmtNum, fmtPct } from "../lib/format";
import type { PredlabBookName, PredlabWeight } from "../types";

const BOOKS: PredlabBookName[] = ["champion", "vt10"];

function WeightsTable(props: { title: string; rows: PredlabWeight[] }) {
  return (
    <div style={{ flex: 1, minWidth: 260 }}>
      <h3>{props.title} ({props.rows.length})</h3>
      <table>
        <thead><tr><th>Symbol</th><th>Weight</th></tr></thead>
        <tbody>
          {props.rows.map((r) => (
            <tr key={r.symbol}><td>{r.symbol}</td>
              <td>{fmtPct(r.weight)}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PredlabBookTab() {
  const [book, setBook] = useState<PredlabBookName>("champion");
  const q = useQuery({
    queryKey: ["predlab-book", book], queryFn: () => api.predlabBook(book),
  });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  const d = q.data.detail;

  return (
    <>
      <div className="pills" style={{ marginTop: 10 }}>
        {BOOKS.map((b) => (
          <button key={b} className={`pill ${b === book ? "active" : ""}`}
            onClick={() => setBook(b)}>{b}</button>
        ))}
      </div>
      {!d ? <p className="muted">no journal rows for {book}</p> : (
        <>
          <div className="cards" style={{ marginTop: 10 }}>
            <Card label="As of" value={d.asof} />
            <Card label="Universe" value={String(d.n_universe ?? "—")} />
            <Card label="Breadth" value={String(d.breadth ?? "—")} />
            <Card label="VT scale" value={fmtNum(d.scale)} />
            <Card label="Est. turnover" value={fmtPct(d.est_turnover)} />
            <Card label="Est. cost" value={fmtPct(d.est_cost)} />
          </div>
          <p className="muted">
            membership {d.membership_hash ?? "—"}
            {d.delta && <> · vs prev day: {d.delta.entered} entered,
              {" "}{d.delta.exited} exited</>}
          </p>
          <Section title="Today's book">
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
              <WeightsTable title="Long" rows={d.longs} />
              <WeightsTable title="Short" rows={d.shorts} />
            </div>
          </Section>
        </>
      )}
    </>
  );
}
```

- [ ] **Step 2: Type-check** — `npx tsc --noEmit`, expected clean.

- [ ] **Step 3: Commit**

```bash
git add tradingagents/monitor/frontend/src/tabs/PredlabBookTab.tsx
git commit -m "feat(monitor-ui): predlab Book tab

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: Gate + Ops tabs

**Files:**
- Create: `tradingagents/monitor/frontend/src/tabs/PredlabGateTab.tsx`
- Create: `tradingagents/monitor/frontend/src/tabs/PredlabOpsTab.tsx`

**Interfaces:**
- Consumes: `api.predlabGate()`, `api.predlabHealth()`, types `PredlabGateResp`, `PredlabHealthResp`, `PredlabBookName`.
- Produces: `export function PredlabGateTab()`, `export function PredlabOpsTab()` (registered in Task 9).

- [ ] **Step 1: Implement `PredlabGateTab.tsx`**

```tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Card } from "../components/Card";
import { Section } from "../components/Section";
import { fmtNum } from "../lib/format";

export function PredlabGateTab() {
  const q = useQuery({ queryKey: ["predlab-gate"], queryFn: api.predlabGate });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  const g = q.data;
  const total = g.days_elapsed + g.days_remaining;
  const pct = total > 0 ? Math.min(100, (g.days_elapsed / total) * 100) : 0;

  return (
    <>
      <p className="muted" style={{ marginTop: 10 }}>
        Informational tracker only — the forward evaluation is ONE-SHOT,
        earliest {g.earliest_eval}. Nothing shown here constitutes an
        evaluation of the sealed window.
      </p>
      <div className="cards">
        <Card label="Forward window start" value={g.window_start} />
        <Card label="Earliest evaluation" value={g.earliest_eval} />
        <Card label="Days elapsed" value={String(g.days_elapsed)} />
        <Card label="Days remaining" value={String(g.days_remaining)} />
        <Card label="Threshold SR" value={fmtNum(g.threshold_sr, 3)} />
        <Card label="Running SR (paper proxy)"
          value={g.running.sr === null
            ? `— (${g.running.n_returns} returns)` : fmtNum(g.running.sr)}
          tone={(g.running.sr ?? 0) >= g.threshold_sr ? "pos" : ""} />
      </div>
      <Section title={`Progress to earliest evaluation (${pct.toFixed(0)}%)`}>
        <div style={{ background: "#21262d", borderRadius: 4, height: 14 }}>
          <div style={{
            width: `${pct}%`, height: "100%", borderRadius: 4,
            background: "#3fb950",
          }} />
        </div>
      </Section>
      <Section title="Pass criteria (sealed one-shot)">
        <ul>{g.criteria.map((c) => <li key={c}>{c}</li>)}</ul>
        <p className="muted">{g.running.note}</p>
      </Section>
    </>
  );
}
```

- [ ] **Step 2: Implement `PredlabOpsTab.tsx`**

```tsx
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Badge } from "../components/Badge";
import { Section } from "../components/Section";
import type { PredlabBookHealth, PredlabBookName } from "../types";

function BookHealth(props: { name: PredlabBookName; h: PredlabBookHealth | null }) {
  const h = props.h;
  return (
    <Section title={`${props.name} journal`}>
      {!h ? <p className="muted">no journal</p> : (
        <>
          <p>
            <Badge kind={h.stale ? "stale" : "ok"}>
              {h.stale ? "STALE" : "OK"}</Badge>{" "}
            last row {h.last_asof} · written {h.written_utc ?? "—"} ·
            {" "}{h.rows} rows
            {h.malformed > 0 && <> · <Badge kind="error">
              {h.malformed} malformed lines</Badge></>}
          </p>
          {h.gaps.length > 0 && (
            <table>
              <thead><tr><th>Missing date</th><th>Status</th></tr></thead>
              <tbody>
                {h.gaps.map((g) => (
                  <tr key={g.date}><td>{g.date}</td>
                    <td>{g.known
                      ? <span className="muted">known (scheduler off)</span>
                      : <Badge kind="error">unexplained</Badge>}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </Section>
  );
}

export function PredlabOpsTab() {
  const q = useQuery({ queryKey: ["predlab-health"], queryFn: api.predlabHealth });
  if (q.isLoading) return <div className="muted">loading…</div>;
  if (q.isError || !q.data) return <div className="badge error">failed: {String(q.error)}</div>;
  return (
    <>
      <BookHealth name="champion" h={q.data.books.champion} />
      <BookHealth name="vt10" h={q.data.books.vt10} />
      <p className="muted">{q.data.heartbeat_note}</p>
    </>
  );
}
```

- [ ] **Step 3: Type-check** — `npx tsc --noEmit`, expected clean.

- [ ] **Step 4: Commit**

```bash
git add tradingagents/monitor/frontend/src/tabs/PredlabGateTab.tsx tradingagents/monitor/frontend/src/tabs/PredlabOpsTab.tsx
git commit -m "feat(monitor-ui): predlab Gate + Ops tabs

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: Legacy wrapper, tab registry rework, Run-tab removal

**Files:**
- Create: `tradingagents/monitor/frontend/src/tabs/LegacyTab.tsx`
- Modify: `tradingagents/monitor/frontend/src/App.tsx` (full rewrite of TABS)
- Delete: `tradingagents/monitor/frontend/src/tabs/RunTab.tsx`, `tradingagents/monitor/frontend/src/lib/adhoc.ts`, `tradingagents/monitor/frontend/src/lib/adhoc.test.ts`
- Modify: `tradingagents/monitor/frontend/src/api.ts` (remove adhoc methods), `tradingagents/monitor/frontend/src/types.ts` (remove `Adhoc*` interfaces + `AdhocStrategy`)

**Interfaces:**
- Consumes: the four predlab tabs (Tasks 6–8); existing `PerformanceTab`, `PositionsTab`, `ExecutionsTab`, `DecisionsTab`, `HealthTab`.
- Produces: final tab registry `performance | book | gate | ops | legacy`; hash default `performance`.

- [ ] **Step 1: Create `LegacyTab.tsx`**

```tsx
import { useState } from "react";
import { PerformanceTab } from "./PerformanceTab";
import { PositionsTab } from "./PositionsTab";
import { ExecutionsTab } from "./ExecutionsTab";
import { DecisionsTab } from "./DecisionsTab";
import { HealthTab } from "./HealthTab";

const SUBTABS = [
  { id: "performance", label: "Performance", el: <PerformanceTab /> },
  { id: "positions", label: "Positions", el: <PositionsTab /> },
  { id: "executions", label: "Executions", el: <ExecutionsTab /> },
  { id: "decisions", label: "Decisions", el: <DecisionsTab /> },
  { id: "health", label: "Health", el: <HealthTab /> },
] as const;

/** Read-only archive of the decommissioned V5 quant/hybrid books. */
export function LegacyTab() {
  const [sub, setSub] = useState<string>("performance");
  const active = SUBTABS.find((t) => t.id === sub) ?? SUBTABS[0];
  return (
    <>
      <p className="badge stale" style={{ marginTop: 10 }}>
        V5 books decommissioned 2026-08-06 — read-only archive. Journals
        frozen; live-exchange panels may show STALE.
      </p>
      <div className="pills" style={{ marginTop: 8 }}>
        {SUBTABS.map((t) => (
          <button key={t.id} className={`pill ${t.id === active.id ? "active" : ""}`}
            onClick={() => setSub(t.id)}>{t.label}</button>
        ))}
      </div>
      {active.el}
    </>
  );
}
```

- [ ] **Step 2: Rewrite the `TABS` registry in `App.tsx`**

Replace imports (drop `RunTab`, add the four predlab tabs + `LegacyTab`) and the registry:

```tsx
const TABS = [
  {
    id: "performance", label: "Performance", el: <PredlabPerformanceTab />,
    desc: "Predlab champion (ewma_20 low-vol LS + vt15_b100) and old vt10 paper books — equity compounded from realized returns, Sharpe, drawdown, cost drag, plus the frozen dev backtest reference.",
  },
  {
    id: "book", label: "Book", el: <PredlabBookTab />,
    desc: "Today's cross-sectional book: 40 longs / 40 shorts at ±2.5%, universe membership, breadth and vol-target scale.",
  },
  {
    id: "gate", label: "Gate", el: <PredlabGateTab />,
    desc: "Sealed one-shot forward tracker — informational only; the evaluation happens once, earliest 2027-01-02.",
  },
  {
    id: "ops", label: "Ops", el: <PredlabOpsTab />,
    desc: "Journal freshness, gaps and malformed-line counts for both paper books, plus the backup-branch heartbeat.",
  },
  {
    id: "legacy", label: "Legacy", el: <LegacyTab />,
    desc: "Read-only archive of the decommissioned V5 8-coin quant/hybrid books (journals frozen 2026-08-06).",
  },
] as const;
```

In the nav render, replace the old Run-tab special-casing: separator + distinct style now apply to `legacy` (`t.id === "legacy"` → `<span className="tab-sep" />` before it, label `▸ Legacy`, className suffix `tab-run` reused for the muted styling).

- [ ] **Step 3: Delete Run-tab code and adhoc client**

```bash
git rm tradingagents/monitor/frontend/src/tabs/RunTab.tsx \
       tradingagents/monitor/frontend/src/lib/adhoc.ts \
       tradingagents/monitor/frontend/src/lib/adhoc.test.ts
```

Then remove from `api.ts`: the five `adhoc*` methods and the `Adhoc*` names in the type import. Remove from `types.ts`: `AdhocStrategy`, `AdhocMeta`, `AdhocRunBody`, `AdhocOutputMeta`, `AdhocStatus`, `AdhocOutput`, `AdhocRunRow`, `AdhocResult`. If `RunTab.tsx` had other imports (react-markdown), leave `package.json` alone — unused deps are harmless and keep the diff minimal.

- [ ] **Step 4: Type-check + unit tests + build**

Run: `cd tradingagents/monitor/frontend && npx tsc --noEmit && npx vitest run && npm run build`
Expected: all clean; build emits `dist/`.

- [ ] **Step 5: Commit (including rebuilt dist)**

```bash
git add -A tradingagents/monitor/frontend
git commit -m "feat(monitor-ui): predlab-first tab registry, Legacy archive, drop Run tab

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 10: Full verification + smoke run

**Files:** none new

- [ ] **Step 1: Full monitor test suite**

Run: `python -m pytest tests/monitor/ -q`
Expected: PASS, zero regressions.

- [ ] **Step 2: Local smoke run against real predlab data**

```bash
cd /home/malecada/master_thesis/TradingAgents
TA_MONITOR_PASSWORD=devpw \
PREDLAB_DATA_DIR=/home/malecada/master_thesis/TradingAgents-predlab/data \
QUANT_DATA_DIR=data LOG_DIR=logs \
python -m tradingagents.monitor &
sleep 3
curl -su admin:devpw http://127.0.0.1:8800/api/predlab/performance | head -c 400
curl -su admin:devpw http://127.0.0.1:8800/api/predlab/book?book=champion | head -c 400
curl -su admin:devpw http://127.0.0.1:8800/api/predlab/gate
curl -su admin:devpw http://127.0.0.1:8800/api/predlab/health
kill %1
```

Expected: real champion rows (asof 2026-08-03+), gate `informational: true`, health shows the known gap handling. Optionally verify the SPA renders via Playwright browser tools at `http://127.0.0.1:8800` (basic-auth in URL: `http://admin:devpw@127.0.0.1:8800`).

- [ ] **Step 3: Commit any fixes surfaced by the smoke run** (message `fix(monitor): smoke-run fixes for predlab endpoints`).

---

### Task 11: Deploy config + docs

**Files:**
- Modify: `deploy/systemd/ta-monitor.service` (add env line)
- Modify: `tradingagents/monitor/README.md` (document predlab source + new tabs, drop Run-tab docs)

**Interfaces:**
- Consumes: everything prior.
- Produces: merged branch; manual VPS steps surfaced to the user (NOT executed — prod systemd writes are blocked by policy).

- [ ] **Step 1: Add the env line to `ta-monitor.service`**

Next to the existing `Environment=` lines add:

```ini
Environment=PREDLAB_DATA_DIR=/opt/tradingagents/predlab-data
```

- [ ] **Step 2: Update `tradingagents/monitor/README.md`**

Document: predlab-first tab set, the four `/api/predlab/*` endpoints, `PREDLAB_DATA_DIR` env, journal semantics (weights-and-returns, equity compounded, warm-up 21), Legacy archive note, Run-tab removal (backend adhoc routes remain but have no UI).

- [ ] **Step 3: Commit + merge**

```bash
git add deploy/systemd/ta-monitor.service tradingagents/monitor/README.md
git commit -m "chore(monitor): PREDLAB_DATA_DIR deploy env + README overhaul

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

Then follow superpowers:finishing-a-development-branch for the merge to main.

- [ ] **Step 4: Surface manual VPS steps to the user (do not run over ssh)**

Print these for the user to run on the VPS (policy: prod systemd writes blocked for the agent):

```bash
# 1. copy small reference files next to the journals
scp /home/malecada/master_thesis/TradingAgents-predlab/data/predlab/gates.json \
    /home/malecada/master_thesis/TradingAgents-predlab/data/predlab/champion_backtest.json \
    <vps>:/opt/tradingagents/predlab-data/predlab/

# 2. on the VPS as root
cd /opt/tradingagents/repo && git pull
cp deploy/systemd/ta-monitor.service /etc/systemd/system/ta-monitor.service
systemctl daemon-reload
systemctl restart ta-monitor.service
systemctl status ta-monitor.service --no-pager
curl -su admin:$PASS http://127.0.0.1:8800/api/predlab/health
```

---

## Self-review notes (done at plan time)

- Spec coverage: backend module/source/endpoints → Tasks 1–3; four tabs → 6–8; Legacy + Run removal → 9; deploy env + reference copy + manual VPS → 11; testing → every task + 10; backtest-context change (yearly table, no curve) reflected in Task 6 and amended in the spec.
- Type consistency: payload keys (`books.champion.cards.warmup.n`, `gate.threshold_sr`, `health.books.*.gaps[].known`) match across Tasks 1–4 and 6–8; `gate_status` receives the whole `final_champion` block (noted in Task 2 Step 3).
- Known judgment calls: champion reuses Badge/chart slot A (green), vt10 slot B (purple); adhoc backend stays; `package.json` untouched even if react-markdown becomes unused.
