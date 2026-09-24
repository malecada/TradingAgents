import hashlib
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tradingagents.research.onchain_replication.eth_source import decode_eth


def test_verified_stream_keeps_precision_and_filter_inputs(tmp_path):
    table=pa.table({'hash':['0x'+'1'*64], 'block_timestamp':pa.array([1704153600000000000],type=pa.timestamp('ns')), 'from_address':['0x'+'a'*40], 'to_address':['None'],'value':[1e18], 'receipt_status':pa.array([1],type=pa.int64())})
    path=tmp_path/'source.parquet';pq.write_table(table,path)
    m={'members':[{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'format':'parquet'}],'start_utc':'2024-01-01T00:00:00Z','end_utc':'2024-01-08T00:00:00Z'}
    schema={f.name:str(f.type) for f in table.schema}
    rows=list(decode_eth(m,schema));assert len(rows)==1
    assert rows[0].recipient is None and rows[0].value==1 and rows[0].precision=='approximate_ETH'
    path.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='hash'):list(decode_eth(m,schema))


def test_projected_archive_columns_are_decoded_without_missing_byte_fill(tmp_path):
    import json,struct,zstandard
    from tradingagents.research.onchain_replication.eth_source import projected_parquet
    table=pa.table({'hash':['0x'+'1'*64], 'block_timestamp':pa.array([1704153600000000000],type=pa.timestamp('ns')), 'from_address':['0x'+'a'*40], 'to_address':['0x'+'b'*40],'value':[1e18], 'receipt_status':pa.array([1],type=pa.int64())})
    p=tmp_path/'full.parquet';pq.write_table(table,p);body=p.read_bytes()
    footer_len=struct.unpack('<I',body[-8:-4])[0]+8
    chunks=[(0,4),(4,len(body)-footer_len),(len(body)-footer_len,len(body))]
    spans=[]
    for i,(a,b) in enumerate(chunks):
        raw=body[a:b];stored=zstandard.ZstdCompressor(write_content_size=True).compress(raw)
        path=tmp_path/f'{i}.zst';path.write_bytes(stored)
        spans.append(dict(path=str(path),start=a,end=b,stored_sha256=hashlib.sha256(stored).hexdigest(),raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw),stored_bytes=len(stored)))
    m={'size':len(body),'spans':spans}
    with projected_parquet(m,tmp_path) as reader:
        assert pq.ParquetFile(reader,pre_buffer=False).read().to_pydict()==table.to_pydict()
    bad={'size':len(body),'spans':[spans[0],spans[-1]]}
    with projected_parquet(bad,tmp_path) as reader:
        reader.seek(4)
        with pytest.raises(ValueError,match='unacquired'):reader.read(10)
