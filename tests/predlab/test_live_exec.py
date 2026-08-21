import math
import pytest

from tradingagents.predlab.live_exec import SymbolFilter, build_targets

F = {
    "AAAUSDT": SymbolFilter(min_notional=5.0, step_size=1.0),
    "BTCUSDT": SymbolFilter(min_notional=50.0, step_size=0.001),
    "BBBUSDT": SymbolFilter(min_notional=20.0, step_size=0.1),
}
MARKS = {"AAAUSDT": 2.0, "BTCUSDT": 73450.0, "BBBUSDT": 10.0}


class TestBuildTargets:
    def test_basic_sizing_rounds_down_to_step(self):
        # leg target = 0.025 * 1.0 * 4000 = 100 USDT -> 50 units of AAA, step 1.0
        tq, dropped = build_targets({"AAAUSDT": 0.025}, 1.0, 4000.0, MARKS, F)
        assert tq == {"AAAUSDT": 50.0}
        assert dropped == []

    def test_short_leg_negative_qty(self):
        tq, _ = build_targets({"AAAUSDT": -0.025}, 1.0, 4000.0, MARKS, F)
        assert tq == {"AAAUSDT": -50.0}

    def test_scale_multiplies(self):
        tq, _ = build_targets({"AAAUSDT": 0.025}, 2.0, 4000.0, MARKS, F)
        assert tq == {"AAAUSDT": 100.0}

    def test_drop_below_min_notional(self):
        # target = 0.025 * 400 = 10 < 20 min notional
        tq, dropped = build_targets({"BBBUSDT": 0.025}, 1.0, 400.0, MARKS, F)
        assert tq == {}
        assert dropped[0]["symbol"] == "BBBUSDT"
        assert dropped[0]["reason"] == "min_notional"

    def test_drop_rounds_to_zero(self):
        # BTC target = 0.025 * 2000 = 50 USDT >= min_notional 50,
        # but qty 50/73450 = 0.00068 rounds down to 0 at step 0.001
        tq, dropped = build_targets({"BTCUSDT": 0.025}, 1.0, 2000.0, MARKS, F)
        assert tq == {}
        assert dropped[0]["reason"] == "rounds_to_zero"

    def test_btc_clears_at_3k(self):
        # target = 75 USDT -> qty 0.001021 -> rounds to 0.001 (= 73.45 USDT >= 50)
        tq, dropped = build_targets({"BTCUSDT": 0.025}, 1.0, 3000.0, MARKS, F)
        assert tq == {"BTCUSDT": 0.001}
        assert dropped == []

    def test_missing_mark_dropped(self):
        tq, dropped = build_targets({"ZZZUSDT": 0.025}, 1.0, 4000.0, MARKS, F)
        assert tq == {}
        assert dropped[0]["reason"] == "no_mark"

    def test_missing_filter_dropped(self):
        marks = dict(MARKS, ZZZUSDT=1.0)
        tq, dropped = build_targets({"ZZZUSDT": 0.025}, 1.0, 4000.0, marks, F)
        assert dropped[0]["reason"] == "no_filter"

    def test_step_rounding_no_float_dust(self):
        # 0.1 step must not produce 0.30000000000000004
        f = {"CCCUSDT": SymbolFilter(5.0, 0.1)}
        tq, _ = build_targets({"CCCUSDT": 0.025}, 1.0, 1400.0, {"CCCUSDT": 100.0}, f)
        assert tq == {"CCCUSDT": 0.3}


from tradingagents.predlab.live_exec import Order, diff_orders


class TestDiffOrders:
    def test_open_new_long(self):
        orders, skipped = diff_orders({"AAAUSDT": 50.0}, {}, MARKS, F)
        assert orders == [Order("AAAUSDT", "BUY", 50.0, False)]
        assert skipped == []

    def test_open_new_short(self):
        orders, _ = diff_orders({"AAAUSDT": -50.0}, {}, MARKS, F)
        assert orders == [Order("AAAUSDT", "SELL", 50.0, False)]

    def test_no_change_no_order(self):
        orders, skipped = diff_orders({"AAAUSDT": 50.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [] and skipped == []

    def test_partial_reduce_is_reduce_only(self):
        orders, _ = diff_orders({"AAAUSDT": 30.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [Order("AAAUSDT", "SELL", 20.0, True)]

    def test_close_missing_target_reduce_only(self):
        orders, _ = diff_orders({}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [Order("AAAUSDT", "SELL", 50.0, True)]

    def test_sign_flip_single_crossing_order_not_reduce_only(self):
        # long 50 -> short 40: one SELL 90, cannot be reduceOnly
        orders, _ = diff_orders({"AAAUSDT": -40.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [Order("AAAUSDT", "SELL", 90.0, False)]

    def test_dust_delta_skipped(self):
        # delta 3 units * 2.0 = 6 USDT < 7 dust threshold
        orders, skipped = diff_orders({"AAAUSDT": 53.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == []
        assert skipped[0]["reason"] == "dust"

    def test_small_reduce_below_dust_skipped(self):
        orders, skipped = diff_orders({"AAAUSDT": 48.0}, {"AAAUSDT": 50.0}, MARKS, F)
        assert orders == [] and skipped[0]["reason"] == "dust"

    def test_increase_below_min_notional_skipped(self):
        # BBB delta 1.5 * 10 = 15 USDT >= dust but < min_notional 20, increasing
        orders, skipped = diff_orders({"BBBUSDT": 6.5}, {"BBBUSDT": 5.0}, MARKS, F)
        assert orders == []
        assert skipped[0]["reason"] == "increase_below_min_notional"

    def test_reduce_below_min_notional_still_sent(self):
        # reduce-only orders are exempt from MIN_NOTIONAL (-4164)
        orders, _ = diff_orders({"BBBUSDT": 5.0}, {"BBBUSDT": 6.5}, MARKS, F)
        assert orders == [Order("BBBUSDT", "SELL", 1.5, True)]

    def test_reduce_only_orders_sorted_first(self):
        orders, _ = diff_orders(
            {"AAAUSDT": 50.0}, {"BBBUSDT": 10.0}, MARKS, F)
        assert [o.reduce_only for o in orders] == [True, False]

    def test_delta_rounded_to_step(self):
        # BTC: current 0.002, target 0.0035 -> delta 0.0015 rounds to 0.001
        orders, _ = diff_orders({"BTCUSDT": 0.0035}, {"BTCUSDT": 0.002},
                                MARKS, F, dust_usd=7.0)
        assert orders == [Order("BTCUSDT", "BUY", 0.001, False)]

    # -- C1: zombie positions (symbol departed the champion book) ----------

    def test_departed_symbol_closed_reduce_only_even_without_mark(self):
        # AAAUSDT held (37 units) but no longer in targets AND no longer in
        # marks (paper trader only writes mark_px for today's book) -> must
        # still be closed, bypassing the mark/dust/min-notional checks.
        marks_no_aaa = {"BBBUSDT": 10.0}
        orders, skipped = diff_orders({}, {"AAAUSDT": 37.0}, marks_no_aaa, F)
        assert orders == [Order("AAAUSDT", "SELL", 37.0, True)]
        assert skipped == []

    def test_departed_symbol_short_closed_reduce_only_without_mark(self):
        marks_no_aaa = {"BBBUSDT": 10.0}
        orders, _ = diff_orders({}, {"AAAUSDT": -12.0}, marks_no_aaa, F)
        assert orders == [Order("AAAUSDT", "BUY", 12.0, True)]

    def test_departed_symbol_closed_bypasses_dust_threshold(self):
        # 1 unit * 2.0 = 2 USDT, well below the 7 USDT dust floor -- a close
        # must never be dropped for size.
        marks_no_aaa = {"BBBUSDT": 10.0}
        orders, skipped = diff_orders({}, {"AAAUSDT": 1.0}, marks_no_aaa, F)
        assert orders == [Order("AAAUSDT", "SELL", 1.0, True)]
        assert skipped == []

    def test_nonzero_target_no_mark_skipped_with_reason(self):
        # ZZZUSDT has a live target but the mark is missing this run:
        # cannot size the delta -> skip, logged (not silently dropped).
        f = dict(F, ZZZUSDT=SymbolFilter(5.0, 1.0))
        orders, skipped = diff_orders({"ZZZUSDT": 50.0}, {}, MARKS, f)
        assert orders == []
        assert skipped == [{"symbol": "ZZZUSDT", "reason": "no_mark"}]

    def test_departing_position_no_filter_skipped_with_reason(self):
        # Symbol held but delisted/non-TRADING (missing from filters) ->
        # cannot be market-ordered; must be closed manually.
        marks = dict(MARKS, ZZZUSDT=1.0)
        orders, skipped = diff_orders({}, {"ZZZUSDT": 10.0}, marks, F)
        assert orders == []
        assert skipped == [{"symbol": "ZZZUSDT", "reason": "no_filter"}]

    def test_target_no_filter_skipped_with_reason(self):
        marks = dict(MARKS, ZZZUSDT=1.0)
        orders, skipped = diff_orders({"ZZZUSDT": 10.0}, {}, marks, F)
        assert orders == []
        assert skipped == [{"symbol": "ZZZUSDT", "reason": "no_filter"}]


from tradingagents.predlab.live_exec import (
    build_journal_row, check_caps, daily_loss_breached)


class TestRiskAndJournal:
    def test_caps_ok(self):
        tn = {"AAAUSDT": 3000.0, "BBBUSDT": -3000.0}
        assert check_caps(tn, equity=3000.0, per_symbol_cap=1.0) == []

    def test_gross_cap_violation(self):
        tn = {"AAAUSDT": 4000.0, "BBBUSDT": -3000.0}
        v = check_caps(tn, equity=3000.0, per_symbol_cap=1.0)
        assert any("gross" in s for s in v)

    def test_per_symbol_cap_violation(self):
        tn = {"AAAUSDT": 400.0, "BBBUSDT": -100.0,
              "CCCUSDT": 100.0, "DDDUSDT": -100.0}
        v = check_caps(tn, equity=3000.0)
        assert any("AAAUSDT" in s for s in v)

    def test_empty_book_no_violations(self):
        assert check_caps({}, equity=3000.0) == []

    def test_daily_loss(self):
        assert daily_loss_breached(2849.0, 3000.0) is True
        assert daily_loss_breached(2851.0, 3000.0) is False

    def test_journal_row_schema(self):
        row = build_journal_row(
            asof="2026-08-22", executed_utc="2026-08-23T00:07:00+00:00",
            equity_before=3000.0, equity_day_start=3010.0, scale=1.2,
            targets_notional={"AAAUSDT": 90.0, "BBBUSDT": -90.0},
            orders=[Order("AAAUSDT", "BUY", 45.0, False)],
            dropped=[{"symbol": "BTCUSDT", "reason": "rounds_to_zero",
                      "target_notional": 50.0}],
            skipped=[{"symbol": "CCCUSDT", "reason": "dust",
                      "delta_notional": 6.0}],
            halt=False, dry_run=True)
        assert row["asof"] == "2026-08-22"
        assert row["orders_placed"] == 1
        assert row["gross_target"] == 180.0
        assert row["legs_dropped_min_notional"] == [
            {"symbol": "BTCUSDT", "reason": "rounds_to_zero",
             "target_notional": 50.0}]
        assert row["deltas_skipped_dust"] == 1
        assert row["dry_run"] is True and row["halt"] is False
        assert row["scale"] == 1.2 and row["equity_day_start"] == 3010.0

    def test_journal_row_scale_raw_defaults_to_scale(self):
        row = build_journal_row(
            asof="2026-08-22", executed_utc="2026-08-23T00:07:00+00:00",
            equity_before=3000.0, equity_day_start=3010.0, scale=1.1,
            targets_notional={}, orders=[], dropped=[], skipped=[],
            halt=False, dry_run=True)
        assert row["scale_raw"] == 1.1

    def test_journal_row_scale_raw_explicit(self):
        # C2: executed (clamped) scale vs the raw overlay scale from the
        # champion journal -- both must be recoverable from the live row.
        row = build_journal_row(
            asof="2026-08-22", executed_utc="2026-08-23T00:07:00+00:00",
            equity_before=3000.0, equity_day_start=3010.0, scale=1.1,
            targets_notional={}, orders=[], dropped=[], skipped=[],
            halt=False, dry_run=True, scale_raw=2.0)
        assert row["scale"] == 1.1 and row["scale_raw"] == 2.0
