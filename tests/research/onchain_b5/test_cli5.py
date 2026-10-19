# tests/research/onchain_b5/test_cli5.py
import copy
import json

import pandas as pd
import pytest

from tradingagents.research.onchain_b5 import cli, config, deribit


def _setup(tmp_path, monkeypatch, fail=()):
    cfg = copy.deepcopy(config.load())
    cfg['window'] = {'start': '2023-06-01', 'end': '2023-06-03'}
    cfg['deribit']['retries'] = []
    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path / 'b5')
    monkeypatch.setattr(cli.config, 'load', lambda: cfg)

    def fake(get, currency, day, c, sleep=None):
        if day in fail:
            raise OSError('net')
        return pd.DataFrame([{'timestamp': 1, 'trade_id': f'{currency}-{day}', 'instrument_name': 'ETH-2JUN23-1900-C',
                              'iv': 50.0, 'price': 0.01, 'index_price': 1900.0, 'amount': 1.0, 'direction': 'buy'}])
    monkeypatch.setattr(deribit, 'fetch_day', fake)
    return tmp_path / 'b5'


def test_fetch_options_writes_resumes_and_marks(tmp_path, monkeypatch):
    art = _setup(tmp_path, monkeypatch, fail=('2023-06-02',))
    cli.main(['fetch-options', '--asset', 'ETH'])
    assert (art / 'options' / 'ETH' / '2023-06-01.parquet').exists()
    assert json.loads((art / 'options' / 'ETH' / '2023-06-02.unavailable.json').read_text())['day'] == '2023-06-02'
    assert cli.options_complete('ETH')                 # a marked day counts as complete
    _setup(tmp_path, monkeypatch)
    cli.main(['fetch-options', '--asset', 'ETH'])
    assert (art / 'options' / 'ETH' / '2023-06-02.parquet').exists()
    assert not (art / 'options' / 'ETH' / '2023-06-02.unavailable.json').exists()
    assert cli.options_complete('ETH')


def test_decisions_refuse_incomplete_options(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match='options incomplete'):
        cli.main(['decisions'])


def test_trades_loader_prepares_and_skips_missing(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    cli.main(['fetch-options', '--asset', 'ETH'])
    load = cli.trades_loader('ETH')
    df = load('2023-06-01')
    assert 'expiry' in df.columns and df['expiry'].iloc[0] == pd.Timestamp('2023-06-02 08:00')
    assert load('2023-07-01') is None
