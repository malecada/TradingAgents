"""Invented wallet balances only; imports do not run a lifecycle or touch data."""
import importlib.util
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "research/broader-allocation-2026-09-15/custody_admission.py"
spec = importlib.util.spec_from_file_location("broader_custody_tested", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_literal_wallets_and_boundary():
    node = module.wallet_node(10000, "0.5", 1, "venue_bank")
    assert node["wallets"] == {"venue": "5000.0", "bank_1": "5000.0"}
    assert node["structural_custody_pass"] is True
    higher = module.wallet_node(10000, "0.5", 2, "venue_bank")
    assert higher["nav"] == "15000.0"
    assert higher["structural_custody_pass"] is False


def test_cash_bank_and_segregation_are_not_implicitly_safe():
    assert not module.wallet_node(10000, 0, 1, "single_venue")["structural_custody_pass"]
    assert not module.wallet_node(10000, 0, 1, "venue_bank")["structural_custody_pass"]
    assert module.wallet_node(10000, 0, 1, "venue_two_banks")["structural_custody_pass"]
    node = module.wallet_node(10000, ".25", 2, "venue_two_banks")
    assert node["wallets"] == {"venue": "5000.00", "bank_1": "3750.00", "bank_2": "3750.00"}
    assert node["maximum_custodian_loss_fraction"] == "0.4"


def test_market_loss_and_scale_invariance():
    first = module.wallet_node(10000, ".25", ".2", "venue_two_banks")
    second = module.wallet_node(100000, ".25", ".2", "venue_two_banks")
    assert first["market_loss_from_initial_fraction"] == "0.200"
    for field in ["maximum_custodian_loss_fraction", "crypto_exposure", "structural_custody_pass"]:
        assert first[field] == second[field]


@pytest.mark.parametrize("values", [(0,.25,1), (100,-.1,1), (100,1.1,1), (100,.25,0),
                                    (True,.25,1), (100,"NaN",1), (100,.25,"Infinity")])
def test_invalid_nodes(values):
    with pytest.raises(ValueError):
        module.wallet_node(*values, "venue_bank")


def test_complete_denominator_and_unknown_terms():
    result = module.evaluate({"capital": "10000", "weights": ["0", "0.25", "0.50", "1"],
                              "factors": ["1", "2", "0.2"], "architectures": list(module.ARCHITECTURES)})
    assert len(result["cells"]) == len({row["id"] for row in result["cells"]}) == 42
    assert sum(row["status"] == "unavailable" for row in result["cells"]) == 6
    assert result["implementation_admitted"] is False
    with pytest.raises(ValueError):
        module.evaluate({})
