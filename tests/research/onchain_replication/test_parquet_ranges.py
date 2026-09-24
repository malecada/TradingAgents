import json
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import zstandard
from tests.research.onchain_replication.test_btc_source import row
from tradingagents.research.onchain_replication.parquet_ranges import plan_ranges,decode_projected_btc
from tradingagents.research.onchain_replication.provenance import digest,file_hash


def fixture(tmp_path):
    value=row();value['outputs'][0]['script']='unused-script'*1000
    value['inputs'][0]['script']='unused-input-script'*1000
    path=tmp_path/'synthetic.parquet'
    pq.write_table(pa.Table.from_pylist([value,{**value,'hash':'e'*64}]),path,row_group_size=1)
    raw=path.read_bytes();trailer=raw[-8:];length=int.from_bytes(trailer[:4],'little')
    return raw,raw[-8-length:-8],trailer


@pytest.mark.parametrize('invalid_header',[False,True])
def test_exact_nested_leaf_projection_decodes_every_row_without_script_pages(tmp_path,invalid_header):
    raw,footer,trailer=fixture(tmp_path)
    if invalid_header:raw=b'FAIL'+raw[4:]
    plan=plan_ranges(footer,trailer,len(raw),'BTC',maximum_span_bytes=128)
    assert plan['rows']==2 and plan['row_groups']==2
    assert len(plan['chunks'])==32 and plan['selected_bytes']<len(raw)
    assert all(s['end']-s['start']<=128 for s in plan['spans'])
    spans=[]
    for i,s in enumerate(plan['spans']):
        body=raw[s['start']:s['end']];stored=zstandard.ZstdCompressor().compress(body)
        path=tmp_path/f'{i}.zst';path.write_bytes(stored)
        spans.append({**s,'path':str(path),'raw_bytes':len(body),'raw_sha256':digest(body),
            'stored_bytes':len(stored),'stored_sha256':digest(stored),'codec':'zstd'})
    path=tmp_path/'projected.json';path.write_text(json.dumps({'size':len(raw),'spans':spans,'column_plan':plan}))
    manifest={'status':'complete','path':str(path),'sha256':file_hash(path),'expected_rows':2,'date':'2016-01-01'}
    if invalid_header:
        with pytest.raises(ValueError,match='header'):list(decode_projected_btc(manifest,scratch=tmp_path,precision_policy='binary64_satoshi_grid_inverse_v1'))
        return
    rows=list(decode_projected_btc(manifest,scratch=tmp_path,precision_policy='binary64_satoshi_grid_inverse_v1'))
    assert len(rows)==2 and {x['transaction']['id'] for x in rows}=={'a'*64,'e'*64}
    assert all(x['prevouts'][('c'*64,3)]['satoshis']==9 for x in rows)
    with pytest.raises(ValueError,match='row count'):list(decode_projected_btc({**manifest,'expected_rows':1},scratch=tmp_path,precision_policy='binary64_satoshi_grid_inverse_v1'))
    changed=json.loads(path.read_text());changed['column_plan']['rows']=1;path.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match='plan differs'):list(decode_projected_btc({**manifest,'sha256':file_hash(path)},scratch=tmp_path,precision_policy='binary64_satoshi_grid_inverse_v1'))


def test_column_planner_rejects_missing_required_fields_and_bad_framing(tmp_path):
    raw,footer,trailer=fixture(tmp_path)
    with pytest.raises(ValueError,match='missing'):plan_ranges(footer,trailer,len(raw),'ETH')
    with pytest.raises(ValueError,match='framing'):plan_ranges(footer,b'bad',len(raw),'BTC')
    with pytest.raises(ValueError,match='byte bound'):plan_ranges(footer,trailer,len(raw),'BTC',maximum_span_bytes=0)


def test_external_column_chunks_are_not_silently_read_from_current_object(tmp_path):
    import io
    raw,footer,trailer=fixture(tmp_path)
    metadata=pq.read_metadata(io.BytesIO(raw));metadata.set_file_path('external-object.parquet')
    buffer=io.BytesIO();metadata.write_metadata_file(buffer);new=buffer.getvalue()
    new_trailer=new[-8:];n=int.from_bytes(new_trailer[:4],'little');new_footer=new[-8-n:-8]
    new_size=len(raw)-len(footer)+len(new_footer)
    with pytest.raises(ValueError,match='external column'):
        plan_ranges(new_footer,new_trailer,new_size,'BTC')
