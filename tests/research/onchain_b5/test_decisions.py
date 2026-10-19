# tests/research/onchain_b5/test_decisions.py
import json

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b5 import config, decisions, implied

CFG = config.load()


def _bars(start, hours, seed=1):
    idx = pd.date_range(start, periods=hours, freq='h')
    rng = np.random.default_rng(seed)
    return pd.DataFrame({'close': 1900 * np.exp(np.cumsum(rng.normal(0, 0.005, hours))),
                         'qvol': rng.gamma(2.0, 1e6, hours)}, index=idx)


def test_realized_logvol():
    idx = pd.date_range('2023-06-01', periods=10, freq='h')
    closes = pd.Series(100 * np.exp(0.01 * np.arange(10)), index=idx)
    t = pd.Timestamp('2023-06-01 03:00')
    want = np.log(np.sqrt(6 * 0.01 ** 2 * 8760 / 6))
    assert np.isclose(decisions.realized_logvol(closes, t, 6), want)
    assert np.isnan(decisions.realized_logvol(closes, pd.Timestamp('2023-06-01 06:00'), 6))


def test_fill_spread_uses_only_earlier_rows():
    df = pd.DataFrame({'iv_mid': [50.0, 50.0, 50.0, 50.0], 'iv_ask': [52.0, np.nan, 60.0, np.nan],
                       'iv_bid': [48.0, 49.0, 40.0, np.nan]}, index=pd.date_range('2023-01-01', periods=4))
    f = decisions.fill_spread(df, 30)
    assert f['iv_ask'].iloc[1] == 52.0            # earlier half-spread 2 only
    assert f['iv_ask'].iloc[3] == 50.0 + np.median([2.0, 10.0]) and f['iv_bid'].iloc[3] == 50.0 - 6.0


def _trades_for(day, tag):
    t = pd.Timestamp(day)
    ts0 = int(pd.Timestamp(day, tz='UTC').timestamp() * 1000)
    exp6 = t + pd.Timedelta(hours=8)
    name = f"ETH-{exp6.day}{exp6.strftime('%b').upper()}{exp6.strftime('%y')}-1900-C"
    rows = [{'timestamp': ts0 + int(h * 3_600_000), 'trade_id': f'{day}-{i}', 'instrument_name': name, 'iv': 50.0 + tag,
             'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy' if i % 2 else 'sell'}
            for i, h in enumerate([0.5, 1.0, 1.5, 1.7])]
    return implied.prepare(pd.DataFrame(rows))


def test_build_skips_ineligible_and_is_causal():
    cfg = json.loads(json.dumps(CFG))
    cfg['window'] = {'start': '2023-06-10', 'end': '2023-06-14'}
    bars = _bars('2023-05-01', 24 * 50)
    dvol = pd.Series(60.0, index=bars.index)
    flows = pd.DataFrame({'eth_x__h1z': np.arange(len(bars), dtype=float), 'stable_x__h1z': 1.0}, index=bars.index)
    have = {'2023-06-10', '2023-06-11', '2023-06-13', '2023-06-14'}
    get = lambda day: _trades_for(day, 0) if day in have else None
    a = decisions.build('S6', bars, dvol, flows, get, cfg)
    assert [str(i) for i in a.index] == ['2023-06-10 02:00:00', '2023-06-11 02:00:00', '2023-06-13 02:00:00', '2023-06-14 02:00:00']
    t = a.index[0]
    assert a.loc[t, 'eth_x__h1z'] == flows.loc[t - pd.Timedelta(hours=1), 'eth_x__h1z']
    assert a.loc[t, 's0'] == bars.loc[t - pd.Timedelta(hours=1), 'close'] and a.loc[t, 'sT'] == bars.loc[t + pd.Timedelta(hours=5), 'close']
    assert a.loc[t, 'K'] == 1900.0 and np.isclose(a.loc[t, 'mk_iv'], np.log(0.5))
    bars2 = bars.copy()
    bars2.loc[t:, 'close'] *= 1.5                 # change prices from the decision time on
    flows2 = flows.copy()
    flows2.loc[t:, 'eth_x__h1z'] = -99.0
    b = decisions.build('S6', bars2, dvol, flows2, get, cfg)
    feats = [c for c in a.columns if c.startswith(('h0_', 'px_', 'mk_', 'eth_', 'stable_'))]
    pd.testing.assert_series_equal(a.loc[t, feats], b.loc[t, feats])
