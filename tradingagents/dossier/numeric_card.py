"""Anonymized numeric block for one (symbol, Friday) from the card panel and daily klines.

Everything is relative: cross-sectional percentiles within that Friday's card universe,
returns, z-scores and buckets. No price levels, no absolute market caps, no dates.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

KLINES = Path("data/xsect/klines")
PCT_FIELDS = ["ret_4w", "ret_12w", "dist_26w_high", "vol_ewma20", "volvol_20", "dvol_30d", "mcap_cm",
              "funding_3d", "funding_30d", "d_adract_30d", "d_txcnt_30d"]
_SIZE_BUCKETS = [(10, "top-10 by size"), (30, "top-30"), (100, "top-100"), (10**9, "below top-100")]


def _pct(series: pd.Series, value) -> float | None:
    if value is None or pd.isna(value):
        return None
    s = series.dropna()
    if s.empty:
        return None
    return float((s < value).mean() + 0.5 * (s == value).mean())


def _bucket(rank) -> str:
    if rank is None or pd.isna(rank):
        return "size rank unavailable"
    for limit, label in _SIZE_BUCKETS:
        if rank <= limit:
            return label
    return "below top-100"


def _age(weeks) -> str:
    if weeks is None or pd.isna(weeks):
        return "listing age unknown"
    years = weeks / 52.18
    if years < 0.5:
        return "listed under 6 months"
    if years < 1:
        return "listed 6-12 months"
    if years < 3:
        return "listed 1-3 years"
    return "listed over 3 years"


def weekly_path(symbol: str, friday: pd.Timestamp, weeks: int = 26, klines_dir: Path = KLINES) -> dict | None:
    """Indexed close path (last = 100), weekly returns, drawdown; only bars with ts <= friday."""
    path = Path(klines_dir) / f"{symbol}.parquet"
    if not path.exists():
        return None
    k = pd.read_parquet(path)
    k.index = pd.to_datetime(k.index, utc=True)
    k = k[k.index <= friday]
    if len(k) < 10:
        return None
    close = k["close"].astype(float)
    wk = close.resample("W-FRI").last().dropna().tail(weeks + 1)
    if len(wk) < 3:
        return None
    rets = wk.pct_change().dropna()
    indexed = (wk / wk.iloc[-1] * 100).round(1)
    daily = close.tail(90)
    dd = float(daily.iloc[-1] / daily.max() - 1)
    rv20 = float(np.log(close).diff().tail(20).std() * np.sqrt(365)) if len(close) > 21 else None
    return {"weeks": len(rets), "indexed_path": indexed.round(1).tolist(),
            "weekly_returns_pct": (rets * 100).round(1).tolist(),
            "drawdown_90d_pct": round(dd * 100, 1),
            "realized_vol_20d_ann_pct": round(rv20 * 100, 1) if rv20 is not None else None}


def numeric_block(cards: pd.DataFrame, symbol: str, friday: pd.Timestamp, path: dict | None) -> dict:
    """Structured, anonymizable numbers for the dossier (keys are stable for the schema)."""
    day = cards[cards["date"] == friday]
    row = day[day["symbol"] == symbol]
    if row.empty:
        raise KeyError(f"{symbol} not in cards on {friday.date()}")
    r = row.iloc[0]
    pct = {f: _pct(day[f], r[f]) for f in PCT_FIELDS}
    block = {
        "universe_size": int(len(day)),
        "size_bucket": _bucket(r.get("size_rank")),
        "volume_rank_pct": pct["dvol_30d"],
        "listing_age": _age(r.get("age_weeks")),
        "category": (str(r["category"]) if pd.notna(r.get("category")) else "unknown"),
        "ret_4w_pct": None if pd.isna(r["ret_4w"]) else round(float(r["ret_4w"]) * 100, 1),
        "ret_12w_pct": None if pd.isna(r["ret_12w"]) else round(float(r["ret_12w"]) * 100, 1),
        "ret_4w_xs_pct": pct["ret_4w"], "ret_12w_xs_pct": pct["ret_12w"],
        "dist_26w_high_pct": None if pd.isna(r["dist_26w_high"]) else round(float(r["dist_26w_high"]) * 100, 1),
        "vol_ewma20_ann_pct": None if pd.isna(r["vol_ewma20"]) else round(float(r["vol_ewma20"]) * 100, 1),
        "vol_xs_pct": pct["vol_ewma20"], "volvol_xs_pct": pct["volvol_20"],
        "funding_3d_ann_pct": None if pd.isna(r["funding_3d"]) else round(float(r["funding_3d"]) * 3 * 365 * 100, 1),
        "funding_30d_ann_pct": None if pd.isna(r["funding_30d"]) else round(float(r["funding_30d"]) * 3 * 365 * 100, 1),
        "funding_xs_pct": pct["funding_3d"],
        "active_addresses_30d_change_pct": None if pd.isna(r["d_adract_30d"]) else round(float(r["d_adract_30d"]) * 100, 1),
        "tx_count_30d_change_pct": None if pd.isna(r["d_txcnt_30d"]) else round(float(r["d_txcnt_30d"]) * 100, 1),
        "onchain_activity_xs_pct": pct["d_adract_30d"],
        "unlock_next30_pct_supply": None if pd.isna(r["unlock_next30_pct"]) else round(float(r["unlock_next30_pct"]) * 100, 2),
        "unlock_prev30_pct_supply": None if pd.isna(r["unlock_prev30_pct"]) else round(float(r["unlock_prev30_pct"]) * 100, 2),
        "price_path": path,
    }
    return block


def render_numeric(block: dict) -> str:
    """Compact text rendering for the prompt; percentiles as 'pct N' within the universe."""
    def p(v):
        return "n/a" if v is None else f"{v}"
    def xs(v):
        return "n/a" if v is None else f"pct {round(v * 100)}"
    lines = [
        f"Universe: {block['universe_size']} assets this week; {block['size_bucket']}; volume rank {xs(block['volume_rank_pct'])}; {block['listing_age']}; category: {block['category']}.",
        f"Returns: 4w {p(block['ret_4w_pct'])}% ({xs(block['ret_4w_xs_pct'])}), 12w {p(block['ret_12w_pct'])}% ({xs(block['ret_12w_xs_pct'])}); distance to 26w high {p(block['dist_26w_high_pct'])}%.",
        f"Volatility: EWMA20 {p(block['vol_ewma20_ann_pct'])}% ann ({xs(block['vol_xs_pct'])}); vol-of-vol {xs(block['volvol_xs_pct'])}.",
        f"Funding (annualized): 3d {p(block['funding_3d_ann_pct'])}%, 30d {p(block['funding_30d_ann_pct'])}% ({xs(block['funding_xs_pct'])}).",
        f"On-chain 30d change: active addresses {p(block['active_addresses_30d_change_pct'])}%, transactions {p(block['tx_count_30d_change_pct'])}% ({xs(block['onchain_activity_xs_pct'])}).",
        f"Supply schedule: unlock next 30d {p(block['unlock_next30_pct_supply'])}% of supply; previous 30d {p(block['unlock_prev30_pct_supply'])}%.",
    ]
    path = block.get("price_path")
    if path:
        lines.append(f"Price path, weekly, indexed to 100 at decision: {path['indexed_path']}")
        lines.append(f"Weekly returns % (oldest first): {path['weekly_returns_pct']}; 90d drawdown {path['drawdown_90d_pct']}%; realized vol 20d {p(path['realized_vol_20d_ann_pct'])}% ann.")
    return "\n".join(f"[n{i}] {line}" for i, line in enumerate(lines, 1))
