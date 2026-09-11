"""Invented WBETH/ETH prices and events; pure financial accounting only."""
from copy import deepcopy
from decimal import Decimal, ROUND_FLOOR
import importlib.util
import math
from pathlib import Path

import pytest

PATH=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11/wbeth_book.py'
spec=importlib.util.spec_from_file_location('wbeth_test_engine',PATH)
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)


def inputs(wbeth_growth=0, common_growth=0, rate=0):
    def bars(base, growth):
        return [[engine.START_MS+i*engine.DAY_MS,base*(1+growth*i/90),base*(1+growth*i/90),base*(1+growth*i/90),base*(1+growth*i/90),1,
                 engine.START_MS+(i+1)*engine.DAY_MS-1,100,1,.5,50,0] for i in range(91)]
    events=[{'symbol':'ETHUSDT','fundingTime':engine.START_MS+i*engine.DAY_MS//3,'fundingRate':rate,'markPrice':100} for i in range(273)]
    return [bars(200,wbeth_growth+common_growth),bars(100,common_growth),bars(100,common_growth),bars(100,common_growth),events]


def book(data=None, **kwargs):
    return engine.book(*(inputs() if data is None else data),capital=kwargs.pop('capital',1000),**kwargs)


def assert_reconciles(result):
    assert result['status']=='conditional',result
    initial,final=result['initial'],result['final_ledger']
    assert final['cash_profit']==pytest.approx(final['cash_profit_from_signed_components'],abs=1e-9)
    assert final['cash_profit']==pytest.approx(final['same_quantity_frictionless_price_pnl']-final['slippage_cost']-final['all_fees']+final['cumulative_funding_cash'],abs=1e-9)
    assert initial['joint_entry_spend']+initial['futures_reserve']+initial['idle_cash']==pytest.approx(result['capital'])
    last=result['daily_trace'][-1]
    assert last['nav']==pytest.approx(last['idle_cash']+last['futures_wallet']+last['short_mtm']+last['wbeth_value'])
    assert last['nav']==final['final_cash']
    assert last['wbeth_quantity']==last['eth_perp_quantity']==last['net_market_value']==last['gross_market_value']==0
    assert last['pre_exit_components']['wbeth_quantity']>0


@pytest.mark.parametrize('capital',[1000,10000])
@pytest.mark.parametrize('scenario',['base','stress'])
def test_constant_prices_release_principal_and_pay_both_asset_fees(capital,scenario):
    result=book(capital=capital,cost_scenario=scenario);assert_reconciles(result)
    initial,final=result['initial'],result['final_ledger']
    assert initial['wbeth_quantity']!=abs(initial['eth_perp_quantity'])
    assert initial['joint_entry_spend']<=.4*capital+1e-10 and initial['idle_cash']>=.1*capital-1e-10
    assert final['same_quantity_frictionless_price_pnl']==0
    assert final['cash_profit']<0
    assert final['all_fees']==pytest.approx(initial['wbeth_quantity']*initial['wbeth_entry_price']*result['costs']['spot_fee']+
        abs(initial['eth_perp_quantity'])*initial['eth_perp_entry_price']*result['costs']['perp_fee']+
        final['wbeth_exit_fee']+final['eth_perp_exit_fee'])
    assert result['true_eth_delta']['status']=='unavailable'
    assert 'net_base_quantity' not in result['daily_trace'][0]


def test_conservative_formula_and_two_distinct_lot_floors():
    result=book();initial=result['initial'];cost=result['costs']
    d=lambda value:Decimal(str(value))
    denominator=d(initial['wbeth_entry_price'])*(1+d(cost['spot_fee']))+2*d(initial['eth_perp_entry_price'])*d(cost['perp_fee'])
    qw=(d(400)/denominator/d('.0001')).to_integral_value(rounding=ROUND_FLOOR)*d('.0001')
    qe=(qw*2/d('.001')).to_integral_value(rounding=ROUND_FLOOR)*d('.001')
    assert initial['wbeth_quantity']==float(qw)
    assert initial['eth_perp_quantity']==-float(qe)
    assert initial['raw_entry_net_market_value']==pytest.approx(float(qw)*200-float(qe)*100)


def test_relative_wbeth_growth_is_market_price_gain_not_staking_attribution():
    result=book(inputs(wbeth_growth=.1));assert_reconciles(result)
    assert result['final_ledger']['same_quantity_frictionless_price_pnl']==pytest.approx(result['initial']['wbeth_quantity']*20)
    assert result['final_ledger']['cash_profit']>0
    assert any('without attribution' in text for text in result['assumptions'])


def test_common_price_change_cancels_except_explicit_initial_lot_residual():
    result=book(inputs(common_growth=.5));assert_reconciles(result)
    residual=result['initial']['raw_entry_net_market_value']
    assert result['final_ledger']['same_quantity_frictionless_price_pnl']==pytest.approx(.5*residual,abs=1e-10)
    row=result['daily_trace'][20]
    assert row['net_market_value']==pytest.approx(row['wbeth_quantity']*row['wbeth_close']+row['eth_perp_quantity']*row['eth_mark_close'])


@pytest.mark.parametrize('rate',[-.0001,.0001])
def test_signed_funding_uses_eth_quantity_and_zero_funding_same_portfolio(rate):
    data=inputs(rate=rate)
    result,zero=book(data),book(data,zero_funding=True)
    assert_reconciles(result);assert_reconciles(zero)
    assert result['initial']==zero['initial']
    funding=abs(result['initial']['eth_perp_quantity'])*100*rate*272
    assert result['metrics']['funding_cash']==pytest.approx(funding)
    assert result['final_ledger']['cash_profit']-zero['final_ledger']['cash_profit']==pytest.approx(funding)
    assert zero['metrics']['funding_cash']==0
    assert sum(row['observed_same_quantity_funding_cash'] for row in zero['daily_trace'])==pytest.approx(funding)
    assert result['metrics']['applied_funding_events']==272


def test_tail_depeg_and_common_rally_margin_are_distinct():
    result=book();tails=result['quantity_price_stresses']
    assert tails['wbeth_depeg_50pct']['cash_profit']<tails['wbeth_depeg_10pct']['cash_profit']<0
    assert tails['common_double']['margin_buffer_scenario']<tails['common_half']['margin_buffer_scenario']
    for tail in tails.values():
        assert tail['wbeth_quantity']==result['initial']['wbeth_quantity']
        assert tail['eth_perp_quantity']==result['initial']['eth_perp_quantity']
        assert tail['cumulative_funding_cash']==0


def test_nonpositive_nav_retains_cash_failure_and_invalid_log_status():
    result=book(inputs(rate=-1))
    assert_reconciles(result)
    assert result['metrics']['nonpositive_nav'] is True
    assert result['metrics']['margin_buffer_breach'] is True
    assert result['convention_diagnostic']['status']=='unavailable'
    assert result['convention_diagnostic']['log1p_sum'] is None
    assert result['final_ledger']['final_cash']<0


@pytest.mark.parametrize('failure',['missing_bar','missing_event','zero_entry_activity','zero_exit_activity','nan','bad_ohlc','tiny_lot','wrong_event_symbol'])
def test_invalid_or_missing_inputs_are_explicitly_unavailable(failure):
    data=inputs()
    if failure=='missing_bar':data[0].pop()
    elif failure=='missing_event':data[4].pop()
    elif failure=='zero_entry_activity':data[0][0][5]=0
    elif failure=='zero_exit_activity':data[2][-1][8]=0
    elif failure=='nan':data[3][0][1]=float('nan')
    elif failure=='bad_ohlc':data[0][5][2]=1
    elif failure=='tiny_lot':
        for row in data[0]:row[1:5]=[1e10]*4
    else:data[4][1]['symbol']='BTCUSDT'
    assert book(data)['status']=='unavailable'
    if failure=='missing_event':assert book(data,zero_funding=True)['status']=='unavailable'


def test_valid_log_forensic_is_not_arithmetic_cash():
    result=book(inputs(wbeth_growth=.1))
    diagnostic=result['convention_diagnostic']
    assert diagnostic['log1p_sum']==pytest.approx(math.log1p(result['metrics']['full_capital_return']))
    assert diagnostic['invalid_log_cash_shadow']!=pytest.approx(result['final_ledger']['cash_profit'])
    data=inputs();data[0][5][5]=0;data[0][5][8]=0
    assert book(data)['held_zero_activity_bars']['wbeth']==1


def test_exact_market_value_hedge_cancels_common_price_gain():
    data=inputs(common_growth=.5)
    for row in data[0]:row[1:5]=[value*1.25 for value in row[1:5]]
    result=book(data);assert_reconciles(result)
    assert result['initial']['raw_entry_net_market_value']==pytest.approx(0,abs=1e-10)
    assert result['final_ledger']['same_quantity_frictionless_price_pnl']==pytest.approx(0,abs=1e-10)
    assert result['final_ledger']['cash_profit']==pytest.approx(-result['final_ledger']['slippage_cost']-result['final_ledger']['all_fees'])
