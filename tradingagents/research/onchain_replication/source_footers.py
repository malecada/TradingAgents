"""Bounded public Parquet metadata sampling, never transaction page acquisition."""
import base64
from datetime import datetime,timezone
import io
import json
from pathlib import Path
from urllib.parse import quote
from ..lifecycle import ResearchRun,_immutable
from .provenance import digest,durable_mkdir,sync_directory
from .source_inventory import HOST,FIELDS,http_transport

POLICY={'selection':'first_key,largest_object_bytes_tie_key,last_key;deduplicate',
        'maximum_objects_per_asset_year':3,'maximum_footer_bytes':2*1024**2,
        'range_requests_per_object':2,'retry':False,'decode_transaction_pages':False}


def select_objects(catalogue):
    if not catalogue['listing_complete']:return ()
    objects=sorted((x for day in catalogue['dates'].values() for x in day['objects']),key=lambda x:x['key'])
    if not objects:return ()
    selected=(objects[0],min(objects,key=lambda x:(-x['bytes'],x['key'])),objects[-1])
    return tuple({x['key']:x for x in selected}.values())


def footer_summary(footer,trailer,asset):
    if len(trailer)!=8 or trailer[4:]!=b'PAR1' or int.from_bytes(trailer[:4],'little')!=len(footer):raise ValueError('invalid Parquet footer framing')
    import pyarrow.parquet as pq
    metadata=pq.read_metadata(io.BytesIO(b'PAR1'+footer+trailer))
    columns={};types={}
    for group in range(metadata.num_row_groups):
        rg=metadata.row_group(group)
        for index in range(rg.num_columns):
            c=rg.column(index);name=c.path_in_schema
            columns[name]=columns.get(name,0)+c.total_compressed_size
            types[name]=c.physical_type
    # Canonical nested list tokens only; actual physical paths remain retained.
    normalized={name.replace('.list.element.','.').replace('.list.item.','.'):name for name in columns}
    return {'rows':metadata.num_rows,'row_groups':metadata.num_row_groups,'schema':str(metadata.schema),
            'column_compressed_bytes':columns,'physical_types':types,
            'required_fields':{name:{'status':'metadata_present' if name in normalized else 'unavailable',
                'physical_path':normalized.get(name)} for name in FIELDS[asset]},
            'transaction_data_admitted':False,'qualification':'sampled current metadata only; no complete daily schema, canonical-chain, historical-vintage or value verification'}


def capture_footer(run,asset,year,item,*,directory,catalogue_sha256,transport=http_transport):
    if not isinstance(run,ResearchRun):raise ValueError('admitted source run required')
    run._active();run._check_source()
    if json.loads(run.read_input('footer_policy'))!=POLICY:raise ValueError('footer policy differs')
    directory=Path(directory).resolve()
    parent=run.admission.root/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/run.admission.experiment_id/(asset+'-'+str(year))
    catalogue_bytes=(parent/'catalogue.json').read_bytes()
    if digest(catalogue_bytes)!=catalogue_sha256:raise ValueError('producer catalogue hash differs')
    catalogue=json.loads(catalogue_bytes)
    if item not in select_objects(catalogue):raise ValueError('object is not in deterministic catalogue sample')
    if directory!=(parent/'footers'/digest(item['key'].encode())).resolve():raise ValueError('footer output identity differs')
    durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    size=item['bytes'];received=0
    def request(name,start,end):
        nonlocal received
        run._active();run._check_source()
        headers={'Range':f'bytes={start}-{end}','If-Match':item['etag']}
        url=HOST+quote(item['key'],safe='/=')
        _immutable(directory/(name+'-intent.json'),{'url':url,'headers':headers,'maximum_bytes':end-start+1,'requested_at':datetime.now(timezone.utc).isoformat(),'retry':False,'source_commit':run.admission.source})
        status,response_headers,body=transport(url,headers,end-start+1);received+=len(body)
        _immutable(directory/(name+'-response.json'),{'status':status,'headers':response_headers,'body_base64':base64.b64encode(body).decode(),'sha256':digest(body),'bytes':len(body),'retrieved_at':datetime.now(timezone.utc).isoformat()})
        lower={k.lower():v for k,v in response_headers.items()}
        if status!=206 or lower.get('content-range')!=f'bytes {start}-{end}/{size}' or len(body)!=end-start+1:raise ValueError('range response does not match registered object extent')
        if lower.get('etag')!=item['etag']:raise ValueError('source ETag changed')
        return body
    result={'asset':asset,'year':year,'object':item,'status':'unavailable','transaction_data_admitted':False}
    try:
        tail=request('trailer',size-8,size-1)
        length=int.from_bytes(tail[:4],'little')
        if tail[4:]!=b'PAR1' or not 0<length<=POLICY['maximum_footer_bytes'] or length>size-12:raise ValueError('footer framing/byte limit')
        footer=request('footer',size-8-length,size-9)
        result.update(status='complete',footer_sha256=digest(footer),summary=footer_summary(footer,tail,asset))
    except Exception as error:result['reason']=type(error).__name__+': '+str(error)
    result['received_bytes']=received
    _immutable(directory/'result.json',result)
    return result
