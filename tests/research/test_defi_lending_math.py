import importlib.util
from pathlib import Path
import pytest
path=Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/lending_math.py'
s=importlib.util.spec_from_file_location('test_lending_math',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ACTIVE=(6<<48)|(1<<56)
def test_half_up_units_and_round_trip():
    assert m.ray_mul(1,m.RAY//2)==1
    assert m.ray_div(1,2*m.RAY)==1
    for income in (m.RAY,11*m.RAY//10,2*m.RAY,17*m.RAY//3):
        for amount in (10,123456,10**10):
            r=m.deposit_preview(amount,income,ACTIVE,0,0)
            out=m.withdrawal_preview(r['scaled_atoms'],income,ACTIVE,10**20)
            assert out['remaining_scaled_atoms']==0
            assert abs(out['underlying_credit_atoms']-amount)<=income//m.RAY+1

def test_interest_is_units_once_not_apr_or_log_pnl():
    r=m.deposit_preview(1000*10**6,m.RAY,ACTIVE,0,0)
    out=m.withdrawal_preview(r['scaled_atoms'],11*m.RAY//10,ACTIVE,2000*10**6)
    assert out['underlying_credit_atoms']==1100*10**6

def test_treasury_counts_toward_supply_cap():
    config=ACTIVE|(1000<<116)
    with pytest.raises(m.SourceModelUnavailable,match='treasury'):
        m.deposit_preview(100*10**6,m.RAY,config,850*10**6,60*10**6)
    r=m.deposit_preview(90*10**6,m.RAY,config,850*10**6,60*10**6)
    assert r['supply_with_treasury_before_atoms']==910*10**6

def test_frozen_deposit_block_but_withdrawal_permitted():
    frozen=ACTIVE|(1<<57)
    with pytest.raises(m.SourceModelUnavailable):m.deposit_preview(100,m.RAY,frozen,0,0)
    assert m.withdrawal_preview(100,m.RAY,frozen,100)['underlying_credit_atoms']==100

def test_paused_cash_shortfall_or_invalid_unit_never_assumed_zero():
    for config,cash in ((ACTIVE|(1<<60),100),(ACTIVE,99),((18<<48)|(1<<56),100)):
        with pytest.raises(m.SourceModelUnavailable):m.withdrawal_preview(100,m.RAY,config,cash)

def test_overflow_negative_and_unknown_treasury_rejected():
    with pytest.raises(ValueError):m.ray_mul(1<<255,m.RAY)
    with pytest.raises(ValueError):m.ray_div(1<<255,1)
    with pytest.raises(ValueError):m.ray_div(1,0)
    with pytest.raises(ValueError):m.deposit_preview(1,m.RAY,ACTIVE,0,None)
    with pytest.raises(ValueError):m.deposit_preview(-1,m.RAY,ACTIVE,0,0)

def test_disabled_cap_does_not_require_unknown_treasury_or_debt():
    r=m.supply_cap_sufficient_bound(1,None,ACTIVE,None,None,None,debt_bound_qualified=False)
    assert r['sufficient_cap_pass'] and r['cap_disabled']

def test_sufficient_treasury_bound_not_false_cap_failure():
    config=ACTIVE|(1000<<116)|(1000<<64)
    r=m.supply_cap_sufficient_bound(100*10**6,m.RAY,config,500*10**6,50*10**6,300*10**6,debt_bound_qualified=True)
    assert r['sufficient_cap_pass']
    r=m.supply_cap_sufficient_bound(200*10**6,m.RAY,config,500*10**6,50*10**6,300*10**6,debt_bound_qualified=True)
    assert not r['sufficient_cap_pass'] and r['inconclusive_if_false']
    with pytest.raises(m.SourceModelUnavailable):m.supply_cap_sufficient_bound(1,m.RAY,config,0,0,0,debt_bound_qualified=False)
