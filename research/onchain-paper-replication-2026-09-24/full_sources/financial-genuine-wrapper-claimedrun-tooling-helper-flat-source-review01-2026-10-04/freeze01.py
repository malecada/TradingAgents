import hashlib,json,stat
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
r=json.loads((H/'READBACK01.json').read_bytes())
v={'schema_version':1,'status':'WITHHELD_TF_DESTINATION01','candidate_sha256':r['candidate_sha256'],'checks':r['checks'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'actual_Root_restore':False,'actual_output_reserved':False,'future_actual_remote_receipt':None}
with (H/'VERDICT01.json').open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
rows=[]
def rec(p,rel):
 s=p.lstat();d={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):
  d['kind']='directory'
  for c in sorted(p.iterdir()):rec(c,rel+'/'+c.name)
 else:
  assert stat.S_ISREG(s.st_mode);b=p.read_bytes();d.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(d)
for p in sorted(H.iterdir()):rec(p,p.name)
with (H/'MANIFEST01.json').open('x') as f:json.dump({'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])},f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'verdict':sha((H/'VERDICT01.json').read_bytes()),'readback':sha((H/'READBACK01.json').read_bytes()),'checks':r['checks'],'members':len(rows)}))
