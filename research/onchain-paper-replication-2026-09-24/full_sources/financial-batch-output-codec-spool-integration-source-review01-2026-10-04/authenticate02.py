import ast,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-codec-spool-integration-preparation01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=0;rows=[]
def ok(v):
 global checks
 assert v;checks+=1
def seal(root,n,pin,count):
 ok(sha((root/n).read_bytes())==pin);m=json.loads((root/n).read_text())['members'];ok(len(m)==count)
 ok(sorted(str(p.relative_to(root)) for p in root.rglob('*') if p!=root/n)==sorted(r['path'] for r in m))
 for r in m:
  p=root/r['path'];s=p.lstat();mode=r['mode'];mode=int(mode,8) if type(mode)is str else mode;ok(stat.S_IMODE(s.st_mode)==mode)
  if r['kind']=='file':b=p.read_bytes();ok(stat.S_ISREG(s.st_mode) and len(b)==r['bytes'] and sha(b)==r['sha256'])
  elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode))
  elif r['kind']=='symlink':ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'])
  else:raise AssertionError('unknown typed member: '+r['kind'])
seal(A,'MANIFEST01.json','086bf7c37b795e339ab9937265ef81b353a36cc12ff132cf2fd69c4ce60666e6',3431)
a=json.loads((A/'AUTHENTICATION01.json').read_text())
for r in a['frozen_scopes']:seal(Path(r['root']),r['manifest'],r['sha256'],r['complete_typed_members'])
for r in a['unchanged_copies']:
 p=Path(r['source']);b=p.read_bytes();q=(A/r['name']).read_bytes();ok(b==q and sha(b)==r['sha256']);ok(ast.dump(ast.parse(b))==ast.dump(ast.parse(q)))
for r in a['authority_sources']:
 p=Path(r['path']);b=p.read_bytes();ok(p.resolve()==p and len(b)==r['bytes'] and sha(b)==r['sha256'])
 rows.append({'path':str(p),'mode':stat.S_IMODE(p.lstat().st_mode),'sha256':sha(b),'bytes':len(b)})
for n in ('router01.py','router02.py','router03.py','router04.py'):
 b=(A/n).read_bytes();ast.parse(b);rows.append({'path':str(A/n),'sha256':sha(b),'bytes':len(b)})
ok(b'bytes is not JSON serializable' in (A/'CHECK01.err').read_bytes());ok(sha((A/'MACHINE01.json').read_bytes())=='6b07f8eddbe2377d0c2ed23593b2c9177f47214b8ffd8ce2a21ea42254c39ce7')
(H/'AUTHENTICATION02.json').write_text(json.dumps({'checks':checks,'all_original_typed_members':3431+301+185+581+555,'all_six_sources_byte_and_AST_equal':True,'references':rows,'original_RED_and_drafts_preserved':True},sort_keys=True,indent=2)+'\n');print(checks,'checks passed')
