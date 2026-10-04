from pathlib import Path
import os,stat,json,hashlib
D=Path(__file__).resolve().parent;entries=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(D)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(type='symlink',target=os.readlink(p))
 elif stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 else:raise ValueError('unsupported type')
 entries.append(r)
(D/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'decision':'ACCEPTED_SOURCE_ONLY_DA4_CORRECTION','scope':'complete review tree excluding only exact root MANIFEST01.json','entries':entries},indent=2,sort_keys=True)+'\n')
print(json.dumps({'members':len(entries),'files':sum(r['type']=='file' for r in entries),'manifest_sha256':hashlib.sha256((D/'MANIFEST01.json').read_bytes()).hexdigest(),'review_sha256':hashlib.sha256((D/'REVIEW01.json').read_bytes()).hexdigest(),'witness_sha256':hashlib.sha256((D/'WITNESS01.json').read_bytes()).hexdigest()}))
