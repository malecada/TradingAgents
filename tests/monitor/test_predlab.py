"""Unit tests for the predlab pure-function layer (no HTTP, no env)."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from tradingagents.monitor import predlab


def _row(asof, ret, scale=None, **over):
    row = {
        "asof": asof, "written_utc": f"{asof}T00:20:00+00:00",
        "n_universe": 523, "membership_hash": "4807428b5dab",
        "weights": {"BTCUSDT": 0.025, "ETHUSDT": 0.025,
                    "AKEUSDT": -0.025, "BANKUSDT": -0.025},
        "realized_book_ret": ret, "est_turnover": 0.10, "est_cost": 0.00005,
        "vt15_b100_scale": scale, "breadth": 200,
    }
    row.update(over)
    return row


def _write_journal(tmp_path, rows):
    p = tmp_path / "journal_champion.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


class TestParseJournal:
    def test_missing_file_returns_empty(self, tmp_path):
        rows, bad = predlab.parse_journal(tmp_path / "nope.jsonl")
        assert rows == [] and bad == 0

    def test_rows_sorted_and_malformed_counted(self, tmp_path):
        p = tmp_path / "j.jsonl"
        p.write_text(
            json.dumps(_row("2026-08-04", 0.01)) + "\n"
            + "{not json\n"
            + json.dumps(_row("2026-08-03", None)) + "\n")
        rows, bad = predlab.parse_journal(p)
        assert [r["asof"] for r in rows] == ["2026-08-03", "2026-08-04"]
        assert bad == 1


class TestDeriveBook:
    def test_empty_rows_none(self):
        assert predlab.derive_book([], "vt15_b100_scale") is None

    def test_equity_compounds_skipping_null_returns(self):
        rows = [_row("2026-08-03", None), _row("2026-08-04", 0.10),
                _row("2026-08-05", None), _row("2026-08-06", -0.05)]
        d = predlab.derive_book(rows, "vt15_b100_scale")
        # anchor at first row, then one point per non-null return
        assert [p["ts"] for p in d["equity"]] == [
            "2026-08-03", "2026-08-04", "2026-08-06"]
        assert d["equity"][0]["value"] == 100.0
        assert d["equity"][1]["value"] == pytest.approx(110.0)
        assert d["equity"][2]["value"] == pytest.approx(104.5)
        assert d["cards"]["cum_return"] == pytest.approx(0.045)
        assert d["cards"]["warmup"] == {"n": 2, "required": 21}
        assert d["cards"]["n_days"] == 4
        assert d["cards"]["last_asof"] == "2026-08-06"

    def test_scale_and_cost_cards(self):
        rows = [_row("2026-08-03", None, scale=None),
                _row("2026-08-04", 0.01, scale=0.5)]
        d = predlab.derive_book(rows, "vt15_b100_scale")
        assert d["cards"]["scale"] == 0.5
        assert d["cards"]["cum_cost"] == pytest.approx(0.0001)
        assert d["cards"]["avg_turnover"] == pytest.approx(0.10)

    def test_drawdown_and_rolling_sharpe_shapes(self):
        rows = [_row("2026-08-03", None)] + [
            _row(f"2026-09-{i:02d}", 0.001 * (1 if i % 2 else -1))
            for i in range(1, 29)]
        d = predlab.derive_book(rows, "vt15_b100_scale")
        assert len(d["drawdown"]) == len(d["equity"])
        assert isinstance(d["rolling_sharpe"], list)  # may be empty < window


class TestBookDetail:
    def test_latest_row_split_and_delta(self):
        prev = _row("2026-08-03", None,
                    weights={"BTCUSDT": 0.025, "AKEUSDT": -0.025})
        cur = _row("2026-08-04", 0.01,
                   weights={"ETHUSDT": 0.025, "AKEUSDT": -0.025}, scale=0.4)
        d = predlab.book_detail([prev, cur], "vt15_b100_scale")
        assert d["asof"] == "2026-08-04"
        assert d["longs"] == [{"symbol": "ETHUSDT", "weight": 0.025}]
        assert d["shorts"] == [{"symbol": "AKEUSDT", "weight": -0.025}]
        assert d["delta"] == {"entered": 1, "exited": 1}
        assert d["scale"] == 0.4
        assert d["breadth"] == 200

    def test_single_row_has_null_delta(self):
        d = predlab.book_detail([_row("2026-08-03", None)], "vt15_b100_scale")
        assert d["delta"] is None

    def test_empty_none(self):
        assert predlab.book_detail([], "vt15_b100_scale") is None


class TestBookHealth:
    NOW = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)

    def test_fresh(self):
        rows = [_row("2026-08-04", 0.01)]
        h = predlab.book_health(rows, 0, self.NOW)
        assert h["stale"] is False and h["rows"] == 1 and h["malformed"] == 0

    def test_stale_after_36h(self):
        rows = [_row("2026-08-01", 0.01)]
        h = predlab.book_health(rows, 2, self.NOW)
        assert h["stale"] is True and h["malformed"] == 2

    def test_gaps_flag_known(self):
        rows = [_row("2026-07-30", None), _row("2026-08-03", 0.01)]
        h = predlab.book_health(rows, 0, self.NOW)
        gaps = {g["date"]: g["known"] for g in h["gaps"]}
        assert gaps == {"2026-07-31": True, "2026-08-01": True,
                        "2026-08-02": True}

    def test_empty_none(self):
        assert predlab.book_health([], 0, self.NOW) is None


class TestGateStatus:
    def test_with_reference(self):
        rows = [_row("2026-08-03", None), _row("2026-08-04", 0.01)]
        ref = {"dev_metrics": {"ovl_sr_full": 1.892}}
        g = predlab.gate_status(rows, ref, date(2026, 8, 6))
        assert g["window_start"] == "2026-07-02"
        assert g["earliest_eval"] == "2027-01-02"
        assert g["days_elapsed"] == 35
        assert g["days_remaining"] == 149
        assert g["threshold_sr"] == pytest.approx(0.946)
        assert g["informational"] is True
        assert g["running"]["n_returns"] == 1

    def test_without_reference_uses_fallback_threshold(self):
        g = predlab.gate_status([], None, date(2026, 8, 6))
        assert g["threshold_sr"] == pytest.approx(0.946)
        assert g["running"]["sr"] is None
