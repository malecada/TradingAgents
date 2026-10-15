# tests/research/onchain_b4/test_cli4.py
import copy
import json
import subprocess

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2.s3source import DayUnavailable
from tradingagents.research.onchain_b4 import cli, config, reader
from tradingagents.research.onchain_b4.reader import Day

A, B, E = ('0x' + c * 40 for c in 'abe')


def _day(day):
    t0 = int(pd.Timestamp(day).timestamp())
    k = reader.addr_keys(np.array([A, B, E], object))
    seed = int(pd.Timestamp(day).dayofyear)
    src = np.array([k[0], k[1], k[0]], np.uint64)
    dst = np.array([k[2], k[0], k[1]], np.uint64)
    return Day(src=src, dst=dst, asset=np.array([0, 1, 0], np.int8), amount=np.array([1.0 + seed, 2e6, 3.0]),
               ts=np.array([t0 + 60, t0 + 7200, t0 + 9000], np.int64), block=np.array([1, 2, 3], np.int64),
               tx_ts=np.array([t0 + 60], np.int64), tx_gwei=np.array([5.0]), blk_ts=np.array([t0 + 60], np.int64),
               blk_gas=np.array([1.0]), blk_txs=np.array([1.0]))


def _setup(tmp_path, monkeypatch, unavailable=()):
    art, b2 = tmp_path / 'b4', tmp_path / 'b2'
    (b2 / 'labels').mkdir(parents=True)
    (b2 / 'labels' / 'labels.json').write_text(json.dumps({E: {'name': 'X'}}))
    cfg = copy.deepcopy(config.load())
    cfg['entities']['bloom_bits_log2'] = 16
    cfg['s3']['retries'] = []
    monkeypatch.setattr(cli, 'ARTIFACTS', art)
    monkeypatch.setattr(cli, 'B2', b2)
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)
    monkeypatch.setattr(cli, 'filesystem', lambda: None)

    def fake(day, **kw):
        if day in unavailable:
            raise DayUnavailable(day, ['boom'])
        return _day(day)
    monkeypatch.setattr(reader, 'read_day', fake)
    return art


def test_pass_writes_hours_and_snapshot(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch)
    cli.main(['pass', '--end', '2017-01-03'])
    assert all((art / 'hours' / f'2017-01-0{d}.parquet').exists() for d in (1, 2, 3))
    h = pd.read_parquet(art / 'hours' / '2017-01-02.parquet')
    assert len(h) == 24 and h['eth_in_val'].iloc[0] == 3.0
    z = np.load(art / 'state' / 'entities.npz')
    assert str(z['last_day'][0]) == '2017-01-03'


def test_resume_matches_uninterrupted(tmp_path, monkeypatch):
    art = _setup(tmp_path / 'one', monkeypatch)
    cli.main(['pass', '--end', '2017-01-04'])
    full = {d: pd.read_parquet(art / 'hours' / f'2017-01-0{d}.parquet') for d in (3, 4)}
    art2 = _setup(tmp_path / 'two', monkeypatch)
    cli.main(['pass', '--end', '2017-01-02'])
    cli.main(['pass', '--end', '2017-01-04'])
    for d in (3, 4):
        pd.testing.assert_frame_equal(full[d], pd.read_parquet(art2 / 'hours' / f'2017-01-0{d}.parquet'))
    a, b = np.load(art / 'state' / 'entities.npz'), np.load(art2 / 'state' / 'entities.npz')
    assert np.array_equal(a['c_keys'], b['c_keys']) and np.array_equal(a['bits'], b['bits'])


def test_unavailable_day_is_marked_and_pass_continues(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch, unavailable=('2017-01-02',))
    cli.main(['pass', '--end', '2017-01-03'])
    assert (art / 'hours' / '2017-01-02.unavailable.json').exists() and (art / 'hours' / '2017-01-03.parquet').exists()


def test_consecutive_unavailable_stops(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, unavailable=('2017-01-01', '2017-01-02', '2017-01-03', '2017-01-04'))
    with pytest.raises(SystemExit, match='consecutive'):
        cli.main(['pass', '--end', '2017-01-05'])


def test_features_refuse_incomplete_pass(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    cli.main(['pass', '--end', '2017-01-02'])
    with pytest.raises(SystemExit, match='pass incomplete'):
        cli.main(['features'])


def test_screen_never_overwrites_selection(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(cli, 'STUDY', tmp_path)
    (tmp_path / 'selection.json').write_text('{"selected": []}')
    with pytest.raises(SystemExit, match='exists'):
        cli.main(['screen'])


def test_holdout_refuses_empty_committed_selection(tmp_path, monkeypatch, capsys):
    art = _setup(tmp_path, monkeypatch)
    repo = tmp_path / 'repo'
    repo.mkdir()
    git = lambda *a: subprocess.run(['git', '-C', str(repo), *a], check=True, capture_output=True)
    git('init', '-q')
    (repo / 'selection.json').write_text('{"selected": []}')
    git('add', 'selection.json')
    git('-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qm', 's')
    monkeypatch.setattr(cli, 'STUDY', repo)
    monkeypatch.setattr(cli, 'ROOT', repo)
    cli.main(['holdout'])
    assert 'holdout not opened' in capsys.readouterr().out and not (art / 'screen' / 'holdout.lock.json').exists()
