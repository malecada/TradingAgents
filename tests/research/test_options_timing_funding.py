"""Invented raw funding receipts; no exchange calls or financial calculation."""
from copy import deepcopy
import pytest
from tests.research.test_options_timing_adapter import receipt, T
from tradingagents.research_options_timing import funding as f
from tradingagents.research_options_timing.schedule import calendar,HOUR,DAY,nominal_ms


def row(t, rate='.001', **extra):
    return {'symbol':'BTCUSDT','fundingTime':t,'fundingRate':rate,'markPrice':'100','rateType':'Regular',**extra}


def fixture(events=None):
    events=[row(T+HOUR),row(T+2*HOUR,rate='-.002')] if events is None else events
    slots=calendar(T);out={'known':{},'daily':{},'final':{}}
    for spec in slots['known']:
        at=spec['scheduled_ms'];h=(at-T)//HOUR
        if h>2:continue
        if spec['id'].endswith('-futures-time'):value={'serverTime':at+250}
        elif spec['id'].endswith('-btc-perp-mark'):value={'symbol':'BTCUSDT','time':at+250,'nextFundingTime':nominal_ms(T,spec)+HOUR}
        else:continue
        out['known'][spec['id']]=receipt(spec['request'],value,nominal_ms(T,spec),hourly=True)
    for group in ('daily','final'):
        for spec in slots[group]:
            params=spec['request']['parameters']
            if not spec['request']['endpoint'].endswith('/fundingRate') or params['symbol']!='BTCUSDT':continue
            selected=[r for r in events if params['startTime']<=r['fundingTime']<=params['endTime']]
            out[group][spec['id']]=receipt(spec['request'],selected,spec['scheduled_ms'])
    return out


def run(data):return f.normalize(asset='BTC',entry_ms=T,exit_ms=T+2*HOUR,receipts=data)


def replace(data,group,name,value):
    spec=next(s for s in calendar(T)[group] if s['id']==name)
    data[group][name]=receipt(spec['request'],value,nominal_ms(T,spec),hourly=group=='known')


def test_known_actual_events_own_prior_inventory_and_signed_rates():
    result=run(fixture())
    assert result['coverage_known'] and result['engine_inputs'] is not None
    assert result['expected_funding_times']==[T+HOUR,T+2*HOUR]
    assert [r['owner_segment'] for r in result['events']]==[0,1]
    assert [r['rate'] for r in result['funding_events']]==['0.001','-0.002']
    assert all(r['local_bounds_ms']==[r['funding_time_ms']-1050,r['funding_time_ms']+1050] for r in result['events'])
    assert len(result['queries'])==47


def test_unannounced_event_is_not_discarded():
    result=run(fixture([row(T+HOUR),row(T+HOUR//2),row(T+2*HOUR)]))
    # Input must be ascending under the fixed response contract.
    assert not result['coverage_known']
    result=run(fixture([row(T+HOUR//2),row(T+HOUR),row(T+2*HOUR)]))
    assert result['coverage_known']
    assert len(result['funding_events'])==3
    assert result['events'][0]['announced'] is False


@pytest.mark.parametrize('fault',['missing-hour','stale','wrong-symbol','wrong-recipe','clock','missing-final','missing-announced'])
def test_source_gaps_never_become_empty_known_funding(fault):
    data=fixture()
    if fault=='missing-hour':del data['known']['h0001-btc-perp-mark']
    elif fault=='stale':replace(data,'known','h0000-btc-perp-mark',{'symbol':'BTCUSDT','time':T+250,'nextFundingTime':T})
    elif fault=='wrong-symbol':replace(data,'known','h0000-btc-perp-mark',{'symbol':'ETHUSDT','time':T+250,'nextFundingTime':T+HOUR})
    elif fault=='wrong-recipe':data['final']['final-btc-0']['request']['parameters']['limit']=999
    elif fault=='clock':data['known']['h0001-futures-time']['metadata']['clock_consistent']=False
    elif fault=='missing-final':del data['final']['final-btc-1']
    else:data=fixture([])
    result=run(data)
    assert not result['coverage_known'] and result['engine_inputs'] is None and result['reasons']


def test_conflicting_duplicate_retains_versions_and_invalidates():
    data=fixture();replace(data,'daily','d01-btc-funding',[row(T+HOUR,rate='.01'),row(T+2*HOUR,rate='-.002')])
    result=run(data)
    assert not result['coverage_known'] and any('conflicting' in x['reason'] for x in result['reasons'])
    assert {x['raw']['fundingRate'] for x in result['event_versions'] if x['raw']['fundingTime']==T+HOUR}=={'.001','.01'}


@pytest.mark.parametrize('fault',['full-page','out-of-query','missing-mark','special','missing-type'])
def test_history_semantics_unavailable(fault):
    data=fixture();rows=[row(T+HOUR),row(T+2*HOUR,rate='-.002')]
    if fault=='full-page':rows=[row(T+HOUR)]*1000
    elif fault=='out-of-query':rows.append(row(T+23*DAY))
    elif fault=='missing-mark':del rows[0]['markPrice']
    elif fault=='special':rows[0]['rateType']='Special'
    elif fault=='missing-type':del rows[0]['rateType']
    replace(data,'final','final-btc-0',rows)
    result=run(data)
    assert not result['coverage_known'] and result['engine_inputs'] is None
    assert any(x['source']=='final-btc-0' for x in result['event_versions'])


def test_missing_type_requires_actual_bootstrap_coin_identity():
    data=fixture()
    for group in ('daily','final'):
        for name in list(data[group]):
            import base64,json
            rows=json.loads(base64.b64decode(data[group][name]['body_base64']))
            for r in rows:r.pop('rateType',None)
            replace(data,group,name,rows)
    spec=next(s for s in calendar(T)['bootstrap'] if s['id']=='initial-futures-rules')
    value={'symbols':[{'symbol':'BTCUSDT','baseAsset':'BTC','quoteAsset':'USDT','marginAsset':'USDT','underlyingType':'COIN','contractType':'PERPETUAL','status':'TRADING'}]}
    bootstrap=receipt(spec['request'],value,nominal_ms(T,spec),hourly=group=='known')
    result=f.normalize(asset='BTC',entry_ms=T,exit_ms=T+2*HOUR,receipts=data,bootstrap_receipt=bootstrap)
    assert result['coverage_known'] and all(x['rate_type']=='unspecified_crypto' for x in result['events'])
    value['symbols'][0]['underlyingType']='INDEX'
    bootstrap=receipt(spec['request'],value,nominal_ms(T,spec),hourly=group=='known')
    assert not f.normalize(asset='BTC',entry_ms=T,exit_ms=T+2*HOUR,receipts=data,bootstrap_receipt=bootstrap)['coverage_known']


def test_action_boundary_unknown_and_outside_rows_retained():
    events=[row(T),row(T+HOUR),row(T+HOUR+5000),row(T+2*HOUR),row(T+3*HOUR)]
    result=run(fixture(events))
    assert not result['coverage_known']
    boundary=next(r for r in result['events'] if r['funding_time_ms']==T+HOUR+5000)
    assert 'boundary' in boundary['reason']
    assert result['events'][0]['exclusion']=='before-entry'
    assert result['events'][-1]['exclusion']=='after-exit'
    assert len(result['event_versions'])>=5


def test_compatible_clock_hull_does_not_falsely_tighten_and_conflict_unknown():
    clocks=[{'request_ms':T,'retrieval_ms':T+100,'offset_low_ms':0,'offset_high_ms':100},
            {'request_ms':T+1000,'retrieval_ms':T+1100,'offset_low_ms':500,'offset_high_ms':600}]
    assert f._bounds(T+HOUR//2,clocks)==[T+HOUR//2-1600,T+HOUR//2+1000]
    clocks[1].update(offset_low_ms=4000,offset_high_ms=4100)
    with pytest.raises(ValueError,match='contradictory'):f._bounds(T+HOUR//2,clocks)
    with pytest.raises(ValueError,match='within one hour'):f._bounds(T+3*HOUR,clocks)


def test_empty_unknown_and_conditionally_known_no_event_are_distinct():
    unknown=run({'known':{},'daily':{},'final':{}})
    assert unknown['expected_funding_times']==[] and unknown['engine_inputs'] is None
    data=fixture([])
    for h in (0,1):replace(data,'known',f'h{h:04d}-btc-perp-mark',{'symbol':'BTCUSDT','time':T+h*HOUR+2250,'nextFundingTime':T+8*HOUR})
    known=run(data)
    assert known['coverage_known'] and known['engine_inputs']=={'expected_funding_times':[],'funding_events':[]}
    assert all(x['status']=='outside-held-window' for x in known['events'])


def test_next_event_after_provider_time_but_not_future_at_arrival_is_unknown():
    data=fixture()
    replace(data,'known','h0001-btc-perp-mark',{'symbol':'BTCUSDT','time':T+HOUR+2250,'nextFundingTime':T+HOUR+2260})
    result=run(data)
    assert not result['coverage_known'] and any('local receipt availability' in r['reason'] for r in result['reasons'])
