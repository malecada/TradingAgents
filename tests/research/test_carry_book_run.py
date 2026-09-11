import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

DIRECTORY = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11"
for name in ("carry_book", "carry_statistics", "carry_book_run"):
    spec = importlib.util.spec_from_file_location(name, DIRECTORY / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
runner = sys.modules["carry_book_run"]


def invented_data():
    start, day = 1775001600000, 86400000
    result = {}
    for asset, price in (("btc", 10000), ("eth", 1000)):
        bars = [[start+i*day, str(price), str(price), str(price), str(price), "0",
                 start+(i+1)*day-1, "0", 0, "0", "0", "0"] for i in range(91)]
        for kind in ("spot", "perp", "mark"):
            result[f"{asset}-{kind}"] = bars
        result[f"{asset}-funding"] = [
            {"symbol": asset.upper()+"USDT", "fundingTime": start+i*day//3,
             "fundingRate": "0.001", "markPrice": str(price)} for i in range(273)]
    return result


def test_whole_frozen_pipeline_recovers_planted_cash_and_funding_off_null():
    books, summary, cells = runner.evaluate(invented_data())
    assert len(cells) == 16 and all(c["status"] == "complete" for c in cells)
    assert len(summary["cases"]) == 8
    for item in summary["cases"]:
        result = books["primary_books"][item["id"]]
        profit = result["metrics"]["cash_profit"]
        assert profit > 0
        assert item["zero_funding_cash_profit"] < 0
        assert profit-item["zero_funding_cash_profit"] == pytest.approx(result["metrics"]["funding_cash"])
        assert item["market_exposure"]["status"] == "unavailable"
        assert not item["all_necessary_conditional_screens_pass"]
        daily = np.diff([result["capital"], *[r["nav"] for r in result["daily_trace"]]]) / result["capital"]
        assert daily.sum() == pytest.approx(result["metrics"]["full_capital_return"])


def test_missing_asset_events_preserves_denominator_and_paired_uncertainty_unavailable():
    data = invented_data()
    data["btc-funding"] = data["btc-funding"][:-1]
    books, summary, cells = runner.evaluate(data)
    assert len(cells) == 16
    assert sum(c["status"] == "unavailable" for c in cells) == 8
    for item in summary["cases"]:
        if item["status"] == "conditional":
            assert item["uncertainty"]["status"] == "unavailable"
            assert not item["all_necessary_conditional_screens_pass"]
