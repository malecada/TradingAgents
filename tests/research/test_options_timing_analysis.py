"""Invented constant six-day cash book and known linear beta, no source I/O."""
from copy import deepcopy
from fractions import Fraction as F
import pytest
from tradingagents.research_options_timing import analysis as a
from tradingagents.research_options_timing.schedule import DAY,HOUR
from tests.research.test_options_timing_adapter import metadata, selected, T


def inputs():
    choices={asset:item['selected'] for asset,item in selected().items()}
    options,futures=metadata();records={};benchmarks={}
    for asset in a.ASSETS:
        choices[asset]['expiry_ms']=T+7*DAY
        for row in options['optionSymbols']:
            if row['underlying']==asset+'USDT':row['expiryDate']=T+7*DAY
        records[asset]=[]
        for i in range(145):
            r={'time_ms':T+i*HOUR,'action_time_ms':T+i*HOUR+5000,'entry_available':True,'hedge_available':True,'exit_available':True,
                'valuation_available':True,'option_valuation_available':True,'perp_valuation_available':True,'index':'100'}
            for side,delta in [('call','.5'),('put','-.5'),('perp','0')]:
                r[side]={'unit':1,'bid':'20' if side!='perp' else '100','ask':'20.1' if side!='perp' else '100.1','bid_qty':'100','ask_qty':'100','mark':'20' if side!='perp' else '100','delta':delta}
            records[asset].append(r)
        benchmarks[asset]=['100']*145
    rules={'options':options,'futures':futures}
    return dict(entry_ms=T,selection=choices,records=records,initial_rules=rules,initial_rules_ms=T-60000,
        rule_vintages=[{'available_ms':T+d*DAY,'options':options,'futures':futures} for d in range(1,7)],
        funding={asset:{'coverage_known':True,'engine_inputs':{'expected_funding_times':[],'funding_events':[]}} for asset in a.ASSETS},benchmarks=benchmarks)


def test_eight_fixed_books_constant_price_loses_exact_spreads_fees():
    out=a.evaluate(**inputs())
    assert set(out['cells'])==set(a.CELLS) and out['count']==8 and not out['strategy_validated']
    for row in out['cells'].values():
        assert row['status']=='complete',row.get('reason')
        book=row['book'];c=a.COSTS[row['cost']]
        # Two shortoptions: base opening20 closing20.1, stress19.9/20.2.
        loss=F('.002') if row['cost']=='base' else F('.006')
        fee=4*F('.01')*F(c['option_fee_rate'])*100
        assert F(book['final']['profit'])==-loss-fee
        assert row['exposure']['beta']['BTC']['status']=='unavailable'


def test_unknown_funding_retains_four_unavailable_cells_without_ledger():
    data=inputs();data['funding']['BTC']={'coverage_known':False,'engine_inputs':None}
    out=a.evaluate(**data)
    assert all(r['status']=='unavailable' and 'book' not in r for r in out['cells'].values() if r['asset']=='BTC')
    assert all(r['status']=='complete' for r in out['cells'].values() if r['asset']=='ETH')


def test_drop_hour_never_compresses_path():
    data=inputs();data['records']['BTC'].pop(7)
    out=a.evaluate(**data)
    assert all('denominator' in r['reason'] for r in out['cells'].values() if r['asset']=='BTC')


def test_known_linear_beta_and_missingness():
    x=[((i*7)%13-6)*.001 for i in range(100)];y=[.002+.4*v for v in x]
    out=a.beta(y,x)
    assert out['coefficient']==pytest.approx(.4) and out['interval'][0]==pytest.approx(.4)
    assert a.beta(y[:10],x[:10])['status']=='unavailable'


def test_exposure_nav_denominator_and_unavailable_inputs():
    row={'index':'100','hedge_available':True,'valuation_available':True,'rule_scope':{'available':True},'call':{'delta':'.5'},'put':{'delta':'-.5'}}
    book={'trace':[{'hedge_quantity':'.08','option_quantity':'-.01','nav':'500'}]}
    out=a.exposure(book,[row],{'BTC':['100'],'ETH':['100']},1000)
    assert F(out['model_net_notional_initial_capital_fraction_max'])==F('.008')
    assert F(out['model_net_notional_NAV_fraction_max'])==F('.016')
    row['stale_sources']=['btc-index']
    assert a.exposure(book,[row],{'BTC':['100'],'ETH':['100']},1000)['model_net_notional_NAV_fraction_max'] is None
