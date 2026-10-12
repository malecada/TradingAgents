"""One authorized local read-only capacity ancestry/body batch; no network."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
ENTRY=HERE.parent/'real-data-pilot-full38-entry-preparation01-2026-10-12'
pins=json.loads((ENTRY/'CAPACITY_SOURCE_MAP01.json').read_bytes());assert len(pins)==428
anchor='1394d8b03163233df2fcefe658378e0f7b13424d';current='0d4b1a9b294a4b0a484fbd2a1d7e27f8257738ec'
ancestry=subprocess.run(['git','merge-base','--is-ancestor',anchor,current],cwd=ROOT,capture_output=True)
(HERE/'CAPACITY_ANCESTRY01.stdout').write_bytes(ancestry.stdout);(HERE/'CAPACITY_ANCESTRY01.stderr').write_bytes(ancestry.stderr)
assert ancestry.returncode==0
queries=[(rev,p) for rev in (anchor,current) for p in sorted(pins)]
request=''.join(rev+':'+p+'\n' for rev,p in queries).encode()
run=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,input=request,capture_output=True)
(HERE/'CAPACITY_GIT_BATCH01.stderr').write_bytes(run.stderr)
assert run.returncode==0
raw=run.stdout;pos=0;rows={}
for rev,path in queries:
    end=raw.index(b'\n',pos);oid,kind,size=raw[pos:end].decode('ascii').split();size=int(size);pos=end+1
    assert kind=='blob';body=raw[pos:pos+size];pos+=size;assert raw[pos:pos+1]==b'\n';pos+=1
    digest=hashlib.sha256(body).hexdigest();assert digest==pins[path]
    assert body==(ROOT/path).read_bytes()
    assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+body).hexdigest()==oid
    rows.setdefault(path,{'sha256':digest,'bytes':size,'git_blob_oids':{}})['git_blob_oids'][rev]=oid
assert pos==len(raw)
result={'decision':'accepted','scope':'Read-only local committed capacity428 body and ancestor join only','anchor':anchor,'current':current,'ancestry_exit_code':ancestry.returncode,'git_batch_exit_code':run.returncode,'request_sha256':hashlib.sha256(request).hexdigest(),'stdout_bytes':len(raw),'stdout_sha256':hashlib.sha256(raw).hexdigest(),'source_paths':428,'git_blob_results':856,'paths':rows,'qualification':'Both actual local commit:path bodies equal current428 pins; one local cat-file batch, no network. Compact parsed Git blob/SHA evidence retained without duplicating856 source bodies. Final binding source and live capacity/namespace eligibility remain separate.'}
print(json.dumps(result,indent=2,sort_keys=True))
