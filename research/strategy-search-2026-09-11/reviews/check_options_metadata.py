"""Independent saved-source review; stdlib only, no collector import/network/PnL."""
import base64
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUN = ROOT / "research_runs/options-metadata-20260911"
OUT = RUN / "outputs"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(values):
    result = {}
    for key, value in values:
        assert key not in result, ("duplicate JSON key", key)
        result[key] = value
    return result


def constant(value):
    raise AssertionError(("nonfinite JSON constant", value))


def read(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_constant=constant, parse_float=Decimal)


def file(path):
    return read(path.read_bytes())


def clock(value):
    stamp = datetime.fromisoformat(value)
    assert stamp.tzinfo is not None
    return stamp


def numeric(value, positive):
    assert not isinstance(value, bool) and isinstance(value, (str, int, Decimal))
    number = Decimal(str(value))
    assert number.is_finite() and number >= 0 and (not positive or number > 0)
    return str(number)


def main():
    claim, complete = file(RUN / "claim.json"), file(RUN / "complete.json")
    source = claim["source"]
    assert source == "828884688b944b5cd2c33537fe4fcabc28325e66"
    gate_path = ROOT / claim["registration"]
    gate = file(gate_path)
    assert sha(gate_path.read_bytes()) == claim["registration_sha256"] == complete["registration_sha256"]
    experiment = gate["experiments"][claim["experiment_id"]]
    for path, expected in experiment["source_files"].items():
        assert sha((ROOT / path).read_bytes()) == expected
        committed = subprocess.check_output(["git", "show", source + ":" + path], cwd=ROOT)
        assert sha(committed) == expected
    for item in [experiment["charter"], *experiment["inputs"].values()]:
        assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"]
    for name, expected in experiment["runtime_hashes"].items():
        assert sha((ROOT / "tradingagents/research" / name).read_bytes()) == expected
    spec = file(ROOT / experiment["inputs"]["request_spec"]["path"])
    capture, admission = file(OUT / "metadata-capture.json"), file(OUT / "metadata-admission.json")
    assert capture["request_spec"] == spec
    ids = [r["id"] for r in spec["requests"]]
    assert len(ids) == len(set(ids)) == 4 and ids == experiment["cells"]
    assert [r["id"] for r in capture["requests"]] == [r["id"] for r in admission["cells"]] == ids
    assert set(p.name for p in OUT.iterdir()) == set(experiment["outputs"]) == set(complete["output_sha256"])
    assert len(experiment["outputs"]) == 6
    for name, expected in complete["output_sha256"].items():
        assert sha((OUT / name).read_bytes()) == expected
    assert sha((RUN / "claim.json").read_bytes()) == complete["claim_sha256"]
    assert complete["cell_count"] == 4 and complete["unavailable_count"] == 0
    assert all(r["status"] == "complete" for r in complete["cells"])
    raw_bodies, clocks, publication_evidence = [], [], []
    previous = clock(claim["started_at"])
    for index, (request, receipt) in enumerate(zip(spec["requests"], capture["requests"], strict=True)):
        receipt_path = OUT / (request["id"] + "-receipt.json")
        assert file(receipt_path) == receipt
        assert all(receipt[k] == v for k, v in request.items())
        assert receipt["attempted"] and receipt["http_status"] == 200 and receipt["body_complete"] and receipt["error"] is None
        raw = base64.b64decode(receipt["body_base64"], validate=True)
        assert len(raw) == receipt["body_bytes"] <= spec["max_response_bytes"]
        assert sha(raw) == receipt["body_sha256"]
        begin, end = clock(receipt["request_utc"]), clock(receipt["retrieval_utc"])
        assert previous <= begin <= end <= clock(complete["ended_at"])
        assert abs((end - begin).total_seconds() - float(receipt["elapsed_seconds"])) < .01
        previous = end
        raw_bodies.append(raw)
        clocks.append({"id": request["id"], "begin": receipt["request_utc"], "end": receipt["retrieval_utc"]})
        modified = receipt_path.stat().st_mtime
        next_begin = clock(capture["requests"][index+1]["request_utc"]).timestamp() if index < 3 else clock(complete["ended_at"]).timestamp()
        publication_evidence.append({"id": request["id"], "mtime_between_retrieval_and_next_request": end.timestamp() <= modified <= next_begin})
    assert sum(map(len, raw_bodies)) == capture["total_body_bytes"] <= spec["max_total_response_bytes"]
    exchange = read(raw_bodies[0]); assert isinstance(exchange, dict) and "code" not in exchange
    rows, normalized = exchange["optionSymbols"], admission["cells"][0]["normalized_symbol_rows"]
    assert all(isinstance(r, dict) for r in rows)
    assert len(rows) == len(normalized) == admission["cells"][0]["symbol_count"]
    identities = Counter(r["symbol"] for r in rows)
    targets, asset_counts, quantity_counts = [], Counter(), Counter()
    fields = ("symbol", "underlying", "underlyingType", "contractType", "expiryDate", "side", "unit", "minQty", "maxQty", "status", "initialMargin", "maintenanceMargin", "minInitialMargin", "minMaintenanceMargin", "nakedSell", "filters")
    for index, (row, actual) in enumerate(zip(rows, normalized, strict=True)):
        assert actual["row_index"] == index and actual["raw_fields"] == row
        assert actual["field_availability"] == {k: "present" if k in row else "unavailable" for k in fields}
        target = row.get("underlying") in ("BTCUSDT", "ETHUSDT")
        assert actual["explicit_btc_eth_target"] == target
        assert identities[row["symbol"]] == 1
        assert actual["crypto_classification"]["status"] == "ambiguous"
        assert all(actual["crypto_classification"][k] == row.get(k) for k in ("contractType", "underlyingType"))
        assert "unavailable" in actual["account_seller_permission"]
        assert type(row["expiryDate"]) is int and row["expiryDate"] > 0 and actual["expiry_status"] == "complete"
        lots = [f for f in row["filters"] if f.get("filterType") == "LOT_SIZE"]
        assert len(lots) == 1
        expected_q = {k: {"status": "complete", "value": numeric(row[k], True)} for k in ("unit", "minQty", "maxQty")}
        expected_lot = {k: {"status": "complete", "value": numeric(lots[0][k], True)} for k in ("minQty", "maxQty", "stepSize")}
        assert expected_q == actual["quantity_fields"] and actual["lot_size_filters"] == [expected_lot]
        assert Decimal(row["minQty"]) <= Decimal(row["maxQty"])
        assert all(Decimal(row[k]) == Decimal(lots[0][k]) for k in ("minQty", "maxQty"))
        assert actual["quantity_rule_status"] == "complete" and actual["ambiguities"] == []
        assert actual["margin_fields"] == {k: {"status": "complete", "value": numeric(row[k], False)} for k in ("initialMargin", "maintenanceMargin", "minInitialMargin", "minMaintenanceMargin")}
        if target:
            targets.append(index); asset_counts[row["underlying"]] += 1
            quantity_counts[(str(row["unit"]), row["minQty"], lots[0]["stepSize"])] += 1
    assert targets == admission["cells"][0]["target_row_indices"]
    assert len(targets) == admission["cells"][0]["explicit_btc_eth_target_count"]
    contracts = exchange["optionContracts"]
    assert admission["cells"][0]["optionContracts"]["literal_value"] == contracts
    assert admission["cells"][0]["optionContracts"]["row_metadata_availability"] == [{"row_index": i, "field_availability": {k: "present" if k in r else "unavailable" for k in ("underlying", "underlyingType", "contractType")}} for i, r in enumerate(contracts)]
    server = read(raw_bodies[1]); assert isinstance(server, dict) and "code" not in server
    assert type(server["serverTime"]) is int and server["serverTime"] == admission["cells"][1]["serverTime"]
    catalogues = []
    ns = "{http://s3.amazonaws.com/doc/2006-03-01/}"
    for request, raw, actual in zip(spec["requests"][2:], raw_bodies[2:], admission["cells"][2:], strict=True):
        text = raw.decode("utf-8"); assert not re.search(r"<!\s*(DOCTYPE|ENTITY)\b", text, re.I)
        xml = ET.fromstring(text); assert xml.tag == ns + "ListBucketResult"
        def one(node, field, required=True):
            items = node.findall(ns + field); assert len(items) <= 1 and (not required or len(items) == 1)
            return (items[0].text or "") if items else None
        assert one(xml, "Prefix") == request["prefix"] == actual["prefix"]
        assert int(one(xml, "MaxKeys")) == request["max_keys"] == actual["max_keys"]
        assert one(xml, "Delimiter", False) == request.get("delimiter") == actual["delimiter"]
        truncated = one(xml, "IsTruncated"); assert truncated in ("true", "false")
        assert actual["partial_listing"] == actual["is_truncated"] == (truncated == "true")
        prefixes = [one(x, "Prefix") for x in xml.findall(ns + "CommonPrefixes")]
        contents = [{"Key": one(x, "Key"), "Size": int(one(x, "Size")), "LastModified": one(x, "LastModified", False), "ETag": one(x, "ETag", False)} for x in xml.findall(ns + "Contents")]
        assert all(x.startswith(request["prefix"]) for x in prefixes)
        assert all(x["Key"].startswith(request["prefix"]) and x["Size"] >= 0 for x in contents)
        assert len(set(prefixes)) == len(prefixes) and len({x["Key"] for x in contents}) == len(contents)
        assert len(prefixes) + len(contents) <= request["max_keys"]
        assert prefixes == actual["common_prefixes"] and contents == actual["contents"]
        assert actual["continuation_metadata"] == {k: one(xml, k, False) for k in ("Marker", "NextMarker", "ContinuationToken", "NextContinuationToken", "StartAfter", "KeyCount", "EncodingType")}
        catalogues.append({"id": request["id"], "prefixes": prefixes, "object_count": len(contents), "partial": actual["partial_listing"], "first_key": contents[0]["Key"] if contents else None, "last_key": contents[-1]["Key"] if contents else None})
    actual_size = sum(p.stat().st_size for p in OUT.iterdir()); assert actual_size <= spec["max_output_bytes"]
    resource = file(HERE / "options-resource-execution.json")
    assert resource["child_exit_code"] == 0 and resource["limit_reason"] is None
    assert resource["rss_limit_bytes"] == 256*1024**2 and resource["wall_limit_seconds"] == 120
    assert resource["peak_sampled_tree_rss_bytes"] <= resource["rss_limit_bytes"]
    report = {"status": "PASS", "reviewed_utc": datetime.now(timezone.utc).isoformat(), "source": source,
              "request_count": 4, "output_count": 6, "raw_body_bytes": capture["total_body_bytes"], "output_bytes": actual_size,
              "symbol_rows": len(rows), "target_rows": len(targets), "target_asset_counts": dict(asset_counts),
              "target_quantity_rules": [{"unit": key[0], "minQty": key[1], "stepSize": key[2], "count": count} for key, count in quantity_counts.items()],
              "target_contract_nakedSell": {r["underlying"]: r.get("nakedSell") for r in contracts if r.get("underlying") in asset_counts},
              "per_symbol_nakedSell_present_count": sum("nakedSell" in r for r in rows),
              "request_clocks": clocks, "receipt_local_mtime_evidence": publication_evidence,
              "mtime_qualification": "Local filesystem corroboration only, not independent publication attestation; immediate write-before-next-request also reviewed in frozen source.",
              "catalogues": catalogues, "resource_report_sha256": sha((HERE / "options-resource-execution.json").read_bytes()),
              "source_gate_sha256": sha(gate_path.read_bytes()), "output_sha256": complete["output_sha256"],
              "limitations": ["Structural source admission only", "Frozen crypto classification remains ambiguous", "No account seller access, affordability or historical executable chain admitted", "No new fetches or financial calculations"]}
    with (HERE / "options-metadata-review.json").open("x") as handle:
        json.dump(report, handle, indent=2, sort_keys=True); handle.write("\n")
    print(json.dumps({k: report[k] for k in ("status", "request_count", "output_count", "raw_body_bytes", "symbol_rows", "target_rows", "target_asset_counts")}))


if __name__ == "__main__":
    main()
