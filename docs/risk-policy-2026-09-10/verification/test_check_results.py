import importlib.util
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location('independent_risk_checker', Path(__file__).with_name('check_results.py'))
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_independent_sigma_uses_only_previous_close():
    prices = 100 * np.exp(np.sin(np.arange(50) / 5) / 10)
    first = checker.sigma_reference(prices)
    prices[35:] *= 1.8
    second = checker.sigma_reference(prices)
    np.testing.assert_equal(first[:36], second[:36])
    assert np.isnan(first[:20]).all() and np.isfinite(first[20:]).all()


def test_control_check_detects_flag_and_weight_changes():
    original = pd.DataFrame({'date': ['2026-01-01'], 'exposure': [0.5], 'halted_after': [False]})
    checker.check_control(original.copy(), original)
    for col, value in [('exposure', .5001), ('halted_after', True)]:
        altered = original.copy()
        altered[col] = value
        with pytest.raises(AssertionError):
            checker.check_control(altered, original)


def test_independent_accounting_checker_rejects_corruption():
    # Deterministic fabricated path only: no repository market input or saved outcome.
    from scripts.baseline_strategy_v2 import run_coin_backtest
    from tradingagents.strategies.factor_risk_policy import FactorRiskPolicy, causal_sigma
    prices = 100 * np.exp(.03 * np.sin(np.arange(1241) / 7))
    clock = pd.date_range('2021-11-07', periods=1241)
    raw = np.where(np.arange(1241) < 20, 0., .3)
    targets = pd.DataFrame(dict(Date=clock, Close=prices, Open=prices,
        High=prices * 1.001, Low=prices * .999, target=raw))
    costs = dict(fee_rate=.0004, slippage=.0005, spread=.0001,
        price_impact=.00005, funding_rate=.0003, stop_loss=1.,
        max_portfolio_dd=.15, take_profit=0.)
    trace = []
    run_coin_backtest(clock, prices, raw, 10000., **costs, highs=targets.High.to_numpy(),
        lows=targets.Low.to_numpy(), price_stop_pct=.03, trace=trace,
        target_policy=FactorRiskPolicy(sizing='daily', reentry='new_target_episode', sigma=causal_sigma(prices)))
    frame = pd.DataFrame(trace)
    checker.check_trace(frame, targets, 'A11', costs)
    changed = frame.copy()
    changed.loc[30, 'funding_dollars'] += 1.
    with pytest.raises(AssertionError, match='funding_dollars'):
        checker.check_trace(changed, targets, 'A11', costs)


@pytest.fixture(scope='module')
def stopped_books():
    """One known price stop, same-sign wait, opposite release and flat reset."""
    from scripts.baseline_strategy_v2 import run_coin_backtest
    from tradingagents.strategies.factor_risk_policy import FactorRiskPolicy, causal_sigma
    prices = np.full(1241, 100.)
    clock = pd.date_range('2021-11-07', periods=1241)
    raw = np.r_[np.zeros(20), np.ones(1221)]
    raw[22], raw[23], raw[24] = 2., -1., 0.
    lows = prices.copy()
    lows[20] = 95.
    targets = pd.DataFrame(dict(Date=clock, Open=prices, High=prices, Low=lows,
                                Close=prices, target=raw))
    costs = dict(fee_rate=0., slippage=0., spread=0., price_impact=0.,
                 funding_rate=0., stop_loss=1., max_portfolio_dd=.15, take_profit=0.)
    books = {}
    for arm, policy in [('A00', 'immediate'), ('A01', 'new_target_episode')]:
        trace = []
        run_coin_backtest(clock, prices, raw, 10000., **costs, highs=prices,
            lows=lows, price_stop_pct=.03, trace=trace,
            target_policy=FactorRiskPolicy(sizing='saved', reentry=policy,
                                           sigma=causal_sigma(prices)))
        books[arm] = pd.DataFrame(trace)
        checker.check_trace(books[arm], targets, arm, costs)
    assert books['A01'].loc[19, 'exit_executed']
    assert books['A01'].loc[20, 'decision_blocked']
    assert books['A01'].loc[22, 'block_release'] == 'raw_opposite'
    return books, targets, costs


def test_required_stop_exit_cannot_be_removed_with_balanced_zero_cost_cashflows(stopped_books):
    books, targets, costs = stopped_books
    altered = books['A00'].copy()
    # A fabricated no-exit book can retain exactly the same NAV when costs are
    # zero. Its marked holdings and next opening turnover still balance.
    altered.loc[19, 'exit_executed'] = False
    altered.loc[19, 'closing_notional'] = 9700.
    altered.loc[19, ['exit_notional', 'exit_turnover_dollars']] = 0.
    altered.loc[19, 'turnover_dollars'] = 10000.
    altered.loc[20, ['entry_turnover_dollars', 'turnover_dollars']] = 0.
    with pytest.raises(AssertionError, match='required executed exit'):
        checker.check_trace(altered, targets, 'A00', costs)


def test_immediate_book_cannot_be_relabelled_as_waiting_policy(stopped_books):
    books, targets, costs = stopped_books
    with pytest.raises(AssertionError, match='reentry identity'):
        checker.check_trace(books['A00'], targets, 'A01', costs)


@pytest.mark.parametrize('row,field,value,label', [
    (20, 'raw_target', 999., 'policy raw target'),
    (20, 'requested_target', 1., 'policy requested target'),
    (20, 'sizing_sigma', 999., 'policy sigma'),
    (20, 'blocked_before', 0, 'policy decision latch'),
    (22, 'blocked_after_decision', 1, 'policy decision latch'),
    (20, 'decision_blocked', False, 'policy release/wait metadata'),
    (22, 'block_release', 'raw_flat', 'policy release/wait metadata'),
    (20, 'decision_reason', 'saved_target', 'policy decision reason'),
    (20, 'policy_sizing', 'daily', 'sizing identity'),
    (20, 'policy_reentry', 'immediate', 'reentry identity'),
    (19, 'blocked_after', 0, 'policy end-of-bar latch'),
    (19, 'stopped_direction', 0, 'executed stopped direction'),
])
def test_checker_independently_reconstructs_each_policy_field(stopped_books, row, field, value, label):
    books, targets, costs = stopped_books
    altered = books['A01'].copy()
    altered.loc[row, field] = value
    with pytest.raises(AssertionError, match=label):
        checker.check_trace(altered, targets, 'A01', costs)


def test_exit_cost_halt_precedes_opposite_target_release():
    from scripts.baseline_strategy_v2 import run_coin_backtest
    from tradingagents.strategies.factor_risk_policy import FactorRiskPolicy, causal_sigma
    prices = np.r_[np.full(20, 100.), np.full(1221, 97.)]
    raw = np.r_[np.zeros(20), 3., np.full(1220, -3.)]
    clock = pd.date_range('2021-11-07', periods=1241)
    targets = pd.DataFrame(dict(Date=clock, Open=prices, High=prices, Low=prices,
                                Close=prices, target=raw))
    costs = dict(fee_rate=.0102, slippage=0., spread=0., price_impact=0.,
                 funding_rate=0., stop_loss=1., max_portfolio_dd=.15, take_profit=0.)
    trace = []
    run_coin_backtest(clock, prices, raw, 10000., **costs, highs=prices, lows=prices,
        price_stop_pct=.03, trace=trace,
        target_policy=FactorRiskPolicy(sizing='saved', reentry='new_target_episode',
                                       sigma=causal_sigma(prices)))
    frame = pd.DataFrame(trace)
    assert not frame.loc[19, 'portfolio_stop_hit'] and frame.loc[19, 'halted_after']
    assert frame.loc[20, 'raw_target'] == -3.
    assert frame.loc[20, 'decision_reason'] == 'permanent_halt'
    checker.check_trace(frame, targets, 'A01', costs)
    frame.loc[19, 'halted_after'] = False
    with pytest.raises(AssertionError, match='post-exit halt'):
        checker.check_trace(frame, targets, 'A01', costs)


def zero_metrics(n):
    return dict(n_bars=n, mean_return=0., annual_mean=0., annual_volatility=0.,
                total_return=0., max_drawdown=0., sharpe=None, sharpe_reason='zero_variance')


@pytest.fixture
def period_book():
    bounds = [('2021-11-08', '2022-12-31'), ('2023-01-01', '2024-12-31'),
              ('2025-01-01', '2025-03-31')]
    record = {'periods': [dict(start=a, end=b, metrics=zero_metrics(len(pd.date_range(a, b))))
                           for a, b in bounds]}
    frame = pd.DataFrame({'index_return': 0.}, index=pd.date_range(bounds[0][0], bounds[-1][1]))
    checker.check_periods(record, frame, 'index_return')
    return record, frame


@pytest.mark.parametrize('indices', [[], [0, 2], [0, 1, 1], [2, 1, 0]])
def test_all_three_periods_are_required_once_and_in_order(period_book, indices):
    record, frame = period_book
    record['periods'] = [record['periods'][i] for i in indices]
    with pytest.raises(AssertionError, match='three ordered periods'):
        checker.check_periods(record, frame, 'index_return')


@pytest.mark.parametrize('bad_clock', ['missing', 'duplicate', 'reordered'])
def test_period_metrics_cannot_hide_a_broken_calendar(period_book, bad_clock):
    record, frame = period_book
    if bad_clock == 'missing':
        frame = frame.drop(frame.index[5])
        record['periods'][0]['metrics'] = zero_metrics(record['periods'][0]['metrics']['n_bars'] - 1)
    elif bad_clock == 'duplicate':
        frame.index = frame.index[:5].append(frame.index[4:5]).append(frame.index[6:])
    else:
        frame = frame.iloc[np.r_[np.arange(4), 5, 4, np.arange(6, len(frame))]]
    with pytest.raises(AssertionError, match='complete period calendar'):
        checker.check_periods(record, frame, 'index_return')


@pytest.fixture
def contrast_book():
    # Four deliberately different scalars make every coefficient and direction
    # identifiable; unprovided metrics must remain null, not become zero.
    arms = ('A00', 'A10', 'A01', 'A11')
    values = (.01, .03, .05, .10)
    cells = [dict(id='synthetic|' + arm, metrics={'variants': {'primary': dict(
        status='complete', index={'metrics': {'mean_return': value}},
        sleeves={'bitcoin': {}, 'ethereum': {}})}}) for arm, value in zip(arms, values)]
    empty_fields = dict.fromkeys(checker.flatten_cell(cells[0]))
    def differences(value):
        return {**empty_fields, 'index.mean_return': value}
    result = dict(cells=cells,
        direct_contrasts=[dict(configuration='synthetic', arm=a, control='A00',
            status='complete', differences=differences(v))
            for a, v in zip(arms[1:], (.02, .04, .09))],
        factorial_contrasts=[dict(configuration='synthetic', effect=e, status='complete',
            differences=differences(v))
            for e, v in [('sizing', .035), ('waiting', .055), ('interaction', .03)]])
    gate = {'configurations': [{'name': 'synthetic'}]}
    checker.check_contrasts(result, gate)
    return result, gate


@pytest.mark.parametrize('collection', ['direct_contrasts', 'factorial_contrasts'])
@pytest.mark.parametrize('which', [0, 1, 2])
def test_each_contrast_formula_is_checked(contrast_book, collection, which):
    result, gate = contrast_book
    result[collection][which]['differences']['index.mean_return'] += .001
    with pytest.raises(AssertionError, match='contrast index.mean_return'):
        checker.check_contrasts(result, gate)


@pytest.mark.parametrize('collection', ['direct_contrasts', 'factorial_contrasts'])
def test_contrasts_require_exact_identity_order_and_full_metric_coverage(contrast_book, collection):
    result, gate = contrast_book
    changed = copy.deepcopy(result)
    changed[collection][0], changed[collection][1] = changed[collection][1], changed[collection][0]
    with pytest.raises(AssertionError, match='identities/order'):
        checker.check_contrasts(changed, gate)
    changed = copy.deepcopy(result)
    del changed[collection][0]['differences']['ethereum.closing.risk_maximum']
    with pytest.raises(AssertionError, match='contrast metric coverage'):
        checker.check_contrasts(changed, gate)


def test_undefined_contrast_does_not_become_zero(contrast_book):
    result, gate = contrast_book
    result['direct_contrasts'][0]['differences']['index.sharpe'] = 0.
    with pytest.raises(AssertionError, match='null contrast preserved'):
        checker.check_contrasts(result, gate)


def test_missing_source_marks_only_involving_contrasts_unavailable(contrast_book):
    result, gate = contrast_book
    result['cells'][1]['metrics']['variants']['primary']['status'] = 'unavailable'
    with pytest.raises(AssertionError, match='contrast availability'):
        checker.check_contrasts(result, gate)
    result['direct_contrasts'][0]['status'] = 'unavailable'
    for record in result['factorial_contrasts']:
        record['status'] = 'unavailable'
    checker.check_contrasts(result, gate)


class AdmissionReached(RuntimeError):
    pass


@pytest.fixture
def evidence_book(tmp_path, monkeypatch):
    """Minimal synthetic JSON evidence; stop before review output is written."""
    monkeypatch.setattr(checker, 'ROOT', tmp_path)
    (tmp_path / 'data/predlab').mkdir(parents=True)
    out = tmp_path / 'synthetic-output'
    out.mkdir()
    prefix = b'{"prior":"synthetic"}\n'
    cells = [dict(id=f'synthetic-{i}', configuration={'name': f'config-{i}'}, arm='A00',
                  metrics={'variants': {}, 'log_shadow': {'status': 'unavailable', 'reason': 'synthetic'}})
             for i in range(72)]
    receipt = b''.join((json.dumps({'cell': c['id'], 'metrics': c['metrics']}) + '\n').encode()
                       for c in cells)
    gate = dict(output_dir=out.name, pinned_files={}, variants=[],
        cells=[{k: c[k] for k in ('id', 'configuration', 'arm')} for c in cells],
        financial_ledger={'path': 'central.jsonl', 'prefix_bytes': len(prefix),
                          'prefix_sha256': hashlib.sha256(prefix).hexdigest()})
    result = dict(registered_gate=gate, cells=cells, output_sha256={},
                  direct_contrasts=[{}] * 54, factorial_contrasts=[{}] * 54)
    (out / 'prepared-ledger.jsonl').write_bytes(receipt)
    (tmp_path / 'central.jsonl').write_bytes(prefix + receipt)
    def save():
        result['output_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in out.iterdir() if p.name != 'result.json'}
        (tmp_path / 'data/predlab/gates.json').write_text(json.dumps({checker.KEY: gate}))
        (out / 'result.json').write_text(json.dumps(result))
    def stop_before_output(*args):
        raise AdmissionReached('synthetic evidence admitted')
    monkeypatch.setattr(checker, 'check_contrasts', stop_before_output)
    save()
    with pytest.raises(AdmissionReached):
        checker.main()
    return tmp_path, out, result, gate, save


def test_unmanifested_file_is_rejected_before_consumption(evidence_book):
    _, out, _, _, _ = evidence_book
    (out / 'unlisted-returns.parquet').write_bytes(b'synthetic unread bytes')
    with pytest.raises(AssertionError, match='every saved output is hashed'):
        checker.main()


@pytest.mark.parametrize('field,value', [('arm', 'A11'), ('configuration', {'name': 'wrong'})])
def test_matching_cell_id_cannot_hide_wrong_arm_or_configuration(evidence_book, field, value):
    _, _, result, _, save = evidence_book
    result['cells'][0][field] = value
    save()
    with pytest.raises(AssertionError, match='complete cell identity'):
        checker.main()


def test_changed_old_ledger_prefix_cannot_be_hidden_by_current_receipt(evidence_book):
    root, _, _, _, _ = evidence_book
    path = root / 'central.jsonl'
    path.write_bytes(path.read_bytes().replace(b'synthetic', b'SYNTHETIC', 1))
    with pytest.raises(AssertionError, match='central original prefix'):
        checker.main()


def test_central_ledger_must_contain_exact_prepared_receipt(evidence_book):
    root, _, _, _, _ = evidence_book
    path = root / 'central.jsonl'
    path.write_bytes(path.read_bytes() + b'{}\n')
    with pytest.raises(AssertionError, match='central ledger receipt'):
        checker.main()


@pytest.mark.parametrize('field', ['cell', 'metrics'])
def test_even_rehashed_matching_ledger_receipt_must_match_result_cells(evidence_book, field):
    root, out, _, gate, save = evidence_book
    path = out / 'prepared-ledger.jsonl'
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[0][field] = 'wrong-id' if field == 'cell' else {'status': 'manufactured'}
    receipt = b''.join((json.dumps(row) + '\n').encode() for row in rows)
    path.write_bytes(receipt)
    central = root / 'central.jsonl'
    central.write_bytes(central.read_bytes()[:gate['financial_ledger']['prefix_bytes']] + receipt)
    save()
    with pytest.raises(AssertionError, match='ledger records exact results'):
        checker.main()
