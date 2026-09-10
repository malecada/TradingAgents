"""Local receipt validation only; no financial accounting, fitting, or replay."""
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def article(value):
    if isinstance(value, dict):
        if value.get("code") == "360033525031" and "body" in value:
            return value
        for child in value.values():
            found = article(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = article(child)
            if found:
                return found


manifest = json.loads((ROOT / "manifest.json").read_text())
for receipt in manifest["responses"]:
    assert sha(ROOT / receipt["body_file"]) == receipt["body_sha256"]
    assert (ROOT / receipt["body_file"]).stat().st_size == receipt["body_bytes"]
assert sum(x["body_bytes"] for x in manifest["responses"]) <= 25_000_000

zpath = ROOT / "archive-index-20220512.zip"
assert sha(zpath) == (ROOT / "archive-index-20220512.CHECKSUM").read_text().split()[0]
with zipfile.ZipFile(zpath) as archive:
    assert archive.namelist() == ["LUNAUSDT-1m-2022-05-12.csv"]
    member = archive.read(archive.namelist()[0])
    rows = list(csv.reader(io.StringIO(member.decode())))  # The source has NO header.
assert len(rows) == 1440
assert [int(row[0]) for row in rows] == list(range(1652313600000, 1652400000000, 60000))
api = json.loads((ROOT / "index-price-preclose-60m.json").read_text())
assert [row[0] for row in api] == list(range(1652365800000, 1652369400000, 60000))
by_time = {int(row[0]): row for row in rows}
assert all([str(value) for value in row] == by_time[row[0]] for row in api)

html = ROOT / "funding-faq-20220402.html"
soup = BeautifulSoup(html.read_text(), "html.parser")
obj = article(json.loads(soup.select_one("script#__APP_DATA").string))
assert obj
body = obj["body"].encode()
with (ROOT / "funding-faq-20220402-body.json").open("xb") as out:
    out.write(body)
result = {
    "purpose": "Evidence validation only; no strategy or financial calculation",
    "transform": {"file": "derive_evidence.py", "sha256": sha(Path(__file__))},
    "receipt_manifest_sha256": sha(ROOT / "manifest.json"),
    "response_count": len(manifest["responses"]),
    "response_bytes": manifest["total_body_bytes"],
    "all_response_hashes_and_sizes_verified": True,
    "zip_checksum_verified": True,
    "archive": {
        "file": zpath.name,
        "sha256": sha(zpath),
        "member": "LUNAUSDT-1m-2022-05-12.csv",
        "member_sha256": hashlib.sha256(member).hexdigest(),
        "header_present": False,
        "rows": len(rows),
        "unique_sorted_complete_utc_minute_clock": True,
        "start_utc": "2022-05-12T00:00:00Z",
        "end_exclusive_utc": "2022-05-13T00:00:00Z",
    },
    "preclosure_index_comparison": {
        "api_file": "index-price-preclose-60m.json",
        "api_sha256": sha(ROOT / "index-price-preclose-60m.json"),
        "rows": len(api),
        "start_utc": "2022-05-12T14:30:00Z",
        "end_exclusive_utc": "2022-05-12T15:30:00Z",
        "all_twelve_fields_equal_archive": True,
        "raw_field8_value_frequencies": dict(collections.Counter(row[8] for row in api)),
        "field8_qualification": "Historical API labels this Number of bisic data; its units, sampling alignment and coverage of settlement inputs are not established. No missing-second count is inferred.",
        "actual_settlement_price_or_bound_established": False,
    },
    "funding_article_extraction": {
        "source_file": html.name,
        "source_sha256": sha(html),
        "wayback_snapshot_utc": "2022-04-02T12:15:00Z",
        "title": obj["title"],
        "code": obj["code"],
        "publishDate": obj.get("publishDate"),
        "lastUpdateTime": obj.get("lastUpdateTime"),
        "output_file": "funding-faq-20220402-body.json",
        "output_sha256": hashlib.sha256(body).hexdigest(),
        "derivation": "HTML script#__APP_DATA JSON recursively matched article code360033525031; unchanged UTF-8 body string",
    },
}
with (ROOT / "validation.json").open("x") as out:
    json.dump(result, out, indent=2)
    out.write("\n")
print(json.dumps(result, indent=2))
