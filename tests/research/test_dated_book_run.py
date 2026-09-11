"""Synthetic parent envelopes/archives only; no registered empirical inputs."""
import base64
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest

DIRECTORY = Path(__file__).resolve().parents[2] / "research/strategy-search-2026-09-11"
for name in ("dated_archive", "dated_book", "dated_book_run"):
    spec = importlib.util.spec_from_file_location(name, DIRECTORY / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
runner = sys.modules["dated_book_run"]


def receipt(request, raw):
    return {**request, "http_status": 200, "body_complete": True, "error": None,
            "body_bytes": len(raw), "body_sha256": hashlib.sha256(raw).hexdigest(),
            "body_base64": base64.b64encode(raw).decode()}


def synthetic_inputs():
    archive = runner.archive
    archive_rows = []
    for request in archive.frozen_request_spec()["requests"][::2]:
        start, end = archive._month_bounds(request["month"])
        count = 744 if request["month"] == "2026-05" else 608
        csv_text = io.StringIO()
        writer = csv.writer(csv_text)
        writer.writerow(archive.HEADER)
        for index in range(count):
            stamp = start + index * archive.HOUR_MS
            # Invented deterministic basis convergence; no historical prices.
            elapsed = (stamp - runner.START_MS) // archive.HOUR_MS
            price = 110 - 10 * min(elapsed, 1343) / 1343
            writer.writerow([stamp, price, price, price, price, 1, stamp + archive.HOUR_MS - 1, 100, 1, .5, 50, 0])
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
            zipped.writestr(request["filename"][:-4] + ".csv", csv_text.getvalue())
        raw = out.getvalue()
        archive_rows.append(receipt(request, raw))
        checksum_request = next(row for row in archive.frozen_request_spec()["requests"] if row["id"] == request["id"][:-3] + "checksum")
        checksum = (hashlib.sha256(raw).hexdigest() + "  " + request["filename"] + "\n").encode()
        archive_rows.append(receipt(checksum_request, checksum))
    spot_rows = []
    for request in archive.capture_module.frozen_request_spec()["requests"]:
        start, day = archive.capture_module.START_MS, archive.capture_module.DAY_MS
        rows = [[start + index * day, 100, 100, 100, 100, 1, start + (index + 1) * day - 1, 100, 1, .5, 50, 0]
                for index in range(91)]
        spot_rows.append(receipt(request, json.dumps(rows if request["kind"] == "spot" else {}).encode()))
    return ({"requests": archive_rows}, {"cells": [{"id": row["id"], "status": "complete"} for row in archive_rows]},
            {"requests": spot_rows}, {"cells": [{"id": row["id"], "status": "complete"} for row in spot_rows]})


@pytest.fixture(autouse=True)
def fake_statistics(monkeypatch):
    def calculate(books, spots):
        return {key: {"status": "unavailable", "market_exposure": {"status": "unavailable"},
                      "expected_return_confidence": {"status": "unavailable", "reason": "one episode"},
                      "power": {"status": "unavailable", "reason": "one episode"}} for key in books}
    monkeypatch.setattr(runner, "exposure_statistics", calculate)


def test_planted_basis_pipeline_clips_and_keeps_eight_primary_cases():
    books, summary, cells = runner.evaluate(*synthetic_inputs())
    assert len(cells) == len(summary["cases"]) == 8
    assert all(row["status"] == "complete" for row in cells)
    for counts in books["input_clipping"].values():
        assert counts["spot"] == {"source_rows": 91, "retained_rows": 56, "excluded_before_start": 30, "excluded_at_or_after_end": 5}
        assert counts["dated"]["retained_rows"] == 1344
        assert counts["dated"]["excluded_at_or_after_end"] == 8
    for row in summary["cases"]:
        assert row["metrics"]["cash_profit"] > 0
        assert row["same_quantity_frictionless_profit"] == row["raw_basis_convergence"]
        assert row["necessary_historical_cash_screen"]["same_capital_base_and_stress_pass"] is True
        assert row["actual_margin_risk"]["status"] == row["execution"]["status"] == "unavailable"
        assert row["graduation"] is False
    assert summary["additional_portfolio_counterfactual_count"] == 0


@pytest.mark.parametrize("failure", ["hash", "admission", "checksum", "identity"])
def test_one_asset_invalid_source_keeps_other_asset_and_all_cells(failure):
    capture, admission, spot_capture, spot_admission = synthetic_inputs()
    if failure == "hash":
        capture["requests"][0]["body_sha256"] = "0" * 64
    elif failure == "admission":
        admission["cells"][0]["status"] = "unavailable"
    elif failure == "checksum":
        record = capture["requests"][1]
        raw = ("0" * 64 + "  " + record["filename"] + "\n").encode()
        record.update(body_base64=base64.b64encode(raw).decode(), body_bytes=len(raw), body_sha256=hashlib.sha256(raw).hexdigest())
    else:
        capture["requests"][0]["symbol"] = "WRONG"
    books, _, cells = runner.evaluate(capture, admission, spot_capture, spot_admission)
    assert len(cells) == 8
    assert sum(row["status"] == "unavailable" for row in cells) == 4
    assert "BTC" in books["input_errors"] and "ETH" not in books["input_errors"]


def test_global_denominator_failure_keeps_all_unavailable_cells():
    inputs = synthetic_inputs()
    inputs[0]["requests"].pop()
    _, summary, cells = runner.evaluate(*inputs)
    assert len(cells) == 8 and all(row["status"] == "unavailable" for row in cells)
    assert summary["graduation"] is False


def test_cash_reconciliation_failure_blocks_case_admission(monkeypatch):
    original = runner.book
    def corrupted(*args, **kwargs):
        result = original(*args, **kwargs)
        result["final_ledger"]["cash_reconciliation_difference"] = 1e-6
        return result
    monkeypatch.setattr(runner, "book", corrupted)
    _, summary, cells = runner.evaluate(*synthetic_inputs())
    assert all(row["status"] == "unavailable" for row in cells)
    assert all(not row["necessary_historical_cash_screen"]["same_capital_base_and_stress_pass"] for row in summary["cases"])


def test_real_statistics_integration_keeps_episode_uncertainty_unavailable(monkeypatch):
    spec = importlib.util.spec_from_file_location("dated_statistics", DIRECTORY / "dated_statistics.py")
    statistics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(statistics)
    monkeypatch.setattr(runner, "exposure_statistics", statistics.exposure_statistics)
    _, summary, cells = runner.evaluate(*synthetic_inputs())
    assert len(cells) == 8 and all(cell["status"] == "complete" for cell in cells)
    for case in summary["cases"]:
        result = case["statistics"]
        # Invented constant benchmarks deliberately make joint OLS singular.
        assert result["market_exposure"]["status"] == "unavailable"
        assert "singular" in result["market_exposure"]["reason"]
        assert result["expected_return_confidence"]["status"] == "unavailable"
        assert result["power"]["status"] == "unavailable"
        assert case["graduation"] is False


@pytest.mark.parametrize("clock_column", [0, 6])
def test_fractional_spot_clock_rejected_before_clipping(clock_column):
    inputs = synthetic_inputs()
    record = next(row for row in inputs[2]["requests"] if row["id"] == "btc-spot")
    rows = json.loads(base64.b64decode(record["body_base64"]))
    rows[30][clock_column] += 0.5
    raw = json.dumps(rows).encode()
    record.update(body_base64=base64.b64encode(raw).decode(), body_bytes=len(raw),
                  body_sha256=hashlib.sha256(raw).hexdigest())
    books, _, cells = runner.evaluate(*inputs)
    assert "integer milliseconds" in books["input_errors"]["BTC"]
    assert "BTC" not in books["input_clipping"]
    assert len(cells) == 8
    assert sum(cell["status"] == "unavailable" for cell in cells) == 4
