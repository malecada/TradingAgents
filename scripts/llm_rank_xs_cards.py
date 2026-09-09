"""llm_c3_rank_xs — weekly card panel builder (frozen fields, charter §2).

Builds data/llm_rank_xs/cards.parquet: one row per (friday, symbol) for
the top-200 30d-median-dollar-volume universe (monthly PIT refresh),
2021-01 -> 2025-03 dev window plus the sealed holdout tail (holdout rows
are built but never read by dev code; the harness clips at dev end).

All features use data through the card date (inclusive); forward returns
are attached separately at evaluation time from t+1 opens.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.xsect import unlock_xs  # noqa: E402

XS = Path("data/xsect")
OUT = Path("data/llm_rank_xs")
FULL = ("2021-01-01", "2026-07-01")
TOP_N = 200


def load_panels():
    closes, dvols, opens = {}, {}, {}
    for f in sorted((XS / "klines").glob("*USDT.parquet")):
        df = pd.read_parquet(f)
        sym = f.stem
        closes[sym] = df["close"]
        opens[sym] = df["open"]
        dvols[sym] = df["quote_volume"]
    return (pd.DataFrame(closes).sort_index(), pd.DataFrame(opens).sort_index(),
            pd.DataFrame(dvols).sort_index())


def load_funding(index):
    cols = {}
    for f in sorted((XS / "funding").glob("*USDT.parquet")):
        df = pd.read_parquet(f)
        rate_col = next((c for c in df.columns if "rate" in c.lower()), df.columns[0])
        s = df[rate_col]
        if not isinstance(s.index, pd.DatetimeIndex):
            s.index = pd.to_datetime(df.index, utc=True)
        cols[f.stem] = s.resample("1D").sum()
    return pd.DataFrame(cols).reindex(index)


def load_fundamentals(index):
    """CM community: mcap + activity, per mapped symbol."""
    uni = json.loads((XS / "fundamentals_universe.json").read_text())
    mapping = uni.get("mapping", {})
    mcap, adr, tx = {}, {}, {}
    for base, meta in mapping.items():
        f = XS / "fundamentals" / f"{base}.parquet"
        sym = meta if isinstance(meta, str) else meta.get("perp") or meta.get("symbol")
        if not f.exists() or not sym:
            continue
        df = pd.read_parquet(f)
        if "CapMrktCurUSD" in df:
            mcap[sym] = df["CapMrktCurUSD"]
        if "AdrActCnt" in df:
            adr[sym] = df["AdrActCnt"]
        if "TxCnt" in df:
            tx[sym] = df["TxCnt"]
    return (pd.DataFrame(mcap).reindex(index), pd.DataFrame(adr).reindex(index),
            pd.DataFrame(tx).reindex(index))


def load_categories():
    cats = {}
    slug_map = json.loads((XS / "unlock_xs_slug_map.json").read_text())
    for slug, sym in slug_map.items():
        f = XS / "emissions" / f"{slug}.json"
        if f.exists():
            doc = json.loads(f.read_text())
            c = doc.get("protocolCategory")
            if not c:
                cl = doc.get("categories")
                c = (list(cl.values())[0] if isinstance(cl, dict) else cl[0]) if cl else None
            if isinstance(c, (list, tuple)):
                c = c[0] if c else None
            cats[sym] = str(c) if c is not None else None
    return cats


def main() -> int:
    OUT.mkdir(exist_ok=True)
    out_path = OUT / "cards.parquet"
    if out_path.exists():
        print(f"{out_path} exists — refusing to overwrite (stop rule)")
        return 1

    close, opens, dvol = load_panels()
    idx = close.index
    logret = np.log(close).diff()
    fund = load_funding(idx)
    mcap, adr, tx = load_fundamentals(idx)
    cats = load_categories()

    slug_map = json.loads((XS / "unlock_xs_slug_map.json").read_text())
    days = idx[(idx >= pd.Timestamp(FULL[0], tz="UTC")) &
               (idx <= pd.Timestamp(FULL[1], tz="UTC"))]
    unl = unlock_xs.build_matrices(XS / "emissions", slug_map, days,
                                   lookaheads=(30,))
    burden30 = unl["burden"][30]
    daily_unlocked = unl["supply"].diff()
    prev30 = (daily_unlocked.rolling(30, min_periods=1).sum()
              / unl["supply"].where(unl["supply"] > 0))

    med_dvol = dvol.rolling(30, min_periods=15).median()
    vol20 = logret.ewm(span=20, min_periods=10).std() * np.sqrt(365)
    volvol = logret.rolling(20).std().rolling(20).std() * np.sqrt(365)
    ret4w = np.log(close / close.shift(28))
    ret12w = np.log(close / close.shift(84))
    high26 = close.rolling(182, min_periods=60).max()
    dist_high = np.log(close / high26)
    f3 = fund.rolling(3, min_periods=1).mean()
    f30 = fund.rolling(30, min_periods=5).mean()
    d_adr = adr.rolling(7, min_periods=3).mean().pct_change(30)
    d_tx = tx.rolling(7, min_periods=3).mean().pct_change(30)
    age_weeks = (~close.isna()).cumsum() / 7.0

    fridays = pd.date_range(FULL[0], FULL[1], freq="W-FRI", tz="UTC")
    fridays = fridays[fridays.isin(idx)]

    rows = []
    month_uni = {}
    for d in fridays:
        mkey = (d.year, d.month)
        if mkey not in month_uni:
            # universe from PREVIOUS month-end data (monthly PIT)
            ref = d - pd.offsets.MonthBegin(1)
            ref_idx = idx[idx < ref]
            if not len(ref_idx):
                continue
            r = med_dvol.loc[ref_idx[-1]].dropna()
            month_uni[mkey] = set(r.nlargest(TOP_N).index)
        syms = month_uni[mkey]
        for s in syms:
            if pd.isna(close.at[d, s]):
                continue
            rows.append({
                "date": d, "symbol": s,
                "ret_4w": ret4w.at[d, s], "ret_12w": ret12w.at[d, s],
                "dist_26w_high": dist_high.at[d, s],
                "vol_ewma20": vol20.at[d, s], "volvol_20": volvol.at[d, s],
                "dvol_30d": med_dvol.at[d, s],
                "mcap_cm": mcap.at[d, s] if s in mcap.columns else np.nan,
                "funding_3d": f3.at[d, s] if s in f3.columns else np.nan,
                "funding_30d": f30.at[d, s] if s in f30.columns else np.nan,
                "d_adract_30d": d_adr.at[d, s] if s in d_adr.columns else np.nan,
                "d_txcnt_30d": d_tx.at[d, s] if s in d_tx.columns else np.nan,
                "unlock_next30_pct": burden30.at[d, s] if s in burden30.columns else np.nan,
                "unlock_prev30_pct": prev30.at[d, s] if s in prev30.columns else np.nan,
                "age_weeks": age_weeks.at[d, s],
                "category": cats.get(s),
            })
    cards = pd.DataFrame(rows)
    # ranks used for anonymized size/liquidity context + later neutralization
    cards["dvol_rank"] = cards.groupby("date")["dvol_30d"].rank(pct=True)
    cards["size_rank"] = cards.groupby("date")["mcap_cm"].rank(pct=True)
    cards.to_parquet(out_path, index=False)
    ndates = cards["date"].nunique()
    print(f"cards: {len(cards)} rows, {ndates} fridays, "
          f"{cards['symbol'].nunique()} distinct symbols")
    for c in cards.columns:
        print(f"  {c}: {cards[c].notna().mean():.0%} coverage")
    return 0


if __name__ == "__main__":
    sys.exit(main())
