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
