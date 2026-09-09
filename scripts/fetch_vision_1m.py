"""1-minute klines from Binance Vision monthly zips (exec_pf, charter 2026-09-03).

Idempotent, manifest-tracked, parallel. For each symbol the month range is
clipped to the symbol's 1h-store coverage (no request for months the symbol
did not trade). 404 = not listed that month, recorded in the confirmed-missing
file and never re-requested; any other failure is retried on the next run.

Output: data/xsect/klines_1m/{SYM}.parquet  (UTC open-time index `ts`,
columns open/high/low/close/volume/quote_volume/n_trades, float64 except
n_trades) + data/xsect/klines_1m_manifest.json + klines_1m_missing_months.json.

Usage: python scripts/fetch_vision_1m.py --symbols-file data/xsect/exec_pf_symbols.txt \
           --start 2020-12 --end 2025-03 --workers 8
"""
from __future__ import annotations

import argparse
import io
import json
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/xsect/klines_1m"
MANIFEST = ROOT / "data/xsect/klines_1m_manifest.json"
MISSING = ROOT / "data/xsect/klines_1m_missing_months.json"
KL1H_MANIFEST = ROOT / "data/xsect/klines_1h_manifest.json"
URL = "https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1m/{sym}-1m-{ym}.zip"
HOLDOUT_CAP = pd.Period("2025-03", freq="M")

COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "n_trades", "taker_buy_base", "taker_buy_quote", "ignore"]
KEEP = ["open", "high", "low", "close", "volume", "quote_volume", "n_trades"]


def _get(url: str, retries: int = 4) -> requests.Response | None:
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=60)
        except requests.RequestException:
            time.sleep(2.0 * (i + 1))
            continue
        if r.status_code in (200, 404):
            return r
        last = r
        time.sleep(2.0 * (i + 1))
    return last


def parse_zip(content: bytes) -> pd.DataFrame:
    """Parse one Vision monthly kline zip (header row optional)."""
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        name = z.namelist()[0]
        raw = z.read(name)
    first = raw[:20]
    header = 0 if first.startswith(b"open_time") else None
    df = pd.read_csv(io.BytesIO(raw), header=header)
    df.columns = COLS[: df.shape[1]]
    ts = pd.to_numeric(df["open_time"])
    if ts.max() > 1e14:          # microseconds (Vision switched units in 2025)
        ts = ts // 1000
    idx = pd.to_datetime(ts, unit="ms", utc=True)
    out = df[KEEP].astype({c: "float64" for c in KEEP if c != "n_trades"})
    out["n_trades"] = out["n_trades"].astype("int64")
    out.index = pd.DatetimeIndex(idx, name="ts")
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out


def fetch_month(sym: str, month: pd.Period) -> tuple[pd.Period, str, pd.DataFrame | None]:
    r = _get(URL.format(sym=sym, ym=str(month)))
    if r is None:
        return month, "failed", None
    if r.status_code == 404:
        return month, "not_listed", None
    if r.status_code != 200:
        return month, "failed", None
    try:
        return month, "ok", parse_zip(r.content)
    except Exception as exc:  # corrupt zip -> retry next run
        print(f"  WARN {sym} {month}: parse error {exc}")
        return month, "failed", None


def months_for(sym: str, start: pd.Period, end: pd.Period, kl1h: dict) -> list[pd.Period]:
    lo, hi = start, min(end, HOLDOUT_CAP)
    if sym in kl1h:
        f = pd.Timestamp(kl1h[sym]["first"]).tz_localize(None).to_period("M")
        l = pd.Timestamp(kl1h[sym]["last"]).tz_localize(None).to_period("M")
        lo, hi = max(lo, f), min(hi, l)
    if hi < lo:
        return []
    return list(pd.period_range(lo, hi, freq="M"))


def month_covered(existing: pd.DataFrame | None, month: pd.Period) -> bool:
    if existing is None or existing.empty:
        return False
    a = month.to_timestamp(how="start").tz_localize("UTC")
    b = month.to_timestamp(how="end").tz_localize("UTC")
    return bool(((existing.index >= a) & (existing.index <= b)).any())


def fetch_symbol(sym: str, months: list[pd.Period], missing: set[str], workers: int) -> tuple[pd.DataFrame | None, list[str]]:
    path = OUT_DIR / f"{sym}.parquet"
    existing = pd.read_parquet(path) if path.exists() else None
    todo = [m for m in months if str(m) not in missing and not month_covered(existing, m)]
    if not todo:
        return existing, []
    parts, newly_missing = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_month, sym, m): m for m in todo}
        for fut in as_completed(futs):
            month, status, df = fut.result()
            if status == "not_listed":
                newly_missing.append(str(month))
            elif status == "ok" and df is not None and not df.empty:
                parts.append(df)
    if parts:
        new = pd.concat(parts)
        existing = new if existing is None else pd.concat([existing, new])
        existing = existing[~existing.index.duplicated(keep="last")].sort_index()
        existing.to_parquet(path)
    return existing, newly_missing


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols-file", required=True)
    ap.add_argument("--start", default="2020-12")
    ap.add_argument("--end", default="2025-03")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    syms = [s.strip() for s in Path(args.symbols_file).read_text().splitlines() if s.strip()]
    start, end = pd.Period(args.start, freq="M"), pd.Period(args.end, freq="M")
    if end > HOLDOUT_CAP:
        raise SystemExit(f"end {end} past the dev cap {HOLDOUT_CAP} (H3 dev-only cycle)")
    kl1h = json.loads(KL1H_MANIFEST.read_text()) if KL1H_MANIFEST.exists() else {}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    missing = json.loads(MISSING.read_text()) if MISSING.exists() else {}
    t0 = time.time()
    for i, sym in enumerate(syms):
        months = months_for(sym, start, end, kl1h)
        miss = set(missing.get(sym, []))
        df, newly = fetch_symbol(sym, months, miss, args.workers)
        if newly:
            missing[sym] = sorted(miss | set(newly))
            MISSING.write_text(json.dumps(missing, indent=1, sort_keys=True))
        if df is None or df.empty:
            print(f"[{i+1}/{len(syms)}] {sym}: NO DATA ({len(months)} months requested)", flush=True)
            continue
        covered = sum(month_covered(df, m) for m in months)
        manifest[sym] = {"first": str(df.index.min()), "last": str(df.index.max()), "rows": int(len(df)),
                         "months_requested": len(months), "months_covered": int(covered),
                         "months_not_listed": len(missing.get(sym, []))}
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        print(f"[{i+1}/{len(syms)}] {sym}: {len(df)} rows, {covered}/{len(months)} months "
              f"({df.index.min().date()} -> {df.index.max().date()}) t={time.time()-t0:.0f}s", flush=True)
    print(f"done: {len(manifest)} symbols in {time.time()-t0:.0f}s -> {MANIFEST}")


if __name__ == "__main__":
    main()
