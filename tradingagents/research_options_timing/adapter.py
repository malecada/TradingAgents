"""Frozen-source admission helpers; no requests, trading or journal mutation.

Provider models, last-observed rules and effective slippage costs are conditional
inputs. This adapter does not establish account eligibility or actual fills.
"""
import base64
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path

from .schedule import ASSETS, DAY, HOUR, WINDOW, ACQUISITION_DELAY_MS, request


def _policy(name):
    path=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'/f'{name}.py'
    spec=importlib.util.spec_from_file_location('_capture_'+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


BATCH=_policy('options_policy_batch')
SELECTION=_policy('options_policy_selection')
RULE_AGE_MS=DAY+300000


def number(value,*,positive=False):
    if isinstance(value,bool) or not isinstance(value,(str,int)):raise ValueError('literal numeric field')
    text=str(value)
    if len(text)>64:raise ValueError('numeric length')
    n=Decimal(text)
    if not n.is_finite() or n and not -32<=n.adjusted()<=32 or n<0 or positive and n<=0:raise ValueError('numeric bound')
    return F(n)


def literal(value):return SELECTION.literal(value)


def decode(receipt,recipe,*,scheduled_ms,cap=8192,hourly=False):
    """Reconstruct raw availability; scheduled_ms is nominal, never acquisition release.

    Hourly calls require release N+2s and the unchanged absolute N+5s deadline.
    Non-hourly bootstrap/daily/final windows retain their original five seconds.
    """
    if not isinstance(receipt,dict) or receipt.get('status')!='received' or receipt.get('request')!=recipe:raise ValueError('receipt identity/state')
    if type(hourly) is not bool or type(scheduled_ms) is not int or hourly and scheduled_ms%HOUR:
        raise ValueError('explicit nominal hourly observation clock')
    release_ms=scheduled_ms+(ACQUISITION_DELAY_MS if hourly else 0)
    deadline_ms=scheduled_ms+WINDOW
    meta=receipt['metadata']
    if any(meta.get(k) is not True for k in ('attempted','body_complete','clock_consistent','within_controller_deadline')) or type(meta.get('http_status')) is not int or meta['http_status']!=200 or meta.get('error') is not None:raise ValueError('complete clock-bound HTTP200 required')
    from .transport import request_url
    if meta.get('request_url')!=request_url(recipe):raise ValueError('URL binding')
    start=meta.get('request_ms');end=meta.get('controller_retrieval_ms')
    if type(start) is not int or type(end) is not int or not release_ms<=start<=end<=deadline_ms:raise ValueError('fixed observation window')
    clock_fields=('request_monotonic_ns','retrieval_ms','retrieval_monotonic_ns','controller_retrieval_monotonic_ns',
                  'controller_window_start_ms','controller_window_start_monotonic_ns','controller_deadline_ms','controller_deadline_monotonic_ns')
    if any(type(meta.get(k)) is not int or meta[k]<0 for k in clock_fields):raise ValueError('raw controller/worker clock fields required')
    sm=meta['request_monotonic_ns'];we=meta['retrieval_ms'];wm=meta['retrieval_monotonic_ns'];em=meta['controller_retrieval_monotonic_ns']
    anchor=meta['controller_window_start_ms'];am=meta['controller_window_start_monotonic_ns'];deadline=meta['controller_deadline_monotonic_ns']
    if not release_ms<=anchor<=start or meta['controller_deadline_ms']!=deadline_ms or deadline!=am+(deadline_ms-anchor)*1000000:raise ValueError('raw controller deadline anchor')
    if not am<=sm<=wm<=em<=deadline or not start<=we<=end+1 or em-am>(deadline_ms-release_ms)*1000000:raise ValueError('raw clock chronology/deadline')
    for x,xm,y,ym in ((anchor,am,start,sm),(start,sm,we,wm),(start,sm,end,em),(anchor,am,end,em)):
        if abs((y-x)*1000000-(ym-xm))>100000000:raise ValueError('raw wall/monotonic inconsistency')
    encoded=receipt['body_base64']
    if not isinstance(encoded,str) or len(encoded)>4*((cap+2)//3):raise ValueError('encoded body bound')
    raw=base64.b64decode(encoded,validate=True)
    if type(receipt['body_bytes']) is not int or len(raw)>cap or receipt['body_bytes']!=len(raw) or receipt['body_sha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('raw body binding')
    if meta.get('body_bytes')!=len(raw) or meta.get('body_sha256')!=receipt['body_sha256']:raise ValueError('transport raw binding')
    return BATCH.strict(raw),raw,meta


def known_requests():
    result={}
    for venue,name in [('eapi','options'),('fapi','futures')]:
        result[name+'-time']={'id':name+'-time','venue':name,'kind':'time',**request(venue,'time')}
    for asset in ASSETS:
        pre=asset.lower();symbol=asset+'USDT'
        for role,venue,route,params,kind in [
            ('index','eapi','index',{'underlying':symbol},'index'),
            ('perp-depth','fapi','depth',{'symbol':symbol,'limit':10},'depth'),
            ('perp-mark','fapi','premiumIndex',{'symbol':symbol},'mark')]:
            result[pre+'-'+role]={'id':pre+'-'+role,'asset':asset,'venue':'options' if venue=='eapi' else 'futures','kind':kind,**request(venue,route,**params)}
    return result


def _recipe(spec):return {k:spec[k] for k in ('endpoint','parameters')}


def _clock(value,meta):
    server=BATCH.integer(value['serverTime'])
    if not meta['request_ms']-5000<=server<=meta['controller_retrieval_ms']+5000:raise ValueError('implausible venue clock')
    return server-meta['controller_retrieval_ms'],server-meta['request_ms']


def _fresh(value,meta,bounds,at):
    event=value.get('event_ms')
    if event is None:raise ValueError('required event clock missing')
    early,late=event-bounds[1],event-bounds[0]
    if at+WINDOW-early>WINDOW or late>meta['controller_retrieval_ms']+1000:raise ValueError('source age or chronology')
    output=value.get('output_event_ms')
    if output is not None and output-bounds[0]>meta['controller_retrieval_ms']+1000:raise ValueError('source output clock')


def select_initial(metadata_receipt,known_receipts,*,entry_ms):
    """Both venue clocks and each asset's known entry sources precede selection.

    A selected pair's rule failure never causes substitution. Each asset result
    remains separately visible even when the worker's all-or-none entry fails.
    """
    result={a:{'asset':a,'entry_ms':entry_ms,'status':'unavailable','selected':None} for a in ASSETS}
    try:
        metadata,_,_=decode(metadata_receipt,request('eapi','exchangeInfo'),scheduled_ms=entry_ms-60000,cap=5*1024**2)
        specs=known_requests();clocks={};values={};metas={};errors={}
        if set(known_receipts)!=set(specs):raise ValueError('exact eight initial known roles required')
        for key,spec in specs.items():
            try:
                value,raw,meta=decode(known_receipts[key],_recipe(spec),scheduled_ms=entry_ms,hourly=True)
                values[key]=BATCH.parse(raw,spec);metas[key]=meta
                if spec['kind']=='time':clocks[spec['venue']]=_clock(value,meta)
            except (KeyError,ValueError,TypeError,ArithmeticError) as exc:errors[key]=str(exc)
        if set(clocks)!={'options','futures'}:raise ValueError('both venue clocks required before entry selection')
        for asset in ASSETS:
            try:
                keys=[asset.lower()+'-'+r for r in ('index','perp-depth','perp-mark')]
                for key in keys:
                    if key in errors:raise ValueError(key+': '+errors[key])
                    _fresh(values[key],metas[key],clocks[specs[key]['venue']],entry_ms)
                result[asset]=SELECTION.select(metadata,asset=asset,entry_ms=entry_ms,index=values[asset.lower()+'-index']['index'])
            except (KeyError,ValueError,TypeError,ArithmeticError) as exc:result[asset]['reason']=str(exc)
    except (KeyError,ValueError,TypeError,ArithmeticError) as exc:
        for item in result.values():item['reason']=str(exc)
    return result


def assemble_hour(*,entry_ms,hour,selection,receipts):
    symbols={a:{side:selection[a][side] for side in ('call','put')} for a in ASSETS}
    at=entry_ms+hour*HOUR;flat=[]
    for spec in BATCH.requests(symbols):
        key=spec['id'];item={'id':key}
        try:
            receipt=receipts[key]
            _,_,meta=decode(receipt,_recipe(spec),scheduled_ms=at,hourly=True)
            item.update(meta)
            item['retrieval_ms']=meta['controller_retrieval_ms']
            item.update({k:receipt[k] for k in ('body_base64','body_bytes','body_sha256')})
        except (KeyError,ValueError,TypeError,ArithmeticError) as exc:item.update(attempted=False,error=str(exc))
        flat.append(item)
    return BATCH.assemble(decision_ms=at,symbols=symbols,receipts=flat,units={a:1 for a in ASSETS})


def _filters(row):
    values=row['filters']
    if not isinstance(values,list) or any(not isinstance(v,dict) or not isinstance(v.get('filterType'),str) for v in values):raise ValueError('filter list')
    result={v['filterType']:v for v in values}
    if len(result)!=len(values):raise ValueError('duplicate filter')
    return result


def _price_rule(f):
    return {k:literal(number(f[k],positive=k=='tickSize')) for k in ('minPrice','maxPrice','tickSize')}


def rule_snapshot(options,futures,asset,selected):
    """Conservative sufficient lot envelope; other order/account limits unknown."""
    q=number(selected['quantity'],positive=True);out={}
    parents=[r for r in options['optionContracts'] if r.get('underlying')==asset+'USDT']
    if len(parents)!=1 or any(parents[0].get(k)!=v for k,v in [('baseAsset',asset),('quoteAsset','USDT'),('settleAsset','USDT')]):raise ValueError('option parent/settlement identity')
    out['identity']={'underlying':asset+'USDT','baseAsset':asset,'quoteAsset':'USDT','settleAsset':'USDT'}
    for side in ('call','put'):
        rows=[r for r in options['optionSymbols'] if r.get('symbol')==selected[side]]
        if len(rows)!=1:raise ValueError('unique selected option rules')
        row=rows[0];f=_filters(row);lot=f['LOT_SIZE'];minimum=number(lot['minQty']);maximum=number(lot['maxQty'],positive=True);step=number(lot['stepSize'],positive=True)
        if number(row['unit'],positive=True)!=1 or row.get('quoteAsset')!='USDT' or row.get('underlying')!=asset+'USDT' or ('status' in row and row['status']!='TRADING'):raise ValueError('option identity/unit/status changed')
        if type(row.get('expiryDate')) is not int or row['expiryDate']!=selected['expiry_ms'] or number(row['strikePrice'],positive=True)!=number(selected['strike'],positive=True) or row.get('side')!=side.upper():raise ValueError('option expiry/strike/side identity')
        if number(row['minQty'])!=minimum or number(row['maxQty'])!=maximum:raise ValueError('top-level option quantity rule conflict')
        if not minimum<=q<=maximum or (q-minimum)%step:raise ValueError('selected option quantity illegal')
        price=_price_rule(f['PRICE_FILTER'])
        if number(price['tickSize'])!=number(selected['option_tick']):raise ValueError('selected option tick changed')
        out[side]={'lot':{k:literal(number(lot[k])) for k in ('minQty','maxQty','stepSize')},'price':price,
                   'identity':{'symbol':row['symbol'],'expiry_ms':row['expiryDate'],'strike':literal(number(row['strikePrice'])),
                               'side':row['side'],'status_present':'status' in row,'status':row.get('status')}}
    rows=[r for r in futures['symbols'] if r.get('symbol')==asset+'USDT']
    if len(rows)!=1:raise ValueError('unique perpetual rules')
    row=rows[0]
    if any(row.get(k)!=v for k,v in [('status','TRADING'),('contractType','PERPETUAL'),('baseAsset',asset),('quoteAsset','USDT'),('marginAsset','USDT')]):raise ValueError('perpetual identity/status')
    filters=_filters(row);lot=filters['LOT_SIZE'];step=number(lot['stepSize'],positive=True);minimum=number(lot['minQty']);maximum=number(lot['maxQty'],positive=True)
    if minimum%step or 2*q+step>maximum:raise ValueError('conservative zero-anchored hedge grid/maxQty unavailable')
    if 'MIN_NOTIONAL' in filters and 'NOTIONAL' in filters:raise ValueError('conflicting notional filters')
    if 'MIN_NOTIONAL' in filters:minn=number(filters['MIN_NOTIONAL']['notional']);maxn=None
    elif 'NOTIONAL' in filters:
        minn=number(filters['NOTIONAL']['minNotional']);maxn=number(filters['NOTIONAL']['maxNotional'])
    else:raise ValueError('minimum notional rule missing')
    out['perp']={'lot':{k:literal(number(lot[k])) for k in ('minQty','maxQty','stepSize')},'price':_price_rule(filters['PRICE_FILTER']),
                 'min_notional':literal(minn),'max_notional':None if maxn is None else literal(maxn),'max_change':literal(2*q+step)}
    return out


def _price_ok(price,rule,*,buy):
    p=number(price,positive=True);lo=number(rule['minPrice']);hi=number(rule['maxPrice']);tick=number(rule['tickSize'],positive=True)
    # Both bounds are required for the conservative supported subset. This is
    # stricter than the option documentation's side-specific outer bounds.
    return (not lo or p>=lo) and (not hi or p<=hi) and (p-lo)%tick==0


def apply_rule_vintages(records,*,asset,selection,initial,initial_ms,vintages,stress):
    """Any observed rule change permanently disables new actions for this episode.

    Missing/stale identical rules may recover. Valuation remains conditional on
    original instrument identity; rule-change latch invalidates it conservatively.
    Perpetual slippage is an effective cash cost, not a tick-valid order price.
    """
    out=deepcopy(records);baseline=rule_snapshot(initial['options'],initial['futures'],asset,selection)
    latest=baseline;latest_ms=initial_ms;cursor=0;latched=False;events=sorted(vintages,key=lambda v:v['available_ms'])
    if len(events)>46:raise ValueError('bounded rule vintages')
    for row in out:
        at=row['time_ms']
        while cursor<len(events) and events[cursor]['available_ms']<=at:
            event=events[cursor];cursor+=1
            try:
                snapshot=rule_snapshot(event['options'],event['futures'],asset,selection)
                if snapshot!=baseline:latched=True
                latest=snapshot;latest_ms=event['available_ms']
            except (KeyError,ValueError,TypeError,ArithmeticError):latched=True
        ready=not latched and 0<=at-latest_ms<=RULE_AGE_MS
        row['rule_scope']={'available':ready,'changed_latched':latched,'latest_available_ms':latest_ms,
                           'qualification':'Last-observed daily rules; effective slippage cost is not an order price. Full account/order compliance unverified.'}
        for phase in ('entry_available','hedge_available','exit_available'):row[phase]=bool(row.get(phase)) and ready
        if latched:
            for key in ('option_valuation_available','perp_valuation_available','valuation_available'):row[key]=False
        if not ready:continue
        for side in ('call','put','perp'):
            try:
                quote=row[side];rule=latest[side]['price']
                if side=='perp':
                    ok=all(_price_ok(quote[name],rule,buy=name=='ask') for name in ('bid','ask'))
                    maxn=latest['perp']['max_notional']
                    if maxn is not None and number(maxn)>0:
                        ok &= number(latest['perp']['max_change'])*number(quote['ask'])*(1+F(4,10000) if stress else 1+F(2,10000))<=number(maxn)
                    if not ok:
                        for phase in ('entry_available','hedge_available','exit_available'):row[phase]=False
                else:
                    tick=number(selection['option_tick']) if stress else F(0)
                    row['entry_available'] &= _price_ok(literal(number(quote['bid'])-tick),rule,buy=False)
                    row['exit_available'] &= _price_ok(literal(number(quote['ask'])+tick),rule,buy=True)
            except (KeyError,ValueError,TypeError,ArithmeticError):
                for phase in (('entry_available','hedge_available','exit_available') if side=='perp' else ('entry_available','exit_available')):row[phase]=False
    return out,baseline
