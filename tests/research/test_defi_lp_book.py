import importlib.util
from datetime import date,timedelta
from fractions import Fraction as F
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('tested_lp_book',Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/lp_book.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def panel():
    sqrt=m.T.sqrt_at_tick(-200000)
    eth=F(sqrt*sqrt,m.M.Q96*m.M.Q96)*10**12
    return [{'date':(date(2025,9,1)+timedelta(days=i)).isoformat(),
             'prices':{'USDC':F(1),'ETH':eth,'WETH':eth},'sqrt_price':sqrt,'tick':-200000,
             'liquidity':10**20,'growth0':123,'growth1':456,'source_model_qualified':True,'unlocked':True,
             'lower_gross':0,'upper_gross':0,'max_tick_liquidity':m.MAX_TICK_LIQUIDITY}
            for i in range(366)]


def exact(record):return F(record['numerator'],record['denominator'])


def test_flat_frictionless_loses_only_route_and_explicit_mint_sale_dust():
    rows=panel();r=m.run_book(rows,'F3','frictionless')
    assert F(-11)<exact(r['exact_net_cash_profit'])<=-10
    assert F(r['cash_attribution']['market_usd'])==0
    assert F(r['cash_attribution']['inventory_transformation_usd'])==0
    assert F(r['cash_attribution']['fee_entitlement_change_usd'])==0
    assert r['terminal_atoms']['LP']==r['terminal_atoms']['WETH']==r['terminal_atoms']['ETH']==0
    assert exact(r['cash_attribution']['reconstructed_profit'])==exact(r['exact_net_cash_profit'])


def test_funded_sizing_is_maximal_and_control_holds_identical_entry_atoms():
    rows=panel();candidate=m.run_book(rows,'F3','primary');control=m.run_book(rows,'matched-entry-inventory','primary')
    plan=candidate['entry_plan'];assert plan==control['entry_plan']
    assert plan['usdc_atoms']+plan['weth_purchase_usdc_atoms']<=plan['sleeve_budget_atoms']
    a,b=m.M.lp_amounts(plan['liquidity']+1,rows[1]['sqrt_price'],m.LOW,m.HIGH,mint=True)
    assert b+m.buy_debit(a,rows[1]['prices'],m.W.SCENARIOS['primary'])>plan['sleeve_budget_atoms']
    assert candidate['events'][0]==control['events'][0]
    assert sum(e['gas_atoms'] for e in candidate['events'])==10*10**14
    assert sum(e['gas_atoms'] for e in control['events'])==5*10**14
    assert exact(candidate['exact_net_cash_profit'])<exact(control['exact_net_cash_profit'])


def test_fee_growth_paid_once_and_preentry_fees_excluded():
    rows=panel();plain=m.run_book(rows,'F3','frictionless');liquidity=plain['entry_plan']['liquidity']
    delta=(100*10**6*m.M.Q128+liquidity-1)//liquidity
    for row in rows[2:]:row['growth1']+=delta
    paid=m.run_book(rows,'F3','frictionless')
    owed=liquidity*delta//m.M.Q128
    assert exact(paid['exact_net_cash_profit'])-exact(plain['exact_net_cash_profit'])==F(owed,10**6)
    assert F(paid['cash_attribution']['fee_entitlement_change_usd'])==F(owed,10**6)
    assert len([e for e in paid['events'] if e['id']=='burn-collect'])==1
    pre=panel()
    for row in pre:row['growth0']+=10**30;row['growth1']+=10**30
    assert exact(m.run_book(pre,'F3','frictionless')['exact_net_cash_profit'])==exact(plain['exact_net_cash_profit'])


def test_price_change_inventory_transformation_is_not_double_charged_il():
    rows=panel();sqrt=m.T.sqrt_at_tick(-186140);eth=F(sqrt*sqrt,m.M.Q96*m.M.Q96)*10**12
    for row in rows[2:]:row.update(sqrt_price=sqrt,tick=-186140,prices={'USDC':F(1),'ETH':eth,'WETH':eth})
    r=m.run_book(rows,'F3','frictionless');control=m.run_book(rows,'matched-entry-inventory','frictionless')
    assert exact(r['exact_net_cash_profit'])<exact(control['exact_net_cash_profit'])
    p=r['entry_plan'];principal=m.M.lp_amounts(p['liquidity'],sqrt,m.LOW,m.HIGH,mint=False)
    # Independent one-step literal terminal inventory calculation, no IL formula.
    usdc=r['initial_atoms']['USDC']-p['weth_purchase_usdc_atoms']-p['usdc_atoms']+principal[1]
    usdc+=(F(principal[0],10**18)*eth*10**6).__floor__()
    usdc+=(F(m.RESERVE,10**18)*eth*10**6).__floor__()
    expected=F(usdc,10**6)-10-10000
    assert exact(r['exact_net_cash_profit'])==expected
    assert F(r['cash_attribution']['fee_entitlement_change_usd'])==0


def test_usdc_depeg_reprices_idle_funds_and_lp_inventory():
    rows=panel();row=rows[2];q={'USDC':5000*10**6,'ETH':5*10**15,'WETH':0,'LP':10**13}
    p,f=m.claims(q,row,rows[1]);cost=m.W.SCENARIOS['frictionless']
    r=m.stress(q,row,rows[1],cost)
    assert r['stable-depeg-lock30']['loss_usd']>1000
    assert not r['stable-depeg-lock30'].get('separate_tail')
    assert r['stable-depeg-lock30']['horizon_cash_unavailable_during_lock']
    assert r['stable-depeg-lock30']['incremental_shock_fees']==0


def test_headroom_missing_or_gas_unfunded_retains_no_invented_position():
    rows=panel();rows[1]['lower_gross']=m.MAX_TICK_LIQUIDITY;progress={}
    with pytest.raises(m.FinancialUnavailable,match='headroom'):
        m.run_book(rows,'F3','primary',progress)
    snap=m.partial_snapshot(progress)
    assert snap['literal_balances_reconciled'] and snap['current_atoms']['LP']==0 and not snap['events']
    assert m.run_book(rows,'matched-entry-inventory','primary')['terminal_atoms']['LP']==0
    q={'USDC':0,'ETH':45*10**13,'WETH':0,'LP':10**13}
    with pytest.raises(m.FinancialUnavailable,match='native gas-reserve sale'):
        m.liquidation(q,rows[0],rows[0],m.W.SCENARIOS['primary'])


def test_partial_terminal_failure_preserves_mint_and_exact_balances():
    rows=panel();progress={};original=m.liquidation
    try:
        def fail(q,row,entry,cost):
            if row['date']=='2026-09-01':raise m.FinancialUnavailable('invented terminal gap')
            return original(q,row,entry,cost)
        m.liquidation=fail
        with pytest.raises(m.FinancialUnavailable):m.run_book(rows,'F3','primary',progress)
        snap=m.partial_snapshot(progress)
        assert snap['literal_balances_reconciled'] and snap['current_atoms']['LP']>0
        assert [e['id'] for e in snap['events']]==['weth-entry','lp-mint']
    finally:m.liquidation=original


def test_tail_same_net_basis_and_native_wrapped_are_separate():
    rows=panel();q={'USDC':5000*10**6,'ETH':5*10**15,'WETH':0,'LP':10**13};cost=m.W.SCENARIOS['primary']
    r=m.stress(q,rows[0],rows[0],cost)['total-pool-position-loss']
    assert r['loss_usd']==m.liquidation(q,rows[0],rows[0],cost)[0]-m.liquidation({**q,'LP':0},rows[0],rows[0],cost)[0]
    assert r['loss_usd']<r['gross_affected_mark_usd']
    assert m.ASSETS['ETH']!=m.ASSETS['WETH']
    rows[6]['prices']['WETH']*=F(99,100)
    with pytest.raises(m.FinancialUnavailable,match='parity'):
        m.run_book(rows,'F3','primary')


def test_post_mutation_valuation_failure_retains_authoritative_lp_receipt():
    rows=panel();progress={};original=m.mark
    try:
        def fail(q,row,entry):
            if q['LP']:raise ValueError('invented mark failure after mint')
            return original(q,row,entry)
        m.mark=fail
        with pytest.raises(ValueError,match='invented mark'):m.run_book(rows,'F3','primary',progress)
        snap=m.partial_snapshot(progress)
        assert snap['literal_balances_reconciled'] and not snap['valued_events_cover_literal_events']
        assert [e['id'] for e in snap['literal_ledger_events']]==['weth-entry','lp-mint']
        assert snap['current_atoms']['LP']>0 and snap['stress_maxima']
        import json
        json.dumps(snap,allow_nan=False)
    finally:m.mark=original
