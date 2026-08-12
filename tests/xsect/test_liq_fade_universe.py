import pandas as pd
from tradingagents.xsect.liq_fade import monthly_top_n


def _daily(sym_vol: dict, start="2020-10-01", days=200):
    idx = pd.date_range(start, periods=days, freq="1D", tz="UTC", name="ts")
    return {s: pd.DataFrame({"close": 1.0, "quote_volume": float(v)}, index=idx)
            for s, v in sym_vol.items()}


def test_ranks_by_trailing_median_dollar_volume():
    d = _daily({"AAA": 100, "BBB": 300, "CCC": 200})
    sel = monthly_top_n(d, "2021-01-01", "2021-02-28", n=2)
    first = sel[pd.Timestamp("2021-01-01", tz="UTC")]
    assert first == ["BBB", "CCC"]


def test_young_symbol_excluded_until_min_age():
    d = _daily({"OLD": 100})
    young = _daily({"NEW": 999}, start="2020-12-20", days=100)
    d.update(young)  # NEW has <60d history before 2021-01-01
    sel = monthly_top_n(d, "2021-01-01", "2021-03-31", n=2)
    assert "NEW" not in sel[pd.Timestamp("2021-01-01", tz="UTC")]
    assert "NEW" in sel[pd.Timestamp("2021-03-01", tz="UTC")]


def test_no_lookahead_selection_ignores_future_volume():
    d = _daily({"AAA": 100, "BBB": 50})
    # BBB volume explodes AFTER Jan-1; Jan selection must not see it
    d["BBB"].loc["2021-01-05":, "quote_volume"] = 10_000.0
    sel = monthly_top_n(d, "2021-01-01", "2021-01-31", n=1)
    assert sel[pd.Timestamp("2021-01-01", tz="UTC")] == ["AAA"]
