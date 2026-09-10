import numpy as np
import pandas as pd
import pytest

from tradingagents.strategies import factor_risk_policy_evaluation as ev


def test_metrics_cash_is_complete_with_null_sharpe():
    idx = pd.date_range('2021-11-08', periods=4, tz='UTC')
    got = ev.return_metrics(pd.Series(0., index=idx), idx)
    assert got['status'] == 'complete'
    assert got['sharpe'] is None and got['sharpe_reason'] == 'zero_variance'
    assert got['n_bars'] == 4 and got['total_return'] == got['max_drawdown'] == 0


def test_initial_loss_drawdown_and_full_cash_tail():
    idx = pd.date_range('2021-11-08', periods=4, tz='UTC')
    got = ev.return_metrics(pd.Series([-.1, 0, 0, 0], index=idx), idx)
    assert got['max_drawdown'] == pytest.approx(-.1)
    assert got['n_bars'] == 4 and got['total_return'] == pytest.approx(-.1)
    assert got['sharpe'] == pytest.approx(np.sqrt(365)*(-.025)/.05)


@pytest.mark.parametrize('fault', ['gap', 'nan', 'ruin', 'order'])
def test_returns_fail_closed(fault):
    idx = pd.date_range('2021-11-08', periods=4, tz='UTC')
    r = pd.Series([0., .01, -.02, .03], index=idx)
    if fault == 'gap': r = r.iloc[1:]
    if fault == 'nan': r.iloc[1] = np.nan
    if fault == 'ruin': r.iloc[1] = -1
    if fault == 'order': r = r.iloc[::-1]
    with pytest.raises(ValueError): ev.return_metrics(r, idx)


def test_trace_parity_compares_flags_nulls_and_original_columns():
    old = pd.DataFrame({'date':['2021-11-08'], 'nav_before':[100.],
                        'exposure':[0.], 'entry_price':[None], 'halted_after':[False]})
    new = old.assign(policy_extra='allowed')
    assert ev.control_trace_parity(new, old, ev.POLICY)['matched']
    for name, value in [('halted_after',True), ('entry_price',1), ('exposure',1e-7)]:
        bad = new.copy(); bad[name] = value
        with pytest.raises(ValueError): ev.control_trace_parity(bad, old, ev.POLICY)


def test_return_parity_requires_both_sleeves_and_index():
    idx = pd.date_range('2021-11-08', periods=2, tz='UTC', name='Date')
    original = pd.DataFrame({'bitcoin':[.1,0], 'ethereum':[0,.2],
                             'index_return':[.05,.1]}, index=idx)
    assert ev.control_return_parity(original, original, ev.POLICY)['matched']
    altered = original.copy(); altered.loc[idx[0],'ethereum'] = .001
    with pytest.raises(ValueError): ev.control_return_parity(altered, original, ev.POLICY)


def test_frozen_shadow_retains_fees_and_does_not_recalculate_stop():
    trace = pd.DataFrame({'mark_return':[.1,-.1], 'exposure':[-1.,0.],
                           'pre_nav':[100.,89.], 'post_nav':[89.,89.]})
    got = ev.frozen_log_shadow(trace)
    assert got[0] == pytest.approx(-np.log1p(.1)-.01)
    assert got[1] == 0


def test_shadow_invalid_return_not_filtered():
    t = pd.DataFrame({'mark_return':[-1.], 'exposure':[0.], 'pre_nav':[1.], 'post_nav':[1.]})
    with pytest.raises(ValueError): ev.frozen_log_shadow(t)


def test_cost_variants_are_independent_and_do_not_mutate():
    costs = dict(ev.COSTS)
    assert ev.cost_variant(costs,'double_execution')['price_impact'] == 2*costs['price_impact']
    assert ev.cost_variant(costs,'zero_execution')['funding_rate'] == costs['funding_rate']
    assert ev.cost_variant(costs,'zero_funding')['fee_rate'] == costs['fee_rate']
    assert costs == ev.COSTS
    with pytest.raises(ValueError): ev.cost_variant(costs,'legacy')


def test_contrasts_preserve_nulls_and_fixed_factorial_identity():
    arms = {k:{'x':x,'sharpe':None} for k,x in [('A00',1),('A10',3),('A01',4),('A11',10)]}
    got = ev.scalar_contrasts(arms)
    assert got['direct']['A10']['x'] == 2
    assert got['factorial']['sizing']['x'] == 4
    assert got['factorial']['waiting']['x'] == 5
    assert got['factorial']['interaction']['x'] == 4
    assert got['direct']['A11']['sharpe'] is None


def test_target_admission_rejects_boolean_and_late_or_incoherent_price():
    idx = pd.date_range('2021-11-07', periods=3, tz='UTC')
    t = pd.DataFrame({'Date':idx, 'Open':100.,'High':101.,'Low':99.,'Close':100.,'target':0.})
    assert ev.validate_targets(t,idx)['Date'].tolist() == idx.tolist()
    for field, value in [('target',True), ('Close',102.), ('Close',np.nan)]:
        bad=t.copy(); bad[field]=value
        with pytest.raises(ValueError): ev.validate_targets(bad,idx)


def test_period_counts_include_zero_cash():
    idx=pd.date_range('2024-12-30',periods=4,tz='UTC')
    periods=[['2024-12-30','2024-12-31'],['2025-01-01','2025-01-02']]
    result=ev.period_metrics(pd.Series([.1,0,0,0],index=idx),periods)
    assert [p['metrics']['n_bars'] for p in result] == [2,2]
    assert result[1]['metrics']['sharpe'] is None


@pytest.fixture
def policy_trace():
    from scripts.baseline_strategy_v2 import run_coin_backtest
    from tradingagents.strategies.factor_risk_policy import FactorRiskPolicy,causal_sigma
    idx=pd.date_range('2021-11-07',periods=52,tz='UTC')
    close=100*np.exp(.01*np.sin(np.arange(52)/4))
    target=np.zeros(52);target[23:]=.2
    targets=pd.DataFrame(dict(Date=idx,Open=close,High=close*1.02,Low=close*.98,Close=close,target=target))
    targets.loc[31,'Low']=90.
    cell=dict(sizing='daily',reentry='new_target_episode')
    trace=[]
    run_coin_backtest(idx.to_numpy(),close,target,10000.,**ev.COSTS,highs=targets.High.to_numpy(),
        lows=targets.Low.to_numpy(),price_stop_pct=.03,trace=trace,
        target_policy=FactorRiskPolicy(**cell,sigma=causal_sigma(close)))
    return targets,pd.DataFrame(trace),cell


def test_daily_waiting_diagnostics_preserve_counts_and_risk_cap(policy_trace):
    targets,trace,cell=policy_trace
    got=ev.evaluate_trace(targets,trace,cell)
    s=got['summary']
    assert s['trace_rows']==51
    assert sum(s[k] for k in ('active_rows','waiting_rows','halted_cash_rows','other_flat_rows'))==51
    assert s['risk_counts']['applied']['above_nominal_budget']==0
    assert s['waiting_rows']>0
    assert set(got['events'].sizing_reference_basis)=={'original_raw_target'}


@pytest.mark.parametrize('column,value',[('raw_target',2.),('fee_dollars',100.),('nav_after',9999.),
    ('sizing_sigma',100.),('decision_blocked',True)])
def test_trace_mutation_is_not_silently_scored(policy_trace,column,value):
    targets,trace,cell=policy_trace
    trace.loc[23,column]=value
    with pytest.raises(ValueError):ev.evaluate_trace(targets,trace,cell)
