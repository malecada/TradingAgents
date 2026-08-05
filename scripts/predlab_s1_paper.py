"""S1 daily paper-trader: computes the live eq_h1 book and journals it.

Forward OOS record for (a) the fill/cost-assumption check and (b) the
predlab_pp2 overlay confirmation. NO orders are placed anywhere — this
writes a journal row only.

Modes:
  --offline   build the book from the local xsect klines store (testing)
  (default)   fetch daily klines from Binance USDT-M public API

Journal: data/predlab/s1_paper/journal.jsonl — one row per UTC date,
idempotent (existing date -> skip). Row: date, universe size, top-200
membership hash, long/short legs (40 names each, weights), vt10 scale
(NaN until 21 book-return days accrue), yesterday's realized book return
computed from the previous row's weights (fill check vs close-to-close).

A SECOND journal (journal_champion.jsonl) tracks the Phase-O final
champion (ewma_20 signal + vt15_naive20 breadth-100 overlay, gates
predlab_opt.final_champion) in parallel. The original journal's config is
intentionally NOT changed: the predlab_pp2 vt10 forward confirmation is
registered on the old book and needs that journal as-is.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import pp  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
JDIR = DATA_ROOT / "predlab" / "s1_paper"
JOURNAL = JDIR / "journal.jsonl"
CH_JOURNAL = JDIR / "journal_champion.jsonl"
FAPI = "https://fapi.binance.com"
LOOKBACK_D = 70  # prior-month median qv + ewma-20 burn-in (tail wt < 0.2%) + slack
VT_TARGET, VT_CAP = 0.10, 2.0
CH_VT_TARGET, CH_BREADTH_FLOOR = 0.15, 100  # Phase-O champion overlay


def _fetch_klines(symbol: str, days: int) -> "pd.DataFrame | None":
    import urllib.request

    url = (f"{FAPI}/fapi/v1/klines?symbol={symbol}&interval=1d&limit={days}")
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            rows = json.load(r)
    except Exception:
        return None
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=[
        "open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "tb_base", "tb_quote", "ignore"])
    df.index = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df[["high", "low", "close", "quote_volume"]].astype(float)


def _perp_symbols() -> "list[str]":
    import urllib.request

    with urllib.request.urlopen(f"{FAPI}/fapi/v1/exchangeInfo", timeout=20) as r:
        info = json.load(r)
    return sorted(s["symbol"] for s in info["symbols"]
                  if s["contractType"] == "PERPETUAL"
                  and s["quoteAsset"] == "USDT" and s["status"] == "TRADING")


def load_panels_online() -> "dict[str, pd.DataFrame]":
    syms = _perp_symbols()
    highs, lows, closes, qvs = {}, {}, {}, {}
    for i, sym in enumerate(syms):
        df = _fetch_klines(sym, LOOKBACK_D)
        if df is None or len(df) < 40:
            continue
        # drop today's incomplete bar
        df = df[df.index < pd.Timestamp.now(tz=timezone.utc).floor("D")]
        highs[sym], lows[sym] = df["high"], df["low"]
        closes[sym], qvs[sym] = df["close"], df["quote_volume"]
        if i % 25 == 0:
            time.sleep(0.5)  # stay far under fapi weight limits
    park = {s: (np.log(highs[s] / lows[s]) ** 2) / (4 * np.log(2)) for s in highs}
    return {"close": pd.DataFrame(closes), "qv": pd.DataFrame(qvs),
            "park": pd.DataFrame(park)}


def load_panels_offline() -> "dict[str, pd.DataFrame]":
    closes, qvs, parks = {}, {}, {}
    for p in sorted((DATA_ROOT / "xsect" / "klines").glob("*.parquet")):
        df = pd.read_parquet(p).tail(LOOKBACK_D)
        closes[p.stem] = df["close"]
        qvs[p.stem] = df["quote_volume"]
        parks[p.stem] = (np.log(df["high"] / df["low"]) ** 2) / (4 * np.log(2))
    return {"close": pd.DataFrame(closes), "qv": pd.DataFrame(qvs),
            "park": pd.DataFrame(parks)}


def todays_book(panels: dict, signal: str = "park_5"
                ) -> "tuple[pd.Timestamp, pd.Series, int]":
    """Book for the last complete UTC day. signal: park_5 (old S1) or
    ewma_20 (Phase-O champion). Returns (asof, weights, breadth) where
    breadth = universe names with a signal value (champion guard input)."""
    qv, park = panels["qv"], panels["park"]
    asof = park.index.max()  # last complete UTC day
    month_start = asof.replace(day=1)
    prior_mask = (qv.index < month_start) & (qv.index >= month_start - timedelta(days=35))
    prior = qv[prior_mask]
    members = prior.median().dropna().nlargest(200).index
    if signal == "park_5":
        sig = park[members].rolling(5).mean().loc[asof]
    elif signal == "ewma_20":
        sig = park[members].ewm(span=20).mean().loc[asof]
    else:
        raise ValueError(signal)
    w = pp.quintile_weights(sig, "eq")
    return asof, w[w != 0], int(sig.notna().sum())


def realized_prev_return(panels: dict, prev_row: dict, asof: pd.Timestamp) -> "float | None":
    """Close-to-close return of the PREVIOUS journal row's book over the day
    ending at `asof` (paper fill check: assumes fills at prior close)."""
    if not prev_row:
        return None
    close = panels["close"]
    w = pd.Series(prev_row["weights"])
    prev_day = pd.Timestamp(prev_row["asof"], tz="UTC")
    if prev_day not in close.index or asof not in close.index or prev_day >= asof:
        return None
    r = np.log(close.loc[asof] / close.loc[prev_day]).reindex(w.index)
    return float((w * r).dropna().sum())


def vt_scale(journal_rows: "list[dict]", target: float = VT_TARGET) -> "float | None":
    rets = [r.get("realized_book_ret") for r in journal_rows]
    rets = [x for x in rets if x is not None]
    if len(rets) < 21:
        return None
    vol = float(np.std(rets[-20:], ddof=1)) * np.sqrt(pp.ANN_DAYS)
    return float(min(target / max(vol, 1e-9), VT_CAP))


def journal_one(journal: Path, panels: dict, signal: str, scale_key: str,
                vt_target: float, breadth_floor: "int | None" = None) -> str:
    rows = ([json.loads(l) for l in journal.read_text().splitlines()]
            if journal.exists() else [])
    asof, w, breadth = todays_book(panels, signal)
    if any(r["asof"] == str(asof.date()) for r in rows):
        return f"{journal.name}: already has {asof.date()} — idempotent skip"
    prev = rows[-1] if rows else None
    realized = realized_prev_return(panels, prev, asof) if prev else None
    est_turn = None
    if prev:
        pw = pd.Series(prev["weights"])
        both = w.index.union(pw.index)
        est_turn = float((w.reindex(both, fill_value=0) - pw.reindex(both, fill_value=0)).abs().sum())
    scale = vt_scale(rows + [{"realized_book_ret": realized}], vt_target)
    if breadth_floor is not None and scale is not None and breadth < breadth_floor:
        scale = 0.0
    row = {
        "asof": str(asof.date()),
        "written_utc": datetime.now(timezone.utc).isoformat(),
        "n_universe": int(panels["park"].shape[1]),
        "membership_hash": hashlib.sha256(
            ",".join(sorted(w.index)).encode()).hexdigest()[:12],
        "weights": {k: round(float(v), 6) for k, v in w.items()},
        "realized_book_ret": realized,
        "est_turnover": est_turn,
        "est_cost": (pp.TAKER_BP / 1e4 * est_turn) if est_turn is not None else None,
        scale_key: scale,
    }
    if breadth_floor is not None:
        row["breadth"] = breadth
    with journal.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    longs = sum(1 for v in w if v > 0)
    return (f"{journal.name} {asof.date()}: book {longs}L/{len(w)-longs}S, "
            f"realized_prev {realized if realized is None else f'{realized:+.4f}'}, "
            f"turn {est_turn}, {scale_key} {scale}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    JDIR.mkdir(parents=True, exist_ok=True)
    panels = load_panels_offline() if args.offline else load_panels_online()
    # original Phase-P book — config frozen for the pp2 vt10 confirmation
    print(journal_one(JOURNAL, panels, "park_5", "vt10_scale", VT_TARGET))
    # Phase-O final champion book — parallel forward journal
    print(journal_one(CH_JOURNAL, panels, "ewma_20", "vt15_b100_scale",
                      CH_VT_TARGET, CH_BREADTH_FLOOR))


if __name__ == "__main__":
    main()
