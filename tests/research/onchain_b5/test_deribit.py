# tests/research/onchain_b5/test_deribit.py
import json

import pandas as pd
import pytest

from tradingagents.research.onchain_b5 import config, deribit

T0 = int(pd.Timestamp('2023-06-01', tz='UTC').timestamp() * 1000)


def _trade(i, ts):
    return {'timestamp': ts, 'trade_id': f'E-{i}', 'instrument_name': 'ETH-2JUN23-1900-C', 'iv': 50.0 + i,
            'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy' if i % 2 else 'sell', 'extra': 1}


def test_fetch_day_paginates_and_dedupes():
    trades = [_trade(i, T0 + 1000 * (i // 2)) for i in range(7)]   # pairs share a timestamp
    calls = []

    def get(url):
        calls.append(url)
        s = int(url.split('start_timestamp=')[1].split('&')[0])
        rest = [t for t in trades if t['timestamp'] >= s]
        page = rest[:3]
        return json.dumps({'result': {'trades': page, 'has_more': len(rest) > 3}}).encode()

    df = deribit.fetch_day(get, 'ETH', '2023-06-01', config.load(), sleep=lambda s: None)
    assert list(df.columns) == deribit.COLUMNS and sorted(df['trade_id']) == [f'E-{i}' for i in range(7)]
    assert 'kind=option' in calls[0] and 'sorting=asc' in calls[0]


def test_retries_then_unavailable():
    slept = []

    def boom():
        raise OSError('net')
    with pytest.raises(deribit.Unavailable):
        deribit.with_retries(boom, [1, 2], sleep=slept.append)
    assert slept == [1, 2]


def test_save_load_round_trip(tmp_path):
    df = pd.DataFrame([{k: _trade(1, T0)[k] for k in deribit.COLUMNS}])
    deribit.save_day(df, tmp_path / 'ETH' / '2023-06-01.parquet')
    pd.testing.assert_frame_equal(deribit.load_day(tmp_path / 'ETH' / '2023-06-01.parquet'), df)
    deribit.save_day(df.iloc[:0], tmp_path / 'ETH' / 'empty.parquet')
    assert len(deribit.load_day(tmp_path / 'ETH' / 'empty.parquet')) == 0


def test_fetch_dvol_follows_continuation():
    hours = [T0 + 3_600_000 * h for h in range(10)]

    def get(url):
        e = int(url.split('end_timestamp=')[1].split('&')[0])
        rows = [[h, 1, 1, 1, 50.0 + i] for i, h in enumerate(hours) if h <= e][-4:]
        cont = rows[0][0] - 3_600_000 if rows and rows[0][0] > hours[0] else None
        return json.dumps({'result': {'data': rows, 'continuation': cont}}).encode()

    s = deribit.fetch_dvol(get, 'ETH', '2023-06-01', '2023-06-01', config.load(), sleep=lambda x: None)
    assert len(s) == 10 and s.index[0] == pd.Timestamp('2023-06-01 00:00') and s.iloc[-1] == 59.0
