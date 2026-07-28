"""1h klines for the xsect symbol universe (liq-fade intraday).

Kline source: Vision monthly zips (full months, cheap bulk download) for the
history up to the last fully-elapsed month, then a paginated FAPI tail
(limit=1500 per call) from the last Vision bar to now. Idempotent tail-append:
re-running only fetches months/bars not already present in the parquet store.

Output: data/xsect/klines_1h/{SYMBOL}.parquet (canonical filename, no dates)
+ data/xsect/klines_1h_manifest.json.

Usage: python scripts/fetch_xsect_klines_1h.py --symbols-file syms.txt --start 2020-06-01
"""
from __future__ import annotations

import argparse
import io
import json
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INTERVAL = "1h"
OUT_DIR = PROJECT_ROOT / "data" / "xsect" / "klines_1h"
MANIFEST = PROJECT_ROOT / "data" / "xsect" / "klines_1h_manifest.json"
VISION_URL = ("https://data.binance.vision/data/futures/um/monthly/klines/"
              "{sym}/1h/{sym}-1h-{ym}.zip")
FAPI = "https://fapi.binance.com/fapi/v1/klines"

KLINE_COLUMNS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
                  "quote_volume", "n_trades", "taker_buy_base", "taker_buy_quote", "ignore"]
OUT_COLUMNS = ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_quote_volume"]

MAX_RETRIES = 3
RETRY_SLEEP = 2.0
FAPI_SLEEP = 0.15


def _get(url: str, params: dict | None = None) -> requests.Response | None:
    """GET with timeout=30 and 3 retries (sleep 2s between attempts).

    Returns the response (even if non-200, e.g. 404) on success, or None if
    every attempt raised an exception (network error / timeout).
    """
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return requests.get(url, params=params, timeout=30)
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_SLEEP)
    print(f"  WARN: request failed after {MAX_RETRIES} attempts: {url} ({last_exc})")
    return None


def merge_tail(existing: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame:
    """Dedup existing+new on index, keep-last (new wins on overlap), sorted."""
    if existing is None or existing.empty:
        return new.sort_index()
    out = pd.concat([existing, new])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out


def _rows_to_df(rows: list) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=OUT_COLUMNS,
                             index=pd.DatetimeIndex([], tz="UTC", name="ts"))
    df = pd.DataFrame(rows, columns=KLINE_COLUMNS[: len(rows[0])])
    ts_raw = pd.to_numeric(df["open_time"])
    ts_raw = ts_raw.where(ts_raw < 10**14, ts_raw // 1000)  # normalize us -> ms
    df["ts"] = pd.to_datetime(ts_raw, unit="ms", utc=True)
    df = df.rename(columns={"taker_buy_quote": "taker_buy_quote_volume"})
    out = df.set_index("ts")[OUT_COLUMNS].astype(float)
    out.index.name = "ts"
    return out[~out.index.duplicated(keep="first")].sort_index()


def fetch_vision_month(sym: str, ym: pd.Period) -> pd.DataFrame:
    """Fetch one Vision monthly zip. Returns empty df on 404 (symbol not listed yet)."""
    url = VISION_URL.format(sym=sym, ym=ym)
    r = _get(url)
    if r is None or r.status_code != 200:
        return pd.DataFrame()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        raw = pd.read_csv(z.open(z.namelist()[0]), header=None)
    if isinstance(raw.iloc[0, 0], str) and not str(raw.iloc[0, 0]).isdigit():
        raw = raw.iloc[1:].reset_index(drop=True)  # some months ship with a header row
    raw.columns = KLINE_COLUMNS[: raw.shape[1]]
    rows = raw.to_dict("records")
    return _rows_to_df(rows)


def fetch_fapi_tail(sym: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Paginated FAPI tail from start_ms to end_ms, limit=1500 per call."""
    rows = []
    start = start_ms
    while start < end_ms:
        r = _get(FAPI, params={"symbol": sym, "interval": INTERVAL,
                                "startTime": start, "endTime": end_ms, "limit": 1500})
        if r is None or r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        rows += batch
        if len(batch) < 1500:
            break
        start = batch[-1][0] + 3_600_000  # 1h in ms
        time.sleep(FAPI_SLEEP)
    return _rows_to_df(rows)


def fetch_symbol(sym: str, start: str, existing: pd.DataFrame | None) -> pd.DataFrame:
    """Fetch missing 1h history for sym from `start` to now, tail-appending onto `existing`."""
    now = pd.Timestamp.now(tz="UTC")
    start_ts = pd.Timestamp(start, tz="UTC")

    df = existing

    # 1) Vision monthly zips, from `start` month through the last fully-elapsed month,
    #    skipping months already covered by existing data.
    last_full_month = now.tz_localize(None).to_period("M") - 1
    start_month = start_ts.tz_localize(None).to_period("M")
    if start_month <= last_full_month:
        already_covered_through = None
        if df is not None and not df.empty:
            already_covered_through = df.index.max().tz_localize(None).to_period("M")
        for month in pd.period_range(start_month, last_full_month, freq="M"):
            if already_covered_through is not None and month < already_covered_through:
                continue  # month fully present already
            monthly = fetch_vision_month(sym, month)
            if monthly.empty:
                continue
            df = merge_tail(df, monthly)
            time.sleep(0.1)

    # 2) FAPI paginated tail from last known bar (or `start` if nothing yet) to now.
    if df is not None and not df.empty:
        tail_start_ms = int(df.index.max().timestamp() * 1000) + 3_600_000
    else:
        tail_start_ms = int(start_ts.timestamp() * 1000)
    end_ms = int(now.timestamp() * 1000)
    if tail_start_ms < end_ms:
        tail = fetch_fapi_tail(sym, tail_start_ms, end_ms)
        if not tail.empty:
            df = merge_tail(df, tail)

    return df if df is not None else _rows_to_df([])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols-file", type=str, required=True,
                     help="Path to a file with one symbol per line.")
    ap.add_argument("--start", type=str, default="2020-06-01",
                     help="Earliest date to fetch from (YYYY-MM-DD, UTC).")
    args = ap.parse_args()

    symbols = [s.strip() for s in Path(args.symbols_file).read_text().splitlines() if s.strip()]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}

    print(f"{len(symbols)} symbols to fetch (1h, start={args.start})")
    for i, sym in enumerate(symbols):
        path = OUT_DIR / f"{sym}.parquet"
        existing = pd.read_parquet(path) if path.exists() else None
        df = fetch_symbol(sym, args.start, existing)
        if df is None or df.empty:
            print(f"  [{i + 1}/{len(symbols)}] {sym}: NO DATA (skipped)")
            continue
        df.to_parquet(path)
        manifest[sym] = {"first": str(df.index.min()), "last": str(df.index.max()),
                          "rows": int(len(df))}
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        print(f"  [{i + 1}/{len(symbols)}] {sym}: {len(df)} rows "
              f"({manifest[sym]['first']} -> {manifest[sym]['last']})")

    print(f"done: {len(manifest)} symbols in manifest -> {MANIFEST}")


if __name__ == "__main__":
    main()
