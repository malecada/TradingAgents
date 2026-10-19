# tests/research/onchain_b6/test_minutes.py
import json

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b6 import config, minutes

CFG = config.load()


def test_fetch_minute_pages():
    stop = int(pd.Timestamp('2023-01-01 02:00', tz='UTC').timestamp() * 1000)

    def get(url):
        ms = int(url.split('startTime=')[1].split('&')[0])
        rows = [[t, '0', '0', '0', str(100 + (t - ms) / 60000), '0', 0, '0'] for t in range(ms, min(stop, ms + 1000 * 60000), 60000)]
        return json.dumps(rows).encode()
    s = minutes.fetch(get, 'ETHUSDT', '2022-12-31', '2023-01-01 02:00', sleep=lambda x: None)
    assert len(s) == 26 * 60 and s.index[0] == pd.Timestamp('2022-12-31 00:00') and s.index[-1] == pd.Timestamp('2023-01-01 01:59')


def _large():
    t0 = int(pd.Timestamp('2023-06-01 10:00:07', tz='UTC').timestamp())
    return pd.DataFrame({'ts': [t0, t0 + 600, t0 + 1900, t0 + 3700, t0 + 3800], 'token': [1, 1, 0, 2, 0],
                         'amount': [1.2e7, 6e7, 6000.0, 2e7, 100.0], 'direction': [1, 1, -1, 1, 1],
                         'entity': [0, 0, 0, 0, 0], 'cp_new': [False] * 5})


def test_select_events_tiers_and_spacing():
    ev = minutes.select_events(_large(), CFG)
    rows = sorted(zip(ev['minute'].astype(str), ev['direction'], ev['tier']))
    assert rows == [('2023-06-01 10:00:00', 1, 1), ('2023-06-01 10:10:00', 1, 2), ('2023-06-01 10:31:00', -1, 1),
                    ('2023-06-01 11:01:00', 1, 1)]                       # 10:10 tier-1 event suppressed by 30-min spacing


def test_response_alignment_and_placebo_gap():
    idx = pd.date_range('2023-06-01', periods=3 * 24 * 60, freq='min')
    closes = pd.Series(100.0, index=idx)
    e = pd.Timestamp('2023-06-01 10:00')
    closes.loc[e + pd.Timedelta(minutes=1):] = 110.0            # jump in the first minute after the event minute
    r = minutes.responses(pd.DatetimeIndex([e]), closes, {**CFG['minutes'], 'block': 1})
    assert np.isclose(r['ret1']['mean'], np.log(1.1)) and np.isclose(r['pre_ret']['mean'], 0.0)
    noisy = pd.Series(100 * np.exp(np.cumsum(np.random.default_rng(3).normal(0, 1e-4, len(idx)))), index=idx)
    noisy.loc[e + pd.Timedelta(minutes=1):] *= 1.1
    assert minutes.responses(pd.DatetimeIndex([e]), noisy, {**CFG['minutes'], 'block': 1})['vol5']['mean'] > 0
    ev = pd.DataFrame({'minute': [e], 'direction': [1], 'tier': [1], 'token': [1]})
    pl = minutes.placebo(ev, closes, CFG['minutes'])
    assert len(pl) == 1 and pl[0].hour == 10 and abs((pl[0] - e).total_seconds()) >= 3600
