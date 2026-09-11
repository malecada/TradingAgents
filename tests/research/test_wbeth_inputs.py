"""Invented WBETH payloads only; no network or empirical source reads."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

DIRECTORY = Path(__file__).resolve().parents[2] / 'research/strategy-search-2026-09-11'
sys.path.insert(0, str(DIRECTORY))
import wbeth_inputs as module


def spec():
    return json.loads((DIRECTORY/'wbeth-request-spec.json').read_text())


def bars():
    return [[module.START_MS+i*module.DAY_MS,'100','102','99','101','5',
             module.START_MS+(i+1)*module.DAY_MS-1,'500',2,'2','200','0'] for i in range(91)]


def metadata():
    return {'symbols':[{'symbol':'WBETHUSDT','baseAsset':'WBETH','quoteAsset':'USDT',
        'status':'TRADING','isSpotTradingAllowed':True,'filters':[{'filterType':'LOT_SIZE','stepSize':'0.0001'}]}]}


def response(body, status=200):
    return {'body':body,'http_status':status,'headers':{},'body_complete':True,'error':None}


def test_fixed_synthetic_sources_and_immediate_persistence():
    saved=[]
    def transport(url):
        assert len(saved)==(0 if 'exchangeInfo' in url else 1)
        return response(json.dumps(metadata() if 'exchangeInfo' in url else bars()).encode())
    raw, admitted, cells=module.capture(spec(),transport,lambda name,value:saved.append((name,value)))
    assert len(saved)==len(cells)==2
    assert all(c['status']=='complete' for c in cells)
    assert admitted['cells'][1]['observations']==91
    assert admitted['cells'][0]['symbol_metadata']['filters']==metadata()['symbols'][0]['filters']
    assert all(hashlib.sha256(__import__('base64').b64decode(r['body_base64'])).hexdigest()==r['body_sha256'] for r in raw['requests'])


@pytest.mark.parametrize('bad',['missing','extra','clock','fractional_clock','bool_clock','shape','ohlc','negative_volume','nan','bool_trade','negative_trade','injected'])
def test_bad_bars_unavailable_without_dropping_other_cell(bad):
    data=bars()
    if bad=='missing':data.pop()
    elif bad=='extra':data.append(data[-1])
    elif bad=='clock':data[2][0]+=1
    elif bad=='fractional_clock':data[2][0]+=.5
    elif bad=='bool_clock':data[2][0]=True
    elif bad=='shape':data[2].pop()
    elif bad=='ohlc':data[2][2]='50'
    elif bad=='negative_volume':data[2][5]='-1'
    elif bad=='nan':data[2][3]='NaN'
    elif bad=='bool_trade':data[2][8]=True
    elif bad=='negative_trade':data[2][8]=-1
    body=json.dumps(data).encode()+ (b',"injected":true' if bad=='injected' else b'')
    raw, admission, cells=module.capture(spec(),lambda url:response(json.dumps(metadata()).encode() if 'exchangeInfo' in url else body))
    assert [c['status'] for c in cells]==['complete','unavailable']
    assert len(raw['requests'])==2


def test_zero_activity_is_retained_as_source_fact():
    data=bars();data[1][5]='0';data[4][8]=0
    result=module.parse_response(json.dumps(data).encode(),spec()['requests'][1])
    assert result['status']=='complete' and result['zero_activity_row_indices']==[1,4]


@pytest.mark.parametrize('bad',['identity','disabled','duplicate_filter','duplicate_json'])
def test_metadata_identity_failures(bad):
    data=metadata()
    if bad=='identity':data['symbols'][0]['baseAsset']='ETH'
    elif bad=='disabled':data['symbols'][0]['isSpotTradingAllowed']=1
    elif bad=='duplicate_filter':data['symbols'][0]['filters']*=2
    body=json.dumps(data).encode() if bad!='duplicate_json' else b'{"symbols":[],"symbols":[]}'
    with pytest.raises((ValueError,TypeError)):
        module.parse_response(body,spec()['requests'][0])


def test_denial_suppresses_second_same_host_and_retains_two_cells():
    calls=[]
    def transport(url):calls.append(url);return response(b'denied',403)
    raw, admission, cells=module.capture(spec(),transport)
    assert len(calls)==1 and len(cells)==2 and all(c['status']=='unavailable' for c in cells)
    assert raw['requests'][1]['attempted'] is False


def test_changed_spec_cannot_start_transport():
    data=spec();data['requests'][1]['url']+='&changed=1'
    with pytest.raises(ValueError,match='frozen'):
        module.capture(data,lambda url:pytest.fail('must not call'))
