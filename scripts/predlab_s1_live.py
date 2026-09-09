"""S1 champion live executor: journal-follower placing real Binance orders.

Reads the latest row of the paper trader's journal_champion_v2.jsonl (never
recomputes signals, never writes into s1_paper/) and rebalances a real
USDT-M futures account to weights x vt15_b100_scale x equity. Measurement
run for fill/slippage quality — not a registered gate. Spec:
docs/superpowers/specs/2026-08-21-s1-live-executor-design.md

Subcommands:
  run [--dry-run]      daily rebalance with persisted reconciliation state
  close-all            flatten every position (reduce-only) + write halt.flag
  status               one-line health summary + WARN lines
  compare              fills vs paper marks -> slippage report JSON

Flags:
  --testnet            use testnet Binance + testnet data paths (Phase 1b rehearsal)
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import math
import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import live_exec  # noqa: E402
from tradingagents.predlab.binance_client import (  # noqa: E402
    BinanceAPIError, FuturesClient)

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT",
                                PROJECT_ROOT / "data"))
CH_JOURNAL = DATA_ROOT / "predlab" / "s1_paper" / "journal_champion_v2.jsonl"
LDIR = DATA_ROOT / "predlab" / "s1_live"
LIVE_JOURNAL = LDIR / "journal_live_v2.jsonl"
FILLS = LDIR / "fills_v2.jsonl"
HALT_FLAG = LDIR / "halt.flag"
DAY_EQUITY = LDIR / "day_equity.json"
LEVERAGE = 4
MARK_MAX_AGE_S = 600
QUOTE_MAX_AGE_S = 90
TERMINAL = {"FILLED", "CANCELED", "EXPIRED", "EXPIRED_IN_MATCH", "REJECTED"}
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
    LIVE_JOURNAL = LDIR / "journal_live_v2.jsonl"
    FILLS = LDIR / "fills_v2.jsonl"
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
        fh.flush()
        os.fsync(fh.fileno())


def _rows(path: Path, *, strict: bool = False) -> list[dict]:
    out = []
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                if strict:
                    raise ValueError(f"unreadable execution state: {path.name}")
    return out


def _states() -> dict[str, dict]:
    return {r['client_order_id']: r for r in _rows(LDIR / 'order_state_v2.jsonl', strict=True)}


def _event(intent: dict, status: str, **extra) -> dict:
    row = dict(intent, status=status, ts_utc=datetime.now(timezone.utc).isoformat(), **extra)
    _append(LDIR / 'order_state_v2.jsonl', row)
    return row


def _observe(client, intent: dict, response: dict) -> dict:
    status = response.get('status', 'UNKNOWN')
    observed = _event(intent, status, response=response)
    executed = float(response.get('executedQty', 0))
    if executed > 0:
        fee = None
        try:
            trades = client.user_trades(intent['symbol'], response['orderId'])
            complete = (trades and all(t.get('commissionAsset') == 'USDT' for t in trades)
                        and math.isclose(sum(float(t.get('qty', 0)) for t in trades),
                                         executed, rel_tol=1e-8, abs_tol=1e-9))
            if complete:
                fee = sum(float(t['commission']) for t in trades)
        except Exception:
            pass
        # Exchange responses are cumulative per order, including partial orders
        # later cancelled. Append revisions; report readers select the latest.
        quote_qty = float(response.get('cumQuote', 0))
        avg_price = float(response.get('avgPrice', 0)) or quote_qty / executed
        fill = dict(intent, status=status, qty=executed, avg_price=avg_price,
            quote_qty=quote_qty, fee_usdt=fee,
            fee_coverage='complete' if fee is not None else 'incomplete',
            order_id=response.get('orderId'))
        prior = [f for f in _rows(FILLS) if f.get('client_order_id') == intent['client_order_id']]
        compared = {k: v for k, v in fill.items() if k not in ('ts_utc', 'response', 'error')}
        old = {k: v for k, v in prior[-1].items() if k not in ('ts_utc', 'response', 'error')} if prior else None
        if old != compared:
            _append(FILLS, dict(compared, ts_utc=datetime.now(timezone.utc).isoformat()))
    return observed


def _reconcile_pending(client) -> list[dict]:
    """An absent lookup after an ambiguous POST does NOT prove nonexecution."""
    pending = []
    for intent in _states().values():
        if intent['status'] in TERMINAL:
            continue
        try:
            r = client.order_status(intent['symbol'], intent['client_order_id'])
            intent = _observe(client, intent, r)
        except Exception as exc:
            intent = _event(intent, 'UNKNOWN', error=str(exc))
        if intent['status'] not in TERMINAL:
            pending.append(intent)
    return pending


def _place(client, orders: list[live_exec.Order], asof: str, marks: dict | None = None) -> list[dict]:
    results = []
    for o in orders:
        old = _states()
        sequence = sum(r['asof'] == asof and r['symbol'] == o.symbol for r in old.values())
        raw = json.dumps([asof, o.symbol, o.side, o.qty, o.reduce_only, sequence])
        cid = 's1v2-' + hashlib.sha256(raw.encode()).hexdigest()[:30]
        intent = {'asof': asof, 'symbol': o.symbol, 'side': o.side, 'qty': o.qty,
                  'reduce_only': o.reduce_only, 'client_order_id': cid,
                  'reference_mark': (marks or {}).get(o.symbol)}
        # Durable intent precedes POST. A crash here leaves a query-only state.
        intent = _event(intent, 'SUBMITTING')
        try:
            response = client.market_order(o.symbol, o.side, o.qty, o.reduce_only,
                                           client_order_id=cid)
            result = _observe(client, intent, response)
        except Exception as exc:
            rejected = isinstance(exc, BinanceAPIError) and not exc.execution_unknown
            result = _event(intent, 'REJECTED' if rejected else 'UNKNOWN', error=str(exc))
        results.append(result)
        if result['status'] not in TERMINAL:
            _reconcile_pending(client)
            if _states()[cid]['status'] not in TERMINAL:
                break
        time.sleep(ORDER_PACE_S)
    return results


def _asof_already_executed(asof: str) -> bool:
    return any(r.get('asof') == asof and r.get('status') == 'reconciled'
               and not r.get('dry_run') and r.get('journal_version') == 2
               for r in _rows(LIVE_JOURNAL))


def _current_marks(client, symbols: set[str]) -> dict[str, float]:
    marks = {}
    quotes = client.book_ticker()
    now = datetime.now(timezone.utc)
    for row in quotes:
        if row['symbol'] not in symbols:
            continue
        bid, ask = float(row['bidPrice']), float(row['askPrice'])
        age = now.timestamp() - float(row.get('time', 0)) / 1000
        if 0 <= age <= QUOTE_MAX_AGE_S and 0 < bid <= ask and math.isfinite(ask):
            marks[row['symbol']] = (bid + ask) / 2
    return marks


def _residual(targets: dict, positions: dict) -> dict:
    return {s: targets.get(s, 0) - positions.get(s, 0)
            for s in sorted(set(targets) | set(positions))
            if not math.isclose(targets.get(s, 0), positions.get(s, 0), abs_tol=1e-9)}


def _locked(action):
    """Serialize state+POST across cron/manual invocations on this host."""
    def wrapped(client, *args, **kwargs):
        LDIR.mkdir(parents=True, exist_ok=True)
        with (LDIR / 'execution_v2.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return 'WAIT: another executor holds the state lock'
            return action(client, *args, **kwargs)
    return wrapped


@_locked
def run(client, dry_run: bool, today: str | None = None) -> str:
    if HALT_FLAG.exists():
        return f'halt: {HALT_FLAG} present; run close-all to retry residual closure'
    now = datetime.now(timezone.utc)
    today = today or str(now.date())
    if not dry_run and client.position_mode():
        return 'ERROR: account in hedge mode; one-way mode required before any order'
    equity = client.equity()
    if not math.isfinite(equity) or equity <= 0:
        return 'ERROR: invalid account equity'
    day_eq = equity if dry_run else day_start_equity(today, equity)
    if live_exec.daily_loss_breached(equity, day_eq):
        if dry_run:
            return 'dry-run: daily loss breached; would halt and flatten'
        return 'halt: daily loss breached; ' + _close_all(client)
    if not dry_run:
        pending = _reconcile_pending(client)
        if pending:
            return f'incomplete: {len(pending)} unresolved order intents; no new submissions'
    row = read_champion_row()
    if row is None:
        return 'ERROR: no champion journal row'
    asof = row['asof']
    if row.get('journal_version') != 2:
        return 'WAIT: champion journal requires corrected measurement version 2'
    try:
        age = (date.fromisoformat(today) - date.fromisoformat(asof)).days
        if age != 1 or row.get('trade_day') != today:
            return 'WAIT: stale or future champion signal date'
    except ValueError:
        return 'WAIT: invalid champion signal date'
    intents = [r for r in _rows(LIVE_JOURNAL) if r.get('asof') == asof and
               not r.get('dry_run') and 'target_qty' in r]
    if not dry_run and _asof_already_executed(asof):
        # Completion is backed by an actual position check even on later wakes.
        prior = [r for r in _rows(LIVE_JOURNAL) if r.get('asof') == asof and
                 r.get('status') == 'reconciled' and not r.get('dry_run')][-1]
        if not _residual(prior['target_qty'], client.positions()):
            return f'skip: {asof} already reconciled'
    scale = row.get('vt15_b100_scale')
    if scale is None:
        return 'WAIT: vt15_b100_scale is null (net vol window not accrued)'
    if not math.isfinite(scale) or scale < 0:
        return 'WAIT: invalid scale'
    weights = row.get('weights') or {}
    if any(not math.isfinite(w) for w in weights.values()):
        return 'WAIT: invalid desired weights'
    paper_marks = row.get('mark_px') or {}
    if any(s not in paper_marks or not math.isfinite(paper_marks[s]) or paper_marks[s] <= 0
           for s, w in weights.items() if w):
        return 'WAIT: champion row has missing or invalid marks'
    # A frozen incomplete batch was admitted with valid paper marks already.
    # Its residuals are reconciled using fresh exchange quotes below; the old
    # immutable paper quote must not strand an otherwise retryable batch.
    if not intents:
        try:
            age_s = (now - datetime.fromisoformat(row['mark_ts'])).total_seconds()
            if not 0 <= age_s <= MARK_MAX_AGE_S:
                return 'WAIT: stale or future champion marks'
        except (KeyError, TypeError, ValueError):
            return 'WAIT: champion mark timestamp unavailable'
    filters = load_filters(client)
    positions = client.positions()
    frozen_symbols = set(intents[0]['target_qty']) if intents else set()
    symbols = set(weights) | set(positions) | frozen_symbols
    try:
        marks = _current_marks(client, symbols)
    except Exception as exc:
        return f'WAIT: current quotes unavailable: {exc}'
    if symbols - marks.keys():
        return 'WAIT: missing or stale current quotes for desired/held exposure'
    scale_executed = min(scale, SCALE_CLAMP)
    targets_qty, dropped = live_exec.build_targets(weights, scale_executed, equity, marks, filters)
    unavailable = {d['symbol'] for d in dropped if d['reason'] in ('no_mark', 'no_filter')}
    if unavailable:
        return 'WAIT: desired target unavailable: ' + ', '.join(sorted(unavailable))
    if intents:
        targets_qty = intents[0]['target_qty']
    orders, skipped = live_exec.diff_orders(targets_qty, positions, marks, filters,
                                            unavailable=unavailable)
    # Accepted dust is an explicit retained holding, frozen in the batch target.
    if not intents:
        for skip in skipped:
            if skip['reason'] in ('dust', 'increase_below_min_notional'):
                targets_qty[skip['symbol']] = positions.get(skip['symbol'], 0)
    tn = {s: q * marks[s] for s, q in targets_qty.items()}
    # Conservative whole-book envelope includes residuals if reductions fail.
    envelope = {s: max(abs(positions.get(s, 0)), abs(targets_qty.get(s, 0))) * marks[s]
                for s in symbols}
    caps = live_exec.check_caps(envelope, equity)
    if caps:
        return 'ERROR: cap violation including held exposure: ' + '; '.join(caps)
    jrow = live_exec.build_journal_row(asof, now.isoformat(), equity, day_eq,
        scale_executed, tn, orders, dropped, skipped, False, dry_run, scale)
    jrow.update(journal_version=2, target_qty=targets_qty, status='intent',
                orders_intended=len(orders), orders_placed=0, orders_acknowledged=0,
                orders_filled=0, quote_px=marks)
    if dry_run:
        jrow.update(status='dry_run', intended_orders=[vars(o) for o in orders])
        _append(LDIR / 'journal_dry_v2.jsonl', jrow)
        return f'dry-run {asof}: {len(orders)} intended orders'
    _append(LIVE_JOURNAL, jrow)
    for o in orders:
        try:
            client.set_leverage(o.symbol, LEVERAGE)
        except BinanceAPIError:
            pass
    outcomes = _place(client, orders, asof, marks)
    pending = _reconcile_pending(client)
    actual = client.positions()
    residual = _residual(targets_qty, actual)
    states = _states()
    outcomes = [states[r['client_order_id']] for r in outcomes]
    filled = sum(r['status'] == 'FILLED' for r in outcomes)
    complete = not residual and not pending and not any(
        r['status'] == 'REJECTED' for r in outcomes) and not any(
        s['reason'] == 'no_filter' for s in skipped)
    jrow.update(status='reconciled' if complete else 'incomplete',
                actual_positions=actual, residual_qty=residual, orders_submitted=len(outcomes),
                orders_placed=filled, orders_filled=filled,
                orders_acknowledged=sum('response' in r for r in outcomes))
    _append(LIVE_JOURNAL, jrow)
    return f"{'done' if complete else 'incomplete'} {asof}: {filled} filled, {len(residual)} residual positions"


def _close_all(client) -> str:
    LDIR.mkdir(parents=True, exist_ok=True)
    HALT_FLAG.write_text(f'manual or risk close-all at {datetime.now(timezone.utc).isoformat()}\n')
    if client.position_mode():
        return 'close-all incomplete: hedge mode; no orders placed, halt.flag written'
    pending = _reconcile_pending(client)
    if pending:
        return f'close-all incomplete: {len(pending)} unknown/working orders; halt.flag written'
    positions = client.positions()
    filters = load_filters(client)
    orders, skipped = live_exec.diff_orders({}, positions, {}, filters)
    asof = f'close-all-{datetime.now(timezone.utc).date()}'
    _place(client, orders, asof)
    pending = _reconcile_pending(client)
    residual = client.positions()
    complete = not residual and not pending and not skipped
    _append(LDIR / 'closure_v2.jsonl', dict(asof=asof,
        status='reconciled' if complete else 'incomplete', residual_positions=residual,
        pending_order_ids=[r['client_order_id'] for r in pending], skipped=skipped))
    if complete:
        return f'close-all: flattened {len(positions)} positions, zero residual verified; halt.flag written'
    return f'close-all incomplete: {len(residual)} residual positions; halt.flag written'


@_locked
def close_all(client) -> str:
    return _close_all(client)


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
            if last.get("status") != "reconciled":
                lines.append(f"WARN: execution {last.get('status', 'unverified legacy')}; residual {last.get('residual_qty')}")
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
    records = [json.loads(l) for l in FILLS.read_text().splitlines()]
    cumulative = {}
    for i, record in enumerate(records):
        cumulative[record.get('client_order_id', f'legacy-row-{i}')] = record
    fills = list(cumulative.values())
    ch = {r["asof"]: r.get("mark_px") or {}
          for r in (json.loads(l)
                    for l in CH_JOURNAL.read_text().splitlines())}
    per_leg: "list[dict]" = []
    for f in fills:
        if "error" in f or not f.get("avg_price"):
            continue
        mark = f.get("reference_mark") or ch.get(f["asof"], {}).get(f["symbol"])
        if not mark:
            continue
        sign = 1.0 if f["side"] == "BUY" else -1.0
        bps = (f["avg_price"] / mark - 1.0) * 1e4 * sign
        per_leg.append({"asof": f["asof"], "symbol": f["symbol"],
                        "side": f["side"], "fill": f["avg_price"],
                        "mark": mark, "bps": round(bps, 2),
                        "benchmark": "execution_quote" if f.get("reference_mark") else "paper_quote_diagnostic"})
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
        "total_fees_usdt": (round(sum(f["fee_usdt"] for f in fills), 6)
                            if fills and all(f.get("fee_usdt") is not None for f in fills) else None),
        "fee_coverage": ("complete" if fills and all(f.get("fee_usdt") is not None for f in fills) else "incomplete"),
        "known_fees_usdt": round(sum(f.get("fee_usdt") or 0.0 for f in fills), 6),
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
