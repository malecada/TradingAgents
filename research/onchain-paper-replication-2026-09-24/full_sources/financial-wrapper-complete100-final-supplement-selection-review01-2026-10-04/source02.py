from pathlib import Path
import hashlib,json,stat,os
D=Path(__file__).resolve().parent;F=D.parent;sha=lambda b:hashlib.sha256(b).hexdigest();checks=[];files=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
for name,expected in [('financial-wrapper-complete100-final-supplement-preservation-review01-2026-10-04','66a4da7d6716327547af5b68c6a8a333a2ae8737ddf49486c155454e1ca48772'),('financial-wrapper-complete100-final-supplement-tooling-review01-2026-10-04','88f9f46801343d5a2350c290db1031b2bbd884a165b72517680e88c0219dd293')]:
 root=F/name;raw=(root/'MANIFEST01.json').read_bytes();ok(sha(raw)==expected,'exact review seal');m=json.loads(raw);rows=m['members'];ok({p.relative_to(root).as_posix() for p in root.rglob('*') if p!=root/'MANIFEST01.json'}=={x['path'] for x in rows}-{'.'},'complete reviewed membership');files.append(root/'MANIFEST01.json')
 for x in rows:
  p=root/x['path'];s=p.lstat();mode=int(x['mode'],8) if isinstance(x['mode'],str) else x['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'reviewed actual modes')
  if x['kind']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and sha(p.read_bytes())==x['sha256'],'exact reviewed body');files.append(p)
  elif x['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'directory')
  else:ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target'],'literal link')
T=F/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04';tm=json.loads((T/'MANIFEST01.json').read_bytes());ok({p.relative_to(T).as_posix() for p in T.rglob('*') if p!=T/'MANIFEST01.json'}=={x['path'] for x in tm['members']}-{'.'},'complete tooling membership')
for x in tm['members']:
 p=T/x['path'];s=p.lstat();mode=int(x['mode'],8) if isinstance(x['mode'],str) else x['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'tooling mode')
 if x['kind']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and sha(p.read_bytes())==x['sha256'],'tooling body');files.append(p)
 elif x['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'tooling dir')
 else:ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target'],'tooling literal link')
files.append(T/'MANIFEST01.json');(D/'SOURCE02.json').write_text(json.dumps({'checks':len(checks),'names':checks,'authenticated_files':[{'path':str(p),'sha256':sha(p.read_bytes())} for p in sorted(set(files))],'release':None},indent=2)+'\n');print(len(checks))
