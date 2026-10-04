import urllib.request, urllib.error, json, hashlib, datetime, pathlib, sys
D=pathlib.Path(__file__).resolve().parent
url,name=sys.argv[1:]
p=D/name
assert not p.exists() and '/' not in name
meta={'url':url,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'limit_bytes':4194304,'timeout_seconds':20,'method':'GET','authenticated':False}
try:
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Historical-cohort-read-only-audit/1.0'}),timeout=20) as r:
  b=r.read(4194305)
  if len(b)>4194304: raise ValueError('bounded response exceeded')
  meta.update(status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  with p.open('xb') as f:f.write(b)
except Exception as e:meta.update(error_type=type(e).__name__,error=str(e))
with (D/(name+'.receipt.json')).open('x') as f:json.dump(meta,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(meta))
