"""Independent, synthetic arithmetic and clock counterexamples; no empirical I/O."""
from copy import deepcopy
import importlib
import math

import pytest


def checker():
    name = 'tradingagents.research.onchain_replication.verification'
    assert importlib.util.find_spec(name) is not None, 'independent checker is missing'
    return importlib.import_module(name)


def test_classification_has_hand_counted_denominators_and_tie_rule():
    got = checker().independent_classification([1, 1, 1, 0, 0], [.9, .7, .5, .8, .2])
    expected = {
        'TP': 2, 'TN': 1, 'FP': 1, 'FN': 1, 'N': 5,
        'accuracy': 3/5, 'precision_up': 2/3, 'recall_up': 2/3, 'f1_up': 2/3,
        'precision_macro': 7/12, 'recall_macro': 7/12, 'f1_macro': 7/12,
        'precision_weighted': 3/5, 'recall_weighted': 3/5, 'f1_weighted': 3/5,
        'balanced_accuracy': 7/12, 'brier': .206,
        'log_loss': -(math.log(.9)+math.log(.7)+math.log(.5)+math.log(.2)+math.log(.8))/5,
    }
    assert got == pytest.approx(expected, abs=1e-14)


def test_single_class_and_clipped_probability_conventions_are_explicit():
    got = checker().independent_classification([0, 0], [0., .5])
    assert got['TN'] == 2 and got['TP'] == 0
    assert got['precision_up'] == got['recall_up'] == got['f1_up'] == 0
    assert got['balanced_accuracy'] == .5
    assert math.isfinite(checker().independent_classification([0, 1], [1., 0.])['log_loss'])


@pytest.mark.parametrize('labels,probabilities', [([], []), ([1], [float('nan')]),
    ([2], [.1]), ([1], [1.1]), ([1], [[.1, .9]]), ([1, 0], [.5]), ([1], ['.9'])])
def test_bad_classification_populations_are_rejected(labels, probabilities):
    with pytest.raises(ValueError): checker().independent_classification(labels, probabilities)


def test_regression_uses_original_price_units_and_percentage_mape():
    assert checker().independent_regression([2, 4, 8], [3, 2, 10]) == pytest.approx({
        'MAE': 5/3, 'MSE': 3., 'RMSE': math.sqrt(3), 'MAPE_percent': 125/3})


@pytest.mark.parametrize('actual,predicted', [([0], [1]), ([-1], [1]),
    ([1], [float('inf')]), ([1], [[1]]), ([], [])])
def test_invalid_regression_denominators_are_rejected(actual, predicted):
    with pytest.raises(ValueError): checker().independent_regression(actual, predicted)


def test_summary_comparison_enforces_c13_and_exact_counts():
    verify = checker().compare_summary
    assert verify({'MAE': 2+1e-9}, {'MAE': 2.})['passed']
    for stated, reference in [({'MAE': 2.001}, {'MAE': 2.}), ({}, {'MAE': 2.}),
                              ({'MAE': float('nan')}, {'MAE': 2.}), ({'N': 1000000001}, {'N': 1000000000})]:
        with pytest.raises(ValueError): verify(stated, reference)
    with pytest.raises(ValueError): verify({'MAE': 2.001}, {'MAE': 2.}, rtol=.1)


def row(day=1):
    return {'lane': 'paper_reconstruction', 'asset': 'ETH', 'arm': 'proposed',
        'fold_id': '2024', 'seed': 11, 'decision_at': f'2024-01-{day:02d}T00:00:00Z',
        'label_start': f'2024-01-{day:02d}T00:00:00Z',
        'label_end': f'2024-01-{day+1:02d}T00:00:00Z',
        'max_input_available_at': f'2024-01-{day:02d}T00:00:00Z',
        'y_true': 1., 'probability_up': .7, 'predicted_price': None,
        'checkpoint_hash': 'a'*64}


def membership():
    return dict(required_decisions=['2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z'],
        test_start='2024-01-01T00:00:00Z', test_end='2024-01-03T00:00:00Z',
        expected_lane='paper_reconstruction', expected_asset='ETH', expected_arm='proposed',
        expected_fold_id='2024', expected_seed=11, task='classification')


def test_prediction_rows_bind_complete_clocks_and_exact_membership():
    validate = checker().validate_predictions
    report = validate([row(2), row(1)], **membership())
    assert report['count'] == 2 and report['checkpoint_hash'] == 'a'*64
    assert report['identity'] == validate([row(1), row(2)], **membership())['identity']
    rows = [row(1), row(2)]
    for r in rows: r.update(y_true=10., probability_up=None, predicted_price=9.)
    assert validate(rows, **{**membership(), 'task': 'regression'})['count'] == 2


@pytest.mark.parametrize('field,value', [('max_input_available_at', '2024-01-01T00:00:01Z'),
    ('max_input_available_at', '2024-01-01T00:00:00.0000001Z'),
    ('decision_at', '2024-01-01T00:00:00'), ('label_start', '2023-12-31T00:00:00Z'),
    ('label_end', '2024-01-04T00:00:00Z'), ('checkpoint_hash', 'bad'),
    ('probability_up', [.2, .8]), ('probability_up', float('nan')), ('probability_up', 1.01),
    ('predicted_price', 2.), ('y_true', 2), ('seed', 23), ('asset', 'BTC'),
    ('arm', 'gru'), ('lane', 'causal_audit'), ('fold_id', '2023')])
def test_prediction_lineage_counterexamples_fail(field, value):
    rows = [row(1), row(2)]; rows[0][field] = value
    with pytest.raises(ValueError): checker().validate_predictions(rows, **membership())


def test_prediction_denominator_cannot_drop_duplicate_or_add_fields():
    verify = checker().validate_predictions
    for rows in [[], [row()], [row(), row()], [row(), row(2), row(3)]]:
        with pytest.raises(ValueError): verify(rows, **membership())
    for change in ['missing', 'extra', 'mixed_checkpoint']:
        rows = [row(), row(2)]
        if change == 'missing': del rows[0]['label_end']
        elif change == 'extra': rows[0]['secret_override'] = True
        else: rows[1]['checkpoint_hash'] = 'b'*64
        with pytest.raises(ValueError): verify(rows, **membership())
    with pytest.raises(ValueError): verify([row(), row(2)], **{**membership(), 'required_decisions': [row()['decision_at']]*2})


def records():
    return {f'C{i:02d}': {'status': 'passed', 'scope': 'full_paper', 'evidence': [f'evidence-{i}.json']}
            for i in range(1, 19)}


def completion_kwargs():
    return dict(scope='full_paper', implementation_ids={'C01', 'C02', 'C05', 'C08'},
        paper_scope_ids=set(records()), numerical_agreement={'status': 'different',
        'scope': 'full_paper', 'evidence': ['comparison.json'], 'reason': 'accuracy differs'})


def test_completion_keeps_numerical_agreement_separate_from_work():
    result = checker().completion_status(records(), **completion_kwargs())
    assert result['implementation_complete'] and result['paper_scope_complete']
    assert result['numerical_agreement'] is False
    kwargs = completion_kwargs(); kwargs['numerical_agreement']['status'] = 'matched'
    kwargs['numerical_agreement']['reason'] = 'within the registered comparison tolerance'
    assert checker().completion_status(records(), **kwargs)['numerical_agreement'] is True


def test_blockers_and_scope_cannot_be_hidden_by_complete_cell_counts():
    entries = records(); entries['C17'] = {'status': 'blocked', 'scope': 'full_paper',
        'evidence': ['source-audit.json'], 'reason': 'fund cohort unavailable'}
    result = checker().completion_status(entries, **completion_kwargs())
    assert result['implementation_complete'] and not result['paper_scope_complete']
    assert result['unresolved']['paper_scope'] == ['C17']
    entries = records(); entries['C02']['scope'] = 'initial_eth'
    assert not checker().completion_status(entries, **completion_kwargs())['implementation_complete']
    kwargs = completion_kwargs(); kwargs['scope'] = 'initial_eth'
    entries = records()
    for item in entries.values(): item['scope'] = 'initial_eth'
    assert not checker().completion_status(entries, **kwargs)['paper_scope_complete']


@pytest.mark.parametrize('change', ['missing', 'extra', 'unknown_status', 'no_evidence', 'no_reason', 'narrow_paper', 'empty_implementation'])
def test_completion_requires_complete_explicit_evidence_contract(change):
    entries = records(); kwargs = completion_kwargs()
    if change == 'missing': del entries['C18']
    elif change == 'extra': entries['C19'] = deepcopy(entries['C18'])
    elif change == 'unknown_status': entries['C18']['status'] = 'done'
    elif change == 'no_evidence': entries['C18']['evidence'] = []
    elif change == 'no_reason': entries['C18']['status'] = 'unavailable'
    elif change == 'narrow_paper': kwargs['paper_scope_ids'] = {'C08'}
    else: kwargs['implementation_ids'] = set()
    with pytest.raises(ValueError): checker().completion_status(entries, **kwargs)
