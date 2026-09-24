import json
import pytest
from tests.research.test_lifecycle import registered,start,commit
from tradingagents.research.onchain_replication.price_source import price_policy,capture_admitted_prices
from tradingagents.research.onchain_replication.source_inventory import required_dates
from tradingagents.research.onchain_replication.provenance import file_hash


@pytest.mark.parametrize('response',['valid_partial','http_denial','invalid_schema'])
def test_price_source_retains_complete_denominator_and_never_retries(registered,response):
    root,spec,_=registered;policy=root/'policy.json';policy.write_text(json.dumps(price_policy('ETH')))
    spec['experiments']['example-a']['inputs']['price_policy']={'path':'policy.json','sha256':file_hash(policy),'dataset':'sample'}
    dates=[d for y in range(2016,2025) for d in required_dates(y)]
    spec['experiments']['example-a']['cells']=['capture',*('price-'+d for d in dates)]
    fixture=root,spec,commit(root,spec);calls=[]
    def fetch(url,timeout,limit):
        calls.append(url)
        if response=='http_denial':return 429,{},b'synthetic denied'
        if response=='invalid_schema':return 200,{},b'{}'
        return 200,{},json.dumps({'chart':{'error':None,'result':[{'meta':{'symbol':'ETH-USD','currency':'USD','exchangeTimezoneName':'UTC','dataGranularity':'1d'},'timestamp':[1451606400], 'indicators':{'quote':[{'close':[100.]}]}}]}}).encode()
    with start(fixture) as run:
        rows,summary,directory=capture_admitted_prices(run,'ETH',fetch=fetch)
        assert len(rows)==3289 and summary['admitted_dates']==int(response=='valid_partial')
        assert len(summary['missing_dates'])==3288-summary['admitted_dates']
        assert len(list(directory.glob('price-20*.json')))==3288
        assert not summary['financial_run_admitted'] and not summary['all_dates_available']
        with pytest.raises(FileExistsError):capture_admitted_prices(run,'ETH',fetch=fetch)
        assert len(calls)==1
