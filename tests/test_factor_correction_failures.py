"""Caller-level failure preservation using only temporary synthetic inputs.

These exercise the real main orchestration and output writer. Engines, archived
builders, and registry authority are test seams, not accounting verification.
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_runner(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'scripts/audit_factor_floor_2026_09_10.py'
    spec = importlib.util.spec_from_file_location('factor_failure_review', path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, 'BASE', tmp_path / 'case')
    monkeypatch.setattr(runner, 'ARCHIVE', tmp_path / 'archive')
    monkeypatch.setattr(runner, 'WINDOW', ('2021-11-07', '2021-11-11'))
    runner.ARCHIVE.mkdir()
    (runner.BASE / 'inputs').mkdir(parents=True)
    dates = pd.date_range(pd.Timestamp(runner.WINDOW[0]) - pd.Timedelta(days=200),
                          runner.WINDOW[1], freq='D')
    frame = pd.DataFrame({'Date': dates, 'Open': 100., 'High': 101.,
                          'Low': 99., 'Close': 100.})
    for coin in runner.COINS:
        frame.to_csv(runner.BASE / 'inputs' / f'{coin}.csv', index=False)
    specs = [{'name': f'synthetic_{i}',
              'builder': lambda data: np.zeros(len(data), dtype=np.int8)}
             for i in range(18)]
    configs = [{'name': item['name']} for item in specs]
    (runner.ARCHIVE / 'comparison.json').write_text(json.dumps({'cells': [
        {'configname': item['name'], 'original_metrics': {
            'sharpe': 0., 'total_return': 0., 'max_drawdown': 0., 'n_bars': 4}}
        for item in specs]}))
    fault = {'variant': None}

    def engine(dates, prices, positions, capital, **kwargs):
        if fault['variant'] == 'zero_execution' and kwargs['fee_rate'] == 0:
            raise ValueError('synthetic zero-execution-only failure')
        if 'trace' in kwargs:
            for day in dates[1:]:
                kwargs['trace'].append(dict(
                    date=str(day), pre_nav=capital, post_nav=capital,
                    mark_return=0., exposure=0., halted_after=False,
                    gross_dollars=0., funding_dollars=0., fee_dollars=0.,
                    impact_dollars=0., turnover_dollars=0.,
                    price_stop_hit=False, stop_outside_envelope=False))
        return [capital] * len(dates), {'halted': False}

    def extract(path, names):
        if 'build_config_specs' in names:
            return {'build_config_specs': lambda: specs}
        return {'run_coin_backtest': engine}

    monkeypatch.setattr(runner, 'extract_functions', extract)
    monkeypatch.setattr(runner, 'run_coin_backtest', engine)
    monkeypatch.setattr(runner.registry, 'preflight', lambda *args: {'git_commit': 'synthetic'})
    monkeypatch.setattr(runner.registry, 'get_experiment', lambda key: {
        'variants': list(runner.VARIANTS), 'pinned_files': {}, 'cells': configs})
    logged = []
    monkeypatch.setattr(runner.registry, 'log_trial', lambda *args: logged.append(args))
    return runner, fault, logged


@pytest.mark.parametrize('failure', ['shadow_only', 'zero_execution'])
def test_main_preserves_primary_and_all_registered_variants_after_failure(
        synthetic_runner, monkeypatch, failure):
    runner, fault, logged = synthetic_runner
    if failure == 'shadow_only':
        def invalid_shadow(trace):
            raise ValueError('synthetic shadow-only invalid arithmetic')
        monkeypatch.setattr(runner, 'log_shadow', invalid_shadow)
    else:
        fault['variant'] = failure

    runner.main()
    output = runner.BASE / 'results'
    result = json.loads((output / 'result.json').read_bytes())
    assert len(result['cells']) == len(logged) == 18
    assert len({cell['id'] for cell in result['cells']}) == 18
    assert sum(len(cell['variants']) for cell in result['cells']) == 90
    assert result['validated_strategies'] == 0
    for cell, ledger_call in zip(result['cells'], logged):
        assert cell['metrics']['status'] == 'qualified_benchmark_measurement'
        assert cell['metrics']['n_bars'] == 4
        assert cell['metrics']['validated'] is False
        assert list(cell['variants']) == list(runner.VARIANTS)
        assert ledger_call[-1]['status'] == cell['metrics']['status']
        assert ledger_call[-1]['variants'] == cell['variants']
        for variant in runner.VARIANTS:
            measured = not (failure == 'zero_execution' and variant == 'zero_execution')
            item = cell['variants'][variant]
            assert item['status'] == ('measured' if measured else 'unavailable')
            if measured:
                assert item['metrics']['n_bars'] == 4
                saved = pd.read_parquet(output / f"{cell['id']}-{variant}-returns.parquet")
                assert len(saved) == 4 and saved.notna().all().all()
            else:
                assert 'synthetic zero-execution-only failure' in item['reason']
        shadow = cell['invalid_log_shadow']
        assert ledger_call[-1]['invalid_log_shadow'] == shadow
        if failure == 'shadow_only':
            assert shadow['status'] == 'unavailable'
            assert 'synthetic shadow-only invalid arithmetic' in shadow['reason']
        else:
            assert shadow['status'] == 'invalid_frozen_exposure_diagnostic'
    assert all((output / name).exists() for name in result['output_sha256'])
