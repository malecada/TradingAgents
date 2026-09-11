"""Synthetic-only saved-series diagnostic checks; no historical input access."""
import importlib.util
import math
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11/carry_definition.py"
spec = importlib.util.spec_from_file_location("carry_definition", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(rows=None):
    rows = rows or ["2024-01-01,-0.03,-0.01,-0.02", "2024-01-02,0.01,0.03,0.02"]
    raw = ("date,btc,eth,sleeve\n" + "\n".join(rows) + "\n").encode()
    costs = {"window": ["2024-01-01", "2024-01-03"], "annualization": "sqrt(252)",
             "cost_parameters": {"target_notional_per_leg": 1, "rf_daily": 0.06,
                                 "margin_fraction_of_perp_notional": 0.5},
             "stressed_blended_sr": 0.0}
    return raw, costs


def run(raw, costs):
    return module.diagnose(raw, costs, start="2024-01-01", end="2024-01-03")


def test_known_opportunity_cost_and_legacy_units():
    result = run(*fixture())
    assert result["daily_opportunity_cost_addback"] == 0.03
    assert result["series_denominator"] == ["btc", "eth", "sleeve"]
    for name in module.SERIES:
        cell = result["series"][name]
        assert cell["stressed"]["n"] == 2
        assert cell["opportunity_cost_addback"]["sum"] - cell["stressed"]["sum"] == pytest.approx(0.06)
    sleeve = result["series"]["sleeve"]
    assert sleeve["stressed"]["compounded_index_starting_at_one"] == pytest.approx(0.9996)
    assert sleeve["opportunity_cost_addback"]["compounded_index_starting_at_one"] == pytest.approx(1.0605)
    assert sleeve["opportunity_cost_addback"]["sr_sqrt252"] == pytest.approx(0.03 / math.sqrt(0.0008) * math.sqrt(252))
    assert sleeve["additive_sum_sign"] == {"stressed": "zero", "addback": "positive", "changed": True}
    assert result["saved_blended_sr_check"]["agrees"] is True
    assert all(result[name]["status"] == "unavailable" for name in ("cashflow_profit", "full_capital_returns", "market_beta"))


@pytest.mark.parametrize("rows", [
    ["2024-01-01,0,0,0"],
    ["2024-01-01,0,0,0", "2024-01-01,0,0,0"],
    ["2024-01-02,0,0,0", "2024-01-01,0,0,0"],
    ["2024-01-01T00:00:00+01:00,0,0,0", "2024-01-02,0,0,0"],
    ["2024-01-01,NaN,0,0", "2024-01-02,0,0,0"],
    ["2024-01-01,0,inf,0", "2024-01-02,0,0,0"],
    ["2024-01-01,0,0,0.1", "2024-01-02,0,0,0"],
])
def test_invalid_input_fails_closed(rows):
    with pytest.raises(ValueError):
        run(*fixture(rows))


def test_constant_pnl_has_no_fabricated_finite_sharpe():
    result = run(*fixture(["2024-01-01,0.01,0.01,0.01", "2024-01-02,0.01,0.01,0.01"]))
    for cell in result["series"].values():
        assert cell["stressed"]["sr_sqrt252"] is None
        assert cell["opportunity_cost_addback"]["sr_sqrt252"] is None
    assert result["saved_blended_sr_check"]["agrees"] is None


def test_convention_diagnostic_is_explicit_and_complete():
    result = run(*fixture())
    for cell in result["series"].values():
        for definition in ("stressed", "opportunity_cost_addback"):
            diagnostic = cell[definition]["convention_diagnostic"]
            assert diagnostic["all_days"] == diagnostic["valid_simple_index_days"] == 2
            assert "not cash PnL" in diagnostic["label"]
    diagnostic = result["series"]["sleeve"]["stressed"]["convention_diagnostic"]
    assert diagnostic["log1p_sum"] == pytest.approx(math.log(0.9996))


def test_invalid_simple_index_does_not_drop_bad_days():
    raw, costs = fixture(["2024-01-01,-1,-1,-1", "2024-01-02,0,0,0"])
    costs["stressed_blended_sr"] = -math.sqrt(126)
    result = run(raw, costs)
    cell = result["series"]["sleeve"]["stressed"]
    assert cell["sum"] == -1
    assert cell["compounded_index_starting_at_one"] is None
    assert cell["convention_diagnostic"]["invalid_simple_index_days"] == 1
    assert cell["convention_diagnostic"]["log1p_sum"] is None


def test_saved_sr_mismatch_and_cost_window_are_visible():
    raw, costs = fixture()
    costs["stressed_blended_sr"] = 1
    with pytest.raises(ValueError, match="SR disagreement"):
        run(raw, costs)
    costs["window"][1] = "2024-01-04"
    with pytest.raises(ValueError, match="window"):
        run(raw, costs)


@pytest.mark.parametrize("failure", ["window", "sr_mismatch", "sr_undefined"])
def test_cli_retains_all_six_cells_on_semantic_failure(monkeypatch, failure):
    raw, costs = fixture()
    if failure != "window":
        monkeypatch.setattr(module, "WINDOWS", {name: ("2024-01-01", "2024-01-03")
                                               for name in ("dev", "holdout")})
    if failure == "sr_mismatch":
        costs["stressed_blended_sr"] = 1.0
    if failure == "sr_undefined":
        raw, costs = fixture(["2024-01-01,0.01,0.01,0.01", "2024-01-02,0.01,0.01,0.01"])
    import json
    class FakeRun:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read_input(self, name):
            return raw if name.endswith("series") else json.dumps(costs).encode()

        def write_json(self, name, value):
            self.output = value

        def finish(self, cells):
            self.cells = cells

    fake = FakeRun()
    monkeypatch.setattr(module.ResearchRun, "start", lambda **kwargs: fake)
    monkeypatch.setattr("sys.argv", ["carry_definition.py", "--source", "a" * 40])
    module.main()
    assert len(fake.cells) == 6
    assert {cell["id"] for cell in fake.cells} == {
        f"{window}-{symbol}" for window in ("dev", "holdout") for symbol in module.SERIES}
    assert all(cell["status"] == "unavailable" and cell["reason"] for cell in fake.cells)
    assert all(result["status"] == "unavailable" for result in fake.output.values())
