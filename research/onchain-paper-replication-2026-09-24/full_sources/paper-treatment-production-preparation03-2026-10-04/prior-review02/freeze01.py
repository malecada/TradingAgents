from pathlib import Path
import hashlib,json,stat
D=Path(__file__).resolve().parent
rows=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(D)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 else:raise ValueError('unexpected member')
 rows.append(r)
out={'schema_version':1,'decision':'WITHHELD_TP3_NULL_REGISTERED_INPUT_HASH','scope':'complete review tree except only exact root MANIFEST01.json','entries':rows}
(D/'MANIFEST01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'members':len(rows),'files':sum(r['type']=='file' for r in rows),'manifest_sha256':hashlib.sha256((D/'MANIFEST01.json').read_bytes()).hexdigest(),'review_sha256':hashlib.sha256((D/'REVIEW02.json').read_bytes()).hexdigest(),'witness_sha256':hashlib.sha256((D/'TP3_WITNESS01.json').read_bytes()).hexdigest()}))
