"""Synthetic PRX correction checks: never consume research return panels."""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from statsmodels.tsa.stattools import adfuller, coint


def module():
    return importlib.import_module('scripts.audit_reevaluate_prx_2026_09_09')


def panels(end='2025-03-31'):
    idx = pd.date_range('2020-10-03', end, freq='D', tz='UTC')
    rng = np.random.default_rng(904)
    b = np.cumsum(rng.normal(0, .02, len(idx))) + 4
    e = np.zeros(len(idx))
    for i in range(1, len(idx)):
        e[i] = .8 * e[i - 1] + rng.normal(0, .004)
    return (pd.DataFrame({'A': np.exp(b + e), 'B': np.exp(b)}, index=idx),
            pd.DataFrame({'A': 2., 'B': 1.}, index=idx))


def month_rows():
    return [{'month': str(d.date()), 'status': 'complete',
             'selected_rate': .3, 'random_rate': .1}
            for d in pd.date_range('2021-01-01', '2025-02-01', freq='MS', tz='UTC')]


def test_estimated_residual_uses_cointegration_null():
    rng = np.random.default_rng(11)
    a, b = np.cumsum(rng.normal(size=200)), np.cumsum(rng.normal(size=200))
    a, b = pd.Series(a), pd.Series(b)
    got = module().fit_pair(a, b)
    want = coint(a, b, trend='c', maxlag=5, autolag=None)[1]
    beta = np.polyfit(b, a, 1)[0]
    ordinary = adfuller(a - beta * b, maxlag=5, autolag=None)[1]
    assert got['p'] == pytest.approx(want)
    assert abs(got['p'] - ordinary) > .01
    assert got['n_paired'] == 200


def test_formation_is_unchanged_by_future_prices_and_volume():
    m = module()
    c, q = panels('2021-03-01')
    date = pd.Timestamp('2021-01-01', tz='UTC')
    before = m.formation_pairs(c, q, date)
    c.loc[date:, 'A'] *= 7
    q.loc[date:, 'B'] *= 1000
    assert m.formation_pairs(c, q, date) == before
    assert before['n_formation_days'] == 90
    assert before['formation_start'] == '2020-10-03'


def test_missing_selected_spread_is_explicit_not_a_rejection():
    m = module()
    idx = pd.date_range('2021-01-01', periods=31, tz='UTC')
    a = pd.Series(np.arange(31, dtype=float), index=idx)
    b = a.copy()
    a.iloc[:10] = np.nan
    got = m.score_spread(a, b, beta=.5)
    assert got['stationary'] is None
    assert got['n_observed'] == 21
    assert got['reason'] == 'fewer_than_25_observations'


def test_every_original_month_survives_empty_inputs():
    m = module()
    c, q = panels()
    q[:] = np.nan
    got = m.evaluate_p0(c, q)
    assert len(got['months']) == 50
    assert got['months'][0]['month'] == '2021-01-01'
    assert got['months'][-1]['month'] == '2025-02-01'
    assert all(r['n_selected'] == 0 for r in got['months'])
    assert got['summary']['n_months_planned'] == 50
    assert got['summary']['n_months_paired'] == 0
    assert got['summary']['dependence_diagnostic']['status'] == 'unavailable_incomplete_calendar'
    assert got['p1_executed'] is False
    assert got['strategy_validation'] is False


def test_repeated_random_pairs_are_reported_and_seeded():
    m = module()
    c, q = panels('2021-01-31')
    d = pd.Timestamp('2021-01-01', tz='UTC')
    one = m.score_month(c, q, d, np.random.default_rng(42))
    two = m.score_month(c, q, d, np.random.default_rng(42))
    assert one == two
    assert one['n_random_scoreable'] == 20
    assert one['n_random_attempts'] == 20
    assert one['random_unordered_duplicates'] == 19
    assert one['random_ordered_duplicates'] >= 18
    assert one['random_reversed_pairs'] == 1


def test_missing_panel_day_keeps_rates_conditional():
    m = module()
    c, q = panels('2021-01-31')
    c = c.drop(pd.Timestamp('2021-01-14', tz='UTC'))
    got = m.score_month(c, q, pd.Timestamp('2021-01-01', tz='UTC'), np.random.default_rng(42))
    assert got['status'] == 'incomplete'
    assert got['missing_panel_dates']['close_persistence'] == ['2021-01-14']
    assert got['n_random_scoreable'] == 20


def test_no_compressed_bootstrap_when_month_missing_or_partial():
    m = module()
    rows = month_rows()
    rows[10]['status'] = 'incomplete'
    got = m.summarize_months(rows)
    assert got['n_months_paired'] == 50
    assert got['n_months_complete'] == 49
    assert got['historical_conditional_gate']['passes'] is True
    assert got['complete_panel_verdict'] == 'unavailable'
    assert got['dependence_diagnostic']['status'] == 'unavailable_incomplete_calendar'
    assert got['candidate_selected'] is False
    with pytest.raises(ValueError, match='50'):
        m.summarize_months(rows[:-1])


def test_fixed_stationary_bootstrap_reports_sensitivity_without_selection():
    from tradingagents.predlab.meanstats import stationary_bootstrap_means
    m = module()
    rows = month_rows()
    differences = np.repeat([.25, -.125, .5, -.25, .125], 10)
    for row, diff in zip(rows, differences):
        row['selected_rate'] = float(.5 + diff)
        row['random_rate'] = .5
    got = m.summarize_months(rows)
    draws = stationary_bootstrap_means(differences, n_boot=2000, mean_block=3, seed=4242)
    diag = got['dependence_diagnostic']
    assert diag['mean_difference'] == pytest.approx(.10)
    assert diag['interval_95'] == pytest.approx(np.quantile(draws, [.025, .975]))
    assert diag['fraction_positive'] == pytest.approx(float(np.mean(draws > 0)))
    assert got['candidate_selected'] is False


def test_zero_difference_has_no_wilcoxon_evidence():
    rows = month_rows()
    for row in rows:
        row['selected_rate'] = row['random_rate']
    got = module().summarize_months(rows)
    assert got['historical_conditional_gate']['wilcoxon_p'] == 1.
    assert got['historical_conditional_gate']['passes'] is False


def test_evaluation_does_not_read_or_trade_future_rows(monkeypatch):
    m = module()
    c, q = panels()
    # Empty screen avoids expensive fits; no month may use post-February prices.
    q[:] = np.nan
    before = m.evaluate_p0(c, q)
    c.loc['2025-03-01':] = -1
    q.loc['2025-03-01':] = 1e20
    assert m.evaluate_p0(c, q) == before
    assert before['holdout_read'] is False
    assert before['forecast_models_refit'] is False
    assert before['formation_regressions_recomputed'] is True


def test_gate_rejects_changed_seed_before_any_data_read():
    gate = json.loads((Path(__file__).parents[2] / 'data/predlab/gates.json').read_text())
    g = gate['audit_reevaluation_2026_09_09']['families']['prx']
    module().validate_gate(g)
    g['random_seed'] = 43
    with pytest.raises(ValueError, match='registered'):
        module().validate_gate(g)


def test_one_random_orientation_is_not_reported_as_a_reversal():
    class OneDirection:
        def choice(self, values, size, replace):
            return np.array(['B', 'A'])
    c, q = panels('2021-01-31')
    got = module().score_month(c, q, pd.Timestamp('2021-01-01', tz='UTC'), OneDirection())
    assert got['random_ordered_duplicates'] == 19
    assert got['random_reversed_pairs'] == 0


def test_changed_formation_contract_is_rejected():
    gates = json.loads((Path(__file__).parents[2] / 'data/predlab/gates.json').read_text())
    g = gates['audit_reevaluation_2026_09_09']['families']['prx']
    g['formation'] = 'ordinary ADF or changed window'
    with pytest.raises(ValueError, match='registered'):
        module().validate_gate(g)


@pytest.fixture
def synthetic_context(tmp_path, monkeypatch):
    from scripts.audit_reeval_common import RunContext, registry
    gate = json.loads((Path(__file__).parents[2] / 'data/predlab/gates.json').read_text())['audit_reevaluation_2026_09_09']
    gate['source_roots'] = [str(tmp_path / 'other-source'), str(tmp_path / 'source')]
    monkeypatch.setattr(registry, 'get_experiment', lambda key: gate)
    monkeypatch.setattr(registry, 'preflight', lambda *args: {'git_commit': 'synthetic', 'gate_sha256': 'synthetic'})
    recorded = []
    monkeypatch.setattr(registry, 'log_trial', lambda **kwargs: recorded.append(kwargs))
    ctx = RunContext('prx', root=tmp_path / 'output')
    return ctx, tmp_path / 'source', recorded


def write_synthetic_inputs(data_root):
    cache = data_root / 'predlab/t7_panels'
    cache.mkdir(parents=True)
    c, q = panels('2025-04-05')
    q[:] = np.nan
    c.to_parquet(cache / 'close.parquet')
    q.to_parquet(cache / 'qv.parquet')
    original = data_root / 'predlab/xfam/prx_result.json'
    original.parent.mkdir(parents=True)
    original.write_text(json.dumps({'git_commit': 'historical_synthetic',
        'P0': {'n_months': 50, 'per_month': month_rows(), 'ratio': 1.,
               'mean_sel_rate': .1, 'mean_rnd_rate': .1, 'wilcoxon_p': 1., 'pass': False}}))


def test_real_context_writes_one_cell_filters_dates_and_never_p1(synthetic_context, monkeypatch):
    ctx, data_root, recorded = synthetic_context
    write_synthetic_inputs(data_root)
    m = module()
    from scripts import predlab_xfam_lib
    def forbidden(*args, **kwargs):
        pytest.fail('P1 engine was called')
    monkeypatch.setattr(predlab_xfam_lib, 'pair_zmr_backtest', forbidden)
    actual_evaluate = m.evaluate_p0
    def bounded(close, qv, **kwargs):
        assert close.index.min() == pd.Timestamp('2020-10-03', tz='UTC')
        assert close.index.max() == pd.Timestamp('2025-02-28', tz='UTC')
        assert qv.index.max() == close.index.max()
        return actual_evaluate(close, qv, **kwargs)
    monkeypatch.setattr(m, 'evaluate_p0', bounded)
    output = m.run(ctx, data_root)
    payload = json.loads(output.read_text())
    assert payload['p1_executed'] is False
    assert payload['holdout_read'] is False
    assert payload['candidate_selected'] is False
    assert [r['id'] for r in payload['cells']] == ['top50_90d_persistence']
    assert payload['input_unchanged_after_run'] is True
    assert len(payload['input_sha256']) == 3
    assert len(recorded) == 1
    archive = pd.read_parquet(ctx.output_dir / 'monthly.parquet')
    assert len(archive) == 50
    assert archive.iloc[-1]['month'] == '2025-02-01'
    with pytest.raises(FileExistsError):
        m.run(ctx, data_root)


def test_missing_source_retains_blocked_primary_cell(synthetic_context):
    ctx, data_root, recorded = synthetic_context
    output = module().run(ctx, data_root)
    payload = json.loads(output.read_text())
    assert payload['status'] == 'blocked'
    assert payload['cells'][0]['id'] == 'top50_90d_persistence'
    assert payload['cells'][0]['metrics']['status'] == 'blocked'
    assert len(recorded) == 1
    assert payload['p1_executed'] is False


def test_zero_random_rate_preserves_declared_legacy_denominator_floor():
    rows = month_rows()
    for row in rows:
        row['selected_rate'] = .1
        row['random_rate'] = 0.
    gate = module().summarize_months(rows)['historical_conditional_gate']
    assert gate['ratio'] == pytest.approx(1e8)
    assert gate['zero_random_baseline'] is True
    assert gate['ratio_denominator'] == 1e-9
    assert gate['passes'] is True


def test_default_cli_cannot_create_run_state_or_read_inputs(monkeypatch, tmp_path):
    from scripts import audit_reeval_common
    def forbidden(*args, **kwargs):
        (tmp_path / 'incorrect-start').write_text('consumed')
        raise AssertionError('RunContext must not exist without --execute')
    monkeypatch.setattr(audit_reeval_common, 'RunContext', forbidden)
    assert module().main([]) == 0
    assert not (tmp_path / 'incorrect-start').exists()


def test_help_cannot_create_run_state(monkeypatch, tmp_path):
    from scripts import audit_reeval_common
    def forbidden(*args, **kwargs):
        (tmp_path / 'incorrect-start').write_text('consumed')
        raise AssertionError('Help created run state')
    monkeypatch.setattr(audit_reeval_common, 'RunContext', forbidden)
    with pytest.raises(SystemExit) as exc:
        module().main(['--help'])
    assert exc.value.code == 0
    assert not (tmp_path / 'incorrect-start').exists()


def test_run_rejects_replacement_input_root_before_consumption(synthetic_context):
    ctx, data_root, recorded = synthetic_context
    unregistered = data_root.parent / 'replacement'
    write_synthetic_inputs(unregistered)
    with pytest.raises(ValueError, match='registered'):
        module().run(ctx, unregistered)
    assert not ctx.hashes
    assert not recorded
    assert not (ctx.output_dir / 'result.json').exists()


def test_progress_reports_only_fixed_calendar_counts():
    c, q = panels()
    q[:] = np.nan
    counts = []
    module().evaluate_p0(c, q, progress=lambda done, total: counts.append((done, total)))
    assert counts == [(n, 50) for n in range(5, 51, 5)]
