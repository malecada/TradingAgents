"""Bounded external recovery of already-published metadata, never a market capture."""
from pathlib import Path
import concurrent.futures,hashlib,json,os,signal,sys
from urllib.request import Request,build_opener,ProxyHandler,HTTPRedirectHandler
from datetime import datetime,timezone
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.onchain_replication.resources import assert_guarded_worker
from tradingagents.research.onchain_replication.provenance import durable_mkdir,sync_directory,file_hash

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
GUARD=HERE/'preparation-recovery-02-guard'

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def main():
    assert_guarded_worker(GUARD,sys.orig_argv,required_paths=[ROOT],wall_seconds=900,
        memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2)
    contract=json.loads((HERE/'preparation-recovery-02-contract.json').read_bytes())
    members=contract['members'];total=sum(v['bytes'] for v in members.values())
    if total>contract['maximum_total_bytes'] or any(not 0<=v['bytes']<=contract['maximum_member_bytes'] for v in members.values()):raise ValueError('declared recovery byte bound')
    output=Path(contract['output']);output.mkdir(exist_ok=False);sync_directory(output.parent)
    _immutable(output/'intent.json',{'contract_sha256':file_hash(HERE/'preparation-recovery-02-contract.json'),'started_at':datetime.now(timezone.utc).isoformat()})
    def fetch(item):
        name,info=item
        if Path(name).is_absolute() or '..' in Path(name).parts or not name.startswith(('research/onchain-paper-replication-2026-09-24/','tradingagents/research/onchain_replication/','tests/research/onchain_replication/')):raise ValueError('unregistered recovery member')
        url='https://raw.githubusercontent.com/'+contract['repository']+'/'+contract['commit']+'/'+name
        result={'path':name,'url':url,'status':'failed','started_at':datetime.now(timezone.utc).isoformat()}
        target=output/name;durable_mkdir(target.parent)
        try:
            request=Request(url,headers={'User-Agent':'ReplicationEvidenceRecovery/1.0'})
            with build_opener(ProxyHandler({}),NoRedirect()).open(request,timeout=contract['timeout_seconds']) as response:
                body=response.read(info['bytes']+1);result['http_status']=response.status
                with target.open('xb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
                result.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
                if response.status!=200 or len(body)!=info['bytes'] or result['sha256']!=info['sha256']:raise ValueError('remote response differs from committed member')
                result['status']='complete'
        except Exception as error:result['reason']=type(error).__name__+': '+str(error)
        result['ended_at']=datetime.now(timezone.utc).isoformat();return result
    results=[];pending=iter(sorted(members.items()));stopping=False
    with concurrent.futures.ThreadPoolExecutor(max_workers=contract['workers']) as pool:
        live={pool.submit(fetch,item) for item in [next(pending) for _ in range(min(contract['workers'],len(members)))]}
        while live:
            done,live=concurrent.futures.wait(live,return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                record=future.result();_immutable(output/f'receipt-{len(results):04d}.json',record);results.append(record)
                stopping|=record['status']!='complete'
                if not stopping:
                    item=next(pending,None)
                    if item is not None:live.add(pool.submit(fetch,item))
    seen={x['path'] for x in results}
    results.extend({'path':name,'status':'unavailable','reason':'stopped after bounded retrieval failure; no retry'} for name in members if name not in seen)
    status='complete' if all(x['status']=='complete' for x in results) else 'failed'
    record={'status':status,'commit':contract['commit'],'verified_members':sum(x['status']=='complete' for x in results),
        'required_members':len(members),'verified_bytes':sum(x.get('bytes',0) for x in results if x['status']=='complete'),
        'output':str(output),'results':results,'qualification':'reviewed preparation snapshot only; no active-pilot transaction-body or empirical-model backup claim'}
    _immutable(output/'result.json',record);_immutable(HERE/('preparation-recovery-02-'+status+'.json'),record)
    print(json.dumps({k:v for k,v in record.items() if k!='results'}),flush=True)
    return 0 if status=='complete' else 1

if __name__=='__main__':raise SystemExit(main())
