"""Invented signed-cashflow and margin examples only; no empirical reads."""
import copy
import importlib.util
import math
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11/carry_book.py"
spec = importlib.util.spec_from_file_location("carry_book", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def invented(price=100, rate=0, asset="ETH"):
    bars = [[module.START_MS + day * module.DAY_MS, price, price, price, price, "0",
             module.START_MS + (day + 1) * module.DAY_MS - 1, "0", 0, "0", "0", "0"] for day in range(91)]
    events = [{"symbol": asset + "USDT", "fundingTime": module.START_MS + index * module.DAY_MS // 3,
               "fundingRate": rate, "markPrice": price} for index in range(273)]
    return bars, copy.deepcopy(bars), copy.deepcopy(bars), events


def run(data=None, **kwargs):
    return module.book(*(data or invented()), asset=kwargs.pop("asset", "ETH"),
                       capital=kwargs.pop("capital", 1000), **kwargs)


def test_constant_prices_cash_reconciles_and_principal_returns():
    result = run()
    initial, ledger = result["initial"], result["final_ledger"]
    q = initial["quantity"]
    assert initial["spot_quantity"] == -initial["perp_quantity"] == q
    assert initial["futures_reserve"] == 500
    assert initial["idle_cash"] >= 100
    assert ledger["cash_profit"] == pytest.approx(-q * 100 * 4 * 0.0002 - ledger["all_fees"])
    assert ledger["cash_reconciliation_difference"] == pytest.approx(0, abs=1e-10)
    assert ledger["final_cash"] > 990  # Neither principal nor reserve disappears.
    assert ledger["terminal_spot_quantity"] == ledger["terminal_perp_quantity"] == 0
    assert result["daily_trace"][-1]["nav"] == ledger["final_cash"]
    assert result["metrics"]["cash_profit"] < 0
    assert result["metrics"]["max_drawdown"] > 0  # Initial C is included.


def test_signed_funding_and_first_event_exclusion():
    positive, negative, zero = run(invented(rate=0.001)), run(invented(rate=-0.001)), run()
    q = positive["initial"]["quantity"]
    expected = 272 * q * 100 * 0.001
    assert positive["metrics"]["funding_cash"] == pytest.approx(expected)
    assert negative["metrics"]["funding_cash"] == pytest.approx(-expected)
    assert positive["metrics"]["cash_profit"] - zero["metrics"]["cash_profit"] == pytest.approx(expected)
    assert negative["metrics"]["cash_profit"] - zero["metrics"]["cash_profit"] == pytest.approx(-expected)
    assert positive["metrics"]["applied_funding_events"] == 272
    assert positive["daily_trace"][0]["funding_event_count"] == 2


def test_exact_quantity_cancellation_on_shared_price_path():
    data = invented()
    for bars in data[:3]:
        for day, row in enumerate(bars):
            close = 100 + day * 3
            row[2], row[3], row[4] = max(100, close), min(100, close), close
    result = run(data)
    rows = result["daily_trace"]
    assert all(row["pre_exit_nav"] == pytest.approx(rows[0]["pre_exit_nav"]) for row in rows)
    assert all(row["net_base_quantity"] == row["net_market_notional"] == 0 for row in rows)
    # Fixed short quantities lose value linearly; no percentage-return drift proxy.
    q = result["initial"]["quantity"]
    assert rows[-1]["pre_exit_components"]["short_mtm"] - rows[0]["short_mtm"] == pytest.approx(-q * 270)
    assert result["metrics"]["margin_buffer_breach"] is True


def test_cost_stress_and_lot_capital_constraints():
    base, stress = run(), run(cost_scenario="stress")
    assert stress["metrics"]["cash_profit"] < base["metrics"]["cash_profit"]
    for asset, lot in (("BTC", 0.001), ("ETH", 0.01)):
        result = run(invented(asset=asset), asset=asset)
        q = result["initial"]["quantity"]
        assert q / lot == pytest.approx(round(q / lot))
        assert result["initial"]["idle_cash"] >= 100
    assert run(invented(price=1e9))["status"] == "unavailable"


def test_intraday_negative_funding_and_high_are_conservative():
    data = invented(rate=0.001)
    data[3][1]["fundingRate"] = -0.1
    data[2][0][2] = 250
    result = run(data)
    row, initial = result["daily_trace"][0], result["initial"]
    q = initial["quantity"]
    assert row["negative_funding_cash"] == pytest.approx(-q * 100 * 0.1)
    assert row["margin_wallet_lower_bound"] == pytest.approx(500 - q * 100 * 0.1)
    expected = 500 - q * 10 + q * (initial["perp_entry_price"] - 250) - 0.01 * q * 250
    assert row["margin_buffer_lower_bound"] == pytest.approx(expected)
    assert result["metrics"]["margin_buffer_breach"] is True


def test_half_double_price_stresses_keep_quantity_and_entry_fees():
    result = run()
    half, double = [result["quantity_price_stresses"][key] for key in ("half", "double")]
    q = result["initial"]["quantity"]
    assert half["quantity"] == double["quantity"] == q
    assert half["cash_profit"] < 0 and double["cash_profit"] < 0
    assert double["margin_buffer_lower_bound"] < half["margin_buffer_lower_bound"]
    assert half["cumulative_funding_cash"] == double["cumulative_funding_cash"] == 0
    assert half["idle_cash"] == result["initial"]["idle_cash"]


def test_log_shadow_is_not_cash_pnl_and_reconciles_index():
    result = run(invented(rate=0.001))
    diagnostic = result["convention_diagnostic"]
    assert "not cash PnL" in diagnostic["label"]
    assert diagnostic["all_days"] == diagnostic["valid_simple_index_days"] == 91
    assert diagnostic["log1p_sum"] == pytest.approx(math.log(result["final_ledger"]["final_cash"] / 1000))
    arithmetic = math.fsum(row["full_capital_daily_return"] for row in result["daily_trace"])
    assert diagnostic["arithmetic_daily_simple_return_sum"] == pytest.approx(arithmetic)
    assert diagnostic["log_sum_minus_arithmetic_daily_sum"] == pytest.approx(diagnostic["log1p_sum"] - arithmetic)
    assert result["metrics"]["annualized_simple_return_365"] == pytest.approx(result["metrics"]["full_capital_return"] * 365 / 91)


def test_zero_friction_constant_book_returns_every_dollar(monkeypatch):
    monkeypatch.setitem(module.COSTS, "base", {"spot_fee": 0.0, "perp_fee": 0.0, "slippage": 0.0})
    result = run()
    assert result["initial"]["quantity"] == 4
    assert result["final_ledger"]["final_cash"] == 1000
    assert result["final_ledger"]["cash_profit"] == 0
    assert all(row["nav"] == 1000 for row in result["daily_trace"])
    assert result["metrics"]["max_drawdown"] == 0


def test_nonpositive_nav_keeps_cash_loss_but_blocks_log_diagnostic():
    result = run(invented(rate=-1))
    assert result["final_ledger"]["final_cash"] < 0
    assert result["metrics"]["margin_buffer_breach"] is True
    assert result["convention_diagnostic"]["status"] == "unavailable"
    assert result["convention_diagnostic"]["log1p_sum"] is None
    assert result["final_ledger"]["cash_reconciliation_difference"] == pytest.approx(0, abs=1e-8)


def test_terminal_trace_cash_components_and_exposures_reconcile():
    result = run(invented(rate=0.001))
    row, ledger = result["daily_trace"][-1], result["final_ledger"]
    assert row["pre_exit_components"]["gross_market_notional"] > 0
    assert row["pre_exit_components"]["spot_quantity"] > 0
    assert row["pre_exit_components"]["nav"] == row["pre_exit_nav"]
    assert row["spot_quantity"] == row["perp_quantity"] == row["spot_value"] == row["short_mtm"] == 0
    assert row["gross_market_notional"] == row["net_market_notional"] == 0
    assert row["futures_wallet"] == ledger["futures_cash_after_close"]
    assert row["nav"] == pytest.approx(row["idle_cash"] + row["futures_wallet"] + row["short_mtm"] + row["spot_value"])
    assert row["nav"] == ledger["final_cash"]


@pytest.mark.parametrize("failure", ["missing_funding", "duplicate_funding", "nonfinite", "missing_bar"])
def test_unknown_inputs_fail_without_fill(failure):
    data = invented()
    if failure == "missing_funding":
        data[3].pop()
    elif failure == "duplicate_funding":
        data[3][1]["fundingTime"] = data[3][0]["fundingTime"]
    elif failure == "nonfinite":
        data[0][0][4] = float("nan")
    else:
        data[0].pop()
    with pytest.raises(ValueError):
        run(data)
