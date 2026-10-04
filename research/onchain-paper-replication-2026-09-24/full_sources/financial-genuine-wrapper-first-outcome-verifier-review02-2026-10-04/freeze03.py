from pathlib import Path
import hashlib,json,os,stat
D=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(D/'MANIFEST02.json')=='a2c8e341b1d2226e8eacbb97e8873639a9d009ab4f8bfe37e5837e37388ef23f'
rows=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST03.json':continue
 s=p.lstat();r={'path':p.relative_to(D).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=sha(p))
 elif stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(type='symlink',target=os.readlink(p))
 else:raise ValueError(str(p))
 rows.append(r)
m={'schema_version':1,'status':'WITHHELD_VF2','scope':'complete additive review including immutable MANIFEST02 and explicit fixed-old-binding limitation; excludes only exact root MANIFEST03.json','entries':rows,'members':len(rows),'regular_files':sum(r['type']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows),'prior_review_manifest02_sha256':sha(D/'MANIFEST02.json'),'binding_limitation_sha256':sha(D/'BINDING_LIMITATION03.json'),'authority':None}
(D/'MANIFEST03.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n');print(json.dumps({'manifest03':sha(D/'MANIFEST03.json'),'binding':sha(D/'BINDING_LIMITATION03.json'),'members':m['members'],'files':m['regular_files'],'bytes':m['regular_bytes']}))
