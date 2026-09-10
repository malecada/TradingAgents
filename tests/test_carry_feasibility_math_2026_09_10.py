"""Synthetic cash and quantity examples; no market data or strategy execution."""
from decimal import Decimal, localcontext, ROUND_DOWN
import importlib
import importlib.util

import pytest

NAME = 'scripts.carry_feasibility_math_2026_09_10'
D = Decimal


@pytest.fixture
def api():
    assert importlib.util.find_spec(NAME) is not None, 'pure carry calculator is not implemented'
    return importlib.import_module(NAME)


def inputs(**updates):
    args = dict(
        spot_book={'asks': [['100', '100']], 'bids': [['99', '100']]},
        future_book={'bids': [['110', '100']], 'asks': [['111', '100']]},
        spot_rules={'step_size': '.001', 'min_qty': '.001', 'max_qty': '100', 'min_notional': '1'},
        future_rules={'step_size': '.1', 'min_qty': '.1', 'max_qty': '100', 'min_notional': '1'},
        capital='210.255', reserve_fraction='1', fee_multiplier='1')
    args.update(updates)
    return args


def test_base_fee_grossup_ceiling_preserves_residual_and_cash_principal(api):
    e = api.size_hedge(**inputs())
    assert e['status'] == 'complete'
    assert D(e['future_contracts']) == 1
    assert D(e['future_base_quantity']) == 1
    assert D(e['spot_gross_quantity']) == D('1.002')
    assert D(e['spot_entry_base_fee']) == D('.001002')
    assert D(e['spot_net_quantity']) == D('1.000998')
    assert D(e['residual_base_quantity']) == D('.000998')
    assert D(e['spot_entry_cost']) == D('100.2')
    assert D(e['future_entry_notional']) == 110
    assert D(e['future_entry_cash_fee']) == D('.055')
    assert D(e['reserve_committed']) == 110
    assert D(e['entry_cash_required']) == D('210.255')
    assert D(e['uncommitted_cash']) == 0
    assert e['future_entry_principal_cashflow'] == '0'
    assert e['executable_admission'] is False


@pytest.mark.parametrize('ratio,profit,terminal_reserve', [
    ('.5', '9.7198501', '169.975'), ('1', '9.6947002', '119.95'),
    ('2', '9.6444004', '19.9')])
def test_hand_derived_down_flat_up_terminal_cash_reconciles(api, ratio, profit, terminal_reserve):
    e = api.size_hedge(**inputs())
    r = api.terminal_case(e, terminal_index_ratio=ratio, adverse_exit_bps='0', seconds_to_expiry='31536000')
    assert r['status'] == 'complete'
    assert D(r['net_cash_profit']) == D(profit)
    assert D(r['terminal_nav']) == D('210.255') + D(profit)
    assert D(r['terminal_futures_reserve']) == D(terminal_reserve)
    c = r['cash_components']
    assert D(r['terminal_nav']) == D(c['uncommitted_cash']) + D(c['spot_sale_net']) + D(r['terminal_futures_reserve'])
    assert D(r['annualized_simple_return']) == D(r['net_return_on_capital'])
    assert r['pathwise_margin_survival_verified'] is False


def test_terminal_mismatch_values_entire_spot_holding_and_benchmark_separately(api):
    e = api.size_hedge(**inputs())
    base = api.terminal_case(e, terminal_index_ratio='1', adverse_exit_bps='0', seconds_to_expiry='31536000')
    r = api.terminal_case(e, terminal_index_ratio='1', adverse_exit_bps='50', seconds_to_expiry='31536000')
    assert D(base['net_cash_profit']) - D(r['net_cash_profit']) == D('1.000998') * D('.5') * D('.999')
    assert D(r['benchmarks']['0.03']['cash_profit']) == D('210.255') * D('.03')
    assert D(r['benchmarks']['0.03']['excess_cash_profit']) == D(r['net_cash_profit']) - D('210.255') * D('.03')
    assert D(r['cash_components']['paid_financing']) == 0
    assert D(r['cash_components']['credited_interest']) == 0


def test_one_third_reserve_is_exact_for_budget_comparison_and_not_profit_expense(api):
    # q=3, no spot fee, A=300, E=.165, reserve=110 exactly.
    e = api.size_hedge(**inputs(capital='410.165', reserve_fraction='1/3', spot_fee='0'))
    assert D(e['future_base_quantity']) == 3
    assert D(e['reserve_committed']) == 110
    assert D(e['uncommitted_cash']) == 0
    assert e['reserve_fraction'] == '1/3'
    # For an identical hedge the reserve changes capital allocation, not profit.
    full = api.size_hedge(**inputs(capital='630.165', spot_fee='0'))
    a = api.terminal_case(e, terminal_index_ratio='2', adverse_exit_bps='0', seconds_to_expiry='86400')
    b = api.terminal_case(full, terminal_index_ratio='2', adverse_exit_bps='0', seconds_to_expiry='86400')
    assert a['net_cash_profit'] == b['net_cash_profit']
    assert a['terminal_reserve_insufficient'] is True
    assert b['terminal_reserve_insufficient'] is False


def test_depth_cost_crosses_levels_and_never_extrapolates(api):
    args = inputs(capital='10000', spot_fee='0', future_entry_fee='0', future_expiry_fee='0')
    args['spot_book']['asks'] = [['100', '1'], ['102', '1']]
    args['future_book']['bids'] = [['110', '1'], ['108', '1']]
    e = api.size_hedge(**args)
    assert D(e['future_base_quantity']) == 2
    assert D(e['spot_entry_cost']) == 202
    assert D(e['future_entry_notional']) == 218
    assert e['depth_limited'] is True
    assert e['spot_ask_levels_used'] == 2 and e['future_bid_levels_used'] == 2


def test_binary_search_finds_largest_lot_below_budget_with_base_fee_steps(api):
    e = api.size_hedge(**inputs(capital='210.254999999999'))
    assert D(e['future_base_quantity']) == D('.9')
    e2 = api.size_hedge(**inputs(capital='210.255'))
    assert D(e2['future_base_quantity']) == 1


def test_multiplier_and_order_limit_apply_in_contract_units(api):
    args = inputs(capital='10000', spot_fee='0', future_multiplier='.01')
    args['future_rules'].update(step_size='1', min_qty='1', max_qty='25')
    e = api.size_hedge(**args)
    assert D(e['future_contracts']) == 25
    assert D(e['future_base_quantity']) == D('.25')
    assert D(e['future_entry_notional']) == D('27.5')
    assert 'future_max_qty' in e['binding_constraints']


@pytest.mark.parametrize('leg,field,value,reason', [
    ('spot','min_notional','1000','minimum'), ('future','min_notional','1000','minimum'),
    ('future','min_qty','2','minimum'), ('spot','min_qty','2','minimum')])
def test_minimum_filters_do_not_destroy_binary_search_monotonicity(api,leg,field,value,reason):
    args=inputs(); args[leg+'_rules'][field]=value
    e=api.size_hedge(**args)
    assert e['status']=='unavailable' and reason in e['reason']


@pytest.mark.parametrize('leg,field,value,expected', [
    ('spot','max_qty','.999','0.9'), ('future','max_qty','.9','0.9'),
    ('spot','max_notional','100','0.9'), ('future','max_notional','100','0.9')])
def test_maximum_filters_bound_size(api,leg,field,value,expected):
    args=inputs(capital='10000');args[leg+'_rules'][field]=value
    e=api.size_hedge(**args)
    assert D(e['future_base_quantity'])==D(expected)


def test_empty_feasible_set_is_explicit_and_preserves_capital(api):
    e=api.size_hedge(**inputs(capital='1'))
    assert e['status']=='unavailable' and e['capital']=='1' and e['reason']
    r=api.terminal_case(e,terminal_index_ratio='1',adverse_exit_bps='0',seconds_to_expiry='10')
    assert r['status']=='unavailable' and r['reason']==e['reason']


@pytest.mark.parametrize('bad',[True,1.5,'NaN','Infinity','-1','0'])
def test_invalid_capital_and_binary_float_are_rejected(api,bad):
    with pytest.raises(ValueError):api.size_hedge(**inputs(capital=bad))


@pytest.mark.parametrize('problem',['crossed','unordered','duplicate','zero_quantity','empty','nonfinite'])
def test_invalid_depth_is_not_silently_cleaned(api,problem):
    args=inputs()
    if problem=='crossed':args['spot_book']['bids']=[['100','1']]
    if problem=='unordered':args['spot_book']['asks']=[['101','1'],['100','1']]
    if problem=='duplicate':args['spot_book']['asks']=[['100','1'],['100','1']]
    if problem=='zero_quantity':args['spot_book']['asks']=[['100','0']]
    if problem=='empty':args['future_book']['bids']=[]
    if problem=='nonfinite':args['future_book']['bids']=[['NaN','1']]
    with pytest.raises(ValueError):api.size_hedge(**args)


def test_doubled_fees_affect_quantity_and_all_four_fee_legs(api):
    e=api.size_hedge(**inputs(capital='1000',fee_multiplier='2'))
    assert e['spot_entry_fee_rate']=='0.002' and e['spot_exit_fee_rate']=='0.002'
    assert e['future_entry_fee_rate']=='0.001' and e['future_expiry_fee_rate']=='0.001'
    assert D(e['spot_net_quantity']) >= D(e['future_base_quantity'])
    r=api.terminal_case(e,terminal_index_ratio='1',adverse_exit_bps='10',seconds_to_expiry='86400.5')
    assert D(r['cash_components']['future_expiry_fee'])==D(e['future_base_quantity'])*100*D('.001')
    assert D(r['cash_components']['spot_exit_fee'])==D(r['cash_components']['spot_sale_gross'])*D('.002')


def test_composed_interface_matches_separate_steps_and_ignores_global_precision(api):
    args=inputs(capital='220', reserve_fraction='1/3')
    terminal=dict(terminal_index_ratio='1',adverse_exit_bps='10',seconds_to_expiry='31536000')
    e=api.size_hedge(**args); expected=api.terminal_case(e,**terminal)
    with localcontext() as ctx:
        ctx.prec=8
        ctx.rounding=ROUND_DOWN
        actual=api.evaluate_case(**args,**terminal)
    assert actual==expected


@pytest.mark.parametrize('kwargs',[{'seconds_to_expiry':'0'},{'seconds_to_expiry':'-1'},
 {'terminal_index_ratio':'0'},{'adverse_exit_bps':'10000'},{'cash_benchmark_annual':['0','NaN']}])
def test_invalid_terminal_contract_fails_instead_of_substituting_prices(api,kwargs):
    terminal=dict(terminal_index_ratio='1',adverse_exit_bps='0',seconds_to_expiry='100')
    terminal.update(kwargs)
    with pytest.raises(ValueError):api.terminal_case(api.size_hedge(**inputs()),**terminal)


def test_affordable_size_above_minima_is_not_discarded_by_small_search_candidates(api):
    args=inputs(capital='1000')
    args['future_rules']['min_qty']='4.5'
    args['spot_rules']['min_qty']='4.5'
    e=api.size_hedge(**args)
    assert e['status']=='complete'
    assert D(e['future_base_quantity'])==D('4.7')


def test_negative_basis_and_adverse_terminal_scenario_cannot_select_smaller_size(api):
    args=inputs(capital='1000')
    args['future_book']={'bids':[['90','100']], 'asks':[['91','100']]}
    a=api.evaluate_case(**args,terminal_index_ratio='.5',adverse_exit_bps='0',seconds_to_expiry='86400')
    b=api.evaluate_case(**args,terminal_index_ratio='2',adverse_exit_bps='50',seconds_to_expiry='86400')
    assert a['future_base_quantity']==b['future_base_quantity']
    assert D(a['net_cash_profit'])<0 and D(b['net_cash_profit'])<0
    assert a['status']==b['status']=='complete'


def test_invalid_frozen_log_accounting_does_not_reproduce_fixed_quantity_hedge(api):
    e=api.size_hedge(**inputs())
    r=api.terminal_case(e,terminal_index_ratio='2',adverse_exit_bps='0',seconds_to_expiry='86400')
    with localcontext() as context:
        context.prec=80
        h=D(e['spot_net_quantity']); initial_spot=D(e['initial_top_spot_ask'])
        a=D(e['spot_entry_cost']); b=D(e['future_entry_notional'])
        q=D(e['future_base_quantity']); terminal=D(r['terminal_index'])
        c=r['cash_components']
        invalid_log=(h*initial_spot*(terminal/initial_spot).ln()+(h*initial_spot-a)
                     -b*(terminal/(b/q)).ln()-D(e['future_entry_cash_fee'])
                     -D(c['future_expiry_fee'])-D(c['spot_exit_fee']))
    assert D(r['net_cash_profit'])==D('9.6444004')
    assert abs(D(r['net_cash_profit'])-invalid_log)>1
