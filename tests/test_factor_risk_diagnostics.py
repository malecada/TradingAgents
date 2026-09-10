"""Hand-derived synthetic books only; never consume saved research outcomes."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]


def module():
    path = ROOT / 'tradingagents/strategies/factor_risk_diagnostics.py'
    assert path.exists(), 'pure factor risk diagnostics have not been implemented'
    spec = importlib.util.spec_from_file_location('factor_risk_test_module', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def synthetic_book(n=45, side=1, variation=1.):
    """A specified constant-target book, not a strategy or risk-policy replay."""
    clock = pd.date_range('2023-01-01', periods=n, freq='D')
    close = 100 * np.exp(variation*np.cumsum(np.resize([.004, -.003, .008, -.006], n)))
    visible = np.r_[close[0], close[:-1]]
    vol20 = np.std(np.diff(np.log(visible[:21])), ddof=1) * np.sqrt(252)
    weights = np.r_[np.zeros(20), np.full(n-20, side * min(.15/vol20, 3.))]
    targets = pd.DataFrame({'Date': clock, 'Close': close, 'Open': close,
                            'High': close, 'Low': close, 'Volume': 1.,
                            'signal': side, 'target': weights})
    rows, nav, holding = [], 10000., 0.
    for i in range(1, n):
        w = weights[i]
        ret = close[i]/close[i-1]-1
        gross = nav*w*ret
        funding = -nav*w*.0003
        turnover = abs(nav*w-holding)
        fee = .001*turnover
        impact = nav*.00005*(turnover/nav)**2
        after = nav+gross+funding-fee-impact
        holding = nav*w*(1+ret)
        rows.append(dict(date=clock[i].isoformat(), nav_before=nav, pre_nav=nav,
            target_position=w, exposure=w, mark_return=ret, mark_price=close[i],
            entry_price=close[19] if w else None, gross_dollars=gross,
            funding_dollars=funding, entry_fee_dollars=fee, entry_impact_dollars=impact,
            entry_turnover_dollars=turnover, exit_fee_dollars=0., exit_impact_dollars=0.,
            exit_turnover_dollars=0., exit_notional=0., exit_executed=False,
            halted_before=False, price_stop_hit=False, stop_outside_envelope=False,
            nav_after=after, post_nav=after, net_return=(after-nav)/nav,
            fee_dollars=fee, impact_dollars=impact, turnover_dollars=turnover,
            closing_notional=holding, portfolio_stop_hit=False, halted_after=False))
        nav = after
    return targets, pd.DataFrame(rows)


def test_causal_volatility_exact_original_lag_reset_and_warmup():
    m = module()
    close = np.exp(np.r_[0., np.cumsum(np.linspace(.001, .04, 29))])
    out = m.volatility_features(close)
    assert out.sigma_252.iloc[:20].isna().all()
    visible = np.r_[close[0], close[:-1]]
    expected = np.std(np.diff(np.log(visible[:21])), ddof=1)*np.sqrt(252)
    assert out.sigma_252.iloc[20] == pytest.approx(expected)
    changed = close.copy(); changed[23:] *= 10
    pd.testing.assert_frame_equal(out.iloc[:24], m.volatility_features(changed).iloc[:24])
    assert not out.vol_entry_gate_open.iloc[:20].any()


def test_gate_uses_only_twenty_prior_finite_volatilities():
    out = module().volatility_features(np.exp(np.arange(70)**2/10000))
    assert out.entry_gate_threshold.iloc[:40].isna().all()
    assert out.entry_gate_threshold.iloc[40] == pytest.approx(
        np.quantile(out.sigma_252.iloc[:40].dropna(), .95))


@pytest.mark.parametrize('side', [1, -1])
def test_drift_maintenance_is_actual_turnover_not_a_new_target(side):
    out = module().turnover_components(100., 60.*side, .5*side, .5*side)
    assert out['target_change_dollars'] == 0
    assert out['maintenance_dollars'] == -10*side
    assert out['opening_turnover_dollars'] == 10
    assert out['row_class'] == 'unchanged_target_maintenance'


def test_opposing_trade_components_preserve_netting():
    out = module().turnover_components(100., 60., .7, .5)
    assert out['target_change_dollars'] == pytest.approx(20)
    assert out['maintenance_dollars'] == -10
    assert out['opening_turnover_dollars'] == pytest.approx(10)
    assert out['component_netting_dollars'] == pytest.approx(20)
    assert out['row_class'] == 'same_sign_target_change'


@pytest.mark.parametrize('held,w,old,kind', [
    (0, 0, 0, 'no_trade'), (0, .5, .5, 'opening_from_flat'),
    (50, 0, .5, 'closing_to_flat'), (50, -.5, .5, 'sign_flip')])
def test_turnover_classes_are_exclusive(held, w, old, kind):
    assert module().turnover_components(100., held, w, old)['row_class'] == kind


@pytest.mark.parametrize('side', [1, -1])
def test_analyzer_separates_targets_holdings_and_nominal_risk(side):
    targets, trace = synthetic_book(side=side)
    before = targets.copy(deep=True), trace.copy(deep=True)
    out = module().analyze_sleeve(targets, trace)
    assert out['summary']['status'] == 'complete_qualified'
    daily = out['daily']
    pd.testing.assert_index_equal(pd.DatetimeIndex(daily.date), pd.DatetimeIndex(targets.Date[1:]), check_names=False)
    entry = daily.iloc[19]
    assert entry.builder_sizing_event == 'entry'
    assert entry.applied_risk_proxy == pytest.approx(min(.15, 3*entry.sigma_252))
    later = daily.iloc[21]
    assert later.applied_weight == entry.applied_weight
    assert later.incoming_weight != later.applied_weight
    assert later.applied_risk_proxy != entry.applied_risk_proxy
    assert later.sizing_date == entry.date.isoformat()
    assert out['summary']['risk_distributions']['applied']['unavailable_rows'] == 19
    assert out['summary']['initial_nav'] == 10000
    assert out['summary']['first_halt'] is None
    assert out['summary']['components']['net_dollars'] == pytest.approx(trace.nav_after.iloc[-1]-10000)
    pd.testing.assert_frame_equal(targets, before[0]); pd.testing.assert_frame_equal(trace, before[1])


def test_input_defects_preserve_unavailable_status_and_reason():
    m = module()
    targets, trace = synthetic_book()
    bad = trace.copy(); bad.loc[3, 'date'] = bad.loc[2, 'date']
    out = m.analyze_sleeve(targets, bad)
    assert out['summary']['status'] == 'unavailable'
    assert 'clock' in out['summary']['reason']
    for column in ('gross_dollars', 'nav_before', 'exposure', 'closing_notional'):
        bad = trace.copy(); bad.loc[25, column] += 1
        assert m.analyze_sleeve(targets, bad)['summary']['status'] == 'unavailable', column


def test_same_sign_raw_target_change_is_unsupported_not_a_resizing_event():
    t, r = synthetic_book(); t.loc[30:, 'target'] *= .9
    out = module().analyze_sleeve(t, r)
    assert out['summary']['status'] == 'unavailable'
    assert 'same-sign raw-target' in out['summary']['reason']


def test_low_volatility_entry_is_clipped_and_all_exposure_ratios_have_denominators():
    targets,trace=synthetic_book(variation=.01)
    out=module().analyze_sleeve(targets,trace)
    assert out['summary']['status']=='complete_qualified'
    entry=out['daily'].iloc[19]
    assert entry.applied_weight==3
    assert entry.applied_risk_proxy==pytest.approx(3*entry.sigma_252)
    assert entry.applied_risk_proxy < .15
    for label in ('latent','incoming','applied','closing'):
        assert label+'_reference_risk_ratio' in out['daily']
        distribution=out['summary']['risk_distributions'][label+'_reference_ratio']
        assert distribution['active_finite_rows']+distribution['active_unavailable_rows']==distribution['active_rows']
        count=out['summary']['counts'][label+'_risk_thresholds']
        assert count['reference_available_active_rows']+count['reference_unavailable_active_rows']==distribution['active_rows']


def test_warmup_unavailable_thresholds_are_null_not_claimed_false():
    targets,trace=synthetic_book()
    daily=module().analyze_sleeve(targets,trace)['daily']
    assert pd.isna(daily.loc[0,'incoming_above_reference_risk'])
    assert pd.isna(daily.loc[0,'applied_above_nominal_entry_budget'])


def test_closed_volatility_entry_gate_does_not_relabel_existing_hold_as_invalid():
    t,r=synthetic_book(variation=np.r_[np.ones(20),np.linspace(1.,2.,25)])
    out=module().analyze_sleeve(t,r)
    assert out['summary']['status']=='complete_qualified'
    assert out['summary']['counts']['applied_while_entry_gate_closed'] > 0
    assert out['summary']['counts']['builder_entries']==1


def test_flat_warmup_book_has_honest_empty_active_and_stop_denominators():
    t,r=synthetic_book(n=20)
    out=module().analyze_sleeve(t,r)
    assert out['summary']['status']=='complete_qualified'
    assert out['summary']['risk_distributions']['applied']['active_rows']==0
    assert out['summary']['risk_distributions']['applied']['median'] is None
    assert out['summary']['price_stops']==0
    assert out['summary']['stop_sizing_age_distributions']['at_reentry']['active_rows']==0


def test_complete_post_exit_halt_book_retains_latent_targets_and_exact_cash_tail():
    t,r=synthetic_book(n=25)
    i=19; nav=10000.; w=r.loc[i,'exposure']; gross=nav*w*(-.03)
    entry_fee=r.loc[i,'entry_fee_dollars']; impact=r.loc[i,'entry_impact_dollars']
    after=nav+gross-entry_fee-impact-2000
    marked=nav*w*.97
    r.loc[i,['mark_return','gross_dollars','funding_dollars']]=[-.03,gross,0.]
    r.loc[i,'mark_price']=t.loc[19,'Close']*.97
    r.loc[i,['exit_fee_dollars','fee_dollars']]=[2000,entry_fee+2000]
    r.loc[i,['exit_notional','exit_turnover_dollars']]=marked
    r.loc[i,'turnover_dollars']=r.loc[i,'entry_turnover_dollars']+marked
    r.loc[i,['closing_notional','nav_after','post_nav','net_return']]=[0,after,after,after/nav-1]
    r.loc[i,['exit_executed','price_stop_hit','halted_after']]=True
    for j in range(i+1,len(r)):
        for k in module().NUM_COLUMNS:
            if k.endswith('_dollars') or k in ('exposure','target_position','closing_notional','exit_notional','net_return'):
                r.loc[j,k]=0.
        r.loc[j,['nav_before','pre_nav','nav_after','post_nav']]=after
        r.loc[j,['halted_before','halted_after','portfolio_stop_hit']]=True
    out=module().analyze_sleeve(t,r)
    assert out['summary']['status']=='complete_qualified'
    assert out['summary']['first_halt']['crossing_stage']=='post_exit'
    assert out['summary']['halted_cash_rows']==4
    assert out['summary']['counts']['latent_nonzero_halted_rows']==4
    assert out['events'].iloc[0].successor=='permanently_halted'
    tail=out['daily'].iloc[20:]
    assert (tail.applied_risk_proxy==0).all()
    assert (tail.latent_risk_proxy > 0).all()


def stop_fixture(next_weight=.5, next_halted=False, n=3):
    dates = pd.date_range('2023-01-01', periods=n)
    return pd.DataFrame(dict(date=dates, price_stop_hit=[True]*n,
        portfolio_stop_hit=[False]*n, stop_outside_envelope=[False]*n,
        applied_weight=[.5]+[next_weight]*(n-1), latent_target=[.5]*n,
        halted_after=[next_halted]*n, halted_before=[False]+[next_halted]*(n-1),
        sizing_date=['2022-12-20T00:00:00']*n, bars_since_sizing=np.arange(12,12+n),
        entry_fee_dollars=np.arange(1., n+1), entry_impact_dollars=[.1]*n,
        exit_fee_dollars=[1.]*n, exit_impact_dollars=[.1]*n,
        entry_price=[100.]*n, mark_price=[97.]*n,
        gross_dollars=[-1.]*n, funding_dollars=[-.1]*n))


def test_stop_records_both_stop_and_reentry_sizing_age_without_reset():
    events=module().stop_events(stop_fixture())
    assert events.iloc[0].bars_since_sizing==12
    assert events.iloc[0].next_bars_since_sizing==13
    assert events.iloc[0].next_sizing_date=='2022-12-20T00:00:00'
    assert pd.isna(events.iloc[-1].next_bars_since_sizing)


@pytest.mark.parametrize('weight,halted,kind', [(.5, False, 'same_sign_reentry'),
    (-.5, False, 'opposite_sign_entry'), (0, False, 'flat'), (0, True, 'permanently_halted')])
def test_price_stop_successor_classes_and_unique_next_entry_charges(weight, halted, kind):
    out = module().stop_events(stop_fixture(weight, halted))
    assert out.iloc[0].successor == kind
    assert out.iloc[-1].successor == 'end_of_window_censored'
    if weight:
        assert out.next_entry_fee_dollars.sum() == 5
        assert out.iloc[0].reused_sizing_reference
        assert out.iloc[1].repeated_stop_chain
    else:
        assert out.next_entry_fee_dollars.sum() == 0


def stage_fixture(gross, entry_fee, exit_fee, price_stop, portfolio_stop, halted):
    nav=100.; rows=[]
    for g, ef, xf, ps, ph, h in zip(gross, entry_fee, exit_fee, price_stop, portfolio_stop, halted):
        after=nav+g-ef-xf
        rows.append(dict(date=pd.Timestamp('2023-01-01')+pd.Timedelta(days=len(rows)),
            nav_before=nav, nav_after=after, gross_dollars=g, funding_dollars=0.,
            entry_fee_dollars=ef, entry_impact_dollars=0., exit_fee_dollars=xf,
            exit_impact_dollars=0., price_stop_hit=ps, portfolio_stop_hit=ph,
            halted_after=h, halted_before=bool(rows and rows[-1]['halted_after'])))
        nav=after
    return pd.DataFrame(rows)


def test_staged_peak_includes_pre_exit_peak_and_attributes_from_that_stage():
    trace=stage_fixture([10., -14.], [0., 0.], [1., 2.], [True, True], [False, False], [False, True])
    out=module().staged_accounting(trace, initial_nav=100.)
    halt=out['first_halt']
    assert halt['peak_nav'] == 110
    assert halt['peak_stage'] == 'pre_exit'
    assert halt['crossing_stage'] == 'post_exit'
    assert halt['peak_to_halt_components']['gross_dollars'] == -14
    assert halt['peak_to_halt_components']['fee_dollars'] == 3
    assert halt['peak_to_halt_components']['net_dollars'] == -17


def test_pre_exit_halt_is_distinct_from_post_exit_threshold_crossing():
    trace=stage_fixture([-16.], [0.], [1.], [False], [True], [True])
    out=module().staged_accounting(trace, initial_nav=100.)
    assert out['first_halt']['crossing_stage'] == 'pre_exit'
    assert out['first_halt']['pre_exit_drawdown'] == pytest.approx(.16)
    assert out['first_halt']['post_exit_drawdown'] == pytest.approx(.17)


def test_recorded_halt_flags_must_match_staged_threshold():
    trace=stage_fixture([-1.], [0.], [0.], [False], [False], [True])
    with pytest.raises(ValueError, match='halt'):
        module().staged_accounting(trace, initial_nav=100.)
