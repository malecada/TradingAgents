# tests/research/onchain_b6/test_cli6.py
import copy
import json

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2.s3source import DayUnavailable
from tradingagents.research.onchain_b4.reader import addr_keys
from tradingagents.research.onchain_b6 import cli, config, labels6, reader6
from tradingagents.research.onchain_b6.reader6 import Day6

A, B, X = ('0x' + c * 40 for c in 'abx')


def _day(day):
    t0 = int(pd.Timestamp(day, tz='UTC').timestamp())
    ka, kb, kx = addr_keys(np.array([A, B, X], object))
    return Day6(src=np.array([ka, kx, kb], np.uint64), dst=np.array([kx, kb, ka], np.uint64), token=np.array([1, 0, 1], np.int8),
                amount=np.array([2e6, 1.0, 3.0]), ts=np.array([t0 + 60, t0 + 7200, t0 + 9000], np.int64),
                mint=np.zeros(3, bool), burn=np.zeros(3, bool), rows={'eth_transfers': 1, 'stable_transfers': 2, 'mint': 0, 'burn': 0})


def _setup(tmp_path, monkeypatch, unavailable=()):
    art = tmp_path / 'b6'
    cfg = copy.deepcopy(config.load())
    cfg['window'] = {'first_day': '2017-01-01', 'last_day': '2017-01-05'}
    cfg['structure']['bloom_bits_log2'] = 16
    cfg['s3']['retries'] = []
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)
    monkeypatch.setattr(cli, 'filesystem', lambda: None)
    monkeypatch.setattr(cli.shutil, 'disk_usage', lambda p: type('U', (), {'free': 10**12})())
    doc = {'exchange': {X: 'okx'}, 'dex': [], 'bridge': [], 'mev': [], 'funds': [], 'issuer': {'usdt_treasury': cfg['issuer']['usdt_treasury']}}
    labels6.save(doc, art / 'labels' / 'labels6.json')

    def fake(day, **kw):
        if day in unavailable:
            raise DayUnavailable(day, ['boom'])
        return _day(day)
    monkeypatch.setattr(reader6, 'read_day6', fake)
    return art


def test_pass_writes_rows_large_and_activates(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch)
    cli.main(['pass'])
    h = pd.read_parquet(art / 'hours' / '2017-01-03.parquet')
    assert len(h) == 24 and h['tk_usdt_in'].iloc[0] == 2e6            # X active from day 2 on
    assert pd.read_parquet(art / 'hours' / '2017-01-01.parquet')['tk_usdt_in'].iloc[0] == 0.0
    assert (art / 'large' / '2017-01-03.parquet').exists() and (art / 'state' / 'state.npz').exists()
    assert not (art / 'state' / 'bloom.npy').exists()                     # one atomic bundle, not three files
    assert cli.pass_complete()


def test_resume_matches_uninterrupted(tmp_path, monkeypatch):
    art = _setup(tmp_path / 'one', monkeypatch)
    cli.main(['pass'])
    full = pd.read_parquet(art / 'hours' / '2017-01-05.parquet')
    art2 = _setup(tmp_path / 'two', monkeypatch)
    cli.main(['pass', '--end', '2017-01-02'])
    cli.main(['pass'])
    pd.testing.assert_frame_equal(full, pd.read_parquet(art2 / 'hours' / '2017-01-05.parquet'))


def test_unavailable_day_marked_and_features_refuse_incomplete(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch, unavailable=('2017-01-02',))
    cli.main(['pass', '--end', '2017-01-03'])
    assert (art / 'hours' / '2017-01-02.unavailable.json').exists()
    with pytest.raises(SystemExit, match='pass incomplete'):
        cli.main(['features'])
