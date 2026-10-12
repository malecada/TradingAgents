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


def test_report_table(tmp_path):
    import json
    for arm, preds in (('full', [1, 1, 0, 1]), ('lstm', [1, 0, 0, 0])):
        d = tmp_path / 'classification' / arm / 'seed11'
        d.mkdir(parents=True)
        d.joinpath('predictions.json').write_text(json.dumps([{'decision': f'2024-01-0{k+1}', 'pred': p, 'target': t}
                                                               for k, (p, t) in enumerate(zip(preds, [1, 1, 0, 0]))]))
    text = E.report(tmp_path)
    assert '| classification | full | 1 | 0.7500' in text and '| classification | lstm | 1 | 0.7500' in text
