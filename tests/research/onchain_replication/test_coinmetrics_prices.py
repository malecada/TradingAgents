import json
import http.client
from datetime import date, timedelta
import pytest
from tradingagents.research.onchain_replication.coinmetrics_prices import (
    price_policy, parse_prices, capture_response, capture_admitted_prices)
from tradingagents.research.onchain_replication.provenance import digest, file_hash
from tests.research.test_lifecycle import registered, start, commit
from tradingagents.research.onchain_replication.source_inventory import required_dates


def parse(raw, **kwargs):
    return parse_prices(raw, expected_dates=['2016-01-01', '2016-01-02'],
        policy=price_policy('BTC'), sha256=digest(raw), retrieved_at='2026-09-24T00:00:00Z', **kwargs)


def test_dates_missing_values_and_outside_rows_are_not_filled_or_shifted():
    panel, extent = parse(b'time,Other,PriceUSD\n2015-12-31,x,4\n2016-01-01,x,10.25\n2016-01-02,x,\n2025-01-01,x,99\n')
    assert panel.dates == ('2016-01-01',) and panel.closes == (10.25,)
    assert panel.missing_dates == ('2016-01-02',)
    assert extent == {'rows':4, 'first_date':'2015-12-31', 'last_date':'2025-01-01', 'outside_required_dates':2}


@pytest.mark.parametrize('raw', [
    b'time,ReferenceRateUSD\n2016-01-01,1\n',
    b'time,PriceUSD,PriceUSD\n2016-01-01,1,2\n',
    b'time,PriceUSD\n2016-01-01,1\n2016-01-01,2\n',
    b'time,PriceUSD\n2016-01-02,1\n2016-01-01,2\n',
    b'time,PriceUSD\n2016-1-01,1\n',
    b'time,PriceUSD\n2016-02-30,1\n',
    b'time,PriceUSD\n2016-01-01,NaN\n',
    b'time,PriceUSD\n2016-01-01,0\n',
    b'time,PriceUSD\n2016-01-01,1e999\n',
    b'time,PriceUSD\n2016-01-01,1,extra\n',
    b'time,PriceUSD\n2016-01-01,"unclosed\n',
    b'time,PriceUSD\n2016-01-01,\xff\n',
])
def test_invalid_sources_rejected(raw):
    with pytest.raises(ValueError): parse(raw)


def test_hash_mismatch_and_wrong_policy_rejected():
    raw=b'time,PriceUSD\n2016-01-01,1\n'
    with pytest.raises(ValueError, match='hash'):
        parse_prices(raw, expected_dates=['2016-01-01'], policy=price_policy('BTC'), sha256='0'*64, retrieved_at='2026-09-24T00:00:00Z')
    policy=price_policy('BTC');policy['url'] += '?different'
    with pytest.raises(ValueError, match='policy'): capture_response(policy, '/unused', fetch=lambda *a: None)


def test_parser_enforces_rows_columns_and_unrelated_row_validity():
    days = [date(2000,1,1)+timedelta(days=i) for i in range(10001)]
    raw = ('time,PriceUSD\n'+''.join(f'{d},1\n' for d in days)).encode()
    with pytest.raises(ValueError, match='row bound'): parse(raw)
    with pytest.raises(ValueError, match='header'):
        parse(('time,PriceUSD,'+','.join('m'+str(i) for i in range(511))+'\n').encode())
    with pytest.raises(ValueError, match='PriceUSD'):
        parse(b'time,PriceUSD\n2015-12-31,-1\n2016-01-01,2\n')


def test_oversized_response_is_unavailable_and_prefix_preserved(tmp_path):
    raw=b'x'*(price_policy('BTC')['max_bytes']+1)
    result,body=capture_response(price_policy('BTC'),tmp_path/'capture',fetch=lambda *args:(200,{},raw))
    assert result['status']=='unavailable' and body.stat().st_size==len(raw)


def test_partial_transport_bytes_retained_without_retry(tmp_path):
    calls=[]
    def fetch(*args):
        calls.append(args);raise http.client.IncompleteRead(b'prefix', 10)
    result, body=capture_response(price_policy('BTC'), tmp_path/'capture', fetch=fetch)
    assert result['status']=='unavailable' and body.read_bytes()==b'prefix'
    assert result['http_status'] is None and len(calls)==1
    with pytest.raises(FileExistsError): capture_response(price_policy('BTC'),tmp_path/'capture',fetch=fetch)
    assert len(calls)==1


@pytest.mark.parametrize('status,raw,admitted', [(200,b'time,PriceUSD\n2016-01-01,2\n',1),(429,b'denied',0),(200,b'time,ReferenceRateUSD\n2016-01-01,2\n',0)])
def test_registered_capture_preserves_all_cells(registered,status,raw,admitted):
    root,spec,_=registered;policy=root/'policy.json';policy.write_text(json.dumps(price_policy('ETH')))
    spec['experiments']['example-a']['inputs']['price_policy']={'path':'policy.json','sha256':file_hash(policy),'dataset':'sample'}
    dates=[d for y in range(2016,2025) for d in required_dates(y)]
    spec['experiments']['example-a']['cells']=['capture',*('price-'+d for d in dates)]
    fixture=root,spec,commit(root,spec);calls=[]
    def fetch(*args):calls.append(args);return status,{},raw
    with start(fixture) as run:
        rows,summary,directory=capture_admitted_prices(run,'ETH',fetch=fetch)
        assert len(rows)==3289 and summary['admitted_dates']==admitted
        assert len(summary['missing_dates'])==3288-admitted
        assert not summary['financial_run_admitted']
        assert len(list(directory.glob('price-20*.json')))==3288
        with pytest.raises(FileExistsError):capture_admitted_prices(run,'ETH',fetch=fetch)
        assert len(calls)==1
