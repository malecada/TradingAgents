"""5m klines for the Prediction Lab (BTC/ETH RV + volume targets).

Adapted from scripts/fetch_xsect_klines_1h.py (feature/value-unlock-xs blob):
Vision monthly zips for elapsed months + paginated FAPI tail, idempotent
tail-append, per-month coverage checks (failed months retried every run,
confirmed-404 months remembered). Differences: INTERVAL=5m, n_trades kept,
output under data/predlab/klines_5m/ (canonical filenames, no dates).

Usage: python scripts/predlab_fetch_klines_5m.py [--symbols BTCUSDT ETHUSDT] [--start 2020-01-01]
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

INTERVAL = "5m"
INTERVAL_MS = 300_000
OUT_DIR = DATA_ROOT / "predlab" / "klines_5m"
MANIFEST = DATA_ROOT / "predlab" / "klines_5m_manifest.json"
MISSING_MONTHS = DATA_ROOT / "predlab" / "klines_5m_missing_months.json"
VISION_URL = ("https://data.binance.vision/data/futures/um/monthly/klines/"
              "{sym}/" + INTERVAL + "/{sym}-" + INTERVAL + "-{ym}.zip")
FAPI = "https://fapi.binance.com/fapi/v1/klines"

KLINE_COLUMNS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
                 "quote_volume", "n_trades", "taker_buy_base", "taker_buy_quote", "ignore"]
OUT_COLUMNS = ["open", "high", "low", "close", "volume", "quote_volume",
               "taker_buy_quote_volume", "n_trades"]

MAX_RETRIES = 3
RETRY_SLEEP = 2.0
FAPI_SLEEP = 0.15


def month_zip_url(sym: str, ym) -> str:
    """Vision monthly-zip URL for a symbol and a YYYY-MM month (str or Period)."""
    return VISION_URL.format(sym=sym, ym=str(ym))


def _get(url: str, params: dict | None = None) -> requests.Response | None:
    """GET with retries; 404 returned immediately (semantic not-found on Vision)."""
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
    """Dedup existing+new on index, keep-last (new wins on overlap), sorted."""
    if existing is None or existing.empty:
        return new[~new.index.duplicated(keep="last")].sort_index()
    out = pd.concat([existing, new])
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out


def month_needs_fetch(month: pd.Period, existing: pd.DataFrame | None,
                      confirmed_missing: "set[pd.Period]") -> bool:
    """True unless the month is confirmed-404 or real bars already cover it."""
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


def fetch_vision_month(sym: str, ym: pd.Period) -> "tuple[pd.DataFrame, str]":
    """One Vision monthly zip -> (df, "ok"|"not_listed"|"failed")."""
    r = _get(month_zip_url(sym, ym))
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
    return _rows_to_df(raw.to_dict("records")), "ok"


def fetch_fapi_tail(sym: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Paginated FAPI tail from start_ms to end_ms, limit=1500 per call."""
    rows = []
    start = start_ms
    while start < end_ms:
        r = _get(FAPI, params={"symbol": sym, "interval": INTERVAL,
                               "startTime": start, "endTime": end_ms, "limit": 1500})
        if r is None or r.status_code != 200:
            code = "network" if r is None else f"HTTP {r.status_code}"
            print(f"  WARN: {sym}: FAPI tail {code} at startTime={start} — stopping, retried next run")
            break
        batch = r.json()
        if not batch:
            break
        rows += batch
        if len(batch) < 1500:
            break
        start = batch[-1][0] + INTERVAL_MS
        time.sleep(FAPI_SLEEP)
    return _rows_to_df(rows)


def fetch_symbol(sym: str, start: str, existing: pd.DataFrame | None,
                 confirmed_missing: "set[pd.Period]") -> pd.DataFrame:
    """Fetch missing 5m history for sym, tail-appending onto existing."""
    now = pd.Timestamp.now(tz="UTC")
    start_ts = pd.Timestamp(start, tz="UTC")
    df = existing

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
            if status == "failed" or monthly.empty:
                continue
            df = merge_tail(df, monthly)
            time.sleep(0.1)

    if df is not None and not df.empty:
        tail_start_ms = int(df.index.max().timestamp() * 1000) + INTERVAL_MS
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
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    ap.add_argument("--start", type=str, default="2020-01-01")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    missing_raw = json.loads(MISSING_MONTHS.read_text()) if MISSING_MONTHS.exists() else {}

    print(f"{len(args.symbols)} symbols to fetch ({INTERVAL}, start={args.start})")
    for i, sym in enumerate(args.symbols):
        path = OUT_DIR / f"{sym}.parquet"
        existing = pd.read_parquet(path) if path.exists() else None
        confirmed_missing = {pd.Period(m, freq="M") for m in missing_raw.get(sym, [])}
        df = fetch_symbol(sym, args.start, existing, confirmed_missing)
        missing_raw[sym] = sorted(str(m) for m in confirmed_missing)
        MISSING_MONTHS.write_text(json.dumps(missing_raw, indent=1, sort_keys=True))
        if df is None or df.empty:
            print(f"  [{i + 1}/{len(args.symbols)}] {sym}: NO DATA (skipped)")
            continue
        df.to_parquet(path)
        manifest[sym] = {"first": str(df.index.min()), "last": str(df.index.max()),
                         "rows": int(len(df))}
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        # honest coverage note: expected bars/month ~ 8640 (5m)
        print(f"  [{i + 1}/{len(args.symbols)}] {sym}: {len(df)} rows "
              f"({manifest[sym]['first']} -> {manifest[sym]['last']})")

    print(f"done: {len(manifest)} symbols in manifest -> {MANIFEST}")


if __name__ == "__main__":
    main()
