"""Predlab paper-book journal parsing and derived metrics.

The S1 paper trader writes JSONL weights-and-returns journals (no equity
or position fields). This module is pure: functions take parsed rows and
return plain dicts for the API layer. Filesystem access is limited to
``parse_journal`` / ``_load_json``; both degrade to empty results on
missing files. See docs/superpowers/specs/2026-08-06-monitor-predlab-
overhaul-design.md.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from tradingagents.monitor import metrics
from tradingagents.monitor.sources import ttl_cached

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
        asof = row.get("asof") if isinstance(row, dict) else None
        if isinstance(asof, str):
            try:
                date.fromisoformat(asof)
            except ValueError:
                asof = None
        else:
            asof = None
        if asof is not None:
            rows.append(row)
        else:
            malformed += 1
    rows.sort(key=lambda r: r["asof"])
    return rows, malformed


def _realized(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("realized_book_ret") is not None]


def derive_slippage(rows: list[dict]) -> dict | None:
    """What the close-to-close fill assumption costs, in basis points.

    ``realized_book_ret`` prices the book at the UTC close; the paper
    trader writes the row minutes later and stores ``realized_mark_ret``
    for the same book measured between those write-time marks. The
    difference is the slippage the close-only journal used to hide.
    Negative = the assumed close fill flattered the book. None until a day
    carries both legs (rows written before 2026-08-18 carry no marks).
    """
    pairs = [r for r in rows
             if r.get("realized_book_ret") is not None
             and r.get("realized_mark_ret") is not None]
    if not pairs:
        return None
    bps = [(r["realized_mark_ret"] - r["realized_book_ret"]) * 1e4
           for r in pairs]
    last = pairs[-1]
    return {
        "n": len(pairs),
        "mean_bps": round(sum(bps) / len(bps), 4),
        "cum_bps": round(sum(bps), 4),
        "last": {"asof": last["asof"],
                 "close_ret": last["realized_book_ret"],
                 "mark_ret": last["realized_mark_ret"],
                 "bps": round(bps[-1], 4)},
    }


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
        "slippage": derive_slippage(rows),
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


def derive_nav(rows: list[dict], scale_key: str) -> dict | None:
    """Account-percent NAV: 100 x prod(1 + scale_prev_t x ret_t).

    ``scale_prev`` is the PREVIOUS row's ``scale_key`` value — the scale
    that was actually known when the position for day t was put on. A row
    only compounds when both its own ``realized_book_ret`` is not None
    AND the previous row's scale is not None; otherwise the day is flat
    (no position / no return data) and NAV carries forward unchanged.
    Series starts at the first row, base 100.0; None if rows is empty.
    """
    if not rows:
        return None
    series = [{"ts": rows[0]["asof"], "value": 100.0}]
    nav = 100.0
    active_days = 0
    prev_scale = rows[0].get(scale_key)
    for row in rows[1:]:
        ret = row.get("realized_book_ret")
        if ret is not None:
            if prev_scale is not None:
                nav *= 1.0 + prev_scale * ret
                active_days += 1
            series.append({"ts": row["asof"], "value": nav})
        prev_scale = row.get(scale_key)
    scales = [r.get(scale_key) for r in rows if r.get(scale_key) is not None]
    return {
        "series": series,
        "cards": {
            "nav_cum_return": (nav / 100.0 - 1.0) if active_days else None,
            "active_days": active_days,
            "warmup": {"n": len(scales), "required": WARMUP_RETURNS},
            "last_scale": scales[-1] if scales else None,
        },
    }


def derive_account(rows: list[dict], halted: bool) -> dict | None:
    """Live-account equity block from ``journal_live`` rows, or None when
    no row carries a positive numeric ``equity_before`` (unfunded/zero
    first reading can't anchor an index-to-100 series — avoid a
    division-by-zero that would otherwise poison the ttl-cached payload
    for every /api/predlab endpoint)."""
    valid = [r for r in rows if isinstance(r.get("equity_before"), (int, float))
             and not isinstance(r.get("equity_before"), bool)
             and r["equity_before"] > 0]
    if not valid:
        return None
    first = valid[0]["equity_before"]
    series = [{"ts": r["asof"], "value": 100.0 * r["equity_before"] / first}
              for r in valid]
    last_eq = valid[-1]["equity_before"]
    last_row = rows[-1]
    return {
        "series": series,
        "cards": {
            "cum_return": last_eq / first - 1.0,
            "equity": last_eq,
            "n_cycles": len(rows),
            "orders_total": sum((r.get("orders_placed") or 0) for r in rows),
            "last_asof": last_row["asof"],
            "dry_run_last": bool(last_row.get("dry_run")),
            "halted": halted,
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
        except (ValueError, TypeError):
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
        account = {}
        for venue in ("testnet", "live"):
            venue_root = root / f"s1_{venue}"
            venue_rows, _m = parse_journal(venue_root / "journal_live.jsonl")
            halted = (venue_root / "halt.flag").is_file()
            account[venue] = derive_account(venue_rows, halted)
        return {
            "performance": {
                "books": {b: derive_book(rows, sk)
                          for b, (rows, _m, sk) in parsed.items()},
                "nav": {b: derive_nav(rows, sk)
                        for b, (rows, _m, sk) in parsed.items()},
                "account": account,
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
