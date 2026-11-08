"""Scheduled, point-in-time-knowable events for the dossier (plan §5.3): FOMC decision dates
(published years ahead by the Federal Reserve) and the asset's supply schedule from the card.
Rendered relative to the decision time only."""
from __future__ import annotations

import pandas as pd

FOMC_DECISION_DATES = [
    # second day of each scheduled two-day meeting
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
]
_FOMC = pd.to_datetime(FOMC_DECISION_DATES, utc=True)


def next_fomc_days(decision_ts: pd.Timestamp) -> int | None:
    future = _FOMC[_FOMC >= decision_ts.normalize()]
    return int((future[0] - decision_ts.normalize()).days) if len(future) else None


def last_fomc_days(decision_ts: pd.Timestamp) -> int | None:
    past = _FOMC[_FOMC < decision_ts.normalize()]
    return int((decision_ts.normalize() - past[-1]).days) if len(past) else None


def render_calendar(decision_ts: pd.Timestamp, numeric: dict) -> str:
    lines = ["## Scheduled events (known in advance)"]
    nxt, last = next_fomc_days(decision_ts), last_fomc_days(decision_ts)
    if nxt is not None:
        lines.append(f"- Next US central-bank rate decision in {nxt} days" + (f"; the last one was {last} days ago." if last is not None else "."))
    unlock = numeric.get("unlock_next30_pct_supply")
    if unlock:
        lines.append(f"- Token unlock within the next 30 days equal to {unlock}% of circulating supply.")
    elif unlock == 0:
        lines.append("- No scheduled unlock in the next 30 days.")
    else:
        lines.append("- Unlock schedule unavailable for this asset.")
    lines.append("- Weekly perpetual-futures funding settles every 8 hours; quarterly futures expire on the last Friday of each quarter.")
    return "\n".join(lines) + "\n"
