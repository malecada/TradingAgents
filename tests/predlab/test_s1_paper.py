"""Unit tests for the S1 daily paper-trader (synthetic rows — no network).

Covers the two forward-record integrity fixes:
  * the vol-target window must ignore returns measured across a journal gap
    (host down => one row carries a multi-day return, not a daily one);
  * each row records the price actually observable at write time, so the
    close-to-close fill assumption can be checked against a real mark.
"""
from __future__ import annotations

import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from predlab_s1_paper import (  # noqa: E402
    journal_one, realized_prev_mark_return, vt_scale,
)


def _rows(pairs: "list[tuple[str, float | None]]") -> "list[dict]":
    return [{"asof": d, "realized_book_ret": r} for d, r in pairs]


def _seq(start: str, rets: "list[float | None]") -> "list[tuple[str, float | None]]":
    d0 = date.fromisoformat(start)
    return [(str(d0 + timedelta(days=i)), r) for i, r in enumerate(rets)]


VALS = [0.01 * (1 if i % 2 else -1) * (1 + i / 30) for i in range(21)]


def test_vt_scale_ignores_return_measured_across_a_journal_gap():
    """A gap row's multi-day return must not enter the 20-day vol window."""
    clean = _rows(_seq("2026-01-01", [None] + VALS))

    gap = _rows(_seq("2026-01-01", [None] + VALS[:9]))
    gap.append({"asof": "2026-01-14", "realized_book_ret": 0.30})  # spans 4d
    gap += _rows(_seq("2026-01-15", VALS[9:]))

    assert vt_scale(gap, 0.15) == pytest.approx(vt_scale(clean, 0.15))


def test_vt_scale_needs_21_gap_free_returns():
    """Dropping gap rows must also drop them from the sufficiency count."""
    rows = _rows(_seq("2026-01-01", [None] + VALS[:20]))
    rows.append({"asof": "2026-01-25", "realized_book_ret": 0.02})  # spans 4d
    assert vt_scale(rows, 0.15) is None


def test_realized_prev_mark_return_uses_the_marks_recorded_at_write_time():
    prev = {"weights": {"AAA": 0.5, "BBB": -0.5},
            "mark_px": {"AAA": 100.0, "BBB": 50.0}}
    got = realized_prev_mark_return(prev, {"AAA": 110.0, "BBB": 45.0})
    assert got == pytest.approx(0.5 * math.log(1.1) - 0.5 * math.log(0.9))


def test_realized_prev_mark_return_is_none_for_a_row_written_without_marks():
    prev = {"weights": {"AAA": 1.0}}
    assert realized_prev_mark_return(prev, {"AAA": 110.0}) is None


def test_realized_prev_mark_return_skips_symbols_absent_from_current_marks():
    prev = {"weights": {"AAA": 0.5, "BBB": -0.5},
            "mark_px": {"AAA": 100.0, "BBB": 50.0}}
    got = realized_prev_mark_return(prev, {"AAA": 110.0})
    assert got == pytest.approx(0.5 * math.log(1.1))


@pytest.fixture()
def panels():
    syms = [f"S{i:02d}USDT" for i in range(30)]
    idx = pd.date_range("2026-01-01", periods=45, freq="D", tz="UTC")
    rng = np.random.default_rng(3)
    close = pd.DataFrame(100.0, index=idx, columns=syms)
    qv = pd.DataFrame(rng.uniform(1e6, 9e6, (len(idx), len(syms))),
                      index=idx, columns=syms)
    park = pd.DataFrame(rng.uniform(1e-4, 9e-4, (len(idx), len(syms))),
                        index=idx, columns=syms)
    return {"close": close, "qv": qv, "park": park}


def test_journal_one_records_the_write_time_mark_for_every_book_name(panels, tmp_path):
    journal = tmp_path / "j.jsonl"
    marks = {s: 100.0 + i for i, s in enumerate(panels["close"].columns)}

    journal_one(journal, panels, "ewma_20", "vt15_b100_scale", 0.15,
                breadth_floor=None, marks=marks)

    import json
    row = json.loads(journal.read_text().splitlines()[0])
    assert set(row["mark_px"]) == set(row["weights"])
    assert row["mark_ts"] is not None
    assert row["realized_mark_ret"] is None  # no prior row to mark against
