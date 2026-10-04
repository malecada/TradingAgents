import ast,hashlib,json,os,stat
from pathlib import Path
D=Path(__file__).resolve().parent;rows=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(D)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,nlink=s.st_nlink,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 else:raise ValueError('unsupported member')
 rows.append(r)
for p in D.glob('*.py'):ast.parse(p.read_bytes())
(D/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'scope':'complete candidate and retained opaque controls; excludes only exact root MANIFEST01.json','status':'DRAFT_NOT_RELEASED','entries':rows},indent=2,sort_keys=True)+'\n')
print(json.dumps({'manifest_sha256':hashlib.sha256((D/'MANIFEST01.json').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((D/'chunk_archive01.py').read_bytes()).hexdigest(),'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'bytes':sum(r.get('bytes',0) for r in rows)}))
