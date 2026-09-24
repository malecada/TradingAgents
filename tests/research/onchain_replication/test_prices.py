import hashlib,json
import pytest
from tradingagents.research.onchain_replication.prices import read_prices


def test_yahoo_instrument_gaps_and_unadjusted_field(tmp_path):
    x={'chart':{'error':None,'result':[{'meta':{'symbol':'ETH-USD','currency':'USD','exchangeTimezoneName':'UTC','dataGranularity':'1d'},'timestamp':[1704067200,1704153600], 'indicators':{'quote':[{'close':[100.,110.]}],'adjclose':[{'adjclose':[1.,2.]}]}}]}}
    p=tmp_path/'prices.json';p.write_text(json.dumps(x))
    m={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'complete','retrieved_at':'2026-09-24T00:00:00Z','expected_dates':['2024-01-01','2024-01-02','2024-01-03']}
    panel=read_prices(m,{'symbol':'ETH-USD','field':'unadjusted daily Close'})
    assert panel.closes==(100.,110.) and panel.missing_dates==('2024-01-03',)
    with pytest.raises(ValueError,match='instrument'):read_prices(m,{'symbol':'BTC-USD','field':'unadjusted daily Close'})
    with pytest.raises(ValueError,match='unavailable'):read_prices(m|{'status':'unavailable'},{'symbol':'ETH-USD'})


def test_capture_retains_denial_and_never_retries(tmp_path):
    from tradingagents.research.onchain_replication.prices import capture_prices
    calls=[]
    def fetch(url,timeout,maximum):
        calls.append(url);return 429,{'content-type':'text/plain'},b'denied'
    contract={'url':'https://query1.finance.yahoo.com/v8/finance/chart/ETH-USD?period1=1&period2=2&interval=1d','timeout_seconds':10,'max_bytes':1000}
    result=capture_prices(contract,tmp_path,'a'*64,fetch=fetch)
    assert result['status']=='unavailable' and result['http_status']==429 and len(calls)==1
    assert (tmp_path/('a'*64)/'response.bin').read_bytes()==b'denied'
    with pytest.raises(FileExistsError):capture_prices(contract,tmp_path,'a'*64,fetch=fetch)
    assert len(calls)==1


@pytest.mark.parametrize('bad',['boolean_close','boolean_timestamp','multiple_quotes','weekly','granularity_absent'])
def test_ambiguous_or_nonnumeric_price_schema_rejected(tmp_path,bad):
    data={'meta':{'symbol':'BTC-USD','currency':'USD','exchangeTimezoneName':'UTC','dataGranularity':'1d'},
          'timestamp':[1704067200],'indicators':{'quote':[{'close':[100.]}]}}
    if bad=='boolean_close':data['indicators']['quote'][0]['close']=[True]
    elif bad=='boolean_timestamp':data['timestamp']=[True]
    elif bad=='multiple_quotes':data['indicators']['quote'].append({'close':[200.]})
    elif bad=='weekly':data['meta']['dataGranularity']='1wk'
    else:del data['meta']['dataGranularity']
    p=tmp_path/'raw.json';p.write_text(json.dumps({'chart':{'error':None,'result':[data]}}))
    manifest={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'complete',
              'retrieved_at':'2026-09-24T00:00:00Z','expected_dates':['2024-01-01']}
    with pytest.raises(ValueError):read_prices(manifest,{'symbol':'BTC-USD','field':'unadjusted daily Close'})


def test_price_parser_uses_the_same_buffer_as_hash_check(tmp_path,monkeypatch):
    from pathlib import Path
    data={'chart':{'error':None,'result':[{'meta':{'symbol':'BTC-USD','currency':'USD','exchangeTimezoneName':'UTC','dataGranularity':'1d'},'timestamp':[1704067200],'indicators':{'quote':[{'close':[100.]}]}}]}}
    path=tmp_path/'raw.json';raw=json.dumps(data).encode();path.write_bytes(raw)
    manifest={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'status':'complete',
              'retrieved_at':'2026-09-24T00:00:00Z','expected_dates':['2024-01-01']}
    original=Path.read_bytes;calls=[]
    def switched(p):
        value=original(p)
        if p==path:
            calls.append(1);p.write_bytes(raw.replace(b'100.0',b'999.0'))
        return value
    monkeypatch.setattr(Path,'read_bytes',switched)
    panel=read_prices(manifest,{'symbol':'BTC-USD','field':'unadjusted daily Close'})
    assert panel.closes==(100.,) and len(calls)==1
