import hashlib,json,stat
from pathlib import Path
P=Path(__file__).resolve().parent
rows=[]
for p in sorted(P.rglob('*')):
 if p.name in ('MANIFEST01.json','MANIFEST01.sha256'):continue
 s=p.lstat();r={'path':str(p.relative_to(P)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 else:raise ValueError('unexpected special file')
 rows.append(r)
raw=(json.dumps({'schema_version':1,'status':'source preparation; genuine execution unperformed','members':rows},sort_keys=True,indent=2)+'\n').encode();(P/'MANIFEST01.json').write_bytes(raw);pin=hashlib.sha256(raw).hexdigest();(P/'MANIFEST01.sha256').write_text(pin+'  MANIFEST01.json\n')
print(json.dumps({'members':len(rows),'manifest_sha256':pin,'source_sha256':hashlib.sha256((P/'financial_wrapper_fixture.py').read_bytes()).hexdigest(),'protocol_sha256':hashlib.sha256((P/'PROTOCOL01.md').read_bytes()).hexdigest()}))
