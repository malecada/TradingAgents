from pathlib import Path
import hashlib,json,stat
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-final-recovery-preparation04-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((A/'MANIFEST04.json').read_bytes())=='7764229f794d10aa61b999c311e9ddfe69f11f3938b83c57b4e959ad9a69f54d'
m=json.loads((A/'MANIFEST04.json').read_bytes());out=[]
for name in ('recovery04.py','owned_io.py','bounded_git01.py'):
 row=next(x for x in m['members'] if x['path']==name);p=A/name;b=p.read_bytes();s=p.lstat();assert len(b)==row['bytes'] and H(b)==row['sha256'] and stat.S_IMODE(s.st_mode)==row['mode'] and s.st_nlink==row['nlink'];out.append(row)
print(json.dumps({'manifest_sha256':H((A/'MANIFEST04.json').read_bytes()),'actual_dependency_bodies':out,'invoked':False},sort_keys=True))
