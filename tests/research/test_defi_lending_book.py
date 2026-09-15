import importlib.util
from datetime import date, timedelta
from fractions import Fraction as F
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('tested_lending_book',Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/lending_book.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def panel():
    return [{'date':(date(2025,9,1)+timedelta(days=i)).isoformat(),
             'prices':{'USDC':F(1),'ETH':F(2000)},'income':10**27,
             'config':(6<<48)|(1<<56),'contract_cash':10**15,'source_model_qualified':True}
            for i in range(366)]


def test_flat_conservation_and_exact_four_gas_debits():
    r=m.run_book(panel(),'frictionless')
    assert F(r['net_cash_profit_usd'])==-10
    assert F(r['cash_attribution']['interest_entitlement_change_usd'])==0
    r=m.run_book(panel(),'primary')
    # Supply/withdraw retain9990USDC; four gas debits leave0.0046ETH.
    # Its terminal sale retains 0.997*0.999, rounded down to USDC atoms.
    terminal_usdc=9990*10**6+(F(46,10000)*2000*F(997,1000)*F(999,1000)*10**6).__floor__()
    expected=F(terminal_usdc,10**6)-10-10000
    assert F(r['net_cash_profit_usd'])==expected
    assert sum(e['gas_atoms'] for e in r['events'])==4*10**14
    assert r['terminal_atoms']=={'USDC':terminal_usdc,'ETH':0,'AUSDC_SCALED':0}


def test_interest_paid_once_with_literal_atom_replay():
    rows=panel()
    for row in rows[2:]:row['income']=11*10**26
    r=m.run_book(rows,'frictionless')
    assert F(r['net_cash_profit_usd'])==F('689.3')
    assert F(r['cash_attribution']['interest_entitlement_change_usd'])==F('699.3')
    assert F(r['cash_attribution']['market_usd'])==0
    balances=dict(r['initial_atoms'])
    for event in r['events']:
        for asset,q in event['debits_atoms'].items():balances[asset]-=q
        for asset,q in event['credits_atoms'].items():balances[asset]+=q
        balances['ETH']-=event['gas_atoms']
        assert balances==event['after_atoms'] and min(balances.values())>=0
    assert balances==r['terminal_atoms']
    assert F(r['log_convention_diagnostic']['difference_usd'])<0


def test_interest_price_cross_term_and_initial_gas_losses_reconcile():
    rows=panel()
    for row in rows[2:]:
        row['income']=11*10**26;row['prices']={'USDC':F(4,5),'ETH':F(1000)}
    r=m.run_book(rows,'frictionless')
    # Wallet2997 + claim7692.3 USDC, plus0.005ETH at1000, minus route.
    assert F(r['net_cash_profit_usd'])==F('10689.3')*F(4,5)+5-10-10000
    assert F(r['cash_attribution']['market_usd'])==-2003
    assert F(r['cash_attribution']['interest_entitlement_change_usd'])==F('559.44')


def test_risk_uses_drift_and_credit_depeg_not_exempt_tail():
    rows=panel()
    flat=m.run_book(rows,'frictionless')
    s=flat['stress']['combined-credit-depeg-outage']
    assert F(s['loss_fraction'])>F(48,100) and not s.get('separate_tail')
    assert flat['numerical_risk_pass_conditional']
    for row in rows[2:]:row['income']=2*10**27
    large=m.run_book(rows,'frictionless')
    assert large['absolute_floor_pass_conditional']
    assert not large['numerical_risk_pass_conditional']
    assert F(large['stress']['combined-credit-depeg-outage']['loss_fraction'])>F(1,2)


def test_cap_unknown_or_bound_false_is_unavailable_not_cap_failure():
    rows=panel();rows[1]['config']|=1000000<<116
    with pytest.raises(m.FinancialUnavailable,match='unqualified'):
        m.run_book(rows,'primary')
    rows[1].update(scaled_supply=10**18,stored_treasury=0,current_debt_upper_bound=0,debt_bound_qualified=True)
    with pytest.raises(m.FinancialUnavailable,match='inconclusive'):
        m.run_book(rows,'primary')


def test_pause_or_cash_gap_preserves_partial_book():
    rows=panel();rows[-1]['contract_cash']=0
    progress={}
    with pytest.raises(m.FinancialUnavailable,match='insufficient observed contract cash'):
        m.run_book(rows,'primary',progress)
    snapshot=m.partial_snapshot(progress)
    assert snapshot['literal_balances_reconciled']
    assert snapshot['current_atoms']['AUSDC_SCALED']==6993*10**6
    assert [e['id'] for e in snapshot['events']]==['supply']
    assert len(snapshot['states'])==366
    rows=panel();rows[-1]['config']|=1<<60
    with pytest.raises(m.FinancialUnavailable,match='active/paused'):
        m.run_book(rows,'primary')


def test_frozen_after_entry_can_withdraw_and_source_model_must_be_qualified():
    rows=panel()
    for row in rows[2:]:row['config']|=1<<57
    assert m.run_book(rows,'frictionless')['terminal_atoms']['AUSDC_SCALED']==0
    rows[2]['source_model_qualified']=False
    with pytest.raises(m.FinancialUnavailable,match='unqualified'):
        m.run_book(rows,'primary')


def test_tail_writeoff_is_net_same_basis_and_gas_cannot_be_borrowed():
    row=panel()[0];cost=m.W.SCENARIOS['primary']
    q={'USDC':2997*10**6,'AUSDC_SCALED':6993*10**6,'ETH':48*10**14}
    s=m.stress(q,row,cost)['total-contract-position-loss']
    assert s['loss_usd']==m.liquidation(q,row,cost)[0]-m.liquidation({**q,'AUSDC_SCALED':0},row,cost)[0]
    assert s['loss_usd']<6993 and s['separate_tail']
    with pytest.raises(m.FinancialUnavailable,match='gas-reserve exit'):
        m.liquidation({**q,'ETH':2*10**14},row,cost)


def test_bad_calendar_index_or_float_marks_fail_closed():
    with pytest.raises(ValueError):m.run_book(panel()[:-1],'primary')
    rows=panel();rows[6]['prices']['ETH']=2000.0
    with pytest.raises(ValueError):m.run_book(rows,'primary')
    rows=panel();rows[1]['income']=2*10**27
    with pytest.raises(m.FinancialUnavailable,match='decreasing'):
        m.run_book(rows,'primary')


def test_ceiling_dominates_actual_half_up_units_not_continuous_units():
    rows=panel()
    for row in rows:row['income']=15*10**26
    bound=m.opportunity_ceiling(rows)
    s=bound['ceiling_scaled_atoms'];claim=bound['ceiling_terminal_claim_atoms'];a=bound['deposit_atoms']
    actual_s=m.L.ray_div(a,15*10**26)
    actual_claim=m.L.ray_mul(actual_s,15*10**26)
    assert s>=actual_s and claim>=actual_claim
    assert bound['upper_bound_below_absolute_floor'] and not bound['primary_pass']
    r=m.run_book(rows,'frictionless')
    b=bound['exact_net_cash_profit_upper_bound']
    assert F(b['numerator'],b['denominator'])>=F(r['net_cash_profit_usd'])+10
    # Counterexample to incorrectly using a continuous claim as an upper bound.
    assert m.L.ray_mul(m.L.ray_div(1,15*10**26),15*10**26)==2
    assert F(1)*F(15,10)/F(15,10)==1


def test_post_mutation_valuation_failure_keeps_authoritative_literal_receipt():
    rows=panel();progress={};original=m.mark
    try:
        def fail(q,row):
            if q['AUSDC_SCALED']:raise ValueError('invented mark failure after supply')
            return original(q,row)
        m.mark=fail
        with pytest.raises(ValueError,match='invented mark'):m.run_book(rows,'primary',progress)
        snap=m.partial_snapshot(progress)
        assert snap['literal_balances_reconciled'] and not snap['valued_events_cover_literal_events']
        assert snap['literal_ledger_events'][0]['id']=='supply'
        assert snap['current_atoms']['AUSDC_SCALED']>0
        assert snap['stress_maxima'] and snap['current_source_row']['date']=='2025-09-02'
        import json
        json.dumps(snap,allow_nan=False)
    finally:m.mark=original


def test_ceiling_does_not_require_unused_withdrawal_fields():
    rows=panel()
    for row in rows:
        del row['contract_cash'];del row['config']
    assert m.opportunity_ceiling(rows)['upper_bound_below_absolute_floor']


def test_explicit_cap_assumption_keeps_proof_unavailable():
    rows=panel();rows[1]['config']|=1000000<<116
    r=m.run_book(rows,'primary',cap_assumption='assume-cap-for-diagnostic')
    assert r['entry_cap_check']['cap_unproved'] and not r['strict_entry_cap_proved']
    assert r['entry_cap_check']['sufficient_cap_pass'] is None
    assert not r['implementation_admitted'] and not r['promotion_admitted']


def test_ceiling_accepts_only_fixed_endpoints_without_midyear_invention():
    rows=panel();expected=m.opportunity_ceiling(rows)
    sparse=[rows[0],rows[1],rows[-1]]
    for row in sparse:
        del row['config'];del row['contract_cash']
    del sparse[0]['income'];del sparse[1]['prices']
    assert m.opportunity_ceiling(sparse)==expected
    sparse[1]['date']='2025-09-03'
    with pytest.raises(m.FinancialUnavailable,match='fixed ceiling endpoint'):m.opportunity_ceiling(sparse)
