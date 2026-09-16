"""Invented source metadata fixtures; no public archive or financial reads."""
import importlib.util
import base64
import hashlib
import io
import json
from pathlib import Path
import struct
import urllib.parse

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

PATH=Path(__file__).resolve().parents[2]/'research/onchain-graph-2026-09-16/panel_readiness/audit.py'
spec=importlib.util.spec_from_file_location('panel_metadata_tested',PATH)
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def xml(table='blocks',year=2024,keys=None,truncated=False):
    prefix=f'v1.0/eth/{table}/date={year}-'
    objects=''.join(f'<Contents><Key>{prefix}{key}</Key><Size>1234</Size><ETag>"test"</ETag><LastModified>2026-09-16T00:00:00Z</LastModified></Contents>' for key in (keys or []))
    return (f'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Prefix>{prefix}</Prefix><IsTruncated>{str(truncated).lower()}</IsTruncated>{objects}</ListBucketResult>').encode()


def test_inventory_dates_missing_ambiguous_and_leap_year():
    inv=audit.inventory(xml(keys=['01-01/a.parquet','02-29/a.parquet','03-01/a.parquet','03-01/b.parquet']),'blocks',2024)
    assert len(inv['dates'])==366
    rows={r['date']:r for r in inv['dates']}
    assert rows['2024-02-29']['status']=='complete'
    assert rows['2024-03-01']['reason'].startswith('multiple')
    assert rows['2024-12-31']['reason']=='missing object'
    assert sum(r['status']=='complete' for r in rows.values())==2


def test_truncation_or_unexpected_keys_cannot_admit_coverage():
    for raw in [xml(keys=['01-01/a.parquet'],truncated=True),xml(keys=['01-01/a.parquet','02-30/a.parquet'])]:
        inv=audit.inventory(raw,'blocks',2024)
        assert all(r['status']=='unavailable' for r in inv['dates'])
    with pytest.raises(ValueError,match='duplicate'):
        audit.inventory(xml(keys=['01-01/a.parquet']*2),'blocks',2024)


def test_footer_projection_matches_invented_encoded_columns():
    table=pa.table({'number':[1,2],'hash':['a','b'],'parent_hash':['z','a'],
                    'timestamp':pa.array([1,2],type=pa.timestamp('ns')),'transaction_count':[3,4],
                    'unneeded':['long data payload'*20]*2})
    sink=io.BytesIO();pq.write_table(table,sink,row_group_size=1);raw=sink.getvalue();length=struct.unpack('<I',raw[-8:-4])[0]
    result=audit.projected_metadata(raw[-8:],raw[-length-8:],{'size':len(raw)},'blocks')
    metadata=pq.read_metadata(io.BytesIO(raw))
    expected=sum(metadata.row_group(g).column(c).total_compressed_size for g in range(2) for c in range(5))
    assert result['projected_compressed_bytes']==expected
    assert result['projected_range_count']==10 and not result['missing_columns']
    with pytest.raises(ValueError):audit.projected_metadata(b'bad tail',raw[-length-8:],{'size':len(raw)},'blocks')


def test_exact_january_reuse_rejects_changed_object_without_network():
    class Capture:
        spec={'base_url':'https://example.invalid/'}
        def get(self,*args):raise AssertionError('no substitute acquisition')
    retained={'blocks':[{'url':'old','request_headers':{'If-Match':'old'}}]*2}
    with pytest.raises(ValueError,match='identity changed'):
        audit.inspect(Capture(),{'key':'new','etag':'new','size':100},'blocks','2024-01-01',retained)


def test_failed_source_retains_entire_fixed_denominator(monkeypatch):
    class FailedCapture:
        def __init__(self,spec,publish):self.count=0;self.total=0;self.spec=spec
        def get(self,url):return None,{'error':'source denied'}
    monkeypatch.setattr(audit.transport,'Capture',FailedCapture)
    spec={'years':[2022,2023,2024],'tables':['blocks','transactions'],'base_url':'https://example.invalid/',
          'max_keys':1000,'max_requests':54,'sample_dates':[f'{y}-{m:02d}-01' for y in [2022,2023,2024] for m in [1,4,7,10]]}
    outputs={};cells=audit.execute(spec,{},lambda n,v:outputs.setdefault(n,v))
    assert len(cells)==30 and all(c['status']=='unavailable' for c in cells)
    assert len(outputs)==111
    assert sum(len(i['dates']) for i in outputs['inventory.json']['inventories'])==2192
    assert outputs['summary.json']['transaction_rows_decoded']==0
    assert len(outputs['schemas.json']['samples'])==24


@pytest.mark.parametrize('type_drift',[False,True])
def test_complete_fixed_sequence_reuses_four_receipts_and_retains_drift(monkeypatch,type_drift):
    plan=json.loads((PATH.parent/'plan.json').read_bytes())
    payloads={}
    for table,types in plan['required_types'].items():
        arrays={}
        for column,kind in types.items():
            arrow_type={'string':pa.string(),'int64':pa.int64(),'double':pa.float64(),'timestamp[ns]':pa.timestamp('ns')}[kind]
            if type_drift and column=='receipt_status':arrow_type=pa.string()
            arrays[column]=pa.array(['a','b'] if pa.types.is_string(arrow_type) else [1,2],type=arrow_type)
        sink=io.BytesIO();pq.write_table(pa.table(arrays),sink);payloads[table]=sink.getvalue()
    def record(body,url,headers,status,response_headers):
        return {'url':url,'request_headers':headers,'status':status,'response_headers':response_headers,
                'body_base64':base64.b64encode(body).decode(),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
    retained={}
    for table,raw in payloads.items():
        url=plan['base_url']+f'v1.0/eth/{table}/date=2024-01-01/fixture.parquet';end=len(raw)-1
        length=struct.unpack('<I',raw[-8:-4])[0]
        retained[table]=[]
        for start in [end-7,len(raw)-length-8]:
            retained[table].append(record(raw[start:],url,{'Range':f'bytes={start}-{end}','If-Match':'"fixture"'},206,
                {'etag':'"fixture"','content-range':f'bytes {start}-{end}/{len(raw)}'}))
    class SyntheticCapture:
        def __init__(self,spec,publish):self.spec=spec;self.publish=publish;self.count=0;self.total=0
        def get(self,url,headers=None):
            self.count+=1;headers=headers or {};self.publish(f'request-{self.count:02d}-intent.json',{'url':url})
            parsed=urllib.parse.urlparse(url)
            if parsed.query:
                prefix=urllib.parse.parse_qs(parsed.query)['prefix'][0];table=prefix.split('/')[2];year=int(prefix.split('date=')[1][:4])
                body=xml(table,year,[f'{d[5:]}/fixture.parquet' for d in audit.dates(year)]).replace(b'<Size>1234</Size>',f'<Size>{len(payloads[table])}</Size>'.encode()).replace(b'"test"',b'"fixture"')
                result=record(body,url,headers,200,{})
            else:
                table=parsed.path.split('/')[3];raw=payloads[table]
                assert headers['If-Match']=='"fixture"'
                start,end=map(int,headers['Range'].removeprefix('bytes=').split('-'));body=raw[start:end+1]
                result=record(body,url,headers,206,{'etag':'"fixture"','content-range':f'bytes {start}-{end}/{len(raw)}'})
            self.total+=len(body);self.publish(f'request-{self.count:02d}.json',result);return body,result
    monkeypatch.setattr(audit.transport,'Capture',SyntheticCapture)
    output={};cells=audit.execute(plan,retained,lambda n,v:output.setdefault(n,v))
    assert len(output)==111 and output['summary.json']['requests']==50
    assert output['summary.json']['complete_date_table_cells']==2192
    assert output['summary.json']['complete_schema_cells']==(12 if type_drift else 24)
    assert sum(c['status']=='unavailable' for c in cells)==(12 if type_drift else 0)
    if type_drift:
        failed=[s for s in output['schemas.json']['samples'] if s['status']=='unavailable']
        assert all(s['metadata']['schema']['receipt_status']=='string' and s['type_drift'] for s in failed)
