import importlib.util
from pathlib import Path
from fractions import Fraction as F
from datetime import date,timedelta
import pytest
path=Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/wrapper_book.py'
s=importlib.util.spec_from_file_location('tested_wrapper_book',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def panel():
    return [{'date':(date(2025,9,1)+timedelta(days=i)).isoformat(),'prices':{'USDC':F(1),'ETH':F(2000),'WST':F(2400)}} for i in range(366)]
def test_flat_frictionless_conserves_all_capital_and_route():
    for policy in m.POLICIES:
        r=m.run_book(panel(),policy,'frictionless')
        assert F(r['net_cash_profit_usd'])==-10
        assert r['terminal_atoms']['ETH']==r['terminal_atoms']['WST']==0
        assert F(r['cash_attribution']['market_usd'])==0

def test_flat_primary_spends_costs_and_wrapper_extra_hop_is_not_free():
    profits={p:F(m.run_book(panel(),p,'primary')['net_cash_profit_usd']) for p in m.POLICIES}
    assert profits['F2']<profits['wallet-ETH25']<profits['wallet-cash']<-10

def test_wrapper_increment_distinct_from_eth_beta():
    rows=panel()
    for i,row in enumerate(rows):
        if i>1:row['prices']['WST']*=F(11,10);row['prices']['ETH']*=F(11,10)
    r=m.run_book(rows,'F2','frictionless');c=m.run_book(rows,'wallet-ETH25','frictionless')
    assert abs(F(r['net_cash_profit_usd'])-F(c['net_cash_profit_usd']))<F(1,10**6)
    rows=panel()
    for row in rows[2:]:row['prices']['WST']*=F(11,10)
    r=m.run_book(rows,'F2','frictionless');c=m.run_book(rows,'wallet-ETH25','frictionless')
    assert abs((F(r['net_cash_profit_usd'])-F(c['net_cash_profit_usd']))-F(999,4))<F(1,10**6)

def test_gas_mark_loss_included_and_depeg_hits_cash():
    rows=panel()
    for row in rows[2:]:row['prices']['USDC']=F(4,5);row['prices']['ETH']=F(1000)
    r=m.run_book(rows,'wallet-cash','frictionless')
    assert F(r['net_cash_profit_usd'])==-2013

def test_missing_day_price_or_unfunded_gas_rejected():
    with pytest.raises(ValueError):m.run_book(panel()[:-1],'F2','primary')
    rows=panel();rows[7]['prices']['WST']=0
    with pytest.raises(ValueError):m.run_book(rows,'F2','primary')
    with pytest.raises(ValueError):m.liquidation({'USDC':100,'ETH':1,'WST':10},panel()[0]['prices'],m.SCENARIOS['primary'])

def test_loss_book_not_log_returns_and_atom_ledger_reconciles():
    rows=panel()
    for row in rows[2:]:row['prices']['WST']=F(1200)
    r=m.run_book(rows,'F2','primary')
    assert F(r['net_cash_profit_usd'])<-1200
    assert F(r['log_convention_diagnostic']['difference_usd'])<0
    for event in r['events']:
        expected=dict(event['before_atoms'])
        for a,q in event['debits_atoms'].items():expected[a]-=q
        for a,q in event['credits_atoms'].items():expected[a]+=q
        expected['ETH']-=event['gas_atoms']
        assert expected==event['after_atoms']
        assert min(expected.values())>=0

def test_tail_loss_uses_same_net_liquidation_basis():
    q={'USDC':7500*10**6,'ETH':5*10**15,'WST':10**18};p=panel()[0]['prices'];c=m.SCENARIOS['primary']
    result=m.stress(q,p,c)['total-wrapper-position-loss']
    without={**q,'WST':0}
    assert result['loss_usd']==m.liquidation(q,p,c)[0]-m.liquidation(without,p,c)[0]
    assert result['loss_usd']<result['gross_affected_mark_usd']

def test_late_failure_retains_current_cash_events_and_states():
    rows=panel();progress={}
    # Force unsupported terminal sale units without touching real observations.
    original=m.sell_value
    try:
        def altered(q,a,p,c):
            if a=='WST' and p['WST']==F(1234):return 0
            return original(q,a,p,c)
        m.sell_value=altered;rows[-1]['prices']['WST']=F(1234)
        with pytest.raises(ValueError,match='rounds to zero'):m.run_book(rows,'F2','primary',progress)
        partial=m.partial_snapshot(progress)
        assert partial['literal_balances_reconciled'] and partial['current_atoms']['WST']>0
        assert partial['events'][0]['id']=='entry' and len(partial['states'])>=366
    finally:m.sell_value=original
