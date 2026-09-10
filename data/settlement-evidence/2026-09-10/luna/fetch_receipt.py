"""Bounded single-request public evidence receipt under gate506373e; no market replay."""
import argparse,datetime,hashlib,json,pathlib,sys,time
import requests
ROOT=pathlib.Path(__file__).resolve().parent
BUDGET=25_000_000
ap=argparse.ArgumentParser();ap.add_argument('name');ap.add_argument('url');ap.add_argument('--params',default='{}');a=ap.parse_args()
if pathlib.Path(a.name).name!=a.name:raise ValueError('local filename required')
manifest=ROOT/'manifest.json'; state=json.loads(manifest.read_text()) if manifest.exists() else {'experiment':'audit_settlement_evidence_2026_09_10','instrument':'LUNAUSDT','transform_commit':'506373e','request_policy':'one request at a time; timeout30s; one attempt; no authenticated endpoints','budget_bytes':BUDGET,'responses':[]}
if (ROOT/a.name).exists():raise FileExistsError(a.name)
used=sum(x.get('body_bytes',0) for x in state['responses']); remaining=BUDGET-used
params=json.loads(a.params);started=datetime.datetime.now(datetime.timezone.utc).isoformat(); rec={'name':a.name,'requested_url':a.url,'params':params,'request_started_utc':started,'attempt':1}
try:
 r=requests.get(a.url,params=params,timeout=30,stream=True)
 rec.update(final_url=r.url,status=r.status_code,headers={k:v for k,v in r.headers.items() if k.lower() in ['date','content-type','content-length','content-encoding','etag','last-modified','cache-control','memento-datetime','retry-after','x-mbx-used-weight-1m','x-amz-version-id']},redirects=[{'url':h.url,'status':h.status_code,'location':h.headers.get('location')} for h in r.history])
 chunks=[];total=0
 for b in r.iter_content(65536):
  if total+len(b)>remaining:raise RuntimeError('remaining download budget exceeded')
  chunks.append(b);total+=len(b)
 body=b''.join(chunks);r.close()
 with (ROOT/a.name).open('xb') as f:f.write(body)
 rec.update(body_bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),body_file=a.name)
except Exception as e:rec.update(error=type(e).__name__+': '+str(e))
rec['retrieved_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();state['responses'].append(rec);state['total_body_bytes']=sum(x.get('body_bytes',0) for x in state['responses']);manifest.write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(rec));print('total_body_bytes',state['total_body_bytes'])
