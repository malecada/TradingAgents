"""Independent read-only reconstruction; does not import the research runner.

Only the final review JSON is written; inputs, registration and run are read-only.
"""
from pathlib import Path
from decimal import Decimal, localcontext
from datetime import date, timedelta, datetime
import csv
import hashlib
import io
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "research_runs/carry-definition-20260911"
EXPECTED_SOURCE = "d3ba86924bd8711704fc80fd771a0e717cc9bb51"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def committed(path):
    return subprocess.check_output(["git", "show", f"{EXPECTED_SOURCE}:{path}"], cwd=ROOT)


def check():
    claim_raw = (RUN / "claim.json").read_bytes()
    claim = json.loads(claim_raw)
    receipt_raw = (RUN / "complete.json").read_bytes()
    receipt = json.loads(receipt_raw)
    result_raw = (RUN / "outputs/diagnostic.json").read_bytes()
    result = json.loads(result_raw)
    registration_raw = committed(claim["registration"])
    gate = json.loads(registration_raw)["experiments"][claim["experiment_id"]]
    assert claim["source"] == receipt["source"] == EXPECTED_SOURCE
    assert claim["design_source"] == EXPECTED_SOURCE
    assert sha(registration_raw) == claim["registration_sha256"] == receipt["registration_sha256"]
    assert sha(claim_raw) == receipt["claim_sha256"]
    assert sha(result_raw) == receipt["output_sha256"]["diagnostic.json"]
    assert receipt["status"] == "complete"
    assert claim["experiment"] == gate
    assert claim["inputs"] == gate["inputs"]
    assert datetime.fromisoformat(receipt["ended_at"]) >= datetime.fromisoformat(claim["started_at"])
    assert sorted(p.name for p in RUN.iterdir()) == ["claim.json", "complete.json", "outputs"]
    assert [p.name for p in (RUN / "outputs").iterdir()] == gate["outputs"]
    source_hashes = dict(gate["source_files"])
    source_hashes[gate["charter"]["path"]] = gate["charter"]["sha256"]
    source_hashes.update({"tradingagents/research/" + k: v for k, v in gate["runtime_hashes"].items()})
    for path, expected in source_hashes.items():
        assert sha(committed(path)) == expected, path
    inputs = {}
    for name, spec in gate["inputs"].items():
        raw = (ROOT / spec["path"]).read_bytes()
        assert sha(raw) == spec["sha256"], name
        assert sha(committed(spec["path"])) == spec["sha256"], name
        inputs[name] = raw
    ids = [c["id"] for c in receipt["cells"]]
    assert len(ids) == len(set(ids)) == receipt["cell_count"] == 6
    assert ids == gate["cells"]
    assert all(c["status"] == "complete" for c in receipt["cells"])
    assert receipt["unavailable_count"] == 0
    assert set(result) == {"dev", "holdout"}
    comparisons = []
    reconstructed = {}

    def compare(label, actual, expected):
        assert actual is not None and math.isfinite(actual), label
        difference = abs(actual - float(expected))
        assert math.isclose(actual, float(expected), rel_tol=1e-10, abs_tol=1e-12), (label, actual, expected)
        comparisons.append(difference)

    with localcontext() as ctx:
        ctx.prec = 60
        for window, start, end, count in [
            ("dev", "2021-11-08", "2025-03-31", 1239),
            ("holdout", "2025-04-01", "2026-07-01", 456),
        ]:
            costs = json.loads(inputs[window + "_costs"], parse_float=Decimal)
            assert costs["window"] == [start, end]
            p = costs["cost_parameters"]
            assert p["target_notional_per_leg"] == 1
            assert costs["annualization"] == "sqrt(252)"
            compare(window + "/historical_rf", float(p["rf_daily"]), Decimal("1.045") ** (Decimal(1) / 252) - 1)
            compare(window + "/margin", float(p["margin_fraction_of_perp_notional"]), Decimal(1) / 3)
            drag = p["rf_daily"] * p["margin_fraction_of_perp_notional"]
            rows = list(csv.DictReader(io.StringIO(inputs[window + "_series"].decode())))
            assert len(rows) == count == (date.fromisoformat(end) - date.fromisoformat(start)).days
            assert [r["date"] for r in rows] == [(date.fromisoformat(start) + timedelta(days=i)).isoformat() for i in range(count)]
            assert all(set(row) == {"date", "btc", "eth", "sleeve"} for row in rows)
            output = result[window]
            assert output["window"] == [start, end]
            assert output["series_denominator"] == ["btc", "eth", "sleeve"]
            assert set(output["series"]) == {"btc", "eth", "sleeve"}
            assert all(output[key]["status"] == "unavailable" for key in ("cashflow_profit", "full_capital_returns", "market_beta"))
            assert len(output["inherited_defects"]) == 3
            compare(window + "/drag", output["daily_opportunity_cost_addback"], drag)
            reconstructed[window] = {}
            for row in rows:
                compare(window + "/blend", float(row["sleeve"]), (Decimal(row["btc"]) + Decimal(row["eth"])) / 2)
            for series in ["btc", "eth", "sleeve"]:
                original = [Decimal(r[series]) for r in rows]
                assert all(x.is_finite() for x in original)
                sums = []
                reconstructed[window][series] = {}
                for variant in ["stressed", "opportunity_cost_addback"]:
                    xs = original if variant == "stressed" else [x + drag for x in original]
                    total = sum(xs)
                    mean = total / count
                    sd = (sum((x - mean) ** 2 for x in xs) / (count - 1)).sqrt()
                    sr = mean / sd * Decimal(252).sqrt()
                    product = Decimal(1)
                    for x in xs:
                        assert x > -1
                        product *= 1 + x
                    logarithm = product.ln()
                    got = output["series"][series][variant]
                    assert got["n"] == count
                    stats = {"sum": total, "mean": mean, "sample_std_ddof1": sd,
                             "sr_sqrt252": sr, "compounded_index_starting_at_one": product}
                    for metric, expected in stats.items():
                        compare(f"{window}/{series}/{variant}/{metric}", got[metric], expected)
                    diagnostic = got["convention_diagnostic"]
                    assert diagnostic["status"] == "complete"
                    assert diagnostic["all_days"] == diagnostic["valid_simple_index_days"] == count
                    assert diagnostic["invalid_simple_index_days"] == 0
                    compare("log convention", diagnostic["log1p_sum"], logarithm)
                    compare("convention gap", diagnostic["log_sum_minus_additive_sum"], logarithm - total)
                    reconstructed[window][series][variant] = {k: float(v) for k, v in stats.items()}
                    sums.append(total)
                compare("sum addback identity", float(sums[1] - sums[0]), count * drag)
                signs = ["positive" if v > 0 else "negative" if v < 0 else "zero" for v in sums]
                assert output["series"][series]["additive_sum_sign"] == {"stressed": signs[0], "addback": signs[1], "changed": signs[0] != signs[1]}
            assert output["saved_blended_sr_check"]["agrees"] is True
            for variant, saved in [("stressed", costs["stressed_blended_sr"]),
                                   ("opportunity_cost_addback", costs["waterfall_sr"]["plus_rebalance"])]:
                compare(window + "/saved_waterfall", output["series"]["sleeve"][variant]["sr_sqrt252"], saved)
    report = {
        "status": "pass_narrow_definition_diagnostic", "reviewer": "independent_review",
        "source": EXPECTED_SOURCE, "claim_sha256": sha(claim_raw), "receipt_sha256": sha(receipt_raw),
        "output_sha256": sha(result_raw), "checker_sha256": sha(Path(__file__).read_bytes()),
        "method": "60-digit Decimal reconstruction from four committed raw saved inputs; direct products, central-moment sample variance, logarithm of product; no runner import or experiment rerun",
        "cells_verified": ids, "complete": 6, "unavailable": 0,
        "input_hashes": {k: sha(v) for k, v in inputs.items()},
        "numeric_comparisons": len(comparisons), "maximum_absolute_difference": max(comparisons),
        "reconstructed": reconstructed,
        "material_new_diagnostic_findings": [],
        "inherited_findings": [
            {"location": "tradingagents/strategies/carry_sleeve.py:190", "issue": "Missing price-return differences zero-filled; event funding completeness unproven", "impact": "Index identity cannot establish actual cashflow validity"},
            {"location": "scripts/carry_audit_costs.py:124", "issue": "Short equity compounded as a drift proxy; identical100→105→100 path invents0.004762 final drift", "impact": "Restored index is not a signed-quantity cash book"},
        ],
        "not_tested": ["Actual funding-event completeness and event-mark prices", "Execution timing and achievable fills", "Full-capital cash profit at1,000/10,000", "Margin/liquidation path", "BTC/ETH beta or prospective sample freshness", "Account/product eligibility", "Concurrency fault injection", "Independent external proof of push before run"],
        "next_action": "One separately registered bounded input-admission investigation for a signed-quantity cash book; require complete event marks, spot prices, funding, principal/collateral and quantity rules before new economics. If unavailable, retain denominator and switch family.",
    }
    destination = Path(__file__).with_name("carry-definition-review.json")
    with destination.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({k: report[k] for k in ["status", "complete", "unavailable", "numeric_comparisons", "maximum_absolute_difference"]}))


if __name__ == "__main__":
    check()
