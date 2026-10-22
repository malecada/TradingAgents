# tests/research/onchain_b8/test_cli8.py
import copy
import json

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2.s3source import DayUnavailable
from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6 import labels6
from tradingagents.research.onchain_b6.labels6 import LabelState
from tradingagents.research.onchain_b8 import cli, config, reader8
from tradingagents.research.onchain_b8.reader8 import Day8

A, B, X = ('0x' + ch * 40 for ch in 'abx')
T0, T1 = '2020-06-01', '2021-12-31'


def _klines(path, symbol, n, rng, start=T0):
    idx = pd.date_range(start, periods=n, freq='h', tz='UTC')
    close = 10 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    pd.DataFrame({'open': close, 'high': close, 'low': close, 'close': close, 'volume': 1.0, 'quote_volume': rng.gamma(2, 1e5, n),
                  'taker_buy_quote_volume': 1.0}, index=pd.Index(idx, name='ts')).to_parquet(path / f'{symbol}.parquet')


def _setup(tmp_path, monkeypatch, unavailable=()):
    rng = np.random.default_rng(41)
    cfg = copy.deepcopy(config.load())
    cfg['window'] = {'first_day': T0, 'last_day': T1}
    cfg['universe']['min_rows'] = 1000
    cfg['s3']['retries'] = []
    cfg['panel']['min_tokens_hour'] = 2
    cfg['folds'] = {'test_years': [2021], 'inner_len': 300, 'min_train': 100, 'min_year_wins': 1}
    cfg['models']['trees_es'].update({'max_iter': 20, 'min_iter': 5})
    cfg['gate'].update({'draws': 100, 'block': 24})
    k, b6, art, study = tmp_path / 'k', tmp_path / 'b6', tmp_path / 'b8', tmp_path / 'study'
    for p in (k, b6 / 'labels', b6 / 'state', study / 'config'):
        p.mkdir(parents=True)
    n = 24 * 579
    for sym in ('AAAUSDT', 'BBBUSDT', 'CCCUSDT'):
        _klines(k, sym, n, rng)
    tm = {'map': {'AAAUSDT': {'address': '0x' + '1' * 40, 'decimals': 18, 'how': 'binance_spot'},
                  'BBBUSDT': {'address': '0x' + '2' * 40, 'decimals': 6, 'how': 'binance_spot'},
                  'CCCUSDT': {'address': '0x' + '3' * 40, 'decimals': 18, 'how': 'binance_spot'}}}
    (tmp_path / 'map.json').write_text(json.dumps(tm))
    doc = {'exchange': {X: 'okx'}, 'dex': [], 'bridge': [], 'mev': [], 'funds': [], 'issuer': {'usdt_treasury': '0x5754284f345afc66a98fbb0a0afe71e0f007b949'}}
    labels6.save(doc, b6 / 'labels' / 'labels6.json')
    st = LabelState(doc, doc['issuer']['usdt_treasury'])
    st.ex_first[:] = config.day_ord('2020-01-01')
    np.savez(b6 / 'state' / 'state.npz', ex_first=st.ex_first, **{f'cls_first_{c}': st.cls_first[c] for c in labels6.CLASSES},
             bits=np.zeros(8, np.uint8), last_day=np.array(['2026-10-11']))
    monkeypatch.setattr(config, 'KLINES', k)
    monkeypatch.setattr(config, 'TOKEN_MAP', tmp_path / 'map.json')
    monkeypatch.setattr(cli, 'B6', b6)
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli, 'STUDY', study)
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)
    monkeypatch.setattr(cli.config, 'universe', lambda: json.loads((study / 'config' / 'universe.json').read_text())['tokens'])
    monkeypatch.setattr(cli, 'filesystem', lambda: None)
    monkeypatch.setattr(cli.shutil, 'disk_usage', lambda p: type('U', (), {'free': 10**12})())
    ka, kb, kx = addr_keys(np.array([A, B, X], object))

    def fake(day, **kw):
        if day in unavailable:                                                      # a set: tests may clear it
            raise DayUnavailable(day, ['boom'])
        t0 = int(pd.Timestamp(day, tz='UTC').timestamp())
        r = np.random.default_rng(int(day.replace('-', '')))
        n_tr = 40
        src = r.choice([ka, kb, kx], n_tr)
        dst = r.choice([ka, kb, kx], n_tr)
        return Day8(src=src.astype(np.uint64), dst=dst.astype(np.uint64), token=r.integers(0, 3, n_tr).astype(np.int16),
                    amount=r.gamma(2, 1000, n_tr), ts=np.sort(t0 + r.integers(0, 86400, n_tr)).astype(np.int64), rows={'transfers': n_tr})
    monkeypatch.setattr(reader8, 'read_day8', fake)
    return cfg, art, study


def test_universe_stage_freezes_once(tmp_path, monkeypatch):
    cfg, art, study = _setup(tmp_path, monkeypatch)
    cli.main(['universe'])
    u = json.loads((study / 'config' / 'universe.json').read_text())
    assert [t['symbol'] for t in u['tokens']] == ['AAAUSDT', 'BBBUSDT', 'CCCUSDT'] and u['min_rows'] == 1000
    with pytest.raises(SystemExit):
        cli.main(['universe'])


def test_pass_resumes_and_marks_unavailable(tmp_path, monkeypatch):
    cfg, art, study = _setup(tmp_path, monkeypatch, unavailable={'2020-06-03'})
    cli.main(['universe'])
    cli.main(['pass', '--end', '2020-06-05'])
    d = pd.read_parquet(art / 'days' / '2020-06-02.parquet')
    assert len(d) == 72 and list(d.columns) == ['hour', 'token'] + cli.hourly8.SERIES and d['dep_usd'].notna().all()
    assert (art / 'days' / '2020-06-03.unavailable.json').exists() and not (art / 'days' / '2020-06-03.parquet').exists()
    stamp = (art / 'days' / '2020-06-02.parquet').stat().st_mtime_ns
    cli.main(['pass', '--end', '2020-06-07'])
    assert (art / 'days' / '2020-06-02.parquet').stat().st_mtime_ns == stamp and (art / 'days' / '2020-06-07.parquet').exists()
    assert not cli.pass_complete() and cli.day_status('2020-06-03') == 'unavailable'


def test_panel_forecast_report(tmp_path, monkeypatch):
    cfg, art, study = _setup(tmp_path, monkeypatch, unavailable={'2021-06-15'})
    cli.main(['universe'])
    cli.main(['pass'])
    assert cli.pass_complete()
    cli.main(['panel'])
    p = pd.read_parquet(art / 'panel' / 'panel.parquet')
    assert p['token'].nunique() == 3 and p.index.min() >= pd.Timestamp(T0) + pd.Timedelta(days=30)
    assert {'n_dep_usd__ex1', 'xs_n_dep_usd__s24z', 'xs_h0_rv24', 'h0_rv24', 'px_rv6', 'V6', 'V24', 'XV24'} <= set(p.columns)
    assert p['n_dep_usd__ex1'].dtype == np.float32
    assert p.loc['2021-06-15':'2021-06-16 22:00', 'n_dep_usd__s24z'].isna().all() and p.loc['2021-06-16 23:00':'2021-06-17', 'n_dep_usd__s24z'].notna().all()
    cli.main(['forecast', '--only', 'V6'])
    assert (art / 'forecast' / 'V6.json').exists()
    cli.main(['forecast'])
    res = json.loads((art / 'forecast' / 'results.json').read_text())
    assert len(res['results']) == 18 and set(res['meta']) == {'V6', 'V24', 'XV24'} and res['n']['V6']['years']['2021']['hours'] > 1000
    assert (art / 'forecast' / 'per_token.csv').exists()
    cli.main(['report'])
    text = (study / 'TABLES.md').read_text()
    assert '| XV24 | trees_es | P2 vs P0 |' in text and 'V6 | trees_es:P2' in text


def test_pass_retries_unavailable_days_on_relaunch(tmp_path, monkeypatch):
    bad = {'2020-06-03'}
    cfg, art, study = _setup(tmp_path, monkeypatch, unavailable=bad)
    cli.main(['universe'])
    cli.main(['pass', '--end', '2020-06-04'])
    assert cli.day_status('2020-06-03') == 'unavailable'
    bad.clear()                                                                       # the outage is over
    cli.main(['pass', '--end', '2020-06-04'])
    assert cli.day_status('2020-06-03') == 'done' and not (art / 'days' / '2020-06-03.unavailable.json').exists()
    assert len(pd.read_parquet(art / 'days' / '2020-06-03.parquet')) == 72
