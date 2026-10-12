from datetime import date, timedelta

from tradingagents.research.onchain_b import calendar as cal


def test_week_denominator():
    w = cal.weeks()
    assert len(w) == 156 and w[0] == '2022-01-03' and w[-1] == '2024-12-23'
    assert cal.week_days('2022-01-03') == [f'2022-01-0{k}' for k in range(3, 10)]


def test_availability_lag():
    assert cal.available_week(date(2022, 1, 9)) is None
    assert cal.available_week(date(2022, 1, 10)) == '2022-01-03'
    assert cal.available_week(date(2022, 1, 16)) == '2022-01-03'
    assert cal.available_week(date(2022, 1, 17)) == '2022-01-10'
    assert cal.available_week(date(2024, 12, 31)) == '2024-12-23'


def test_fold_membership_and_warmup():
    train, test = cal.decision_dates('train'), cal.decision_dates('test')
    assert train[0] == date(2022, 2, 6) and train[-1] == date(2023, 12, 30) and len(train) == 693
    assert test[0] == date(2024, 1, 1) and test[-1] == date(2024, 12, 30) and len(test) == 365
    assert all(d + timedelta(days=1) < date(2024, 1, 1) for d in train)


def test_warmup_exclusion():
    # 2022-02-05 has a step (2022-01-09) with no available week → not a training decision date
    assert date(2022, 2, 5) not in cal.decision_dates('train')
    assert all(cal.available_week(t) is not None for t in cal.window(date(2022, 2, 6)))


def test_window_length():
    w = cal.window(date(2023, 3, 1))
    assert len(w) == 28 and w[-1] == date(2023, 3, 1) and w[0] == date(2023, 2, 2)
