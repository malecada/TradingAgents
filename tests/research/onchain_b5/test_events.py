# tests/research/onchain_b5/test_events.py
import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, events, implied

CFG = config.load()


def test_first_per_window_spacing():
    t = pd.to_datetime(['2023-01-01 00:00', '2023-01-01 05:00', '2023-01-02 00:00', '2023-01-02 01:00', '2023-01-03 02:00'])
    assert [str(x) for x in events.first_per_window(t, 24)] == ['2023-01-01 00:00:00', '2023-01-02 00:00:00', '2023-01-03 02:00:00']


def _bars(n, seed=2):
    idx = pd.date_range('2022-01-01', periods=n, freq='h')
    rng = np.random.default_rng(seed)
    return pd.DataFrame({'close': 1000 * np.exp(np.cumsum(rng.normal(0, 0.004, n))), 'qvol': rng.gamma(2.0, 1e6, n)}, index=idx)


def test_placebo_size_and_vol_targets():
    bars = _bars(24 * 120)
    pl = events.placebo_events(bars, 5, CFG)
    assert len(pl) <= 5 and pl == sorted(pl)
    Y, R = events.vol_targets(bars, 3)
    lc = np.log(bars['close'])
    b = bars.index[100]
    r = lc.diff()
    assert np.isclose(Y.loc[b, 'y3'], np.log(np.sqrt((r.iloc[101:104] ** 2).sum() * 8760 / 3)))
    assert np.isclose(R.loc[b, 'r3'], lc.iloc[103] - lc.iloc[100])


def test_responses_detect_injected_jump():
    idx = pd.date_range('2022-01-01', periods=2000, freq='h')
    S = pd.DataFrame({f's{k}': 0.0 for k in (1, 2)}, index=idx)
    R = pd.DataFrame({f'r{k}': 0.0 for k in (1, 2)}, index=idx)
    ev = list(idx[200::100][:15])
    for e in ev:
        S.loc[e, 's1'] = 1.0 + 0.01 * ev.index(e)
        S.loc[e, 's2'] = 0.5
    iv = pd.Series(50.0, index=idx)
    out = events.responses(ev, S, R, iv, 2, {**CFG['gate'], 'block': 1})
    k1 = [o for o in out if o['k'] == 1][0]
    assert k1['post_vol']['mean'] > 0.9 and k1['post_vol']['lo'] > 0.9 and k1['pre_vol']['mean'] == 0.0
    assert k1['d_iv']['mean'] == 0.0 and k1['n'] == 15


def test_iv_series_uses_nearest_live_expiry():
    ts0 = int(pd.Timestamp('2023-06-01', tz='UTC').timestamp() * 1000)
    rows = [(6.5, 'ETH-1JUN23-1900-C', 99.0),      # expires 08:00, bin 06:00 ends 07:00 < 08:00 + 2h rule: excluded
            (6.6, 'ETH-2JUN23-1900-C', 55.0), (6.7, 'ETH-2JUN23-1900-P', 57.0), (6.8, 'ETH-9JUN23-1900-C', 70.0)]
    df = implied.prepare(pd.DataFrame([{'timestamp': ts0 + int(h * 3_600_000), 'trade_id': str(i), 'instrument_name': n, 'iv': iv,
                                        'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy'}
                                       for i, (h, n, iv) in enumerate(rows)]))
    s = events.iv_series(lambda d: df if d == '2023-06-01' else None, ['2023-06-01'], CFG)
    assert s.loc[pd.Timestamp('2023-06-01 06:00')] == 55.0


def test_pre_window_and_iv_baseline_exclude_event_hour():
    idx = pd.date_range('2022-01-01', periods=500, freq='h')
    S = pd.DataFrame({'s1': 0.0}, index=idx)
    R = pd.DataFrame({'r1': 0.0}, index=idx)
    ev = [idx[100], idx[200], idx[300]]
    iv = pd.Series(50.0, index=idx)
    for e in ev:
        S.loc[e - pd.Timedelta(hours=1), 's1'] = 5.0      # covers the event hour itself
        iv.loc[e] = 99.0                                  # the event hour's own IV bin
    out = events.responses(ev, S, R, iv, 1, {**CFG['gate'], 'block': 1})[0]
    assert out['pre_vol']['mean'] == 0.0 and out['d_iv']['mean'] == 0.0
