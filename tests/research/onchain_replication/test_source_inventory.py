import pytest
import json
from tests.research.test_lifecycle import registered,start,commit
from tradingagents.research.onchain_replication.source_inventory import required_cells,required_dates,parse_listing,catalogue_summary


def listing(key='v1.0/btc/transactions/date=2016-01-01/part-0.parquet',truncated='false',token=''):
    return f'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>{truncated}</IsTruncated>{token}<Contents><Key>{key}</Key><Size>1234</Size><ETag>abc</ETag></Contents></ListBucketResult>'.encode()


def test_all_asset_date_field_cells_retained_and_leap_days_explicit():
    assert len(required_dates(2016))==366 and len(required_dates(2017))==365
    cells=[c for a in ('BTC','ETH') for y in range(2016,2025) for c in required_cells(a,y)]
    assert len({c['id'] for c in cells})==len(cells)==3288*(16+10)
    assert all(c['status']=='unavailable' for c in cells)


def test_partial_catalogue_does_not_claim_transaction_coverage():
    objects,token=parse_listing(listing(),'BTC',2016);assert token is None
    report=catalogue_summary('BTC',2016,objects,True)
    assert report['required_dates']==366 and report['listed_dates']==1
    assert report['listed_object_bytes']==1234 and not report['transaction_data_admitted']
    assert report['dates']['2016-01-02']['status']=='unavailable'
    assert report['dates']['2016-01-01']['status']=='metadata_only'


def test_foreign_dates_and_broken_pagination_refused():
    with pytest.raises(ValueError,match='foreign'):parse_listing(listing(key='v1.0/btc/transactions/date=2015-01-01/x.parquet'),'BTC',2016)
    with pytest.raises(ValueError,match='continuation'):parse_listing(listing(truncated='true'),'BTC',2016)


@pytest.mark.parametrize('failure',['http','duplicate','limit','transport','none','shutdown'])
def test_capture_retains_failures_without_retry_and_cannot_relaunch(registered,failure):
    from tradingagents.research.onchain_replication.source_inventory import capture_catalogue,HOST
    from tradingagents.research.onchain_replication.provenance import file_hash
    root,spec,_=registered
    policy=root/'source-policy.json'
    policy.write_text(json.dumps({'asset':'BTC','year':2016,'host':HOST,'max_pages':8,'max_bytes':32*1024**2,'kind':'unsigned_listing_only'}))
    spec['experiments']['example-a']['inputs']['source_policy']={'path':'source-policy.json','sha256':file_hash(policy),'dataset':'sample'}
    registered=root,spec,commit(root,spec)
    output=root/'research_artifacts/onchain-paper-replication-2026-09-24/sources/example-a'
    calls=[]
    def transport(url,headers,limit):
        calls.append(url)
        if failure=='shutdown':raise SystemExit('synthetic shutdown')
        if failure=='transport':raise TimeoutError('synthetic')
        if failure=='limit':return 200,{},b'x'*(limit+1)
        if failure=='http':return 503,{},b'busy'
        if failure=='duplicate':return 200,{},listing(truncated='true',token='<NextContinuationToken>next</NextContinuationToken>')
        return 200,{},listing()
    with start(registered) as run:
        if failure=='shutdown':
            with pytest.raises(SystemExit):capture_catalogue(run,'BTC',2016,output_directory=output,transport=transport)
            assert len(calls)==1 and (output/'intent-00.json').exists()
            assert not (output/'catalogue.json').exists()
            return
        result=capture_catalogue(run,'BTC',2016,output_directory=output,transport=transport)
        assert result['listing_complete']==(failure=='none')
        assert not result['transaction_data_admitted']
        assert len(result['dates'])==366
        assert len(calls)==(2 if failure=='duplicate' else 1)
        assert (output/'intent-00.json').exists() and (output/'catalogue.json').exists()
        if failure!='transport':assert (output/'response-00.json').exists()
        with pytest.raises(FileExistsError):capture_catalogue(run,'BTC',2016,output_directory=output,transport=transport)
