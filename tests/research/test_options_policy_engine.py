"""Invented accounting paths only; no empirical files or network."""
import copy
import importlib.util
from pathlib import Path
from fractions import Fraction as F
import pytest

spec=importlib.util.spec_from_file_location('options_policy_engine',Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11/options_policy_engine.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def row(i, *, price='100', premium='10', delta='0'):
    option={'unit':1,'bid':premium,'ask':premium,'bid_qty':'100','ask_qty':'100','mark':premium,'delta':delta}
    return {'time_ms':i*3600000,'decision_available':True,'index':price,'call':dict(option),'put':dict(option,delta='0'),
            'perp':{'bid':price,'ask':price,'bid_qty':'100','ask_qty':'100','mark':price}}


def run(rows, **overrides):
    args=dict(capital='1000',option_quantity='1',costs={'option_fee_rate':'0','perp_fee_rate':'0','perp_slippage':'0','option_tick_worsening':'0'},hedge_lot='1',hedge_min_quantity='0',hedge_min_notional='0',expected_funding_times=[],funding_events=[])
    args.update(overrides)
    return m.ledger(rows,**args)


def test_premium_liability_and_terminal_principal():
    out=run([row(0),row(1,premium='5')])
    assert out['trace'][0]['option_cash']=='420'
    assert out['trace'][0]['option_liability']=='20'
    assert out['trace'][0]['nav']=='1000'
    assert out['final']['cash']=='1010' and out['final']['profit']=='10'
    assert out['trace'][-1]['option_liability']=='0' and out['trace'][-1]['hedge_quantity']=='0'


def test_long_loss_reversal_realized_and_no_notional_cash():
    out=run([row(0,delta='1'),row(1,price='90',delta='-1'),row(2,price='80')])
    assert out['trace'][0]['perp_cash_known_component']=='500'
    assert [t['quantity'] for t in out['trades']]==['1','-2','1']
    assert out['cash_components']['perp_realized']=='0'
    assert out['cash_components']['perp_turnover']=='360'
    assert out['final']['cash']=='1000'


def test_exact_rounding_and_min_order():
    assert m.nearest_lot(F(3,2),F(1))==1
    assert m.nearest_lot(F(-3,2),F(1))==-1
    assert m.nearest_lot(F(151,100),F(1))==2
    out=run([row(0,delta='0.5'),row(1)])
    assert not out['trades'] and out['trace'][0]['model_hedge_residual']=='-1/2'
    out=run([row(0,delta='1'),row(1)],hedge_min_notional='101')
    assert out['trace'][0]['decision']=='minimum_order_no_trade'


def test_funding_prior_inventory_before_same_time_reversal():
    out=run([row(0,delta='1'),row(1,delta='-1'),row(2)],expected_funding_times=[0,3600000,7200000],funding_events=[{'time_ms':0,'rate':'1','mark':'100'},{'time_ms':3600000,'rate':'0.01','mark':'100'},{'time_ms':7200000,'rate':'-0.02','mark':'100'}])
    assert [e['inventory'] for e in out['funding_events']]==['1','-1']
    assert [e['cash'] for e in out['funding_events']]==['-1','-2']
    assert out['final']['profit']=='-3'


def test_fees_ticks_and_terminal_once():
    costs={'option_fee_rate':'0.0003','perp_fee_rate':'0.001','perp_slippage':'0.01','option_tick_worsening':'1'}
    out=run([row(0,delta='1'),row(1)],costs=costs)
    assert out['cash_components']['premium']=='18'
    assert out['cash_components']['option_buyback']=='22'
    assert out['cash_components']['option_fees']=='3/25'
    assert out['cash_components']['perp_fees']=='1/5'
    assert out['cash_components']['perp_realized']=='-2'
    assert out['final']['profit']=='-158/25'
    assert len(out['trades'])==2 and out['trades'][-1]['terminal'] is True


def test_missing_decision_keeps_inventory_and_missing_mark_only_nav():
    rows=[row(0,delta='1'),row(1,delta='-1'),row(2)]
    rows[1]['decision_available']=False;rows[1]['call']['mark']=None
    out=run(rows)
    assert out['trace'][1]['hedge_quantity']=='1'
    assert out['trace'][1]['nav'] is None
    assert out['final']['cash']=='1000'
    assert out['risk']['max_drawdown'] is None
    assert out['convention_diagnostic']['log_return_sum'] is None


def test_missing_funding_preserves_known_cash_but_no_final():
    out=run([row(0,delta='1'),row(1),row(2)],expected_funding_times=[3600000,7200000],funding_events=[{'time_ms':7200000,'rate':'0.01','mark':'100'}])
    assert out['final']['cash'] is None
    assert out['cash_components']['known_funding']=='0'
    assert out['trace'][1]['perp_cash_known_component']=='500'
    assert out['missing_funding_times']==[3600000]


def test_terminal_unavailable_no_partial_close():
    rows=[row(0,delta='1'),row(1)];rows[-1]['put']['ask_qty']='0'
    out=run(rows)
    assert out['final']['closed'] is False and out['final']['cash'] is None
    assert out['trace'][-1]['hedge_quantity']=='1'
    assert out['cash_components']['option_buyback']=='0'


def test_wallet_deficit_not_hidden_by_total_nav():
    out=run([row(0,delta='1'),row(1,price='1000',premium='300')])
    assert out['risk']['option_wallet_deficit'] is True
    assert F(out['final']['profit'])>0
    assert out['risk']['actual_margin_and_access']=='unavailable'


def test_nonpositive_nav_and_log_shadow():
    out=run([row(0),row(1,premium='1000')])
    assert F(out['final']['cash'])<0
    assert out['convention_diagnostic']['log_return_sum'] is None
    out=run([row(0),row(1,premium='20'),row(2,premium='5')])
    assert float(F(out['convention_diagnostic']['arithmetic_return_sum'])) != pytest.approx(out['convention_diagnostic']['log_return_sum'])


@pytest.mark.parametrize('mutation',['hour','unit','size','capital','quantity','fund_duplicate'])
def test_contract_guards(mutation):
    rows=[row(0),row(1)];args={}
    if mutation=='hour':rows[1]['time_ms']+=1
    if mutation=='unit':rows[0]['call']['unit']=2
    if mutation=='size':rows[0]['call']['bid_qty']='0'
    if mutation=='capital':args['capital']='0'
    if mutation=='quantity':args['option_quantity']='0'
    if mutation=='fund_duplicate':args.update(expected_funding_times=[3600000],funding_events=[{'time_ms':3600000,'rate':'0','mark':'100'}]*2)
    if mutation in ('unit','size'):
        out=run(rows,**args);assert out['final']['cash'] is None and out['cash_components']['premium']=='0'
    else:
        with pytest.raises(ValueError):run(rows,**args)


def test_partial_reduction_then_add_preserves_direct_pnl():
    out=run([row(0,delta='2'),row(1,price='110',delta='1'),row(2,price='120',delta='2'),row(3,price='130')])
    assert out['trace'][1]['perp_execution_offset_uncredited']=='-90'
    assert out['trace'][1]['perp_total_pnl_known']=='20'
    assert out['trace'][2]['perp_execution_offset_uncredited']=='-210'
    assert out['trace'][2]['perp_total_pnl_known']=='30'
    assert out['cash_components']['perp_realized']=='50'
    assert out['final']['profit']=='50'


def test_known_size_no_trade_and_zero_inventory_missing_funding():
    rows=[row(0,delta='1'),row(1)];rows[0]['perp']['ask_qty']='0'
    out=run(rows)
    assert out['trace'][0]['decision']=='hedge_size_unavailable'
    assert out['trace'][0]['hedge_quantity']=='0'
    out=run([row(0),row(1)],expected_funding_times=[3600000])
    assert out['final']['cash'] is None
    assert out['funding_events'][0]['cash'] is None


def test_option_fee_cap_and_explicit_cash_benchmarks():
    out=run([row(0,premium='0.01'),row(1,premium='0.01')],costs={'option_fee_rate':'0.5','perp_fee_rate':'0','perp_slippage':'0','option_tick_worsening':'0'})
    assert out['cash_components']['option_fees']=='1/250'
    assert out['metrics']['cash_benchmarks']['0']=='1000'


def test_phase_exit_does_not_require_delta_or_mark():
    rows=[row(0,delta='1'),row(1)]
    rows[1].update(decision_available=False,hedge_available=False,exit_available=True,valuation_available=False)
    for key in ('call','put'):
        rows[1][key]['delta']=None;rows[1][key]['mark']=None
    rows[1]['perp']['mark']=None
    out=run(rows)
    assert out['final']['closed'] is True and out['final']['cash']=='1000'
    assert out['trace'][-1]['nav']=='1000'


def test_phase_stale_exit_overrides_generic_success():
    rows=[row(0,delta='1'),row(1)]
    rows[1].update(exit_available=False,hedge_available=True,valuation_available=True)
    out=run(rows)
    assert out['final']['closed'] is False
    assert out['final']['cash'] is None
    assert out['trace'][-1]['hedge_quantity']=='1'


def test_phase_entry_hedge_valuation_and_no_generic_required():
    rows=[row(0,delta='1'),row(1,delta='-1'),row(2)]
    for r in rows:r.pop('decision_available')
    rows[0]['entry_available']=True
    rows[1].update(hedge_available=False,valuation_available=False)
    rows[2]['exit_available']=True
    out=run(rows)
    assert out['trace'][1]['hedge_quantity']=='1' and out['trace'][1]['nav'] is None
    assert out['final']['cash']=='1000'
    rows[0]['entry_available']=False
    assert run(rows)['cash_components']['premium']=='0'


def test_phase_flags_are_typed():
    rows=[row(0),row(1)];rows[-1]['exit_available']=1
    with pytest.raises(ValueError):run(rows)


def test_receipt_boundary_funding_before_actions_and_initial_exclusion():
    rows=[row(0,delta='1'),row(1,delta='-1'),row(2)]
    for r in rows:r['action_time_ms']=r['time_ms']+5000
    calendar=[3000,3603000,7203000]
    out=run(rows,expected_funding_times=calendar,funding_events=[{'time_ms':3603000,'rate':'0.01','mark':'100'},{'time_ms':7203000,'rate':'0.02','mark':'100'}])
    assert out['initial_zero_inventory_funding_times']==[3000]
    assert out['missing_funding_times']==[]
    assert [e['inventory'] for e in out['funding_events']]==['1','-1']
    assert [e['cash'] for e in out['funding_events']]==['-1','2']
    assert out['final']['profit']=='1'
    assert out['trace'][1]['time_ms']==3600000
    assert out['trace'][1]['action_time_ms']==3605000
    assert out['trades'][1]['action_time_ms']==3605000


def test_missing_terminal_latency_funding_invalidates_cash():
    rows=[row(0,delta='1'),row(1)]
    rows[-1]['action_time_ms']=3605000
    out=run(rows,expected_funding_times=[3603000])
    assert out['final']['closed'] is True and out['final']['cash'] is None
    assert out['funding_events'][0]['inventory']=='1'
    assert out['metrics']['duration_ms']==3605000


@pytest.mark.parametrize('action',[-1,5001,True,0.5])
def test_action_clock_bound(action):
    rows=[row(0),row(1)];rows[0]['action_time_ms']=action
    with pytest.raises(ValueError):run(rows)


def test_unknown_wallet_risk_flags_and_observed_deficit_dominates():
    rows=[row(0,delta='1'),row(1),row(2)]
    rows[1]['call']['mark']=None;rows[1]['perp']['mark']=None
    rows[1]['hedge_available']=False
    out=run(rows)
    assert out['risk']['option_wallet_deficit'] is None
    assert out['risk']['perp_wallet_deficit'] is None
    out=run([row(0,delta='1'),row(1),row(2)],expected_funding_times=[3600000])
    assert out['risk']['perp_wallet_deficit'] is None
    rows[0]['call']['mark']='1000'
    out=run(rows)
    assert out['risk']['option_wallet_deficit'] is True
    assert out['risk']['perp_wallet_deficit'] is None


def test_log_fraction_no_float_ratio_underflow():
    import math
    tiny=F(1,10**1000)
    assert float(tiny)==0
    assert math.isfinite(m.log_fraction(tiny))
    assert m.log_fraction(tiny)==pytest.approx(-1000*math.log(10))
    assert m.log_fraction(1/tiny)==pytest.approx(1000*math.log(10))


def test_component_valuation_preserves_known_deficit_and_other_wallet():
    rows=[row(0,delta='1'),row(1),row(2)]
    rows[1].update(hedge_available=False,valuation_available=False,
                   option_valuation_available=True,perp_valuation_available=False)
    rows[1]['call']['mark']='1000';rows[1]['perp']['mark']=None
    out=run(rows)
    assert out['trace'][1]['option_wallet_equity']=='-590'
    assert out['trace'][1]['perp_wallet_equity'] is None
    assert out['trace'][1]['nav'] is None
    assert out['risk']['option_wallet_deficit'] is True
    rows[1].update(option_valuation_available=False,perp_valuation_available=True)
    rows[1]['call']['mark']=None;rows[1]['perp']['mark']='100'
    out=run(rows)
    assert out['trace'][1]['option_wallet_equity'] is None
    assert out['trace'][1]['perp_wallet_equity']=='500'
    assert out['risk']['perp_wallet_deficit'] is False


@pytest.mark.parametrize('field',['option_valuation_available','perp_valuation_available'])
def test_component_valuation_flags_typed(field):
    rows=[row(0),row(1)];rows[0][field]=1
    with pytest.raises(ValueError):run(rows)


def test_episode_slot_scope_bounded():
    with pytest.raises(ValueError):run([row(i) for i in range(1058)])


def test_reviewer_1057_row_basis_growth_now_direct_execution_completes():
    deltas=['.50000000000000000001','.50000000000000000000',
            '.50000000000000000003','.49999999999999999999']
    rows=[]
    for i in range(1057):
        r=row(i,price=str(100+i%7),delta=deltas[i%4])
        for key in ('call','put','perp'):
            r[key]['bid_qty']='1e25';r[key]['ask_qty']='1e25'
        rows.append(r)
    out=run(rows,capital='1e25',option_quantity='1e20')
    assert out['status']=='conditional_cash_complete'
    offset=sum(-F(t['quantity'])*F(t['price']) for t in out['trades'])
    assert F(out['cash_components']['perp_realized'])==offset


def test_serialization_bound_checked_before_integer_conversion():
    with pytest.raises(m.ArithmeticScopeError):m._encoded(F(1,2**4096))
    with pytest.raises(m.ArithmeticScopeError):m._encoded(F(2**4096,1))
    assert m._encoded(F(1,2**4095)).startswith('1/')


def test_ordinary_1057_slot_policy_and_flat_reentry_keep_offset():
    rows=[row(i,price=str(100+i%7),delta=['1','.2','.7','.4'][i%4]) for i in range(1057)]
    for r in rows:r['put']['delta']='-.5'
    out=run(rows,option_quantity='.01',hedge_lot='.0001')
    assert out['status']=='conditional_cash_complete'
    offset=sum(-F(t['quantity'])*F(t['price']) for t in out['trades'])
    assert F(out['cash_components']['perp_realized'])==offset
    assert F(out['final']['profit'])==offset
    out=run([row(0,delta='1'),row(1,price='110'),row(2,price='120',delta='1'),row(3,price='130')])
    assert out['trace'][1]['hedge_quantity']=='0'
    assert out['trace'][1]['perp_total_pnl_known']=='10'
    assert out['trace'][2]['perp_total_pnl_known']=='10'
    assert out['trace'][2]['perp_realized_cash_while_open']=='unavailable'
    assert out['trace'][2]['perp_cash_known_component']=='500'
    assert out['final']['profit']=='20'


def test_open_pnl_cash_unavailable_but_equity_known():
    rows=[row(0,delta='1'),row(1,price='120')];rows[-1]['exit_available']=False
    out=run(rows)
    assert out['cash_components']['perp_realized'] is None
    assert out['trace'][-1]['perp_total_pnl_known']=='20'
    assert out['trace'][-1]['perp_wallet_equity']=='520'
    assert out['final']['cash'] is None


@pytest.mark.parametrize('capital',['1000','10000'])
@pytest.mark.parametrize('stress',[False,True])
def test_full_cost_funding_path_diagnostic_cannot_break_cash(capital,stress):
    rows=[]
    for i in range(1057):
        r=row(i,price=str(100+i%7),delta=['1','.2','.7','.4'][i%4])
        r['put']['delta']='-.5'
        r['call']['ask']='10.01';r['put']['ask']='10.01'
        r['action_time_ms']=r['time_ms']+5000
        rows.append(r)
    expected=[h*3600000+3000 for h in range(0,1057,8)]
    events=[{'time_ms':t,'rate':'.0001','mark':'100'} for t in expected[1:]]
    costs={'option_fee_rate':'.00030' if stress else '.00024',
           'perp_fee_rate':'.001' if stress else '.0005',
           'perp_slippage':'.0004' if stress else '.0002',
           'option_tick_worsening':'.01' if stress else '0'}
    out=run(rows,capital=capital,option_quantity='.01',hedge_lot='.0001',costs=costs,
            expected_funding_times=expected,funding_events=events)
    assert out['status']=='conditional_cash_complete' and len(out['trace'])==1057
    parts=out['cash_components']
    profit=F(parts['premium'])-F(parts['option_buyback'])-F(parts['all_fees'])+F(parts['perp_realized'])+F(parts['known_funding'])
    assert F(out['final']['profit'])==profit
    assert out['convention_diagnostic']['arithmetic_return_sum'] is not None
    assert out['convention_diagnostic']['arithmetic_precision'].startswith('60 significant')
