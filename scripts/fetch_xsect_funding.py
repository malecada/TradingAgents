"""Funding-rate store for the 799-symbol xsect universe (carry_xs_t1).

Fetches full /fapi/v1/fundingRate history per symbol into
data/xsect/funding/{SYMBOL}.parquet (canonical name, idempotent tail-append),
writes funding_manifest.json and a klines-vs-funding coverage report.

Usage: python scripts/fetch_xsect_funding.py [--symbols BTCUSDT ...] [--report-only]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.strategies.v3.features._http import with_backoff  # noqa: E402

URL = "https://fapi.binance.com/fapi/v1/fundingRate"
FUND_DIR = PROJECT_ROOT / "data" / "xsect" / "funding"
MANIFEST = PROJECT_ROOT / "data" / "xsect" / "funding_manifest.json"
COVERAGE = PROJECT_ROOT / "data" / "xsect" / "funding_coverage.json"
KLINES_MANIFEST = PROJECT_ROOT / "data" / "xsect" / "klines_manifest.json"
FETCH_END = pd.Timestamp("2026-07-03", tz="UTC")  # klines store ends 2026-07-02


def merge_prints(existing: pd.DataFrame | None, rows: list[dict]) -> pd.DataFrame:
    new = pd.DataFrame(rows)
    if new.empty:
        return existing if existing is not None else _empty()
    new["fundingTime"] = pd.to_datetime(new["fundingTime"], unit="ms", utc=True)
    new["fundingRate"] = new["fundingRate"].astype(float)
    new = new.set_index("fundingTime")[["fundingRate"]]
    df = new if existing is None else pd.concat([existing, new])
    return df[~df.index.duplicated(keep="last")].sort_index()


def _empty() -> pd.DataFrame:
    idx = pd.DatetimeIndex([], tz="UTC", name="fundingTime")
    return pd.DataFrame({"fundingRate": pd.Series([], dtype=float)}, index=idx)


def manifest_entry(df: pd.DataFrame) -> dict:
    return {"first": str(df.index[0]), "last": str(df.index[-1]), "rows": int(len(df))}


def _fetch_page(symbol: str, start_ms: int, limit: int = 1000) -> list[dict]:
    r = requests.get(URL, params={"symbol": symbol, "startTime": start_ms,
                                  "endTime": int(FETCH_END.timestamp() * 1000),
                                  "limit": limit}, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_symbol(symbol: str, existing: pd.DataFrame | None) -> pd.DataFrame:
    cursor = 0 if existing is None or existing.empty else \
        int(existing.index[-1].timestamp() * 1000) + 1
    df = existing
    while True:
        page = with_backoff(lambda: _fetch_page(symbol, cursor))
        if not page:
            break
        df = merge_prints(df, page)
        last = page[-1]["fundingTime"]
        if last + 1 <= cursor or len(page) < 1000:
            break
        cursor = last + 1
        time.sleep(0.15)
    return df if df is not None else _empty()


def write_coverage(manifest: dict) -> None:
    km = json.loads(KLINES_MANIFEST.read_text())
    cov, missing = {}, []
    for sym, ke in km.items():
        fe = manifest.get(sym)
        if fe is None or fe["rows"] == 0:
            missing.append(sym)
            cov[sym] = {"kline_first": ke["first"], "kline_last": ke["last"],
                        "funding_first": None, "funding_last": None,
                        "n_prints": 0, "day_coverage_frac": 0.0}
            continue
        k0, k1 = pd.Timestamp(ke["first"]), pd.Timestamp(ke["last"])
        f = pd.read_parquet(FUND_DIR / f"{sym}.parquet")
        days_with = f.loc[k0:k1 + pd.Timedelta(days=1)].index.normalize().nunique()
        n_days = (k1 - k0).days + 1
        cov[sym] = {"kline_first": ke["first"], "kline_last": ke["last"],
                    "funding_first": fe["first"], "funding_last": fe["last"],
                    "n_prints": fe["rows"],
                    "day_coverage_frac": round(days_with / max(n_days, 1), 4)}
    fracs = [c["day_coverage_frac"] for c in cov.values()]
    cov["_summary"] = {
        "n_symbols_klines": len(km), "n_missing_funding": len(missing),
        "missing": sorted(missing),
        "median_day_coverage": float(pd.Series(fracs).median()),
        "n_below_90pct": int(sum(x < 0.9 for x in fracs)),
    }
    COVERAGE.write_text(json.dumps(cov, indent=1, sort_keys=True))
    print(json.dumps(cov["_summary"], indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=None)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    FUND_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    if not args.report_only:
        symbols = args.symbols or sorted(json.loads(KLINES_MANIFEST.read_text()))
        for i, sym in enumerate(symbols):
            path = FUND_DIR / f"{sym}.parquet"
            existing = pd.read_parquet(path) if path.exists() else None
            df = fetch_symbol(sym, existing)
            if len(df):
                df.to_parquet(path)
                manifest[sym] = manifest_entry(df)
            else:
                manifest[sym] = {"first": None, "last": None, "rows": 0}
            if (i + 1) % 25 == 0:
                print(f"[{i + 1}/{len(symbols)}] {sym}: {manifest[sym]['rows']} prints")
                MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
        MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    write_coverage(manifest)


if __name__ == "__main__":
    main()
