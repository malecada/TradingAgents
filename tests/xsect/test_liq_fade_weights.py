import pandas as pd
from tradingagents.xsect.liq_fade import event_weights_hourly


def _trig(events: dict, hours=50, syms=("A", "B")):
    idx = pd.date_range("2021-01-01", periods=hours, freq="1h", tz="UTC")
    t = pd.DataFrame(False, index=idx, columns=list(syms))
    for s, bars in events.items():
        t.iloc[bars, t.columns.get_loc(s)] = True
    return t


def test_hold_window_t_plus_1_to_t_plus_H():
    W = event_weights_hourly(_trig({"A": [10]}), H=3)
    col = W["A"].to_numpy()
    assert col[10] == 0.0                       # trigger bar itself: flat
    assert list(col[11:14]) == [0.1, 0.1, 0.1]  # t+1..t+3
    assert col[14] == 0.0


def test_retrigger_resets_timer():
    W = event_weights_hourly(_trig({"A": [10, 12]}), H=3)
    assert list(W["A"].to_numpy()[11:16]) == [0.1, 0.1, 0.1, 0.1, 0.1]  # 11..15
    assert W["A"].iloc[16] == 0.0


def test_gross_cap_ignores_excess_event():
    trig = _trig({s: [10] for s in "ABCDEFGHIJK"}, syms=tuple("ABCDEFGHIJK"))
    W = event_weights_hourly(trig, H=3)
    assert W.iloc[11].sum() == 1.0              # 10 events × 0.1, 11th ignored
    assert W["K"].iloc[11] == 0.0               # last column dropped


def test_no_shorts_and_no_negative_weights():
    W = event_weights_hourly(_trig({"A": [10]}), H=3)
    assert (W.to_numpy() >= 0).all()
