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

MISSING_MONTHS = PROJECT_ROOT / "data" / "xsect" / "klines_1h_missing_months.json"


def _get(url: str, params: dict | None = None) -> requests.Response | None:
    """GET with timeout=30, up to 3 attempts total, flat 2s sleep between attempts.

    Retries both network exceptions and non-200 status codes EXCEPT 404, which Vision
    uses as a semantic "not found" result rather than a transient error and is returned
    immediately. Returns the last response received (even if still non-200) so callers can
    inspect status_code and log accordingly; returns None only if every attempt raised an
    exception (pure network failure, no response at all). Logs loudly when giving up.
    """
    last_exc = None
    last_resp = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, timeout=30)
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_SLEEP)
            continue
        if r.status_code == 200 or r.status_code == 404:
            return r
        last_resp = r
        if attempt < MAX_RETRIES - 1:
            print(f"  WARN: HTTP {r.status_code} on {url} (attempt {attempt + 1}/{MAX_RETRIES}), retrying")
            time.sleep(RETRY_SLEEP)
    if last_resp is not None:
        print(f"  WARN: giving up after {MAX_RETRIES} attempts, last status {last_resp.status_code}: {url}")
        return last_resp
    print(f"  WARN: request failed after {MAX_RETRIES} attempts: {url} ({last_exc})")
    return None


def merge_tail(existing: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame:
    """Dedup existing+new on index, keep-last (new wins on overlap), sorted.

    Applies the same dedup+sort even when `existing` is None/empty, so `new` is never
    passed through unchecked.
    """
    if existing is None or existing.empty:
        return new[~new.index.duplicated(keep="last")].sort_index()
    out = pd.concat([existing, new])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out


def month_needs_fetch(month: pd.Period, existing: pd.DataFrame | None,
                       confirmed_missing: set[pd.Period]) -> bool:
    """Pure decision: does this Vision month still need to be (re-)fetched?

    False only if (a) the month was previously confirmed HTTP 404 (symbol genuinely not
    listed that month -- permanently absent, safe to skip), or (b) `existing` already has
    real bars falling inside that month. Coverage is checked per-month against the actual
    data, never inferred from a single max-timestamp watermark -- a month that failed for
    an unknown reason (503, timeout, ...) has no bars and isn't in `confirmed_missing`, so
    this returns True and the caller retries it, even if later months already succeeded.
    """
    if month in confirmed_missing:
        return False
    if existing is not None and not existing.empty:
        month_start = month.to_timestamp(how="start").tz_localize("UTC")
        month_end = month.to_timestamp(how="end").tz_localize("UTC")
        if ((existing.index >= month_start) & (existing.index <= month_end)).any():
            return False
    return True


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


def fetch_vision_month(sym: str, ym: pd.Period) -> tuple[pd.DataFrame, str]:
    """Fetch one Vision monthly zip.

    Returns (df, status):
      "ok"         - fetched and parsed successfully (df has the month's bars)
      "not_listed" - confirmed HTTP 404: symbol wasn't listed that month, permanently
                     absent, safe for the caller to remember and never retry
      "failed"     - request never got a clean 200 (network failure or non-200/404 after
                     retries): unknown cause, caller must NOT treat this month as covered
    """
    url = VISION_URL.format(sym=sym, ym=ym)
    r = _get(url)
    if r is None:
        print(f"  WARN: {sym} {ym}: Vision request failed after retries (network) — leaving gap")
        return pd.DataFrame(), "failed"
    if r.status_code == 404:
        return pd.DataFrame(), "not_listed"
    if r.status_code != 200:
        print(f"  WARN: {sym} {ym}: Vision returned HTTP {r.status_code} after retries — leaving gap")
        return pd.DataFrame(), "failed"
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        raw = pd.read_csv(z.open(z.namelist()[0]), header=None)
    if isinstance(raw.iloc[0, 0], str) and not str(raw.iloc[0, 0]).isdigit():
        raw = raw.iloc[1:].reset_index(drop=True)  # some months ship with a header row
    raw.columns = KLINE_COLUMNS[: raw.shape[1]]
    rows = raw.to_dict("records")
    return _rows_to_df(rows), "ok"


def fetch_fapi_tail(sym: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Paginated FAPI tail from start_ms to end_ms, limit=1500 per call."""
    rows = []
    start = start_ms
    while start < end_ms:
        r = _get(FAPI, params={"symbol": sym, "interval": INTERVAL,
                                "startTime": start, "endTime": end_ms, "limit": 1500})
        if r is None:
            print(f"  WARN: {sym}: FAPI tail request failed after retries at startTime={start}"
                  " — stopping pagination, remaining bars will be retried next run")
            break
        if r.status_code != 200:
            print(f"  WARN: {sym}: FAPI tail got HTTP {r.status_code} after retries at "
                  f"startTime={start} — stopping pagination, remaining bars will be retried next run")
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


def fetch_symbol(sym: str, start: str, existing: pd.DataFrame | None,
                  confirmed_missing: set[pd.Period]) -> pd.DataFrame:
    """Fetch missing 1h history for sym from `start` to now, tail-appending onto `existing`.

    `confirmed_missing` is mutated in place with any newly-confirmed-404 months so the
    caller can persist it (avoids re-requesting genuinely not-listed months every run).
    """
    now = pd.Timestamp.now(tz="UTC")
    start_ts = pd.Timestamp(start, tz="UTC")

    df = existing

    # 1) Vision monthly zips, from `start` month through the last fully-elapsed month.
    #    Per-month coverage is checked against actual data (month_needs_fetch), not a
    #    single watermark, so a month that failed for an unknown reason is retried on
    #    every run instead of being silently skipped forever (see Finding 1).
    last_full_month = now.tz_localize(None).to_period("M") - 1
    start_month = start_ts.tz_localize(None).to_period("M")
    if start_month <= last_full_month:
        for month in pd.period_range(start_month, last_full_month, freq="M"):
            if not month_needs_fetch(month, df, confirmed_missing):
                continue
            monthly, status = fetch_vision_month(sym, month)
            if status == "not_listed":
                confirmed_missing.add(month)
                continue
            if status == "failed":
                continue  # not covered -> month_needs_fetch will retry it next run
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
    missing_raw = json.loads(MISSING_MONTHS.read_text()) if MISSING_MONTHS.exists() else {}

    print(f"{len(symbols)} symbols to fetch (1h, start={args.start})")
    for i, sym in enumerate(symbols):
        path = OUT_DIR / f"{sym}.parquet"
        existing = pd.read_parquet(path) if path.exists() else None
        confirmed_missing = {pd.Period(m, freq="M") for m in missing_raw.get(sym, [])}
        df = fetch_symbol(sym, args.start, existing, confirmed_missing)
        missing_raw[sym] = sorted(str(m) for m in confirmed_missing)
        MISSING_MONTHS.write_text(json.dumps(missing_raw, indent=1, sort_keys=True))
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
