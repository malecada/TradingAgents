"""CoinMetrics community fundamentals store for value_xs_t1.

Free tier, no API key. Serves AdrActCnt, TxCnt, CapMrktCurUSD from 2017 for
132 assets including delisted names, so the store inherits the survivorship
safety of the 799-symbol perp store.

Coverage discipline follows fetch_xsect_klines_1h.py: per-asset manifest,
interior gaps retried rather than silently skipped, explicit vintage stamp.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "xsect" / "fundamentals"
MANIFEST = PROJECT_ROOT / "data" / "xsect" / "fundamentals_manifest.json"
VINTAGE = PROJECT_ROOT / "data" / "xsect" / "fundamentals_vintage.json"
KLINES_DIR = PROJECT_ROOT / "data" / "xsect" / "klines"

BASE = "https://community-api.coinmetrics.io/v4"
METRICS = ["AdrActCnt", "TxCnt", "CapMrktCurUSD"]

# Stablecoins and pegged assets: excluded because a value ratio on a pegged
# asset is meaningless and the names are not directional trades.
STABLE_EXCLUDE = {"usdc", "frax", "paxg", "xaut", "usdt", "dai", "busd",
                  "gusd", "husd", "tusd", "usdp"}

# CoinMetrics ids carry chain suffixes for bridged/wrapped variants
# (matic_eth, trx_eth, ...). The perp trades the native asset, so the suffix
# is stripped for symbol mapping. Verified against the store in Step 5.
def _cm_base(asset: str) -> str:
    return asset.split("_")[0]


def _catalog_assets() -> list[str]:
    url = (f"{BASE}/catalog-v2/asset-metrics?metrics={','.join(METRICS)}"
           f"&page_size=10000")
    data = requests.get(url, timeout=60).json()["data"]
    need = set(METRICS)
    out = []
    for row in data:
        got = {m["metric"] for m in row["metrics"]
               if any(f.get("community") for f in m["frequencies"])}
        if need <= got:
            out.append(row["asset"].lower())
    return sorted(out)


def _perp_bases() -> set[str]:
    return {p.stem[:-4].lower() for p in KLINES_DIR.glob("*USDT.parquet")}


def _resolve_universe() -> tuple[list[str], dict[str, str]]:
    """Assets with all three metrics, a tradeable perp, and not pegged."""
    bases = _perp_bases()
    assets, mapping = [], {}
    for a in _catalog_assets():
        b = _cm_base(a)
        if b in STABLE_EXCLUDE or a in STABLE_EXCLUDE:
            continue
        if b in bases and b not in {_cm_base(x) for x in assets}:
            assets.append(a)
            mapping[a] = f"{b.upper()}USDT"
    return assets, mapping


CM_ASSETS, ASSET_TO_SYMBOL = _resolve_universe()


def fetch_asset(asset: str, start: str, end: str) -> pd.DataFrame:
    """Daily metrics for one asset, UTC-indexed, paginated."""
    rows, url = [], (
        f"{BASE}/timeseries/asset-metrics?assets={asset}"
        f"&metrics={','.join(METRICS)}&frequency=1d"
        f"&start_time={start}&end_time={end}&page_size=10000"
    )
    while url:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        payload = r.json()
        rows.extend(payload.get("data", []))
        url = payload.get("next_page_url")
        if url:
            time.sleep(0.2)
    if not rows:
        return pd.DataFrame(columns=METRICS)
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], utc=True).dt.normalize()
    df = df.set_index("time").sort_index()
    for m in METRICS:
        df[m] = pd.to_numeric(df.get(m), errors="coerce")
    return df[METRICS]


def write_vintage(path: Path, source_url: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "note": "vendor may restate; this stamp is what makes restatement detectable",
    }, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-06-01")
    ap.add_argument("--end", default="2025-04-15")  # never past holdout+15d
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    for i, a in enumerate(CM_ASSETS, 1):
        out = OUT_DIR / f"{a}.parquet"
        if out.exists() and manifest.get(a, {}).get("end") == args.end:
            continue
        df = fetch_asset(a, args.start, args.end)
        df.to_parquet(out)
        manifest[a] = {"rows": int(len(df)), "start": args.start, "end": args.end,
                       "symbol": ASSET_TO_SYMBOL[a],
                       "first": str(df.index.min())[:10] if len(df) else None,
                       "last": str(df.index.max())[:10] if len(df) else None}
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        print(f"[{i}/{len(CM_ASSETS)}] {a} -> {len(df)} rows")
        time.sleep(0.25)
    write_vintage(VINTAGE, f"{BASE}/timeseries/asset-metrics (community tier)")


if __name__ == "__main__":
    main()
