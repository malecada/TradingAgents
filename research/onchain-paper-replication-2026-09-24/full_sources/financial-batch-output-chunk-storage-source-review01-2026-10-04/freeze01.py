import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();c=json.loads((H/'CHECKS01.json').read_bytes())
v={'schema_version':1,'reviewer':'combined_worker_review','status':'WITHHELD_CS1_CS2_CS3','codec_sha256':'00d06377c4567bd7880dd7ddbf396b613a78968a7317a565f7e034319c9ed4fe','sink_sha256':'2614242ebc8395f859e704db1971dd46172ff8ea9802fb4c77397c80970bdb52','author_manifest_sha256':'1181852868d880e624caf3e4a3982f6bd27301983cc3fe2e7a2a0c92f6e3ef8d','broader_checks':c['checks'],'material_witnesses':3,'witness_sha256':sha((H/'WITNESSES01.json').read_bytes()),'checks_sha256':sha((H/'CHECKS01.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'scaled_allocation_witness_not_actual64MiB':True,'live_or_numerical_authority':None,'source_installed':False,'retained_harness_failure':'CHECK01.err: original manifest symlink spelling mismatch; successor check02 only normalizes that spelling'}
with (H/'VERDICT01.json').open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
rows=[]
def rec(p,rel):
 st=p.lstat();r={'path':rel,'mode':stat.S_IMODE(st.st_mode)}
 if stat.S_ISLNK(st.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
 elif stat.S_ISDIR(st.st_mode):
  r['kind']='directory'
  for x in sorted(p.iterdir()):rec(x,rel+'/'+x.name)
 else:
  assert stat.S_ISREG(st.st_mode);body=p.read_bytes();r.update(kind='file',bytes=len(body),sha256=sha(body))
 rows.append(r)
for p in sorted(H.iterdir()):rec(p,p.name)
with (H/'MANIFEST01.json').open('x') as f:json.dump({'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])},f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'verdict':sha((H/'VERDICT01.json').read_bytes()),'witness':sha((H/'WITNESSES01.json').read_bytes()),'checks':sha((H/'CHECKS01.json').read_bytes()),'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'bytes':sum(r.get('bytes',0) for r in rows)}))
