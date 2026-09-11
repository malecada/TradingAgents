"""Independent saved-archive verification. No collector imports or PnL."""
import base64
import calendar
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "research_runs/dated-archive-20260911/outputs"
DEST = Path(__file__).with_name("dated-archive-review.json")
HOUR = 3600000


def digest(body):
    return hashlib.sha256(body).hexdigest()


def epoch(month, day=1, hour=0):
    return int(datetime(2026, month, day, hour, tzinfo=timezone.utc).timestamp() * 1000)


def verify():
    capture = json.loads((OUTPUT / "archive-capture.json").read_text())
    admission = json.loads((OUTPUT / "archive-admission.json").read_text())
    reported = {row["id"]: row for row in admission["cells"]}
    receipts = {row["id"]: row for row in capture["requests"]}
    assert len(receipts) == len(reported) == 8
    assert admission["terminal_lifetime"] == "unverified"
    bodies, findings, expected_ids = {}, [], []
    for asset in ("btc", "eth"):
        for month in (5, 6):
            symbol = asset.upper() + "USDT_260626"
            filename = f"{symbol}-1h-2026-{month:02d}.zip"
            url = f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1h/{filename}"
            key = f"{asset}-2026-{month:02d}"
            for kind in ("zip", "checksum"):
                identity = key + "-" + kind
                expected_ids.append(identity)
                receipt = receipts[identity]
                assert receipt == json.loads((OUTPUT / (identity + "-receipt.json")).read_text())
                assert receipt["url"] == url + (".CHECKSUM" if kind == "checksum" else "")
                assert receipt["attempted"] and receipt["http_status"] == 200
                assert receipt["body_complete"] and receipt["error"] is None
                assert datetime.fromisoformat(receipt["request_utc"]) <= datetime.fromisoformat(receipt["retrieval_utc"])
                body = base64.b64decode(receipt["body_base64"], validate=True)
                assert len(body) == receipt["body_bytes"] and digest(body) == receipt["body_sha256"]
                assert reported[identity]["status"] == "complete"
                bodies[identity] = body
            zipped, checksum = bodies[key + "-zip"], bodies[key + "-checksum"]
            assert checksum.decode("ascii").rstrip("\r\n") == digest(zipped) + "  " + filename
            assert reported[key + "-checksum"]["declared_archive_sha256"] == digest(zipped)
            with zipfile.ZipFile(io.BytesIO(zipped)) as archive:
                member = filename[:-4] + ".csv"
                assert archive.namelist() == [member]
                info = archive.getinfo(member)
                assert not info.flag_bits & 1
                assert info.file_size <= 2097152 and info.file_size / max(1, info.compress_size) <= 100
                raw = archive.read(member)
                assert archive.testzip() is None
                assert len(raw) == info.file_size
            result = reported[key + "-zip"]
            assert result["member"] == member and result["member_sha256"] == digest(raw)
            assert result["member_bytes"] == len(raw) and result["terminal_lifetime"] == "unverified"
            reader = list(csv.reader(io.StringIO(raw.decode("utf-8"))))
            header = "open_time open high low close volume close_time quote_volume count taker_buy_volume taker_buy_quote_volume ignore".split()
            assert reader.pop(0) == header and result["header_present"]
            stamps, zero_volume, zero_trades = [], [], []
            for row in reader:
                assert len(row) == 12
                opened, closed = int(row[0]), int(row[6])
                assert str(opened) == row[0] and len(row[0]) == 13
                assert opened % HOUR == 0 and closed == opened + HOUR - 1
                values = [Decimal(field) for field in row]
                assert all(value.is_finite() for value in values)
                assert 0 < values[3] <= min(values[1], values[4]) <= max(values[1], values[4]) <= values[2]
                assert all(values[i] >= 0 for i in (5, 7, 8, 9, 10))
                assert values[8] == int(values[8])
                if values[5] == 0:
                    zero_volume.append(opened)
                if values[8] == 0:
                    zero_trades.append(opened)
                stamps.append(opened)
            calendar_clock = list(range(epoch(month), epoch(month + 1), HOUR))
            assert stamps == calendar_clock[:len(stamps)]
            missing = calendar_clock[len(stamps):]
            coverage = result["coverage"]
            assert coverage["observed_hours"] == len(stamps)
            assert coverage["calendar_hours"] == calendar.monthrange(2026, month)[1] * 24
            assert coverage["missing_calendar_hour_ids_ms"] == coverage["trailing_missing_hour_ids_ms"] == missing
            assert coverage["internal_gap_hour_ids_ms"] == coverage["leading_missing_hour_ids_ms"] == []
            assert coverage["zero_volume_hour_ids_ms"] == zero_volume
            assert coverage["zero_trade_hour_ids_ms"] == zero_trades
            assert coverage["zero_volume_hour_count"] == len(zero_volume)
            assert coverage["zero_trade_hour_count"] == len(zero_trades)
            assert coverage["first_open_ms"] == stamps[0] and coverage["last_open_ms"] == stamps[-1]
            if month == 5:
                assert len(stamps) == 744 and not missing and not zero_volume
            else:
                assert len(stamps) == 609 and stamps[-1] == epoch(6, 26, 8)
                assert len(missing) == 111 and zero_volume == zero_trades == [stamps[-1]]
            # Proposed future observation window only; no return or prices emitted.
            selected = [s for s in stamps if epoch(5) <= s < epoch(6, 26)]
            expected = [s for s in calendar_clock if epoch(5) <= s < epoch(6, 26)]
            assert selected == expected and not set(selected).intersection(zero_volume + zero_trades)
            findings.append({"id": key, "archive_sha256": digest(zipped), "member_sha256": digest(raw),
                             "observed_hours": len(stamps), "missing_tail_hours": len(missing),
                             "zero_volume_hours": len(zero_volume), "zero_trade_hours": len(zero_trades),
                             "proposed_window_complete_hours": len(selected)})
    assert list(receipts) == expected_ids and list(reported) == expected_ids
    assert capture["total_body_bytes"] == sum(len(body) for body in bodies.values())
    return {"status": "PASS", "reviewed_utc": datetime.now(timezone.utc).isoformat(),
            "independent_collector_imports": False, "network_requests": 0, "financial_computations": 0,
            "receipts": 8, "admission_cells": 8, "findings": findings,
            "window": "2026-05-01T00:00:00Z through 2026-06-25T23:59:59.999Z",
            "window_observation_admission": "Complete 1344 hourly trade bars per asset; conditional historical price-proxy inputs only.",
            "not_established": ["executable fills/spreads", "margin mark prices/path survival", "exact expiry/settlement", "historical lot limits/fees", "account eligibility", "matched spot inputs", "fresh confirmation"]}


if __name__ == "__main__":
    result = verify()
    with DEST.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "receipts": 8, "admission_cells": 8}))
