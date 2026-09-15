"""Invented fixed-calendar source responses; no actual prices or return tests."""
import importlib.util
import json
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[2]/'research/broader-allocation-2026-09-15'
s=importlib.util.spec_from_file_location('tested_input_readiness',P/'input_readiness.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
SPEC=json.loads((P/'readiness-spec.json').read_text())


def payload(kind):
    if kind=='usd_identity':return {'error':[],'result':{'USDCUSD':{'base':'USDC','quote':'ZUSD','altname':'USDCUSD','wsname':'USDC/USD'}}}
    times=range(SPEC['start_epoch'],SPEC['terminal_epoch']+1,86400)
    if kind=='usd_bars':return {'error':[],'result':{'USDCUSD':[[t,'1','1.1','0.9','1','1','100',2] for t in times],'last':SPEC['terminal_epoch']}}
    return [[t*1000,'100','110','90','105','100',t*1000+86399999,'10000',2,'50','5000','0'] for t in times]


def fake(url):
    kind=next(r['id'] for r in SPEC['requests'] if r['url']==url)
    return {'body':json.dumps(payload(kind)).encode(),'http_status':200,'headers':{},'error':None,'body_complete':True}


def test_four_sources_join_exact_calendar_no_power_claim():
    r,p,receipts=m.capture(SPEC,fake)
    assert r['attempted_requests']==4 and len(r['cells'])==7 and len(receipts)==4
    assert len(p['joined'])==566
    assert p['joined'][0]['open_epoch']==SPEC['start_epoch'] and p['joined'][-1]['open_epoch']==SPEC['terminal_epoch']
    assert p['joined'][-1]['usd_bars']=={'open':'1'}
    assert sum(c['status']=='unavailable' for c in r['cells'])==1
    assert r['cells'][-1]['id']=='confirmation-power' and not r['confirmation_admitted']


def test_host_denial_preserves_independent_host_and_denominator():
    calls=[]
    def fetch(url):
        calls.append(url)
        if 'binance.com' in url:return {'body':b'denied','http_status':403,'headers':{},'error':'HTTP403','body_complete':True}
        return fake(url)
    r,p,_=m.capture(SPEC,fetch)
    assert len(calls)==3 and len(r['cells'])==7 and p['joined']==[]
    assert r['cells'][1]['status']=='unavailable' and r['cells'][3]['status']=='complete'


def test_identity_failure_skips_dependent_bars_without_substitution():
    def fetch(url):
        response=fake(url)
        if 'AssetPairs' in url:
            data=payload('usd_identity');data['result']['USDCUSD']['quote']='USDT';response['body']=json.dumps(data).encode()
        return response
    r,p,receipts=m.capture(SPEC,fetch)
    assert r['attempted_requests']==3 and receipts[-1]['attempted'] is False and p['joined']==[]


def test_missing_fixed_day_is_retained_not_filled():
    data=payload('btc_bars');del data[30]
    fields,series=m.parse(json.dumps(data).encode(),'btc_bars',SPEC,SPEC['terminal_epoch']+172800)
    assert fields['missing_epochs']==[SPEC['start_epoch']+30*86400] and len(series)==565


@pytest.mark.parametrize('mutation',['duplicate','zero_volume','bad_bounds','wrong_close','boolean','nan','nonutc'])
def test_malformed_source_fails_without_return_screen(mutation):
    data=payload('btc_bars')
    if mutation=='duplicate':data[1]=data[0]
    if mutation=='zero_volume':data[0][5]='0'
    if mutation=='bad_bounds':data[0][1]='120'
    if mutation=='wrong_close':data[0][6]+=1
    if mutation=='boolean':data[0][0]=True
    if mutation=='nan':data[0][2]='NaN'
    if mutation=='nonutc':data[0][0]+=1000
    with pytest.raises((ValueError,ArithmeticError)):m.parse(json.dumps(data).encode(),'btc_bars',SPEC,SPEC['terminal_epoch']+172800)


def test_kraken_current_partial_kept_raw_excluded_from_normalized():
    data=payload('usd_bars');stamp=SPEC['terminal_epoch']+86400
    data['result']['USDCUSD'].append([stamp,'1','1','1','1','1','1',1])
    f,series=m.parse(json.dumps(data).encode(),'usd_bars',SPEC,stamp+10)
    assert f['partial_rows_excluded']==1 and f['coverage_complete'] and str(stamp) not in series


def test_unknown_spec_and_private_url_rejected_without_request():
    with pytest.raises(ValueError):m.capture({**SPEC,'max_requests':5},lambda *_:pytest.fail('not permitted'))
    with pytest.raises(ValueError):m.transport.public_get('https://api.kraken.com/0/private/Balance')


def test_tomorrow_is_invalid_not_a_current_partial_bar():
    data=payload('usd_bars');today=SPEC['terminal_epoch']+86400
    data['result']['USDCUSD'].append([today+86400,'1','1','1','1','1','1',1])
    with pytest.raises(ValueError,match='future daily open'):
        m.parse(json.dumps(data).encode(),'usd_bars',SPEC,today+10)
