# tradingagents/research/onchain_b5/deribit.py
"""Deribit public history (spec §3): every option trade of a UTC day with its implied
volatility and taker side, and hourly DVOL. Raw pages are not kept."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd

COLUMNS = ['timestamp', 'trade_id', 'instrument_name', 'iv', 'price', 'index_price', 'amount', 'direction']
DAY_MS = 86_400_000


class Unavailable(RuntimeError):
    def __init__(self, errors):
        super().__init__(f'unavailable after {len(errors)} attempts: {errors[-1] if errors else ""}')
        self.errors = errors


def _ms(day):
    return int(pd.Timestamp(day, tz='UTC').timestamp() * 1000)


def fetch_day(get, currency, day, cfg, sleep=time.sleep):
    d = cfg['deribit']
    s, end = _ms(day), _ms(day) + DAY_MS - 1
    rows, seen = [], set()
    while True:
        url = (f"{d['trades_url']}?currency={currency}&kind=option&start_timestamp={s}&end_timestamp={end}"
               f"&count={d['count']}&include_old=true&sorting=asc")
        res = json.loads(get(url))['result']
        trades = res['trades']
        new = [t for t in trades if t['trade_id'] not in seen]
        for t in new:
            seen.add(t['trade_id'])
            rows.append({k: t.get(k) for k in COLUMNS})
        if not res.get('has_more') or not trades:
            break
        last = trades[-1]['timestamp']
        s = last if new else last + 1        # same-millisecond trades may straddle pages
        sleep(d['pause'])
    return pd.DataFrame(rows, columns=COLUMNS)


def with_retries(fn, retries, sleep=time.sleep):
    errors = []
    for attempt in range(len(retries) + 1):
        try:
            return fn()
        except Exception as e:          # network or decode failure: retry, then mark unavailable
            errors.append(repr(e))
            if attempt < len(retries):
                sleep(retries[attempt])
    raise Unavailable(errors)


def save_day(df, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name('.' + path.name + '.tmp')
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


def load_day(path):
    return pd.read_parquet(path)


def fetch_dvol(get, currency, start, end, cfg, sleep=time.sleep):
    url0 = cfg['deribit']['dvol_url']
    s, e = _ms(start), _ms(end) + DAY_MS
    vals = {}
    while e > s:
        res = json.loads(get(f'{url0}?currency={currency}&start_timestamp={s}&end_timestamp={e}&resolution=3600'))['result']
        for row in res['data']:
            vals[int(row[0])] = float(row[4])
        cont = res.get('continuation')
        if not res['data'] or cont is None or cont >= e:
            break
        e = cont
        sleep(cfg['deribit']['pause'])
    keys = sorted(k for k in vals if s <= k < _ms(end) + DAY_MS)
    return pd.Series([vals[k] for k in keys], index=pd.to_datetime(keys, unit='ms'), name='dvol')
