"""Invented full-year policy/benchmark books and deterministic stress checks."""
from decimal import Decimal as D
import importlib.util
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[2]/'research/broader-allocation-2026-09-15/conditional_book.py'
s=importlib.util.spec_from_file_location('tested_conditional_book',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def panel(vary=False):
    rows=[]
    for i in range(566):
        price=str(100+(i%7 if vary else 0))
        rows.append({'open_epoch':m.START-200*m.DAY+i*m.DAY,
                     'btc_bars':{'open':price,'close':price},'eth_bars':{'open':'50','close':'50'},'usd_bars':{'open':'1','close':'1'}})
    for a in ('btc_bars','eth_bars','usd_bars'):rows[-1][a].pop('close')
    return {'joined':rows}


def test_cash_does_not_pay_fictional_trading_fees():
    r=m.run_book(panel(),'B0','primary')
    assert r['net_cash_profit_usd']=='-10' and r['trade_count']==0
    assert D(r['cash_attribution']['commission_usd'])==0 and r['cash_days']==365
    assert r['stress']['total-binance-loss']['loss_fraction']=='1'
    assert D(r['stress']['stable-depeg-redemption-lock']['loss_fraction'])>D('.2')


def test_buy_hold_literal_round_trip_and_full_capital():
    r=m.run_book(panel(),'B9','frictionless')
    assert D(r['net_cash_profit_usd'])==D('-10') and r['trade_count']==2
    assert r['events'][0]['id']=='month-'+str(m.START+m.DAY)+'-BTC-buy'
    assert r['events'][-2]['id']=='terminal-BTC'
    assert D(r['mean_crypto_fraction'])<D('.251')
    assert D(r['log_convention_diagnostic']['difference_usd'])==0


def test_rebalance_stress_takes_profit_before_crash():
    b=m.m.SpotBook({('cex','USDC'):'7500',('cex','BTC'):'25'})
    p={'USDC':D(1),'BTC':D(100),'ETH':D(50)}
    r=m.stress_at(b,p,'frictionless',m.START+m.DAY,'H2',[D(100)]*201)
    # NAV includes $10 remaining route fee. Doubled gross12500; target25% of12490.
    # BTC31.225? 3122.5/200=15.6125; cash9377.5; down BTC value1249; final10616.5.
    assert D(r['double-then-minus60']['nav'])==D('10616.5000')
    assert r['double-then-minus60']['intervening_actions']==1
    assert D(r['crypto-minus80']['nav'])==D('7990')


def test_all_four_strategies_on_invented_varying_prices():
    for policy in ('H2','H3','H4','H5'):
        r=m.run_book(panel(True),policy,'primary',with_stress=False)
        assert len(r['decisions'])==12
        assert abs(D(r['net_cash_profit_usd'])-D(r['cash_attribution']['reconstructed_profit_usd']))<D('.00000001')
        assert all(D(v)>=0 for state in r['states'] for v in state['balances'].values())
        assert not r['promotion_admitted']
        lag=m.run_book(panel(True),policy,'primary',lagged_instructions=r['decisions'],with_stress=False)
        assert lag['decisions'][0]['instruction'] is None


def test_h4_installments_include_costs_and_all_idle_money():
    r=m.run_book(panel(),'H4','primary',with_stress=False)
    buys=[e for e in r['events'] if not e['skipped'] and e['side']=='buy']
    assert len(buys)==4
    for e in buys:assert D(e['notional_usd'])+D(e['commission_usd'])<=625
    assert all(D(s['balances']['USDC'])>7499 for s in r['states'])


def test_zero_volatility_is_unavailable_not_retuned():
    with pytest.raises(ValueError,match='zero or unavailable'):m.run_book(panel(),'H5','primary',with_stress=False)


def test_month_start_shock_does_not_change_prior_close_trigger():
    b=m.m.SpotBook({('cex','USDC'):'7500',('cex','BTC'):'25'})
    p={'USDC':D(1),'BTC':D(100),'ETH':D(50)}
    r=m.stress_at(b,p,'frictionless',m.START,'H2',[D(100)]*200)
    assert r['double-then-minus60']['intervening_actions']==0
    assert D(r['double-then-minus60']['nav'])==D('9490')


def test_precommitted_pending_action_survives_stress_origin():
    b=m.m.SpotBook({('cex','USDC'):'10000'})
    p={'USDC':D(1),'BTC':D(100),'ETH':D(50)}
    pending=(m.START+300,{'weights':('.25',0)})
    r=m.stress_at(b,p,'frictionless',m.START+m.DAY,'H2',[D(100)]*201,pending=pending)
    assert r['double-then-minus60']['intervening_actions']==1
    assert D(r['double-then-minus60']['nav'])==D('8491.50')


def test_maximum_exposure_includes_close_spikes():
    data=panel();data['joined'][202]['btc_bars']['close']='1000'
    r=m.run_book(data,'B9','frictionless',with_stress=False)
    actual=max(D(s['crypto_fraction']) for s in r['states'])
    assert D(r['max_crypto_fraction'])==actual and actual>D('.7')


def test_remaining_pre_sized_orders_reject_overspend_after_shock():
    b=m.m.SpotBook({('cex','USDC'):'100',('cex','BTC'):'1'})
    p={'USDC':D(1),'BTC':D(100),'ETH':D(50)}
    order={'asset':'ETH','side':'buy','quantity':'2'}
    r=m.stress_at(b,p,'frictionless',m.START+m.DAY,'B4',[D(100)]*201,remaining_orders=[order])
    assert r['double-then-minus60']['intervening_actions']==0
    assert D(r['double-then-minus60']['nav'])==D('170')


def test_exception_retains_known_partial_cashflows():
    progress={}
    # H5 first decisions have nonzero returns, then become undefined after a flat stretch.
    data=panel(True)
    for row in data['joined'][250:]:
        row['btc_bars']['open']='100'
        if 'close' in row['btc_bars']:row['btc_bars']['close']='100'
    with pytest.raises(ValueError,match='zero or unavailable'):
        m.run_book(data,'H5','primary',with_stress=False,progress=progress)
    assert progress['events'] and progress['states'] and progress['decisions']
    assert all(v>=0 for v in m.balances(progress['book']).values())


def test_full_wrapper_keeps_33_cells_three_missing_cash_controls_and_placebo():
    spec=importlib.util.spec_from_file_location('tested_conditional_run',P.with_name('conditional_run.py'))
    run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
    output={}
    def publish(name,value):
        assert name not in output
        output[name]=value
    result=run.execute(panel(True),'H2',publish)
    assert len(result['cells'])==33 and sum(c['status']=='unavailable' for c in result['cells'])==3
    assert len(output)==74 and set(output['benchmarks.json'])=={'B'+str(i) for i in range(10)}
    assert not result['measurement_defect'] and not result['promotion_admitted']
    for scenario in ('primary','doubled','frictionless'):
        assert result['comparisons'][scenario]['benchmark_differences']['B1']['status']=='unavailable'
        assert output['h2-'+scenario+'-placebo.json']['status']=='complete'


def test_intermediate_stress_failure_restores_final_book(monkeypatch):
    original=m.stress_at
    def fail(book,*args,**kwargs):
        q=m.balances(book)
        if q['BTC']>0 and q['ETH']==0:raise ValueError('injected intermediate stress failure')
        return original(book,*args,**kwargs)
    monkeypatch.setattr(m,'stress_at',fail)
    progress={}
    with pytest.raises(ValueError,match='injected'):
        m.run_book(panel(),'B4','frictionless',progress=progress)
    assert m.balances(progress['book'])=={'USDC':D('10'),'BTC':D('49.95'),'ETH':D('99.9')}
    assert len(progress['book'].events)==2


def test_second_asset_failure_retains_first_literal_cashflow(monkeypatch):
    original=m.trade
    def fail(book,event,asset,side,*args,**kwargs):
        if asset=='ETH' and side=='buy':raise ValueError('injected second asset failure')
        return original(book,event,asset,side,*args,**kwargs)
    monkeypatch.setattr(m,'trade',fail);progress={}
    with pytest.raises(ValueError,match='injected'):
        m.run_book(panel(),'B4','frictionless',progress=progress,with_stress=False)
    spec=importlib.util.spec_from_file_location('tested_partial_snapshot',P.with_name('conditional_run.py'))
    wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
    retained=wrapper.partial_snapshot(progress)
    assert retained['literal_balances_reconciled'] and len(retained['literal_ledger_events'])==1
    assert D(retained['balances']['USDC'])==D('5005')
