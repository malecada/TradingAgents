"""Invented prices and quantities only; no actual quotes or network."""
import importlib.util
import math
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11/triangle_bound.py"
spec = importlib.util.spec_from_file_location("triangle_bound", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def quotes():
    return {symbol: {"bidPrice": price, "askPrice": price, "bidQty": 1e8, "askQty": 1e8}
            for symbol, price in (("BTCUSDT", 100), ("ETHUSDT", 10), ("ETHBTC", .1))}


def test_planted_parity_and_three_received_asset_fees():
    result = module.evaluate(quotes())
    assert len(result["cells"]) == result["case_count"] == 8
    assert all(row["status"] == "complete" for row in result["cells"])
    for case in result["cases"].values():
        capital, fee = case["initial_capital_usdt"], case["received_asset_fee_rate_per_leg"]
        assert case["gross_roundtrip_factor"] == pytest.approx(1)
        assert case["terminal_usdt"] == pytest.approx(capital * (1 - fee)**3)
        assert case["cash_profit_usdt"] == pytest.approx(capital * ((1 - fee)**3 - 1))
        assert case["three_fees_terminal_usdt_equivalent"] == pytest.approx(capital - case["terminal_usdt"])
        assert case["graduation"] is False


def test_positive_gross_cycle_erased_by_three_fees():
    data = quotes()
    data["ETHUSDT"]["bidPrice"] = data["ETHUSDT"]["askPrice"] = 10.02
    result = module.evaluate(data)["cases"]
    gross, net = result["btc-eth-1000-zero-fee"], result["btc-eth-1000-10bp"]
    assert gross["cash_profit_usdt"] > 0 and net["cash_profit_usdt"] < 0
    assert net["necessary_after_10bp_screen"]["positive"] is False


def test_reverse_direction_conversion_units_and_wallet_conservation():
    result = module.evaluate(quotes())["cases"]
    reverse = result["eth-btc-1000-zero-fee"]
    assert reverse["currency_path"] == ["USDT", "ETH", "BTC", "USDT"]
    assert [row["acquired_gross_quantity"] for row in reverse["trace"]] == pytest.approx([100, 10, 1000])
    for case in result.values():
        for row in case["trace"]:
            for asset, before in row["wallets_before"].items():
                assert before + row["signed_currency_flows"][asset] == pytest.approx(row["wallets_after"][asset])
            assert row["acquired_gross_quantity"] - row["fee_quantity"] == pytest.approx(row["acquired_net_quantity"])
            assert row["fee_asset"] == row["acquired_asset"]
        assert case["terminal_wallets"]["BTC"] == case["terminal_wallets"]["ETH"] == 0
        assert all(abs(value) < 1e-8 for value in case["currency_flow_reconciliation"].values())


def test_size_insufficiency_remains_a_conditional_proxy():
    data = quotes()
    data["BTCUSDT"]["askQty"] = .00001
    result = module.evaluate(data)
    case = result["cases"]["btc-eth-1000-10bp"]
    assert case["status"] == "conditional_full_notional_proxy"
    assert case["all_displayed_best_sizes_sufficient"] is False
    assert case["trace"][0]["executed_base_quantity_before_fee"] == 10
    assert case["trace"][0]["displayed_best_size_sufficient"] is False
    assert case["execution"]["status"] == "unavailable"
    assert len(result["cells"]) == 8


@pytest.mark.parametrize("failure", ["missing", "crossed", "nonfinite", "zero_size", "boolean"])
def test_bad_inputs_preserve_all_eight_unavailable_cells(failure):
    data = quotes()
    if failure == "missing":
        data.pop("ETHBTC")
    elif failure == "crossed":
        data["ETHBTC"]["bidPrice"] = .2
    elif failure == "nonfinite":
        data["BTCUSDT"]["askPrice"] = float("inf")
    elif failure == "zero_size":
        data["BTCUSDT"]["bidQty"] = 0
    else:
        data["ETHUSDT"]["bidQty"] = True
    result = module.evaluate(data)
    assert len(result["cells"]) == 8
    assert all(row["status"] == "unavailable" for row in result["cells"])


def test_log_shadow_is_distinct_from_actual_cash_and_no_graduation():
    data = quotes()
    data["ETHUSDT"]["bidPrice"] = data["ETHUSDT"]["askPrice"] = 12
    case = module.evaluate(data)["cases"]["btc-eth-1000-10bp"]
    diagnostic = case["convention_diagnostic"]
    assert diagnostic["capital_times_log_factor_usdt"] == pytest.approx(1000 * math.log(case["after_fee_roundtrip_factor"]))
    assert diagnostic["capital_times_log_factor_usdt"] != pytest.approx(case["cash_profit_usdt"])
    assert case["necessary_after_10bp_screen"]["positive"] is True
    assert case["graduation"] is False
