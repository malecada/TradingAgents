"""Independent retained source/schema review; no collector import or cycle PnL."""
import base64
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT/'research_runs/triangle-inputs-20260911'
REVIEW = Path(__file__).resolve().parent
PAIRS = {'BTCUSDT': ('BTC','USDT'), 'ETHUSDT': ('ETH','USDT'), 'ETHBTC': ('ETH','BTC')}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result, 'duplicate JSON key'
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonfinite JSON constant: ' + value)


def decode(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=no_duplicates, parse_constant=reject_constant)


def read(path):
    return decode(path.read_bytes())


def blob(commit, path):
    assert re.fullmatch('[0-9a-f]{40}', commit)
    assert not Path(path).is_absolute() and '..' not in Path(path).parts
    assert not any(x in {'keys','apis','.env','hf_token.txt'} for x in Path(path).parts)
    return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)


def positive(value):
    assert not isinstance(value, bool)
    number = Decimal(str(value))
    assert number.is_finite() and number > 0
    return number


def symbol_map(rows):
    assert isinstance(rows,list) and len(rows)==3 and all(isinstance(row,dict) for row in rows)
    result = {row['symbol']: row for row in rows}
    assert set(result)==set(PAIRS) and len(result)==len(rows)
    return result


def check():
    claim, complete = read(RUN/'claim.json'), read(RUN/'complete.json')
    assert not (RUN/'failed.json').exists()
    commit=claim['source']
    assert commit==complete['source']==claim['design_source']
    assert sha((RUN/'claim.json').read_bytes())==complete['claim_sha256']
    gate_raw=blob(commit,claim['registration']);gate=decode(gate_raw)
    assert sha(gate_raw)==claim['registration_sha256']==complete['registration_sha256']
    exp=gate['experiments'][claim['experiment_id']]
    assert exp==claim['experiment'] and claim['family']==gate['families'][exp['family']]
    assert exp['stage']=='development' and exp['reuse']=='exploratory' and exp['selection'] is None
    ancestor=decode(blob(commit,'research/strategy-search-2026-09-11/gates-options-eoh.json'))
    for group in ('families','datasets','experiments'):
        assert all(gate[group][key]==value for key,value in ancestor[group].items())
    pins={**exp['source_files'],exp['charter']['path']:exp['charter']['sha256']}
    pins.update({'tradingagents/research/'+name:digest for name,digest in exp['runtime_hashes'].items()})
    for path,digest in pins.items():assert sha(blob(commit,path))==digest,path
    info=exp['inputs']['request_spec'];spec_raw=blob(commit,info['path'])
    assert sha(spec_raw)==info['sha256'];spec=decode(spec_raw)
    outputs=RUN/'outputs';names=set(exp['outputs'])
    assert len(names)==8 and names==set(complete['output_sha256'])=={p.name for p in outputs.iterdir()}
    for name,digest in complete['output_sha256'].items():assert sha((outputs/name).read_bytes())==digest
    capture,admission=read(outputs/'triangle-capture.json'),read(outputs/'triangle-admission.json')
    assert capture['request_spec']==spec
    ids=[r['id'] for r in spec['requests']]
    assert len(ids)==len(set(ids))==6 and ids==exp['cells']
    assert [r['id'] for r in capture['requests']]==[r['id'] for r in admission['cells']]==ids
    assert complete['cells']==[{'id':identifier,'status':'complete'} for identifier in ids]
    assert complete['cell_count']==6 and complete['unavailable_count']==0
    assert admission['scope']=='Asynchronously observed public inputs only; no cross-source alignment, fills, fees, cash profit or graduation.'
    clocks=[];checks=[];total_bytes=0;previous=datetime.fromisoformat(claim['started_at'])
    for request,aggregate,cell in zip(spec['requests'],capture['requests'],admission['cells']):
        receipt=read(outputs/(request['id']+'-receipt.json'))
        assert receipt==aggregate and all(receipt[k]==v for k,v in request.items())
        assert receipt['attempted'] is True and receipt['http_status']==200
        assert receipt['body_complete'] is True and receipt['error'] is None
        raw=base64.b64decode(receipt['body_base64'],validate=True)
        assert len(raw)==receipt['body_bytes']<=spec['max_response_bytes'] and sha(raw)==receipt['body_sha256']
        total_bytes+=len(raw)
        start,end=(datetime.fromisoformat(receipt[k]) for k in ('request_utc','retrieval_utc'))
        assert previous<=start<=end<=datetime.fromisoformat(complete['ended_at'])
        assert start.utcoffset().total_seconds()==end.utcoffset().total_seconds()==0
        delta=(end-start).total_seconds()-receipt['elapsed_seconds']
        assert abs(delta)<.001 and 0<=receipt['elapsed_seconds']<=spec['timeout_seconds']
        previous=end
        http_date=parsedate_to_datetime(next(v for k,v in receipt['headers'].items() if k.lower()=='date'))
        clock={'id':request['id'],'request_utc':receipt['request_utc'],'retrieval_utc':receipt['retrieval_utc'],
               'elapsed_seconds':receipt['elapsed_seconds'],'local_vs_monotonic_difference_seconds':delta,
               'http_date_minus_local_retrieval_seconds':(http_date-end).total_seconds()}
        data=decode(raw);kind=request['kind']
        assert cell['status']=='complete'
        observation={'id':request['id'],'kind':kind,'raw_body_bytes':len(raw),'raw_sha256':sha(raw),'schema_status':'pass'}
        if kind=='exchange-info':
            rows=symbol_map(data['symbols'])
            assert cell['symbols']==rows and cell['additional_metadata']=={k:v for k,v in data.items() if k!='symbols'}
            rules={}
            for symbol,row in rows.items():
                assert (row['baseAsset'],row['quoteAsset'])==PAIRS[symbol]
                assert row['status']=='TRADING' and row['isSpotTradingAllowed'] is True
                filters=row.get('filters')
                assert filters is None or isinstance(filters,list)
                assert all(isinstance(x,dict) and isinstance(x.get('filterType'),str) and x['filterType'] for x in filters or [])
                kinds=[x['filterType'] for x in filters or []]
                missing=[x for x in ('LOT_SIZE','MARKET_LOT_SIZE') if x not in kinds]
                if not {'NOTIONAL','MIN_NOTIONAL'}.intersection(kinds):missing.append('MIN_NOTIONAL-or-NOTIONAL')
                saved=cell['filter_interpretation'][symbol]
                assert saved['status']=='unavailable' and saved['observed_filter_types']==kinds and saved['missing_relevant_filters']==missing
                rules[symbol]={'status':row['status'],'isSpotTradingAllowed':True,'filter_types':kinds,
                               'missing_relevant_filter_names':missing,'filter_economics_and_account_access':'unavailable'}
            observation['current_pair_metadata']=rules
        elif kind=='server-time':
            assert isinstance(data,dict) and type(data['serverTime']) is int and data['serverTime']>0
            assert cell['raw_fields']==data
            server=datetime.fromtimestamp(data['serverTime']/1000,tz=timezone.utc)
            clock['server_time_utc']=server.isoformat()
            clock['server_time_minus_local_request_seconds']=(server-start).total_seconds()
            clock['server_time_minus_local_retrieval_seconds']=(server-end).total_seconds()
        elif kind=='book-ticker':
            rows=symbol_map(data)
            assert cell['quotes']==rows
            for row in rows.values():
                for key in ('bidPrice','askPrice','bidQty','askQty'):positive(row[key])
                assert positive(row['bidPrice'])<=positive(row['askPrice'])
            observation['symbol_count']=3
            observation['literal_keys_by_symbol']={symbol:list(row) for symbol,row in rows.items()}
            observation['event_clock_availability']='No event timestamp supplied in the observed rows; one HTTP batch does not prove atomic cross-symbol state.'
        elif kind=='depth':
            assert type(data['lastUpdateId']) is int and data['lastUpdateId']>=0
            assert cell['symbol']==request['symbol'] and cell['raw_fields']==data
            levels={}
            for side in ['bids','asks']:
                rows=data[side];assert isinstance(rows,list) and 1<=len(rows)<=20
                assert all(isinstance(row,list) and len(row)==2 for row in rows)
                values=[positive(row[0]) for row in rows]
                for row in rows:positive(row[1])
                assert len(set(values))==len(values)
                assert values==sorted(values,reverse=side=='bids')
                levels[side]=len(rows)
            assert positive(data['bids'][0][0])<=positive(data['asks'][0][0])
            assert cell['observed_bid_levels']==levels['bids'] and cell['observed_ask_levels']==levels['asks']
            observation['symbol']=request['symbol'];observation['level_counts']=levels
            observation['literal_keys']=list(data)
            observation['event_clock_availability']='lastUpdateId is not interpreted as a timestamp; no event timestamp is supplied.'
        else:raise AssertionError('unexpected request kind')
        clocks.append(clock);checks.append(observation)
    assert total_bytes==capture['total_body_bytes']<=6*spec['max_response_bytes']
    output_bytes=sum((outputs/name).stat().st_size for name in names)
    assert output_bytes<=spec['max_output_bytes'] and (outputs/'triangle-admission.json').stat().st_size<=spec['max_admission_bytes']
    resources=read(REVIEW/'triangle-resource-execution.json')
    assert resources['child_exit_code']==0 and resources['limit_reason'] is None
    assert resources['peak_sampled_tree_rss_bytes']<=spec['max_memory_mib']*1024**2
    assert resources['elapsed_seconds']<=spec['max_wall_seconds']
    return {'status':'pass','scope':'Raw source/schema reconstruction only; no conversion factors, profit, quote alignment or collector imports',
            'source':commit,'registration_sha256':sha(gate_raw),'claim_sha256':complete['claim_sha256'],
            'output_sha256':complete['output_sha256'],'cells':6,'unavailable_cells':0,'outputs':8,
            'raw_body_bytes':total_bytes,'actual_output_bytes':output_bytes,'schemas':checks,'capture_clocks':clocks,
            'total_local_capture_span_seconds':(datetime.fromisoformat(clocks[-1]['retrieval_utc'])-datetime.fromisoformat(clocks[0]['request_utc'])).total_seconds(),
            'resource_report':resources,'family':claim['family'],
            'next_input_admission':'Exact retained exchange-info and batch-ticker inputs are structurally available for a separately frozen static conversion proxy only.',
            'untested':['conversion factors and financial profit','simultaneous matching-engine observations','quote freshness/event time',
                        'account access, fee/lot/filter economics, depth fills, atomicity and market exposure','independent clock attestation','external backup']}


if __name__=='__main__':
    report=check()
    (REVIEW/'triangle-inputs-review.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ('status','cells','outputs','raw_body_bytes','actual_output_bytes','total_local_capture_span_seconds')}))
