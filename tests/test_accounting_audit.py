"""Synthetic accounting counterexamples; no market stores or registry writes."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from tradingagents.predlab import opt, pp
from tradingagents.xsect import portfolio, trend, carry_xs, combo, liq_fade, ls_common
from tradingagents.backtesting.engine import compute_metrics

ROOT = Path(__file__).resolve().parents[1]


def panels(n=3):
    ix = pd.date_range('2024-01-01', periods=n, tz='UTC')
    cols = [f'S{i:02}' for i in range(30)]
    sig = pd.DataFrame(np.tile(np.arange(30.), (n, 1)), index=ix, columns=cols)
    ret = pd.DataFrame(0., index=ix, columns=cols)
    return ix, cols, sig, ret, pd.DataFrame(True, index=ix, columns=cols)


def load_functions(path, names, ns):
    tree = ast.parse((ROOT / path).read_text())
    body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=body, type_ignores=[]), path, 'exec'), ns)
    return ns


@pytest.mark.parametrize('metric', [pp.max_drawdown, combo.maxdd_simple, portfolio.maxdd])
def test_drawdown_counts_loss_from_initial_capital(metric):
    assert metric(pd.Series([-.2, 0., 0.])) == pytest.approx(.2)
    assert metric(pd.Series([], dtype=float)) == 0.


@pytest.mark.parametrize('caller,engine,freq', [('run_s2_dev','run_s2','D'), ('run_s3_dev','run_s3','h')])
def test_strategy_callers_convert_stored_log_returns(caller, engine, freq):
    ix = pd.date_range('2024-01-01', periods=40, freq=freq, tz='UTC')
    expected = pd.Series(np.tile([.1, -.095], 20), index=ix)
    store = pd.DataFrame({'ret': np.log1p(expected), 'rv': .04/365}, index=ix)
    captured = []
    def boundary(_forecast, returns, *args):
        captured.append(returns)
        raise StopIteration
    ns = load_functions('scripts/predlab_pp_dev.py', {caller},
        dict(pd=pd, np=np, DATA_ROOT=Path('/unused'), DEV=('2024-01-01','2024-12-31'),
             pp=SimpleNamespace(**{engine: boundary}),
             _load_fc=lambda *args: pd.DataFrame({'pred': .8}, index=ix)))
    with patch.object(pd, 'read_parquet', return_value=store), pytest.raises(StopIteration):
        ns[caller]()
    np.testing.assert_allclose(captured[0], expected, rtol=1e-13)


def test_s2_charges_initial_entry():
    ix = pd.date_range('2024-01-01', periods=21, tz='UTC')
    result = pp.run_s2(pd.Series(.04/365,index=ix), pd.Series(0.,index=ix))
    assert result['rets'].iloc[0] == pytest.approx(-.0005)


@pytest.mark.parametrize('fast', [False, True])
def test_weekly_engine_holds_units_between_rebalances(fast):
    ix = pd.date_range('2024-01-01', periods=3, tz='UTC')
    kl = {s: pd.DataFrame({'close': p}, index=ix) for s,p in
          {'A':[100.,110.,121.], 'B':[100.,100.,100.]}.items()}
    reb = ix[:1]
    if fast:
        result = portfolio.fast_weekly_portfolio({ix[0]: ['A','B']}, reb,
            *portfolio.build_fast_arrays(kl), cost_bps=0.)
    else:
        result = portfolio.run_weekly_portfolio(kl, reb, lambda _: ['A','B'], cost_bps=0.)
    assert (1+result).prod() == pytest.approx(1.105)
    assert result.iloc[1] == pytest.approx(1.105/1.05-1)


def test_opt_cadence_holds_contracts():
    ix, cols, sig, ret, uni = panels()
    ret.loc[ix[1]:, cols[0]] = .1
    result = opt.run_ls(sig, ret, uni, None, opt.OptConfig(cadence=3,taker_bp=0.), str(ix[0].date()),str(ix[-1].date()))
    assert (1+result['rets'].net).prod() == pytest.approx(1.035)
    assert result['rets'].turnover.tolist() == pytest.approx([2., 0., 0.])


@pytest.mark.parametrize('engine', ['s1', 'opt'])
def test_missing_signal_retains_exposure_and_clock(engine):
    ix, cols, sig, ret, uni = panels()
    sig.loc[ix[1]] = np.nan
    ret.loc[ix[1], cols[:6]] = -.1
    with patch.object(pp, 'TAKER_BP', 0.):
        result = (pp.run_s1(sig,ret,uni,None,'eq',1,'2024-01-01','2024-01-03') if engine=='s1'
                  else opt.run_ls(sig,ret,uni,None,opt.OptConfig(taker_bp=0.),'2024-01-01','2024-01-03'))
    assert result['rets'].index.equals(ix)
    assert result['rets'].loc[ix[1], 'net'] == pytest.approx(-.1)


@pytest.mark.parametrize('engine', ['s1', 'opt'])
def test_missing_held_return_fails_explicitly(engine):
    ix, cols, sig, ret, uni = panels()
    ret.loc[ix[1], cols[0]] = np.nan
    with pytest.raises(ValueError, match='missing_held_return.*S00'):
        if engine == 's1':
            pp.run_s1(sig,ret,uni,None,'eq',1,'2024-01-01','2024-01-03')
        else:
            opt.run_ls(sig,ret,uni,None,opt.OptConfig(),'2024-01-01','2024-01-03')


@pytest.mark.parametrize('engine', ['trend','carry'])
def test_daily_rebalance_charges_actual_drifted_turnover(engine):
    ix = pd.date_range('2024-01-01',periods=3,tz='UTC')
    w = pd.DataFrame({'A': .5, 'B': .5},index=ix)
    r = pd.DataFrame({'A': [0.,.1,0.], 'B': 0.},index=ix)
    if engine == 'trend':
        result = trend.run_daily_portfolio(w,r,cost_bps=100.)
    else:
        result = carry_xs.run_ls_portfolio(w,r,r*0,cost_bps=100.,rf_daily=0.)
    # Initial fee .01, gain .05 => NAV1=1.04; notionals .55/.50.
    # Next targets .52/.52; turnover dollars=.03+.02=.05; fee=.0005.
    assert result.iloc[1] == pytest.approx(-.0005/1.04)


def test_weekly_ls_metadata_preserves_declared_cadence():
    ix = pd.date_range('2024-01-01',periods=3,tz='UTC')
    s = pd.DataFrame(np.tile(np.arange(6.),(3,1)),index=ix,columns=list('ABCDEF'))
    w = ls_common.ls_weights(ix,s,s.notna(),ix[:1],.2)
    r = pd.DataFrame(0.,index=ix,columns=s.columns)
    r.loc[ix[1]:,'A'] = .1
    result = carry_xs.run_ls_portfolio(w,r,r*0,cost_bps=0.,rf_daily=0.)
    assert (1+result).prod() == pytest.approx(1.105)


def test_hourly_returns_compound_to_daily_nav():
    ix = pd.date_range('2024-01-01',periods=2,freq='h',tz='UTC')
    w = pd.DataFrame({'A':[1.,1.]},index=ix)
    r = pd.DataFrame({'A':[1.,-.5]},index=ix)
    assert liq_fade.run_hourly_portfolio(w,r,cost_bps=0.,rf_annual=0.).iloc[0] == pytest.approx(0.)


def test_missing_calendar_day_does_not_disappear_with_held_book():
    ix, cols, sig, ret, uni = panels()
    ret = ret.drop(ix[1])
    with pytest.raises(ValueError,match='missing_held_return'):
        opt.run_ls(sig,ret,uni,None,opt.OptConfig(),'2024-01-01','2024-01-03')


def test_calendar_sharpe_includes_inactive_days():
    returns = [.01,.03]+[0.]*8
    result = compute_metrics(returns,[1.,1.]+[0.]*8,1.,[1.]+np.cumprod(1+np.array(returns)).tolist(),risk_free_rate=0.)
    assert result['sharpe_ratio'] == pytest.approx(7.910214072718)


@pytest.mark.parametrize('script', ['predlab_correction_aug24.py','predlab_champion_backtest.py'])
def test_overlay_does_not_charge_underlying_fee_twice(script):
    ix = pd.date_range('2024-01-01',periods=40,tz='UTC')
    base = pd.DataFrame({'net':np.tile([.01,-.01],20)-.0005,'turnover':1.},index=ix)
    ns = load_functions('scripts/'+script, {'overlay_o4'},dict(pd=pd,np=np,ANN_DAYS=365.,TAKER_BP=5.))
    result = ns['overlay_o4'](base,pd.Series(200.,index=ix),target=.15)
    if isinstance(result,tuple): result = result[0]
    scale = .15/(base.net.rolling(20).std().shift(1)*np.sqrt(365))
    # At day25 scale is unchanged: only existing scaled underlying fees apply.
    assert result.iloc[25] == pytest.approx(scale.iloc[25]*base.net.iloc[25])


def test_helper_postfee_exposure_funding_and_drift_are_explicit():
    from tradingagents.accounting import accounting_step
    row = accounting_step(100.,pd.Series({'A':50.,'B':-50.}),
        pd.Series({'A':.1,'B':-.1}),target_weights=pd.Series({'A':.5,'B':-.5}),
        funding=pd.Series({'A':.01,'B':.02}),fee_rate=.001)
    assert row['nav'] == pytest.approx(110.5)
    assert row['carry'] == pytest.approx(.005)
    assert row['notionals'].to_dict() == pytest.approx({'A':55.,'B':-45.})
    entry = accounting_step(100.,pd.Series(dtype=float),pd.Series({'A':0.}),
        target_weights=pd.Series({'A':1.}),fee_rate=.01)
    assert entry['nav'] == 99.
    assert entry['postfee_weights']['A'] == pytest.approx(100/99)


def test_overlay_executes_scaled_contracts_and_actual_turnover():
    from tradingagents.accounting import run_target_book
    ix = pd.date_range('2024-01-01',periods=3,tz='UTC')
    base = run_target_book(pd.DataFrame({'A':1.},index=ix),
                          pd.DataFrame({'A':[.1,0.,0.]},index=ix),fee_rate=.01)
    # Volatility target tuned to obtain half exposure at final timestamp.
    # The shared helper is the production boundary used by all four scripts.
    from tradingagents.accounting import scaled_overlay
    result = scaled_overlay(base,pd.Series(.5,index=ix),fee_rate=.01)
    assert result.iloc[0] == pytest.approx(.045)
    # .55 current A -> desired .5225: sell .0275, fee .000275 / NAV1.045.
    assert result.iloc[1] == pytest.approx(-.000275/1.045)


def test_thin_ls_keeps_unavailable_signal_day_and_held_loss():
    ns = load_functions('scripts/predlab_xfam_lib.py', {'thin_ls_backtest'},dict(pd=pd,np=np,TAKER_BP=5.))
    ix = pd.date_range('2024-01-01',periods=3,tz='UTC')
    sig = pd.DataFrame(np.tile([0.,1.,2.,3.],(3,1)),index=ix,columns=list('ABCD'))
    sig.loc[ix[1]] = np.nan
    ret = pd.DataFrame(0.,index=ix,columns=sig.columns)
    ret.loc[ix[1],'D'] = -.1
    result = ns['thin_ls_backtest'](sig,ret,n_leg=1,taker_bp=0.)
    assert result.index.equals(ix)
    assert result.loc[ix[1],'net'] == pytest.approx(-.1)


def v2_result(prices,positions,**kwargs):
    ns = load_functions('scripts/baseline_strategy_v2.py', {'run_coin_backtest'},dict(np=np,pd=pd))
    args = dict(dates=pd.date_range('2024-01-01',periods=len(prices)),prices=np.array(prices),
        positions=np.array(positions),initial_capital=1.,fee_rate=0.,slippage=0.,spread=0.,
        price_impact=0.,funding_rate=0.,stop_loss=2.,max_portfolio_dd=2.)
    args.update(kwargs)
    return ns['run_coin_backtest'](**args)


def test_v2_short_receives_signed_positive_funding():
    equity,_ = v2_result([100.,100.],[0.,-1.],funding_rate=.01)
    assert equity[-1] == pytest.approx(1.01)


def test_v2_charges_one_fee_on_actual_notional_change():
    equity,_ = v2_result([100.,110.,110.],[0.,.5,.5],fee_rate=.01)
    # Fee .005 + gain .05 -> NAV1.045; next target .5225 vs held .55.
    assert equity == pytest.approx([1.,1.045,1.044725])


def test_v2_marks_missing_held_price_as_incomplete():
    with pytest.raises(ValueError,match='missing_held_return'):
        v2_result([100.,100.,np.nan],[0.,1.,1.])


def test_classic_engine_charges_entry_and_actual_drift_maintenance_once():
    from tradingagents.backtesting.engine import run_backtest
    from tradingagents.backtesting.strategies import FiveLevelSignal
    result = run_backtest(pd.Series(pd.date_range('2024-01-01',periods=3)),
        np.array([100.,110.,110.]),['OVERWEIGHT']*3,FiveLevelSignal(),
        initial_capital=1.,fee_rate=.01,slippage=0.,short_cost=0.)
    assert result.equity_curve == pytest.approx([1.,1.045,1.044725])


def test_v2_price_stop_closes_actual_contracts_with_one_exit_fee():
    equity,_ = v2_result([100.,90.],[0.,1.],fee_rate=.01,price_stop_pct=.05,
                         highs=np.array([100.,100.]),lows=np.array([100.,90.]))
    assert equity[-1] == pytest.approx(.9305)


def test_v2_equity_stop_charges_close_at_actual_mark():
    equity,_ = v2_result([100.,90.],[0.,1.],fee_rate=.01,stop_loss=.05)
    assert equity[-1] == pytest.approx(.881)


def test_cost_stress_replays_fee_changed_nav_with_held_contracts():
    ix,cols,sig,ret,uni = panels()
    ret.loc[ix[1]:,cols[0]] = .1
    result = opt.run_ls(sig,ret,uni,None,opt.OptConfig(cadence=3,taker_bp=100.),
                        '2024-01-01','2024-01-03')
    # Initial fees .04 under 2x costs; same initial units gain .035 thereafter.
    assert (1+opt.cost_stress(result,2.)).prod() == pytest.approx(.995)


def test_o8_overlay_does_not_repeat_base_fees():
    ix=pd.date_range('2024-01-01',periods=3,tz='UTC')
    ns=load_functions('scripts/predlab_opt_o8.py',{'overlay_book'},dict(pd=pd,np=np,
        OVL={'target':.15,'cap':2.,'breadth_floor':100,'est':'unused'},
        sigma_hat=lambda net,est: pd.Series(.3,index=net.index)))
    result,_=ns['overlay_book'](pd.Series(.01,index=ix),pd.Series(1.,index=ix),pd.Series(200.,index=ix))
    assert result.iloc[1] == pytest.approx(.005)


def test_o8_drawdown_includes_initial_capital():
    ns=load_functions('scripts/predlab_opt_o8.py',{'stats'},dict(pd=pd,np=np))
    ix=pd.date_range('2024-01-01',periods=3,tz='UTC')
    _,dd=ns['stats'](pd.Series([-.2,0.,0.],index=ix),'2024-01-01','2024-01-03')
    assert dd == pytest.approx(.2)


def test_supplied_missing_funding_fails_for_held_position():
    from tradingagents.accounting import accounting_step
    with pytest.raises(ValueError,match='missing_held_funding'):
        accounting_step(1.,pd.Series(dtype=float),pd.Series({'A':0.}),
            target_weights=pd.Series({'A':1.}),funding=pd.Series({'A':np.nan}))


def test_target_without_return_column_is_not_dropped():
    from tradingagents.accounting import run_target_book
    ix=pd.date_range('2024-01-01',periods=1,tz='UTC')
    with pytest.raises(ValueError,match='missing_held_return.*B'):
        run_target_book(pd.DataFrame({'B':1.},index=ix),pd.DataFrame({'A':0.},index=ix))


def test_overlay_preserves_declared_capital_charge():
    from tradingagents.accounting import run_target_book,scaled_overlay
    ix=pd.date_range('2024-01-01',periods=2,tz='UTC')
    base=run_target_book(pd.DataFrame({'A':1.},index=ix),pd.DataFrame({'A':0.},index=ix),capital_charge=.01)
    net=scaled_overlay(base,pd.Series(.5,index=ix),fee_rate=0.)
    assert net.tolist() == pytest.approx([-.01,-.01])


def test_hourly_daily_capital_charge_changes_next_day_trade_nav():
    ix=pd.date_range('2024-01-01',periods=48,freq='h',tz='UTC')
    w=pd.DataFrame({'A':.5},index=ix)
    r=pd.DataFrame({'A':0.},index=ix)
    net=liq_fade.run_hourly_portfolio(w,r,cost_bps=100.,rf_annual=1.1**365-1.)
    # Entry + maintenance fees form the series .005 + .000025 + ...;
    # day1 ends .8949748743718593 after its .1 charge. Day2's .05 notional
    # reduction plus fee maintenance costs .000502512562814; its charge
    # is .0894974874371859. The final dollar NAV is independently derived.
    assert (1+net).prod() == pytest.approx(.8049748743718592)


@pytest.mark.parametrize('shift', ['combo_shared','combo_independent','trend_shared','trend_independent'])
def test_placebo_transform_preserves_weekly_execution_cadence(shift):
    ix=pd.date_range('2024-01-01',periods=6,tz='UTC')
    s=pd.DataFrame(np.tile(np.arange(6.),(6,1)),index=ix,columns=list('ABCDEF'))
    w=ls_common.ls_weights(ix,s,s.notna(),ix[:1],.2)
    if shift=='combo_shared': shifted=combo.shared_shift(w,0)
    elif shift=='combo_independent': shifted=combo.indep_shift(w,np.random.default_rng(0),1)
    elif shift=='trend_shared': shifted=trend.shared_shift_weights(w,np.random.default_rng(0),1)
    else: shifted=trend.circular_shift_weights(w,np.random.default_rng(0),1)
    r=pd.DataFrame(0.,index=ix,columns=s.columns)
    r.loc[ix[1:3],'A']=.1
    net=carry_xs.run_ls_portfolio(shifted,r,r*0,cost_bps=0.,rf_daily=0.)
    assert (1+net).prod() == pytest.approx(1.105)


def test_opt_selected_name_missing_return_column_fails():
    ix,cols,sig,ret,uni=panels()
    with pytest.raises(ValueError,match='missing_held_return.*S00'):
        opt.run_ls(sig,ret.drop(columns=cols[0]),uni,None,opt.OptConfig(),
                   '2024-01-01','2024-01-03')


def test_archive_returns_preserves_values_and_light_metadata(tmp_path):
    from tradingagents.accounting import run_target_book,archive_returns
    ix=pd.date_range('2024-01-01',periods=3,tz='UTC')
    base=run_target_book(pd.DataFrame({'A':.5},index=ix),
        pd.DataFrame({'A':[.1,0.,-.1]},index=ix),fee_rate=.01)
    path=tmp_path/'synthetic.parquet'
    archive_returns(base).to_parquet(path)
    loaded=pd.read_parquet(path)
    np.testing.assert_allclose(loaded.net,base.net,atol=1e-14)
    assert loaded.attrs['accounting_version']=='pretrade-nav-v1'
    assert 'accounting_inputs' not in loaded.attrs
    assert 'accounting_inputs' in base.attrs
