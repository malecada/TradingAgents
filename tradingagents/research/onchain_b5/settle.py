"""Settlement price at a Deribit daily expiry (pre-run amendment 4): the mean of the thirty Binance
1-minute closes from 07:30 to 08:00 UTC, mirroring Deribit's 30-minute delivery TWAP."""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

URL = 'https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&startTime={ms}&limit=30'
MINUTE = 60_000


def fetch(get, symbol, dates, sleep=time.sleep, pause=0.05):
    out = {}
    for d in dates:
        ms = int((pd.Timestamp(d, tz='UTC') + pd.Timedelta(hours=7, minutes=30)).timestamp() * 1000)
        rows = [r for r in json.loads(get(URL.format(symbol=symbol, ms=ms))) if ms <= r[0] < ms + 30 * MINUTE]
        out[d] = float(np.mean([float(r[4]) for r in rows])) if len(rows) == 30 else None
        sleep(pause)
    return out
