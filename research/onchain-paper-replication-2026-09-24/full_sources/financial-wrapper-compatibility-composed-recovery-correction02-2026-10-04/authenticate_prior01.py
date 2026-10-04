from pathlib import Path
import hashlib,json,os,stat
D=Path(__file__).resolve().parent;F=D.parent;h=lambda b:hashlib.sha256(b).hexdigest();rows=[]
for dirname,pin in [('financial-wrapper-compatibility-composed-recovery-preparation01-2026-10-04','5370777415963c2f47fcdcb4c86475d39ed2b89c270c4a7c2283f31aea0a2987'),('financial-wrapper-compatibility-composed-recovery-review01-2026-10-04','e7c071a53071a5fcd866b707a23fa2415c9ec2290a2f9746bb71c17ceb5fecc8')]:
 root=F/dirname;raw=(root/'MANIFEST01.json').read_bytes();assert h(raw)==pin;m=json.loads(raw);declared={x['path'] for x in m['members']};actual=set()
 for base,ds,fs in os.walk(root,followlinks=False):
  for n in ds+fs:
   p=Path(base)/n
   if p!=root/'MANIFEST01.json':actual.add(p.relative_to(root).as_posix())
 assert actual==declared-{'.'}
 for x in m['members']:
  p=root/x['path'];s=p.lstat();mode=int(x['mode'],8) if isinstance(x['mode'],str) else x['mode'];assert stat.S_IMODE(s.st_mode)==mode
  if 'nlink' in x:assert s.st_nlink==x['nlink']
  if x['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and h(p.read_bytes())==x['sha256']
  elif x['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
  elif x['kind']=='fifo':assert stat.S_ISFIFO(s.st_mode)
  elif x['kind']=='symlink':assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target']
  else:raise ValueError(x['kind'])
 rows.append({'root':str(root),'manifest_sha256':pin,'typed_members':len(m['members']),'all_regular_bodies_rehashed':True,'special_negative_fixtures_metadata_only':True})
prior=F/'financial-wrapper-compatibility-composed-recovery-review01-2026-10-04';out=D/'prior-review01';out.mkdir(mode=0o700)
for n in ['MACHINE01.json','MANIFEST01.json','REPORT01.md','WITNESS01.json','WITNESS02.json','witness01.py','witness02.py','WITNESS01.stderr','WITNESS02.stderr']:(out/n).write_bytes((prior/n).read_bytes())
(D/'PRIOR_AUTHENTICATION01.json').write_text(json.dumps({'schema_version':1,'roots':rows,'originals_mutated':False},indent=2)+'\n');print(rows)
