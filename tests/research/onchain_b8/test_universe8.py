# tests/research/onchain_b8/test_universe8.py
import json

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b8 import universe8 as U


def _klines(path, symbol, n, tz=True):
    idx = pd.date_range('2021-01-01', periods=n, freq='h', tz='UTC' if tz else None)
    df = pd.DataFrame({'open': 1.0, 'high': 1.0, 'low': 1.0, 'close': np.linspace(1, 2, n), 'volume': 1.0,
                       'quote_volume': 5.0, 'taker_buy_quote_volume': 2.0}, index=pd.Index(idx, name='ts'))
    df.to_parquet(path / f'{symbol}.parquet')


def test_build_filters_dedupes_and_sorts(tmp_path):
    k = tmp_path / 'k'
    k.mkdir()
    for sym, n in (('AAAUSDT', 20000), ('BBBUSDT', 100), ('1000CCCUSDT', 30000), ('CCCUSDT', 25000), ('EEEUSDT', 20000)):
        _klines(k, sym, n)
    tm = {'map': {'AAAUSDT': {'address': '0xAAAA', 'decimals': 18, 'how': 'binance_spot'},
                  'BBBUSDT': {'address': '0xbbbb', 'decimals': 6, 'how': 'binance_spot'},
                  '1000CCCUSDT': {'address': '0xcccc', 'decimals': 9, 'how': 'binance_spot'},
                  'CCCUSDT': {'address': '0xcccc', 'decimals': 9, 'how': 'fallback_single_ranked'},
                  'DDDUSDT': {'address': '0xdddd', 'decimals': 18, 'how': 'binance_spot'},
                  'EEEUSDT': {'how': 'fallback_no_candidate'}}}
    (tmp_path / 'map.json').write_text(json.dumps(tm))
    u = U.build(tmp_path / 'map.json', k, 17520)
    assert [r['symbol'] for r in u] == ['1000CCCUSDT', 'AAAUSDT']               # BBB too short, DDD no bars, EEE no address, CCC duplicate contract
    assert u[1]['address'] == '0xaaaa' and u[1]['decimals'] == 18 and u[1]['rows'] == 20000 and u[0]['how'] == 'binance_spot'


def test_load_bars_naive_utc_close_and_qvol(tmp_path):
    _klines(tmp_path, 'AAAUSDT', 50)
    b = U.load_bars(tmp_path, 'AAAUSDT')
    assert list(b.columns) == ['close', 'qvol'] and b.index.tz is None and b.index[0] == pd.Timestamp('2021-01-01')
    assert b['qvol'].iloc[0] == 5.0 and np.isclose(b['close'].iloc[-1], 2.0)
