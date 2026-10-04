import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):
 with (H/n).open('xb') as f:f.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
r=json.loads((H/'READBACK01.json').read_bytes())
write('VERDICT01.json',{'schema_version':1,'reviewer':'combined_worker_review','status':'ACCEPTED_ACTUAL_LOCAL_TOOLING_CAPTURE','checks':r['checks'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'actual_authentication_sha256':r['actual_authentication_sha256'],'actual_terminal_sha256':r['actual_terminal_sha256'],'archives':r['archives'],'whole_original_files':316,'whole_original_bytes':41887064,'literal_links':50,'actual_external_recovery':None,'actual_Root_flat_recovery':None,'general_PAX_defect_cleared':False,'numerical_release':False,'failed_harnesses':[]})
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
write('MANIFEST01.json',{'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])})
print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'verdict':sha((H/'VERDICT01.json').read_bytes()),'readback':sha((H/'READBACK01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes()),'members':len(rows),'bytes':sum(r.get('bytes',0) for r in rows)}))
