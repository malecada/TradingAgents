"""S1 — the weekly parity check must DIFF the live journal against the replay.

Before: compare() loaded a nonexistent `decisions` table, never loaded
portfolio_snapshots, and set the verdict purely from the replay's own Sharpe>1
— so it never noticed when the live equity curve diverged from the replay
(the whole point of a parity check). Now it aligns the live daily returns
(from portfolio_snapshots) against the replay portfolio returns over the same
window and the verdict is driven by their divergence.
"""
import numpy as np
import pandas as pd
import pytest

parity = pytest.importorskip("scripts.parity_refetch_and_replay")


def _write_replay(replay_dir, dates, port_returns):
    replay_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({"portfolio": port_returns}, index=pd.to_datetime(dates))
    df.to_csv(replay_dir / "daily_returns.csv")


def _live(snapshot_dates, values, status="ok"):
    n = len(snapshot_dates)
    return {
        "cycles": pd.DataFrame({
            "cycle_id": list(snapshot_dates),
            "status": [status] * n,
            "n_trades": [1] * n,
        }),
        "predictions": pd.DataFrame(),
        "sizing": pd.DataFrame(),
        "trades": pd.DataFrame(),
        "portfolio_snapshots": pd.DataFrame({
            "ts": [f"{d}T00:06:00+00:00" for d in snapshot_dates],
            "total_value": values,
        }),
    }


def test_pass_when_live_tracks_replay(tmp_path):
    dates = pd.date_range("2026-05-01", periods=16, freq="D")
    iso = [d.strftime("%Y-%m-%d") for d in dates]
    rng = np.random.default_rng(3)
    # Realistic varying daily returns; the live equity is built from the SAME
    # returns the replay produces (high corr, ~zero gap) -> PASS.
    rets = rng.normal(0.001, 0.015, len(dates) - 1)
    values = [10000.0]
    for r in rets:
        values.append(values[-1] * (1 + r))
    replay_returns = [0.0] + list(rets)
    _write_replay(tmp_path / "replay", dates, replay_returns)

    verdict = parity.compare(
        _live(iso, values), tmp_path / "replay", tmp_path / "report.md",
        iso[0], iso[-1],
    )
    assert verdict == "PASS"


def test_fail_when_live_diverges_from_replay(tmp_path):
    dates = pd.date_range("2026-05-01", periods=16, freq="D")
    iso = [d.strftime("%Y-%m-%d") for d in dates]
    rng = np.random.default_rng(5)
    rets = rng.normal(0.001, 0.015, len(dates) - 1)
    # live realizes the OPPOSITE of the replay -> anti-correlated, huge gap.
    live_rets = -rets
    values = [10000.0]
    for r in live_rets:
        values.append(values[-1] * (1 + r))
    replay_returns = [0.0] + list(rets)
    _write_replay(tmp_path / "replay", dates, replay_returns)

    verdict = parity.compare(
        _live(iso, values), tmp_path / "replay", tmp_path / "report.md",
        iso[0], iso[-1],
    )
    assert verdict == "FAIL"


def test_insufficient_window_when_few_bars(tmp_path):
    dates = pd.date_range("2026-05-01", periods=4, freq="D")
    iso = [d.strftime("%Y-%m-%d") for d in dates]
    values = [10000, 10010, 10020, 10030]
    _write_replay(tmp_path / "replay", dates, [0.0, 0.001, 0.001, 0.001])
    verdict = parity.compare(
        _live(iso, values), tmp_path / "replay", tmp_path / "report.md",
        iso[0], iso[-1],
    )
    assert verdict == "INSUFFICIENT_WINDOW"


def test_load_live_journal_reads_sizing_not_decisions(tmp_path):
    """The live journal has a `sizing` table, not `decisions`."""
    import sqlite3
    from tradingagents.execution.live.journal import Journal

    db = tmp_path / "trade_journal.db"
    Journal(str(db)).close()  # create schema
    conn = sqlite3.connect(db)
    tables = set(pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table'", conn)["name"])
    conn.close()
    assert "sizing" in tables
    assert "decisions" not in tables

    rows = parity.load_live_journal_rows(str(db), "2026-05-01", "2026-05-31")
    assert "sizing" in rows
    assert "portfolio_snapshots" in rows
