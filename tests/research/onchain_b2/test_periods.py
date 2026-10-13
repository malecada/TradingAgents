from datetime import date, timedelta

from tradingagents.research.onchain_b2 import config, periods


def test_week_denominators():
    w = periods.all_weeks()
    assert len(w) == 510 and w[0] == '2017-01-02' and w[-1] == '2026-10-05'
    d = periods.dictionary_weeks()
    assert len(d) == 104 and d[-1] == '2018-12-24'


def test_lag_rule():
    weeks = periods.all_weeks()
    assert periods.latest_week_for(date(2017, 1, 8), weeks) is None
    assert periods.latest_week_for(date(2017, 1, 9), weeks) == '2017-01-02'
    assert periods.latest_week_for(date(2017, 1, 15), weeks) == '2017-01-02'
    assert periods.latest_week_for(date(2017, 1, 16), weeks) == '2017-01-09'


def test_windows_and_embargo():
    ms = [periods.week_end(w) for w in periods.all_weeks()]
    dev = [m for m in ms if periods.weekly_window(m) == 'dev']
    hold = [m for m in ms if periods.weekly_window(m) == 'holdout']
    assert len(dev) == 378 and dev[0] == date(2017, 10, 2) and dev[-1] == date(2024, 12, 23)
    assert len(hold) == 92 and hold[0] == date(2025, 1, 6) and hold[-1] == date(2026, 10, 5)
    assert periods.weekly_window(date(2024, 12, 30)) is None
    assert periods.daily_window(date(2024, 12, 30)) == 'dev' and periods.daily_window(date(2024, 12, 31)) is None
    assert periods.daily_window(date(2025, 1, 1)) == 'holdout' and periods.daily_window(date(2026, 10, 12)) is None


def test_frozen_numbers_and_ignore():
    c = config.load()
    assert c['k'] == 5000 and c['n_max'] == 32 and c['dictionary']['seed'] == 11
    assert c['gate']['draws'] == 2000 and c['gate']['min_year_wins'] == 4 and c['gate']['max_selected'] == 3
    assert '/research_artifacts/onchain-b2/' in (config.ROOT / '.gitignore').read_text()