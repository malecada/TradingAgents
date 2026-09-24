import pytest
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
