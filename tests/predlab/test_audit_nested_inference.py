"""Explicit nesting and matching-loss eligibility reach actual battery callers."""
import json

import numpy as np
import pandas as pd
import pytest

from scripts import predlab_run_battery as battery
from tradingagents.predlab import registry, rollup, runner
from tradingagents.predlab.baselines import Forecaster


class ColumnForecast(Forecaster):
    def __init__(self, name, column):
        self.name, self.column = name, column

    def predict(self, y_hist, x_now=None):
        return x_now[self.column]


def series():
    x = np.arange(120.)
    y = 2 + .3 * np.sin(x)
    return pd.DataFrame({'y': y, 'base': y + .5 + .1 * np.cos(x), 'large': y + .05},
                        index=pd.date_range('2021-01-01', periods=len(x), freq='h', tz='UTC'))


def cell(loss='qlike', nested=True, registered='clark_west'):
    return {'cell': 'SYN', 'target': 'T3_rv', 'horizon_bars': 1,
            'strong_baseline': 'har_levels', 'loss': loss, 'min_train': 30,
            'nested_models': {'harq': 'har_levels'} if nested else {},
            'registered_nested_test': registered}


@pytest.mark.parametrize('loss,nested,registered,primary,eligible', [
    ('qlike', True, 'clark_west', 'unavailable_nested_loss_test', False),
    ('se', True, 'clark_west', 'clark_west', True),
    ('se', True, None, 'unavailable_nested_loss_test', False),
    ('se', False, 'clark_west', 'dm_hac', True),
])
def test_runner_requires_explicit_nesting_and_matching_registered_test(loss, nested, registered, primary, eligible):
    rows = runner.run_cell(cell(loss, nested, registered), series(),
        [ColumnForecast('har_levels', 0), ColumnForecast('harq', 1), ColumnForecast('log_har', 1)],
        'synthetic', 'test', dry=True).set_index('model')
    assert bool(rows.loc['harq', 'nested']) is nested
    assert rows.loc['harq', 'primary_test'] == primary
    assert bool(rows.loc['harq', 'inference_eligible']) is eligible
    assert not bool(rows.loc['log_har', 'nested'])  # a shared family does not declare nesting
    assert rows.loc['log_har', 'primary_test'] == 'dm_hac'
    assert np.isfinite(rows.loc['harq', ['dm_p', 'cw_p', 'gw_p']].astype(float)).all()


@pytest.mark.parametrize('loss,gate_test,primary,eligible', [
    ('qlike', 'clark_west', 'unavailable_nested_loss_test', False),
    ('se', None, 'unavailable_nested_loss_test', False),
    ('se', 'clark_west', 'clark_west', True),
])
def test_written_card_and_trial_keep_nested_inference_qualification(tmp_path, monkeypatch, loss, gate_test, primary, eligible):
    monkeypatch.setattr(registry, 'preflight', lambda *a, **k: {'git_commit': 'synthetic'})
    monkeypatch.setattr(registry, 'gates_path', lambda: tmp_path / 'gates.json')
    monkeypatch.setattr(registry, 'get_experiment', lambda *a: {'tests': {'nested': gate_test}})
    logged = []
    monkeypatch.setattr(registry, 'log_trial', lambda *a, **k: logged.append(a))
    runner.run_cell(cell(loss, registered='clark_west'), series(),
                    [ColumnForecast('har_levels', 0), ColumnForecast('harq', 1)],
                    'synthetic', 'test', dry=False)
    card = json.loads((tmp_path / 'cards/synthetic/SYN.json').read_text())['test']
    assert card['nested_models'] == {'harq': 'har_levels'}
    assert card['per_model']['harq']['nested'] is True
    assert card['registered_nested_test'] == gate_test  # caller cannot invent gate registration
    assert card['per_model']['harq']['primary_test'] == primary
    assert card['per_model']['harq']['inference_eligible'] is eligible
    config = next(args[3] for args in logged if args[2] == 'harq')
    assert config['primary_test'] == primary
    assert config['inference_eligible'] is eligible


@pytest.mark.parametrize('call,horizon', [
    ('run_tier1_t3_24h', '24h'), ('run_tier1_1h', '1h'),
    ('run_tier1_7d', '7d'), ('run_tier2_t3t4', '24h'),
])
def test_actual_harq_battery_call_cannot_select_dm_for_nested_qlike(monkeypatch, call, horizon):
    entry = {'protocol': {'refit_every': {'arima_ets_garch': {'1h': 1, '24h': 1}, '24h': 1},
                          'min_train': {'1h': 30, '24h': 30, '7d': 30}, 'loss': {'T3': 'qlike'}},
             'cells': [{'cell': 'SYN', 'symbol': 'BTCUSDT', 'horizon': horizon,
                        'target': 'T3_rv', 'strong_baseline': 'har_levels', 'eval_start': '2021-01-01'}],
             'dev_window': ['2021-01-01', '2021-03-01'],
             'tests': {'nested': 'clark_west'}, 'feature_sets': {'T3_rv': ['rq_lag1']}}
    toy = series()
    store = pd.DataFrame({'rv': toy.y, 'ret': .01, 'rq': .2}, index=toy.index)
    monkeypatch.setattr(registry, 'get_experiment', lambda *a: entry)
    monkeypatch.setattr(battery, '_rv_store', lambda *a: store)
    monkeypatch.setattr(battery, '_t2_features', lambda *a: store.rq.to_frame('rq_lag1'))
    real_runner = runner.run_cell
    captured = []
    def offline_run(cell, supplied_series, models, **kwargs):
        # Exercise actual cell/model construction, with synthetic forecasts at the
        # expensive fit boundary. No stored data or empirical model fit is used.
        assert any(m.name == 'harq' for m in models)
        rows = real_runner(cell, toy,
            [ColumnForecast(m.name, int(m.name == 'harq')) for m in models],
            kwargs['gates_key'], kwargs['tier'], dry=True)
        captured.append((cell, rows))
        return rows
    monkeypatch.setattr(runner, 'run_cell', offline_run)
    args = ('synthetic', '*') if call == 'run_tier2_t3t4' else ('synthetic',)
    getattr(battery, call)(*args)
    assert len(captured) == 1
    declared, rows = captured[0]
    assert declared['nested_models'] == {'harq': 'har_levels'}
    per_model = rows.set_index('model').to_dict('index')
    assert per_model['harq']['primary_test'] == 'unavailable_nested_loss_test'
    assert per_model['harq']['inference_eligible'] is False
    chosen = rollup.champion({'loss': 'qlike', 'strong_baseline': 'har_levels', 'per_model': per_model})
    assert np.isnan(chosen['dm_p'])
    assert chosen['inference_eligible'] is False
