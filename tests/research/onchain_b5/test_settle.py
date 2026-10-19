import json

import pandas as pd

from tradingagents.research.onchain_b5 import settle


def _get(n):
    def get(url):
        ms = int(url.split('startTime=')[1].split('&')[0])
        return json.dumps([[ms + 60000 * i, '0', '0', '0', str(100 + i), '0', 0, '0'] for i in range(n)]).encode()
    return get


def test_twap_from_minute_klines():
    seen = []
    out = settle.fetch(lambda u: (seen.append(u), _get(30)(u))[1], 'ETHUSDT', ['2023-06-01'], sleep=lambda s: None)
    assert out == {'2023-06-01': 114.5}
    start = int(pd.Timestamp('2023-06-01 07:30', tz='UTC').timestamp() * 1000)
    assert f'startTime={start}' in seen[0] and 'interval=1m' in seen[0]


def test_incomplete_minutes_give_none():
    assert settle.fetch(_get(29), 'ETHUSDT', ['2023-06-01'], sleep=lambda s: None) == {'2023-06-01': None}
