# tests/research/onchain_b5/test_config.py
from tradingagents.research.onchain_b5 import config


def test_config_schedules_sets_and_window():
    c = config.load()
    assert c['schedules']['S6'] == {'hour': 2, 'tau_h': 6, 'expiry_days': 0}
    assert c['schedules']['S24'] == {'hour': 8, 'tau_h': 24, 'expiry_days': 1}
    assert c['sets']['M2'][:3] == c['sets']['M1'] and c['sets']['IV'] == ['mk_iv']
    d = config.days(c)
    assert len(d) == 2029 and d[0] == '2021-03-24' and d[-1] == '2026-10-12'


def test_registration_files_exist():
    for name in ('CHARTER.md', 'PLAN.md', 'STATE.md'):
        assert (config.STUDY / name).exists()
