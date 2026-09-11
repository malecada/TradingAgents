"""Invented option identities/rules only; no observations or acquisition."""
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'))
import options_policy_selection as select

START=int(datetime(2027,1,1,tzinfo=timezone.utc).timestamp()*1000)


def row(day,strike,side,step='.01',minimum='.01',maximum='100',tick='.01'):
    expiry=START+day*select.DAY
    date=datetime.fromtimestamp(expiry//1000,timezone.utc).strftime('%y%m%d')
    return {'symbol':f'BTC-{date}-{strike}-{side[0]}','underlying':'BTCUSDT','quoteAsset':'USDT','side':side,'expiryDate':expiry,
        'strikePrice':str(strike),'unit':1,'minQty':minimum,'maxQty':maximum,
        'filters':[{'filterType':'LOT_SIZE','minQty':minimum,'maxQty':maximum,'stepSize':step},
                   {'filterType':'PRICE_FILTER','tickSize':tick}]}


def fixture():return {'optionContracts':[{'underlying':'BTCUSDT','baseAsset':'BTC','quoteAsset':'USDT','settleAsset':'USDT'}],
    'optionSymbols':[row(day,strike,side) for day in (20,29,31) for strike in (90,110) for side in ('CALL','PUT')]}


def run(data):return select.select(data,asset='BTC',entry_ms=START,index='100')


def test_fixed_expiry_strike_ties_no_premium_input():
    data=fixture();result=run(data)
    assert result['status']=='complete' and result['candidate_count']==6
    assert result['selected']['expiry_ms']==START+29*select.DAY
    assert result['selected']['strike']=='90' and result['selected']['quantity']=='0.01'
    assert result['selected']['exit_ms']==START+28*select.DAY
    for r in data['optionSymbols']:r['premium']='999999999'
    assert run(data)==result


def test_exact_minimum_common_quantity_and_no_capital_scaling():
    data=fixture();data['optionSymbols']=[row(30,100,'CALL',step='.02',minimum='.03'),row(30,100,'PUT',step='.03',minimum='.04')]
    assert run(data)['selected']['quantity']=='0.07'


@pytest.mark.parametrize('mutation',['unit','tick','maximum','duplicatefilter','missingfilter'])
def test_selected_rule_failure_does_not_choose_farther_pair(mutation):
    data=fixture();chosen=next(r for r in data['optionSymbols'] if r['expiryDate']==START+29*select.DAY and r['strikePrice']=='90' and r['side']=='CALL')
    if mutation=='unit':chosen['unit']=2
    if mutation=='tick':chosen['filters'][1]['tickSize']='.02'
    if mutation=='maximum':chosen['maxQty']='.001';chosen['filters'][0]['maxQty']='.001'
    if mutation=='duplicatefilter':chosen['filters'].append(dict(chosen['filters'][0]))
    if mutation=='missingfilter':chosen['filters'].pop()
    result=run(data);assert result['status']=='unavailable' and result['selected']['strike']=='90'


def test_missing_put_never_manufactured_and_duplicate_identity_excluded():
    data=fixture();data['optionSymbols']=[r for r in data['optionSymbols'] if r['side']=='CALL']
    assert run(data)['selected'] is None
    data=fixture();data['optionSymbols'].append(deepcopy(data['optionSymbols'][0]))
    result=run(data);assert result['candidate_count']==5


def test_bad_parent_or_expiry_clock_and_bool_unit():
    data=fixture();data['optionContracts'][0]['settleAsset']='OTHER'
    assert run(data)['status']=='unavailable'
    data=fixture()
    for r in data['optionSymbols']:r['expiryDate']+=1
    assert run(data)['selected'] is None
    data=fixture()
    for r in data['optionSymbols']:r['unit']=True
    assert run(data)['status']=='unavailable'


def test_incompatible_offset_grids_unavailable_without_resizing():
    data=fixture();data['optionSymbols']=[row(30,100,'CALL',step='.02',minimum='.01'),row(30,100,'PUT',step='.02',minimum='.02')]
    result=run(data)
    assert result['status']=='unavailable' and 'no intersection' in result['reason']
    assert result['selected']['strike']=='100'


def test_equal_and_zero_aligned_grids_keep_minimum_quantity():
    data=fixture();data['optionSymbols']=[row(30,100,'CALL',step='.02',minimum='.02'),row(30,100,'PUT',step='.03',minimum='.03')]
    assert run(data)['selected']['quantity']=='0.06'
    data['optionSymbols'][1]=row(30,100,'PUT',step='.02',minimum='.08')
    assert run(data)['selected']['quantity']=='0.08'
