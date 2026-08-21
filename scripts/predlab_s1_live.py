"""S1 champion live executor: journal-follower placing real Binance orders.

Reads the latest row of the paper trader's journal_champion.jsonl (never
recomputes signals, never writes into s1_paper/) and rebalances a real
USDT-M futures account to weights x vt15_b100_scale x equity. Measurement
run for fill/slippage quality — not a registered gate. Spec:
docs/superpowers/specs/2026-08-21-s1-live-executor-design.md

Subcommands:
  run [--dry-run]      daily rebalance (idempotent per asof date)
  close-all            flatten every position (reduce-only) + write halt.flag
  status               one-line health summary + WARN lines
  compare              fills vs paper marks -> slippage report JSON

Flags:
  --testnet            use testnet Binance + testnet data paths (Phase 1b rehearsal)
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
LEVERAGE = 4
# Champion book gross is 2.0x; vt15_b100_scale can reach ~2.0 -> gross target
# up to 4x equity. Gross cap is 2.2x and leverage 4 means margin = gross/4,
# so an unclamped scale can refuse the whole batch (cap violation) or exceed
# available margin. Clamp the *executed* scale; the raw overlay scale is
# still recorded in the journal (scale_raw) for the record.
SCALE_CLAMP = 1.1
ORDER_PACE_S = 0.25  # ~4 orders/s, far under fapi order-rate limits
TESTNET_BASE = "https://testnet.binancefuture.com"


def _use_testnet() -> None:
    """Rebind journal/flag paths to the testnet data dir (Phase 1b rehearsal)."""
    global LDIR, LIVE_JOURNAL, FILLS, HALT_FLAG, DAY_EQUITY
    LDIR = DATA_ROOT / "predlab" / "s1_testnet"
    LIVE_JOURNAL = LDIR / "journal_live.jsonl"
    FILLS = LDIR / "fills.jsonl"
    HALT_FLAG = LDIR / "halt.flag"
    DAY_EQUITY = LDIR / "day_equity.json"


def make_client(testnet: bool) -> FuturesClient:
    if testnet:
        return FuturesClient(
            api_key=os.environ.get("BINANCE_TESTNET_API_KEY"),
            api_secret=os.environ.get("BINANCE_TESTNET_API_SECRET"),
            base=TESTNET_BASE)
    return FuturesClient()


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
        except Exception:
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


def _asof_already_executed(asof: str) -> bool:
    """True if `asof` has a row in journal_live.jsonl. Skips any line that
    fails to parse (a torn trailing line from a killed process must not
    crash the hourly idempotency scan — M1)."""
    if not LIVE_JOURNAL.exists():
        return False
    for l in LIVE_JOURNAL.read_text().splitlines():
        try:
            parsed = json.loads(l)
        except (json.JSONDecodeError, ValueError):
            continue
        if parsed.get("asof") == asof:
            return True
    return False


def run(client, dry_run: bool, today: "str | None" = None) -> str:
    row = read_champion_row()
    if row is None:
        return "ERROR: no champion journal row"
    asof = row["asof"]

    # Halt flag is checked first, before any API call, so a halted account
    # costs zero network traffic per wake.
    if HALT_FLAG.exists():
        return f"halt: {HALT_FLAG} present — no orders (remove flag to resume)"

    # Daily-loss check runs on EVERY wake — including an hourly wake whose
    # asof was already executed earlier in the day — because it is the only
    # place equity is read. Checking it after the idempotency skip (the old
    # order) meant the breach could never fire on any wake but the first of
    # the day, since every later wake short-circuited on "already executed"
    # before equity was ever read (I1).
    today = today or str(datetime.now(timezone.utc).date())
    equity = client.equity()
    day_eq = day_start_equity(today, equity)

    if live_exec.daily_loss_breached(equity, day_eq):
        filters = load_filters(client)
        positions = client.positions()
        marks = row.get("mark_px") or {}
        orders = _flatten(client, positions, filters, marks, asof, dry_run)
        HALT_FLAG.write_text(
            f"daily loss: equity {equity:.2f} < 95% of {day_eq:.2f} "
            f"at {datetime.now(timezone.utc).isoformat()}\n")
        return (f"halt: daily loss breached, flattened "
                f"{len(orders)} positions, halt.flag written")

    if _asof_already_executed(asof):
        return f"skip: {asof} already executed"

    scale = row.get("vt15_b100_scale")
    if scale is None:
        return "WAIT: vt15_b100_scale is null (vol window not accrued)"

    weights = row.get("weights") or {}
    marks = row.get("mark_px") or {}
    if weights and not marks:
        # Champion row has a live book but no marks this wake (paper-trader
        # data gap) -- retry on a later wake/next day rather than journaling
        # a false "flat" day (I2).
        return "WAIT: champion row has no marks"

    # Champion gross is 2.0x; scale can reach ~2.0 -> up to 4x equity gross.
    # Clamp the *executed* scale so the batch never refuses on cap/margin;
    # the raw (unclamped) overlay scale is still recorded (scale_raw) so a
    # capped live run is legible as a capped replica, not full-scale (C2).
    scale_executed = min(scale, SCALE_CLAMP)

    filters = load_filters(client)
    positions = client.positions()

    targets_qty, dropped = live_exec.build_targets(
        weights, scale_executed, equity, marks, filters)
    tn = {s: q * marks[s] for s, q in targets_qty.items()}
    caps = (live_exec.check_caps(tn, equity) if len(tn) >= 20
            else live_exec.check_caps(tn, equity, per_symbol_cap=1.0))
    if caps:
        return "ERROR: cap violation — no orders: " + "; ".join(caps)

    orders, skipped = live_exec.diff_orders(targets_qty, positions,
                                            marks, filters)
    jrow = live_exec.build_journal_row(
        asof=asof, executed_utc=datetime.now(timezone.utc).isoformat(),
        equity_before=equity, equity_day_start=day_eq, scale=scale_executed,
        targets_notional=tn, orders=orders, dropped=dropped,
        skipped=skipped, halt=False, dry_run=dry_run, scale_raw=scale)
    if dry_run:
        jrow["intended_orders"] = [
            {"symbol": o.symbol, "side": o.side, "qty": o.qty,
             "reduce_only": o.reduce_only} for o in orders]
        _append(LIVE_JOURNAL, jrow)
        return (f"dry-run {asof}: {len(orders)} intended orders, "
                f"gross {jrow['gross_target']:.0f}, "
                f"{len(dropped)} legs dropped")
    if client.position_mode():
        # One-way mode is assumed throughout diff_orders' reduceOnly
        # semantics; hedge mode must be caught before any order is placed
        # (M2).
        return "ERROR: account in hedge mode — set one-way position mode"
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


def close_all(client) -> str:
    # halt.flag is the FIRST statement (I3): even if positions()/load_filters()
    # itself raises (network down mid-emergency-stop), the account must
    # already be flagged halted before any further API call is attempted.
    LDIR.mkdir(parents=True, exist_ok=True)
    HALT_FLAG.write_text(
        f"manual close-all at {datetime.now(timezone.utc).isoformat()}\n")
    try:
        positions = client.positions()
        filters = load_filters(client)
        marks = {s: 1e9 for s in positions}  # dust filter must never skip a close
        asof = f"close-all-{datetime.now(timezone.utc).date()}"
        orders = _flatten(client, positions, filters, marks, asof, dry_run=False)
    finally:
        # re-write is idempotent/harmless; the flag is already in place above
        HALT_FLAG.write_text(
            f"manual close-all at {datetime.now(timezone.utc).isoformat()}\n")
    return f"close-all: flattened {len(orders)} positions, halt.flag written"


def status(client) -> str:
    lines: "list[str]" = []
    if not LIVE_JOURNAL.exists():
        lines.append("no live journal yet")
    else:
        try:
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
        except Exception as e:
            lines.append(f"WARN: cannot parse live journal: {e}")
    if HALT_FLAG.exists():
        lines.append(f"WARN: halt.flag present — {HALT_FLAG.read_text().strip()}")
    if FILLS.exists():
        try:
            tail = [json.loads(l) for l in FILLS.read_text().splitlines()][-5:]
            errs = [f for f in tail if "error" in f]
            if errs:
                lines.append(f"WARN: {len(errs)} order errors in last 5 fills")
        except Exception as e:
            lines.append(f"WARN: cannot parse fills: {e}")
    try:
        lines.append(f"open positions: {len(client.positions())}")
    except Exception as e:  # status must never crash
        lines.append(f"WARN: cannot read positions: {e}")
    return "\n".join(lines)


def compare() -> str:
    import statistics
    if not FILLS.exists():
        return "compare: no fills yet"
    if not CH_JOURNAL.exists():
        return "compare: no champion journal"
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--testnet", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p_run = sub.add_parser("run")
    p_run.add_argument("--dry-run", action="store_true")
    sub.add_parser("close-all")
    sub.add_parser("status")
    sub.add_parser("compare")
    args = ap.parse_args()
    cmd = args.cmd or "run"
    if args.testnet:
        _use_testnet()
    client = make_client(args.testnet)
    if cmd == "run":
        print(run(client, dry_run=getattr(args, "dry_run", False)))
    elif cmd == "close-all":
        print(close_all(client))       # Task 6
    elif cmd == "status":
        print(status(client))          # Task 6
    elif cmd == "compare":
        print(compare())               # Task 7


if __name__ == "__main__":
    main()
