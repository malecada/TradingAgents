"""Eight fixed WBETH books; source reconstruction and descriptive exposure only."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse

from tradingagents.research import ResearchRun
from options_metadata import strict_json, lifecycle_bytes
import carry_capture as carry_source
import wbeth_inputs as wbeth_source
from wbeth_book import book
from carry_statistics import market_exposure

REGISTRATION='research/strategy-search-2026-09-11/gates-wbeth-book.json'
EXPERIMENT='wbeth-book-20260911'
MAX_OUTPUT_BYTES=20*1024**2
REQUIRED_CARRY=('eth-spot','eth-perp','eth-mark','eth-funding')
CASES=[(capital,scenario,zero) for zero in (False,True) for capital in (1000,10000) for scenario in ('base','stress')]


def case_id(capital,scenario,zero):
    return f'wbeth-{capital}-{scenario}'+('-zero-funding' if zero else '')


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def strict_value(raw):
    value=strict_json(b'{"value":'+raw+b'}')
    if set(value)!={'value'}:
        raise ValueError('source body is not a single strict JSON value')
    return value['value']


def index(rows,ids):
    if not isinstance(rows,list) or len(rows)!=len(ids) or any(not isinstance(row,dict) for row in rows) or {row['id'] for row in rows}!=set(ids):
        raise ValueError('exact parent source denominator required')
    return {row['id']:row for row in rows}


def _utc(stamp):
    value=datetime.fromisoformat(stamp)
    if value.tzinfo is None or value.utcoffset().total_seconds()!=0:
        raise ValueError('source request/retrieval clock must be explicit UTC')
    return value


def sources(capture,admission,kind):
    if kind=='carry':
        spec=carry_source.frozen_request_spec()
        valid=canonical(capture['request_spec'])==canonical(spec)
    else:
        spec=capture['request_spec']
        valid=hashlib.sha256(canonical(spec).encode()).hexdigest()==wbeth_source.SPEC_CANONICAL_SHA256
    if not valid:raise ValueError('parent source request specification changed')
    ids=[request['id'] for request in spec['requests']]
    receipts,parents=index(capture['requests'],ids),index(admission['cells'],ids)
    values,states={},{}
    for request in spec['requests']:
        identity=request['id'];record=receipts[identity];parent=parents[identity]
        state={'id':identity,'parent_status':parent.get('status'),'request_utc':record.get('request_utc'),
               'retrieval_utc':record.get('retrieval_utc'),'status':'unavailable'}
        try:
            if canonical({key:record.get(key) for key in request})!=canonical(request):
                raise ValueError('receipt request identity mismatch')
            if kind=='carry':
                expected=request['url']+('?' + urllib.parse.urlencode(request['parameters']) if request['parameters'] else '')
                if record.get('request_url')!=expected:raise ValueError('carry request URL mismatch')
            raw=base64.b64decode(record['body_base64'],validate=True)
            if type(record['body_bytes']) is not int or len(raw)!=record['body_bytes'] or len(raw)>5*1024**2 or hashlib.sha256(raw).hexdigest()!=record['body_sha256']:
                raise ValueError('raw body hash/size differs')
            if record.get('attempted') is not True or record.get('body_complete') is not True or type(record.get('http_status')) is not int or record['http_status']!=200 or record.get('error') is not None:
                raise ValueError('source was not an attempted complete HTTP200 response')
            before,after=_utc(record['request_utc']),_utc(record['retrieval_utc'])
            if after<before:raise ValueError('source retrieval precedes request')
            data=strict_value(raw)
            if kind=='carry':
                normalized=carry_source.admit_response(request,raw)
                if request['kind']=='funding':normalized['coverage']=carry_source.funding_coverage(data)
                if request['kind']=='server-time':
                    lower=int(before.timestamp()*1000)-5000;upper=int(after.timestamp()*1000)+5000
                    stamp=normalized['server_time_ms']
                    normalized['clock_check']={'earliest_allowed_ms':lower,'latest_allowed_ms':upper,
                        'server_minus_request_ms':stamp-(lower+5000),'server_minus_retrieval_ms':stamp-(upper-5000),'agrees':lower<=stamp<=upper}
                    if not lower<=stamp<=upper:raise ValueError('server clock outside receipt interval')
            else:normalized=wbeth_source.parse_response(raw,request)
            if parent.get('status')!='complete':raise ValueError('parent did not admit source: '+str(parent.get('reason','unavailable')))
            if canonical(parent)!=canonical({'id':identity,**normalized}):
                raise ValueError('parent normalized admission differs from raw reconstruction')
            values[identity]=data;state['status']='complete'
        except MemoryError:raise
        except Exception as exc:state['reason']=type(exc).__name__+': '+str(exc)
        states[identity]=state
    return values,states


def _safe_sources(capture,admission,kind):
    ids=([row['id'] for row in carry_source.frozen_request_spec()['requests']] if kind=='carry' else ['wbeth-exchange-info','wbeth-spot'])
    try:return sources(capture,admission,kind)
    except MemoryError:raise
    except Exception as exc:
        return {},{identity:{'id':identity,'status':'unavailable','reason':type(exc).__name__+': '+str(exc)} for identity in ids}


def returns(rows):
    previous=float(rows[0][1]);out=[]
    for row in rows:
        close=float(row[4]);out.append(close/previous-1);previous=close
    return out


def evaluate(wbeth_capture,wbeth_admission,carry_capture,carry_admission):
    wb,ws=_safe_sources(wbeth_capture,wbeth_admission,'wbeth')
    ca,cs=_safe_sources(carry_capture,carry_admission,'carry')
    source_states={**ws,**cs}
    required=('wbeth-exchange-info','wbeth-spot',*REQUIRED_CARRY)
    for identity,state in source_states.items():
        state['required_for_cash_book']=identity in required
        state['required_for_joint_exposure']=identity in ('btc-spot','eth-spot')
    missing=[identity for identity in required if source_states[identity]['status']!='complete']
    primary,cells={},[]
    for capital,scenario,zero in CASES:
        identity=case_id(capital,scenario,zero)
        if missing:result={'status':'unavailable','reason':'Required sources unavailable: '+', '.join(missing)}
        else:result=book(wb['wbeth-spot'],ca['eth-spot'],ca['eth-perp'],ca['eth-mark'],ca['eth-funding'],capital=capital,cost_scenario=scenario,zero_funding=zero)
        primary[identity]=result
        cells.append({'id':identity,'status':'complete' if result['status']=='conditional' else 'unavailable',
                      **({'reason':result['reason']} if result['status']=='unavailable' else {})})
    summaries=[]
    for capital,scenario,zero in CASES:
        identity=case_id(capital,scenario,zero);result=primary[identity]
        if result['status']!='conditional':exposure={'status':'unavailable','reason':'book unavailable'}
        elif cs['btc-spot']['status']!='complete':exposure={'status':'unavailable','reason':'BTC source unavailable; cash book retained'}
        else:
            try:exposure=market_exposure([row['nav'] for row in result['daily_trace']],capital,returns(ca['btc-spot']),returns(ca['eth-spot']))
            except (ValueError,TypeError,KeyError,ArithmeticError) as exc:exposure={'status':'unavailable','reason':str(exc)}
        pair=[primary[case_id(capital,cost,False)] for cost in ('base','stress')]
        cash_pass=all(row['status']=='conditional' and row['metrics']['cash_profit']>0 and row['metrics']['annualized_simple_return_365']>=.03 for row in pair)
        beta_pass=(exposure['status']=='complete' and all(abs(exposure[key+'_beta'])<=.1 and exposure[key+'_interval'][0]>=-.2 and exposure[key+'_interval'][1]<=.2 for key in ('btc','eth')))
        summary={'id':identity,'capital':capital,'cost_scenario':scenario,'zero_funding':zero,'status':result['status'],
                 'role':'same-quantity zero-funding counterfactual; not pure staking' if zero else 'primary observed-funding book',
                 'statistics':{'market_exposure':exposure,'expected_return_confidence':{'status':'unavailable','reason':'One 91-day episode; no independent repeated-trade expected-profit sample.'},
                               'power':{'status':'unavailable','reason':'No expected-profit test or repeated-episode sample.'}},
                 'necessary_historical_screens':{'primary_positive_cash_and_3pct_annual_base_and_stress':cash_pass,
                    'beta':{'status':exposure['status'],'passes':beta_pass if exposure['status']=='complete' else None},
                    'observed_drawdown_at_most_10pct':result['metrics']['max_drawdown']<=.1 if result['status']=='conditional' else None,
                    'scope':'Conditional descriptive historical screens only; annual frequency and future performance are unestablished.'},
                 'realized_net_base_delta_at_most_1pct_nav':{'status':'unavailable','reason':'True WBETH-to-ETH delta is unverified; market-value mismatch cannot substitute for base delta.'},
                 'execution':{'status':'unavailable','reason':'Historical/current fills, lots, fees and personal access unverified.'},
                 'future_tail_risk':{'status':'unavailable','reason':'Invented scenarios are not future loss bounds or liquidation guarantees.'},'graduation':False}
        if result['status']=='conditional':summary.update(metrics=result['metrics'],cash_benchmarks=result['cash_benchmarks'],true_eth_delta=result['true_eth_delta'])
        else:summary['reason']=result['reason']
        summaries.append(summary)
    return {'cases':primary,'source_availability':source_states}, {'cases':summaries,'case_count':8,'primary_count':4,'counterfactual_count':4,
            'source_availability':source_states,'graduation':False,'validated_strategies':0,
            'interpretation':'WBETH market-value hedge approximation; no pure staking attribution, contractual delta or return inference from one episode.'},cells


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2],registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        inputs=[strict_json(run.read_input(name)) for name in ('wbeth_capture','wbeth_admission','carry_capture','carry_admission')]
        books,summary,cells=evaluate(*inputs)
        if len(lifecycle_bytes(books))+len(lifecycle_bytes(summary))>MAX_OUTPUT_BYTES:raise ValueError('combined actual pretty outputs exceed20MiB')
        run.write_json('books.json',books);run.write_json('summary.json',summary);run.finish(cells)


if __name__=='__main__':main()
