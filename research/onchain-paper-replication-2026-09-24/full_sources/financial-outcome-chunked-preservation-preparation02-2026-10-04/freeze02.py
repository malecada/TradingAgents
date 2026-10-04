from pathlib import Path
import hashlib,json,stat,os,ast
D=Path(__file__).resolve().parent;B=D.parent;entries=[]
origins=[]
for rel in ('financial-outcome-chunked-preservation-preparation01-2026-10-04/MANIFEST01.json','financial-outcome-chunked-preservation-review01-2026-10-04/MANIFEST01.json','financial-outcome-chunked-preservation-review01-2026-10-04/REVIEW01.json'):
 p=B/rel;origins.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'preserved original actual body, not copied whole evidence tree'})
(D/'ORIGINS02.json').write_text(json.dumps(origins,indent=2)+'\n')
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST02.json':continue
 s=p.lstat();r={'path':str(p.relative_to(D)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(type='symlink',target=os.readlink(p))
 elif stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,nlink=s.st_nlink,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 else:raise ValueError('unsupported retained type')
 entries.append(r)
for p in D.glob('*.py'):ast.parse(p.read_bytes())
(D/'MANIFEST02.json').write_text(json.dumps({'schema_version':1,'status':'DRAFT_NOT_RELEASED','scope':'complete new candidate/control tree excluding only exact root MANIFEST02.json','entries':entries},indent=2,sort_keys=True)+'\n')
print(json.dumps({'members':len(entries),'files':sum(r['type']=='file' for r in entries),'bytes':sum(r.get('bytes',0) for r in entries),'manifest_sha256':hashlib.sha256((D/'MANIFEST02.json').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((D/'chunk_archive01.py').read_bytes()).hexdigest(),'inverse_sha256':hashlib.sha256((D/'INVERSE03.json').read_bytes()).hexdigest()}))
