# tests/research/onchain_b4/test_markets.py
import json

import pandas as pd
import pytest

from tradingagents.research.onchain_b4 import cmdaily, hourmarket


def _binance(last):
    stop = int(pd.Timestamp(last, tz='UTC').timestamp() * 1000)

    def get(url):
        ms = int(url.split('startTime=')[1].split('&')[0])
        rows = [[t, '0', '0', '0', str(1000 + t / 3.6e9), '0', 0, '5', 0, '0', '0', '0']
                for t in range(ms, min(stop, ms + 1000 * 3_600_000), 3_600_000)]
        return json.dumps(rows).encode()
    return get


def test_hourly_fetch_pages_store_and_seal(tmp_path):
    bars, pages = hourmarket.fetch(_binance('2025-01-03 00:00'), 'ETHUSDT', '2024-11-01', '2025-01-05')
    assert len(bars) == 63 * 24 and len(pages) == 2
    meta = hourmarket.store(bars, pages, tmp_path, '2024-12-31T23')
    assert meta['dev_hours'] == 61 * 24 and meta['sealed_hours'] == 48
    dev = hourmarket.load_dev(tmp_path / 'market' / 'hourly_dev.json', '2024-12-31T23')
    assert dev.index.max() == pd.Timestamp('2024-12-31 23:00') and list(dev.columns) == ['close', 'qvol']
    both = hourmarket.load_all(tmp_path / 'market' / 'hourly_dev.json', tmp_path / 'sealed' / 'hourly_sealed.json')
    assert len(both) == 63 * 24 and both.index.is_monotonic_increasing
    (tmp_path / 'bad.json').write_text(json.dumps({'2025-01-01T00': [1.0, 1.0]}))
    with pytest.raises(ValueError, match='sealed'):
        hourmarket.load_dev(tmp_path / 'bad.json', '2024-12-31T23')


def _cm():
    days = pd.date_range('2024-12-25', '2025-01-05', freq='D')

    def get(url):
        assets = url.split('assets=')[1].split('&')[0].split(',')
        metrics = url.split('metrics=')[1].split('&')[0].split(',')
        page = 2 if 'page=2' in url else 1
        part = days[:6] if page == 1 else days[6:]
        data = [{'asset': a, 'time': d.strftime('%Y-%m-%dT00:00:00.000000000Z'),
                 **{m: str(float(i + 1)) for m in metrics}} for a in assets for i, d in enumerate(part)]
        doc = {'data': data}
        if page == 1:
            doc['next_page_url'] = url + '&page=2'
        return json.dumps(doc).encode()
    return get


def test_coinmetrics_fetch_frame_store_and_seal(tmp_path):
    eth, p1 = cmdaily.fetch(_cm(), ['eth'], ['FlowInExNtv', 'SplyExNtv'], '2024-12-25', '2025-01-05')
    st, p2 = cmdaily.fetch(_cm(), ['usdt', 'usdc'], ['SplyCur'], '2024-12-25', '2025-01-05')
    assert len(p1) == 2 and len(eth['eth']['FlowInExNtv']) == 12
    frame = cmdaily.to_frame({**eth, **st}, ['FlowInExNtv', 'SplyExNtv'], ['usdt', 'usdc', 'dai'])
    assert list(frame.columns) == ['FlowInExNtv', 'SplyExNtv', 'usdt', 'usdc', 'dai'] and frame['dai'].isna().all()
    meta = cmdaily.store(frame, p1 + p2, tmp_path, '2024-12-31')
    assert meta['dev_days'] == 7 and meta['sealed_days'] == 5
    dev = cmdaily.load_dev(tmp_path / 'market' / 'cm_dev.json', '2024-12-31')
    assert dev.index.max() == pd.Timestamp('2024-12-31')
    both = cmdaily.load_all(tmp_path / 'market' / 'cm_dev.json', tmp_path / 'sealed' / 'cm_sealed.json')
    assert len(both) == 12
    with pytest.raises(ValueError, match='sealed'):
        cmdaily.load_dev(tmp_path / 'sealed' / 'cm_sealed.json', '2024-12-31')
