"""Invented dated-futures quantities; no empirical observations or network."""
import importlib.util
import math
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11/dated_book.py"
spec = importlib.util.spec_from_file_location("dated_book", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def bars(count, interval, price=100):
    return [[module.START_MS + index * interval, price, price, price, price, 1,
             module.START_MS + (index + 1) * interval - 1, 100, 1, 0.5, 50, 0] for index in range(count)]


def invented():
    return bars(56, module.DAY_MS), bars(1344, module.HOUR_MS)


def run(data=None, **kwargs):
    return module.book(*(data or invented()), asset=kwargs.pop("asset", "ETH"),
                       capital=kwargs.pop("capital", 1000), **kwargs)


def test_constant_prices_cash_principal_and_friction_reconcile():
    result = run()
    initial, final = result["initial"], result["final_ledger"]
    q = initial["quantity"]
    assert final["final_cash"] > 990
    assert final["raw_basis_convergence"] == final["zero_friction_same_quantity_profit"] == 0
    assert final["slippage_cost"] == pytest.approx(q * 400 * 0.0002)
    assert final["cash_profit"] == pytest.approx(-final["slippage_cost"] - final["all_fees"])
    assert final["cash_reconciliation_difference"] == pytest.approx(0, abs=1e-10)
    assert initial["futures_reserve"] == 500 and initial["idle_cash"] >= 100
    assert initial["spot_quantity"] == -initial["future_quantity"]
    assert result["actual_margin_risk"]["status"] == "unavailable"


def test_raw_basis_gain_is_quantity_cash_not_compounded_spread():
    spot, future = invented()
    for index, row in enumerate(future):
        price = 110 - 10 * index / 1343
        row[1:5] = [price] * 4
    result = run((spot, future))
    final, q = result["final_ledger"], result["initial"]["quantity"]
    assert final["raw_basis_convergence"] == pytest.approx(q * 10)
    assert final["cash_profit"] == pytest.approx(q * 10 - final["slippage_cost"] - final["all_fees"])
    assert final["zero_friction_same_quantity_profit"] == final["raw_basis_convergence"]


def test_terminal_post_exit_trace_is_coherent():
    result = run()
    row = result["daily_trace"][-1]
    assert row["date"] == "2026-06-25"
    assert row["pre_exit_components"]["gross_market_notional"] > 0
    assert row["spot_value"] == row["short_mtm"] == row["gross_market_notional"] == 0
    assert row["spot_quantity"] == row["future_quantity"] == row["net_market_notional"] == 0
    assert row["nav"] == pytest.approx(row["idle_cash"] + row["futures_wallet"])
    assert row["nav"] == result["final_ledger"]["final_cash"]


def test_zero_friction_recovers_all_initial_cash(monkeypatch):
    monkeypatch.setitem(module.COSTS, "base", {"spot_fee": 0, "perp_fee": 0, "slippage": 0})
    result = run()
    assert result["final_ledger"]["final_cash"] == 1000
    assert result["metrics"]["cash_profit"] == result["metrics"]["max_drawdown"] == 0


def test_cost_and_price_stress_keep_literal_quantity():
    base, stress = run(), run(cost_scenario="stress")
    assert stress["metrics"]["cash_profit"] < base["metrics"]["cash_profit"]
    scenarios = base["quantity_price_stresses"]
    assert all(row["quantity"] == base["initial"]["quantity"] for row in scenarios.values())
    assert scenarios["double"]["trade_high_reserve_buffer_proxy"] < scenarios["half"]["trade_high_reserve_buffer_proxy"]
    assert all(row["cash_profit"] < 0 for row in scenarios.values())


@pytest.mark.parametrize("index", [0, -1])
def test_entry_exit_zero_activity_is_unavailable(index):
    data = invented()
    data[1][index][5] = 0
    assert run(data)["status"] == "unavailable"


def test_held_zero_activity_is_retained_not_filled_or_dropped():
    data = invented()
    data[1][15][5] = data[1][15][8] = 0
    result = run(data)
    assert result["status"] == "conditional"
    assert result["held_activity"]["all_hour_count"] == 1344
    assert result["held_activity"]["zero_volume_hour_count"] == 1
    assert result["held_activity"]["zero_trade_hour_count"] == 1
    assert len(result["daily_trace"]) == 56


def test_missing_hours_fail_closed():
    data = invented()
    data[1].pop(10)
    with pytest.raises(ValueError):
        run(data)


def test_negative_cash_kept_and_log_shadow_unavailable():
    data = invented()
    for row in data[1][24:]:
        row[1:5] = [1000] * 4
    result = run(data)
    assert result["metrics"]["cash_profit"] < -1000
    assert result["metrics"]["trade_high_proxy_breach"] is True
    assert result["actual_margin_risk"]["status"] == "unavailable"
    assert result["convention_diagnostic"]["status"] == "unavailable"
    assert result["final_ledger"]["cash_reconciliation_difference"] == pytest.approx(0, abs=1e-8)


def test_convention_sums_include_terminal_fees():
    result = run()
    diagnostic = result["convention_diagnostic"]
    assert diagnostic["log1p_sum"] == pytest.approx(math.log(result["final_ledger"]["final_cash"] / 1000))
    assert diagnostic["arithmetic_daily_simple_return_sum"] == pytest.approx(sum(row["full_capital_daily_return"] for row in result["daily_trace"]))
    assert diagnostic["all_days"] == diagnostic["valid_simple_index_days"] == 56
    assert result["metrics"]["annualized_simple_return_365"] == pytest.approx(result["metrics"]["full_capital_return"] * 365 / 56)


@pytest.mark.parametrize("endpoint", [0, -1])
@pytest.mark.parametrize("field", [5, 8])
def test_zero_activity_spot_endpoints_are_unavailable(endpoint, field):
    data = invented()
    data[0][endpoint][field] = 0
    assert run(data)["status"] == "unavailable"
