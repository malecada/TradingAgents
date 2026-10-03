"""Strict normalized BTC row adapter; source acquisition/admission is separate.

Individual binary64 values must be exact images of integer satoshis. Producer
floating aggregate totals/fees are not substituted for exact prevout arithmetic.
The provider supplies prevout enrichment; observed overlap is checked by the
weekly builder, while external prevout/canonical-chain provenance stays qualified.
"""
from datetime import datetime,timezone
from pathlib import Path
from .btc import recover_binary64_satoshis
from .provenance import require_hash,file_hash,utc

REQUIRED=('hash','block_hash','block_number','index','block_timestamp','is_coinbase',
          'input_count','output_count','inputs','outputs')


def _integer(value,label):
    if type(value) is not int or value<0:raise ValueError('invalid '+label)
    return value


def _ordered(values,count):
    if type(values) is not list or len(values)!=_integer(count,'nested count'):raise ValueError('nested count mismatch')
    for item in values:_integer(item['index'],'nested index')
    if sorted(x['index'] for x in values)!=list(range(len(values))):raise ValueError('nested indices must be unique and contiguous')
    return sorted(values,key=lambda x:x['index'])


def _output(value):
    address=value['address']
    if address is None or address=='':address=None
    elif type(address) is not str:raise ValueError('source address schema unadmitted; expected nullable single string')
    return {'address':address,'satoshis':recover_binary64_satoshis(value['value'])}


def normalize_btc_row(row,*,source_hash,expected_day,precision_policy):
    if precision_policy!='binary64_satoshi_grid_inverse_v1':raise ValueError('unadmitted precision policy')
    require_hash(source_hash)
    for name in REQUIRED:
        if name not in row:raise KeyError('missing required '+name)
    require_hash(row['hash']);require_hash(row['block_hash'])
    position=(_integer(row['block_number'],'chain position height'),_integer(row['index'],'chain position index'))
    if type(row['is_coinbase']) is not bool:raise ValueError('coinbase flag required')
    if row['is_coinbase']!=(position[1]==0):raise ValueError('coinbase flag and block transaction position differ')
    timestamp=row['block_timestamp']
    if isinstance(timestamp,datetime):
        # The admitted AWS timestamp convention is UTC even without Arrow timezone metadata.
        if timestamp.tzinfo is None:timestamp=timestamp.replace(tzinfo=timezone.utc)
        timestamp=timestamp.isoformat()
    timestamp=utc(timestamp)
    if timestamp.date().isoformat()!=expected_day:raise ValueError('source partition date mismatch')
    inputs=_ordered(row['inputs'],row['input_count']);outputs=_ordered(row['outputs'],row['output_count'])
    if not outputs:raise ValueError('transaction has no outputs')
    normalized=[];prevouts={}
    if not row['is_coinbase']:
        if not inputs:raise ValueError('non-coinbase transaction has no inputs')
        for item in inputs:
            txid=item['spent_transaction_hash'];require_hash(txid)
            index=_integer(item['spent_output_index'],'spent output index');key=(txid,index)
            if key in prevouts:raise ValueError('duplicate spent prevout')
            normalized.append({'txid':txid,'vout':index});prevouts[key]=_output(item)
    return {'transaction':{'id':row['hash'],'coinbase':row['is_coinbase'],'inputs':normalized,'outputs':[_output(item) for item in outputs]},
            'prevouts':prevouts,'timestamp':timestamp.isoformat().replace('+00:00','Z'),
            'source_hash':source_hash,'chain_position':position,'block_hash':row['block_hash'],
            'precision_policy':precision_policy,'timestamp_policy':'source-declared UTC; historical publication unverified'}


def decode_parquet(manifest,*,precision_policy,batch_size=4096):
    """Stream a complete hash-bound object, with exact declared count/date checks.

    No empirical runner is authorized by calling this library function. Missing
    transaction position is unavailable, not synthesized from file order.
    """
    import pyarrow.parquet as pq
    if type(batch_size) is not int or not 0<batch_size<=4096:raise ValueError('decoder batch bound')
    if manifest['status']!='complete':raise ValueError('unavailable source object')
    path=Path(manifest['path']);sha=manifest['sha256'];require_hash(sha)
    if file_hash(path)!=sha:raise ValueError('source body hash differs')
    count=0
    with path.open('rb') as stream:
        parquet=pq.ParquetFile(stream)
        if parquet.metadata.num_rows!=manifest['expected_rows']:raise ValueError('source declared row count differs')
        if not set(REQUIRED)<=set(parquet.schema_arrow.names):raise ValueError('required BTC source fields missing')
        for batch in parquet.iter_batches(batch_size=batch_size,columns=list(REQUIRED),use_threads=False):
            for row in batch.to_pylist():
                yield normalize_btc_row(row,source_hash=sha,expected_day=manifest['date'],precision_policy=precision_policy)
                count+=1
    if count!=manifest['expected_rows'] or file_hash(path)!=sha:raise ValueError('source rows/hash changed during decoding')
