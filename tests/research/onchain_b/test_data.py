from datetime import date, timedelta

from tradingagents.research.onchain_b import calendar as cal
from tradingagents.research.onchain_b import data as Dt
from tradingagents.research.onchain_b import prices as P


def _prices():
    d0 = date(2021, 12, 1)
    return {d0 + timedelta(days=k): 1000.0 + k for k in range(1200)}


def test_train_examples_never_touch_2024():
    px = _prices()
    sc = P.Scaler().fit(px, [date(2022, 2, 6)])
    ex = Dt.examples('train', px, sc, 'classification')
    assert len(ex) == 693 and all(w < '2024' for e in ex for w in e.step_weeks)
    assert all(max(e.step_days) + timedelta(days=1) < date(2024, 1, 1) for e in ex)


def test_test_examples_use_available_weeks_only():
    px = _prices()
    sc = P.Scaler().fit(px, [date(2022, 2, 6)])
    ex = Dt.examples('test', px, sc, 'regression')
    assert len(ex) == 365
    for e in ex:
        for t, w in zip(e.step_days, e.step_weeks):
            assert cal.week_end(w) <= t


def test_batches_are_chronological_and_sized():
    px = _prices()
    sc = P.Scaler().fit(px, [date(2022, 2, 6)])
    ex = Dt.examples('train', px, sc, 'regression')
    bs = list(Dt.batches(ex, 16))
    assert len(bs) == 44 and bs[0].prices.shape == (16, 28) and bs[-1].prices.shape[0] == 693 - 43 * 16
    assert bs[0].decisions[0] < bs[1].decisions[0]
