"""Four frozen historical source requests; no returns, variance or strategy book."""
import argparse
import base64
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from tradingagents.research import ResearchRun
HERE=Path(__file__).resolve().parent

def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

helpers=load('readiness_json','dex_source.py')
transport=load('readiness_transport','readiness_transport.py')
EXPERIMENT='allocation-input-readiness-20260915'
REGISTRATION='research/broader-allocation-2026-09-15/gates-input-readiness.json'
SPEC_HASH='53e07b706dd3ef6c8933aed6b80714bd01cf6effa06ce2455bb85befabe3800c'
DAY=86400


def number(v,zero=False):
    if not isinstance(v,str):raise ValueError('decimal string required')
    n=Decimal(v)
    if not n.is_finite() or n<0 or (n==0 and not zero):raise ValueError('nonnegative/positive finite decimal required')
    return n


def integer(v):
    if type(v) is not int or v<0:raise ValueError('nonnegative integer required')
    return v


def parse(raw,kind,spec,received_epoch):
    data=helpers.strict_json(raw);json.dumps(data,allow_nan=False)
    if kind=='usd_identity':
        if not isinstance(data,dict) or data.get('error')!=[] or not isinstance(data.get('result'),dict) or set(data['result'])!={'USDCUSD'}:
            raise ValueError('wrong Kraken pair response')
        r=data['result']['USDCUSD']
        if not isinstance(r,dict) or any(r.get(k)!=v for k,v in {'base':'USDC','quote':'ZUSD','altname':'USDCUSD','wsname':'USDC/USD'}.items()):
            raise ValueError('wrong USDC/USD base/quote orientation')
        return {'identity':'Kraken USDC/USD','base':'USDC','quote':'USD','scope':'cross-venue USD mark proxy; not account redemption'},None
    kraken=kind=='usd_bars'
    if kind not in ('btc_bars','eth_bars','usd_bars'):raise ValueError('unknown source cell')
    if kraken:
        if not isinstance(data,dict) or data.get('error')!=[] or not isinstance(data.get('result'),dict) or set(data['result'])!={'USDCUSD','last'}:
            raise ValueError('wrong Kraken OHLC response')
        integer(data['result']['last']);raw_rows=data['result']['USDCUSD'];limit=720
    else:raw_rows=data;limit=1000
    if not isinstance(raw_rows,list) or not 1<=len(raw_rows)<=limit:raise ValueError('wrong daily row count')
    series={};previous=-1;partial=0;seen=[]
    for r in raw_rows:
        if not isinstance(r,list) or len(r)!=(8 if kraken else 12):raise ValueError('wrong candle width')
        stamp=integer(r[0]);stamp=stamp if kraken else stamp//1000
        if not kraken and r[0]%1000:raise ValueError('subsecond daily candle')
        if stamp%DAY or stamp<=previous:raise ValueError('non-UTC/duplicate/unordered daily opens')
        if stamp > int(received_epoch)//DAY*DAY:
            raise ValueError('future daily open beyond receipt current day')
        previous=stamp;seen.append(stamp)
        o,h,l,c=map(number,r[1:5])
        if l>min(o,c) or max(o,c)>h:raise ValueError('inconsistent OHLC bounds')
        if kraken:
            number(r[5],zero=True);volume=number(r[6],zero=True);trades=integer(r[7])
        else:
            volume=number(r[5],zero=True)
            if integer(r[6])!=r[0]+DAY*1000-1:raise ValueError('incorrect Binance close timestamp')
            trades=integer(r[8])
            for idx in (7,9,10):number(r[idx],zero=True)
            if not spec['start_epoch']<=stamp<=spec['terminal_epoch']:raise ValueError('Binance row outside fixed query bounds')
        if stamp+DAY>received_epoch:
            partial+=1;continue
        if spec['start_epoch']<=stamp<=spec['terminal_epoch']:
            if volume<=0 or trades<=0:raise ValueError('fixed daily candle has no positive reported activity')
            # Terminal later-day fields are never exposed through normalized panel.
            series[str(stamp)]={'open':str(o)}
            if stamp<spec['terminal_epoch']:series[str(stamp)]['close']=str(c)
    wanted=set(range(spec['start_epoch'],spec['terminal_epoch']+1,DAY))
    missing=sorted(wanted-set(map(int,series)))
    fields={'returned_rows':len(raw_rows),'normalized_rows':len(series),'partial_rows_excluded':partial,
        'returned_first_epoch':seen[0],'returned_last_epoch':seen[-1],
        'missing_epochs':missing,'coverage_complete':not missing,'scope':'Daily bars; no historical execution or publication witness'}
    return fields,series


def capture(spec,fetch=transport.public_get,persist=None):
    if hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=SPEC_HASH:
        raise ValueError('unregistered historical request specification')
    begin=time.monotonic();denied=set();identity=False;rows=[];receipts=[];series={}
    for req in spec['requests']:
        start=datetime.now(timezone.utc);before=time.monotonic();kind=req['id']
        reason=('not attempted after host denial' if req['host'] in denied else
                'not attempted: USDC/USD identity unavailable' if kind=='usd_bars' and not identity else
                'insufficient cooperative time' if before+spec['timeout_seconds']>begin+spec['cooperative_seconds'] else None)
        response=fetch(req['url']) if reason is None else {'body':b'','http_status':None,'headers':{},'error':reason,'body_complete':False}
        body=response['body']
        if not isinstance(body,bytes):raise ValueError('raw bytes required')
        if len(body)>spec['max_response_bytes']:
            body=body[:spec['max_response_bytes']];response={**response,'error':'oversized response; retained prefix','body_complete':False}
        if response['http_status'] in transport.DENIALS:denied.add(req['host'])
        received=datetime.now(timezone.utc)
        receipt={**req,'attempted':reason is None,'request_utc':start.isoformat(),'retrieval_utc':received.isoformat(),
                 'elapsed_seconds':time.monotonic()-before,'http_status':response['http_status'],'headers':response['headers'],
                 'error':response['error'],'body_complete':response['body_complete'],'body_bytes':len(body),
                 'body_sha256':hashlib.sha256(body).hexdigest(),'body_base64':base64.b64encode(body).decode()}
        receipts.append(receipt)
        if persist:persist(kind+'-receipt.json',receipt)
        if response['error'] or response['http_status']!=200 or response['body_complete'] is not True:
            rows.append({'id':kind,'status':'unavailable','reason':response['error'] or 'incomplete HTTP response'});continue
        try:
            fields,values=parse(body,kind,spec,received.timestamp())
            good=fields.get('coverage_complete',True)
            row={'id':kind,'status':'complete' if good else 'unavailable','fields':fields}
            if not good:row['reason']='missing fixed calendar rows'
            rows.append(row)
            if kind=='usd_identity':identity=True
            else:series[kind]=values
        except (ValueError,TypeError,KeyError,ArithmeticError,OverflowError) as exc:
            rows.append({'id':kind,'status':'unavailable','reason':type(exc).__name__+': '+str(exc)})
    complete=all(r['status']=='complete' for r in rows)
    joined=[]
    if complete:
        for stamp in range(spec['start_epoch'],spec['terminal_epoch']+1,DAY):
            joined.append({'open_epoch':stamp,**{k:series[k][str(stamp)] for k in ('btc_bars','eth_bars','usd_bars')}})
        if len(joined)!=spec['expected_days']:raise ValueError('wrong fixed joined calendar')
    rows.append({'id':'joined-panel','status':'complete' if complete else 'unavailable',**({} if complete else {'reason':'one or more required source/coverage cells unavailable'})})
    rows.extend([{'id':'estimator-requirements','status':'complete','scope':'One annual cohort, all-capital P and all fixed D;88contrasts. No empirical variance estimated.'},
                 {'id':'confirmation-power','status':'unavailable','reason':'No independently admitted coherent joint cash/benchmark/risk model; one annual cohort cannot establish80%full-gate power.'}])
    panel={'scope':'Fixed historical bar and cross-venue USD mark proxies only','status':'complete' if complete else 'unavailable','cohort_start':spec['cohort_start'],'cohort_end':spec['cohort_end'],'series':series,'joined':joined}
    result={'scope':'Input and estimator readiness only; no returns, empirical variance or financial outcomes','attempted_requests':sum(r['attempted'] for r in receipts),'cells':rows,'implementation_admitted':False,'confirmation_admitted':False,'conditional_panel_available':complete,
            'actual_missing_terms':'Cash admission remains authoritative; proxy marks do not resolve personal terms, B1 or actual exit value.'}
    size=sum(len((json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()) for x in [*receipts,panel,result])
    if size>spec['max_output_bytes']:raise ValueError('output bound exceeded; raw receipts retained')
    return result,panel,receipts


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);a=p.parse_args()
    with ResearchRun.start(root=HERE.parents[1],registration=REGISTRATION,experiment=EXPERIMENT,source=a.source) as run:
        run.read_input('ancestry');run.read_input('cash_result');run.read_input('engine_result')
        spec=helpers.strict_json(run.read_input('spec'));result,panel,_=capture(spec,persist=run.write_json)
        run.write_json('panel.json',panel);run.write_json('readiness.json',result)
        run.finish([{k:r[k] for k in ('id','status','reason') if k in r} for r in result['cells']])

if __name__=='__main__':main()
