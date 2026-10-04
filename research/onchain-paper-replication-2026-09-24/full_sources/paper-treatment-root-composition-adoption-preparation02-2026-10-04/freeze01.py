import hashlib,json,stat
from pathlib import Path
D=Path(__file__).resolve().parent;entries=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(D)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 else:raise ValueError('unexpected source type')
 entries.append(r)
(D/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'status':'DRAFT_SOURCE_COPY_ONLY','scope':'complete owned composition tree excluding only exact root MANIFEST01.json','entries':entries},indent=2,sort_keys=True)+'\n')
print(json.dumps({'members':len(entries),'files':sum(r['type']=='file' for r in entries),'manifest_sha256':hashlib.sha256((D/'MANIFEST01.json').read_bytes()).hexdigest(),'closure_sha256':hashlib.sha256((D/'CLOSURE01.json').read_bytes()).hexdigest(),'recipe_sha256':hashlib.sha256((D/'recipe01.py').read_bytes()).hexdigest(),'candidate_admission_sha256':hashlib.sha256((D/'candidate/tradingagents/research/onchain_replication/treatment_admission.py').read_bytes()).hexdigest()}))
