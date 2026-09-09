import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import predlab_fetch_klines_5m as f5
import predlab_fetch_oi_5m as oi
from tradingagents.predlab.rv import aggregate_rv


def test_one_row_cannot_cover_month_or_day():
    one = pd.DataFrame({'close': [1.]}, index=pd.DatetimeIndex(['2021-02-01T00:00:00Z']))
    assert f5.month_needs_fetch(pd.Period('2021-02'), one, set())
    assert oi.day_needs_fetch(pd.Timestamp('2021-02-01'), one, set())
    full = pd.DataFrame({'close': 1.}, index=pd.date_range('2021-02-01', '2021-03-01', freq='5min', tz='UTC', inclusive='left'))
    assert not f5.month_needs_fetch(pd.Period('2021-02'), full, set())
    assert f5.month_needs_fetch(pd.Period('2021-02'), full.drop(full.index[30]), set())


def test_fetch_revisits_last_cached_candle_and_excludes_unfinished_tail(monkeypatch):
    old = pd.DataFrame({'close': [100.]}, index=pd.DatetimeIndex(['2021-02-01T00:00:00Z']))
    def tail(sym, start_ms, end_ms):
        assert start_ms == 1612137600000  # re-fetch cached00:00 candle, not00:05
        return pd.DataFrame({'close': [101., 999.]},
                            index=pd.DatetimeIndex(['2021-02-01T00:00:00Z', '2021-02-01T00:05:00Z']))
    monkeypatch.setattr(f5, 'fetch_fapi_tail', tail)
    out = f5.fetch_symbol('ETHUSDT', '2021-02-01', old, set(), now=pd.Timestamp('2021-02-01T00:07:00Z'))
    assert out.close.tolist() == [101.]


def test_rv_retains_missing_clock_bucket_and_never_bridges_price_gap():
    times = pd.date_range('2021-01-01', periods=48, freq='5min', tz='UTC')
    bars = pd.DataFrame({'ts': times.asi8 // 10**6, 'close': 100., 'high': 101., 'low': 99.,
                         'quote_volume': 1., 'taker_buy_quote_volume': .5, 'n_trades': 1.})
    bars = bars.drop(index=range(24, 36))
    bars.loc[36:, ['close', 'high', 'low']] *= 2
    out = aggregate_rv(bars, '1h')
    assert out.index.tolist() == times[[12, 24, 36]].tolist()
    assert out.n_bars.tolist() == [12, 0, 12]
    assert out.rv.iloc[0] == 0.
    assert np.isnan(out.rv.iloc[1:]).all()
    assert np.isnan(out.ret.iloc[1:]).all()
    assert np.isnan(out.quote_volume.iloc[1])


def test_partial_period_volume_and_return_are_unknown_not_partial_targets():
    times = pd.date_range('2021-01-01', periods=24, freq='5min', tz='UTC')
    bars = pd.DataFrame({'ts': times.asi8 // 10**6, 'close': 100., 'high': 101., 'low': 99.,
                         'quote_volume': 1., 'taker_buy_quote_volume': .5, 'n_trades': 1.}).drop(index=20)
    out = aggregate_rv(bars, '1h')
    assert out.n_bars.iloc[0] == 11
    assert np.isnan(out.loc[out.index[0], ['rv', 'ret', 'quote_volume', 'n_trades']]).all()
