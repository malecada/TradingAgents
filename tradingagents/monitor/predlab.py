"""Read-only v2 measurements; legacy journals remain composition diagnostics."""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from tradingagents.monitor.journal_measurements import (
    derive_account, derive_book, derive_nav, number, quantities, record_error,
)
from tradingagents.monitor.sources import ttl_cached

# book key -> (journal filename, scale key). Champion is the frozen
# Phase-O system; vt10 is the old S1 book kept for the pp2 confirmation.
BOOKS: dict[str, tuple[str, str]] = {
    "champion": ("journal_champion.jsonl", "vt15_b100_scale"),
    "vt10": ("journal.jsonl", "vt10_scale"),
}
WARMUP_RETURNS = 20          # v2 paper trader uses 20 contiguous base net returns
STALE_AFTER_HOURS = 36.0
_ROLLING_WINDOW = 30
# VPS scheduler was off on these dates — documented, not an incident.
KNOWN_GAPS = {"2026-07-31", "2026-08-01", "2026-08-02"}
# Sealed one-shot (gates.json predlab_opt.forward_one_shot). The gate
# display is informational only; the evaluation itself stays sealed.
FORWARD_START = date(2026, 7, 2)
EARLIEST_EVAL = date(2027, 1, 2)
V2_JOURNALS = {'champion': 'journal_champion_v2.jsonl', 'vt10': 'journal_v2.jsonl'}


def parse_journal(path: Path) -> tuple[list[dict], int]:
    """(rows sorted by asof, malformed-line count); ([], 0) if missing."""
    if not path.is_file():
        return [], 0
    rows: list[dict] = []
    malformed = 0
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeError):
        return [], 1
    for line in lines:
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
                if date.fromisoformat(asof).isoformat() != asof:
                    raise ValueError('noncanonical daily date')
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
             if number(r.get("realized_book_ret"))
             and number(r.get("realized_mark_ret"))]
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


def book_detail(rows: list[dict], scale_key: str) -> dict | None:
    """Latest-row book composition, or None when the journal is empty."""
    if not rows:
        return None
    cur = rows[-1]
    weights: dict = cur.get("weights") if quantities(cur.get("weights")) else {}
    longs = sorted(
        ({"symbol": s, "weight": w} for s, w in weights.items() if w > 0),
        key=lambda x: x["symbol"])
    shorts = sorted(
        ({"symbol": s, "weight": w} for s, w in weights.items() if w < 0),
        key=lambda x: x["symbol"])
    delta = None
    if len(rows) >= 2:
        prior_weights = rows[-2].get("weights")
        prev = set(prior_weights) if quantities(prior_weights) else set()
        now = set(weights)
        delta = {"entered": len(now - prev), "exited": len(prev - now)}
    return {
        "asof": cur["asof"],
        "n_universe": cur.get("n_universe") if number(cur.get("n_universe")) else None,
        "breadth": cur.get("breadth") if number(cur.get("breadth")) else None,
        "membership_hash": cur.get("membership_hash") if isinstance(cur.get("membership_hash"), str) else None,
        "scale": cur.get(scale_key) if number(cur.get(scale_key)) else None,
        "est_turnover": cur.get("est_turnover") if number(cur.get("est_turnover")) else None,
        "est_cost": cur.get("est_cost") if number(cur.get("est_cost")) else None,
        "longs": longs, "shorts": shorts, "delta": delta,
    }


def book_health(rows: list[dict], malformed: int,
                now_utc: datetime) -> dict | None:
    """Freshness + gap payload for one book; None when journal empty."""
    if not rows:
        return None
    last = rows[-1]
    stale = True
    written = last.get("written_utc") if isinstance(last.get("written_utc"), str) else None
    if isinstance(written, str):
        try:
            # fromisoformat rejects a trailing "Z" before Python 3.11
            ts = datetime.fromisoformat(written.replace("Z", "+00:00"))
            age_h = (now_utc - ts).total_seconds() / 3600.0
            stale = age_h < 0 or age_h > STALE_AFTER_HOURS
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
    """Operational suspension; saved historical criteria are never rewritten."""
    return {
        'status': 'suspended_after_audit',
        'reason': 'Historical development and legacy paper measurements were invalidated; no active validation gate is served.',
        'window_start': FORWARD_START.isoformat(),
        'earliest_eval': EARLIEST_EVAL.isoformat(),
        'days_elapsed': (today_utc - FORWARD_START).days,
        'days_remaining': max(0, (EARLIEST_EVAL - today_utc).days),
        'threshold_sr': None, 'criteria': [],
        'running': {'sr': None, 'n_returns': 0,
                    'note': 'Suspended after audit; operational measurements do not validate a strategy.'},
        'informational': True,
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
        now = datetime.now(timezone.utc)
        books, nav, details, health, descriptors = {}, {}, {}, {}, {}
        for book, (legacy_name, scale_key) in BOOKS.items():
            directory = root / 's1_paper'
            legacy, legacy_bad = parse_journal(directory / legacy_name)
            v2_path = directory / V2_JOURNALS[book]
            is_v2 = v2_path.exists()
            selected = v2_path if is_v2 else directory / legacy_name
            rows, malformed = parse_journal(selected) if is_v2 else (legacy, legacy_bad)
            issue = ('malformed or unreadable journal records' if malformed else
                     record_error(rows, paper=True) if is_v2 and rows else None)
            books[book] = derive_book(rows, scale_key, invalid_reason=issue) if is_v2 else None
            nav[book] = derive_nav(rows, scale_key, invalid_reason=issue) if is_v2 else None
            if is_v2:
                statuses = [block['measurement_status'] for block in (books[book], nav[book]) if block]
                status = ('invalid' if issue or 'invalid' in statuses else 'incomplete' if not rows or 'incomplete' in statuses else
                          'warmup' if 'warmup' in statuses else 'corrected_v2')
                reason = issue or next((block['measurement_reason'] for block in (books[book], nav[book])
                                       if block and block['measurement_reason']), None)
                if not rows and not issue:
                    reason = 'v2 journal exists but has no measurement records'
            else:
                status = 'legacy_only' if selected.exists() else 'missing'
                reason = ('legacy gross journals are not corrected net measurements' if status == 'legacy_only'
                          else 'no journal available')
            descriptors[book] = dict(status=status, reason=reason,
                                     journal=selected.name if selected.exists() else None)
            details[book] = book_detail(rows, scale_key)
            h = book_health(rows, malformed, now)
            if h is None and selected.exists():
                h = dict(last_asof=None, written_utc=None, stale=True, rows=0, malformed=malformed, gaps=[])
            if h is not None:
                h.update(journal_version=2 if is_v2 else None, measurement_status=status,
                         measurement_reason=reason, legacy_rows=len(legacy), journal=selected.name)
            health[book] = h
        account = {}
        for venue in ('testnet', 'live'):
            directory = root / f's1_{venue}'
            v2_path = directory / 'journal_live_v2.jsonl'
            legacy_path = directory / 'journal_live.jsonl'
            selected = v2_path if v2_path.exists() else legacy_path
            rows, malformed = parse_journal(selected)
            issue = 'malformed or unreadable account journal' if malformed else None
            if v2_path.exists() and rows:
                issue = issue or record_error(rows, duplicates=False)
            account[venue] = derive_account(rows, (directory/'halt.flag').is_file(),
                invalid_reason=issue, empty_status='incomplete' if v2_path.exists() else None)
            if account[venue]:
                account[venue]['journal'] = selected.name
        statuses = [d['status'] for d in descriptors.values()]
        overall = (statuses[0] if len(set(statuses)) == 1 else 'invalid' if 'invalid' in statuses else
                   'incomplete' if any(s in {'corrected_v2', 'incomplete', 'warmup'} for s in statuses) else
                   'legacy_only' if 'legacy_only' in statuses else 'missing')
        return {
            'performance': {'books': books, 'nav': nav, 'account': account,
                'reference': None, 'backtest_yearly': None,
                'measurement': {'status': overall,
                    'note': 'Version-2 net measurements require complete contiguous journals; legacy gross observations do not validate a strategy.',
                    'books': descriptors}},
            'books': details, 'gate': gate_status([], None, now.date()),
            'health': {'books': health, 'heartbeat_note': HEARTBEAT_NOTE},
        }


def resolve_predlab_source() -> PredlabSource | None:
    """PredlabSource from PREDLAB_DATA_DIR, or None when unset."""
    data_dir = os.environ.get("PREDLAB_DATA_DIR")
    return PredlabSource(data_dir) if data_dir else None
