# tradingagents/research/onchain_b8/universe8.py
"""Frozen token universe (spec §1.2): perp symbols with a mainnet ERC-20 contract in the smw
token map and at least `min_rows` hourly bars, one symbol per contract (the longer history
wins). Hourly bars as close / quote volume on a naive UTC index."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


_MULT = re.compile(r'^(1000000|1000)(?=[A-Z])')


def multiplier(symbol):
    """Binance quotes "1000X" and "1000000X" perps per 1,000 / 1,000,000 tokens."""
    m = _MULT.match(symbol)
    return int(m.group(1)) if m else 1


def build(token_map_path, klines_dir, min_rows, exclude=()):
    tm = json.loads(Path(token_map_path).read_text())['map']
    rows = []
    for sym, v in sorted(tm.items()):
        addr = v.get('address')
        p = Path(klines_dir) / f'{sym}.parquet'
        if not addr or not p.exists() or sym in set(exclude):
            continue
        n = pq.read_metadata(p).num_rows
        if n < min_rows:
            continue
        rows.append({'symbol': sym, 'address': addr.lower(), 'decimals': int(v['decimals']), 'rows': int(n), 'how': v.get('how'),
                     'multiplier': multiplier(sym)})
    best = {}
    for r in rows:
        if r['address'] not in best or r['rows'] > best[r['address']]['rows']:
            best[r['address']] = r
    return sorted(best.values(), key=lambda r: r['symbol'])


def load_bars(klines_dir, symbol):
    df = pd.read_parquet(Path(klines_dir) / f'{symbol}.parquet', columns=['close', 'quote_volume'])
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_convert('UTC').tz_localize(None)
    out = pd.DataFrame({'close': df['close'].to_numpy(float), 'qvol': df['quote_volume'].to_numpy(float)}, index=idx).sort_index()
    return out[~out.index.duplicated()]
