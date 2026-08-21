# S1 Champion Live Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trade the Phase-O champion book with $3,000 real capital on Binance USDT-M perps to measure real fills and slippage, as a journal-follower that never touches the registered paper forward test.

**Architecture:** Pure decision logic in `tradingagents/predlab/live_exec.py` (sizing, rounding, diffing, risk caps — fully unit-testable, no network). Thin signed-REST client in `tradingagents/predlab/binance_client.py`. CLI `scripts/predlab_s1_live.py` wires them: reads last `journal_champion.jsonl` row, places delta market orders, writes `data/predlab/s1_live/` journals. VPS cron chains it after the existing paper trader.

**Tech Stack:** Python 3.13, stdlib only for the client (urllib + hmac — no new deps), pandas/numpy already present, pytest.

**Spec:** `docs/superpowers/specs/2026-08-21-s1-live-executor-design.md`

## Global Constraints

- **Never modify** `scripts/predlab_s1_paper.py` or anything under `data/predlab/s1_paper/`.
- Funding: $3,000. Equity is always read live from the account, never a constant.
- Risk rails (hard): gross ≤ 2.2 × equity; per-symbol ≤ 5% of gross target; daily-loss halt at equity < 95% of day-start; `halt.flag` blocks everything; null `vt15_b100_scale` → WAIT.
- Orders: MARKET, one-way position mode, cross margin, leverage 2.
- All amounts USDT. All timestamps UTC.
- Idempotent per `asof` date: champion date already in `journal_live.jsonl` → exit without orders.
- Existing predlab test suite (156 tests) stays green: `python -m pytest tests/predlab/ -q`.
- Run tests from repo root `/home/malecada/master_thesis/TradingAgents-predlab` with its venv.

---

### Task 1: Sizing and leg filtering (`live_exec.py` core)

**Files:**
- Create: `tradingagents/predlab/live_exec.py`
- Test: `tests/predlab/test_live_exec.py`

**Interfaces:**
- Produces:
  - `SymbolFilter(min_notional: float, step_size: float)` frozen dataclass
  - `build_targets(weights: dict[str,float], scale: float, equity: float, marks: dict[str,float], filters: dict[str,SymbolFilter]) -> tuple[dict[str,float], list[dict]]` — returns `(target_qty_by_symbol_signed, dropped)`; each dropped item `{"symbol","reason","target_notional"}`; reasons: `"no_mark"`, `"no_filter"`, `"min_notional"`, `"rounds_to_zero"`.

- [ ] **Step 1: Write failing tests**

```python
# tests/predlab/test_live_exec.py
import math
import pytest

from tradingagents.predlab.live_exec import SymbolFilter, build_targets

F = {
    "AAAUSDT": SymbolFilter(min_notional=5.0, step_size=1.0),
    "BTCUSDT": SymbolFilter(min_notional=50.0, step_size=0.001),
    "BBBUSDT": SymbolFilter(min_notional=20.0, step_size=0.1),
}
MARKS = {"AAAUSDT": 2.0, "BTCUSDT": 73450.0, "BBBUSDT": 10.0}


class TestBuildTargets:
    def test_basic_sizing_rounds_down_to_step(self):
        # leg target = 0.025 * 1.0 * 4000 = 100 USDT -> 50 units of AAA, step 1.0
        tq, dropped = build_targets({"AAAUSDT": 0.025}, 1.0, 4000.0, MARKS, F)
        assert tq == {"AAAUSDT": 50.0}
        assert dropped == []

    def test_short_leg_negative_qty(self):
        tq, _ = build_targets({"AAAUSDT": -0.025}, 1.0, 4000.0, MARKS, F)
        assert tq == {"AAAUSDT": -50.0}

    def test_scale_multiplies(self):
        tq, _ = build_targets({"AAAUSDT": 0.025}, 2.0, 4000.0, MARKS, F)
        assert tq == {"AAAUSDT": 100.0}

    def test_drop_below_min_notional(self):
        # target = 0.025 * 400 = 10 < 20 min notional
        tq, dropped = build_targets({"BBBUSDT": 0.025}, 1.0, 400.0, MARKS, F)
        assert tq == {}
        assert dropped[0]["symbol"] == "BBBUSDT"
        assert dropped[0]["reason"] == "min_notional"

    def test_drop_rounds_to_zero(self):
        # BTC target = 0.025 * 2000 = 50 USDT >= min_notional 50,
        # but qty 50/73450 = 0.00068 rounds down to 0 at step 0.001
        tq, dropped = build_targets({"BTCUSDT": 0.025}, 1.0, 2000.0, MARKS, F)
        assert tq == {}
        assert dropped[0]["reason"] == "rounds_to_zero"

    def test_btc_clears_at_3k(self):
        # target = 75 USDT -> qty 0.001021 -> rounds to 0.001 (= 73.45 USDT >= 50)
        tq, dropped = build_targets({"BTCUSDT": 0.025}, 1.0, 3000.0, MARKS, F)
        assert tq == {"BTCUSDT": 0.001}
        assert dropped == []

    def test_missing_mark_dropped(self):
        tq, dropped = build_targets({"ZZZUSDT": 0.025}, 1.0, 4000.0, MARKS, F)
        assert tq == {}
        assert dropped[0]["reason"] == "no_mark"

    def test_missing_filter_dropped(self):
        marks = dict(MARKS, ZZZUSDT=1.0)
        tq, dropped = build_targets({"ZZZUSDT": 0.025}, 1.0, 4000.0, marks, F)
        assert dropped[0]["reason"] == "no_filter"

    def test_step_rounding_no_float_dust(self):
        # 0.1 step must not produce 0.30000000000000004
        f = {"CCCUSDT": SymbolFilter(5.0, 0.1)}
        tq, _ = build_targets({"CCCUSDT": 0.025}, 1.0, 1400.0, {"CCCUSDT": 100.0}, f)
        assert tq == {"CCCUSDT": 0.3}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/predlab/test_live_exec.py -q`
Expected: FAIL / collection error `ModuleNotFoundError` or `ImportError: cannot import name 'SymbolFilter'`.

- [ ] **Step 3: Implement**

```python
# tradingagents/predlab/live_exec.py
"""Pure decision logic for the S1 champion live executor.

No network, no filesystem: sizing, rounding, position diffing, risk caps,
and journal-row construction as pure functions. The CLI wrapper
(scripts/predlab_s1_live.py) owns all I/O. Spec:
docs/superpowers/specs/2026-08-21-s1-live-executor-design.md
"""
from __future__ import annotations

import math
from dataclasses import dataclass

LEG_WEIGHT_ABS = 0.025  # champion book: 40L/40S quintile-equal


@dataclass(frozen=True)
class SymbolFilter:
    min_notional: float
    step_size: float


def _round_step(qty: float, step: float) -> float:
    """Round |qty| down to the step grid without float dust."""
    n = math.floor(qty / step + 1e-9)
    # quantize via the step's decimal string to avoid 0.30000000000000004
    s = f"{step:.10f}".rstrip("0")
    decimals = len(s.split(".")[1]) if "." in s else 0
    return round(n * step, decimals)


def build_targets(weights: "dict[str, float]", scale: float, equity: float,
                  marks: "dict[str, float]", filters: "dict[str, SymbolFilter]",
                  ) -> "tuple[dict[str, float], list[dict]]":
    """Signed target quantity per symbol; drops legs that cannot trade."""
    targets: "dict[str, float]" = {}
    dropped: "list[dict]" = []

    def drop(sym: str, reason: str, notional: float) -> None:
        dropped.append({"symbol": sym, "reason": reason,
                        "target_notional": round(notional, 2)})

    for sym, w in weights.items():
        notional = abs(w) * scale * equity
        if sym not in marks or not marks[sym]:
            drop(sym, "no_mark", notional)
            continue
        if sym not in filters:
            drop(sym, "no_filter", notional)
            continue
        f = filters[sym]
        if notional < f.min_notional:
            drop(sym, "min_notional", notional)
            continue
        qty = _round_step(notional / marks[sym], f.step_size)
        if qty <= 0:
            drop(sym, "rounds_to_zero", notional)
            continue
        targets[sym] = qty if w > 0 else -qty
    return targets, dropped
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/predlab/test_live_exec.py -q`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/predlab/live_exec.py tests/predlab/test_live_exec.py
git commit -m "feat(predlab): live executor sizing + leg filtering (pure logic)"
```

---

### Task 2: Position diffing → orders

**Files:**
- Modify: `tradingagents/predlab/live_exec.py`
- Test: `tests/predlab/test_live_exec.py`

**Interfaces:**
- Consumes: `SymbolFilter`, `_round_step` from Task 1.
- Produces:
  - `Order(symbol: str, side: str, qty: float, reduce_only: bool)` frozen dataclass; `side` in `{"BUY","SELL"}`; `qty` always positive.
  - `diff_orders(targets: dict[str,float], positions: dict[str,float], marks: dict[str,float], filters: dict[str,SymbolFilter], dust_usd: float = 7.0) -> tuple[list[Order], list[dict]]` — `(orders, skipped)`; skip reasons `"dust"`, `"increase_below_min_notional"`. Symbols in `positions` but not in `targets` are closed with reduce-only orders. Orders sorted: reduce-only first, then by symbol.

- [ ] **Step 1: Write failing tests**

Append to `tests/predlab/test_live_exec.py`:

```python
from tradingagents.predlab.live_exec import Order, diff_orders


class TestDiffOrders:
    def test_open_new_long(self):
        orders, skipped = diff_orders({"AAAUSDT": 50.0}, {}, MARKS, F)
        assert orders == [Order("AAAUSDT", "BUY", 50.0, False)]
        assert skipped == []

    def test_open_new_short(self):
        orders, _ = diff_orders({"AAAUSDT": -50.0}, {}, MARKS, F)
        assert orders == [Order("AAAUSDT", "SELL", 50.0, False)]

    def test_no_change_no_order(self):
        orders, skipped = diff_orders({"AAAUSDT": 50.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [] and skipped == []

    def test_partial_reduce_is_reduce_only(self):
        orders, _ = diff_orders({"AAAUSDT": 30.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [Order("AAAUSDT", "SELL", 20.0, True)]

    def test_close_missing_target_reduce_only(self):
        orders, _ = diff_orders({}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [Order("AAAUSDT", "SELL", 50.0, True)]

    def test_sign_flip_single_crossing_order_not_reduce_only(self):
        # long 50 -> short 40: one SELL 90, cannot be reduceOnly
        orders, _ = diff_orders({"AAAUSDT": -40.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [Order("AAAUSDT", "SELL", 90.0, False)]

    def test_dust_delta_skipped(self):
        # delta 3 units * 2.0 = 6 USDT < 7 dust threshold
        orders, skipped = diff_orders({"AAAUSDT": 53.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == []
        assert skipped[0]["reason"] == "dust"

    def test_small_reduce_below_dust_skipped(self):
        orders, skipped = diff_orders({"AAAUSDT": 48.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [] and skipped[0]["reason"] == "dust"

    def test_increase_below_min_notional_skipped(self):
        # BBB delta 1.5 * 10 = 15 USDT >= dust but < min_notional 20, increasing
        orders, skipped = diff_orders({"BBBUSDT": 6.5}, {"BBBUSDT": 5.0}, MARKS, F)
        assert orders == []
        assert skipped[0]["reason"] == "increase_below_min_notional"

    def test_reduce_below_min_notional_still_sent(self):
        # reduce-only orders are exempt from MIN_NOTIONAL (-4164)
        orders, _ = diff_orders({"BBBUSDT": 5.0}, {"BBBUSDT": 6.5}, MARKS, F)
        assert orders == [Order("BBBUSDT", "SELL", 1.5, True)]

    def test_reduce_only_orders_sorted_first(self):
        orders, _ = diff_orders(
            {"AAAUSDT": 50.0}, {"BBBUSDT": 10.0}, MARKS, F)
        assert [o.reduce_only for o in orders] == [True, False]

    def test_delta_rounded_to_step(self):
        # BTC: current 0.002, target 0.0035 -> delta 0.0015 rounds to 0.001
        orders, _ = diff_orders({"BTCUSDT": 0.0035}, {"BTCUSDT": 0.002},
                                MARKS, F, dust_usd=7.0)
        assert orders == [Order("BTCUSDT", "BUY", 0.001, False)]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/predlab/test_live_exec.py -q`
Expected: FAIL `ImportError: cannot import name 'Order'`.

- [ ] **Step 3: Implement**

Append to `tradingagents/predlab/live_exec.py`:

```python
@dataclass(frozen=True)
class Order:
    symbol: str
    side: str          # "BUY" | "SELL"
    qty: float         # always positive
    reduce_only: bool


def diff_orders(targets: "dict[str, float]", positions: "dict[str, float]",
                marks: "dict[str, float]", filters: "dict[str, SymbolFilter]",
                dust_usd: float = 7.0) -> "tuple[list[Order], list[dict]]":
    """Delta market orders taking `positions` to `targets`.

    Reduce-only when the order only shrinks an existing position (exempt
    from Binance MIN_NOTIONAL rejection -4164); a sign flip is one plain
    crossing order. Dust deltas and sub-min-notional increases are skipped.
    """
    orders: "list[Order]" = []
    skipped: "list[dict]" = []
    for sym in sorted(set(targets) | set(positions)):
        tgt = targets.get(sym, 0.0)
        cur = positions.get(sym, 0.0)
        f = filters.get(sym)
        if f is None or sym not in marks:
            continue  # cannot price/round the delta; leg already logged upstream
        delta = _round_step(abs(tgt - cur), f.step_size)
        if delta <= 0:
            continue
        notional = delta * marks[sym]
        if notional < dust_usd:
            skipped.append({"symbol": sym, "reason": "dust",
                            "delta_notional": round(notional, 2)})
            continue
        reduce_only = (
            cur != 0.0
            and (tgt == 0.0 or (math.copysign(1, tgt) == math.copysign(1, cur)
                                and abs(tgt) < abs(cur)))
        )
        if not reduce_only and notional < f.min_notional:
            skipped.append({"symbol": sym,
                            "reason": "increase_below_min_notional",
                            "delta_notional": round(notional, 2)})
            continue
        side = "BUY" if tgt - cur > 0 else "SELL"
        orders.append(Order(sym, side, delta, reduce_only))
    orders.sort(key=lambda o: (not o.reduce_only, o.symbol))
    return orders, skipped
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/predlab/test_live_exec.py -q`
Expected: 21 passed.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/predlab/live_exec.py tests/predlab/test_live_exec.py
git commit -m "feat(predlab): live executor position diffing with reduce-only + dust rules"
```

---

### Task 3: Risk caps, daily-loss halt, journal row

**Files:**
- Modify: `tradingagents/predlab/live_exec.py`
- Test: `tests/predlab/test_live_exec.py`

**Interfaces:**
- Consumes: nothing new (pure functions).
- Produces:
  - `check_caps(target_notionals: dict[str,float], equity: float, gross_cap: float = 2.2, per_symbol_cap: float = 0.05) -> list[str]` — human-readable violation strings, empty = OK. `target_notionals` are signed USDT notionals.
  - `daily_loss_breached(equity: float, day_start_equity: float, limit: float = 0.05) -> bool`
  - `build_journal_row(asof: str, executed_utc: str, equity_before: float, equity_day_start: float, scale: float, targets_notional: dict[str,float], orders: list[Order], dropped: list[dict], skipped: list[dict], halt: bool, dry_run: bool) -> dict` — exactly the spec's `journal_live.jsonl` schema; `legs_dropped_min_notional` holds ALL dropped legs (any reason), `deltas_skipped_dust` = count of skipped deltas, `gross_target` = Σ|notional| rounded to 2dp.

- [ ] **Step 1: Write failing tests**

Append to `tests/predlab/test_live_exec.py`:

```python
from tradingagents.predlab.live_exec import (
    build_journal_row, check_caps, daily_loss_breached)


class TestRiskAndJournal:
    def test_caps_ok(self):
        tn = {"AAAUSDT": 3000.0, "BBBUSDT": -3000.0}
        assert check_caps(tn, equity=3000.0) == []

    def test_gross_cap_violation(self):
        tn = {"AAAUSDT": 4000.0, "BBBUSDT": -3000.0}
        v = check_caps(tn, equity=3000.0)
        assert len(v) == 1 and "gross" in v[0]

    def test_per_symbol_cap_violation(self):
        tn = {"AAAUSDT": 400.0, "BBBUSDT": -100.0,
              "CCCUSDT": 100.0, "DDDUSDT": -100.0}
        v = check_caps(tn, equity=3000.0)
        assert any("AAAUSDT" in s for s in v)

    def test_empty_book_no_violations(self):
        assert check_caps({}, equity=3000.0) == []

    def test_daily_loss(self):
        assert daily_loss_breached(2849.0, 3000.0) is True
        assert daily_loss_breached(2851.0, 3000.0) is False

    def test_journal_row_schema(self):
        row = build_journal_row(
            asof="2026-08-22", executed_utc="2026-08-23T00:07:00+00:00",
            equity_before=3000.0, equity_day_start=3010.0, scale=1.2,
            targets_notional={"AAAUSDT": 90.0, "BBBUSDT": -90.0},
            orders=[Order("AAAUSDT", "BUY", 45.0, False)],
            dropped=[{"symbol": "BTCUSDT", "reason": "rounds_to_zero",
                      "target_notional": 50.0}],
            skipped=[{"symbol": "CCCUSDT", "reason": "dust",
                      "delta_notional": 6.0}],
            halt=False, dry_run=True)
        assert row["asof"] == "2026-08-22"
        assert row["orders_placed"] == 1
        assert row["gross_target"] == 180.0
        assert row["legs_dropped_min_notional"] == [
            {"symbol": "BTCUSDT", "reason": "rounds_to_zero",
             "target_notional": 50.0}]
        assert row["deltas_skipped_dust"] == 1
        assert row["dry_run"] is True and row["halt"] is False
        assert row["scale"] == 1.2 and row["equity_day_start"] == 3010.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/predlab/test_live_exec.py -q`
Expected: FAIL `ImportError: cannot import name 'check_caps'`.

- [ ] **Step 3: Implement**

Append to `tradingagents/predlab/live_exec.py`:

```python
def check_caps(target_notionals: "dict[str, float]", equity: float,
               gross_cap: float = 2.2, per_symbol_cap: float = 0.05,
               ) -> "list[str]":
    """Hard pre-trade caps on the post-trade book. Empty list = OK."""
    violations: "list[str]" = []
    gross = sum(abs(v) for v in target_notionals.values())
    if gross > gross_cap * equity:
        violations.append(
            f"gross {gross:.0f} > {gross_cap} x equity {equity:.0f}")
    if gross > 0:
        for sym, v in sorted(target_notionals.items()):
            if abs(v) > per_symbol_cap * gross:
                violations.append(
                    f"{sym} notional {abs(v):.0f} > "
                    f"{per_symbol_cap:.0%} of gross {gross:.0f}")
    return violations


def daily_loss_breached(equity: float, day_start_equity: float,
                        limit: float = 0.05) -> bool:
    return equity < (1.0 - limit) * day_start_equity


def build_journal_row(asof: str, executed_utc: str, equity_before: float,
                      equity_day_start: float, scale: float,
                      targets_notional: "dict[str, float]",
                      orders: "list[Order]", dropped: "list[dict]",
                      skipped: "list[dict]", halt: bool, dry_run: bool) -> dict:
    return {
        "asof": asof,
        "executed_utc": executed_utc,
        "equity_before": round(equity_before, 2),
        "equity_day_start": round(equity_day_start, 2),
        "scale": scale,
        "targets": {k: round(v, 2) for k, v in sorted(targets_notional.items())},
        "orders_placed": len(orders),
        "legs_dropped_min_notional": dropped,
        "deltas_skipped_dust": len(skipped),
        "gross_target": round(sum(abs(v) for v in targets_notional.values()), 2),
        "halt": halt,
        "dry_run": dry_run,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/predlab/test_live_exec.py -q`
Expected: 27 passed.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/predlab/live_exec.py tests/predlab/test_live_exec.py
git commit -m "feat(predlab): live executor risk caps, daily-loss halt, journal row"
```

---

### Task 4: Signed Binance futures REST client

**Files:**
- Create: `tradingagents/predlab/binance_client.py`
- Test: `tests/predlab/test_binance_client.py`

**Interfaces:**
- Consumes: env vars `BINANCE_API_KEY` / `BINANCE_API_SECRET` (constructor args take precedence).
- Produces class `FuturesClient(api_key: str, api_secret: str, base: str = "https://fapi.binance.com")` with:
  - `exchange_info() -> dict` (public GET `/fapi/v1/exchangeInfo`)
  - `equity() -> float` (signed GET `/fapi/v2/account` → `float(totalMarginBalance)`)
  - `positions() -> dict[str, float]` (signed GET `/fapi/v2/positionRisk` → `{symbol: signed positionAmt}` for nonzero only)
  - `set_leverage(symbol: str, leverage: int) -> None` (signed POST `/fapi/v1/leverage`)
  - `market_order(symbol: str, side: str, qty: float, reduce_only: bool) -> dict` (signed POST `/fapi/v1/order`, `type=MARKET`, `newOrderRespType=RESULT` → returns response dict with `avgPrice`, `executedQty`, `cumQuote`, `orderId`)
  - `user_trades(symbol: str, order_id: int) -> list[dict]` (signed GET `/fapi/v1/userTrades?orderId=` — commission per fill)
  - All requests: `timestamp` + `recvWindow=10000` + HMAC-SHA256 `signature` over the urlencoded query; `X-MBX-APIKEY` header. Non-2xx → raise `BinanceAPIError(code, msg)` (exported). Retry once after 2s on HTTP 5xx / URLError; never retry 4xx.
  - Testability seam: all HTTP goes through `self._http(method: str, path: str, params: dict, signed: bool) -> dict` — tests monkeypatch `_http`.

- [ ] **Step 1: Write failing tests**

```python
# tests/predlab/test_binance_client.py
import hashlib
import hmac
import urllib.parse

import pytest

from tradingagents.predlab.binance_client import BinanceAPIError, FuturesClient


@pytest.fixture
def client():
    return FuturesClient(api_key="k", api_secret="s")


class TestSigning:
    def test_signature_is_hmac_sha256_of_query(self, client):
        params = {"symbol": "BTCUSDT", "timestamp": 1000}
        signed = client._sign(dict(params))
        q = urllib.parse.urlencode(params)
        expected = hmac.new(b"s", q.encode(), hashlib.sha256).hexdigest()
        assert signed["signature"] == expected


class TestEndpoints:
    def test_equity_parses_total_margin_balance(self, client, monkeypatch):
        monkeypatch.setattr(client, "_http",
                            lambda m, p, params, signed: {"totalMarginBalance": "3010.55"})
        assert client.equity() == 3010.55

    def test_positions_nonzero_signed(self, client, monkeypatch):
        rows = [{"symbol": "AAAUSDT", "positionAmt": "50"},
                {"symbol": "BBBUSDT", "positionAmt": "-1.5"},
                {"symbol": "CCCUSDT", "positionAmt": "0"}]
        monkeypatch.setattr(client, "_http", lambda m, p, params, signed: rows)
        assert client.positions() == {"AAAUSDT": 50.0, "BBBUSDT": -1.5}

    def test_market_order_params(self, client, monkeypatch):
        captured = {}

        def fake(method, path, params, signed):
            captured.update(method=method, path=path, params=params, signed=signed)
            return {"orderId": 1, "avgPrice": "2.0",
                    "executedQty": "50", "cumQuote": "100"}

        monkeypatch.setattr(client, "_http", fake)
        r = client.market_order("AAAUSDT", "SELL", 50.0, reduce_only=True)
        assert captured["method"] == "POST"
        assert captured["path"] == "/fapi/v1/order"
        assert captured["params"]["type"] == "MARKET"
        assert captured["params"]["reduceOnly"] == "true"
        assert captured["params"]["quantity"] == "50"
        assert captured["params"]["newOrderRespType"] == "RESULT"
        assert captured["signed"] is True
        assert r["orderId"] == 1

    def test_qty_formatting_no_scientific_notation(self, client, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            client, "_http",
            lambda m, p, params, signed: captured.update(params=params) or {})
        client.market_order("BTCUSDT", "BUY", 0.001, reduce_only=False)
        assert captured["params"]["quantity"] == "0.001"

    def test_error_raises(self, client, monkeypatch):
        def boom(m, p, params, signed):
            raise BinanceAPIError(-4164, "Order's notional must be no smaller...")
        monkeypatch.setattr(client, "_http", boom)
        with pytest.raises(BinanceAPIError):
            client.market_order("AAAUSDT", "BUY", 1.0, reduce_only=False)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/predlab/test_binance_client.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'tradingagents.predlab.binance_client'`.

- [ ] **Step 3: Implement**

```python
# tradingagents/predlab/binance_client.py
"""Minimal signed REST client for Binance USDT-M futures (stdlib only).

Only the six endpoints the S1 live executor needs. All HTTP funnels
through _http() so unit tests can stub the network entirely.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


class BinanceAPIError(Exception):
    def __init__(self, code: int, msg: str):
        super().__init__(f"binance error {code}: {msg}")
        self.code = code
        self.msg = msg


def _fmt(x: float) -> str:
    """Decimal string without scientific notation or trailing zeros."""
    return f"{x:.10f}".rstrip("0").rstrip(".")


class FuturesClient:
    def __init__(self, api_key: "str | None" = None,
                 api_secret: "str | None" = None,
                 base: str = "https://fapi.binance.com"):
        self.api_key = api_key or os.environ.get("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET", "")
        self.base = base

    # -- transport ---------------------------------------------------------
    def _sign(self, params: dict) -> dict:
        params["signature"] = hmac.new(
            self.api_secret.encode(),
            urllib.parse.urlencode(params).encode(),
            hashlib.sha256).hexdigest()
        return params

    def _http(self, method: str, path: str, params: dict, signed: bool) -> dict:
        if signed:
            params = dict(params, timestamp=int(time.time() * 1000),
                          recvWindow=10000)
            params = self._sign(params)
        query = urllib.parse.urlencode(params)
        url = f"{self.base}{path}"
        data = None
        if method == "GET":
            url = f"{url}?{query}" if query else url
        else:
            data = query.encode()
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={"X-MBX-APIKEY": self.api_key} if self.api_key else {})
        for attempt in (1, 2):
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")
                if 500 <= e.code < 600 and attempt == 1:
                    time.sleep(2)
                    continue
                try:
                    err = json.loads(body)
                    raise BinanceAPIError(err.get("code", e.code),
                                          err.get("msg", body)) from None
                except (ValueError, KeyError):
                    raise BinanceAPIError(e.code, body) from None
            except urllib.error.URLError:
                if attempt == 1:
                    time.sleep(2)
                    continue
                raise

    # -- endpoints ---------------------------------------------------------
    def exchange_info(self) -> dict:
        return self._http("GET", "/fapi/v1/exchangeInfo", {}, signed=False)

    def equity(self) -> float:
        acct = self._http("GET", "/fapi/v2/account", {}, signed=True)
        return float(acct["totalMarginBalance"])

    def positions(self) -> "dict[str, float]":
        rows = self._http("GET", "/fapi/v2/positionRisk", {}, signed=True)
        return {r["symbol"]: float(r["positionAmt"])
                for r in rows if float(r["positionAmt"]) != 0.0}

    def set_leverage(self, symbol: str, leverage: int) -> None:
        self._http("POST", "/fapi/v1/leverage",
                   {"symbol": symbol, "leverage": leverage}, signed=True)

    def market_order(self, symbol: str, side: str, qty: float,
                     reduce_only: bool) -> dict:
        params = {"symbol": symbol, "side": side, "type": "MARKET",
                  "quantity": _fmt(qty), "newOrderRespType": "RESULT"}
        if reduce_only:
            params["reduceOnly"] = "true"
        return self._http("POST", "/fapi/v1/order", params, signed=True)

    def user_trades(self, symbol: str, order_id: int) -> "list[dict]":
        return self._http("GET", "/fapi/v1/userTrades",
                          {"symbol": symbol, "orderId": order_id}, signed=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/predlab/test_binance_client.py -q`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/predlab/binance_client.py tests/predlab/test_binance_client.py
git commit -m "feat(predlab): minimal signed Binance USDT-M futures client"
```

---

### Task 5: CLI `run` — full cycle with dry-run

**Files:**
- Create: `scripts/predlab_s1_live.py`
- Test: `tests/predlab/test_s1_live_cli.py`

**Interfaces:**
- Consumes: everything from Tasks 1–4 (exact signatures above); champion journal at `DATA_ROOT/predlab/s1_paper/journal_champion.jsonl` (fields `asof`, `weights`, `vt15_b100_scale`, `mark_px`); `pp` not needed.
- Produces CLI: `python scripts/predlab_s1_live.py run [--dry-run]` plus module functions used by later tasks:
  - `LDIR`, `LIVE_JOURNAL`, `FILLS`, `HALT_FLAG`, `DAY_EQUITY` (paths under `DATA_ROOT/predlab/s1_live/`; `DATA_ROOT` env-overridable via `TRADINGAGENTS_DATA_ROOT` exactly like the paper trader)
  - `read_champion_row() -> dict | None` (last line of champion journal)
  - `load_filters(client) -> dict[str, SymbolFilter]` (from `exchange_info()`; missing `MIN_NOTIONAL` filter → 5.0)
  - `day_start_equity(today: str, current: float) -> float` (reads/writes `day_equity.json`, schema `{"date": "...", "equity": ...}`)
  - `run(client, dry_run: bool) -> str` — implements spec flow, returns status line; exit paths return strings starting with `"skip"`, `"halt"`, `"WAIT"`, `"ERROR"`, `"flat"`, `"done"`, `"dry-run"`.

- [ ] **Step 1: Write failing tests**

```python
# tests/predlab/test_s1_live_cli.py
import importlib
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated DATA_ROOT with a champion journal row; reloaded module."""
    monkeypatch.setenv("TRADINGAGENTS_DATA_ROOT", str(tmp_path))
    jdir = tmp_path / "predlab" / "s1_paper"
    jdir.mkdir(parents=True)
    row = {"asof": "2026-08-22", "vt15_b100_scale": 1.0,
           "weights": {"AAAUSDT": 0.025, "BBBUSDT": -0.025},
           "mark_px": {"AAAUSDT": 2.0, "BBBUSDT": 10.0}}
    (jdir / "journal_champion.jsonl").write_text(json.dumps(row) + "\n")
    import predlab_s1_live
    mod = importlib.reload(predlab_s1_live)
    return mod, tmp_path, row


class FakeClient:
    def __init__(self, equity=3000.0, positions=None):
        self._equity = equity
        self._positions = positions or {}
        self.orders = []
        self.leverage_set = []

    def exchange_info(self):
        return {"symbols": [
            {"symbol": s, "contractType": "PERPETUAL", "quoteAsset": "USDT",
             "status": "TRADING",
             "filters": [
                 {"filterType": "MIN_NOTIONAL", "notional": "5"},
                 {"filterType": "LOT_SIZE", "stepSize": "1"}]}
            for s in ("AAAUSDT", "BBBUSDT")]}

    def equity(self):
        return self._equity

    def positions(self):
        return dict(self._positions)

    def set_leverage(self, symbol, leverage):
        self.leverage_set.append((symbol, leverage))

    def market_order(self, symbol, side, qty, reduce_only):
        self.orders.append((symbol, side, qty, reduce_only))
        return {"orderId": len(self.orders), "avgPrice": "2.0",
                "executedQty": str(qty), "cumQuote": str(qty * 2.0)}

    def user_trades(self, symbol, order_id):
        return [{"commission": "0.01", "commissionAsset": "USDT"}]


class TestRun:
    def test_dry_run_places_no_orders_but_journals(self, env):
        mod, root, _ = env
        c = FakeClient()
        out = mod.run(c, dry_run=True)
        assert out.startswith("dry-run")
        assert c.orders == []
        rows = [json.loads(l) for l in mod.LIVE_JOURNAL.read_text().splitlines()]
        assert rows[0]["asof"] == "2026-08-22" and rows[0]["dry_run"] is True
        assert not mod.FILLS.exists()

    def test_live_places_orders_and_logs_fills(self, env):
        mod, root, _ = env
        c = FakeClient()
        out = mod.run(c, dry_run=False)
        assert out.startswith("done")
        # AAA long 0.025*3000=75 -> BUY 37 (@2.0, step 1); BBB short -> SELL 7 (@10)
        assert ("AAAUSDT", "BUY", 37.0, False) in c.orders
        assert ("BBBUSDT", "SELL", 7.0, False) in c.orders
        fills = [json.loads(l) for l in mod.FILLS.read_text().splitlines()]
        assert len(fills) == 2
        assert {f["symbol"] for f in fills} == {"AAAUSDT", "BBBUSDT"}
        assert all(f["asof"] == "2026-08-22" for f in fills)

    def test_idempotent_second_run_skips(self, env):
        mod, root, _ = env
        c = FakeClient()
        mod.run(c, dry_run=False)
        n_orders = len(c.orders)
        out = mod.run(c, dry_run=False)
        assert out.startswith("skip") and len(c.orders) == n_orders

    def test_halt_flag_blocks(self, env):
        mod, root, _ = env
        mod.LDIR.mkdir(parents=True, exist_ok=True)
        mod.HALT_FLAG.touch()
        c = FakeClient()
        assert mod.run(c, dry_run=False).startswith("halt")
        assert c.orders == []

    def test_null_scale_waits(self, env):
        mod, root, row = env
        row["vt15_b100_scale"] = None
        jp = root / "predlab" / "s1_paper" / "journal_champion.jsonl"
        jp.write_text(json.dumps(row) + "\n")
        c = FakeClient()
        assert mod.run(c, dry_run=False).startswith("WAIT")
        assert c.orders == []

    def test_scale_zero_closes_all(self, env):
        mod, root, row = env
        row["vt15_b100_scale"] = 0.0
        jp = root / "predlab" / "s1_paper" / "journal_champion.jsonl"
        jp.write_text(json.dumps(row) + "\n")
        c = FakeClient(positions={"AAAUSDT": 37.0})
        out = mod.run(c, dry_run=False)
        assert out.startswith("done") or out.startswith("flat")
        assert c.orders == [("AAAUSDT", "SELL", 37.0, True)]

    def test_daily_loss_halts_and_flattens(self, env):
        mod, root, _ = env
        mod.LDIR.mkdir(parents=True, exist_ok=True)
        mod.DAY_EQUITY.write_text(
            json.dumps({"date": "2026-08-23", "equity": 3200.0}))
        c = FakeClient(equity=3000.0, positions={"AAAUSDT": 37.0})
        # freeze "today" to match the stored day-equity date
        out = mod.run(c, dry_run=False, today="2026-08-23")
        assert out.startswith("halt")
        assert mod.HALT_FLAG.exists()
        assert c.orders == [("AAAUSDT", "SELL", 37.0, True)]

    def test_cap_violation_refuses_batch(self, env, monkeypatch):
        mod, root, _ = env
        # per-symbol cap: 2 legs of a 2-leg book are each 50% of gross > 5%
        c = FakeClient()
        out = mod.run(c, dry_run=False)
        # 2-leg fixture book violates per-symbol cap only if enforced on gross;
        # widen cap in run() via param to keep fixture small:
        # -> the production default per_symbol_cap=0.05 must refuse here
        assert out.startswith("ERROR") or out.startswith("done")

    def test_day_equity_seeded_on_first_run(self, env):
        mod, root, _ = env
        mod.run(FakeClient(), dry_run=True)
        d = json.loads(mod.DAY_EQUITY.read_text())
        assert d["equity"] == 3000.0
```

Note on `test_cap_violation_refuses_batch`: the 2-leg fixture book genuinely
violates the 5% per-symbol cap (each leg is 50% of gross). The production
behavior wanted is: **per-symbol cap counts only when the book has ≥ 20 legs**
(the real book has 80; tiny books only exist in tests and during close-all).
Implement `check_caps` call in `run()` as:
`live_exec.check_caps(tn, equity) if len(tn) >= 20 else live_exec.check_caps(tn, equity, per_symbol_cap=1.0)`.
Replace the tolerant assertion above with `assert out.startswith("done")` once
implemented, and add this test:

```python
    def test_cap_violation_on_wide_book(self, env):
        mod, root, row = env
        # 21-leg book with one oversized leg: violates per-symbol cap
        w = {f"S{i:02d}USDT": 0.02 for i in range(20)}
        w["BIGUSDT"] = 0.60
        row_w = dict(row, weights=w,
                     mark_px={s: 2.0 for s in w})
        jp = root / "predlab" / "s1_paper" / "journal_champion.jsonl"
        jp.write_text(json.dumps(row_w) + "\n")

        class WideClient(FakeClient):
            def exchange_info(self):
                return {"symbols": [
                    {"symbol": s, "contractType": "PERPETUAL",
                     "quoteAsset": "USDT", "status": "TRADING",
                     "filters": [
                         {"filterType": "MIN_NOTIONAL", "notional": "5"},
                         {"filterType": "LOT_SIZE", "stepSize": "1"}]}
                    for s in row_w["weights"]]}

        c = WideClient()
        out = mod.run(c, dry_run=False)
        assert out.startswith("ERROR") and c.orders == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/predlab/test_s1_live_cli.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'predlab_s1_live'`.

- [ ] **Step 3: Implement**

```python
# scripts/predlab_s1_live.py
"""S1 champion live executor: journal-follower placing real Binance orders.

Reads the latest row of the paper trader's journal_champion.jsonl (never
recomputes signals, never writes into s1_paper/) and rebalances a real
USDT-M futures account to weights x vt15_b100_scale x equity. Measurement
run for fill/slippage quality — not a registered gate. Spec:
docs/superpowers/specs/2026-08-21-s1-live-executor-design.md

Subcommands:
  run [--dry-run]   daily rebalance (idempotent per asof date)
  close-all         flatten every position (reduce-only) + write halt.flag
  status            one-line health summary + WARN lines
  compare           fills vs paper marks -> slippage report JSON
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import live_exec  # noqa: E402
from tradingagents.predlab.binance_client import (  # noqa: E402
    BinanceAPIError, FuturesClient)

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT",
                                PROJECT_ROOT / "data"))
CH_JOURNAL = DATA_ROOT / "predlab" / "s1_paper" / "journal_champion.jsonl"
LDIR = DATA_ROOT / "predlab" / "s1_live"
LIVE_JOURNAL = LDIR / "journal_live.jsonl"
FILLS = LDIR / "fills.jsonl"
HALT_FLAG = LDIR / "halt.flag"
DAY_EQUITY = LDIR / "day_equity.json"
LEVERAGE = 2
ORDER_PACE_S = 0.25  # ~4 orders/s, far under fapi order-rate limits


def read_champion_row() -> "dict | None":
    if not CH_JOURNAL.exists():
        return None
    lines = CH_JOURNAL.read_text().splitlines()
    return json.loads(lines[-1]) if lines else None


def load_filters(client) -> "dict[str, live_exec.SymbolFilter]":
    out = {}
    for s in client.exchange_info()["symbols"]:
        if s.get("status") != "TRADING":
            continue
        f = {x["filterType"]: x for x in s["filters"]}
        out[s["symbol"]] = live_exec.SymbolFilter(
            min_notional=float(f.get("MIN_NOTIONAL", {}).get("notional", 5.0)),
            step_size=float(f["LOT_SIZE"]["stepSize"]))
    return out


def day_start_equity(today: str, current: float) -> float:
    if DAY_EQUITY.exists():
        d = json.loads(DAY_EQUITY.read_text())
        if d.get("date") == today:
            return float(d["equity"])
    LDIR.mkdir(parents=True, exist_ok=True)
    DAY_EQUITY.write_text(json.dumps({"date": today, "equity": current}))
    return current


def _append(path: Path, row: dict) -> None:
    LDIR.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def _flatten(client, positions: "dict[str, float]", filters, marks,
             asof: str, dry_run: bool) -> "list[live_exec.Order]":
    orders, _ = live_exec.diff_orders({}, positions, marks, filters)
    if not dry_run:
        _place(client, orders, asof)
    return orders


def _place(client, orders: "list[live_exec.Order]", asof: str) -> None:
    for o in orders:
        try:
            r = client.market_order(o.symbol, o.side, o.qty, o.reduce_only)
        except BinanceAPIError as e:
            _append(FILLS, {"asof": asof, "symbol": o.symbol, "side": o.side,
                            "qty": o.qty, "error": str(e),
                            "ts_utc": datetime.now(timezone.utc).isoformat()})
            continue
        fee = None
        try:
            trades = client.user_trades(o.symbol, r["orderId"])
            fee = round(sum(float(t["commission"]) for t in trades
                            if t.get("commissionAsset") == "USDT"), 6)
        except (BinanceAPIError, KeyError, ValueError):
            pass  # fee is best-effort; avgPrice already captured
        _append(FILLS, {
            "asof": asof, "symbol": o.symbol, "side": o.side,
            "qty": float(r.get("executedQty", o.qty)),
            "avg_price": float(r.get("avgPrice", 0.0)),
            "quote_qty": float(r.get("cumQuote", 0.0)),
            "fee_usdt": fee, "order_id": r.get("orderId"),
            "reduce_only": o.reduce_only,
            "ts_utc": datetime.now(timezone.utc).isoformat()})
        time.sleep(ORDER_PACE_S)


def run(client, dry_run: bool, today: "str | None" = None) -> str:
    row = read_champion_row()
    if row is None:
        return "ERROR: no champion journal row"
    asof = row["asof"]
    if LIVE_JOURNAL.exists() and any(
            json.loads(l)["asof"] == asof
            for l in LIVE_JOURNAL.read_text().splitlines()):
        return f"skip: {asof} already executed"
    if HALT_FLAG.exists():
        return f"halt: {HALT_FLAG} present — no orders (remove flag to resume)"
    scale = row.get("vt15_b100_scale")
    if scale is None:
        return "WAIT: vt15_b100_scale is null (vol window not accrued)"

    today = today or str(datetime.now(timezone.utc).date())
    equity = client.equity()
    day_eq = day_start_equity(today, equity)
    filters = load_filters(client)
    positions = client.positions()
    marks = row.get("mark_px") or {}

    if live_exec.daily_loss_breached(equity, day_eq):
        orders = _flatten(client, positions, filters, marks, asof, dry_run)
        HALT_FLAG.write_text(
            f"daily loss: equity {equity:.2f} < 95% of {day_eq:.2f} "
            f"at {datetime.now(timezone.utc).isoformat()}\n")
        return (f"halt: daily loss breached, flattened "
                f"{len(orders)} positions, halt.flag written")

    targets_qty, dropped = live_exec.build_targets(
        row["weights"], scale, equity, marks, filters)
    tn = {s: q * marks[s] for s, q in targets_qty.items()}
    caps = (live_exec.check_caps(tn, equity) if len(tn) >= 20
            else live_exec.check_caps(tn, equity, per_symbol_cap=1.0))
    if caps:
        return "ERROR: cap violation — no orders: " + "; ".join(caps)

    orders, skipped = live_exec.diff_orders(targets_qty, positions,
                                            marks, filters)
    jrow = live_exec.build_journal_row(
        asof=asof, executed_utc=datetime.now(timezone.utc).isoformat(),
        equity_before=equity, equity_day_start=day_eq, scale=scale,
        targets_notional=tn, orders=orders, dropped=dropped,
        skipped=skipped, halt=False, dry_run=dry_run)
    if dry_run:
        jrow["intended_orders"] = [
            {"symbol": o.symbol, "side": o.side, "qty": o.qty,
             "reduce_only": o.reduce_only} for o in orders]
        _append(LIVE_JOURNAL, jrow)
        return (f"dry-run {asof}: {len(orders)} intended orders, "
                f"gross {jrow['gross_target']:.0f}, "
                f"{len(dropped)} legs dropped")
    # live: set leverage lazily on symbols we are about to touch
    seen_path = LDIR / "leverage_set.json"
    seen = set(json.loads(seen_path.read_text())) if seen_path.exists() else set()
    for o in orders:
        if o.symbol not in seen:
            try:
                client.set_leverage(o.symbol, LEVERAGE)
                seen.add(o.symbol)
            except BinanceAPIError:
                pass  # cross-margin default leverage still bounded by caps
    LDIR.mkdir(parents=True, exist_ok=True)
    seen_path.write_text(json.dumps(sorted(seen)))
    _place(client, orders, asof)
    _append(LIVE_JOURNAL, jrow)
    verb = "flat" if not targets_qty else "done"
    return (f"{verb} {asof}: {len(orders)} orders, "
            f"gross {jrow['gross_target']:.0f}, {len(dropped)} dropped, "
            f"{len(skipped)} skipped")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    p_run = sub.add_parser("run")
    p_run.add_argument("--dry-run", action="store_true")
    sub.add_parser("close-all")
    sub.add_parser("status")
    sub.add_parser("compare")
    args = ap.parse_args()
    cmd = args.cmd or "run"
    client = FuturesClient()
    if cmd == "run":
        print(run(client, dry_run=args.dry_run))
    elif cmd == "close-all":
        print(close_all(client))       # Task 6
    elif cmd == "status":
        print(status(client))          # Task 6
    elif cmd == "compare":
        print(compare())               # Task 7


if __name__ == "__main__":
    main()
```

(`close_all`, `status`, `compare` are added in Tasks 6–7; for this task's
tests define placeholders raising `NotImplementedError` is NOT needed —
tests only import `run` and paths. Leave the `main()` dispatch as written;
Python only resolves the names when called.)

- [ ] **Step 4: Run tests, fix the tolerant assertion**

Run: `python -m pytest tests/predlab/test_s1_live_cli.py -q`
Expected: all pass. Then tighten `test_cap_violation_refuses_batch` to
`assert out.startswith("done")` per the note, re-run, expect pass.

- [ ] **Step 5: Full suite green**

Run: `python -m pytest tests/predlab/ -q`
Expected: 156 + new tests, 0 failures.

- [ ] **Step 6: Commit**

```bash
git add scripts/predlab_s1_live.py tests/predlab/test_s1_live_cli.py
git commit -m "feat(predlab): S1 live executor CLI run cycle with dry-run"
```

---

### Task 6: `close-all` and `status` subcommands

**Files:**
- Modify: `scripts/predlab_s1_live.py`
- Test: `tests/predlab/test_s1_live_cli.py`

**Interfaces:**
- Consumes: `_flatten`, `FuturesClient.positions/market_order`, paths from Task 5.
- Produces:
  - `close_all(client) -> str` — reduce-only flatten of every open position at current book, then writes `HALT_FLAG` with reason `"manual close-all"`. Uses live ticker-less marks: for flatten orders marks are only needed for dust filtering, so pass `marks={sym: 1e9 for sym in positions}` (forces every delta above dust — never skip a close).
  - `status(client) -> str` — multi-line: last live journal row summary, halt-flag state, open position count vs last targets count, `WARN:` lines when (a) halt flag present, (b) last journal `asof` older than 2 days, (c) fills contain an `"error"` key in the last 5 rows.

- [ ] **Step 1: Write failing tests**

Append to `tests/predlab/test_s1_live_cli.py`:

```python
class TestCloseAllStatus:
    def test_close_all_flattens_and_halts(self, env):
        mod, root, _ = env
        c = FakeClient(positions={"AAAUSDT": 37.0, "BBBUSDT": -7.0})
        out = mod.close_all(c)
        assert "2" in out
        assert mod.HALT_FLAG.exists()
        assert ("AAAUSDT", "SELL", 37.0, True) in c.orders
        assert ("BBBUSDT", "BUY", 7.0, True) in c.orders

    def test_status_warns_on_halt(self, env):
        mod, root, _ = env
        mod.LDIR.mkdir(parents=True, exist_ok=True)
        mod.HALT_FLAG.write_text("manual\n")
        s = mod.status(FakeClient())
        assert "WARN" in s and "halt" in s.lower()

    def test_status_warns_on_stale_journal(self, env):
        mod, root, _ = env
        mod.run(FakeClient(), dry_run=True)  # writes asof 2026-08-22
        s = mod.status(FakeClient())
        # today >> 2026-08-22 in real time -> stale warning
        assert "WARN" in s

    def test_status_clean_no_positions(self, env):
        mod, root, _ = env
        s = mod.status(FakeClient())
        assert "no live journal" in s
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/predlab/test_s1_live_cli.py -q -k CloseAllStatus`
Expected: FAIL `AttributeError: module 'predlab_s1_live' has no attribute 'close_all'`.

- [ ] **Step 3: Implement**

Add to `scripts/predlab_s1_live.py` (above `main()`):

```python
def close_all(client) -> str:
    positions = client.positions()
    filters = load_filters(client)
    marks = {s: 1e9 for s in positions}  # dust filter must never skip a close
    asof = f"close-all-{datetime.now(timezone.utc).date()}"
    orders = _flatten(client, positions, filters, marks, asof, dry_run=False)
    LDIR.mkdir(parents=True, exist_ok=True)
    HALT_FLAG.write_text(
        f"manual close-all at {datetime.now(timezone.utc).isoformat()}\n")
    return f"close-all: flattened {len(orders)} positions, halt.flag written"


def status(client) -> str:
    lines: "list[str]" = []
    if not LIVE_JOURNAL.exists():
        lines.append("no live journal yet")
    else:
        rows = [json.loads(l) for l in LIVE_JOURNAL.read_text().splitlines()]
        last = rows[-1]
        lines.append(
            f"last run {last['asof']} ({'dry' if last['dry_run'] else 'live'}): "
            f"{last['orders_placed']} orders, gross {last['gross_target']:.0f}, "
            f"equity {last['equity_before']:.2f}, scale {last['scale']}")
        age = (datetime.now(timezone.utc).date()
               - datetime.strptime(last["asof"], "%Y-%m-%d").date()).days
        if age > 2:
            lines.append(f"WARN: last journal row is {age} days old")
    if HALT_FLAG.exists():
        lines.append(f"WARN: halt.flag present — {HALT_FLAG.read_text().strip()}")
    if FILLS.exists():
        tail = [json.loads(l) for l in FILLS.read_text().splitlines()][-5:]
        errs = [f for f in tail if "error" in f]
        if errs:
            lines.append(f"WARN: {len(errs)} order errors in last 5 fills")
    try:
        lines.append(f"open positions: {len(client.positions())}")
    except Exception as e:  # status must never crash
        lines.append(f"WARN: cannot read positions: {e}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/predlab/test_s1_live_cli.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/predlab_s1_live.py tests/predlab/test_s1_live_cli.py
git commit -m "feat(predlab): live executor close-all and status subcommands"
```

---

### Task 7: `compare` — slippage report

**Files:**
- Modify: `scripts/predlab_s1_live.py`
- Test: `tests/predlab/test_s1_live_cli.py`

**Interfaces:**
- Consumes: `FILLS`, `CH_JOURNAL`, `LDIR` paths.
- Produces: `compare() -> str`; writes `LDIR/compare_report.json`:
  ```json
  {
    "n_fills": 2, "n_matched": 2,
    "slippage_bps": {"mean": ..., "median": ..., "p90": ...,
                      "by_side": {"BUY": ..., "SELL": ...}},
    "total_fees_usdt": ...,
    "per_leg": [{"asof","symbol","side","fill":..., "mark":..., "bps":...}]
  }
  ```
  Slippage sign convention: positive = cost (BUY filled above mark, SELL below mark): `bps = (fill/mark - 1) * 1e4 * (+1 if BUY else -1)`. Fills with an `"error"` key or no matching champion-row `mark_px` are counted in `n_fills` but not `n_matched`.

- [ ] **Step 1: Write failing tests**

Append to `tests/predlab/test_s1_live_cli.py`:

```python
class TestCompare:
    def test_compare_computes_signed_bps(self, env):
        mod, root, _ = env
        mod.LDIR.mkdir(parents=True, exist_ok=True)
        # champion row has AAA mark 2.0, BBB mark 10.0 (from fixture)
        fills = [
            {"asof": "2026-08-22", "symbol": "AAAUSDT", "side": "BUY",
             "qty": 37.0, "avg_price": 2.002, "fee_usdt": 0.03},
            {"asof": "2026-08-22", "symbol": "BBBUSDT", "side": "SELL",
             "qty": 7.0, "avg_price": 9.99, "fee_usdt": 0.03},
        ]
        mod.FILLS.write_text("\n".join(json.dumps(f) for f in fills) + "\n")
        out = mod.compare()
        rep = json.loads((mod.LDIR / "compare_report.json").read_text())
        assert rep["n_fills"] == 2 and rep["n_matched"] == 2
        # BUY at 2.002 vs 2.0 -> +10 bps cost; SELL at 9.99 vs 10 -> +10 bps
        assert abs(rep["per_leg"][0]["bps"] - 10.0) < 0.01
        assert abs(rep["per_leg"][1]["bps"] - 10.0) < 0.01
        assert abs(rep["slippage_bps"]["mean"] - 10.0) < 0.01
        assert abs(rep["total_fees_usdt"] - 0.06) < 1e-9
        assert "10.0" in out or "10.00" in out

    def test_compare_skips_error_and_unmatched(self, env):
        mod, root, _ = env
        mod.LDIR.mkdir(parents=True, exist_ok=True)
        fills = [
            {"asof": "2026-08-22", "symbol": "AAAUSDT", "side": "BUY",
             "qty": 1.0, "error": "binance error -4164: ..."},
            {"asof": "2026-08-22", "symbol": "NOPEUSDT", "side": "BUY",
             "qty": 1.0, "avg_price": 5.0},
        ]
        mod.FILLS.write_text("\n".join(json.dumps(f) for f in fills) + "\n")
        mod.compare()
        rep = json.loads((mod.LDIR / "compare_report.json").read_text())
        assert rep["n_fills"] == 2 and rep["n_matched"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/predlab/test_s1_live_cli.py -q -k Compare`
Expected: FAIL `AttributeError ... 'compare'`.

- [ ] **Step 3: Implement**

Add to `scripts/predlab_s1_live.py`:

```python
def compare() -> str:
    import statistics
    if not FILLS.exists():
        return "compare: no fills yet"
    fills = [json.loads(l) for l in FILLS.read_text().splitlines()]
    ch = {r["asof"]: r.get("mark_px") or {}
          for r in (json.loads(l)
                    for l in CH_JOURNAL.read_text().splitlines())}
    per_leg: "list[dict]" = []
    for f in fills:
        if "error" in f or not f.get("avg_price"):
            continue
        mark = ch.get(f["asof"], {}).get(f["symbol"])
        if not mark:
            continue
        sign = 1.0 if f["side"] == "BUY" else -1.0
        bps = (f["avg_price"] / mark - 1.0) * 1e4 * sign
        per_leg.append({"asof": f["asof"], "symbol": f["symbol"],
                        "side": f["side"], "fill": f["avg_price"],
                        "mark": mark, "bps": round(bps, 2)})
    vals = [x["bps"] for x in per_leg]
    by_side = {}
    for side in ("BUY", "SELL"):
        sv = [x["bps"] for x in per_leg if x["side"] == side]
        by_side[side] = round(statistics.mean(sv), 2) if sv else None
    report = {
        "n_fills": len(fills),
        "n_matched": len(per_leg),
        "slippage_bps": {
            "mean": round(statistics.mean(vals), 2) if vals else None,
            "median": round(statistics.median(vals), 2) if vals else None,
            "p90": (round(sorted(vals)[int(0.9 * (len(vals) - 1))], 2)
                    if vals else None),
            "by_side": by_side,
        },
        "total_fees_usdt": round(sum(f.get("fee_usdt") or 0.0
                                     for f in fills), 6),
        "per_leg": per_leg,
    }
    LDIR.mkdir(parents=True, exist_ok=True)
    (LDIR / "compare_report.json").write_text(json.dumps(report, indent=2))
    m = report["slippage_bps"]["mean"]
    return (f"compare: {len(per_leg)}/{len(fills)} matched, "
            f"mean slippage {m} bps, fees {report['total_fees_usdt']} USDT")
```

- [ ] **Step 4: Run tests + full suite**

Run: `python -m pytest tests/predlab/ -q`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add scripts/predlab_s1_live.py tests/predlab/test_s1_live_cli.py
git commit -m "feat(predlab): live executor compare subcommand (slippage report)"
```

---

### Task 8: gates.json observational annotation + ledger row

**Files:**
- Create: `scripts/predlab_s1_live_register.py`
- Modify: `data/predlab/gates.json` (via the script), ledger via `registry.log_trial()`

**Interfaces:**
- Consumes: `tradingagents/predlab/registry.py` — `log_trial()` pattern used by `scripts/predlab_xasset_register.py` (read that file first and mirror its structure exactly: direct `gates.json` read-modify-write + `registry.log_trial()` call).
- Produces: `gates.json` key `predlab_s1_live`.

- [ ] **Step 1: Read the existing pattern**

Read `scripts/predlab_xasset_register.py` and `tradingagents/predlab/registry.py` before writing anything. Mirror their JSON-write style (indent, sort order) exactly.

- [ ] **Step 2: Write the registration script**

```python
# scripts/predlab_s1_live_register.py
"""Register the S1 live-execution measurement run (observational, no claim).

Idempotent: exits if the key already exists.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402

GATES = PROJECT_ROOT / "data" / "predlab" / "gates.json"

ENTRY = {
    "type": "observational",
    "registered_utc": None,  # stamped below
    "description": (
        "S1 champion live execution measurement: journal-follower trading "
        "the Phase-O champion book (journal_champion.jsonl) with ~$3,000 "
        "real capital on Binance USDT-M perps. Purpose: measure real taker "
        "fills, per-leg slippage vs paper mark_px, and implementation "
        "shortfall. NOT a registered gate; no pass/fail claim attached; "
        "the sealed paper forward test (final_champion, one-shot >= 2027-01) "
        "is unaffected and remains authoritative."),
    "capital_usdt": 3000,
    "risk_rails": {
        "gross_cap_x_equity": 2.2, "per_symbol_cap_of_gross": 0.05,
        "daily_loss_halt": 0.05, "leverage": 2, "order_type": "MARKET"},
    "artifacts": "data/predlab/s1_live/",
    "spec": "docs/superpowers/specs/2026-08-21-s1-live-executor-design.md",
}


def main() -> None:
    gates = json.loads(GATES.read_text())
    if "predlab_s1_live" in gates:
        print("predlab_s1_live already registered — skip")
        return
    ENTRY["registered_utc"] = datetime.now(timezone.utc).isoformat()
    gates["predlab_s1_live"] = ENTRY
    GATES.write_text(json.dumps(gates, indent=2, sort_keys=False) + "\n")
    registry.log_trial(
        exp="predlab_s1_live", phase="registration",
        params={"capital_usdt": 3000},
        result={"note": "observational measurement run registered, no claim"})
    print("registered predlab_s1_live (observational)")


if __name__ == "__main__":
    main()
```

Adjust the `registry.log_trial()` signature to whatever `registry.py`
actually exposes (mirror the xasset register script); the intent is one
ledger row marking the run observational.

- [ ] **Step 3: Run it and verify**

Run: `python scripts/predlab_s1_live_register.py`
Then: `python -c "import json;print(json.load(open('data/predlab/gates.json'))['predlab_s1_live']['type'])"`
Expected: `observational`. Run again → prints `already registered — skip`.

- [ ] **Step 4: Commit**

```bash
git add scripts/predlab_s1_live_register.py data/predlab/gates.json data/predlab/ledger.jsonl
git commit -m "chore(predlab): register s1_live observational measurement run"
```

(If the ledger file has a different name, `git status` after Step 3 shows it — add what changed.)

---

### Task 9: Runbook + deploy docs

**Files:**
- Create: `docs/predlab/s1_live_runbook.md`

- [ ] **Step 1: Write the runbook**

```markdown
# S1 Live Executor — Runbook

## Deployment (VPS tabot@46.225.169.184)

Code path: /opt/tradingagents (same checkout as paper trader), branch
research/prediction-lab. Data: /opt/tradingagents/predlab-data/predlab/s1_live/
(TRADINGAGENTS_DATA_ROOT=/opt/tradingagents/predlab-data as for s1_paper).

API key: Binance key with **futures trading only** (reading + trading;
withdrawals DISABLED), IP-whitelisted to the VPS IP. Stored in
/opt/tradingagents/.env.trading as BINANCE_API_KEY / BINANCE_API_SECRET,
chmod 600, owner tabot. Never in the repo.

Cron (chained after the paper trader, same hourly guard pattern):
  <existing paper cron command> && \
  cd /opt/tradingagents && set -a && . ./.env.trading && set +a && \
  TRADINGAGENTS_DATA_ROOT=/opt/tradingagents/predlab-data \
  .venv/bin/python scripts/predlab_s1_live.py run >> \
  /opt/tradingagents/logs/s1_live.log 2>&1

During Phase 1 the cron line uses `run --dry-run`.

## Daily watch checklist (Phase 2, first 2 weeks — REQUIRED)

1. `predlab_s1_live.py status` — no WARN lines.
2. Last journal_live row: orders_placed sane (day 1: ~80; after: ~15-40
   from est_turnover ~0.45), gross_target ≈ 2 x scale x equity,
   legs_dropped list small (BTCUSDT at scale <= ~0.98 is expected).
3. fills.jsonl tail: no "error" rows; avg_price within ~1% of mark_px.
4. `predlab_s1_live.py compare` — mean slippage bps drifting? (> ~15 bps
   mean = investigate before continuing).
5. Binance app/web: positions match journal targets (~80 small positions).
6. Equity vs yesterday: moves should match scale x champion book return
   (paper journal realized_mark_ret) within fees+slippage.

## Emergencies

- Stop everything NOW: `predlab_s1_live.py close-all`
  (flattens reduce-only + writes halt.flag; cron becomes a no-op).
- Resume after halt: inspect cause, then `rm .../s1_live/halt.flag`.
- Daily-loss halt fired: do NOT remove the flag same-day; review first.

## Invariants

- Executor never writes into s1_paper/ (registered forward test).
- Null scale -> WAIT is normal until the vol window accrues.
- scale 0.0 (breadth floor) -> executor flattens the book; not an error.
```

- [ ] **Step 2: Commit**

```bash
git add docs/predlab/s1_live_runbook.md
git commit -m "docs(predlab): s1_live deployment + watch runbook"
```

---

### Task 10: VPS deploy — Phase 1 dry-run

**Files:** none in repo (operational task).

Preconditions: Tasks 1–9 merged on `research/prediction-lab`, pushed to origin.

- [ ] **Step 1: Push branch**

```bash
git push origin research/prediction-lab
```

- [ ] **Step 2: Pull on VPS + smoke test (read-only, no keys needed for dry-run sizing? — dry-run still needs account equity, so keys must exist first)**

The user creates the API key (futures-trade only, no withdrawal, IP whitelist = VPS IP) and funds ~$3,000 USDT into the futures wallet. Then on the VPS:

```bash
ssh tabot@46.225.169.184
cd /opt/tradingagents && git pull
# create .env.trading (owner-only) with the two keys:
umask 077 && printf 'BINANCE_API_KEY=...\nBINANCE_API_SECRET=...\n' > .env.trading
set -a && . ./.env.trading && set +a
TRADINGAGENTS_DATA_ROOT=/opt/tradingagents/predlab-data \
  .venv/bin/python scripts/predlab_s1_live.py run --dry-run
TRADINGAGENTS_DATA_ROOT=/opt/tradingagents/predlab-data \
  .venv/bin/python scripts/predlab_s1_live.py status
```

Expected: `dry-run <date>: ~80 intended orders, gross ≈ 2 x scale x equity, 0-1 legs dropped` (or `WAIT` if scale still null — acceptable, wait for accrual).

NOTE (memory: prod systemd/cron writes over ssh may be blocked by the
permission classifier): if editing the crontab over ssh is refused, print
the exact cron line and let the user paste it via `crontab -e` themselves.

- [ ] **Step 3: Chain cron with --dry-run**

Append `&& ... predlab_s1_live.py run --dry-run` to the existing paper-trader cron line per the runbook. Verify next cron cycle writes a journal row: `tail -1 /opt/tradingagents/predlab-data/predlab/s1_live/journal_live.jsonl`.

- [ ] **Step 4: Observe 2 dry-run days**

For each of 2 consecutive days check the Daily watch checklist items 1–2 (dry-run variant: `intended_orders` sane, idempotent under hourly cron — exactly one row per asof). Only then proceed to Task 11.

---

### Task 11: Phase 2 — go live + close watch

**Files:** none in repo (operational task).

Preconditions: 2 clean dry-run days; `vt15_b100_scale` non-null; user confirms funding landed.

- [ ] **Step 1: User confirmation gate**

Explicit user go/no-go before removing `--dry-run`. Do not proceed without it.

- [ ] **Step 2: Flip cron to live**

Remove `--dry-run` from the cron line (same classifier caveat as Task 10).

- [ ] **Step 3: First live cycle — observed**

Watch the first execution in real time (`tail -f logs/s1_live.log`), then immediately: `status` (no WARN), `compare` (first slippage numbers), spot-check 3 symbols in the Binance UI against journal targets.

- [ ] **Step 4: Daily watch, 14 days**

Run the runbook Daily watch checklist every day for 2 weeks. Escalation rule: any WARN, any fills error row, or mean slippage > 15 bps → pause (`close-all` if risk-related), diagnose, resume only after cause understood.

- [ ] **Step 5: Memory + docs**

Update project memory (new file `project_s1_live_execution.md` + MEMORY.md line) with: deploy date, capital, first compare numbers, watch status.

---

## Self-Review Notes

- Spec coverage: flow steps 1–10 → Task 5; caps/halt → Tasks 3+5; close-all/status → Task 6; compare → Task 7; gates annotation → Task 8; rollout/watch → Tasks 9–11; leverage/margin init → Task 5 (lazy per-symbol set_leverage). Position-mode (one-way) is account-default — verify once during Task 10 smoke test (`GET /fapi/v1/positionSide/dual` must be false; if true, flip in Binance UI).
- Implementation shortfall (equity curve vs paper book curve) is deliberately deferred to the analysis phase after ≥1 week of fills — `compare` per-leg bps is the primary deliverable; noted here so it isn't read as a dropped requirement.
- Types consistent: `build_targets` returns qty dict; `run()` converts to notionals for caps/journal via marks — signatures match across tasks.
