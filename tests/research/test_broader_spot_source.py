"""Frozen public spot-source parsing and denial behavior with invented replies."""
import importlib.util
import json
from pathlib import Path
import pytest

P=Path(__file__).resolve().parents[2]/'research/broader-allocation-2026-09-15'
s=importlib.util.spec_from_file_location('tested_spot_source',P/'spot_source.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
SPEC=json.loads((P/'spot-source-spec.json').read_text())


def payloads():
    rows=[]
    for symbol,base in [('BTCUSDC','BTC'),('ETHUSDC','ETH')]:
        rows.append({'symbol':symbol,'baseAsset':base,'quoteAsset':'USDC','status':'TRADING','isSpotTradingAllowed':True,'filters':[
            {'filterType':'LOT_SIZE','minQty':'0.001','maxQty':'100','stepSize':'0.001'},
            {'filterType':'PRICE_FILTER','minPrice':'0','maxPrice':'0','tickSize':'0.01'},
            {'filterType':'NOTIONAL','minNotional':'5','maxNotional':'100000'},
            {'filterType':'UNKNOWN_NEW_FILTER','note':'retained but not implemented'}]})
    return {'clock':{'serverTime':1700000000000},'symbols':{'symbols':rows},
        'btc_depth':{'lastUpdateId':1,'bids':[['99','2'],['98','4']],'asks':[['101','2'],['102','4']]},
        'eth_depth':{'lastUpdateId':2,'bids':[['9','20']],'asks':[['11','20']]}}


def fetch(url):
    kind=next(r['id'] for r in SPEC['requests'] if r['url']==url)
    return dict(body=json.dumps(payloads()[kind]).encode(),http_status=200,headers={},error=None,body_complete=True)


def test_all_four_source_cells_and_no_financial_admission():
    result,receipts=m.capture(SPEC,fetch)
    assert len(result['cells'])==len(receipts)==result['attempted_requests']==4
    assert all(r['status']=='complete' for r in result['cells'])
    assert not result['implementation_admitted']
    assert result['cells'][2]['fields']['top_bid']=='99'
    assert result['cells'][2]['fields']['event_time']=='unavailable'
    symbols=result['cells'][1]['fields']['symbols']
    assert 'UNKNOWN_NEW_FILTER' in symbols['BTCUSDC']['filters']
    assert symbols['BTCUSDC']['filter_implementation_complete'] is False


def test_denied_host_keeps_four_unavailable_cells_no_retry():
    calls=[]
    def denied(url):
        calls.append(url);return dict(body=b'denied',http_status=451,headers={},error='HTTP451',body_complete=True)
    result,receipts=m.capture(SPEC,denied)
    assert len(calls)==result['attempted_requests']==1
    assert len(result['cells'])==4 and all(r['status']=='unavailable' for r in result['cells'])
    assert [r['attempted'] for r in receipts]==[True,False,False,False]


def test_wrong_quote_and_missing_filter_block_depths():
    def wrong(url):
        r=fetch(url)
        if 'exchangeInfo' in url:
            d=payloads()['symbols'];d['symbols'][0]['quoteAsset']='USDT';r['body']=json.dumps(d).encode()
        return r
    result,receipts=m.capture(SPEC,wrong)
    assert result['attempted_requests']==2 and all(r['status']=='unavailable' for r in result['cells'][1:])
    d=payloads()['symbols'];d['symbols'][0]['filters']=[]
    with pytest.raises(ValueError):m.parse(json.dumps(d).encode(),'symbols')


@pytest.mark.parametrize('change',[{'bids':[['102','2']]},{'bids':[['99','0']]},{'bids':[['99','2'],['99','3']]},{'asks':[['102','2'],['101','2']]},{'lastUpdateId':True},{'asks':[['NaN','1']]}])
def test_invalid_depth_cannot_be_admitted(change):
    d={**payloads()['btc_depth'],**change}
    with pytest.raises(ValueError):m.parse(json.dumps(d).encode(),'btc_depth')


def test_unknown_spec_and_private_endpoint_rejected_without_fetch():
    with pytest.raises(ValueError):m.capture({**SPEC,'max_requests':5},lambda *a:pytest.fail('must not fetch'))
    with pytest.raises(ValueError):m.transport.public_get('https://api.binance.com/api/v3/account')


def test_boolean_clock_is_not_millisecond_time():
    with pytest.raises(ValueError):m.parse(b'{"serverTime":true}','clock')
