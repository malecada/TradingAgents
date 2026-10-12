"""Monday-anchored UTC weeks, one-day graph lag, initial-ETH fold membership (spec §10)."""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

from .config import load

LOOKBACK = 28
_G = load('graph')
_C = load('calendar')
FIRST_WEEK = date.fromisoformat(_G['first_week'])
LAST_WEEK = date.fromisoformat(_G['last_week'])
LAG = timedelta(days=_C['graph_lag_days'])


@lru_cache(maxsize=None)
def weeks() -> list[str]:
    out, d = [], FIRST_WEEK
    while d <= LAST_WEEK:
        out.append(d.isoformat())
        d += timedelta(days=7)
    assert len(out) == _G['expected_weeks']
    return out


def week_days(week: str) -> list[str]:
    start = date.fromisoformat(week)
    return [(start + timedelta(days=k)).isoformat() for k in range(7)]


def week_end(week: str) -> date:
    return date.fromisoformat(week) + timedelta(days=7)


def available_week(day: date) -> str | None:
    """Latest week whose end (next Monday) plus the lag is at or before the start of day+1, i.e. end <= day."""
    best = None
    for w in weeks():
        if week_end(w) + LAG <= day + timedelta(days=1):
            best = w
        else:
            break
    return best


def window(d: date) -> list[date]:
    return [d - timedelta(days=LOOKBACK - 1 - k) for k in range(LOOKBACK)]


def _complete(d: date) -> bool:
    return all(available_week(t) is not None for t in window(d))


@lru_cache(maxsize=None)
def decision_dates(split: str) -> list[date]:
    label_end = date.fromisoformat(_C['train_label_end_exclusive'])
    if split == 'train':
        start, end = FIRST_WEEK, label_end - timedelta(days=2)      # label day d+1 < label_end
    elif split == 'test':
        start = date.fromisoformat(_C['test_decision_start'])
        end = date.fromisoformat(_C['test_decision_end'])
    else:
        raise ValueError(split)
    out, d = [], start
    while d <= end:
        if _complete(d):
            out.append(d)
        d += timedelta(days=1)
    return out
