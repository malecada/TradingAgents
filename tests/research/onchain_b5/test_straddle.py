# tests/research/onchain_b5/test_straddle.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, straddle


def test_black76_values_parity_and_extremes():
    c, p = straddle.black76(np.array([100.0]), np.array([100.0]), np.array([1.0]), np.array([0.2]))
    assert np.isclose(c[0], 7.9656, atol=1e-4) and np.isclose(p[0], 7.9656, atol=1e-4)
    F, K = np.array([2000.0, 2000.0, 2000.0]), np.array([1500.0, 2000.0, 3000.0])
    c, p = straddle.black76(F, K, np.full(3, 6 / 8760), np.full(3, 0.6))
    assert np.isfinite(c).all() and np.isfinite(p).all() and np.allclose(c - p, F - K)


def test_pnl_signs_fees_and_cap():
    s0, K, T = np.array([2000.0, 2000.0]), np.array([2000.0, 2000.0]), np.array([6 / 8760] * 2)
    iv = np.array([50.0, 50.0])
    big = np.array([2100.0, 2100.0])
    p, prem = straddle.pnl(np.array([1, -1]), s0, K, big, T, iv, iv, 0.0003, 0.125)
    # long + short on the same straddle sum to minus both sides' fees: entry 0.6 per leg, delivery 0.63 on the call
    assert p[0] > 0 > p[1] and np.isclose(p[0] + p[1], -2 * (2 * 0.6 + 0.63), atol=1e-6)
    p0, _ = straddle.pnl(np.array([0]), s0[:1], K[:1], big[:1], T[:1], iv[:1], iv[:1], 0.0003, 0.125)
    assert p0[0] == 0.0
    one = lambda x: np.array([x])
    c, pu = straddle.black76(one(2000.0), one(2500.0), one(6 / 8760), one(0.5))
    out, _ = straddle.pnl(one(1), one(2000.0), one(2500.0), one(2000.0), one(6 / 8760), one(50.0), one(50.0), 0.0003, 0.125)
    assert 0.125 * c[0] < 0.6                               # far OTM call: the 12.5 % cap binds
    assert np.isclose(out[0], 500.0 - (c[0] + pu[0]) - (0.125 * c[0] + 0.6) - 0.6)


def test_sides_and_backtest_benchmarks():
    assert list(straddle.sides(np.array([0.3, 0.0, -0.3]), 0.1)) == [1, 0, -1]
    idx = pd.date_range('2022-01-01 02:00', '2026-06-30', freq='D')
    rng = np.random.default_rng(1)
    n = len(idx)
    real = rng.normal(np.log(0.5), 0.3, n)
    df = pd.DataFrame({'s0': 2000.0, 'K': 2000.0, 'tau_h': 6.0, 'mk_iv': np.log(0.5), 'iv_ask': 51.0, 'iv_bid': 49.0,
                       'y': real}, index=idx)
    df['sT'] = 2000.0 * np.exp(0.798 * np.exp(real) * np.sqrt(6 / 8760) * rng.choice([-1, 1], n))   # |move| = E|Z| σ√T
    preds = pd.DataFrame({'linear:M1': rng.normal(np.log(0.5), 0.3, n), 'linear:M2': real}, index=idx)
    cfg = config.load()
    cfg = {**cfg, 'families': ['linear']}
    out = straddle.backtest(df, preds, cfg)
    get = {(o['rule'], o['variant'], o['theta']): o for o in out}
    assert ('always_buy', None, None) in get and ('always_sell', None, None) in get
    assert get[('signal', 'M2', 0.1)]['groups']['2022-24']['total'] > get[('signal', 'M1', 0.1)]['groups']['2022-24']['total']
    assert get[('flip', 'M2', 0.1)]['groups']['2022-24']['total'] < 0
