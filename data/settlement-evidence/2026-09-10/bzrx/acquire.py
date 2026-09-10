"""Serial public documentary retrieval; exact bytes and failures retained."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
LIMIT=25_000_000

def now(): return datetime.now(timezone.utc).isoformat()
def sha(body): return hashlib.sha256(body).hexdigest()

def fetch(name,url,purpose):
    manifest_path=ROOT/'manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        'gate':'audit_settlement_evidence_2026_09_10','registration_commit':'506373e',
        'scope':'BZRXUSDT settlement evidence only; no financial evaluation',
        'quota_bytes':LIMIT,'requests':[],'raw_originals_modified':False,
        'acquisition_script_sha256':sha(Path(__file__).read_bytes()),
        'request_policy':'Serial unauthenticated GET, 30 second timeout; one attempt per distinct route; HTTP429 stops that route.'}
    if any(r['name']==name for r in manifest['requests']): raise RuntimeError('receipt name already exists')
    used=sum(r['bytes'] for r in manifest['requests'])
    if used>=LIMIT: raise RuntimeError('quota exhausted')
    started=now();status=None;headers={};body=bytearray();error=None;final_url=url
    try:
        query=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 settlement-evidence-audit/2026-09-10','Accept-Encoding':'identity'})
        try: response=urllib.request.urlopen(query,timeout=30)
        except urllib.error.HTTPError as exc: response=exc
        with response:
            status=response.status;headers=dict(response.headers);final_url=response.geturl()
            while len(body)<LIMIT-used:
                chunk=response.read(min(65536,LIMIT-used-len(body)))
                if not chunk:break
                body.extend(chunk)
            length=headers.get('Content-Length')
            if length and length.isdigit() and len(body)!=int(length):error='truncated body or quota reached'
    except Exception as exc: error=type(exc).__name__+': '+str(exc)
    target=ROOT/(name+'.bin')
    with target.open('xb') as out:out.write(body)
    row={'name':name,'url':url,'parameters':urllib.parse.parse_qs(urllib.parse.urlsplit(url).query),
         'final_url':final_url,'method':'GET','authenticated':False,'request_started_utc':started,
         'retrieved_utc':now(),'status':status,'headers':headers,'bytes':len(body),'sha256':sha(body),
         'body_file':target.name,'purpose':purpose,'error':error}
    (ROOT/(name+'.receipt.json')).write_text(json.dumps(row,indent=2)+'\n')
    manifest['requests'].append(row);manifest['downloaded_bytes']=used+len(body)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:row[k] for k in ['name','status','bytes','sha256','error']}))

if __name__=='__main__':fetch(*sys.argv[1:])
