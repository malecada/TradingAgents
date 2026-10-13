import json
import subprocess

import numpy as np
import pandas as pd
import pytest

from tradingagents.research.onchain_b2 import config, holdout as H


def _git(repo, *args):
    subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)


def test_committed_selection_guard(tmp_path):
    _git(tmp_path, 'init', '-q')
    _git(tmp_path, 'config', 'user.email', 't@t')
    _git(tmp_path, 'config', 'user.name', 't')
    sel = tmp_path / 'selection.json'
    sel.write_text(json.dumps({'selected': []}))
    with pytest.raises(PermissionError, match='not committed'):
        H.committed_selection(sel, tmp_path)
    _git(tmp_path, 'add', 'selection.json')
    _git(tmp_path, 'commit', '-qm', 'sel')
    assert H.committed_selection(sel, tmp_path) == {'selected': []}
    sel.write_text(json.dumps({'selected': [1]}))
    with pytest.raises(PermissionError, match='uncommitted'):
        H.committed_selection(sel, tmp_path)


def test_holm():
    assert np.allclose(H.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


def test_evaluate_detects_signal_once():
    rng = np.random.default_rng(3)
    def frame(start, end):
        idx = pd.date_range(start, end, freq='7D')
        sig = rng.normal(size=len(idx))
        return pd.DataFrame({'f0_a__x': rng.normal(size=len(idx)), 'f1_sig__z8': sig,
                             'T3': 2 * sig + 0.3 * rng.normal(size=len(idx))}, index=idx)
    dev, hold = {'weekly': frame('2017-10-02', '2024-12-23')}, {'weekly': frame('2025-01-06', '2026-10-05')}
    sel = {'selected': [{'target': 'T3', 'family': 'linear', 'set': 'S1', 'comparator': 'S0'}]}
    res = H.evaluate(dev, hold, sel, config.load())
    assert res[0]['n'] == 92 and res[0]['mean_diff'] < 0 and res[0]['passed'] and res[0]['p_holm'] < 0.05

def test_selection_identity_records_head_and_blob(tmp_path):
    _git(tmp_path, 'init', '-q')
    _git(tmp_path, 'config', 'user.email', 't@t')
    _git(tmp_path, 'config', 'user.name', 't')
    sel = tmp_path / 'selection.json'
    sel.write_text('{"selected": []}')
    _git(tmp_path, 'add', 'selection.json')
    _git(tmp_path, 'commit', '-qm', 'sel')
    ident = H.selection_identity(sel, tmp_path)
    head = subprocess.run(['git', '-C', str(tmp_path), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    assert ident['head'] == head and len(ident['blob']) == 40
