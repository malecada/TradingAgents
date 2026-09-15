import importlib.util
from pathlib import Path
from datetime import date,timedelta
from fractions import Fraction as F
import pytest
HERE=Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15'
spec=importlib.util.spec_from_file_location('tested_protocol_results',HERE/'protocol_financial_results.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def summary():
    rows=[]
    for i in range(366):
        d=(date(2025,9,1)+timedelta(days=i)).isoformat()
        values={'aave-income':10**27,'aave-config':(6<<48)|(1<<56)|(1000000<<116),
                'aave-contract-cash':10**15,'aave-scaled-supply':10**9,'aave-total-supply':10**9}
        rows.append({'date':d,'block':{'hash':'0x'+format(i+1,'064x')},
                    'oracle_prices':{'status':'complete','value':{'ETH':2000*10**8,'USDC':10**8}},
                    'supply_identity':{'status':'complete'},'fields':{k:{'status':'complete','value':{'words':[v]}} for k,v in values.items()}})
    return {'status':'complete','rows':rows,'boundary_identity_witnesses_complete':True,'boundary_code_witnesses_equal':True}


def benchmarks():
    return {'B'+str(i):{s:({'status':'unavailable','reason':'actual account cash terms unproved'} if i==1 else
                         {'status':'complete','net_cash_profit_usd':'0','conditional_numeric_risk_pass':True})
                       for s in m.SCENARIOS} for i in range(10)}


def execute(s):
    saved={}
    def publish(name,value):
        assert name not in saved
        if name.endswith('.json') and not name.endswith('-attempt.json') and name not in ('financial-summary.json',):
            assert name[:-5]+'-attempt.json' in saved
        saved[name]=value
    cells=m.financial(s,benchmarks(),'F1',publish)
    return saved,cells


def test_cap_unproved_numerical_book_and_ceiling_never_promote():
    saved,cells=execute(summary());expected,outputs=m.manifests('F1')
    assert set(saved)==set(outputs) and {c['id'] for c in cells}==set(expected)
    assert saved['2026-strict-entry-feasibility.json']['status']=='unavailable'
    r=saved['2026-f1-primary.json']
    assert r['status']=='complete' and not r['strict_entry_cap_proved']
    assert F(r['net_cash_profit_usd'])<-10
    assert saved['2026-opportunity-ceiling.json']['upper_bound_below_absolute_floor']
    decision=saved['financial-summary.json']['primary_decision']
    assert decision['status']=='unavailable' and not decision['known_comparator_numerical_pass_only']
    assert saved['financial-summary.json']['comparisons']['primary']['B1']['status']=='unavailable'
    assert all(not saved[f'{year}-f1-primary-attempt.json']['attempted'] for year in ('2024','2025'))


def test_daily_cash_gap_keeps_endpoint_ceiling_and_wallet_controls():
    s=summary();s['status']='unavailable';s['rows'][20]['fields']['aave-contract-cash']={'status':'unavailable','reason':'invented missing cash'}
    saved,cells=execute(s)
    assert saved['2026-f1-primary.json']['status']=='unavailable'
    assert saved['2026-opportunity-ceiling.json']['status']=='complete'
    assert saved['2026-wallet-cash-primary.json']['status']=='complete'
    assert saved['2026-wallet-eth25-primary.json']['status']=='complete'
    assert all(v['status']=='unavailable' for v in saved['financial-summary.json']['comparisons']['primary'].values())


def test_missing_terminal_price_never_filled_or_promoted():
    s=summary();s['status']='unavailable';s['rows'][-1]['oracle_prices']={'status':'unavailable','reason':'invented failed mark'}
    saved,cells=execute(s)
    assert saved['2026-opportunity-ceiling.json']['status']=='unavailable'
    assert saved['2026-wallet-cash-primary.json']['status']=='unavailable'
    assert not saved['2026-f1-primary-attempt.json']['attempted']


def test_positive_ceiling_is_inconclusive_and_risk_cannot_be_rescued():
    s=summary()
    for row in s['rows'][2:]:row['fields']['aave-income']['value']['words']=[2*10**27]
    saved,cells=execute(s)
    assert not saved['2026-opportunity-ceiling.json']['upper_bound_below_absolute_floor']
    r=saved['2026-f1-primary.json']
    assert r['absolute_floor_pass_conditional'] and not r['numerical_risk_pass_conditional']
    assert saved['financial-summary.json']['primary_decision']['status']=='unavailable'


def test_measurement_failure_preserves_remaining_unattempted_cells():
    s=summary();original=m.L.run_book
    try:
        def fail(*args,**kwargs):raise ValueError('invented book defect')
        m.L.run_book=fail
        saved,cells=execute(s)
        assert saved['financial-summary.json']['measurement_defect']
        assert saved['2026-f1-primary-attempt.json']['attempted']
        assert not saved['2026-f1-doubled-attempt.json']['attempted']
        assert not saved['2026-wallet-cash-primary-attempt.json']['attempted']
        assert len(cells)==len(m.manifests('F1')[0])
    finally:m.L.run_book=original


def test_f3_full_grid_preserves_matched_inventory_and_wallet_controls():
    s=summary();sqrt=m.LP.T.sqrt_at_tick(-200000)
    for row in s['rows']:
        values={'lp-slot0':[sqrt,-200000,0,1,1,0,True],'lp-liquidity':[10**20],'lp-fee0':[0],'lp-fee1':[0],
                'lp-lower':[0], 'lp-upper':[0], 'lp-max-liquidity':[m.LP.MAX_TICK_LIQUIDITY]}
        row['fields']={k:{'status':'complete','value':{'words':v}} for k,v in values.items()}
        row['supply_identity']=None
    saved={}
    def publish(name,value):assert name not in saved;saved[name]=value
    cells=m.financial(s,benchmarks(),'F3',publish)
    expected,outputs=m.manifests('F3')
    assert set(saved)==set(outputs) and {c['id'] for c in cells}==set(expected)
    a=saved['2026-f3-primary.json'];b=saved['2026-matched-entry-inventory-primary.json']
    assert a['status']==b['status']=='complete'
    assert a['entry_plan']==b['entry_plan']
    assert F(a['net_cash_profit_usd'])<F(b['net_cash_profit_usd'])
    assert saved['financial-summary.json']['comparisons']['primary']['matched-entry-inventory']['status']=='complete'
    assert saved['financial-summary.json']['primary_decision']['status']=='unavailable'
