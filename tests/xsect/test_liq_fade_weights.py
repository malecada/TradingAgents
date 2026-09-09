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


def test_already_held_symbol_resets_while_cap_full():
    """Verify that already-held symbols reset timer regardless of cap.

    cap=0.1 means 1 slot max. A triggers at bar 10, retriggers at bar 12.
    B triggers at bar 12 (same bar as A's retrigger). A should reset its timer
    and continue holding; B should be ignored (A occupies the only slot).
    Gross sum must never exceed cap.
    """
    trig = _trig({"A": [10, 12], "B": [12]}, syms=("A", "B"))
    W = event_weights_hourly(trig, H=3, w_per=0.1, cap=0.1)

    # First trigger at bar 10: A holds bars 11-13
    assert W["A"].iloc[11] == 0.1
    assert W["A"].iloc[12] == 0.1
    assert W["A"].iloc[13] == 0.1

    # Retrigger at bar 12 (processed at bar 13): A resets timer and continues
    # After reset, A holds bars 13-15 (overlap at bar 13, then extends to 14-15)
    assert W["A"].iloc[14] == 0.1
    assert W["A"].iloc[15] == 0.1

    # B triggered at bar 12 (processed at bar 13): ignored because A occupies slot
    assert W["B"].iloc[13] == 0.0
    assert W["B"].iloc[14] == 0.0
    assert W["B"].iloc[15] == 0.0

    # Verify gross sum never exceeds cap
    assert (W.sum(axis=1) <= 0.1 + 1e-10).all()


def test_freed_slot_on_expiry():
    """Verify that freed slots (via expiry) allow new events to open.

    cap=0.1 means 1 slot max. A triggers at bar 10 with H=1 (holds only bar 11).
    B triggers at bar 11. A's slot expires at bar 12, allowing B to open then.
    Gross sum must never exceed cap.
    """
    trig = _trig({"A": [10], "B": [11]}, syms=("A", "B"))
    W = event_weights_hourly(trig, H=1, w_per=0.1, cap=0.1)

    # A triggered at 10: holds only bar 11 (t+1 with H=1)
    assert W["A"].iloc[11] == 0.1
    assert W["A"].iloc[12] == 0.0

    # B triggered at 11: opens at bar 12 when A's slot freed (also H=1)
    assert W["B"].iloc[11] == 0.0
    assert W["B"].iloc[12] == 0.1
    assert W["B"].iloc[13] == 0.0

    # Verify gross sum never exceeds cap
    assert (W.sum(axis=1) <= 0.1 + 1e-10).all()
