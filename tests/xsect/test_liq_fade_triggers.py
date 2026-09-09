import numpy as np
import pandas as pd
from tradingagents.xsect.liq_fade import cascade_triggers


def _panel(hours=3000, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2021-01-01", periods=hours, freq="1h", tz="UTC")
    ret = rng.normal(0, 0.005, hours)
    close = pd.DataFrame({"AAA": 100 * np.exp(np.cumsum(ret))}, index=idx)
    qvol = pd.DataFrame({"AAA": rng.lognormal(10, 0.3, hours)}, index=idx)
    return close, qvol


def test_crash_with_volume_spike_triggers():
    close, qvol = _panel()
    t = 2500
    close.iloc[t:, 0] *= 0.90          # -10% crash bar at t
    qvol.iloc[t, 0] *= 50              # volume spike at t
    trig = cascade_triggers(close, qvol, thr=2.5)
    assert bool(trig.iloc[t, 0])
    assert trig.iloc[t - 100 : t, 0].sum() == 0


def test_crash_without_volume_does_not_trigger():
    close, qvol = _panel()
    close.iloc[2500:, 0] *= 0.90       # crash, but volume normal
    trig = cascade_triggers(close, qvol, thr=2.5)
    assert not bool(trig.iloc[2500, 0])


def test_causal_future_edit_does_not_change_past():
    close, qvol = _panel()
    close.iloc[2500:, 0] *= 0.90
    qvol.iloc[2500, 0] *= 50
    a = cascade_triggers(close, qvol, thr=2.5).iloc[:2501]
    close.iloc[2700:, 0] *= 0.5        # edit strictly-future data
    qvol.iloc[2700:, 0] *= 100
    b = cascade_triggers(close, qvol, thr=2.5).iloc[:2501]
    assert a.equals(b)


def test_warmup_no_triggers_before_min_periods():
    close, qvol = _panel()
    close.iloc[100:, 0] *= 0.80
    qvol.iloc[100, 0] *= 100
    trig = cascade_triggers(close, qvol, thr=2.5)
    assert trig.iloc[:1440].to_numpy().sum() == 0
