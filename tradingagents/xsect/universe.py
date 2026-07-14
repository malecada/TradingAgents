"""PIT universe: eligibility from raw kline availability (incl. delisted symbols)."""
from pathlib import Path

import pandas as pd


def load_klines(kline_dir: Path) -> dict[str, pd.DataFrame]:
    return {p.stem: pd.read_parquet(p) for p in sorted(Path(kline_dir).glob("*.parquet"))}


def eligibility(klines: dict, date: pd.Timestamp, min_age_days: int = 30,
                min_mvol: float = 5e6, top_n: int = 100) -> list[str]:
    scored = []
    for sym, df in klines.items():
        if date not in df.index:
            continue
        if df.index[0] > date - pd.Timedelta(days=min_age_days):
            continue
        window = df.loc[:date].tail(30)["quote_volume"]
        mvol = float(window.median())
        if mvol >= min_mvol:
            scored.append((sym, mvol))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return [s for s, _ in scored[:top_n]]


def weekly_rebalance_dates(start: str, end: str) -> pd.DatetimeIndex:
    days = pd.date_range(start, end, freq="D", tz="UTC")
    return days[days.dayofweek == 0]
