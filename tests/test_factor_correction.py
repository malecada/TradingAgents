"""Synthetic safety contracts for the fixed factor correction, no market data."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import pytest


def module():
    path = Path(__file__).resolve().parents[1] / 'scripts/audit_factor_floor_2026_09_10.py'
    assert path.exists(), 'isolated fixed-grid correction runner is missing'
    spec = importlib.util.spec_from_file_location('factor_correction', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture():
    return pd.DataFrame({'Date': pd.date_range('2021-01-01', periods=5),
                         'Open': [100.] * 5, 'High': [110.] * 5,
                         'Low': [90.] * 5, 'Close': [100.] * 5})


def test_initial_loss_and_cash_tail_are_counted():
    m = module().metrics(np.array([-.1, .0, .0, .0]))
    assert m['max_drawdown'] == pytest.approx(-.1)
    assert m['total_return'] == pytest.approx(-.1)
    assert m['n_bars'] == 4
    assert m['sharpe'] == pytest.approx(np.sqrt(365) * -.025 / .05)


@pytest.mark.parametrize('defect', ['gap', 'duplicate', 'nan', 'envelope', 'nonmidnight', 'holdout'])
def test_bad_market_data_cannot_be_dropped_or_filled(defect):
    frame = fixture()
    if defect == 'gap': frame = frame.drop(2)
    if defect == 'duplicate': frame.loc[2, 'Date'] = frame.loc[1, 'Date']
    if defect == 'nan': frame.loc[2, 'Low'] = np.nan
    if defect == 'envelope': frame.loc[2, 'Close'] = 120
    if defect == 'nonmidnight': frame.loc[2, 'Date'] += pd.Timedelta(hours=1)
    if defect == 'holdout': frame.loc[4, 'Date'] = pd.Timestamp('2025-04-01')
    with pytest.raises(ValueError): module().validate_market(frame)


def test_log_shadow_is_disclosed_frozen_exposure_distortion():
    trace = pd.DataFrame({'exposure': [-1., 1.], 'mark_return': [.1, -.1],
                          'pre_nav': [100., 90.], 'post_nav': [90., 81.]})
    out = module().log_shadow(trace)
    assert out[0] == pytest.approx(-np.log(1.1))
    assert out[1] == pytest.approx(np.log(.9))


def test_invalid_log_shadow_is_unavailable():
    trace = pd.DataFrame({'exposure': [1.], 'mark_return': [-1.],
                          'pre_nav': [100.], 'post_nav': [10.]})
    with pytest.raises(ValueError): module().log_shadow(trace)


def test_aggregation_rejects_missing_sleeve_instead_of_skipna():
    with pytest.raises(ValueError): module().index_returns([np.array([.1, np.nan]), np.array([.1, .2])])


def test_output_refuses_previous_run(tmp_path):
    output = tmp_path / 'run'
    module().reserve_output(output, {'test': True})
    with pytest.raises(FileExistsError): module().reserve_output(output, {'test': True})


def test_one_variant_failure_does_not_hide_others():
    attempted = []
    def run(name):
        attempted.append(name)
        if name == 'zero_execution': raise ValueError('synthetic insolvency')
        return {'value': name}
    result = module().guarded_variants(run)
    assert attempted == list(module().VARIANTS)
    assert result['primary'] == {'value': 'primary'}
    assert result['zero_execution']['status'] == 'unavailable'
    assert result['legacy'] == {'value': 'legacy'}


@pytest.mark.parametrize('variant', ['primary', 'zero_execution', 'double_execution', 'zero_funding'])
def test_cost_and_funding_controls_have_hand_calculated_cashflows(variant):
    mod = module()
    costs = mod.cost_variant(variant)
    for side in (-1., 1.):
        trace = []
        equity, _ = mod.run_coin_backtest(pd.date_range('2024-01-01', periods=2),
            np.array([100., 100.]), np.array([0., side]), 10000., **costs, trace=trace)
        # Flat price, one entry:10 execution dollars +.5 quadratic impact;
        # signed3 dollars assumed funding. Fixed sensitivities alter only stated charges.
        charge = {'primary': 10.5, 'zero_execution': 0., 'double_execution': 21., 'zero_funding': 10.5}[variant]
        funding = 0. if variant == 'zero_funding' else -3.*side
        assert equity[-1] == pytest.approx(10000.-charge+funding)


def test_archived_engine_can_be_replayed_without_importing_historical_loader():
    mod = module()
    old = mod.extract_functions(mod.ARCHIVE/'baseline_strategy_v2_f359050.py', ['run_coin_backtest'])['run_coin_backtest']
    eq, _ = old(pd.date_range('2024-01-01', periods=3), np.array([100.,110.,121.]),
        np.array([0.,1.,1.]), 100., fee_rate=.01, slippage=0., spread=0., price_impact=0.,
        funding_rate=0., stop_loss=1., max_portfolio_dd=1.)
    assert eq == pytest.approx([100.,108.,118.8])
