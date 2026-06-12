"""P4: blend the funding-carry sleeve with the V5 MIX core book.

Builds a BTC/ETH real-basis carry sleeve, correlates it against the V5 MIX
portfolio returns, sweeps the carry allocation, and stress-tests the blend at
haircut carry Sharpe levels (since the real-basis SR is an upper bound that
omits intraday liquidation + margin capital cost — see
docs/CARRY_SLEEVE_BACKTEST_SPEC.md, P5/open-question).

Usage:
    python scripts/carry_blend_p4.py \
        --v5-csv data/v5_mix_kelly_025/daily_returns.csv \
        --start 2021-11-07 --end 2026-04-15
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd
import requests

from tradingagents.strategies.carry_sleeve import (
    blend_returns,
    carry_sleeve_return,
    compute_price_pnl,
    fetch_perp_mark,
    funding_daily_income,
)

_SPOT_BASE = "https://api.binance.com/api/v3/klines"


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def fetch_spot_close(symbol: str, start: date, end: date) -> pd.Series:
    """Daily spot close from Binance spot klines (paginated), date-indexed."""
    s = int(datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc).timestamp() * 1000)
    e = int(datetime.combine(end, datetime.min.time()).replace(tzinfo=timezone.utc).timestamp() * 1000)
    rows: list[list] = []
    cur = s
    while cur < e:
        d = requests.get(_SPOT_BASE, params={"symbol": symbol, "interval": "1d",
                                             "startTime": cur, "endTime": e, "limit": 1000},
                         timeout=30).json()
        if not d:
            break
        rows += d
        nxt = d[-1][0] + 1
        if nxt <= cur:
            break
        cur = nxt
    idx = pd.to_datetime([r[0] for r in rows], unit="ms", utc=True).date
    return pd.Series([float(r[4]) for r in rows], index=idx, name="spot")


def sharpe(r) -> float:
    r = np.asarray(r, dtype=float)
    return float(r.mean() / r.std() * np.sqrt(365))


def maxdd(r) -> float:
    eq = (1 + np.asarray(r, dtype=float)).cumprod()
    return float((eq / np.maximum.accumulate(eq) - 1).min())


def build_sleeve(symbols: list[str], start: date, end: date) -> pd.Series:
    """Equal-weight real-basis carry sleeve over the given perp symbols."""
    legs = {}
    for sym in symbols:
        inc = funding_daily_income(sym, start, end)
        perp = fetch_perp_mark(sym, start, end)
        spot = fetch_spot_close(sym, start, end)
        idx = inc.index.intersection(perp.index).intersection(spot.index)
        legs[sym] = carry_sleeve_return(inc.loc[idx], price_pnl=compute_price_pnl(spot.loc[idx], perp.loc[idx]))
    common = legs[symbols[0]].index
    for sym in symbols[1:]:
        common = common.intersection(legs[sym].index)
    w = 1.0 / len(symbols)
    sleeve = sum(w * legs[sym].loc[common] for sym in symbols)
    sleeve.index = pd.to_datetime(list(common))
    sleeve.name = "carry_sleeve"
    return sleeve


def haircut_to_sharpe(sleeve: pd.Series, target_sr: float) -> pd.Series:
    """Shift the sleeve mean to hit a target annualized Sharpe at unchanged vol.

    Models liquidation/capital drag eating return without assuming where it bites.
    """
    r = sleeve.to_numpy(dtype=float)
    mu_t = (target_sr / np.sqrt(365)) * r.std()
    return pd.Series(r - r.mean() + mu_t, index=sleeve.index, name="carry_sleeve")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v5-csv", default="data/v5_mix_kelly_025/daily_returns.csv")
    ap.add_argument("--v5-col", default="portfolio")
    ap.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    ap.add_argument("--start", type=_parse_date, default=_parse_date("2021-11-07"))
    ap.add_argument("--end", type=_parse_date, default=_parse_date("2026-04-15"))
    ap.add_argument("--allocs", nargs="+", type=float, default=[0.05, 0.10, 0.15, 0.20, 0.30])
    args = ap.parse_args()

    sleeve = build_sleeve(args.symbols, args.start, args.end)
    v5 = pd.read_csv(args.v5_csv, index_col=0, parse_dates=True)[args.v5_col]
    j = sleeve.index.intersection(v5.index)
    s, v = sleeve.loc[j].to_numpy(), v5.loc[j].to_numpy()
    base = sharpe(v)

    print(f"\nP4 carry blend  sleeve={'+'.join(args.symbols)}  overlap={len(j)}d "
          f"{j.min().date()}..{j.max().date()}")
    print(f"  V5 core ({args.v5_csv})  SR={base:.2f}  maxDD={maxdd(v)*100:.1f}%")
    print(f"  carry sleeve (real-basis, UPPER BOUND)  SR={sharpe(s):.2f}  maxDD={maxdd(s)*100:.1f}%")
    print(f"  CORRELATION(sleeve, V5) = {np.corrcoef(s, v)[0, 1]:+.3f}\n")

    print("  Allocation sweep at real-basis (upper-bound) carry SR:")
    print(f"    {'alloc':>6} | {'blend SR':>8} | {'Δ':>6} | {'maxDD':>7}")
    for X in args.allocs:
        b = blend_returns(v5.loc[j], sleeve.loc[j], X).to_numpy()
        print(f"    {X*100:>5.0f}% | {sharpe(b):>8.2f} | {sharpe(b)-base:>+6.2f} | {maxdd(b)*100:>6.1f}%")

    print("\n  Haircut stress — blend SR if true carry SR were lower (liquidation/capital drag):")
    print(f"    {'carry SR':>9} | " + " | ".join(f"@{int(X*100)}%" for X in args.allocs))
    for tgt in [sharpe(s), 5.0, 2.5, 1.0, 0.0]:
        sh = haircut_to_sharpe(sleeve, tgt)
        cells = []
        for X in args.allocs:
            b = blend_returns(v5.loc[j], sh.loc[j], X).to_numpy()
            cells.append(f"{sharpe(b):.2f}")
        print(f"    {tgt:>9.2f} | " + " | ".join(f"{c:>4}" for c in cells))


if __name__ == "__main__":
    main()
