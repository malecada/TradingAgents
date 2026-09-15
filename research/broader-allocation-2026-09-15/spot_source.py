"""Four registered public spot metadata/depth observations; no financial book."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from tradingagents.research import ResearchRun

HERE=Path(__file__).resolve().parent

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

helpers=load('spot_source_json_helpers','dex_source.py')
transport=load('spot_source_transport','spot_transport.py')
EXPERIMENT='allocation-spot-source-20260915'
REGISTRATION='research/broader-allocation-2026-09-15/gates-spot-source.json'
SPEC_SHA256='ccba9a272ae555e88fa7441540d259d9efd88e2a6b7ccd047e83bed4ff215dff'


def decimal(value,zero=False):
    if not isinstance(value,str):raise ValueError('decimal string required')
    number=Decimal(value)
    if not number.is_finite() or number<0 or (not zero and number==0):
        raise ValueError('invalid nonnegative/positive decimal')
    return number


def parse(raw,kind):
    data=helpers.strict_json(raw)
    json.dumps(data,allow_nan=False)  # Reject exponent-overflow floats even in retained unknown fields.
    if not isinstance(data,dict) or 'code' in data:raise ValueError('invalid/API error object')
    if kind=='clock':
        value=data.get('serverTime')
        if type(value) is not int or value<=0:raise ValueError('positive integer millisecond serverTime required')
        return {'server_time_ms':value,'scope':'Server clock observation, not depth event timestamp'}
    if kind=='symbols':
        rows=data.get('symbols')
        if not isinstance(rows,list) or len(rows)!=2:raise ValueError('exact two symbol records required')
        wanted={'BTCUSDC':'BTC','ETHUSDC':'ETH'}; result={}
        for row in rows:
            if not isinstance(row,dict):raise ValueError('symbol object required')
            name=row.get('symbol')
            if name not in wanted or name in result or row.get('baseAsset')!=wanted[name] or row.get('quoteAsset')!='USDC':
                raise ValueError('wrong/duplicate instrument identity')
            if not isinstance(row.get('status'),str) or type(row.get('isSpotTradingAllowed')) is not bool:
                raise ValueError('missing spot/status fields')
            filters=row.get('filters')
            if not isinstance(filters,list):raise ValueError('filters array required')
            mapping={}
            for f in filters:
                if not isinstance(f,dict) or not isinstance(f.get('filterType'),str) or f['filterType'] in mapping:
                    raise ValueError('invalid/duplicate filter type')
                mapping[f['filterType']]=f
            for filtertype,fields in [('LOT_SIZE',('minQty','maxQty','stepSize')),('PRICE_FILTER',('minPrice','maxPrice','tickSize'))]:
                if filtertype not in mapping:raise ValueError('required filter missing: '+filtertype)
                for field in fields:decimal(mapping[filtertype].get(field),zero=True)
            minimum=mapping.get('NOTIONAL',mapping.get('MIN_NOTIONAL'))
            if minimum is None:raise ValueError('notional filter missing')
            decimal(minimum.get('minNotional'),zero=True)
            if 'maxNotional' in minimum:decimal(minimum['maxNotional'],zero=True)
            result[name]={'base':wanted[name],'quote':'USDC','status':row['status'],
                'spot_trading_allowed':row['isSpotTradingAllowed'],'filters':mapping,
                'account_eligibility':'unavailable','filter_implementation_complete':False}
        return {'symbols':result,'scope':'Literal public rule fields; neither account access nor full filter engine'}
    if kind not in ('btc_depth','eth_depth'):raise ValueError('unregistered kind')
    if type(data.get('lastUpdateId')) is not int or data['lastUpdateId']<0:raise ValueError('invalid depth update ID')
    parsed={}
    for side in ('bids','asks'):
        rows=data.get(side)
        if not isinstance(rows,list) or not 1<=len(rows)<=100:raise ValueError('invalid depth row count')
        values=[]
        for row in rows:
            if not isinstance(row,list) or len(row)!=2:raise ValueError('depth price/quantity pair required')
            values.append((decimal(row[0]),decimal(row[1])))
        prices=[v[0] for v in values]
        if len(set(prices))!=len(prices) or prices!=sorted(prices,reverse=side=='bids'):
            raise ValueError('unordered or duplicate depth levels')
        parsed[side]=values
    if parsed['bids'][0][0]>=parsed['asks'][0][0]:raise ValueError('crossed or locked depth')
    return {'symbol':'BTCUSDC' if kind=='btc_depth' else 'ETHUSDC','last_update_id':data['lastUpdateId'],
        'levels':{s:len(v) for s,v in parsed.items()},'top_bid':str(parsed['bids'][0][0]),'top_ask':str(parsed['asks'][0][0]),
        'event_time':'unavailable','scope':'Receipt-timed snapshot; no promised fill, slippage, exact source age or account access'}


def capture(spec,fetch=transport.public_get,persist=None):
    if hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=SPEC_SHA256:
        raise ValueError('unregistered request specification')
    deadline=time.monotonic()+spec['cooperative_seconds'];rows=[];receipts=[];denied=False;symbols=None
    for req in spec['requests']:
        start=datetime.now(timezone.utc);before=time.monotonic();kind=req['id']
        name='BTCUSDC' if kind=='btc_depth' else 'ETHUSDC'
        reason=('not attempted after same-host HTTP denial' if denied else
            'not attempted: instrument metadata unavailable/not trading' if kind.endswith('_depth') and (symbols is None or symbols[name]['status']!='TRADING' or not symbols[name]['spot_trading_allowed']) else
            'insufficient cooperative time' if before+spec['timeout_seconds']>deadline else None)
        response=fetch(req['url']) if reason is None else dict(body=b'',http_status=None,headers={},error=reason,body_complete=False)
        body=response['body']
        if not isinstance(body,bytes):raise ValueError('raw bytes required')
        if len(body)>spec['max_response_bytes']:
            body=body[:spec['max_response_bytes']];response={**response,'body_complete':False,'error':'oversized response; prefix retained'}
        if response['http_status'] in transport.DENIALS:denied=True
        receipt={**req,'attempted':reason is None,'request_utc':start.isoformat(),'retrieval_utc':datetime.now(timezone.utc).isoformat(),
            'elapsed_seconds':time.monotonic()-before,'http_status':response['http_status'],'headers':response['headers'],
            'error':response['error'],'body_complete':response['body_complete'],'body_bytes':len(body),
            'body_sha256':hashlib.sha256(body).hexdigest(),'body_base64':base64.b64encode(body).decode()}
        receipts.append(receipt)
        if persist:persist(kind+'-receipt.json',receipt)
        if response['error'] or response['http_status']!=200 or response['body_complete'] is not True:
            row={'id':kind,'status':'unavailable','reason':response['error'] or 'incomplete HTTP response'}
        else:
            try:
                fields=parse(body,kind);row={'id':kind,'status':'complete','fields':fields}
                if kind=='symbols':symbols=fields['symbols']
            except (ValueError,TypeError,KeyError,InvalidOperation,OverflowError) as exc:
                row={'id':kind,'status':'unavailable','reason':type(exc).__name__+': '+str(exc)}
        rows.append(row)
    result={'scope':'Public spot source only; no account or economic admission','implementation_admitted':False,
        'registered_requests':4,'attempted_requests':sum(r['attempted'] for r in receipts),'cells':rows,
        'reported_network_route':'NordVPN Finland according to user; not independently observed',
        'unmeasured':['Czech-account eligibility','fees/FX/deposit/withdrawal','stablecoin USD valuation/yield','historical spot/action coverage','fill latency and capacity','net profit and benchmark value']}
    size=sum(len((json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()) for v in [*receipts,result])
    if size>spec['max_output_bytes']:raise ValueError('output bound exceeded; partial receipts retained')
    return result,receipts


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);args=p.parse_args()
    with ResearchRun.start(root=HERE.parents[1],registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        spec=helpers.strict_json(run.read_input('spec'));run.read_input('ancestry')
        result,_=capture(spec,persist=run.write_json);run.write_json('source-summary.json',result)
        run.finish([{k:r[k] for k in ('id','status','reason') if k in r} for r in result['cells']])


if __name__=='__main__':main()
