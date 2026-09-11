"""Registered conditional cash book on captured spent-quarter data; no network."""
from __future__ import annotations

import argparse
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import numpy as np

from tradingagents.research import ResearchRun
from carry_book import book
from carry_statistics import market_exposure, paired_uncertainty

REGISTRATION = "research/strategy-search-2026-09-11/gates-book.json"
EXPERIMENT = "carry-book-20260911"
CASES = [(asset, capital, cost) for asset in ("BTC", "ETH")
         for capital in (1000, 10000) for cost in ("base", "stress")]


def case_id(asset, capital, cost):
    return f"{asset.lower()}-{capital}-{cost}"


def decode_inputs(capture, admission):
    expected = {f"{a}-{k}" for a in ("btc", "eth") for k in ("funding", "spot", "perp", "mark")} | {"exchange-info", "server-time"}
    records = capture["requests"]
    if len(records) != 10 or {r["id"] for r in records} != expected:
        raise ValueError("capture request denominator mismatch")
    admitted = admission["cells"]
    if len(admitted) != 10 or {r["id"] for r in admitted} != expected or any(r["status"] != "complete" for r in admitted):
        raise ValueError("all ten captured source cells must be admitted")
    decoded = {}
    for record in records:
        raw = base64.b64decode(record["body_base64"], validate=True)
        if len(raw) != record["body_bytes"] or hashlib.sha256(raw).hexdigest() != record["body_sha256"]:
            raise ValueError("raw captured body hash mismatch")
        if record["http_status"] != 200 or not record["body_complete"] or record["error"]:
            raise ValueError("captured source response is incomplete")
        decoded[record["id"]] = json.loads(raw)
    return decoded


def spot_returns(rows):
    closes = np.asarray([float(row[4]) for row in rows])
    previous = np.r_[float(rows[0][1]), closes[:-1]]
    return closes / previous - 1


def evaluate(data):
    results, counterfactuals, cells = {}, {}, []
    for asset, capital, cost in CASES:
        identifier, prefix = case_id(asset, capital, cost), asset.lower()
        try:
            result = book(data[f"{prefix}-spot"], data[f"{prefix}-perp"], data[f"{prefix}-mark"],
                          data[f"{prefix}-funding"], asset=asset, capital=capital, cost_scenario=cost)
            no_funding = deepcopy(data[f"{prefix}-funding"])
            for event in no_funding:
                event["fundingRate"] = "0"
            counter = book(data[f"{prefix}-spot"], data[f"{prefix}-perp"], data[f"{prefix}-mark"],
                           no_funding, asset=asset, capital=capital, cost_scenario=cost)
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            result = {"status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc)}
            counter = dict(result)
        results[identifier], counterfactuals[identifier] = result, counter
        for name, value in ((identifier, result), (identifier + "-zero-funding", counter)):
            cells.append({"id": name, "status": "unavailable" if value["status"] == "unavailable" else "complete",
                          **({"reason": value["reason"]} if value["status"] == "unavailable" else
                             {"qualification": "conditional development; not validated or actual fills"})})
    all_complete = all(value["status"] == "conditional" for value in results.values())
    if all_complete:
        changes = [np.diff(np.r_[capital, [r["nav"] for r in results[case_id(asset, capital, cost)]["daily_trace"]]]) / capital
                   for asset, capital, cost in CASES]
        uncertainties = paired_uncertainty(changes)
        btc, eth = spot_returns(data["btc-spot"]), spot_returns(data["eth-spot"])
    summaries = []
    for index, (asset, capital, cost) in enumerate(CASES):
        identifier = case_id(asset, capital, cost)
        result = results[identifier]
        if result["status"] != "conditional":
            summaries.append({"id": identifier, **result})
            continue
        uncertainty = uncertainties[index] if all_complete else {"status": "unavailable", "reason": "paired eight-case denominator incomplete"}
        exposure = market_exposure([r["nav"] for r in result["daily_trace"]], capital, btc, eth) if all_complete else {"status": "unavailable"}
        m, final = result["metrics"], result["final_ledger"]
        beta_ok = exposure["status"] == "complete" and all(
            abs(exposure[f"{asset}_beta"]) <= .1 and exposure[f"{asset}_interval"][0] >= -.2 and exposure[f"{asset}_interval"][1] <= .2
            for asset in ("btc", "eth"))
        pieces = {
            "annualized_cash_at_least_3pct": m["annualized_simple_return_365"] >= .03,
            "exploratory_simultaneous_cash_lower_positive": all_complete and uncertainty["annualized_lower"] > 0,
            "beta_point_and_interval_screen": beta_ok,
            "max_drawdown_at_most_10pct": m["max_drawdown"] <= .1,
            "conditional_daily_margin_buffer_nonnegative": m["minimum_margin_buffer_lower_bound"] >= 0,
            "base_delta_at_most_1pct_nav": all(abs(row["net_base_quantity"] * row["spot_close"]) <= .01 * row["nav"] for row in result["daily_trace"]),
            "doubling_stress_wallet_and_buffer_nonnegative": all(result["quantity_price_stresses"]["double"][key] >= 0 for key in ("futures_cash_after_close", "margin_buffer_lower_bound")),
            "cash_components_reconcile": abs(final["cash_reconciliation_difference"]) <= 1e-8,
        }
        zero = counterfactuals[identifier]
        summaries.append({"id": identifier, "status": "conditional", "asset": asset, "capital": capital,
                          "cost_scenario": cost, "metrics": m, "uncertainty": uncertainty, "market_exposure": exposure,
                          "zero_funding_cash_profit": zero.get("metrics", {}).get("cash_profit"),
                          "cash_benchmarks": {str(rate): capital * rate * 91 / 365 for rate in (0, .03, .05)},
                          "necessary_conditional_screens": pieces, "all_necessary_conditional_screens_pass": all(pieces.values()),
                          "adoption_or_execution_validated": False,
                          "unresolved": ["spent sample and unknown prior multiplicity", "historical event calendar independent proof",
                                         "account/entity/product eligibility", "actual lot/minimum notionals, fee assets and commissions",
                                         "simultaneous fills, intraday margin/liquidation, stablecoin/counterparty risk"]})
    return {"primary_books": results, "zero_funding_counterfactual_books": counterfactuals}, {
        "cases": summaries, "primary_count": 8, "counterfactual_count": 8, "validated_strategies": 0,
        "interpretation": "Conditional development on spent 2026Q2; annualization is not a forecast; no candidate selected."}, cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    with ResearchRun.start(root=root, registration=REGISTRATION, experiment=EXPERIMENT, source=args.source) as run:
        data = decode_inputs(json.loads(run.read_input("capture")), json.loads(run.read_input("admission")))
        books, summary, cells = evaluate(data)
        run.write_json("books.json", books)
        run.write_json("summary.json", summary)
        run.finish(cells)


if __name__ == "__main__":
    main()
