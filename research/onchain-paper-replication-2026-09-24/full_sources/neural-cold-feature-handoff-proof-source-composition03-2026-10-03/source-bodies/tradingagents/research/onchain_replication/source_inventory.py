"""Finite unsigned public-source inventory. Capture requires an admitted run.

No transaction-column body is decoded and no missing date is filled. Metadata
coverage is deliberately separate from admitted transaction and price coverage.
"""
from datetime import date,timedelta,datetime,timezone
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request,build_opener,ProxyHandler,HTTPRedirectHandler
from urllib.error import HTTPError
import xml.etree.ElementTree as ET
from ..lifecycle import ResearchRun,_immutable
from .provenance import digest,durable_mkdir,sync_directory

HOST='https://aws-public-blockchain.s3.us-east-2.amazonaws.com/'
FIELDS={
 'ETH':('hash','block_hash','block_number','block_timestamp','transaction_index','from_address','to_address','value','receipt_status'),
 'BTC':('hash','block_hash','block_number','block_timestamp','is_coinbase','input_count','output_count','inputs.index','inputs.spent_transaction_hash','inputs.spent_output_index','inputs.address','inputs.value','outputs.index','outputs.address','outputs.value')}


def required_dates(year):
    if year not in range(2016,2025):raise ValueError('unregistered source year')
    day=date(year,1,1);end=date(year+1,1,1);out=[]
    while day<end:out.append(day.isoformat());day+=timedelta(days=1)
    return tuple(out)


def required_cells(asset,year):
    if asset not in FIELDS:raise ValueError('unregistered asset')
    return tuple({'id':asset+'-'+d+'-'+field,'asset':asset,'date':d,'field':field,'status':'unavailable','reason':'metadata/source admission pending'} for d in required_dates(year) for field in (*FIELDS[asset],'price.Close'))


def parse_listing(body,asset,year):
    """Parse bounded public XML; reject duplicate, foreign and undated members."""
    if len(body)>4*1024**2:raise ValueError('listing byte bound')
    if asset not in FIELDS:raise ValueError('asset')
    allowed=set(required_dates(year));root=ET.fromstring(body);ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
    out=[];seen=set()
    for item in root.findall('s:Contents',ns):
        key=item.findtext('s:Key',namespaces=ns);match=re.fullmatch(r'v1\.0/'+asset.lower()+r'/transactions/date=(\d{4}-\d{2}-\d{2})/[^/]+\.parquet',key or '')
        if not match or match[1] not in allowed:raise ValueError('foreign/undated source object')
        if key in seen:raise ValueError('duplicate source object')
        seen.add(key);size=int(item.findtext('s:Size',namespaces=ns));etag=item.findtext('s:ETag',namespaces=ns)
        if size<12 or not etag:raise ValueError('invalid object metadata')
        out.append({'key':key,'date':match[1],'bytes':size,'etag':etag,'last_modified':item.findtext('s:LastModified',namespaces=ns)})
    truncated=root.findtext('s:IsTruncated',namespaces=ns)
    if truncated not in ('true','false'):raise ValueError('missing pagination state')
    token=root.findtext('s:NextContinuationToken',namespaces=ns)
    if (truncated=='true')!=bool(token):raise ValueError('invalid continuation token')
    return out,token


def catalogue_summary(asset,year,objects,complete):
    days=required_dates(year);group={d:[] for d in days}
    if len({x['key'] for x in objects})!=len(objects):raise ValueError('duplicate object across pages')
    for item in objects:
        if item['date'] not in group:raise ValueError('foreign source date')
        group[item['date']].append(item)
    return {'asset':asset,'year':year,'listing_complete':bool(complete),'required_dates':len(days),'listed_dates':sum(bool(v) for v in group.values()),'listed_object_bytes':sum(x['bytes'] for x in objects),'dates':{d:{'objects':v,'status':'metadata_only' if complete and v else 'unavailable','reason':'transaction columns not yet hash-verified or decoded' if v else 'no listed member; not imputed'} for d,v in group.items()},'transaction_data_admitted':False}


def http_transport(url,headers,limit):
    if not url.startswith(HOST):raise ValueError('unregistered source host')
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    request=Request(url,headers=headers)
    try:response=build_opener(ProxyHandler({}),NoRedirect()).open(request,timeout=30)
    except HTTPError as error:response=error
    with response:
        if not response.geturl().startswith(HOST):raise ValueError('unexpected source redirect')
        body=response.read(limit+1)
        return response.status,dict(response.headers),body


def capture_catalogue(run,asset,year,*,output_directory,transport=http_transport,max_pages=8,max_bytes=32*1024**2,source_policy_input='source_policy'):
    if type(max_pages) is not int or not 1<=max_pages<=8 or type(max_bytes) is not int or not 0<max_bytes<=32*1024**2:raise ValueError('source capture bounds')
    if not isinstance(run,ResearchRun):raise ValueError('admitted source run required')
    run._active();run._check_source()
    policy=json.loads(run.read_input(source_policy_input))
    expected={'asset':asset,'year':year,'host':HOST,'max_pages':max_pages,'max_bytes':max_bytes,'kind':'unsigned_listing_only'}
    if policy!=expected:raise ValueError('source policy differs from registered limits')
    directory=Path(output_directory).resolve();allowed=run.admission.root/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/run.admission.experiment_id
    if source_policy_input!='source_policy':allowed=allowed/(asset+'-'+str(year))
    if directory!=allowed.resolve():raise ValueError('source output root differs')
    durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    objects=[];token=None;used=0;tokens=set();reason=None;complete=False
    for page in range(max_pages):
        run._active();run._check_source();params={'list-type':'2','prefix':f'v1.0/{asset.lower()}/transactions/date={year}-','max-keys':'1000'}
        if token is not None:params['continuation-token']=token
        url=HOST+'?'+urlencode(params);limit=min(4*1024**2,max_bytes-used)
        if limit<=0:reason='registered byte budget exhausted';break
        _immutable(directory/f'intent-{page:02d}.json',{'url':url,'max_response_bytes':limit,'retry':False,'requested_at':datetime.now(timezone.utc).isoformat(),'source_commit':run.admission.source})
        try:
            status,headers,body=transport(url,{},limit);used+=len(body)
            # Preserve failed/over-limit response bytes, without admitting them.
            import base64
            _immutable(directory/f'response-{page:02d}.json',{'status':status,'headers':headers,'body_base64':base64.b64encode(body).decode(),'sha256':digest(body),'bytes':len(body),'retrieved_at':datetime.now(timezone.utc).isoformat()})
            if len(body)>limit:raise ValueError('response byte limit exceeded')
            if status!=200:raise ValueError('source HTTP status '+str(status))
            members,next_token=parse_listing(body,asset,year)
            if {x['key'] for x in objects}&{x['key'] for x in members}:raise ValueError('duplicate object across pages')
            objects.extend(members)
            if next_token is None:complete=True;break
            if next_token in tokens:raise ValueError('repeated pagination token')
            tokens.add(next_token);token=next_token
        except Exception as error:reason=type(error).__name__+': '+str(error);break
    if not complete and reason is None:reason='registered page budget exhausted'
    result=catalogue_summary(asset,year,objects,complete);result.update(reason=reason,received_bytes=used)
    _immutable(directory/'catalogue.json',result)
    return result
