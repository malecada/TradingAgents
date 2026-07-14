"""Bulk daily klines for ALL Binance USDT-M perps ever listed (incl. delisted).

Symbol enumeration: S3 listing of data.binance.vision (includes delisted symbols).
Kline source: fapi /fapi/v1/klines (works for most delisted symbols); fallback to
data.binance.vision monthly zips when fapi returns nothing.
"""
import argparse
import io
import json
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
PREFIX = "data/futures/um/daily/klines/"
FAPI = "https://fapi.binance.com/fapi/v1/klines"
OUT = Path("data/xsect/klines")
START_MS = int(pd.Timestamp("2019-09-01", tz="UTC").timestamp() * 1000)
END_MS = int(pd.Timestamp("2026-07-02", tz="UTC").timestamp() * 1000)


def list_all_symbols() -> list[str]:
    symbols, marker = [], None
    while True:
        params = {"delimiter": "/", "prefix": PREFIX}
        if marker:
            params["marker"] = marker
        r = requests.get(S3, params=params, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        ns = {"s3": root.tag.split("}")[0].strip("{")}
        prefixes = [p.find("s3:Prefix", ns).text for p in root.findall("s3:CommonPrefixes", ns)]
        symbols += [p[len(PREFIX):].strip("/") for p in prefixes]
        if root.find("s3:IsTruncated", ns) is not None and root.find("s3:IsTruncated", ns).text == "true":
            marker = prefixes[-1]
        else:
            break
    return sorted(s for s in symbols if s.endswith("USDT"))


def fetch_fapi(symbol: str) -> pd.DataFrame:
    rows, start = [], START_MS
    while True:
        r = requests.get(FAPI, params={"symbol": symbol, "interval": "1d",
                                        "startTime": start, "endTime": END_MS, "limit": 1500},
                         timeout=30)
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        rows += batch
        if len(batch) < 1500:
            break
        start = batch[-1][0] + 86_400_000
        time.sleep(0.15)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume",
                                     "close_time", "quote_volume", "n", "tbv", "tbqv", "x"])
    df["ts"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    out = df.set_index("ts")[["open", "high", "low", "close", "quote_volume"]].astype(float)
    return out[~out.index.duplicated(keep="first")].sort_index()


def fetch_vision_monthly(symbol: str) -> pd.DataFrame:
    """Fallback: iterate monthly zips 2019-09..2026-06 for delisted symbols fapi refuses."""
    frames = []
    for month in pd.period_range("2019-09", "2026-06", freq="M"):
        url = (f"https://data.binance.vision/data/futures/um/monthly/klines/"
               f"{symbol}/1d/{symbol}-1d-{month}.zip")
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            continue
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            raw = pd.read_csv(z.open(z.namelist()[0]), header=None)
        if isinstance(raw.iloc[0, 0], str) and not str(raw.iloc[0, 0]).isdigit():
            raw = raw.iloc[1:].reset_index(drop=True)  # some months ship with header row
        raw.columns = ["open_time", "open", "high", "low", "close", "volume", "close_time",
                       "quote_volume", "n", "tbv", "tbqv", "x"][: raw.shape[1]]
        frames.append(raw)
        time.sleep(0.1)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames)
    ts = pd.to_numeric(df["open_time"])
    # vision switched to microseconds in 2025 — normalize to ms
    ts = ts.where(ts < 10**14, ts // 1000)
    df["ts"] = pd.to_datetime(ts, unit="ms", utc=True)
    out = df.set_index("ts")[["open", "high", "low", "close", "quote_volume"]].astype(float)
    return out[~out.index.duplicated(keep="first")].sort_index()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", type=str, default=None,
                         help="Comma-separated symbol list to restrict the run to (smoke/debug mode). "
                              "Writes to klines_manifest_smoke.json instead of the full manifest. "
                              "Default (omitted): full enumeration via list_all_symbols().")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}

    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
        manifest_path = "data/xsect/klines_manifest_smoke.json"
    else:
        symbols = list_all_symbols()
        manifest_path = "data/xsect/klines_manifest.json"

    print(f"{len(symbols)} USDT symbols enumerated (incl. delisted)")
    for i, sym in enumerate(symbols):
        path = OUT / f"{sym}.parquet"
        if path.exists():
            df = pd.read_parquet(path)
        else:
            df = fetch_fapi(sym)
            if df.empty:
                df = fetch_vision_monthly(sym)
            if df.empty:
                print(f"  {sym}: NO DATA (skipped)")
                continue
            df.to_parquet(path)
        manifest[sym] = {"first": str(df.index.min()), "last": str(df.index.max()), "rows": len(df)}
        if i % 25 == 0:
            print(f"  [{i}/{len(symbols)}] {sym}: {len(df)} rows")
    json.dump(manifest, open(manifest_path, "w"), indent=1)
    print(f"done: {len(manifest)} symbols stored -> {manifest_path}")


if __name__ == "__main__":
    main()
