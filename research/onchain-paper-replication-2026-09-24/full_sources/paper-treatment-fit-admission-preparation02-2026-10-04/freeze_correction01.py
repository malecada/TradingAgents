from pathlib import Path
import hashlib,json,stat
D=Path(__file__).resolve().parent;rows=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST02.json':continue
 s=p.lstat();r={'path':str(p.relative_to(D)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 else:raise ValueError('unexpected member')
 rows.append(r)
out={'schema_version':1,'status':'DRAFT_NOT_RELEASED','scope':'complete successor tree excluding only exact root MANIFEST02.json; original MANIFEST01 retained','entries':rows}
(D/'MANIFEST02.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'members':len(rows),'files':sum(r['type']=='file' for r in rows),'manifest_sha256':hashlib.sha256((D/'MANIFEST02.json').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((D/'overlay/tradingagents/research/onchain_replication/treatment_admission.py').read_bytes()).hexdigest(),'inverse_sha256':hashlib.sha256((D/'CORRECTION_INVERSE01.json').read_bytes()).hexdigest()}))
