"""Finite metadata-only year drafts. This module deliberately cannot release jobs."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import stat
from datetime import date,timedelta
from range_policy_source import range_policy
from owned_io import _cleanup

HERE=Path(__file__).resolve().parent
POPULATION=tuple((a,y) for a,stop in (('BTC',2025),('ETH',2022)) for y in range(2016,stop))
META='research_runs/paper-full-source-metadata-20260924/'
ART='research_artifacts/onchain-paper-replication-2026-09-24/sources/paper-full-source-metadata-20260924/'
LIMIT_KEYS={'maximum_span_bytes','max_requests','max_received_bytes','max_blob_bytes'}
MISSING=('independently reviewed cumulative and categorical source allowance, including all current spent claims',
 'committed fresh experiment identity, charter/gate/source closure/runtime/environment and exact native policy',
 'whole writable namespace/storage/receipt/scratch/failure and archive/recovery bounds with >=10GiB local floor',
 'actual verified external preservation protocol and original-to-restored recovery mapping',
 'fresh native eligibility/dedup and genuine job admission; no claim resume or implicit daily subdivision')

class ReleaseUnavailable(ValueError):pass

def require_execution_release(value):
    # There is no established typed cumulative/native/preservation release contract
    # for these years. A mapping containing approval flags is never authority.
    raise ReleaseUnavailable('; '.join(MISSING))

def _need(ok,why):
    if not ok:raise ValueError(why)

def _sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def read_pinned(root,ref):
    _need(type(ref) is dict and set(ref)=={'path','bytes','sha256'},'exact metadata ref')
    name=ref['path'];n=ref['bytes'];h=ref['sha256']
    _need(type(name) is str and 0<len(name)<=2048,'path bound')
    p=PurePosixPath(name)
    _need(not p.is_absolute() and str(p)==name and len(p.parts)<=32 and all(x not in ('.','..','','keys','apis','.env','hf_token.txt') and not x.endswith(('.pem','.key')) for x in p.parts),'unsafe metadata path')
    _need(type(n) is int and 0<n<=4*1024**2 and type(h) is str and re.fullmatch('[0-9a-f]{64}',h),'metadata bound/hash')
    fds=[]
    try:
        fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(fd)
        for part in p.parts[:-1]:
            fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);fds.append(fd)
        parent=fd
        fd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent);fds.append(fd)
        before=os.fstat(fd);_need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==n,'metadata regular single-link length')
        chunks=[];left=n+1
        while left:
            block=os.read(fd,min(left,65536))
            if not block:break
            chunks.append(block);left-=len(block)
        raw=b''.join(chunks)
        _need(len(raw)==n and hashlib.sha256(raw).hexdigest()==h,'metadata body hash')
        _need(_sig(before)==_sig(os.fstat(fd))==_sig(os.stat(p.name,dir_fd=parent,follow_symlinks=False)),'metadata inode changed')
        # Rejoin each acquired directory by descriptor-relative original spelling.
        _need(os.stat(root,follow_symlinks=False).st_ino==os.fstat(fds[0]).st_ino and os.stat(root,follow_symlinks=False).st_dev==os.fstat(fds[0]).st_dev,'root changed')
        for i,part in enumerate(p.parts[:-1]):
            s=os.stat(part,dir_fd=fds[i],follow_symlinks=False);t=os.fstat(fds[i+1]);_need(stat.S_ISDIR(s.st_mode) and (s.st_dev,s.st_ino)==(t.st_dev,t.st_ino),'parent changed')
        return raw
    finally:_cleanup(tuple(lambda f=f:os.close(f) for f in reversed(fds)))

def year_dates(year):
    _need(type(year) is int and 2016<=year<=2024,'calendar year')
    day=date(year,1,1);end=date(year+1,1,1);result=[]
    while day<end:result.append(day.isoformat());day+=timedelta(days=1)
    return result

def catalogue_scope(c,asset,year):
    _need((asset,year) in POPULATION,'prospective year denominator')
    days=year_dates(year)
    _need(type(c) is dict and c.get('asset')==asset and type(c.get('year')) is int and c['year']==year and c.get('listing_complete') is True and c.get('transaction_data_admitted') is False,'not a complete historical catalogue')
    _need(type(c.get('dates')) is dict and sorted(c['dates'])==days and type(c.get('required_dates')) is int and type(c.get('listed_dates')) is int and c['required_dates']==c['listed_dates']==len(days),'entire year required')
    seen=set();total=0;maximum=0;ordered=[]
    for d in days:
        row=c['dates'][d];_need(type(row) is dict and type(row.get('objects')) is list and len(row['objects'])<=128,'daily object bound')
        for o in sorted(row['objects'],key=lambda x:x['key']):
            _need(type(o) is dict and o.get('date')==d and type(o.get('key')) is str and re.fullmatch(r'v1\.0/'+asset.lower()+r'/transactions/date='+d+r'/[A-Za-z0-9_.-]+\.parquet',o['key']),'object scope')
            _need(o['key'] not in seen and type(o.get('bytes')) is int and 12<=o['bytes']<=8*1024**3 and type(o.get('etag')) is str and re.fullmatch(r'"[A-Za-z0-9-]+"',o['etag']),'object uniqueness/extent/ETag')
            seen.add(o['key']);total+=o['bytes'];maximum=max(maximum,o['bytes']);ordered.append({'date':d,'key':o['key'],'etag':o['etag'],'bytes':o['bytes']})
    _need(type(c.get('listed_object_bytes')) is int and c['listed_object_bytes']==total,'catalogue byte sum')
    return {'dates':days,'objects':len(seen),'ordered_objects':ordered,'listed_complete_object_bytes':total,'maximum_object_bytes':maximum,'selected_column_bytes':None,'current_etag_available':None,'transaction_data_admitted':False}

def policy_draft(asset,year,input_name,caps):
    _need((asset,year) in POPULATION,'prospective year denominator')
    _need(type(input_name) is str and re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,63}',input_name),'registered input name')
    if caps is None:return None
    _need(type(caps) is dict and set(caps)==LIMIT_KEYS,'all four explicit source caps required')
    return range_policy(asset,year_dates(year),{str(year):input_name},**caps)

def prepare(root,caps_by_year=None):
    """Read exact preserved metadata; return unregistered drafts, never run/admit."""
    pins=json.loads((HERE/'source-pins01.json').read_bytes());_need(len(pins['files'])==9,'source pin cardinality')
    bodies={r['path']:read_pinned(root,r) for r in pins['files']}
    doc=lambda path:json.loads(bodies[path])
    claim=doc(META+'claim.json');terminal=doc(META+'complete.json');coverage=doc(META+'outputs/source-coverage.json');index=doc(META+'outputs/artifact-index.json')
    _need(terminal['status']=='complete' and terminal['claim_sha256']==hashlib.sha256(bodies[META+'claim.json']).hexdigest(),'original terminal claim')
    _need(claim['registration_sha256']==hashlib.sha256(bodies[claim['registration']]).hexdigest(),'original registration')
    for name in ('source-coverage.json','artifact-index.json'):_need(terminal['output_sha256'][name]==hashlib.sha256(bodies[META+'outputs/'+name]).hexdigest(),'original output join')
    _need(type(index) is dict and len(index)<=2048 and len(coverage['catalogues'])==18,'historical index scope')
    caps_by_year={} if caps_by_year is None else caps_by_year
    _need(type(caps_by_year) is dict and set(caps_by_year)<=set(a+'-'+str(y) for a,y in POPULATION),'unknown year caps')
    field_tree=ast.parse(bodies['tradingagents/research/onchain_replication/parquet_ranges.py'])
    fields={node.targets[0].id:ast.literal_eval(node.value) for node in field_tree.body if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('BTC_FIELDS','ETH_FIELDS')}
    _need(len(fields['BTC_FIELDS'])==16 and len(fields['ETH_FIELDS'])==9,'selected original field denominator')
    rows=[];readbytes=0
    for asset,year in POPULATION:
        key=f'{asset}-{year}';path=ART+key+'/catalogue.json';ref={'path':path,**index[path]};readbytes+=ref['bytes'];_need(readbytes<=4*1024**2,'all selected catalogues bound')
        raw=read_pinned(root,ref);catalogue=json.loads(raw);_need(catalogue==coverage['catalogues'][key],'original catalogue coverage join')
        receiptpath=ART+key+'-catalogue.json';receipt=json.loads(read_pinned(root,{'path':receiptpath,**index[receiptpath]}))
        _need(receipt['status']=='complete' and receipt['id']==key+'-catalogue' and receipt['catalogue_sha256']==ref['sha256'],'original cell receipt catalogue join')
        scope=catalogue_scope(catalogue,asset,year);input_name=f'catalogue_{asset}_{year}'
        rows.append({'asset_year':key,'scope':scope,'required_physical_leaves':list(fields[asset+'_FIELDS']),'catalogue_input':{'name':input_name,**ref},'cells':[asset+'-'+d for d in scope['dates']],
          'range_policy':policy_draft(asset,year,input_name,caps_by_year.get(key)),
          'execution_job_template':{'schema_version':1,'kind':'ranges','resources':None,'environment_input':None,'payload':{}},
          'output_names':['cell-ledger.json','source-summary.json','artifact-index.json'],
          'experiment_identity':None,'destination_template':'research_artifacts/onchain-paper-replication-2026-09-24/sources/<fresh-root-reviewed-experiment-id>'})
    return {'schema_version':1,'status':'UNREGISTERED_RELEASE_REFUSED','route':'range_policy -> genuine job.execute_source_job(kind=ranges) -> capture_ranges','asset_years':rows,
     'requested_allocation_units':15,'cumulative_ceiling':None,'category_remaining_allowance':None,'identity_allocation':None,'release_blockers':list(MISSING),
     'whole_object_bytes_are_not_capture_bytes':True,'historical_preservation_scope_bytes':103524489043,'historical_preservation_is_not_new_capacity':True,
     'transaction_data_admitted':False,'financial_fits_admitted':False,'fund_cohort_replaced':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);args=parser.parse_args()
    # Printing a bounded draft is the only CLI action. Caller retains bytes.
    result=json.dumps(prepare(args.root),sort_keys=True,indent=2)+'\n';_need(len(result.encode())<=8*1024**2,'draft output bound');print(result,end='')
