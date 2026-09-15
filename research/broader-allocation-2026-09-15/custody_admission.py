"""Frozen synthetic wallet concentration; no market arrays or network."""
from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path

from tradingagents.research import ResearchRun

EXPERIMENT = "allocation-custody-20260915"
REGISTRATION = "research/broader-allocation-2026-09-15/gates-custody.json"
ARCHITECTURES = ("single_venue", "venue_bank", "venue_two_banks")
UNKNOWN_TERMS = ("account-eligibility", "cash-vehicle", "custody-recovery",
                 "transfer-prefund", "fees-fx", "execution-depth")


def number(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a balance")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("nonfinite balance")
    return result


def wallet_node(capital, weight, price_factor, architecture):
    capital, weight, factor = map(number, (capital, weight, price_factor))
    if capital <= 0 or not 0 <= weight <= 1 or factor <= 0:
        raise ValueError("invalid capital, fraction or price factor")
    if architecture not in ARCHITECTURES:
        raise ValueError("unknown wallet architecture")
    crypto = capital * weight * factor
    cash = capital * (1 - weight)
    if architecture == "single_venue":
        wallets = {"venue": crypto + cash}
    elif architecture == "venue_bank":
        wallets = {"venue": crypto, "bank_1": cash}
    else:
        wallets = {"venue": crypto, "bank_1": cash / 2, "bank_2": cash / 2}
    nav = crypto + cash
    largest = max(wallets.values())
    return {"capital": str(capital), "initial_crypto_fraction": str(weight),
            "price_factor": str(factor), "architecture": architecture,
            "wallets": {key: str(value) for key, value in wallets.items()},
            "nav": str(nav), "crypto_exposure": str(crypto / nav),
            "maximum_custodian_loss_fraction": str(largest / nav),
            "market_loss_from_initial_fraction": str((capital - nav) / capital),
            "structural_custody_pass": largest <= nav * Decimal("0.50")}


def evaluate(spec):
    if spec != {"capital": "10000", "weights": ["0", "0.25", "0.50", "1"],
                "factors": ["1", "2", "0.2"], "architectures": list(ARCHITECTURES)}:
        raise ValueError("unregistered synthetic specification")
    rows = []
    for architecture in spec["architectures"]:
        for weight in spec["weights"]:
            for factor in spec["factors"]:
                rows.append({"id": f"{architecture}-w{weight}-p{factor}", "status": "complete",
                             **wallet_node(spec["capital"], weight, factor, architecture)})
    rows.extend({"id": key, "status": "unavailable",
                 "reason": "Not established for the intended real account; no zero-cost or recovery assumption."}
                for key in UNKNOWN_TERMS)
    return {"scope": "Invented structural wallet nodes only; no economic strategy pass.",
            "implementation_admitted": False, "custody_comparison_is_adoption_gate": False,
            "accepted_exchange_failure_tail": "Potential100% loss reported separately; market/stablecoin stress limit50%.",
            "cells": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2], registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as run:
        run.read_input("ancestry")
        result = evaluate(json.loads(run.read_input("spec")))
        encoded = json.dumps(result, allow_nan=False).encode()
        if len(encoded) > 1024 * 1024:
            raise ValueError("output bound exceeded")
        run.write_json("custody.json", result)
        run.finish([{key: row[key] for key in ("id", "status", "reason") if key in row}
                    for row in result["cells"]])


if __name__ == "__main__":
    main()
