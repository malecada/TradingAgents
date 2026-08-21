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
