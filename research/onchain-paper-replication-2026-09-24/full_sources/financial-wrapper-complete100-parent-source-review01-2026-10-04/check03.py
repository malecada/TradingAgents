"""Authenticate actual Root preservation readback and both complete review trees."""
import hashlib,json,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;sha=lambda b:hashlib.sha256(b).hexdigest();rows=[]
p=B/'heartbeat-root-checkpoint10-2026-10-04/REFERENCE_PARENT_AND_RECOVERY_READBACK01.json';raw=p.read_bytes();assert sha(raw)=='6787cd7753b9046d9d803b78380ac7cc010164aa2805ab517ad1f67c7a1ce1cd';assert (H/'ROOT_REFERENCE_AND_RECOVERY_READBACK01.json').read_bytes()==raw
for ref in json.loads(raw)['reviews']:
 d=B/ref['directory'];mb=(d/'MANIFEST01.json').read_bytes();assert sha(mb)==ref['manifest_sha256'];m=json.loads(mb);members=m['members'];assert len(members)==ref['members_verified'];names=[]
 for r in members:
  p=d/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode'];names.append(r['path'])
  if r['kind']=='file':
   assert stat.S_ISREG(s.st_mode) and s.st_size<=4194304;b=p.read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
  else:assert r['kind']=='directory' and stat.S_ISDIR(s.st_mode)
 assert sorted(names)==sorted(['.']+[str(p.relative_to(d)) for p in d.rglob('*') if p.name!='MANIFEST01.json'])
 rows.append({'directory':str(d),'manifest_sha256':sha(mb),'actual_complete_members':len(members)})
# Complete Main preparation membership/type/mode too, not merely nine hashes.
p=B/'financial-wrapper-complete100-root-parent-preparation01-2026-10-04';m=json.loads((p/'MANIFEST01.json').read_bytes());assert len(m['members'])==9
for r in m['members']:
 s=(p/r['path']).lstat();b=(p/r['path']).read_bytes();assert stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==r['mode'] and len(b)==r['bytes'] and sha(b)==r['sha256']
assert sorted(r['path'] for r in m['members'])==sorted(str(x.relative_to(p)) for x in p.rglob('*') if x.name!='MANIFEST01.json')
(H/'REVIEW_SCOPE_JOINS01.json').write_text(json.dumps({'root_receipt_sha256':sha(raw),'reviews':rows,'preparation_members':9,'scope':'complete metadata membership/modes/body authentication; original independent semantic verdicts retained, no recovery replay'},indent=2,sort_keys=True)+'\n')
print(json.dumps({'review_members':sum(r['actual_complete_members'] for r in rows),'preparation_members':9,'verified':True}))
