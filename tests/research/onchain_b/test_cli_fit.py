import torch

from tradingagents.research.onchain_b import cli
from tradingagents.research.onchain_b import train as T


def _capture(monkeypatch, tmp_path):
    calls = {}

    def fake_fit(arm, task, seed, out, store=None, epochs=None, diag=None):
        calls.update(arm=arm, task=task, seed=seed, out=out, store=store, epochs=epochs, diag=diag, threads=torch.get_num_threads())
        return {'arm': arm}

    monkeypatch.setattr(cli, 'ARTIFACTS', tmp_path)
    monkeypatch.setattr(T, 'fit', fake_fit)
    return calls


def test_fit_stage_uses_two_threads_and_fit_layout(tmp_path, monkeypatch):
    calls = _capture(monkeypatch, tmp_path)
    cli.main(['fit', '--arm', 'lstm', '--task', 'regression', '--seed', '23'])
    assert calls['threads'] == 2
    assert calls['out'] == tmp_path / 'fits' / 'regression' / 'lstm' / 'seed23' and calls['store'] is None
    assert calls['epochs'] is None and calls['diag'] is None


def test_non_frozen_epochs_write_to_smoke_tree(tmp_path, monkeypatch):
    # a CP3 smoke run must never occupy the one-shot fit directory of the real grid
    calls = _capture(monkeypatch, tmp_path)
    cli.main(['fit', '--arm', 'lstm', '--task', 'regression', '--seed', '23', '--epochs', '1'])
    assert calls['out'] == tmp_path / 'fits-smoke' / 'regression' / 'lstm' / 'seed23' and calls['epochs'] == 1
