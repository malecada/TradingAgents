"""Exact selected-column byte plans; no network or empirical admission here.

All selected column chunks and every row group are retained. The full footer is
required to decode nested Arrow types. Unselected data-page ranges stay holes;
the acquired reader rejects their use. Logical object size is not disk usage.
"""
import io
import json
from pathlib import Path
from .provenance import digest,file_hash

BTC_FIELDS=('hash','block_hash','block_number','block_timestamp','index','is_coinbase',
    'input_count','output_count','inputs.index','inputs.spent_transaction_hash',
    'inputs.spent_output_index','inputs.address','inputs.value',
    'outputs.index','outputs.address','outputs.value')
ETH_FIELDS=('hash','block_hash','block_number','block_timestamp','transaction_index',
    'from_address','to_address','value','receipt_status')


def normalized_column(name):
    return name.replace('.list.element.','.').replace('.list.item.','.')


def plan_ranges(footer,trailer,size,asset,*,maximum_span_bytes=64*1024**2):
    import pyarrow.parquet as pq
    if asset not in ('BTC','ETH'):raise ValueError('unsupported source asset')
    if type(size) is not int or not 12<=size<=8*1024**3:raise ValueError('logical object size bound')
    if type(maximum_span_bytes) is not int or not 1<=maximum_span_bytes<=64*1024**2:raise ValueError('range byte bound')
    if len(trailer)!=8 or trailer[4:]!=b'PAR1' or int.from_bytes(trailer[:4],'little')!=len(footer) or not 0<len(footer)<=2*1024**2 or len(footer)>size-12:raise ValueError('footer framing/size differs')
    metadata=pq.read_metadata(io.BytesIO(b'PAR1'+footer+trailer))
    required=BTC_FIELDS if asset=='BTC' else ETH_FIELDS
    physical={}
    for i in range(len(metadata.schema)):
        path=metadata.schema.column(i).path;name=normalized_column(path)
        if name in physical:raise ValueError('ambiguous normalized column')
        physical[name]=path
    if not set(required)<=set(physical):raise ValueError('required source leaves missing')
    chosen={physical[x] for x in required};footer_start=size-8-len(footer)
    chunks=[];rows=0
    for group in range(metadata.num_row_groups):
        rg=metadata.row_group(group);rows+=rg.num_rows;seen=set()
        for i in range(rg.num_columns):
            c=rg.column(i)
            if c.path_in_schema not in chosen:continue
            if c.file_path:raise ValueError('external column file path is not admitted')
            if c.path_in_schema in seen:raise ValueError('duplicate row-group leaf')
            seen.add(c.path_in_schema)
            starts=[x for x in (c.dictionary_page_offset,c.data_page_offset) if x is not None and x>0]
            if not starts or c.total_compressed_size<=0:raise ValueError('invalid column extent')
            a=min(starts);b=a+c.total_compressed_size
            if not 4<=a<b<=footer_start:raise ValueError('column extent outside object body')
            chunks.append({'row_group':group,'column':c.path_in_schema,'start':a,'end':b})
        if seen!=chosen:raise ValueError('row-group required leaf coverage differs')
    if rows!=metadata.num_rows or not chunks:raise ValueError('empty/inconsistent row-group population')
    intervals=sorted((x['start'],x['end']) for x in chunks)
    if any(a<prior_b for (_,prior_b),(a,_) in zip(intervals,intervals[1:])):raise ValueError('overlapping column extents')
    intervals=[(0,4),*intervals,(footer_start,size)]
    merged=[]
    for a,b in intervals:
        if merged and a==merged[-1][1]:merged[-1]=(merged[-1][0],b)
        else:merged.append((a,b))
    spans=[{'start':a,'end':min(a+maximum_span_bytes,b)} for start,b in merged for a in range(start,b,maximum_span_bytes)]
    return {'schema_version':1,'asset':asset,'size':size,'rows':rows,'row_groups':metadata.num_row_groups,
        'footer_sha256':digest(footer),'trailer_sha256':digest(trailer),
        'required_fields':list(required),'physical_columns':{x:physical[x] for x in required},
        'chunks':chunks,'spans':spans,'selected_bytes':sum(x['end']-x['start'] for x in spans),
        'maximum_span_bytes':maximum_span_bytes,'transaction_data_admitted':False}


def decode_projected_btc(manifest,*,scratch,precision_policy,batch_size=4096):
    """Decode all retained BTC rows using only the admitted required leaf paths."""
    import pyarrow.parquet as pq
    from .btc_source import normalize_btc_row
    from .eth_source import projected_parquet
    if type(batch_size) is not int or not 0<batch_size<=4096:raise ValueError('decoder batch bound')
    if manifest['status']!='complete':raise ValueError('unavailable source object')
    path=Path(manifest['path']);body=path.read_bytes()
    if digest(body)!=manifest['sha256']:raise ValueError('projected manifest hash differs')
    projected=json.loads(body);plan=projected['column_plan']
    count=0
    with projected_parquet(projected,scratch) as source:
        source.seek(0)
        if source.read(4)!=b'PAR1':raise ValueError('invalid acquired Parquet header')
        source.seek(projected['size']-8);trailer=source.read(8)
        length=int.from_bytes(trailer[:4],'little');source.seek(projected['size']-8-length);footer=source.read(length)
        actual=plan_ranges(footer,trailer,projected['size'],'BTC',maximum_span_bytes=plan['maximum_span_bytes'])
        if actual!=plan:raise ValueError('column plan differs from retained footer')
        if [{'start':s['start'],'end':s['end']} for s in projected['spans']]!=plan['spans']:raise ValueError('retained selected range membership differs')
        if plan['rows']!=manifest['expected_rows']:raise ValueError('source declared row count differs')
        source.seek(0);parquet=pq.ParquetFile(source,metadata=source.parquet_metadata,pre_buffer=False)
        for batch in parquet.iter_batches(batch_size=batch_size,columns=list(plan['physical_columns'].values()),use_threads=False):
            for row in batch.to_pylist():
                yield normalize_btc_row(row,source_hash=manifest['sha256'],expected_day=manifest['date'],precision_policy=precision_policy)
                count+=1
    if count!=manifest['expected_rows'] or file_hash(path)!=manifest['sha256']:raise ValueError('source rows/hash changed during decoding')
