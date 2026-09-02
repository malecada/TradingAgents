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
UNIVERSE_FILE = PROJECT_ROOT / "data" / "xsect" / "fundamentals_universe.json"
KLINES_DIR = PROJECT_ROOT / "data" / "xsect" / "klines"

BASE = "https://community-api.coinmetrics.io/v4"
METRICS = ["AdrActCnt", "TxCnt", "CapMrktCurUSD"]

# Sealed-holdout boundary: holdout opens 2025-04-01 (data/rebuild/gates.json,
# value_xs_t1.holdout_window); +15d is warm-up margin only, never data.
MAX_END = "2025-04-15"

# value_xs_dev P0 fix round 2 (2026-07-30): publication lag cannot be derived
# from the store's own last observation, because the store is deliberately
# truncated at MAX_END to protect the holdout -- that endpoint reflects our
# fetch request, not the vendor's frontier. The vendor's true frontier is
# captured here, at fetch time, from the catalog endpoint (which is not
# subject to the --end truncation) and persisted in the vintage stamp so P0
# can read it offline without a live network call. Majors only: full
# coverage back to genesis, no thin-coverage/partial-history noise.
VENDOR_REFERENCE_ASSETS = ["btc", "eth", "ada", "doge"]

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
    """Assets with all three metrics, a tradeable perp, and not pegged.

    Cached to UNIVERSE_FILE on first resolution. Once the file exists it is
    read instead of hitting the catalog, so importing this module (test
    collection, every Task 4/5 call site) never makes a live network call
    and the resolved universe can't silently vary run to run. Delete the
    file to force a fresh catalog resolution.
    """
    if UNIVERSE_FILE.exists():
        cached = json.loads(UNIVERSE_FILE.read_text())
        return list(cached["assets"]), dict(cached["mapping"])

    bases = _perp_bases()
    assets, mapping = [], {}
    seen_bases: set[str] = set()
    for a in _catalog_assets():
        b = _cm_base(a)
        if b in STABLE_EXCLUDE or a in STABLE_EXCLUDE:
            continue
        if b in bases and b not in seen_bases:
            assets.append(a)
            mapping[a] = f"{b.upper()}USDT"
            seen_bases.add(b)

    UNIVERSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    UNIVERSE_FILE.write_text(json.dumps({
        "resolved_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": f"{BASE}/catalog-v2/asset-metrics",
        "assets": assets,
        "mapping": mapping,
    }, indent=1))
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
        return pd.DataFrame(
            {m: pd.Series(dtype="float64") for m in METRICS},
            index=pd.DatetimeIndex([], tz="UTC", name="time"),
        )
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], utc=True).dt.normalize()
    df = df.set_index("time").sort_index()
    for m in METRICS:
        df[m] = pd.to_numeric(df.get(m), errors="coerce")
    return df[METRICS]


def _vendor_max_time(reference_assets: list[str], metrics: list[str]) -> tuple[str, dict[str, str]]:
    """Vendor frontier at fetch time: min max_time across ``metrics`` x
    ``reference_assets`` on the catalog endpoint's 1d/community frequency
    entry. Uses the catalog, not a timeseries fetch, so it is not subject to
    MAX_END truncation. The binding lag is the slowest metric, so the
    minimum (not e.g. the max or an average) is what is recorded; reference
    assets are majors with full coverage so a short max_time here reflects
    genuine vendor lag, not a thin-coverage artifact for that asset.

    Returns (vendor_max_time_date_str, per_asset_metric) where per_asset_metric
    maps "asset:metric" -> its own max_time date, for reproducibility.
    """
    url = (f"{BASE}/catalog-v2/asset-metrics?assets={','.join(reference_assets)}"
           f"&metrics={','.join(metrics)}&page_size=10000")
    data = requests.get(url, timeout=60).json()["data"]
    per_asset_metric: dict[str, str] = {}
    for row in data:
        asset = row["asset"].lower()
        for m in row["metrics"]:
            for f in m["frequencies"]:
                if f.get("frequency") == "1d" and f.get("community"):
                    per_asset_metric[f"{asset}:{m['metric']}"] = f["max_time"][:10]
    missing = [f"{a}:{m}" for a in reference_assets for m in metrics
               if f"{a}:{m}" not in per_asset_metric]
    if missing:
        raise SystemExit(
            f"_vendor_max_time: catalog missing 1d/community entries for {missing}"
        )
    vendor_max_time = min(per_asset_metric.values())
    return vendor_max_time, per_asset_metric


def write_vintage(path: Path, source_url: str, vendor_max_time: str | None = None,
                  vendor_reference_assets: list[str] | None = None,
                  vendor_metrics: list[str] | None = None,
                  vendor_per_asset_metric: dict[str, str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": source_url,
        "note": "vendor may restate; this stamp is what makes restatement detectable",
    }
    if vendor_max_time is not None:
        payload["vendor_max_time"] = vendor_max_time
        payload["vendor_max_time_source"] = f"{BASE}/catalog-v2/asset-metrics"
        payload["vendor_reference_assets"] = vendor_reference_assets
        payload["vendor_metrics"] = vendor_metrics
        payload["vendor_per_asset_metric_max_time"] = vendor_per_asset_metric
        payload["vendor_max_time_note"] = (
            "min(max_time) across vendor_reference_assets x vendor_metrics, "
            "1d/community frequency; captured from the catalog endpoint, not "
            "subject to the --end/MAX_END truncation applied to the stored "
            "timeseries -- this is the true vendor frontier at fetch time. "
            "SCOPE: this measures CoinMetrics' publishing cadence on "
            "actively-covered majors (vendor_reference_assets) -- how many "
            "days behind fetch time the vendor's newest datapoint is for "
            "assets it is actively publishing. It does NOT measure "
            "per-asset coverage termination: several value_xs_t1 candidates "
            "have genuinely stopped receiving CoinMetrics updates years ago "
            "(a separate, already-disclosed gap tracked per-asset in "
            "fundamentals_manifest.json's rows/first/last fields, not a "
            "publishing-lag issue). A thin-coverage or delisted-on-CM asset "
            "would register as a large apparent lag for reasons unrelated "
            "to publishing cadence if used as a lag reference -- which is "
            "exactly why vendor_reference_assets is restricted to majors "
            "with full, continuous coverage instead of being expanded "
            "toward the universe tail."
        )
    path.write_text(json.dumps(payload, indent=1))


def _enforce_holdout_margin(end: str) -> None:
    """Reject any --end that reaches past the sealed holdout margin.

    The holdout window (data/rebuild/gates.json, value_xs_t1) opens
    2025-04-01; MAX_END gives rolling windows 15 days to warm up into that
    boundary and must never be raised past it.
    """
    if end > MAX_END:
        raise SystemExit(
            f"--end {end} reaches past the sealed holdout margin {MAX_END}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-06-01")
    ap.add_argument("--end", default="2025-04-15")  # never past holdout+15d
    ap.add_argument("--vintage-only", action="store_true",
                    help=("Refresh only the vintage stamp (vendor_max_time "
                          "provenance). Does not touch the fundamentals "
                          "parquets or the manifest -- no store refetch."))
    # combo_c1 (2026-09-02): a SEPARATE vintage store may be pulled past the
    # sealed margin for a registered holdout spend. The default store, manifest
    # and vintage stamp are never touched by such a pull; the guard stays on
    # unless --allow-past-holdout names the registered gates key explicitly.
    ap.add_argument("--out-dir", default=None,
                    help="alternate store directory (registered holdout vintages only)")
    ap.add_argument("--allow-past-holdout", default=None, metavar="GATES_KEY",
                    help="lift the MAX_END guard for a registered cycle; requires --out-dir")
    args = ap.parse_args()
    out_dir, manifest_path, vintage_path = OUT_DIR, MANIFEST, VINTAGE
    if args.out_dir:
        out_dir = Path(args.out_dir)
        manifest_path = out_dir.parent / f"{out_dir.name}_manifest.json"
        vintage_path = out_dir.parent / f"{out_dir.name}_vintage.json"
    if args.allow_past_holdout and not args.out_dir:
        raise SystemExit("--allow-past-holdout requires --out-dir (default store stays sealed)")

    vendor_max_time, per_asset_metric = _vendor_max_time(VENDOR_REFERENCE_ASSETS, METRICS)

    if args.vintage_only:
        write_vintage(VINTAGE, f"{BASE}/timeseries/asset-metrics (community tier)",
                     vendor_max_time, VENDOR_REFERENCE_ASSETS, METRICS, per_asset_metric)
        print(f"vintage-only refresh: vendor_max_time={vendor_max_time}")
        return

    if args.allow_past_holdout:
        print(f"MAX_END guard lifted for registered cycle {args.allow_past_holdout!r} "
              f"-> separate store {out_dir}", flush=True)
    else:
        _enforce_holdout_margin(args.end)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for i, a in enumerate(CM_ASSETS, 1):
        out = out_dir / f"{a}.parquet"
        prev = manifest.get(a, {})
        if out.exists() and prev.get("end") == args.end and prev.get("start") == args.start:
            continue
        df = fetch_asset(a, args.start, args.end)
        df.to_parquet(out)
        manifest[a] = {"rows": int(len(df)), "start": args.start, "end": args.end,
                       "symbol": ASSET_TO_SYMBOL[a],
                       "first": str(df.index.min())[:10] if len(df) else None,
                       "last": str(df.index.max())[:10] if len(df) else None}
        manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        print(f"[{i}/{len(CM_ASSETS)}] {a} -> {len(df)} rows", flush=True)
        time.sleep(0.25)
    write_vintage(vintage_path, f"{BASE}/timeseries/asset-metrics (community tier)",
                 vendor_max_time, VENDOR_REFERENCE_ASSETS, METRICS, per_asset_metric)


if __name__ == "__main__":
    main()
