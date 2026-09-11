"""Independent read-only raw-capture verification; no collector import or network.

Writes only the review JSON. Does not compute financial statistics.
"""
import base64
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "research_runs/carry-inputs-20260911"
SOURCE = "8cac1b361ecc96e5bd6f2ab0fa43bf51b1524ec4"
START = datetime(2026, 4, 1, tzinfo=timezone.utc)
END = datetime(2026, 7, 1, tzinfo=timezone.utc)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def snapshot(path):
    return subprocess.check_output(["git", "show", f"{SOURCE}:{path}"], cwd=ROOT)


def ms(stamp):
    return int(stamp.timestamp() * 1000)


def numeric(value, positive=False):
    assert not isinstance(value, bool)
    number = Decimal(str(value))
    assert number.is_finite()
    assert not positive or number > 0
    return number


def check():
    claim_raw = (RUN / "claim.json").read_bytes()
    claim = json.loads(claim_raw)
    receipt_raw = (RUN / "complete.json").read_bytes()
    complete = json.loads(receipt_raw)
    assert claim["source"] == claim["design_source"] == complete["source"] == SOURCE
    assert sha(claim_raw) == complete["claim_sha256"]
    registration_raw = snapshot(claim["registration"])
    assert sha(registration_raw) == claim["registration_sha256"] == complete["registration_sha256"]
    registration = json.loads(registration_raw)
    experiment = registration["experiments"]["carry-inputs-20260911"]
    assert experiment == claim["experiment"]
    assert experiment["parent"] == "carry-definition-20260911"
    assert experiment["stage"] == "development" and experiment["reuse"] == "exploratory"
    family = registration["families"][experiment["family"]]
    assert family["legacy_total_attempts"] == "unknown" and family["new_program_incremental_cap"] == 3
    members = dict(experiment["source_files"])
    members[experiment["charter"]["path"]] = experiment["charter"]["sha256"]
    members.update({"tradingagents/research/" + k: v for k, v in experiment["runtime_hashes"].items()})
    for path, digest in members.items():
        assert sha(snapshot(path)) == digest, path
    assert experiment["source_files"]["research/strategy-search-2026-09-11/carry_capture.py"] == "323ea01ac0d8137288e6f72f697101db1884595e876622402c321f38367d6b12"
    input_spec = experiment["inputs"]["request_spec"]
    spec_raw = snapshot(input_spec["path"])
    assert sha(spec_raw) == input_spec["sha256"]
    assert (ROOT / input_spec["path"]).read_bytes() == spec_raw
    spec = json.loads(spec_raw)
    outputs = RUN / "outputs"
    assert set(p.name for p in outputs.iterdir()) == set(experiment["outputs"]) == set(complete["output_sha256"])
    assert len(experiment["outputs"]) == 12
    for name, digest in complete["output_sha256"].items():
        assert sha((outputs / name).read_bytes()) == digest, name
    aggregate = json.loads((outputs / "capture.json").read_bytes())
    admission = json.loads((outputs / "admission.json").read_bytes())
    expected_ids = [f"{asset}-{kind}" for kind in ("funding", "spot", "perp", "mark") for asset in ("btc", "eth")] + ["exchange-info", "server-time"]
    assert experiment["cells"] == expected_ids
    assert [r["id"] for r in spec["requests"]] == expected_ids
    assert [r["id"] for r in aggregate["requests"]] == expected_ids
    assert [r["id"] for r in complete["cells"]] == expected_ids
    assert [r["id"] for r in admission["cells"]] == expected_ids
    assert complete["cell_count"] == 10 and complete["unavailable_count"] == 0
    assert complete["status"] == "complete" and all(c["status"] == "complete" for c in complete["cells"])
    assert aggregate["request_spec"] == spec
    assert spec["max_requests"] == 10 and spec["timeout_seconds_per_request"] == 20
    assert spec["max_response_bytes"] == 5 * 1024 * 1024
    assert spec["window"] == ["2026-04-01T00:00:00Z", "2026-07-01T00:00:00Z"]
    start_ms, end_ms = ms(START), ms(END)
    expected_bar_times = [ms(START + timedelta(days=i)) for i in range(91)]
    expected_funding_times = [ms(START + timedelta(hours=8*i)) for i in range(273)]
    domains = {"funding": ("fapi.binance.com", "/fapi/v1/fundingRate"),
               "spot": ("api.binance.com", "/api/v3/klines"),
               "perp": ("fapi.binance.com", "/fapi/v1/klines"),
               "mark": ("fapi.binance.com", "/fapi/v1/markPriceKlines"),
               "exchange-info": ("fapi.binance.com", "/fapi/v1/exchangeInfo"),
               "server-time": ("fapi.binance.com", "/fapi/v1/time")}
    summary, payloads, total, previous_retrieval = {}, {}, 0, None
    started = datetime.fromisoformat(claim["started_at"])
    ended = datetime.fromisoformat(complete["ended_at"])
    assert started < ended and (ended - started).total_seconds() <= 300
    for request, record, verdict in zip(spec["requests"], aggregate["requests"], admission["cells"]):
        name, kind = request["id"], request["kind"]
        individual = json.loads((outputs / (name + "-receipt.json")).read_bytes())
        assert individual == record
        assert all(record[key] == value for key, value in request.items())
        assert record["attempted"] is True and record["body_complete"] is True
        assert record["http_status"] == 200 and record["error"] is None
        assert verdict["status"] == "complete"
        url = urlsplit(record["request_url"])
        assert url.scheme == "https" and (url.hostname, url.path) == domains[kind]
        assert url.username is None and url.password is None and url.fragment == ""
        assert parse_qs(url.query) == {k: [str(v)] for k, v in request["parameters"].items()}
        if kind in ("funding", "spot", "perp", "mark"):
            params = request["parameters"]
            assert params["symbol"] == name[:3].upper() + "USDT"
            assert params["startTime"] == start_ms and params["endTime"] == end_ms - 1 and params["limit"] == 1000
            assert kind == "funding" or params["interval"] == "1d"
        else:
            assert request["parameters"] == {}
        raw = base64.b64decode(record["body_base64"], validate=True)
        assert sha(raw) == record["body_sha256"]
        assert len(raw) == record["body_bytes"] <= spec["max_response_bytes"]
        total += len(raw)
        data = json.loads(raw, parse_float=Decimal)
        payloads[name] = data
        request_at, retrieval_at = [datetime.fromisoformat(record[k]) for k in ("request_utc", "retrieval_utc")]
        assert request_at.utcoffset() == retrieval_at.utcoffset() == timedelta(0)
        assert started <= request_at <= retrieval_at <= ended
        assert previous_retrieval is None or previous_retrieval <= request_at
        previous_retrieval = retrieval_at
        assert 0 <= record["elapsed_seconds"] <= 20
        assert abs((retrieval_at - request_at).total_seconds() - record["elapsed_seconds"]) < 0.01
        assert set(record["headers"]) <= {"Date", "Content-Type"}
        assert "application/json" in record["headers"]["Content-Type"]
        source_date = parsedate_to_datetime(record["headers"]["Date"])
        assert request_at - timedelta(seconds=5) <= source_date <= retrieval_at + timedelta(seconds=5)
        item = {"status": "complete", "raw_body_sha256": sha(raw), "raw_bytes": len(raw),
                "request_utc": record["request_utc"], "retrieval_utc": record["retrieval_utc"]}
        if kind == "funding":
            assert isinstance(data, list) and len(data) == 273
            stamps = [r["fundingTime"] for r in data]
            assert all(type(t) is int for t in stamps)
            assert len(set(stamps)) == 273 and stamps == sorted(stamps)
            assert all(start_ms <= t < end_ms for t in stamps)
            offsets = [t - expected for t, expected in zip(stamps, expected_funding_times)]
            assert all(abs(v) <= 5000 for v in offsets)
            assert Counter((t - start_ms) // 86400000 for t in stamps) == Counter({i: 3 for i in range(91)})
            assert all(r["symbol"] == request["parameters"]["symbol"] for r in data)
            for event in data:
                numeric(event["fundingRate"])
                numeric(event["markPrice"], positive=True)
            maximum_offset = max(map(abs, offsets))
            assert verdict["observations"] == verdict["expected_events"] == 273
            assert verdict["maximum_schedule_offset_ms"] == maximum_offset
            coverage = verdict["coverage"]
            assert coverage["status"] == "complete"
            assert coverage["expected_events"] == coverage["observed_events"] == coverage["matched_unique_slots"] == 273
            assert coverage["missing_slot_count"] == coverage["unexpected_count"] == 0
            for key in ("missing_canonical_slots_ms", "unexpected_timestamps_ms", "duplicate_timestamps_ms", "duplicate_canonical_slots_ms", "invalid_timestamp_row_indices"):
                assert coverage[key] == []
            assert coverage["maximum_schedule_offset_ms"] == maximum_offset
            item.update(observations=273, conditional_days=91, missing=0, duplicates=0, unexpected=0,
                        maximum_schedule_offset_ms=maximum_offset, first_event_ms=stamps[0], last_event_ms=stamps[-1],
                        finite_funding_rates=273, positive_event_marks=273)
        elif kind in ("spot", "perp", "mark"):
            assert isinstance(data, list) and len(data) == 91
            assert all(isinstance(row, list) and len(row) == 12 for row in data)
            assert [row[0] for row in data] == expected_bar_times
            assert all(type(row[0]) is int and type(row[6]) is int and row[6] == row[0] + 86400000 - 1 for row in data)
            for row in data:
                opening, high, low, close = [numeric(x, positive=True) for x in row[1:5]]
                assert low <= opening <= high and low <= close <= high
            assert verdict["observations"] == verdict["expected_days"] == 91
            item.update(observations=91, missing=0, duplicates=0, valid_ohlc_rows=91,
                        first_open_ms=data[0][0], last_close_ms=data[-1][6])
        elif kind == "exchange-info":
            assert isinstance(data, dict) and isinstance(data["symbols"], list)
            found = [r for r in data["symbols"] if r.get("symbol") in ("BTCUSDT", "ETHUSDT")]
            assert Counter(r["symbol"] for r in found) == Counter({"BTCUSDT": 1, "ETHUSDT": 1})
            for row in found:
                assert row["contractType"] == "PERPETUAL" and row["quoteAsset"] == row["marginAsset"] == "USDT"
                assert row["status"] == "TRADING"
                assert row["baseAsset"] == row["symbol"][:-4]
            assert verdict["symbols"] == ["BTCUSDT", "ETHUSDT"]
            item.update(symbols=["BTCUSDT", "ETHUSDT"], current_identity_only=True)
        else:
            stamp = data["serverTime"]
            assert type(stamp) is int and stamp > 0
            lower, upper = ms(request_at) - 5000, ms(retrieval_at) + 5000
            assert lower <= stamp <= upper
            assert verdict["server_time_ms"] == stamp
            expected_clock = {"earliest_allowed_ms": lower, "latest_allowed_ms": upper,
                              "server_minus_request_ms": stamp - ms(request_at),
                              "server_minus_retrieval_ms": stamp - ms(retrieval_at), "agrees": True}
            assert verdict["clock_check"] == expected_clock
            item.update(clock_check=expected_clock)
        summary[name] = item
    assert aggregate["total_body_bytes"] == total <= 50 * 1024 * 1024
    mark_range_checks = {}
    for asset in ("btc", "eth"):
        assert [r[0] for r in payloads[asset + "-spot"]] == [r[0] for r in payloads[asset + "-perp"]] == [r[0] for r in payloads[asset + "-mark"]]
        marks_by_day = {row[0]: row for row in payloads[asset + "-mark"]}
        tolerance = Decimal("0.00000001")
        for event in payloads[asset + "-funding"]:
            day = start_ms + ((event["fundingTime"] - start_ms) // 86400000) * 86400000
            bar = marks_by_day[day]
            mark, low, high = [numeric(value, positive=True) for value in (event["markPrice"], bar[3], bar[2])]
            assert low - tolerance <= mark <= high + tolerance, (asset, event["fundingTime"], "event mark outside same-day OHLC")
        mark_range_checks[asset] = {"events_checked": 273, "outside_same_utc_day_mark_range": 0,
                                   "absolute_price_tolerance_usdt": str(tolerance)}
    report = {
        "status": "pass_conditional_source_admission", "reviewer": "independent_review", "source": SOURCE,
        "checker_sha256": sha(Path(__file__).read_bytes()), "claim_sha256": sha(claim_raw),
        "receipt_sha256": sha(receipt_raw), "output_sha256": complete["output_sha256"],
        "method": "Decode and hash every individual raw receipt; reconcile aggregate copies and all registered outputs; reconstruct dates, finite Decimal values, coverage, OHLC and clocks without importing collector. No network or PnL computation.",
        "complete_cells": 10, "unavailable_cells": 0, "outputs_verified": 12, "raw_bytes": total,
        "funding_events_verified": 546, "bar_rows_verified": 546, "cells": summary,
        "funding_event_mark_vs_daily_mark_bar": mark_range_checks,
        "material_capture_findings": [],
        "conditional_quantity_book_sufficiency": "Sufficient for a separately registered conditional fixed-base-quantity book using historical daily prices as proxies and recorded funding-event marks. Not sufficient for executable economics or margin-path validation.",
        "required_financial_registration_caveats": [
            "The conditional 00/08/16 UTC funding calendar is not independently established historical schedule evidence.",
            "Freeze entry/exit event ownership. Do not capture opening-boundary funding merely because its recorded event timestamp trails midnight by milliseconds.",
            "Match spot and perpetual base quantities; reserve full spot principal, futures collateral, costs and cash buffers at each capital size.",
            "Record funding as signed quantity times the associated event mark times rate; never substitute daily-average rates or different price marks.",
            "Daily OHLC prices are execution and valuation proxies. No simultaneous fills, bid/ask, intraday margin sufficiency or liquidation protection is established.",
            "Historical/account-specific fees, fee assets, borrow/conversion costs, spot/perpetual lot filters and maintenance margin remain unverified.",
            "Current exchange metadata is not historical product state or account eligibility evidence.",
            "The quarter is already exposed. New fields and capture time do not establish fresh confirmation or historical publication timing.",
        ],
        "not_tested": ["Independent upstream authenticity or historical data revisions", "Historical funding-calendar changes", "Historical account, fee and lot applicability", "Funding cash amounts for real positions", "Executable fills or intraday margin paths", "Any financial statistic, exposure or return", "External backup/pre-result push timing", "OS crash, maximum-resource or concurrency fault injection"],
        "next_action": "Freeze exactly one conditional fixed-quantity-book development investigation with full-capital cash accounting and independent synthetic/financial review; retain all unverified execution, calendar and margin claims as unavailable.",
    }
    with Path(__file__).with_name("capture-review.json").open("w") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({k: report[k] for k in ("status", "complete_cells", "unavailable_cells", "outputs_verified", "raw_bytes", "funding_events_verified", "bar_rows_verified")}))


if __name__ == "__main__":
    check()
