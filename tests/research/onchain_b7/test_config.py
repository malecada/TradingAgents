# tests/research/onchain_b7/test_config.py
from tradingagents.research.onchain_b7 import config


def test_config_series_sets_tracks_and_targets():
    c = config.load()
    assert len(c['series']['b4']) == 15 and len(c['series']['b6']) == 39
    assert c['sets'] == {'X0': [], 'X1': ['F'], 'X1a': ['FA'], 'Y1': ['N4'], 'Y2': ['N4', 'N6']}
    assert c['set_comparisons'] == [['Y1', 'X1'], ['Y1', 'X1a'], ['Y2', 'Y1'], ['X1', 'X0'], ['Y2', 'X0']]
    assert c['cross_comparisons'] == [[['trees_es', 'Y2'], ['trees_fixed', 'Y2']]]
    assert c['tracks']['A']['test_years'] == [2020, 2021, 2022, 2023, 2024] and c['tracks']['A']['min_year_wins'] == 3
    assert c['tracks']['B']['groups'] == {'2022-24': [2022, 2023, 2024], '2025-26': [2025, 2026]}
    assert set(c['targets']) == {'V6', 'V24', 'J6', 'J24', 'M6', 'M24'} and c['targets']['J6']['task'] == 'classification'
    assert c['models']['trees_es']['max_iter'] == 600 and c['gate']['seed'] == 20261022


def test_registration_files_exist():
    for name in ('CHARTER.md', 'PLAN.md', 'STATE.md'):
        assert (config.STUDY / name).exists()
