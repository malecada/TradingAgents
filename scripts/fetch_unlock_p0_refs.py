"""Independent supply reference series for unlock_xs_t1's P0 probe.

Per the registration: CoinMetrics ``SplyCur`` (community tier) where covered,
CoinGecko circulating (market_cap / price from ``market_chart``) otherwise.
CoinGecko's public tier only serves the trailing 365 days (verified
2026-08-08, error 10012), so CoinGecko-referenced names get a recent-window
comparison only — which is where a silent restatement would show ("divergence
growing toward the present"); the truncation is recorded in the stamp.

These series are P0 diagnostics only: they never enter a signal, weight, or
return computation, which is why extending them to the present does not touch
the sealed holdout's return data.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "xsect" / "unlock_p0_refs"
STAMP = ROOT / "data" / "xsect" / "unlock_p0_refs_vintage.json"
MAP_FILE = ROOT / "data" / "xsect" / "unlock_xs_slug_map.json"
EMISSIONS_DIR = ROOT / "data" / "xsect" / "emissions"

CM_URL = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
CM_CATALOG = "https://community-api.coinmetrics.io/v4/catalog-v2/asset-metrics"
CG_URL = "https://api.coingecko.com/api/v3/coins/{gid}/market_chart"


def _base_ticker(sym: str) -> str:
    b = sym[:-4]  # strip USDT
    for pref in ("1000000", "1000"):
        if b.startswith(pref):
            b = b[len(pref):]
    return b.lower()


def cm_community_assets() -> set:
    r = requests.get(CM_CATALOG, params={"metrics": "SplyCur",
                                         "page_size": 2000}, timeout=60)
    r.raise_for_status()
    return {a["asset"] for a in r.json()["data"]
            if any(f.get("community") for m in a["metrics"]
                   for f in m["frequencies"])}


def fetch_cm(asset: str) -> pd.Series:
    rows, url, params = [], CM_URL, {
        "assets": asset, "metrics": "SplyCur", "frequency": "1d",
        "page_size": 10000}
    while url:
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        j = r.json()
        rows += j["data"]
        url, params = j.get("next_page_url"), None
    if not rows:
        return pd.Series(dtype=float)
    df = pd.DataFrame(rows)
    s = pd.Series(pd.to_numeric(df["SplyCur"]).to_numpy(),
                  index=pd.to_datetime(df["time"], utc=True).dt.normalize())
    return s[~s.index.duplicated(keep="last")].sort_index()


def fetch_cg(gid: str, retries: int = 5) -> pd.Series:
    for i in range(retries):
        r = requests.get(CG_URL.format(gid=gid),
                         params={"vs_currency": "usd", "days": "365",
                                 "interval": "daily"}, timeout=60)
        if r.status_code == 200:
            j = r.json()
            px = {t: v for t, v in j.get("prices", [])}
            rows = {pd.Timestamp(t, unit="ms", tz="UTC").normalize(): m / px[t]
                    for t, m in j.get("market_caps", [])
                    if px.get(t) and m}
            return pd.Series(rows).sort_index()
        if r.status_code in (429, 503):
            time.sleep(30 * (i + 1))
            continue
        break
    return pd.Series(dtype=float)


def gecko_id_for(slug: str) -> str | None:
    doc = json.loads((EMISSIONS_DIR / f"{slug}.json").read_text())
    gid = doc.get("gecko_id")
    if gid:
        return gid
    tok = (doc.get("metadata") or {}).get("token") or ""
    if tok.startswith("coingecko:"):
        return tok.split(":", 1)[1]
    return slug


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug_map = json.loads(MAP_FILE.read_text())
    cm_assets = cm_community_assets()
    sources, failed = {}, []
    for i, (slug, sym) in enumerate(sorted(slug_map.items())):
        dest = OUT_DIR / f"{sym}.parquet"
        if dest.exists():
            continue
        ticker = _base_ticker(sym)
        s, src = pd.Series(dtype=float), None
        if ticker in cm_assets:
            try:
                s, src = fetch_cm(ticker), f"coinmetrics:{ticker}"
            except requests.RequestException:
                pass
        if s.empty:
            gid = gecko_id_for(slug)
            s, src = fetch_cg(gid), f"coingecko:{gid}"
            time.sleep(8)   # public-tier rate limit
        if s.empty:
            failed.append({"slug": slug, "symbol": sym, "tried": src})
            continue
        s.rename("ref_supply").to_frame().to_parquet(dest)
        sources[sym] = {"source": src, "first": str(s.index[0].date()),
                        "last": str(s.index[-1].date()), "rows": int(len(s))}
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(slug_map)}")
    STAMP.write_text(json.dumps({
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "coingecko_public_tier_note": ("market_chart limited to trailing 365 "
                                       "days on the public tier (error 10012, "
                                       "verified 2026-08-08); CoinGecko-"
                                       "referenced names therefore get a "
                                       "recent-window P0 comparison only"),
        "n_ok": len(sources), "n_failed": len(failed), "failed": failed,
        "sources": sources}, indent=1))
    print(f"refs: {len(sources)} ok, {len(failed)} failed")


if __name__ == "__main__":
    main()
