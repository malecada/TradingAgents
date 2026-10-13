"""Weeks, the one-day graph lag and the development / holdout windows (spec §4.2)."""
from __future__ import annotations

import bisect
from datetime import date, timedelta
from functools import lru_cache

from .config import load

_C = load()
LAG = timedelta(days=_C['graph_lag_days'])
DEV_START = date.fromisoformat(_C['windows']['dev_start'])
DEV_END = date.fromisoformat(_C['windows']['dev_end'])
HOLD_START = date.fromisoformat(_C['windows']['holdout_start'])
HOLD_END = date.fromisoformat(_C['windows']['holdout_end'])


def mondays(first: str, last: str) -> list[str]:
    d, end, out = date.fromisoformat(first), date.fromisoformat(last), []
    assert d.weekday() == 0 and end.weekday() == 0
    while d <= end:
        out.append(d.isoformat())
        d += timedelta(days=7)
    return out


@lru_cache(maxsize=None)
def _all():
    return tuple(mondays(_C['weeks']['first'], _C['weeks']['last']))


def all_weeks() -> list[str]:
    return list(_all())


def dictionary_weeks() -> list[str]:
    return mondays(_C['dictionary']['first_week'], _C['dictionary']['last_week'])


def week_days(week: str) -> list[str]:
    start = date.fromisoformat(week)
    return [(start + timedelta(days=k)).isoformat() for k in range(7)]


def week_end(week: str) -> date:
    return date.fromisoformat(week) + timedelta(days=7)


def latest_week_for(day: date, weeks: list[str]) -> str | None:
    """Latest week whose end plus the lag is no later than the start of day+1."""
    ends = [week_end(w) + LAG for w in weeks]
    i = bisect.bisect_right(ends, day + timedelta(days=1))
    return weeks[i - 1] if i else None


def weekly_window(m: date) -> str | None:
    if DEV_START <= m and m + timedelta(days=7) <= DEV_END:
        return 'dev'
    if HOLD_START <= m and m + timedelta(days=7) <= HOLD_END:
        return 'holdout'
    return None


def daily_window(d: date) -> str | None:
    if DEV_START <= d and d + timedelta(days=1) <= DEV_END:
        return 'dev'
    if HOLD_START <= d and d + timedelta(days=1) <= HOLD_END:
        return 'holdout'
    return None