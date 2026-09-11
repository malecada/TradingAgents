"""Registered eight-case dated episode runner; no network or parameter selection."""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

from tradingagents.research import ResearchRun
import dated_archive as archive
from dated_book import book, START_MS, END_MS

REGISTRATION = "research/strategy-search-2026-09-11/gates-dated-book.json"
EXPERIMENT = "dated-book-20260911"
CASES = [(asset, capital, scenario) for asset in ("BTC", "ETH")
         for capital in (1000, 10000) for scenario in ("base", "stress")]


def case_id(asset, capital, scenario):
    return f"{asset.lower()}-{capital}-{scenario}"


def _records(rows, expected):
    if len(rows) != len(expected) or {row["id"] for row in rows} != set(expected):
        raise ValueError("parent source cell denominator mismatch")
    return {row["id"]: row for row in rows}


def _raw(record, admitted, expected):
    if admitted["status"] != "complete":
        raise ValueError("parent source cell is unavailable")
    if any(record.get(key) != value for key, value in expected.items()):
        raise ValueError("parent request identity differs from frozen specification")
    if record["http_status"] != 200 or not record["body_complete"] or record["error"]:
        raise ValueError("parent raw response is incomplete")
    raw = base64.b64decode(record["body_base64"], validate=True)
    if len(raw) != record["body_bytes"] or hashlib.sha256(raw).hexdigest() != record["body_sha256"]:
        raise ValueError("parent raw body hash/size mismatch")
    return raw


def _clip(rows):
    selected, before, after = [], 0, 0
    for row in rows:
        stamp = int(row[0])
        if stamp < START_MS:
            before += 1
        elif stamp >= END_MS:
            after += 1
        else:
            selected.append(row)
    return selected, {"source_rows": len(rows), "retained_rows": len(selected),
                      "excluded_before_start": before, "excluded_at_or_after_end": after}


def decode_inputs(capture, admission, spot_capture, spot_admission):
    """Re-admit immutable source bytes and preserve per-asset failures/exclusions."""
    expected_archives = {row["id"]: row for row in archive.frozen_request_spec()["requests"]}
    expected_spots = {row["id"]: row for row in archive.capture_module.frozen_request_spec()["requests"]}
    records = _records(capture["requests"], expected_archives)
    admitted = _records(admission["cells"], expected_archives)
    spot_records = _records(spot_capture["requests"], expected_spots)
    spot_admitted = _records(spot_admission["cells"], expected_spots)
    data, errors, clipping = {}, {}, {}
    for asset in ("BTC", "ETH"):
        prefix = asset.lower()
        try:
            source_spot = json.loads(_raw(spot_records[prefix + "-spot"], spot_admitted[prefix + "-spot"],
                                         expected_spots[prefix + "-spot"]))
            # Revalidate all quarter source clocks and OHLC before explicit clipping.
            archive.capture_module.admit_response(expected_spots[prefix + "-spot"], json.dumps(source_spot).encode())
            source_hours, archive_checks = [], []
            for month in ("2026-05", "2026-06"):
                key = f"{prefix}-{month}-zip"
                checksum_key = f"{prefix}-{month}-checksum"
                raw = _raw(records[key], admitted[key], expected_archives[key])
                checksum = _raw(records[checksum_key], admitted[checksum_key], expected_archives[checksum_key])
                check = archive.validate_archive(raw, checksum, expected_archives[key])
                if check["status"] != "complete":
                    raise ValueError("parent archive no longer passes source admission: " + check["reason"])
                archive_checks.append({"id": key, "coverage": check["coverage"], "member_sha256": check["member_sha256"]})
                with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
                    rows = list(csv.reader(io.StringIO(zipped.read(check["member"]).decode("utf-8"))))
                if rows and rows[0] == archive.HEADER:
                    rows = rows[1:]
                source_hours.extend(rows)
            spot, spot_counts = _clip(source_spot)
            hours, hour_counts = _clip(source_hours)
            data[asset] = {"spot": spot, "dated": hours}
            clipping[asset] = {"spot": spot_counts, "dated": hour_counts, "source_archive_checks": archive_checks,
                               "terminal_lifetime": "unverified; no expiry-day price or settlement used"}
        except (ValueError, KeyError, TypeError, OverflowError, OSError, csv.Error, zipfile.BadZipFile, archive.zlib.error, RuntimeError) as exc:
            errors[asset] = type(exc).__name__ + ": " + str(exc)
    return data, errors, clipping


def exposure_statistics(primary_books, spot_by_asset):
    # Imported only at evaluation, allowing engineering tests to supply a fake
    # statistics function while the separately owned module is being prepared.
    from dated_statistics import exposure_statistics as calculate
    return calculate(primary_books, spot_by_asset)


def evaluate(capture, admission, spot_capture, spot_admission):
    """Four parsed registered input envelopes -> books, summary, eight cells."""
    try:
        data, errors, clipping = decode_inputs(capture, admission, spot_capture, spot_admission)
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        data, clipping = {}, {}
        errors = {asset: type(exc).__name__ + ": " + str(exc) for asset in ("BTC", "ETH")}
    primary, cells = {}, []
    for asset, capital, scenario in CASES:
        identifier = case_id(asset, capital, scenario)
        if asset in errors:
            result = {"status": "unavailable", "reason": errors[asset], "asset": asset, "capital": capital}
        else:
            try:
                result = book(data[asset]["spot"], data[asset]["dated"], asset=asset, capital=capital, cost_scenario=scenario)
                if result["status"] == "conditional":
                    difference = result["final_ledger"]["cash_reconciliation_difference"]
                    if not math.isfinite(difference) or abs(difference) > 1e-8:
                        result.update(status="unavailable", reason="cash reconciliation exceeds absolute 1e-8 USDT tolerance")
            except (ValueError, KeyError, TypeError, OverflowError) as exc:
                result = {"status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc)}
        primary[identifier] = result
        cells.append({"id": identifier, "status": "complete" if result["status"] == "conditional" else "unavailable",
                      **({"reason": result["reason"]} if result["status"] == "unavailable" else
                         {"scope": "one conditional historical episode; no graduation"})})
    statistics = exposure_statistics(primary, {asset: values["spot"] for asset, values in data.items()})
    screens = {}
    for identifier, result in primary.items():
        screens[identifier] = (result["status"] == "conditional" and result["metrics"]["cash_profit"] > 0
                               and result["metrics"]["annualized_simple_return_365"] >= 0.03)
    summaries = []
    for asset, capital, scenario in CASES:
        identifier = case_id(asset, capital, scenario)
        result = primary[identifier]
        combined = all(screens[case_id(asset, capital, cost)] for cost in ("base", "stress"))
        entry = {"id": identifier, "status": result["status"], "asset": asset, "capital": capital,
                 "cost_scenario": scenario, "statistics": statistics[identifier],
                 "cash_benchmarks": {str(rate): capital * rate * 56 / 365 for rate in (0, .03, .05)},
                 "necessary_historical_cash_screen": {"case_positive_and_annualized_at_least_3pct": screens[identifier],
                    "same_capital_base_and_stress_pass": combined,
                    "scope": "Provisional deterministic episode relevance only; annualization is descriptive."},
                 "actual_margin_risk": {"status": "unavailable", "reason": "Actual mark/maintenance/liquidation path unavailable."},
                 "execution": {"status": "unavailable", "reason": "Historical/current lots, fees, eligibility and realized simultaneous fills unverified."},
                 "graduation": False, "adoption_or_execution_validated": False}
        if result["status"] == "conditional":
            entry.update(metrics=result["metrics"], raw_basis_convergence=result["final_ledger"]["raw_basis_convergence"],
                         same_quantity_frictionless_profit=result["final_ledger"]["zero_friction_same_quantity_profit"],
                         slippage_cost=result["final_ledger"]["slippage_cost"], commissions=result["final_ledger"]["all_fees"],
                         accounting_reconciles=True, held_activity=result["held_activity"])
        else:
            entry.update(reason=result["reason"], accounting_reconciles=None)
        summaries.append(entry)
    return {"primary_books": primary, "input_clipping": clipping, "input_errors": errors}, {
        "cases": summaries, "primary_count": 8, "additional_portfolio_counterfactual_count": 0,
        "validated_strategies": 0, "graduation": False,
        "interpretation": "One spent historical convergence episode per asset. Frictionless values use the same primary quantity; no fresh confirmation or expected-profit inference."}, cells


run = evaluate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2], registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as registered:
        inputs = [json.loads(registered.read_input(name)) for name in ("capture", "admission", "spot_capture", "spot_admission")]
        books, summary, cells = evaluate(*inputs)
        registered.write_json("books.json", books)
        registered.write_json("summary.json", summary)
        registered.finish(cells)


if __name__ == "__main__":
    main()
