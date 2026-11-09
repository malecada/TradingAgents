"""Anonymized numeric block for one (symbol, Friday) from the card panel and daily klines.

Everything is relative: cross-sectional percentiles within that Friday's card universe,
returns, z-scores and buckets. No price levels, no absolute market caps, no dates.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

KLINES = Path("data/xsect/klines")
PCT_FIELDS = ["ret_4w", "ret_12w", "dist_26w_high", "vol_ewma20", "volvol_20", "dvol_30d", "mcap_cm",
              "funding_3d", "funding_30d", "d_adract_30d", "d_txcnt_30d"]
# size_rank in the card panel is a cross-sectional PERCENTILE (0-1, higher = larger market cap)
_SIZE_BUCKETS = [(0.9, "top decile by market cap"), (0.5, "upper half by market cap"), (0.0, "lower half by market cap")]


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
    for floor, label in _SIZE_BUCKETS:
        if rank >= floor:
            return label
    return "lower half by market cap"


def _pct_from_log(x):
    """Card returns are log returns; render as simple percentage changes."""
    return None if x is None or pd.isna(x) else round(float(np.expm1(x)) * 100, 1)


def _ann_funding(x):
    """Card funding fields are mean DAILY funding (sum of the 8-hour rates); annualize x365."""
    return None if x is None or pd.isna(x) else round(float(x) * 365 * 100, 1)


def _age(weeks) -> str:
    if weeks is None or pd.isna(weeks):
        return "listing age unknown"
    years = weeks / 52.18
    if years < 1:
        return "listed under a year"
    return "listed over a year"


_LABEL_SKIP = ("ecosystem", "portfolio", "index", "alleged", "made in", "launchpool", "launchpad", "binance", "coinbase", "okx")
_FAMILIES = [("meme", "meme"), ("smart contract", "network or infrastructure"), ("artificial intelligence", "AI"),
             ("decentralized finance", "DeFi"), ("defi", "DeFi"), ("gambl", "gaming or NFT"), ("fan token", "gaming or NFT"),
             ("sports", "gaming or NFT"), ("socialfi", "social"), ("social", "social"), ("e-commerce", "payments"),
             ("inscription", "meme"), ("brc-20", "meme"), ("depin", "infrastructure services"),
             ("internet of things", "infrastructure services"), ("infrastructure", "network or infrastructure"),
             ("ai agent", "AI"), ("oracle", "infrastructure services"), ("storage", "infrastructure services"),
             ("real world asset", "real-world assets"), ("liquid staking", "DeFi"), ("perpetual", "DeFi"), ("gaming", "gaming or NFT"), ("nft", "gaming or NFT"), ("metaverse", "gaming or NFT"),
             ("chain", "network or infrastructure"), ("bridge", "network or infrastructure"), ("rollup", "network or infrastructure"),
             ("layer", "network or infrastructure"), ("dex", "DeFi"), ("lending", "DeFi"), ("yield", "DeFi"), ("cdp", "DeFi"),
             ("derivative", "DeFi"), ("staking", "DeFi"), ("stablecoin", "DeFi"), ("launchpad", "DeFi"), ("farm", "DeFi"),
             ("oracle", "infrastructure services"), ("storage", "infrastructure services"), ("ai", "infrastructure services"),
             ("data", "infrastructure services"), ("privacy", "infrastructure services"), ("exchange", "exchange token"),
             ("cex", "exchange token"), ("payment", "payments"), ("wallet", "payments")]


CATEGORIES_PATH = Path("data/dossier/categories.json")
_CATEGORIES: dict | None = None


def _fallback_categories(symbol: str) -> list[str]:
    """CoinGecko category labels fetched by scripts/dossier_categories_fetch.py (stable attribute, not dated)."""
    global _CATEGORIES
    if _CATEGORIES is None:
        _CATEGORIES = json.loads(CATEGORIES_PATH.read_text()) if CATEGORIES_PATH.exists() else {}
    return _CATEGORIES.get(symbol, {}).get("categories", [])


def category_family(category, symbol: str | None = None) -> str:
    """Coarse family instead of the raw category label, which can single out an asset. Falls back to the
    CoinGecko labels when the card panel has no category for the symbol."""
    labels = []
    if not (category is None or (isinstance(category, float) and pd.isna(category))):
        labels.append(str(category))
    if symbol is not None:
        labels.extend(_fallback_categories(symbol))
    if not labels:
        return "unknown"
    labels = [l.lower() for l in labels if not any(k in l.lower() for k in _LABEL_SKIP)] or ["other"]
    for key, fam in _FAMILIES:                       # family priority (meme before network) over label order
        if any(key in c for c in labels):
            return fam
    return "other"


def weekly_path(symbol: str, friday: pd.Timestamp, weeks: int = 12, klines_dir: Path = KLINES) -> dict | None:
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
    indexed = (wk / wk.iloc[-1] * 100).round(0)
    daily = close.tail(90)
    dd = float(daily.iloc[-1] / daily.max() - 1)
    rv20 = float(np.log(close).diff().tail(20).std() * np.sqrt(365)) if len(close) > 21 else None
    return {"weeks": len(rets), "indexed_path": indexed.round(1).tolist(),
            "weekly_returns_pct": (rets * 100).round(1).tolist(),
            "drawdown_90d_pct": round(dd * 100, 1),
            "realized_vol_20d_ann_pct": round(rv20 * 100, 1) if rv20 is not None else None}


def numeric_block(cards: pd.DataFrame, symbol: str, friday: pd.Timestamp, path: dict | None,
                  universe_symbols=None) -> dict:
    """Structured, anonymizable numbers for the dossier (keys are stable for the schema).
    Percentiles are taken within ``universe_symbols`` (the week's decision universe) when given, so the
    reference class matches the forecast target (outperformance of the universe median)."""
    day = cards[cards["date"] == friday]
    if universe_symbols is not None:
        day = day[day["symbol"].isin(set(universe_symbols) | {symbol})]
    row = day[day["symbol"] == symbol]
    if row.empty:
        raise KeyError(f"{symbol} not in cards on {friday.date()}")
    r = row.iloc[0]
    pct = {f: _pct(day[f], r[f]) for f in PCT_FIELDS}
    block = {
        "size_bucket": _bucket(r.get("size_rank")),
        "volume_rank_pct": pct["dvol_30d"],
        "listing_age": _age(r.get("age_weeks")),
        "category": category_family(r.get("category"), symbol),
        "ret_4w_pct": _pct_from_log(r["ret_4w"]),
        "ret_12w_pct": _pct_from_log(r["ret_12w"]),
        "ret_4w_xs_pct": pct["ret_4w"], "ret_12w_xs_pct": pct["ret_12w"],
        "dist_26w_high_pct": _pct_from_log(r["dist_26w_high"]),
        "vol_ewma20_ann_pct": None if pd.isna(r["vol_ewma20"]) else round(float(r["vol_ewma20"]) * 100, 1),
        "vol_xs_pct": pct["vol_ewma20"], "volvol_xs_pct": pct["volvol_20"],
        "funding_3d_ann_pct": _ann_funding(r["funding_3d"]),
        "funding_30d_ann_pct": _ann_funding(r["funding_30d"]),
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
        f"Profile: {block['size_bucket']}; volume rank {xs(block['volume_rank_pct'])} within this week's universe; {block['listing_age']}; category: {block['category']}.",
        f"Returns: 4w {p(block['ret_4w_pct'])}% ({xs(block['ret_4w_xs_pct'])}), 12w {p(block['ret_12w_pct'])}% ({xs(block['ret_12w_xs_pct'])}); distance to 26w high {p(block['dist_26w_high_pct'])}%.",
        f"Volatility: EWMA20 {p(block['vol_ewma20_ann_pct'])}% ann ({xs(block['vol_xs_pct'])}); vol-of-vol {xs(block['volvol_xs_pct'])}.",
        f"Funding (annualized): 3d {p(block['funding_3d_ann_pct'])}%, 30d {p(block['funding_30d_ann_pct'])}% ({xs(block['funding_xs_pct'])}).",
        f"On-chain 30d change: active addresses {p(block['active_addresses_30d_change_pct'])}%, transactions {p(block['tx_count_30d_change_pct'])}% ({xs(block['onchain_activity_xs_pct'])}).",
        ("Supply schedule: unlock data unavailable for this asset." if block['unlock_next30_pct_supply'] is None and block['unlock_prev30_pct_supply'] is None
         else f"Supply schedule: unlock next 30d {p(block['unlock_next30_pct_supply'])}% of supply; previous 30d {p(block['unlock_prev30_pct_supply'])}%."),
    ]
    path = block.get("price_path")
    if path:
        lines.append(f"Price path, weekly, indexed to 100 at decision: {path['indexed_path']}")
        lines.append(f"Weekly returns % (oldest first): {path['weekly_returns_pct']}; 90d drawdown {path['drawdown_90d_pct']}%; realized vol 20d {p(path['realized_vol_20d_ann_pct'])}% ann.")
    return "\n".join(f"[n{i}] {line}" for i, line in enumerate(lines, 1))
