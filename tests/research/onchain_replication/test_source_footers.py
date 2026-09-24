import io,json
import pytest
import pyarrow as pa
import pyarrow.parquet as pq
from tests.research.test_lifecycle import registered,start,commit
from tradingagents.research.onchain_replication.source_inventory import catalogue_summary
from tradingagents.research.onchain_replication.source_footers import POLICY,select_objects,footer_summary,capture_footer
from tradingagents.research.onchain_replication.provenance import digest,file_hash


def body():
    out=io.BytesIO();pq.write_table(pa.table({'hash':['a'*64],'block_number':[1],'is_coinbase':[False]}),out)
    return out.getvalue()


def test_metadata_parser_reports_missing_fields_without_reading_pages():
    raw=body();length=int.from_bytes(raw[-8:-4],'little')
    summary=footer_summary(raw[-8-length:-8],raw[-8:],'BTC')
    assert summary['rows']==1 and summary['required_fields']['hash']['status']=='metadata_present'
    assert summary['required_fields']['inputs.value']['status']=='unavailable'
    assert not summary['transaction_data_admitted']


def test_selection_is_first_largest_last_without_duplicate_requests():
    objects=[{'key':f'v1.0/btc/transactions/date=2016-01-01/{i}.parquet','date':'2016-01-01','bytes':n,'etag':'"a"'} for i,n in [(3,12),(1,12),(2,20)]]
    assert [x['bytes'] for x in select_objects(catalogue_summary('BTC',2016,objects,True))]==[12,20,12]
    assert len(select_objects(catalogue_summary('BTC',2016,objects[:1],True)))==1
    assert not select_objects(catalogue_summary('BTC',2016,objects,False))


@pytest.mark.parametrize('failure',[None,'etag','range','oversize','timeout'])
def test_capture_uses_exact_registered_ranges_and_retains_failures(registered,failure):
    root,spec,_=registered;policy=root/'footer-policy.json';policy.write_text(json.dumps(POLICY))
    spec['experiments']['example-a']['inputs']['footer_policy']={'path':'footer-policy.json','sha256':file_hash(policy),'dataset':'sample'}
    registered=root,spec,commit(root,spec)
    raw=body();item={'key':'v1.0/btc/transactions/date=2016-01-01/a.parquet','date':'2016-01-01','bytes':len(raw),'etag':'"abc"'}
    parent=root/'research_artifacts/onchain-paper-replication-2026-09-24/sources/example-a/BTC-2016'
    parent.mkdir(parents=True);(parent/'catalogue.json').write_text(json.dumps(catalogue_summary('BTC',2016,[item],True)))
    directory=parent/'footers'/digest(item['key'].encode());calls=[]
    catalogue_sha=file_hash(parent/'catalogue.json')
    def transport(url,headers,limit):
        calls.append(headers)
        if failure=='timeout':raise TimeoutError('synthetic')
        a,b=map(int,headers['Range'][6:].split('-'))
        chunk=raw[a:b+1]
        if failure=='oversize':chunk=b'x'*(limit+1)
        return 206,{'Content-Range':f'bytes {a}-{b}/{len(raw)}' if failure!='range' else 'wrong','ETag':item['etag'] if failure!='etag' else 'changed'},chunk
    with start(registered) as run:
        result=capture_footer(run,'BTC',2016,item,directory=directory,catalogue_sha256=catalogue_sha,transport=transport)
        assert result['status']==('complete' if failure is None else 'unavailable')
        assert len(calls)==(2 if failure is None else 1)
        assert (directory/'trailer-intent.json').exists() and (directory/'result.json').exists()
        with pytest.raises(FileExistsError):capture_footer(run,'BTC',2016,item,directory=directory,catalogue_sha256=catalogue_sha,transport=transport)
        (parent/'catalogue.json').write_bytes(b'{}')
        with pytest.raises(ValueError,match='producer catalogue hash'):capture_footer(run,'BTC',2016,item,directory=directory,catalogue_sha256=catalogue_sha,transport=transport)
