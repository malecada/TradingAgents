"""Fixed representative option-entry component; not hedged-account affordability."""
import argparse
import base64
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation,localcontext
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from tradingagents.research import ResearchRun
import options_metadata
import options_entry_transport as transport_module
from options_metadata import lifecycle_bytes

REGISTRATION='research/strategy-search-2026-09-11/gates-options-entry.json'
EXPERIMENT='options-entry-20260911'
ASSETS=('BTC','ETH')
FEES=('0.00024','0.00030')
DAY=86400000


def default_spec():
    requests=[{'id':'options-time','kind':'time','endpoint':'https://eapi.binance.com/eapi/v1/time','parameters':{}}]
    for kind in ('index','depth','mark'):
        for asset in ASSETS:
            requests.append({'id':asset.lower()+'-'+kind,'kind':kind,'asset':asset,'endpoint':'https://eapi.binance.com/eapi/v1/'+kind,
                             'parameters':{'underlying':asset+'USDT'} if kind=='index' else {'symbol':'SELECTED_'+asset,**({'limit':10} if kind=='depth' else {})}})
    return {'schema_version':1,'experiment':'options-entry-20260911','requests':requests,'max_requests':7,
            'timeout_seconds':20,'capture_seconds':180,'server_clock_tolerance_ms':5000,'max_response_bytes':256*1024,'max_output_bytes':12*1024**2,
            'max_projection_bytes':512*1024,'clock_policy':'positive int64 clocks; nonnegative int64 update IDs','numeric_characters':64,'numeric_adjusted_exponent':[-32,32],
            'selection_days':[7,30,45],'capital_usdt':[1000,10000],'fee_rates':list(FEES),
            'selection_ties':['earlier_expiry','lower_strike','lexical_symbol'],'missing_status':'unverified_public_representative_only'}


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def unavailable(reason):return {'status':'unavailable','reason':reason}
def component_id(asset,capital,fee):return f'{asset.lower()}-{capital}-{fee}'


def number(value,positive=True):
    if isinstance(value,bool) or not isinstance(value,(str,int,Decimal)):raise ValueError('literal decimal required')
    text=str(value)
    if len(text)>64:raise ValueError('numeric representation scope')
    value=Decimal(text)
    if not value.is_finite() or not -32<=value.adjusted()<=32 or value<0 or positive and value==0:raise ValueError('numeric range/sign scope')
    return value


def decode(raw):
    def pairs(rows):
        result={}
        for key,value in rows:
            if key in result:raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    def reject(_):raise ValueError('nonfinite JSON constant')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_float=Decimal,parse_constant=reject)


def metadata(capture,admission,receipt):
    if sha(options_metadata._canonical(capture['request_spec']))!=options_metadata.SPEC_CANONICAL_SHA256:raise ValueError('parent specification differs')
    request=next(r for r in capture['request_spec']['requests'] if r['kind']=='exchange-info')
    rows=[r for r in capture['requests'] if r.get('id')==request['id']]
    parents=[r for r in admission['cells'] if r.get('id')==request['id']]
    if len(rows)!=1 or len(parents)!=1 or canonical(rows[0])!=canonical(receipt):raise ValueError('parent aggregate/receipt disagreement')
    if canonical({k:receipt.get(k) for k in request})!=canonical(request):raise ValueError('parent identity mismatch')
    if receipt.get('attempted') is not True or receipt.get('body_complete') is not True or type(receipt.get('http_status')) is not int or receipt['http_status']!=200 or receipt.get('error') is not None:raise ValueError('parent source unavailable')
    raw=base64.b64decode(receipt['body_base64'],validate=True)
    if type(receipt.get('body_bytes')) is not int or len(raw)!=receipt['body_bytes'] or len(raw)>5*1024**2 or sha(raw)!=receipt['body_sha256']:raise ValueError('parent raw hash/size mismatch')
    normalized=options_metadata.parse_exchange_info(raw)
    if canonical(parents[0])!=canonical({'id':request['id'],**normalized}):raise ValueError('parent normalized admission differs')
    return decode(raw),{'status':'complete','body_sha256':sha(raw),'request_utc':receipt.get('request_utc'),'retrieval_utc':receipt.get('retrieval_utc'),
              'enum_classification':'Original ambiguous numeric enum interpretation preserved; literal parent/leaf mapping only.'}


def select(data,asset,reference,index):
    contracts=[r for r in data.get('optionContracts',[]) if isinstance(r,dict) and r.get('underlying')==asset+'USDT']
    if len(contracts)!=1:raise ValueError('missing/duplicate underlying parent')
    parent=contracts[0]
    if any(parent.get(key)!=value for key,value in [('baseAsset',asset),('quoteAsset','USDT'),('settleAsset','USDT')]):raise ValueError('parent base/quote/settlement mismatch')
    identities=Counter(r.get('symbol') for r in data['optionSymbols'] if isinstance(r.get('symbol'),str))
    eligible=[];excluded=Counter()
    with localcontext() as context:
        context.prec=512
        for row in data['optionSymbols']:
            if row.get('underlying')!=asset+'USDT' or row.get('side')!='CALL':continue
            try:
                symbol=row['symbol'];expiry=row['expiryDate']
                if not isinstance(symbol,str) or len(symbol)>128 or identities[symbol]!=1:raise ValueError('symbol identity')
                if row.get('quoteAsset')!='USDT' or 'status' in row and row['status']!='TRADING':raise ValueError('quote/status')
                if type(expiry) is not int or not 0<expiry<=2**63-1 or not 7*DAY<=expiry-reference<=45*DAY:raise ValueError('expiry band/type')
                strike=number(row['strikePrice']);unit=number(row['unit']);quantity=number(row['minQty']);maximum=number(row['maxQty'])
                match=re.fullmatch(re.escape(asset)+r'-(\d{6})-(\d+(?:\.\d+)?)-C',symbol)
                if not match or match[1]!=datetime.fromtimestamp(expiry/1000,timezone.utc).strftime('%y%m%d') or number(match[2])!=strike:raise ValueError('symbol/expiry/strike disagreement')
                lots=[f for f in row['filters'] if isinstance(f,dict) and f.get('filterType')=='LOT_SIZE']
                if len(lots)!=1:raise ValueError('missing/duplicate LOT_SIZE')
                lot=lots[0];step=number(lot['stepSize'])
                if number(lot['minQty'])!=quantity or number(lot['maxQty'])!=maximum or quantity>maximum or quantity%step:raise ValueError('lot inconsistency')
                eligible.append({'symbol':symbol,'expiry_ms':expiry,'strike':str(strike),'unit':str(unit),'minQty':str(quantity),'maxQty':str(maximum),'stepSize':str(step),
                                 'metadata_status':row.get('status','unverified'),'underlyingType':row.get('underlyingType'),'contractType':row.get('contractType')})
            except (ValueError,KeyError,TypeError,InvalidOperation,OverflowError):excluded['structurally_or_temporally_ineligible']+=1
        if not eligible:raise ValueError('no eligible representative')
        expiry=min({r['expiry_ms'] for r in eligible},key=lambda value:(abs(value-reference-30*DAY),value))
        selected=min((r for r in eligible if r['expiry_ms']==expiry),key=lambda row:(abs(Decimal(row['strike'])-index),Decimal(row['strike']),row['symbol']))
    evidence={'status':'complete','asset':asset,'reference_ms':reference,'index':str(index),'eligible_count':len(eligible),'eligible':eligible,
              'excluded_counts':dict(excluded),'selected':selected,'tradability':'unavailable; saved metadata and public representative only'}
    if len(lifecycle_bytes(evidence))>512*1024:raise ValueError('selection projection cap')
    return evidence


def component(selection,depth,index,capital,fee):
    with localcontext() as context:
        context.prec=512
        row=selection['selected'];q=number(row['minQty']);unit=number(row['unit']);ask=number(depth['asks'][0][0]);size=number(depth['asks'][0][1],False)
        premium=ask*q;commission=min(Decimal(fee)*index*unit,Decimal('0.10')*ask)*q;cash=premium+commission
        return {'status':'complete','symbol':row['symbol'],'quantity':str(q),'unit':str(unit),'ask':str(ask),'index':str(index),'fee_rate':fee,
                'premium_usdt':str(premium),'fee_usdt':str(commission),'entry_component_usdt':str(cash),'capital_usdt':capital,
                'component_fits_capital':cash<=capital,'visible_ask_size_sufficient':size>=q,'visible_ask_size':str(size),
                'scope':'Option-entry component only; no completed trade, hedged-account affordability or personal commission inference.'}


def integer(value,positive=True):
    if type(value) is not int or not (1 if positive else 0)<=value<=2**63-1:raise ValueError('positive int64 required')
    return value


def parse_response(raw,request,receipt):
    data=decode(raw);kind=request['kind']
    if kind=='mark':
        if not isinstance(data,list) or len(data)!=1 or not isinstance(data[0],dict):raise ValueError('one selected mark object required')
        row=data[0]
        if row.get('symbol')!=request['parameters']['symbol']:raise ValueError('mark identity mismatch')
        if not isinstance(row.get('markPrice'),str) or not isinstance(row.get('delta'),str):raise ValueError('mark/delta literal strings required')
        mark=number(row['markPrice']);greeks={}
        for field in ('delta','gamma','theta','vega','highPriceLimit','lowPriceLimit','riskFreeInterest','markIV','bidIV','askIV'):
            if field not in row:greeks[field]={'status':'unavailable','reason':'absent'};continue
            value=row[field]
            if not isinstance(value,str) or len(value)>64:raise ValueError('Greek numeric scope')
            numeric=Decimal(value)
            if not numeric.is_finite() or not -32<=numeric.adjusted()<=32:raise ValueError('Greek finite range required')
            greeks[field]={'status':'complete','value':str(numeric)}
        return {'status':'complete','symbol':row['symbol'],'markPrice':str(mark),'model_fields':greeks,'event_time':'unavailable; not documented','scope':'Model mark/sensitivities, not executable quotes or true delta.'}
    if not isinstance(data,dict) or 'code' in data:raise ValueError('successful object response required')
    if kind=='time':
        stamp=integer(data['serverTime'])
        lower=int(datetime.fromisoformat(receipt['request_utc']).timestamp()*1000)-5000
        upper=int(datetime.fromisoformat(receipt['retrieval_utc']).timestamp()*1000)+5000
        if not lower<=stamp<=upper:raise ValueError('server clock outside request/retrieval +/-5seconds')
        return {'status':'complete','serverTime':stamp,'clock_bounds_ms':[lower,upper]}
    if kind=='index':
        if 'underlying' in data and data['underlying']!=request['parameters']['underlying']:raise ValueError('index optional identity conflicts')
        if not isinstance(data.get('indexPrice'),str):raise ValueError('indexPrice string required')
        return {'status':'complete','indexPrice':str(number(data['indexPrice'])),'time':integer(data['time']),
                'identity_scope':'Exact requested underlying URL; response identity field not documented.'}
    if kind!='depth':raise ValueError('unregistered source kind')
    if 'symbol' in data and data['symbol']!=request['parameters']['symbol']:raise ValueError('depth optional identity conflicts')
    result={'status':'complete','T':integer(data['T']),'lastUpdateId':integer(data['lastUpdateId'],False),
            'identity_scope':'Exact selected-symbol request URL; response symbol not documented.'}
    for side in ('bids','asks'):
        rows=data[side]
        if not isinstance(rows,list) or not 1<=len(rows)<=10:raise ValueError('nonempty depth<=10 required')
        normalized=[]
        for row in rows:
            if not isinstance(row,list) or len(row)!=2 or any(not isinstance(value,str) for value in row):raise ValueError('depth string price/quantity pair required')
            normalized.append([str(number(row[0])),str(number(row[1],False))])
        prices=[Decimal(row[0]) for row in normalized]
        if any((left<=right if side=='bids' else left>=right) for left,right in zip(prices,prices[1:])):raise ValueError('depth prices not strictly ordered')
        result[side]=normalized
    if Decimal(result['bids'][0][0])>Decimal(result['asks'][0][0]):raise ValueError('crossed depth')
    return result


def admit(receipt,request):
    if receipt['attempted'] is not True or receipt['body_complete'] is not True or type(receipt['http_status']) is not int or receipt['http_status']!=200 or receipt['error'] is not None:
        return unavailable(receipt['error'] or 'HTTP/body unavailable')
    try:
        return parse_response(base64.b64decode(receipt['body_base64'],validate=True),request,receipt)
    except MemoryError:raise
    except Exception as exc:return unavailable(type(exc).__name__+': '+str(exc)[:160])


def run(spec,metadata_capture,metadata_admission,metadata_receipt,persist,transport=None):
    if canonical(spec)!=canonical(default_spec()):raise ValueError('request specification differs')
    start=time.monotonic();deadline=start+180
    try:data,metadata_status=metadata(metadata_capture,metadata_admission,metadata_receipt)
    except MemoryError:raise
    except Exception as exc:data=None;metadata_status=unavailable(type(exc).__name__+': '+str(exc)[:160])
    receipts=[];references=[];sources={};selections={};denied=False;written=0
    for template in spec['requests']:
        request={**template,'parameters':dict(template['parameters'])};kind=request['kind'];asset=request.get('asset')
        reason=None
        if metadata_status['status']!='complete':reason='saved metadata unavailable'
        elif denied:reason='same-host denial suppresses remaining slots'
        elif time.monotonic()+20>deadline:reason='remaining capture budget cannot admit full request'
        elif kind in ('depth','mark'):
            if asset not in selections:
                if sources.get('options-time',{}).get('status')!='complete' or sources.get(asset.lower()+'-index',{}).get('status')!='complete':selections[asset]=unavailable('time/index dependency unavailable')
                else:
                    try:selections[asset]=select(data,asset,sources['options-time']['serverTime'],Decimal(sources[asset.lower()+'-index']['indexPrice']))
                    except MemoryError:raise
                    except Exception as exc:selections[asset]=unavailable(type(exc).__name__+': '+str(exc)[:160])
            if selections[asset]['status']!='complete':reason='representative selection unavailable'
            else:request['parameters']['symbol']=selections[asset]['selected']['symbol']
        if kind in ('depth','mark') and selections.get(asset,{}).get('status')=='complete':request['parameters']['symbol']=selections[asset]['selected']['symbol']
        url=request['endpoint']+('?' + urlencode(request['parameters']) if request['parameters'] else '')
        if reason is not None and kind in ('depth','mark') and request['parameters']['symbol'].startswith('SELECTED_'):url=None
        request_utc=utc();before=time.monotonic()
        if reason is None:
            try:response=(transport or transport_module.public_get)(url)
            except MemoryError:raise
            except Exception as exc:response={'body':b'','http_status':None,'headers':{},'body_complete':False,'error':type(exc).__name__}
        else:response={'body':b'','http_status':None,'headers':{},'body_complete':False,'error':reason}
        raw=response['body']
        if not isinstance(raw,bytes):raise ValueError('transport must retain bytes')
        if len(raw)>spec['max_response_bytes']:
            raw=raw[:spec['max_response_bytes']];response={**response,'body_complete':False,'error':'response exceeds256KiB; prefix retained'}
        if response['http_status'] in transport_module.DENIALS:denied=True
        receipt={**request,'request_url':url,'request_utc':request_utc,'retrieval_utc':utc(),'elapsed_seconds':time.monotonic()-before,
                 'attempted':reason is None,'http_status':response['http_status'],'error':response['error'],'body_complete':response['body_complete'],
                 'body_bytes':len(raw),'body_sha256':sha(raw),'body_base64':base64.b64encode(raw).decode(),
                 'headers':{name:value for name,value in response['headers'].items() if name.lower() in ('date','content-type')}}
        name=request['id']+'-receipt.json';persist(name,receipt);written+=len(lifecycle_bytes(receipt));receipts.append((request,receipt))
        references.append({'id':request['id'],'path':name,'receipt_sha256':sha(lifecycle_bytes(receipt)),'body_sha256':sha(raw),'body_bytes':len(raw),
                           'request_url':url,'request_utc':request_utc,'retrieval_utc':receipt['retrieval_utc'],'attempted':receipt['attempted']})
        # Only selection prerequisites are decoded before all seven slots close.
        if kind in ('time','index'):sources[request['id']]=admit(receipt,request)
    capture_closed_utc=utc()
    for request,receipt in receipts:
        if request['kind'] not in ('time','index'):sources[request['id']]=admit(receipt,request)
    for asset in ASSETS:selections.setdefault(asset,unavailable('capture/selection prerequisite unavailable'))
    cases={}
    for asset in ASSETS:
        for capital in (1000,10000):
            for fee in FEES:
                name=component_id(asset,capital,fee)
                if selections[asset]['status']!='complete' or sources[asset.lower()+'-depth']['status']!='complete':cases[name]=unavailable('selected metadata/depth prerequisite unavailable');continue
                try:cases[name]=component(selections[asset],sources[asset.lower()+'-depth'],Decimal(sources[asset.lower()+'-index']['indexPrice']),capital,fee)
                except MemoryError:raise
                except Exception as exc:cases[name]=unavailable(type(exc).__name__+': '+str(exc)[:160])
    capture={'request_spec':spec,'metadata':metadata_status,'receipts':references,'source_admission':sources,'selections':selections,'capture_closed_utc':capture_closed_utc,
             'phase_scope':'Only time/index/metadata selection parsed before capture closed; economics interpreted afterward.'}
    entry={'cases':cases,'calculation':'premium=A*q; fee=min(r*S*U,0.10*A)*q; no second unit multiplication',
           'clock_scope':'Asynchronous observations; no synchronization, quote-age or fill proof.'}
    summary={'planned_source_cells':7,'planned_component_cells':8,'graduation':False,
             'unavailable':['full hedged-account affordability','seller entry margin','actual fees/account access','expected profit','confidence intervals','power','beta','annual relevance','true delta','liquidation risk'],
             'component_counts':dict(Counter(value['status'] for value in cases.values()))}
    if len(lifecycle_bytes(capture))>spec['max_projection_bytes']:
        capture['selections']={asset:unavailable('normalized projection cap') for asset in ASSETS}
        cases={name:unavailable('normalized projection cap') for name in cases};entry['cases']=cases
        summary['component_counts']={'unavailable':8}
    outputs={'capture.json':capture,'entry.json':entry,'summary.json':summary}
    if written+sum(len(lifecycle_bytes(value)) for value in outputs.values())>spec['max_output_bytes']:raise ValueError('actual serialized12MiB output cap')
    for name,value in outputs.items():persist(name,value)
    cells=[{'id':name,'status':value['status'],**({'reason':value['reason']} if value['status']=='unavailable' else {})} for name,value in [*sources.items(),*cases.items()]]
    return capture,entry,summary,cells


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2],registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as registered:
        values={name:options_metadata.strict_json(registered.read_input(name)) for name in ('request_spec','metadata_capture','metadata_admission','metadata_receipt')}
        _,_,_,cells=run(values['request_spec'],values['metadata_capture'],values['metadata_admission'],values['metadata_receipt'],registered.write_json)
        registered.finish(cells)


if __name__=='__main__':main()
