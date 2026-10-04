import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
r=json.loads((H/'READBACK01.json').read_bytes())
v={'schema_version':1,'reviewer':'combined_worker_review','status':'ACCEPTED_SOURCE_ONLY','source_sha256':r['source_sha256'],'checks':r['checks'],'prior_checks_not_rerun':54,'predecessor_withheld_manifest':'31439250f852e81c19659327366156deac5a378b2c76ce3a5514c999534d2178','readback_sha256':sha((H/'READBACK01.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'actual_Root_restore':False,'actual_request_release':None,'numeric_authority':False}
with (H/'VERDICT01.json').open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
rows=[]
def rec(p,rel):
 s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):
  r['kind']='directory'
  for c in sorted(p.iterdir()):rec(c,rel+'/'+c.name)
 else:
  assert stat.S_ISREG(s.st_mode);b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
for p in sorted(H.iterdir()):rec(p,p.name)
with (H/'MANIFEST01.json').open('x') as f:json.dump({'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])},f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'verdict':sha((H/'VERDICT01.json').read_bytes()),'readback':sha((H/'READBACK01.json').read_bytes()),'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'bytes':sum(r.get('bytes',0) for r in rows)}))
