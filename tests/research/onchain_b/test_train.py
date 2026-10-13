import json
from datetime import date, timedelta

import numpy as np
import torch

from tradingagents.research.onchain_b import data as Dt
from tradingagents.research.onchain_b import prices as P
from tradingagents.research.onchain_b import train as T


class FakeStore:
    def __init__(self, K=12, E=30):
        self.K, self.E = K, E
        self.calls = 0

    def tensors(self, week):
        self.calls += 1
        g = torch.Generator().manual_seed(int(week.replace('-', '')) % 2**31)
        return torch.randn(self.K, 32, generator=g), torch.randint(0, self.K, (2, self.E), generator=g)


def _px(period):
    return {date(2021, 12, 1) + timedelta(days=k): 1000.0 + (k % period) for k in range(1200)}


def test_fit_full_model_one_epoch_writes_outputs(tmp_path):
    res = T.fit('full', 'classification', 11, tmp_path, store=FakeStore(), epochs=1, prices=_px(7))
    pred = json.loads((tmp_path / 'predictions.json').read_text())
    assert len(pred) == 365 and set(pred[0]) == {'decision', 'pred', 'target'} and (tmp_path / 'checkpoint.pt').exists()
    assert res['epochs_done'] == 1 and np.isfinite(res['final_train_loss'])


def test_fit_is_deterministic(tmp_path):
    T.fit('lstm', 'regression', 23, tmp_path / 'a', epochs=1, prices=_px(5))
    T.fit('lstm', 'regression', 23, tmp_path / 'b', epochs=1, prices=_px(5))
    pa_ = json.loads((tmp_path / 'a' / 'predictions.json').read_text())
    pb = json.loads((tmp_path / 'b' / 'predictions.json').read_text())
    assert [r['pred'] for r in pa_] == [r['pred'] for r in pb]


def test_svm_arm(tmp_path):
    res = T.fit('svm', 'classification', 11, tmp_path, prices=_px(5))
    assert len(json.loads((tmp_path / 'predictions.json').read_text())) == 365 and res['arm'] == 'svm'


def test_outputs_are_replaced_atomically_with_marker_last(tmp_path, monkeypatch):
    import os
    real = os.replace
    order = []

    def recording_replace(src, dst):
        order.append(os.path.basename(str(dst)))
        return real(src, dst)

    monkeypatch.setattr(os, 'replace', recording_replace)
    T.fit('lstm', 'regression', 11, tmp_path, epochs=1, prices=_px(5))
    assert 'checkpoint.pt' in order and order[-1] == 'predictions.json'
    assert order.index('result.json') < order.index('predictions.json')
    assert not [p for p in tmp_path.iterdir() if p.name.startswith('.tmp')]


def test_label_permutation_diag_changes_targets():
    px = _px(3)
    ex = Dt.examples('train', px, P.Scaler().fit(px, [date(2022, 2, 6)]), 'classification')
    perm = T.permute_labels(ex, 20260924)
    assert [e.target for e in perm] != [e.target for e in ex]
    assert sorted(e.target for e in perm) == sorted(e.target for e in ex)
    assert [e.decision for e in perm] == [e.decision for e in ex]
