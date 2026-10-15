# tests/research/onchain_b4/test_config.py
from tradingagents.research.onchain_b4 import config


def test_config_counts_windows_and_tokens():
    c = config.load()
    n = sum(len(c['comparisons'][t['kind']]) for t in c['targets'].values()) * len(c['families'])
    assert n == 42
    days = config.days(c)
    assert len(days) == 3571 and days[0] == '2017-01-01' and days[-1] == '2026-10-11'
    w = config.windows(c)
    assert w['dev_end'].isoformat() == '2024-12-31' and w['holdout_start'].isoformat() == '2025-01-01'
    assert sorted(v['decimals'] for v in c['tokens'].values()) == [6, 6, 18]
    assert all(v[0] in ('f0_', 'h0_') for v in c['sets'].values())


def test_study_registration_files_exist():
    for name in ('CHARTER.md', 'gates.json', 'STATE.md'):
        assert (config.STUDY / name).exists()
