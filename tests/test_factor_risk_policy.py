"""Synthetic policy/engine proofs; no saved strategy observations are loaded."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.baseline_strategy_v2 import run_coin_backtest
from tradingagents.strategies.v2_sizing import compute_realized_vol

ROOT=Path(__file__).resolve().parents[1]


def module():
    path=ROOT/'tradingagents/strategies/factor_risk_policy.py'
    assert path.exists(), 'registered factor risk policy has not been implemented'
    spec=importlib.util.spec_from_file_location('factor_policy_test',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def controller(n=8, sizing='saved',reentry='new_target_episode',sigma=None):
    return module().FactorRiskPolicy(sizing=sizing,reentry=reentry,
        sigma=np.full(n,.3) if sigma is None else sigma)


def engine_args(prices,raw,**overrides):
    prices=np.asarray(prices,dtype=float)
    args=dict(dates=pd.date_range('2024-01-01',periods=len(prices),tz='UTC'),
        prices=prices,positions=np.asarray(raw,dtype=float),initial_capital=100.,
        fee_rate=.001,slippage=.0005,spread=.0001,price_impact=.00005,
        funding_rate=.0003,stop_loss=1.,max_portfolio_dd=1.,take_profit=0.,
        price_stop_pct=.03,highs=prices.copy(),lows=prices.copy())
    return args|overrides


def archived_engine():
    path=ROOT/'docs/risk-policy-2026-09-10/original/baseline_strategy_v2.py'
    spec=importlib.util.spec_from_file_location('archived_factor_engine',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.run_coin_backtest


def test_daily_sigma_uses_original_estimator_and_exact_once_lag():
    close=np.exp(np.arange(50)**2/10000)
    got=module().causal_sigma(close)
    want=compute_realized_vol(np.r_[close[0],close[:-1]],20)
    np.testing.assert_array_equal(got,want)
    changed=close.copy(); changed[31:]*=2
    np.testing.assert_array_equal(got[:32],module().causal_sigma(changed)[:32])
    assert np.isnan(got[:20]).all()


@pytest.mark.parametrize('side',[1,-1])
def test_daily_sizing_preserves_direction_refreshes_size_and_clips(side):
    p=controller(sizing='daily',sigma=[np.nan,.30,.15,.01])
    assert p.decide(1,side*.7,False)[0]==pytest.approx(side*.5)
    assert p.decide(2,side*.7,False)[0]==pytest.approx(side*1.)
    assert p.decide(3,side*.7,False)[0]==pytest.approx(side*3.)


@pytest.mark.parametrize('invalid',[np.nan,np.inf,-np.inf,0.,-.2])
def test_required_bad_sigma_is_explicit_unavailable_with_date(invalid):
    p=controller(sizing='daily',sigma=[np.nan,invalid])
    with pytest.raises(ValueError,match='2024-01-02.*sigma'):
        p.decide(1,.5,False,date=pd.Timestamp('2024-01-02',tz='UTC'))


def test_flat_blocked_and_halted_requests_do_not_require_sigma():
    p=controller(sizing='daily',sigma=[np.nan,np.nan,.3,np.nan,np.nan])
    assert p.decide(1,0.,False)[0]==0
    assert p.decide(2,.5,False)[0]==.5
    p.on_price_stop(2,.5)
    weight,meta=p.decide(3,.5,False)
    assert weight==0 and meta['decision_blocked']
    weight,meta=p.decide(4,-.5,True)
    assert weight==0 and meta['decision_reason']=='permanent_halt'
    assert meta['blocked_before']==meta['blocked_after']==1


def test_block_is_raw_direction_based_and_releases_on_opposite_same_bar():
    p=controller()
    _,m=p.decide(1,.5,False)
    assert m['blocked_before']==m['blocked_after_decision']==m['blocked_after']==0
    update=p.on_price_stop(1,.5)
    assert update['blocked_after']==update['stopped_direction']==1
    weight,m=p.decide(2,.9,False)
    assert weight==0 and m['decision_blocked'] and m['raw_target']==.9
    weight,m=p.decide(3,-.4,False)
    assert weight==-.4 and m['block_release']=='raw_opposite'
    assert m['blocked_before']==1 and m['blocked_after']==0
    p.on_price_stop(3,-.4)
    assert p.decide(4,-.6,False)[0]==0


def test_raw_flat_releases_but_suppressed_zero_does_not_self_release():
    p=controller()
    p.decide(1,.5,False);p.on_price_stop(1,.5)
    assert p.decide(2,.5,False)[0]==0
    assert p.decide(3,.5,False)[0]==0
    target,meta=p.decide(4,0.,False)
    assert target==0 and meta['block_release']=='raw_flat'
    assert p.decide(5,.5,False)[0]==.5


def test_immediate_policy_records_stops_without_blocking():
    p=controller(reentry='immediate')
    p.decide(1,.5,False)
    assert p.on_price_stop(1,.5)==dict(stopped_direction=1,blocked_after=0)
    assert p.decide(2,.5,False)[0]==.5


@pytest.mark.parametrize('raw',[np.nan,np.inf,True,'0.5'])
def test_malformed_raw_target_never_becomes_retained_holdings_or_a_reset(raw):
    with pytest.raises(ValueError,match='raw target'):
        controller().decide(1,raw,False)


def test_controller_rejects_reused_out_of_order_and_false_stop_notifications():
    p=controller()
    with pytest.raises(ValueError,match='decision'):
        p.on_price_stop(1,.5)
    p.decide(1,0.,False)
    with pytest.raises(ValueError,match='nonzero'):
        p.on_price_stop(1,.5)
    with pytest.raises(ValueError,match='order'):
        p.decide(1,.5,False)
    p.decide(2,.5,False);p.on_price_stop(2,.5)
    with pytest.raises(ValueError,match='already'):
        p.on_price_stop(2,.5)


@pytest.mark.parametrize('side',[1,-1])
@pytest.mark.parametrize('scale,funding',[(1.,.0003),(0.,.0003),(2.,.0003),(1.,0.)])
def test_default_none_and_explicit_a00_match_archived_original_fields(side,scale,funding):
    args=engine_args([100,101,96,105,103,90],[0,.8*side,.8*side,-.5*side,-.5*side,.5*side],
        fee_rate=.0004*scale,slippage=.0005*scale,spread=.0001*scale,
        price_impact=.00005*scale,funding_rate=funding,max_portfolio_dd=.15)
    old_trace=[]; want=archived_engine()(**args,trace=old_trace)
    none_trace=[]; got=run_coin_backtest(**args,trace=none_trace)
    assert got==want and none_trace==old_trace
    trace=[]; got=run_coin_backtest(**args,target_policy=controller(n=6,reentry='immediate'),trace=trace)
    assert got==want
    assert [{k:row[k] for k in old_trace[0]} for row in trace]==old_trace
    assert all(row['blocked_before']==row['blocked_after']==0 for row in trace)
    json.dumps(trace,allow_nan=False)


@pytest.mark.parametrize('side,prices,lows,highs',[
    (1,[100,102,101,96],[100,101,98,96],[100,103,103,102]),
    (-1,[100,98,99,104],[100,97,97,98],[100,99,102,104])])
def test_same_sign_daily_resize_keeps_original_price_stop_anchor(side,prices,lows,highs):
    trace=[]
    args=engine_args(prices,[0,side,side,side],lows=np.array(lows,dtype=float),highs=np.array(highs,dtype=float))
    run_coin_backtest(**args,trace=trace,target_policy=controller(sizing='daily',reentry='immediate',sigma=[np.nan,.3,.15,.2]))
    assert [r['entry_price'] for r in trace]==[100,100,100]
    assert not trace[1]['price_stop_hit']
    assert trace[2]['price_stop_hit']
    assert trace[2]['mark_price']==(97 if side==1 else 103)
    assert trace[2]['exposure']==pytest.approx(.75*side)
    assert trace[2]['exit_notional']==pytest.approx(trace[2]['nav_before']*.75*side*(1+trace[2]['mark_return']))


def test_waiting_updates_after_executed_stop_with_or_without_trace():
    args=engine_args([100,96,95,94,93],[0,.5,.5,0,.5])
    trace=[]; got=run_coin_backtest(**args,trace=trace,target_policy=controller(n=5))
    plain=run_coin_backtest(**args,target_policy=controller(n=5))
    assert got==plain
    assert trace[0]['requested_target']==.5 and trace[0]['blocked_after_decision']==0
    assert trace[0]['price_stop_hit'] and trace[0]['blocked_after']==1
    assert trace[1]['decision_reason']=='waiting_same_direction'
    assert trace[1]['exposure']==trace[1]['closing_notional']==trace[1]['fee_dollars']==0
    assert trace[2]['block_release']=='raw_flat'
    assert trace[3]['exposure']==.5 and trace[3]['entry_price']==94


def test_permanent_halt_beats_opposite_reset_and_requires_no_sigma_in_tail():
    args=engine_args([100,90,120],[0,3,-3],fee_rate=.03,slippage=0,spread=0,price_impact=0,
                     funding_rate=0,max_portfolio_dd=.15)
    trace=[]
    run_coin_backtest(**args,trace=trace,target_policy=controller(sizing='daily',sigma=[np.nan,.05,np.nan]))
    assert trace[0]['halted_after']
    assert trace[1]['decision_reason']=='permanent_halt'
    assert trace[1]['exposure']==trace[1]['fee_dollars']==trace[1]['funding_dollars']==0
    assert trace[1]['nav_before']==trace[1]['nav_after']


@pytest.mark.parametrize('last',[90.,110.])
def test_planted_resize_waiting_tradeoff_does_not_presume_economic_improvement(last):
    args=engine_args([100,97,last],[0,1,1],fee_rate=0,slippage=0,spread=0,
                    price_impact=0,funding_rate=0)
    results={}
    for sizing in ('saved','daily'):
        for reentry in ('immediate','new_target_episode'):
            results[sizing,reentry]=run_coin_backtest(**args,target_policy=controller(n=3,sizing=sizing,reentry=reentry))[0][-1]
    if last==110:
        assert results['saved','immediate'] > results['saved','new_target_episode']
        assert results['saved','immediate'] > results['daily','immediate']
    else:
        assert results['saved','immediate'] < results['saved','new_target_episode']
        assert results['saved','immediate'] < results['daily','immediate']


@pytest.mark.parametrize('bad',[np.nan,np.inf,True,'1',1j,None])
def test_hook_refuses_nonfinite_output_instead_of_legacy_hold_fallback(bad):
    class Broken:
        def decide(self,*args,**kwargs):return bad,{}
    with pytest.raises(ValueError,match='policy target'):
        run_coin_backtest(**engine_args([100,110],[0,1]),target_policy=Broken())


@pytest.mark.parametrize('side,prices,nav1,held1',[(1,[100,110,121],103.85,55.),(-1,[100,90,81],104.15,-45.)])
def test_daily_resizing_charges_actual_drifted_delta_once_with_signed_funding(side,prices,nav1,held1):
    trace=[]
    run_coin_backtest(**engine_args(prices,[0,side,side],fee_rate=.01,slippage=0,spread=0,
        price_impact=.02,funding_rate=.003),trace=trace,
        target_policy=controller(sizing='daily',reentry='immediate',sigma=[np.nan,.3,.15]))
    first,second=trace
    assert first['nav_after']==pytest.approx(nav1)
    assert first['closing_notional']==pytest.approx(held1)
    turnover=abs(nav1*side-held1)
    assert second['entry_turnover_dollars']==pytest.approx(turnover)
    assert second['entry_fee_dollars']==pytest.approx(.01*turnover)
    assert second['entry_impact_dollars']==pytest.approx(.02*turnover**2/nav1)
    assert second['funding_dollars']==pytest.approx(-side*.003*nav1)
    for row in trace:
        assert row['nav_after']-row['nav_before']==pytest.approx(row['gross_dollars']+row['funding_dollars']-row['fee_dollars']-row['impact_dollars'])


def test_post_exit_fee_halt_is_retained_before_policy_can_release_block():
    trace=[]
    run_coin_backtest(**engine_args([100,97,120],[0,3,-3],fee_rate=.0102,slippage=0,
        spread=0,price_impact=0,funding_rate=0,max_portfolio_dd=.15),trace=trace,
        target_policy=controller(sizing='daily',sigma=[np.nan,.05,np.nan]))
    first,tail=trace
    assert first['price_stop_hit'] and not first['portfolio_stop_hit'] and first['halted_after']
    assert first['nav_after']==pytest.approx(84.9718)
    assert first['blocked_after']==1
    assert tail['raw_target']==-3 and tail['decision_reason']=='permanent_halt'
    assert tail['requested_target']==0 and tail['block_release'] is None


def test_new_controllers_are_isolated_and_copy_sigma_inputs():
    sigma=np.array([np.nan,.3,.3])
    first=controller(sizing='daily',sigma=sigma);second=controller(sizing='daily',sigma=sigma)
    sigma[1]=np.nan
    assert first.decide(1,.5,False)[0]==.5
    first.on_price_stop(1,.5)
    assert first.decide(2,.5,False)[0]==0
    assert second.decide(1,.5,False)[0]==.5


def test_hook_cannot_overwrite_original_accounting_fields_or_release_halt():
    class Overwrite:
        def decide(self,*a,**kw):return .5,{'nav_after':0.}
    with pytest.raises(ValueError,match='overwrite'):
        run_coin_backtest(**engine_args([100,101],[0,.5]),trace=[],target_policy=Overwrite())
    class Restart:
        def decide(self,*a,**kw):return 1.,{}
        def on_price_stop(self,*a):return {}
    with pytest.raises(ValueError,match='permanent halt'):
        run_coin_backtest(**engine_args([100,80,120],[0,1,1],price_stop_pct=0,max_portfolio_dd=.15),target_policy=Restart())
