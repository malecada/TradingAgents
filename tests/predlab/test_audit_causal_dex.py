"""Later pools and future daily quotes cannot affect an actionable DEX score."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import predlab_nlst2_features as f2
import predlab_nlst3_features as f3
import predlab_nlst_dex_p0 as dex


def frame():
    df = pd.DataFrame({c: [0., 2., 4., 6., 8.] for c in f2.SIGNS})
    df['quarter'] = '2021Q1'
    df['decision_ts'] = [10., 20., 30., 30., 40.]
    df['available_ts'] = [10., 20., 30., 30., 40.]
    return df


def test_causal_normalization_ignores_later_same_time_and_unavailable_observations():
    df = frame()
    original = f2.per_quarter_z(df, ['lp_secured'])
    # Known history [0,2] has mean1 and sample sd sqrt(2), so z(4)=3/sqrt(2).
    assert original.loc[2, 'lp_secured'] == pytest.approx(3 / np.sqrt(2))
    df.loc[3:, 'lp_secured'] = 100000
    pd.testing.assert_frame_equal(original.iloc[:3], f2.per_quarter_z(df, ['lp_secured']).iloc[:3])
    df.loc[1, 'available_ts'] = 35.
    assert np.isnan(f2.per_quarter_z(df, ['lp_secured']).loc[2, 'lp_secured'])


def test_missing_feature_stays_missing_when_known_history_is_constant():
    df = frame()
    df[list(f2.SIGNS)] = 1.
    df.loc[2, list(f2.SIGNS)[4:]] = np.nan
    assert f2.per_quarter_z(df, list(f2.SIGNS)).loc[2].notna().sum() == 4
    assert np.isnan(f2.composite(df).loc[2])


def test_legacy_feature_table_without_decision_availability_is_rejected():
    with pytest.raises(ValueError, match='decision_ts|availability'):
        f2.composite(frame().drop(columns=['decision_ts', 'available_ts']))


def test_eth_conversion_uses_last_completed_five_minute_quote():
    ts = pd.date_range('2021-01-01 00:55', periods=3, freq='5min', tz='UTC')
    quotes = pd.Series([2000., 3000., 9000.], index=ts)
    quotes.attrs.update(bar_interval='5min', timestamp_label='open')
    # The 00:55 open bar closes at 01:00; the 01:00 bar is not closed at01:02.
    assert dex.eth_usd_at(pd.Timestamp('2021-01-01 01:02Z').timestamp(), quotes) == 2000.
    quotes.iloc[1:] = 50000.
    assert dex.eth_usd_at(pd.Timestamp('2021-01-01 01:02Z').timestamp(), quotes) == 2000.
    assert dex.eth_usd_at(pd.Timestamp('2021-01-01 01:05Z').timestamp(), quotes) == 50000.


def test_eth_conversion_refuses_missing_or_stale_quote_instead_of_daily_substitute():
    quotes = pd.Series([2000.], index=pd.DatetimeIndex(['2021-01-01 00:00Z']))
    with pytest.raises(ValueError, match='five.minute|5m|completed|stale'):
        dex.eth_usd_at(pd.Timestamp('2021-01-01 01:00Z').timestamp(), quotes)


def test_ownership_failure_is_not_cached_as_negative(tmp_path, monkeypatch):
    monkeypatch.setattr(f3, 'RAW3', tmp_path)
    def failed(*args):
        raise RuntimeError('provider unavailable')
    monkeypatch.setattr(f3, 'get_logs', failed)
    meta = dict(pair='pool', token0='token', token1='weth', weth_is_0=False, block=1)
    assert np.isnan(f3.fetch_ownership(meta, 10))
    assert not (tmp_path / 'pool.json').exists()
