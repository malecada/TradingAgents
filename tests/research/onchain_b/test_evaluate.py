import numpy as np

from tradingagents.research.onchain_b import evaluate as E


def test_direction_metrics():
    m = E.direction_metrics([1, 1, 0, 0, 1], [1, 0, 0, 1, 1])
    assert m['accuracy'] == 0.6 and abs(m['precision'] - 2 / 3) < 1e-12 and abs(m['recall'] - 2 / 3) < 1e-12
    assert m['n'] == 5 and m['majority_rate'] == 0.6


def test_regression_metrics():
    m = E.regression_metrics([1.0, 2.0], [2.0, 2.0])
    assert m['mae'] == 0.5 and m['rmse'] == 0.5 ** 0.5 and abs(m['mape'] - 25.0) < 1e-12


def test_bootstrap_deterministic_and_contains_mean():
    x = np.random.default_rng(0).random(365) < 0.55
    lo, hi = E.block_bootstrap(x)
    lo2, hi2 = E.block_bootstrap(x)
    assert (lo, hi) == (lo2, hi2) and lo <= x.mean() <= hi and 0.4 < lo < hi < 0.7


def test_paired_bootstrap_zero_for_identical():
    x = np.random.default_rng(1).random(100) < 0.5
    lo, hi = E.paired_block_bootstrap(x, x)
    assert lo == 0.0 == hi


def test_bootstrap_is_circular_and_unbiased_at_the_edges():
    # non-circular blocks under-weight the first/last 13 days; circular blocks weight every day equally
    x = np.zeros(365)
    x[:13] = 1
    x[-13:] = 1
    assert abs(E._bootstrap_means(x).mean() - x.mean()) < 0.005


def test_bootstrap_refuses_series_shorter_than_block():
    import pytest
    with pytest.raises(ValueError, match='block'):
        E.block_bootstrap(np.ones(10))


def _cell(root, task, arm, seed, preds, targets, epochs=100):
    import json
    d = root / task / arm / f'seed{seed}'
    d.mkdir(parents=True)
    d.joinpath('result.json').write_text(json.dumps({'arm': arm.split('-')[0], 'epochs_done': epochs}))
    d.joinpath('predictions.json').write_text(json.dumps(
        [{'decision': f'2024-01-{k + 1:02d}', 'pred': p, 'target': t} for k, (p, t) in enumerate(zip(preds, targets))]))


def test_report_computes_registered_gates_and_excludes_incomplete_cells(tmp_path):
    targets = [1, 0] * 14                                    # 28 days, majority rate 0.5
    full = [1 - t if k < 7 else t for k, t in enumerate(targets)]   # 21/28 = 0.75
    _cell(tmp_path, 'classification', 'full', 11, full, targets)
    _cell(tmp_path, 'classification', 'full', 23, targets, targets, epochs=1)      # smoke-length cell: excluded
    _cell(tmp_path, 'classification', 'lstm', 11, [1] * 28, targets)               # 0.5
    _cell(tmp_path, 'classification', 'full-label_permutation', 11, [0] * 28, targets)
    _cell(tmp_path, 'regression', 'lstm', 11, [101.0] * 28, [100.0] * 28)
    text = E.report(tmp_path, expected_epochs=100)
    assert '| classification | full | 1 | 0.7500' in text                        # seed 23 not averaged in
    assert 'classification/full/seed23' in text and 'epochs_done=1' in text         # listed as excluded
    assert 'Primary endpoint' in text and '-5.4 pp' in text and 'not numerically close' in text
    assert 'Chance control' in text and 'full-label_permutation' in text and 'within' in text
    assert '| regression | lstm | 1 | 1.0000 | 1.0000 | 1.0000 |' in text           # MAE | RMSE | MAPE %
    assert 'precision' in text.lower() and 'f1' in text.lower()
