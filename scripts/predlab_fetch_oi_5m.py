"""5-minute open-interest + positioning metrics from Binance Vision daily zips.

Source: data/futures/um/daily/metrics/{SYM}/{SYM}-metrics-{YYYY-MM-DD}.zip
(5-min cadence, available from ~2021-01). Same idempotent coverage semantics
as the kline fetchers: per-day coverage checked against actual data; confirmed
HTTP-404 days remembered; unknown failures retried next run.

Output: data/predlab/oi_5m/{SYM}.parquet (canonical name, DatetimeIndex UTC,
columns oi, oi_value, top_ls_accounts, top_ls_positions, ls_accounts,
taker_ls_vol) + manifest + missing-days json.

Usage: python scripts/predlab_fetch_oi_5m.py --symbols BTCUSDT ETHUSDT --start 2021-01-01
"""
from __future__ import annotations

import argparse
import io
import json
import os
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
OUT_DIR = DATA_ROOT / "predlab" / "oi_5m"
MANIFEST = DATA_ROOT / "predlab" / "oi_5m_manifest.json"
MISSING = DATA_ROOT / "predlab" / "oi_5m_missing_days.json"

URL = ("https://data.binance.vision/data/futures/um/daily/metrics/"
       "{sym}/{sym}-metrics-{day}.zip")

RENAME = {
    "sum_open_interest": "oi",
    "sum_open_interest_value": "oi_value",
    "count_toptrader_long_short_ratio": "top_ls_accounts",
    "sum_toptrader_long_short_ratio": "top_ls_positions",
    "count_long_short_ratio": "ls_accounts",
    "sum_taker_long_short_vol_ratio": "taker_ls_vol",
}
OUT_COLUMNS = list(RENAME.values())

MAX_RETRIES = 3
RETRY_SLEEP = 2.0


def day_zip_url(sym: str, day: pd.Timestamp) -> str:
    return URL.format(sym=sym, day=day.strftime("%Y-%m-%d"))


def parse_csv(text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text))
    ts = pd.to_datetime(df["create_time"], utc=True)
    out = df.rename(columns=RENAME)[OUT_COLUMNS].astype(float)
    out.index = pd.DatetimeIndex(ts, name="ts")
    return out[~out.index.duplicated(keep="first")].sort_index()


def merge_days(existing: "pd.DataFrame | None", new: pd.DataFrame) -> pd.DataFrame:
    if existing is None or existing.empty:
        return new[~new.index.duplicated(keep="last")].sort_index()
    out = pd.concat([existing, new])
    return out[~out.index.duplicated(keep="last")].sort_index()


def day_needs_fetch(day: pd.Timestamp, existing: "pd.DataFrame | None",
                    confirmed_missing: "set[pd.Timestamp]") -> bool:
    if day in confirmed_missing:
        return False
    if existing is not None and not existing.empty:
        start = day.tz_localize("UTC") if day.tz is None else day
        end = start + pd.Timedelta(days=1)
        if ((existing.index >= start) & (existing.index < end)).any():
            return False
    return True


def _get(url: str) -> "requests.Response | None":
    last = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=30)
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_SLEEP)
            continue
        if r.status_code in (200, 404):
            return r
        last = r
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_SLEEP)
    return last


def fetch_symbol(sym: str, start: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{sym}.parquet"
    existing = pd.read_parquet(path) if path.exists() else None
    missing_raw = json.loads(MISSING.read_text()) if MISSING.exists() else {}
    confirmed = {pd.Timestamp(d) for d in missing_raw.get(sym, [])}

    yesterday = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize() - pd.Timedelta(days=1)
    days = pd.date_range(start, yesterday, freq="D")
    df = existing
    fetched = 0
    for i, day in enumerate(days):
        if not day_needs_fetch(day, df, confirmed):
            continue
        r = _get(day_zip_url(sym, day))
        if r is None or (r.status_code not in (200, 404)):
            continue  # unknown failure -> retried next run
        if r.status_code == 404:
            confirmed.add(day)
            continue
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            text = z.read(z.namelist()[0]).decode()
        df = merge_days(df, parse_csv(text))
        fetched += 1
        if fetched % 100 == 0:
            df.to_parquet(path)
            print(f"  {sym}: {fetched} days fetched (through {day.date()})", flush=True)
        time.sleep(0.05)
    if df is not None and not df.empty:
        df.to_parquet(path)
        manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
        manifest[sym] = {"first": str(df.index.min()), "last": str(df.index.max()),
                         "rows": int(len(df))}
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    missing_raw[sym] = sorted(str(d.date()) for d in confirmed)
    MISSING.write_text(json.dumps(missing_raw, indent=1, sort_keys=True))
    print(f"{sym}: done, {fetched} new days, rows={0 if df is None else len(df)}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    ap.add_argument("--start", default="2021-01-01")
    args = ap.parse_args()
    for sym in args.symbols:
        fetch_symbol(sym, args.start)


if __name__ == "__main__":
    main()
