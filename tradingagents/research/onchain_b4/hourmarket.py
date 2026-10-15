# tradingagents/research/onchain_b4/hourmarket.py
"""Binance ETHUSDT 1-hour bars (spec §4.5): close and quote volume per bar-open hour (UTC).
Hours after the development cutoff are written only to the sealed directory."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

URL = 'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&startTime={ms}&limit=1000'
HOUR_MS = 3_600_000


def _ms(ts):
    return int(pd.Timestamp(ts, tz='UTC').timestamp() * 1000)


def _iso(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime('%Y-%m-%dT%H')


def fetch(get, symbol, start, end):
    ms, stop = _ms(start), _ms(end)
    bars, pages = {}, []
    while ms < stop:
        raw = get(URL.format(symbol=symbol, ms=ms))
        pages.append(raw)
        rows = json.loads(raw)
        for k in rows:
            if k[0] < stop:
                bars[_iso(k[0])] = (float(k[4]), float(k[7]))
        if len(rows) < 1000:
            break
        ms = rows[-1][0] + HOUR_MS
    return bars, pages


def store(bars, pages, out_dir, cutoff_hour):
    out_dir = Path(out_dir)
    (out_dir / 'market').mkdir(parents=True, exist_ok=True)
    (out_dir / 'sealed' / 'raw').mkdir(parents=True, exist_ok=True)
    dev = {h: v for h, v in sorted(bars.items()) if h <= cutoff_hour}
    sealed = {h: v for h, v in sorted(bars.items()) if h > cutoff_hour}
    (out_dir / 'market' / 'hourly_dev.json').write_text(json.dumps(dev))
    (out_dir / 'sealed' / 'hourly_sealed.json').write_text(json.dumps(sealed))
    for raw in pages:              # raw pages span both windows, so they stay sealed
        (out_dir / 'sealed' / 'raw' / f'binance-{hashlib.sha256(raw).hexdigest()}.json').write_bytes(raw)
    meta = {'cutoff_hour': cutoff_hour, 'dev_hours': len(dev), 'sealed_hours': len(sealed), 'pages': len(pages)}
    (out_dir / 'market' / 'hourly_meta.json').write_text(json.dumps(meta, indent=1))
    return meta


def _frame(doc):
    idx = pd.to_datetime(list(doc), format='%Y-%m-%dT%H')
    vals = list(doc.values())
    return pd.DataFrame({'close': [float(v[0]) for v in vals], 'qvol': [float(v[1]) for v in vals]},
                        index=idx).sort_index()


def load_dev(path, cutoff_hour):
    df = _frame(json.loads(Path(path).read_text()))
    if len(df) and df.index.max() > pd.to_datetime(cutoff_hour, format='%Y-%m-%dT%H'):
        raise ValueError('development hourly file contains sealed hours')
    return df


def load_all(dev_path, sealed_path):
    return pd.concat([_frame(json.loads(Path(dev_path).read_text())),
                      _frame(json.loads(Path(sealed_path).read_text()))]).sort_index()
