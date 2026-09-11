"""Offline16-source hourly batch contract. No transport, scheduling or market I/O."""
import base64
from decimal import Decimal
import hashlib
import json
import re
from urllib.parse import urlencode

LIMIT=8192
MAX_BATCH_MS=5000
MAX_DEPTH_AGE_MS=5000
FUTURE_TOLERANCE_MS=1000


def number(value,*,positive=False):
    if not isinstance(value,str) or len(value)>64:raise ValueError('bounded literal numeric string required')
    result=Decimal(value)
    if not result.is_finite() or not -32<=result.adjusted()<=32 or (positive and result<=0):raise ValueError('numeric range')
    return result


def integer(value):
    if type(value) is not int or not 0<=value<=2**63-1:raise ValueError('nonnegative integer millisecond/update clock required')
    return value


def strict(raw):
    def pairs(items):
        out={}
        for key,value in items:
            if key in out:raise ValueError('duplicate JSON key')
            out[key]=value
        return out
    def reject(value):raise ValueError('nonfinite literal')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=reject)


def requests(symbols):
    if set(symbols)!={'BTC','ETH'}:raise ValueError('fixed two-asset contract required')
    result=[{'id':'options-time','venue':'options','kind':'time','endpoint':'https://eapi.binance.com/eapi/v1/time','parameters':{}}]
    for asset in ('BTC','ETH'):
        pair=symbols[asset]
        if set(pair)!={'call','put'}:raise ValueError('one call/put pair required')
        matched=[]
        for side,suffix in (('call','C'),('put','P')):
            if not isinstance(pair[side],str) or len(pair[side])>64:raise ValueError('bounded literal option identity required')
            match=re.fullmatch(re.escape(asset)+r'-(\d{6})-(\d+(?:\.\d+)?)-'+suffix,pair[side])
            if not match:raise ValueError('literal option identity')
            matched.append(match.groups())
        if matched[0]!=matched[1]:raise ValueError('shared expiry/strike required')
        pre=asset.lower()
        result.append({'id':pre+'-index','venue':'options','asset':asset,'kind':'index','endpoint':'https://eapi.binance.com/eapi/v1/index','parameters':{'underlying':asset+'USDT'}})
        for side in ('call','put'):
            for kind in ('depth','mark'):
                params={'symbol':pair[side]}
                if kind=='depth':params['limit']=10
                result.append({'id':f'{pre}-{side}-{kind}','venue':'options','asset':asset,'side':side,'kind':kind,
                    'endpoint':'https://eapi.binance.com/eapi/v1/'+kind,'parameters':params})
    result.append({'id':'futures-time','venue':'futures','kind':'time','endpoint':'https://fapi.binance.com/fapi/v1/time','parameters':{}})
    for asset in ('BTC','ETH'):
        for kind,endpoint in (('depth','depth'),('mark','premiumIndex')):
            params={'symbol':asset+'USDT'}
            if kind=='depth':params['limit']=10
            result.append({'id':asset.lower()+'-perp-'+kind,'venue':'futures','asset':asset,'kind':kind,
                           'endpoint':'https://fapi.binance.com/fapi/v1/'+endpoint,'parameters':params})
    assert len(result)==16
    return result


def parse(raw,request):
    value=strict(raw);kind=request['kind'];venue=request['venue']
    if kind=='mark' and venue=='options':
        if not isinstance(value,list) or len(value)!=1 or not isinstance(value[0],dict):raise ValueError('single option model row required')
        row=value[0]
        if row.get('symbol')!=request['parameters']['symbol']:raise ValueError('model symbol')
        result={'event_ms':None,'event_time_status':'unavailable; no documented model event clock',
                'model_scope':'Provider model only, unit1 assumption; not true delta or guaranteed freshness.','field_errors':{}}
        for field,source in (('mark','markPrice'),('delta','delta')):
            try:
                number_value=number(row[source],positive=field=='mark')
                lower,upper=(0,1) if request['side']=='call' else (-1,0)
                if field=='delta' and not lower<=number_value<=upper:raise ValueError('unit1 model delta side/range')
                result[field]=str(number_value)
            except (KeyError,ValueError,ArithmeticError) as exc:
                result['field_errors'][field]=type(exc).__name__+': '+str(exc)
        return result
    if not isinstance(value,dict) or 'code' in value:raise ValueError('successful object required')
    if kind=='time':return {'server_ms':integer(value['serverTime'])}
    symbol=request['parameters'].get('symbol')
    if symbol is not None and 'symbol' in value and value['symbol']!=symbol:raise ValueError('response symbol conflicts')
    if kind=='index':
        if 'underlying' in value and value['underlying']!=request['parameters']['underlying']:raise ValueError('index identity conflicts')
        return {'index':str(number(value['indexPrice'],positive=True)),'event_ms':integer(value['time'])}
    if kind=='mark':
        if value.get('symbol')!=symbol:raise ValueError('perpetual mark identity required')
        return {'mark':str(number(value['markPrice'],positive=True)),'event_ms':integer(value['time']),
                'scope':'Valuation mark only; premiumIndex funding fields are not settled cashflows.'}
    if kind!='depth':raise ValueError('unknown source role')
    output={'event_ms':integer(value['T']),'last_update_id':integer(value['lastUpdateId'])}
    if venue=='futures':
        output['output_event_ms']=integer(value['E'])
        if output['output_event_ms']<output['event_ms']:raise ValueError('output event precedes transaction')
    for name in ('bids','asks'):
        rows=value[name]
        if not isinstance(rows,list) or not 1<=len(rows)<=10:raise ValueError('nonempty at-most10 depth levels required')
        normalized=[]
        for row in rows:
            if not isinstance(row,list) or len(row)!=2:raise ValueError('depth pair')
            price=number(row[0],positive=True);quantity=number(row[1])
            if quantity<0:raise ValueError('negative displayed size')
            normalized.append([str(price),str(quantity)])
        prices=[Decimal(row[0]) for row in normalized]
        if any((a<=b if name=='bids' else a>=b) for a,b in zip(prices,prices[1:])):raise ValueError('depth ordering')
        output[name]=normalized
    if Decimal(output['bids'][0][0])>Decimal(output['asks'][0][0]):raise ValueError('crossed depth')
    return output


def assemble(*,decision_ms,symbols,receipts,units):
    """Preserve16source states and independent asset records for the pure ledger.

    Receipt times use one local wall-clock domain, with no unobserved model-time
    substitution. A future actual collector must additionally prove monotonic
    deadlines/clock-jump handling, metadata selection and cumulative admission.
    """
    decision_ms=integer(decision_ms)
    if not isinstance(units,dict) or set(units)!={'BTC','ETH'} or any(type(v) is not int or v!=1 for v in units.values()):raise ValueError('explicit separately admitted unit1 mapping required')
    if decision_ms%3600000:raise ValueError('fixed UTC hourly decision required')
    spec=requests(symbols);ids={r['id'] for r in spec}
    if not isinstance(receipts,list) or len(receipts)!=16 or any(not isinstance(r,dict) or not isinstance(r.get('id'),str) for r in receipts) or {r.get('id') for r in receipts}!=ids:
        return {'status':'unavailable','reason':'exact16unique receipts required','source_count':16,
            'sources':{key:{'status':'unavailable','reason':'batch denominator differs'} for key in sorted(ids)},
            'records':{asset:{'time_ms':decision_ms,'action_time_ms':decision_ms+MAX_BATCH_MS,'decision_available':False,'entry_available':False,'hedge_available':False,'exit_available':False,'valuation_available':False,'option_valuation_available':False,'perp_valuation_available':False,'reason':'batch denominator differs'} for asset in ('BTC','ETH')}}
    records={r['id']:r for r in receipts};states={};values={};offsets={}
    for request in spec:
        key=request['id'];receipt=records[key];state={'status':'unavailable'}
        try:
            url=request['endpoint']+('?' + urlencode(request['parameters']) if request['parameters'] else '')
            if receipt.get('request_url')!=url:raise ValueError('bound request URL differs')
            if receipt.get('attempted') is not True or receipt.get('body_complete') is not True or type(receipt.get('http_status')) is not int or receipt['http_status']!=200 or receipt.get('error') is not None:raise ValueError('response not complete HTTP200')
            encoded=receipt['body_base64']
            if not isinstance(encoded,str) or len(encoded)>4*((LIMIT+2)//3):raise ValueError('encoded body exceeds bound')
            raw=base64.b64decode(encoded,validate=True)
            if type(receipt.get('body_bytes')) is not int or len(raw)!=receipt['body_bytes'] or len(raw)>LIMIT or hashlib.sha256(raw).hexdigest()!=receipt['body_sha256']:raise ValueError('raw bound/length/hash')
            before,after=integer(receipt['request_ms']),integer(receipt['retrieval_ms'])
            if not decision_ms<=before<=after<=decision_ms+MAX_BATCH_MS:raise ValueError('receipt outside fixed decision batch')
            value=parse(raw,request)
            if request['kind']=='time' and not before-5000<=value['server_ms']<=after+5000:raise ValueError('server time not plausible milliseconds within local5second tolerance')
            values[key]=value
            state.update(status='partial' if value.get('field_errors') else 'complete',request_ms=before,retrieval_ms=after,body_sha256=receipt['body_sha256'],body_bytes=len(raw),event_ms=value.get('event_ms'))
            if value.get('field_errors'):state['field_errors']=value['field_errors']
            if request['kind']=='time':offsets[request['venue']]=[value['server_ms']-after,value['server_ms']-before]
        except MemoryError:raise
        except Exception as exc:state['reason']=type(exc).__name__+': '+str(exc)
        states[key]=state
    result={}
    for asset in ('BTC','ETH'):
        relevant=[r for r in spec if r.get('asset')==asset or r['kind']=='time'];keys=[r['id'] for r in relevant]
        missing=[key for key in keys if states[key]['status']!='complete']
        closed=decision_ms+MAX_BATCH_MS  # fixed modeled action after entire5second acquisition window
        freshness={};stale=[]
        for req in relevant:
            key=req['id']
            if states[key]['status']=='unavailable' or req['kind']=='time':continue
            event=values[key].get('event_ms');bounds=offsets.get(req['venue'])
            if event is None:
                freshness[key]={'status':'unavailable','reason':'model event clock undocumented; arrival is not event time'}
                continue
            if bounds is None:
                stale.append(key);freshness[key]={'status':'unavailable','reason':'venue clock unavailable'};continue
            earliest,latest=event-bounds[1],event-bounds[0]
            age=closed-earliest
            future_limit=states[key]['retrieval_ms']+FUTURE_TOLERANCE_MS
            output_event=values[key].get('output_event_ms')
            output_interval=None if output_event is None else [output_event-bounds[1],output_event-bounds[0]]
            ok=age<=MAX_DEPTH_AGE_MS and latest<=future_limit and (output_interval is None or output_interval[1]<=future_limit)
            freshness[key]={'status':'complete' if ok else 'unavailable','local_event_interval_ms':[earliest,latest],
                            'maximum_age_ms':age,'output_local_event_interval_ms':output_interval,'latest_permitted_event_ms':future_limit,'scope':'Time-response interval calibration; network symmetry is not assumed.'}
            if not ok:stale.append(key)
        pre=asset.lower()
        clock_keys=['options-time','futures-time']
        entry_keys=keys
        hedge_keys=clock_keys+[f'{pre}-call-mark',f'{pre}-put-mark',f'{pre}-perp-depth']
        exit_keys=clock_keys+[f'{pre}-index',f'{pre}-call-depth',f'{pre}-put-depth',f'{pre}-perp-depth']
        def ready(needed,model_fields=()):
            if not all(states[key]['status']!='unavailable' and key not in stale for key in needed):return False
            return all(field in values[f'{pre}-{side}-mark'] for side in ('call','put') for field in model_fields)
        hedge_ready=ready(hedge_keys,('delta',))
        out={'time_ms':decision_ms,'action_time_ms':closed,'decision_available':hedge_ready,
            'entry_available':ready(entry_keys,('mark','delta')),'hedge_available':hedge_ready,'exit_available':ready(exit_keys),
            'action_required_sources':{'entry':entry_keys,'hedge':hedge_keys,'exit':exit_keys},
            'valuation_available':False,'missing_sources':missing,'stale_sources':stale,'clock_offsets_ms':offsets,
            'freshness':freshness,'model_freshness':'unavailable; conditional arrived-model policy only'}
        if pre+'-index' in values:out['index']=values[pre+'-index']['index']
        for side in ('call','put','perp'):
            quote=values.get(f'{pre}-{side}-depth',{});model=values.get(f'{pre}-{side}-mark',{})
            entry={'unit':units[asset]} if side in ('call','put') else {}
            if 'bids' in quote:entry.update(bid=quote['bids'][0][0],bid_qty=quote['bids'][0][1],ask=quote['asks'][0][0],ask_qty=quote['asks'][0][1])
            if 'mark' in model:entry['mark']=model['mark']
            if 'delta' in model:entry['delta']=model['delta']
            out[side]=entry
        valuation_keys=[f'{pre}-{side}-mark' for side in ('call','put','perp')]
        out['option_valuation_available']=all('mark' in values.get(f'{pre}-{side}-mark',{}) for side in ('call','put'))
        out['perp_valuation_available']='mark' in values.get(pre+'-perp-mark',{}) and pre+'-perp-mark' not in stale
        out['valuation_available']=out['option_valuation_available'] and out['perp_valuation_available']
        if not out['valuation_available']:
            for side in ('call','put','perp'):
                key=f'{pre}-{side}-mark'
                if 'mark' not in values.get(key,{}) or key in stale:out[side]['mark']=None
        result[asset]=out
    return {'status':'complete','source_count':16,'sources':states,'records':result,
        'scope':'Offline fixed5second action batch schema/clock/missing-decision prototype; metadata/lot/selection/funding/actual access and durable capture remain separate prerequisites.'}
