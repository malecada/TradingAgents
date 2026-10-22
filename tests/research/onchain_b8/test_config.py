# tests/research/onchain_b8/test_config.py
from tradingagents.research.onchain_b8 import config


def test_config_window_sets_and_models():
    c = config.load()
    assert config.days(c)[0] == '2020-06-01' and config.days(c)[-1] == '2026-07-29'
    assert config.day_ord('2017-01-02') == 1 and config.EPOCH.isoformat() == '2017-01-01'
    assert c['series'] == ['dep_usd', 'wd_usd', 'dep_cnt', 'wd_cnt', 'tx_cnt', 'active', 'big_cnt']
    assert c['sets'] == {'P0': [], 'P1': ['N'], 'P2': ['N', 'XN']} and c['comparisons'] == [['P1', 'P0'], ['P2', 'P1'], ['P2', 'P0']]
    assert c['folds']['test_years'] == [2022, 2023, 2024, 2025, 2026] and c['folds']['min_train'] == 50000
    assert c['models']['trees_es']['min_tail_pos'] == 10 and c['gate']['seed'] == 20261023
    assert set(c['targets']) == {'V6', 'V24', 'XV24'}


def test_registration_files_exist():
    for name in ('CHARTER.md', 'PLAN.md', 'STATE.md'):
        assert (config.STUDY / name).exists()
