# tests/research/onchain_b7/test_cli7.py
import copy
import json

import numpy as np
import pandas as pd

from tradingagents.research.onchain_b7 import cli, config

T0, T1 = '2020-06-01', '2021-12-31'


def _inputs(tmp_path, monkeypatch):
    rng = np.random.default_rng(12)
    cfg = copy.deepcopy(config.load())
    cfg['tracks'] = {'A': {**cfg['tracks']['A'], 'start': '2020-10-01', 'end': T1, 'test_years': [2021], 'groups': {'2021': [2021]}, 'min_year_wins': 1},
                     'B': {**cfg['tracks']['B'], 'start': '2020-10-01', 'end': T1, 'test_years': [2021], 'groups': {'2021a': [2021], '2021b': [2021]}}}
    cfg['targets'] = {'V6': cfg['targets']['V6'], 'J6': cfg['targets']['J6'], 'M6': cfg['targets']['M6']}
    cfg['folds'] = {'inner_len': 300, 'min_train': 100}
    cfg['models']['trees_es'].update({'max_iter': 20, 'min_iter': 5})
    cfg['gate'].update({'draws': 100, 'block': 24})
    b4, b6, art = tmp_path / 'b4', tmp_path / 'b6', tmp_path / 'b7'
    idx = pd.date_range(T0, pd.Timestamp(T1) + pd.Timedelta(hours=23), freq='h')
    n = len(idx)
    raw4 = pd.DataFrame({s: rng.gamma(2, 5, n) for s in cfg['series']['b4']}, index=idx)
    raw6 = pd.DataFrame({s: rng.gamma(2, 5, n) for s in cfg['series']['b6']}, index=idx)
    flows = pd.DataFrame({c: rng.normal(size=n) for c in ('eth_in_val__h1z', 'stable_in_val__d24z', 'act_tx_count__h1z', 'lab_eth_in_val__h1z', 'eth_net24__z')}, index=idx)
    (b4 / 'features').mkdir(parents=True)
    (b6 / 'features').mkdir(parents=True)
    raw4.to_parquet(b4 / 'features' / 'hourly_raw.parquet')
    raw6.to_parquet(b6 / 'features' / 'hourly_raw.parquet')
    flows.to_parquet(b4 / 'features' / 'hourly.parquet')
    pd.DataFrame({'mk_dvol': rng.normal(size=n), 'mk_dvol_chg24': rng.normal(size=n), 'mk_iv': rng.normal(size=n), 'other': 1.0}, index=idx).to_parquet(b6 / 'features' / 'features_B.parquet')
    close = 1000 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    bars = {t.strftime('%Y-%m-%dT%H'): [float(c), float(rng.gamma(2, 1e6))] for t, c in zip(idx, close)}
    (b4 / 'market').mkdir()
    (b4 / 'sealed').mkdir()
    (b4 / 'market' / 'hourly_dev.json').write_text(json.dumps({k: v for k, v in bars.items() if k < '2021-10-01T00'}))
    (b4 / 'sealed' / 'hourly_sealed.json').write_text(json.dumps({k: v for k, v in bars.items() if k >= '2021-10-01T00'}))
    midx = pd.date_range(T0, pd.Timestamp(T1) + pd.Timedelta(hours=23, minutes=59), freq='min')
    minutes = pd.Series(np.repeat(close, 60) * np.exp(rng.normal(0, 1e-4, len(midx))), index=midx, name='close')
    (b6 / 'market').mkdir()
    minutes.to_frame().to_parquet(b6 / 'market' / 'minutes_ETH.parquet')
    (b6 / 'large').mkdir()
    ts = [int(pd.Timestamp(t, tz='UTC').timestamp()) for t in ('2020-07-01 10:00', '2021-03-03 03:03', '2021-08-08 08:08')]
    pd.DataFrame({'ts': ts, 'token': [1, 2, 1], 'amount': [2e7, 6e7, 3e7], 'direction': [1, 1, 1], 'entity': 0, 'cp_new': False, 'cp': 0}).to_parquet(b6 / 'large' / '2021-01-01.parquet')
    monkeypatch.setattr(cli, 'B4', b4)
    monkeypatch.setattr(cli, 'B6', b6)
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli, 'STUDY', tmp_path / 'study')
    (tmp_path / 'study').mkdir()
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)
    return cfg, art


def test_features_stage_writes_table_and_targets(tmp_path, monkeypatch):
    cfg, art = _inputs(tmp_path, monkeypatch)
    cli.main(['features'])
    t = pd.read_parquet(art / 'features' / 'table.parquet')
    y = pd.read_parquet(art / 'features' / 'targets.parquet')
    assert len(t) == len(y) == 24 * 579 and list(y.columns) == ['V6', 'V24', 'J6', 'J24', 'M6', 'M24']
    n_cols = [c for c in t.columns if c.startswith('n_')]
    assert len(n_cols) == 54 * 6 and {'ev_since_10m', 'ev_since_50m', 'ix_stable_val_rv6', 'rg_range1', 'rg_range24', 'mk_iv', 'h0_rv24', 'px_rv6', 'eth_net24__z'} <= set(t.columns)
    assert 'lab_eth_in_val__h1z' not in t.columns and 'other' not in t.columns
    assert np.isclose(t['ix_stable_val_rv6'], t['n_stable_in_val__ex1'] * t['px_rv6'], equal_nan=True).all()
    assert t.loc['2021-06-01':, n_cols].notna().all().all() and y['M6'].loc['2021-06-01':'2021-12-30'].notna().all()


def test_forecast_stage_resumes_per_unit(tmp_path, monkeypatch):
    cfg, art = _inputs(tmp_path, monkeypatch)
    cli.main(['features'])
    cli.main(['forecast', '--only', 'A:V6'])
    first = art / 'forecast' / 'A_V6.json'
    assert first.exists() and (art / 'forecast' / 'pred_A_V6.parquet').exists()
    doc = json.loads(first.read_text())
    assert len(doc['results']) == 11 and all(r['n'] > 0 for r in doc['results'])
    stamp = first.stat().st_mtime_ns
    cli.main(['forecast'])
    assert first.stat().st_mtime_ns == stamp                                        # finished unit untouched
    res = json.loads((art / 'forecast' / 'results.json').read_text())
    assert len(res['results']) == 3 * 11 + 3 * 22 and set(res['meta']) == {'A_V6', 'A_J6', 'A_M6', 'B_V6', 'B_J6', 'B_M6'}
    assert res['n']['A']['J6']['mean'] < 0.2 and res['n']['B']['V6']['n'] > 1000
    cli.main(['report'])
    text = (tmp_path / 'study' / 'TABLES.md').read_text()
    assert '| B | M6 | trees_es|trees_fixed | Y2 vs Y2 | 2021b |' in text and 'A_V6 | trees_es:Y2' in text
