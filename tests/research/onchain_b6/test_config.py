# tests/research/onchain_b6/test_config.py
from tradingagents.research.onchain_b6 import config


def test_config_window_sets_and_tracks():
    c = config.load()
    d = config.days(c)
    assert len(d) == 3571 and d[0] == '2017-01-01' and d[-1] == '2026-10-11'
    assert config.day_ord('2017-01-01') == 0 and config.day_ord('2017-01-02') == 1
    assert c['set_blocks']['X4'] == ['F', 'S', 'E'] and c['set_blocks']['X5'] == ['F', 'S', 'E', 'T']
    assert len(c['comparisons']) == 4 and c['tron_comparison'] == ['X5', 'X4']
    assert c['tracks']['A']['test_years'] == [2019, 2020, 2021, 2022, 2023, 2024]
    assert c['tracks']['B']['groups'] == {'2022-24': [2022, 2023, 2024], '2025-26': [2025, 2026]}
    assert c['targets'] == {'V6': 6, 'V24': 24}


def test_registration_files_exist():
    for name in ('CHARTER.md', 'PLAN.md', 'STATE.md'):
        assert (config.STUDY / name).exists()
