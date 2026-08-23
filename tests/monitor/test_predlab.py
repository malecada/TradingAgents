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


class TestSlippage:
    """(mark - close) per day: what the close-to-close fill assumption costs."""

    def test_none_when_no_row_carries_a_mark_return(self):
        rows = [_row("2026-08-03", None), _row("2026-08-04", 0.01)]
        assert predlab.derive_book(rows, "vt15_b100_scale")["slippage"] is None

    def test_mean_and_cumulative_reported_in_basis_points(self):
        rows = [_row("2026-08-03", None, realized_mark_ret=None),
                _row("2026-08-04", 0.0100, realized_mark_ret=0.0105),
                _row("2026-08-05", 0.0200, realized_mark_ret=0.0190)]
        s = predlab.derive_book(rows, "vt15_b100_scale")["slippage"]
        assert s["n"] == 2
        assert s["cum_bps"] == pytest.approx(-5.0)   # +5 then -10
        assert s["mean_bps"] == pytest.approx(-2.5)

    def test_last_pair_carries_both_legs(self):
        rows = [_row("2026-08-04", 0.0100, realized_mark_ret=0.0105)]
        s = predlab.derive_book(rows, "vt15_b100_scale")["slippage"]
        assert s["last"] == {"asof": "2026-08-04", "close_ret": 0.0100,
                             "mark_ret": 0.0105, "bps": pytest.approx(5.0)}

    def test_days_missing_either_leg_are_not_paired(self):
        rows = [_row("2026-08-04", None, realized_mark_ret=0.01),
                _row("2026-08-05", 0.01, realized_mark_ret=None),
                _row("2026-08-06", 0.0100, realized_mark_ret=0.0102)]
        s = predlab.derive_book(rows, "vt15_b100_scale")["slippage"]
        assert s["n"] == 1
        assert s["last"]["asof"] == "2026-08-06"


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


class TestDeriveNav:
    """NAV = 100 x prod(1 + scale_prev_t x ret_t); scale_prev is the
    PREVIOUS row's scale — the value known when the position was put on."""

    def test_empty_rows_none(self):
        assert predlab.derive_nav([], "vt15_b100_scale") is None

    def test_all_null_scales_stays_flat(self):
        rows = [_row("2026-08-03", None), _row("2026-08-04", 0.01),
                _row("2026-08-05", -0.02)]
        d = predlab.derive_nav(rows, "vt15_b100_scale")
        assert [p["value"] for p in d["series"]] == [100.0, 100.0, 100.0]
        assert d["cards"]["nav_cum_return"] is None
        assert d["cards"]["active_days"] == 0
        assert d["cards"]["warmup"] == {"n": 0, "required": 21}
        assert d["cards"]["last_scale"] is None

    def test_scale_set_on_row_n_first_affects_row_n_plus_1(self):
        # R0 anchor; R1 ret uses R0's scale (None) -> flat; R2 sets scale=0.5
        # but R2's OWN ret still uses R1's scale (None) -> flat; R3's ret
        # uses R2's scale (0.5) -> active, first affected row.
        rows = [_row("2026-08-03", None),
                _row("2026-08-04", 0.01, scale=None),
                _row("2026-08-05", 0.02, scale=0.5),
                _row("2026-08-06", 0.10, scale=0.5)]
        d = predlab.derive_nav(rows, "vt15_b100_scale")
        vals = [p["value"] for p in d["series"]]
        assert vals == [100.0, 100.0, 100.0, pytest.approx(105.0)]
        assert d["cards"]["active_days"] == 1
        assert d["cards"]["nav_cum_return"] == pytest.approx(0.05)
        assert d["cards"]["last_scale"] == 0.5
        assert d["cards"]["warmup"] == {"n": 2, "required": 21}

    def test_mixed_null_gap_mid_stream_is_flat_day(self):
        # R2 is a null-return gap whose own scale reverts to None; R3's
        # return must see prev_scale=None (from R2), not R1's 0.5.
        rows = [_row("2026-08-03", None),
                _row("2026-08-04", 0.05, scale=0.5),
                _row("2026-08-05", None, scale=None),
                _row("2026-08-06", 0.10, scale=0.4)]
        d = predlab.derive_nav(rows, "vt15_b100_scale")
        # gap row (2026-08-05) contributes no point (null return)
        assert [p["ts"] for p in d["series"]] == [
            "2026-08-03", "2026-08-04", "2026-08-06"]
        vals = [p["value"] for p in d["series"]]
        assert vals == [100.0, 100.0, 100.0]  # flat throughout
        assert d["cards"]["active_days"] == 0
        assert d["cards"]["nav_cum_return"] is None
        assert d["cards"]["last_scale"] == 0.4


class TestDeriveAccount:
    def test_empty_rows_none(self):
        assert predlab.derive_account([], False) is None

    def test_two_rows_correct_pct(self):
        rows = [{"asof": "2026-08-20", "equity_before": 1000.0,
                 "orders_placed": 2, "dry_run": False},
                {"asof": "2026-08-21", "equity_before": 1050.0,
                 "orders_placed": 3, "dry_run": True}]
        d = predlab.derive_account(rows, False)
        assert [p["value"] for p in d["series"]] == [100.0, pytest.approx(105.0)]
        assert d["cards"]["cum_return"] == pytest.approx(0.05)
        assert d["cards"]["equity"] == 1050.0
        assert d["cards"]["n_cycles"] == 2
        assert d["cards"]["orders_total"] == 5
        assert d["cards"]["last_asof"] == "2026-08-21"
        assert d["cards"]["dry_run_last"] is True
        assert d["cards"]["halted"] is False

    def test_halted_flag_propagates(self):
        rows = [{"asof": "2026-08-20", "equity_before": 1000.0}]
        d = predlab.derive_account(rows, True)
        assert d["cards"]["halted"] is True

    def test_rows_missing_equity_before_skipped(self):
        rows = [{"asof": "2026-08-20", "equity_before": 1000.0},
                {"asof": "2026-08-21"},
                {"asof": "2026-08-22", "equity_before": 1100.0}]
        d = predlab.derive_account(rows, False)
        assert len(d["series"]) == 2
        assert d["cards"]["cum_return"] == pytest.approx(0.10)
        assert d["cards"]["n_cycles"] == 3

    def test_all_rows_missing_equity_before_none(self):
        rows = [{"asof": "2026-08-20"}, {"asof": "2026-08-21"}]
        assert predlab.derive_account(rows, False) is None


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
