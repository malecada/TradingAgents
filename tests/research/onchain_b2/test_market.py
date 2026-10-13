import json
from datetime import date, datetime, timezone

import pytest

from tradingagents.research.onchain_b2 import market as Mk


def _ms(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


def test_coinmetrics_pages():
    p1 = {'data': [{'time': '2024-12-30T00:00:00.000000000Z', 'PriceUSD': '3400.5'}], 'next_page_url': 'NEXT'}
    p2 = {'data': [{'time': '2025-01-02T00:00:00.000000000Z', 'PriceUSD': '3500.0'}]}
    pages = {'NEXT': json.dumps(p2).encode()}
    prices, raw = Mk.fetch_coinmetrics(lambda u: pages.get(u, json.dumps(p1).encode()), date(2024, 12, 30), date(2025, 1, 2))
    assert prices == {date(2024, 12, 30): 3400.5, date(2025, 1, 2): 3500.0} and len(raw) == 2


def test_binance_quote_volume_and_range():
    rows = [[_ms(date(2024, 12, 31)), '1', '1', '1', '1', '9', 0, '1000.5', 1, '0', '0', '0'],
            [_ms(date(2025, 1, 1)), '1', '1', '1', '1', '9', 0, '2000.0', 1, '0', '0', '0']]
    vols, raw = Mk.fetch_binance(lambda u: json.dumps(rows).encode(), date(2024, 12, 31), date(2025, 1, 1))
    assert vols == {date(2024, 12, 31): 1000.5, date(2025, 1, 1): 2000.0} and len(raw) == 1


def test_store_splits_at_cutoff(tmp_path):
    prices = {date(2024, 12, 31): 1.0, date(2025, 1, 1): 2.0}
    vols = {date(2024, 12, 31): 10.0, date(2025, 1, 1): 20.0}
    Mk.store(prices, vols, {'coinmetrics': [b'{}'], 'binance': [b'[]']}, tmp_path, date(2024, 12, 31))
    p, v = Mk.load_dev(tmp_path / 'market' / 'dev.json', date(2024, 12, 31))
    assert p == {date(2024, 12, 31): 1.0} and v == {date(2024, 12, 31): 10.0}
    pa_, va = Mk.load_all(tmp_path / 'market' / 'dev.json', tmp_path / 'sealed' / 'market_sealed.json')
    assert pa_[date(2025, 1, 1)] == 2.0 and va[date(2025, 1, 1)] == 20.0
    assert '2025-01-01' not in (tmp_path / 'market' / 'dev.json').read_text()


def test_load_dev_refuses_sealed_dates(tmp_path):
    f = tmp_path / 'dev.json'
    f.write_text(json.dumps({'prices': {'2025-01-01': 1.0}, 'volumes': {}}))
    with pytest.raises(ValueError, match='sealed'):
        Mk.load_dev(f, date(2024, 12, 31))