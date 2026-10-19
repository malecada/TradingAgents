# tests/research/onchain_b5/test_implied.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, implied

C = config.load()['implied']


def test_parse_instrument_names():
    p = implied.parse(['ETH-2JUN21-2500-C', 'BTC-28JUN19-11000-P'])
    assert list(p['expiry']) == [pd.Timestamp('2021-06-02 08:00'), pd.Timestamp('2019-06-28 08:00')]
    assert list(p['strike']) == [2500.0, 11000.0] and list(p['kind']) == ['C', 'P']


def test_wmedian():
    assert implied.wmedian(np.array([3.0, 1.0, 2.0]), np.array([1.0, 1.0, 5.0])) == 2.0


def _day(rows):
    ts0 = int(pd.Timestamp('2023-06-01', tz='UTC').timestamp() * 1000)
    return implied.prepare(pd.DataFrame([{'timestamp': ts0 + int(h * 3_600_000), 'trade_id': str(i), 'instrument_name': n,
                                          'iv': iv, 'price': 0.01, 'index_price': 1900.0, 'amount': a, 'direction': d}
                                         for i, (h, n, iv, a, d) in enumerate(rows)]))


def test_decision_iv_window_moneyness_sides_and_eligibility():
    t = pd.Timestamp('2023-06-01 03:00')                         # window [01:00, 03:00)
    exp = pd.Timestamp('2023-06-01 08:00')
    tr = _day([(0.5, 'ETH-1JUN23-1900-C', 99.0, 1, 'buy'),       # before the window: excluded
               (1.0, 'ETH-1JUN23-1900-C', 50.0, 2, 'buy'),
               (1.5, 'ETH-1JUN23-1900-P', 52.0, 1, 'sell'),
               (1.6, 'ETH-1JUN23-1925-C', 48.0, 1, 'sell'),
               (1.7, 'ETH-1JUN23-2100-C', 80.0, 5, 'buy'),          # far strike: excluded
               (1.8, 'ETH-2JUN23-1900-C', 70.0, 5, 'buy'),          # other expiry: excluded
               (3.1, 'ETH-1JUN23-1900-C', 90.0, 5, 'buy')])         # after t: excluded
    r = implied.decision_iv(tr, t, exp, C)
    assert r['n_trades'] == 3 and r['iv_mid'] == 50.0 and r['iv_ask'] == 50.0 and r['iv_bid'] == 48.0
    assert r['strikes'] == [1900.0, 1925.0]
    assert implied.decision_iv(tr, t, pd.Timestamp('2023-06-02 08:00'), C) is None    # fewer than 3 trades


def test_decision_iv_ignores_zero_iv_trades():
    t, exp = pd.Timestamp('2023-06-01 03:00'), pd.Timestamp('2023-06-01 08:00')
    rows = [(1.0, 'ETH-1JUN23-1900-C', 50.0, 1, 'buy'), (1.2, 'ETH-1JUN23-1900-P', 52.0, 1, 'sell'),
            (1.4, 'ETH-1JUN23-1875-C', 0.0, 9, 'buy')]                     # iv 0: at/below intrinsic
    assert implied.decision_iv(_day(rows), t, exp, C) is None              # only 2 usable trades
    r = implied.decision_iv(_day(rows + [(1.6, 'ETH-1JUN23-1900-C', 51.0, 1, 'sell')]), t, exp, C)
    assert r['n_trades'] == 3 and r['iv_mid'] == 51.0 and r['iv_ask'] == 50.0
