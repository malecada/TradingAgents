"""Invented raw HTTP receipts, grids and clock intervals; no market I/O."""
import base64
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
import pytest

from tradingagents.research_options_timing import adapter as a
from tradingagents.research_options_timing.schedule import request,DAY,HOUR
from tradingagents.research_options_timing.transport import request_url

T=1798761600000


def metadata():
    expiry=T+30*DAY;date=datetime.fromtimestamp(expiry//1000,timezone.utc).strftime('%y%m%d')
    options={'optionContracts':[],'optionSymbols':[]};futures={'symbols':[]}
    for asset in ('BTC','ETH'):
        options['optionContracts'].append({'underlying':asset+'USDT','baseAsset':asset,'quoteAsset':'USDT','settleAsset':'USDT'})
        for side in ('CALL','PUT'):
            options['optionSymbols'].append({'symbol':f'{asset}-{date}-100-{side[0]}','underlying':asset+'USDT','quoteAsset':'USDT','side':side,
                'expiryDate':expiry,'strikePrice':'100','unit':1,'minQty':'.01','maxQty':'1000','filters':[
                    {'filterType':'LOT_SIZE','minQty':'.01','maxQty':'1000','stepSize':'.01'},
                    {'filterType':'PRICE_FILTER','minPrice':'.1','maxPrice':'1000000','tickSize':'.1'}]})
        futures['symbols'].append({'symbol':asset+'USDT','baseAsset':asset,'quoteAsset':'USDT','marginAsset':'USDT','status':'TRADING','contractType':'PERPETUAL','filters':[
            {'filterType':'LOT_SIZE','minQty':'.001','maxQty':'1000','stepSize':'.001'},
            {'filterType':'PRICE_FILTER','minPrice':'.1','maxPrice':'1000000','tickSize':'.1'},
            {'filterType':'MIN_NOTIONAL','notional':'5'}]})
    return options,futures


def receipt(recipe,value,at,*,hourly=False):
    deadline=at+5000
    if hourly:at+=2000
    raw=json.dumps(value,separators=(',',':')).encode();sha=hashlib.sha256(raw).hexdigest()
    return {'status':'received','request':recipe,'body_base64':base64.b64encode(raw).decode(),'body_bytes':len(raw),'body_sha256':sha,
            'metadata':{'attempted':True,'body_complete':True,'clock_consistent':True,'within_controller_deadline':True,'http_status':200,'error':None,
                        'request_ms':at+200,'controller_retrieval_ms':at+300,'retrieval_ms':at+290,'request_url':request_url(recipe),'body_bytes':len(raw),'body_sha256':sha,
                        'request_monotonic_ns':(at+200)*1000000,'retrieval_monotonic_ns':(at+290)*1000000,'controller_retrieval_monotonic_ns':(at+300)*1000000,
                        'controller_window_start_ms':at,'controller_window_start_monotonic_ns':at*1000000,
                        'controller_deadline_ms':deadline,'controller_deadline_monotonic_ns':deadline*1000000}}


def initial():
    options,futures=metadata();known={}
    for key,spec in a.known_requests().items():
        if spec['kind']=='time':value={'serverTime':T+2250}
        elif spec['kind']=='index':value={'indexPrice':'100','time':T+2250}
        elif spec['kind']=='depth':value={'T':T+2200,'E':T+2250,'lastUpdateId':1,'bids':[['100','100']],'asks':[['100.1','100']]}
        else:value={'symbol':spec['parameters']['symbol'],'markPrice':'100','time':T+2250,'nextFundingTime':T+8*HOUR}
        known[key]=receipt(a._recipe(spec),value,T,hourly=True)
    return receipt(request('eapi','exchangeInfo'),options,T-60000),known,futures


def selected():
    meta,known,_=initial();return a.select_initial(meta,known,entry_ms=T)


def test_initial_real_adapter_all_roles_and_fixed_selection():
    result=selected()
    assert {v['status'] for v in result.values()}=={'complete'}
    assert all(v['selected']['quantity']=='0.01' and v['selected']['expiry_ms']==T+30*DAY for v in result.values())


@pytest.mark.parametrize('fault',['body','clock','late','identity'])
def test_initial_bad_source_preserves_other_asset(fault):
    meta,known,_=initial();row=known['btc-index']
    if fault=='body':row['body_sha256']='0'*64
    if fault=='clock':row['metadata']['clock_consistent']=False
    if fault=='late':row['metadata']['controller_retrieval_ms']=T+5001
    if fault=='identity':row['request']=request('eapi','index',underlying='ETHUSDT')
    out=a.select_initial(meta,known,entry_ms=T)
    assert out['BTC']['status']=='unavailable' and out['ETH']['status']=='complete'


def test_both_clocks_required_and_prefixed_roles_rejected():
    meta,known,_=initial();known['futures-time']['metadata']['body_complete']=False
    assert all(v['status']=='unavailable' for v in a.select_initial(meta,known,entry_ms=T).values())
    _,known,_=initial()
    assert all(v['status']=='unavailable' for v in a.select_initial(meta,{'h0000-'+k:v for k,v in known.items()},entry_ms=T).values())


def record(at=T):
    return {'time_ms':at,'entry_available':True,'hedge_available':True,'exit_available':True,'valuation_available':True,
            'option_valuation_available':True,'perp_valuation_available':True,
            'call':{'bid':'20','ask':'21'},'put':{'bid':'20','ask':'21'},'perp':{'bid':'100','ask':'100.1'}}


def apply(records=None,vintages=(),stress=False,initial_data=None):
    options,futures=metadata()
    return a.apply_rule_vintages(records or [record()],asset='BTC',selection=selected()['BTC']['selected'],
        initial=initial_data or {'options':options,'futures':futures},initial_ms=T-60000,vintages=vintages,stress=stress)


def test_effective_slippage_does_not_claim_tick_order():
    out,rules=apply(stress=True)
    assert out[0]['hedge_available'] and out[0]['entry_available'] and out[0]['exit_available']
    assert 'not an order price' in out[0]['rule_scope']['qualification']
    assert rules['perp']['max_change']=='0.021'


def test_literal_quote_grid_failure_is_no_trade():
    row=record();row['perp']['ask']='100.12'
    assert not any(apply([row])[0][0][k] for k in ('entry_available','hedge_available','exit_available'))


def test_rule_change_is_latched_even_if_it_later_reverts():
    options,futures=metadata();changed=deepcopy(futures);changed['symbols'][0]['filters'][0]['maxQty']='999'
    vintages=[{'available_ms':T+HOUR,'options':options,'futures':changed},{'available_ms':T+2*HOUR,'options':options,'futures':futures}]
    rows,_=apply([record(T+i*HOUR) for i in range(3)],vintages)
    assert rows[0]['entry_available'] and all(not r['hedge_available'] for r in rows[1:])
    assert all(r['rule_scope']['changed_latched'] for r in rows[1:])


def test_stale_rules_recover_only_with_fresh_identical_snapshot():
    options,futures=metadata()
    rows,_=apply([record(T+25*HOUR),record(T+26*HOUR)],[{'available_ms':T+25*HOUR+1,'options':options,'futures':futures}])
    assert not rows[0]['hedge_available'] and rows[1]['hedge_available']


@pytest.mark.parametrize('field,value',[('minQty','.0015'),('maxQty','.02')])
def test_unsupported_hedge_lot_envelope_refuses(field,value):
    options,futures=metadata();futures['symbols'][0]['filters'][0][field]=value
    with pytest.raises(ValueError):apply(initial_data={'options':options,'futures':futures})


@pytest.mark.parametrize('field,value',[('expiryDate',T+31*DAY),('strikePrice','101'),('side','PUT'),('minQty','.02'),('maxQty','999')])
def test_same_symbol_identity_mutation_latches(field,value):
    options,futures=metadata();options['optionSymbols'][0][field]=value
    rows,_=apply([record(T+HOUR)],[{'available_ms':T+1,'options':options,'futures':futures}])
    assert rows[0]['rule_scope']['changed_latched'] and not rows[0]['valuation_available']


@pytest.mark.parametrize('field,value',[('settleAsset','BTC'),('baseAsset','ETH'),('quoteAsset','BTC')])
def test_parent_identity_mutation_latches(field,value):
    options,futures=metadata();options['optionContracts'][0][field]=value
    rows,_=apply([record(T+HOUR)],[{'available_ms':T+1,'options':options,'futures':futures}])
    assert rows[0]['rule_scope']['changed_latched']


def test_new_or_disappearing_status_is_observed_rule_change():
    options,futures=metadata();options['optionSymbols'][0]['status']='TRADING'
    rows,_=apply([record(T+HOUR)],[{'available_ms':T+1,'options':options,'futures':futures}])
    assert rows[0]['rule_scope']['changed_latched']


@pytest.mark.parametrize('field,value',[('request_monotonic_ns',1),('retrieval_monotonic_ns',(T+9000)*1000000),('controller_retrieval_monotonic_ns',(T+1000)*1000000),('controller_deadline_monotonic_ns',(T+6000)*1000000),('controller_window_start_ms',T-1)])
def test_true_verdict_flags_cannot_hide_contradictory_raw_clocks(field,value):
    meta,known,_=initial();known['btc-index']['metadata'][field]=value
    out=a.select_initial(meta,known,entry_ms=T)
    assert out['BTC']['status']=='unavailable' and out['ETH']['status']=='complete'


def test_delayed_collection_retains_nominal_age_boundary():
    meta,known,_=initial()
    # A successful later fetch cannot make an earlier cached economic event fresh.
    spec=a.known_requests()['btc-index']
    known['btc-index']=receipt(a._recipe(spec),{'indexPrice':'100','time':T-1000},T,hourly=True)
    result=a.select_initial(meta,known,entry_ms=T)
    assert result['BTC']['status']=='unavailable'
    assert result['ETH']['status']=='complete'


@pytest.mark.parametrize('shift',[-1,2000])
def test_coherent_early_release_and_extended_deadline_refused(shift):
    meta,known,_=initial();row=known['btc-index']
    # Shift every raw clock consistently: flags and internal coherence do not
    # authorize either an early release or a moved absolute deadline.
    for key in ('request_ms','controller_retrieval_ms','retrieval_ms','controller_window_start_ms','controller_deadline_ms'):
        row['metadata'][key]+=shift
    for key in ('request_monotonic_ns','retrieval_monotonic_ns','controller_retrieval_monotonic_ns','controller_window_start_monotonic_ns','controller_deadline_monotonic_ns'):
        row['metadata'][key]+=shift*1000000
    assert a.select_initial(meta,known,entry_ms=T)['BTC']['status']=='unavailable'


def test_hourly_receipts_require_explicit_nominal_reference():
    _,known,_=initial();row=known['btc-index'];recipe=a._recipe(a.known_requests()['btc-index'])
    assert a.decode(row,recipe,scheduled_ms=T,hourly=True)[0]['indexPrice']=='100'
    with pytest.raises(ValueError):a.decode(row,recipe,scheduled_ms=T+2000,hourly=True)
