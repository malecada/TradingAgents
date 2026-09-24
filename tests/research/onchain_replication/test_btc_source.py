from datetime import datetime,timezone
import pytest
from tradingagents.research.onchain_replication.btc_source import normalize_btc_row


def row():
    return {'hash':'a'*64,'block_hash':'b'*64,'block_number':10,'index':1,
            'block_timestamp':datetime(2016,1,1,12,tzinfo=timezone.utc),'is_coinbase':False,
            'input_count':1,'output_count':1,
            'inputs':[{'index':0,'spent_transaction_hash':'c'*64,'spent_output_index':3,'address':'sender','value':.00000009}],
            'outputs':[{'index':0,'address':'recipient','value':.00000007}]}


def normalize(value):return normalize_btc_row(value,source_hash='d'*64,expected_day='2016-01-01',precision_policy='binary64_satoshi_grid_inverse_v1')


def test_normalized_source_preserves_exact_prevouts_and_chain_position():
    result=normalize(row())
    assert result['prevouts'][('c'*64,3)]=={'address':'sender','satoshis':9}
    assert result['transaction']['outputs']==[{'address':'recipient','satoshis':7}]
    assert result['chain_position']==(10,1)
    assert result['block_hash']=='b'*64 and result['timestamp']=='2016-01-01T12:00:00Z'


@pytest.mark.parametrize('mutation,reason',[
    ('count','count'),('index','contiguous'),('duplicate','contiguous'),('day','date'),
    ('precision','satoshi-grid'),('missing_position','index'),('negative_position','position')])
def test_malformed_or_incomplete_source_remains_unavailable(mutation,reason):
    value=row()
    if mutation=='count':value['output_count']=2
    if mutation=='index':value['outputs'][0]['index']=1
    if mutation=='duplicate':value['outputs']*=2;value['output_count']=2
    if mutation=='day':value['block_timestamp']=datetime(2016,1,2,tzinfo=timezone.utc)
    if mutation=='precision':value['outputs'][0]['value']=.000000001
    if mutation=='missing_position':del value['index']
    if mutation=='negative_position':value['index']=-1
    with pytest.raises((ValueError,KeyError),match=reason):normalize(value)


def test_missing_address_is_explicit_and_nonstring_source_schema_is_unadmitted():
    value=row();value['outputs'][0]['address']=None
    assert normalize(value)['transaction']['outputs'][0]['address'] is None
    for address in (['a'],['a','b'],[],('a',)):
        value['outputs'][0]['address']=address
        with pytest.raises(ValueError,match='schema unadmitted'):normalize(value)
    with pytest.raises(ValueError,match='precision policy'):
        normalize_btc_row(row(),source_hash='d'*64,expected_day='2016-01-01',precision_policy='round_float')


def test_coinbase_position_and_null_prevout_are_not_fabricated():
    value=row();value['is_coinbase']=True
    with pytest.raises(ValueError,match='coinbase flag'):normalize(value)
    value['index']=0;value['inputs'][0]['spent_transaction_hash']=None
    result=normalize(value)
    assert result['transaction']['coinbase'] and not result['prevouts']


def test_streamed_parquet_body_is_hash_count_date_and_position_bound(tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq
    from tradingagents.research.onchain_replication.btc_source import decode_parquet
    from tradingagents.research.onchain_replication.provenance import file_hash
    path=tmp_path/'synthetic.parquet';pq.write_table(pa.Table.from_pylist([row()]),path)
    manifest={'status':'complete','path':str(path),'sha256':file_hash(path),'expected_rows':1,'date':'2016-01-01'}
    values=list(decode_parquet(manifest,precision_policy='binary64_satoshi_grid_inverse_v1'))
    assert len(values)==1 and values[0]['prevouts'][('c'*64,3)]['satoshis']==9
    with pytest.raises(ValueError,match='row count'):list(decode_parquet({**manifest,'expected_rows':2},precision_policy='binary64_satoshi_grid_inverse_v1'))
    with pytest.raises(ValueError,match='date'):list(decode_parquet({**manifest,'date':'2016-01-02'},precision_policy='binary64_satoshi_grid_inverse_v1'))
    path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash'):list(decode_parquet(manifest,precision_policy='binary64_satoshi_grid_inverse_v1'))
