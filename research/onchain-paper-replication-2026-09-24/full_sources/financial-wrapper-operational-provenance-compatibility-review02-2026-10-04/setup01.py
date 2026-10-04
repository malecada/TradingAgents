from pathlib import Path
import hashlib,json,shutil,stat,os,ast
H=Path(__file__).resolve().parent;B=H.parent;P=B/'financial-wrapper-operational-provenance-compatibility-preparation02-2026-10-04';R=B/'financial-wrapper-operational-provenance-compatibility-review01-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=[]
def auth(p,pin):
 raw=(p/'MANIFEST01.json').read_bytes();assert sha(raw)==pin
 obj=json.loads(raw);seen=set()
 for row in obj['members']:
  name=row['path'];assert name not in seen and not Path(name).is_absolute() and '..' not in Path(name).parts;seen.add(name);q=p/name;s=q.lstat();assert stat.S_IMODE(s.st_mode)==row['mode'],name
  if row['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and sha(q.read_bytes())==row['sha256'],name
  elif row['kind']=='directory':assert stat.S_ISDIR(s.st_mode),name
  elif row['kind']=='symlink':assert stat.S_ISLNK(s.st_mode) and os.readlink(q)==row['target'],name
  else:raise AssertionError(row)
  if 'links' in row:assert s.st_nlink==row['links']
  checks.append({'root':p.name,'path':name,'passed':True})
 return obj
pa=auth(P,'adf054ca1d9c9d04cb83c8a0cf5ee736c74c5b4be20d9715f9d6a4d78bc7b391');ra=auth(R,'6f80852042dbf029c24dd88b3d0243c6f486283fd7fe89715da36fe680f41e7a')
assert sha((P/'MACHINE01.json').read_bytes())=='41345f78085dfdbcd2c605a79599b00086f263da2342aa555e93c0844ab3deb0'
for n in ('financial_wrapper_fixture.py','operational_source_compatibility.py','training.py','workflow_storage.py','original_financial_wrapper_fixture.py','original_training.py','SOURCE_INVERSES02.json','SUCCESSOR_INVERSE01.json','POLICY_DRAFT01.json','PROOF_ROLES_DRAFT01.json','ROOT_REQUIREMENTS02.json','SOURCE_CLOSURE_DRAFT01.json'):(H/n).write_bytes((P/n).read_bytes())
for n in ('REPORT01.md','MACHINE01.json','MANIFEST01.json','WITNESS01.json'):
 q=H/'prior-review01'/n;q.parent.mkdir(exist_ok=True);q.write_bytes((R/n).read_bytes())
replay=H/'replay';replay.mkdir()
for n in ('financial_wrapper_fixture.py','operational_source_compatibility.py','training.py','workflow_storage.py','original_financial_wrapper_fixture.py','original_training.py','SOURCE_INVERSES02.json','SUCCESSOR_INVERSE01.json','check02.py'):(replay/n).write_bytes((P/n).read_bytes())
for n in ('predecessor01','independent_finding01'):shutil.copytree(P/n,replay/n,symlinks=True)
(H/'AUTHENTICATION01.json').write_text(json.dumps({'manifest_pins':{P.name:sha((P/'MANIFEST01.json').read_bytes()),R.name:sha((R/'MANIFEST01.json').read_bytes())},'checks':checks},indent=2)+'\n')
print(json.dumps({'authenticated_members':len(checks),'author_members':len(pa['members']),'prior_review_members':len(ra['members'])}))
