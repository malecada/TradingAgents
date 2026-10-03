from pathlib import Path
import hashlib,json,stat
D=Path(__file__).resolve().parent
rows=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(D)),'mode':format(stat.S_IMODE(s.st_mode),'04o')}
 if stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 else:raise ValueError('unsupported member')
 rows.append(r)
out={'schema_version':1,'scope':'complete source-only candidate tree excluding only this exact root MANIFEST01.json','status':'DRAFT_NOT_RELEASED','members':rows,'files':sum(r['type']=='file' for r in rows),'directories':sum(r['type']=='directory' for r in rows),'financial_credit':0}
(D/'MANIFEST01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'manifest_sha256':hashlib.sha256((D/'MANIFEST01.json').read_bytes()).hexdigest(),'members':len(rows),'files':out['files'],'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'overlay').rglob('*.py')}},sort_keys=True))
