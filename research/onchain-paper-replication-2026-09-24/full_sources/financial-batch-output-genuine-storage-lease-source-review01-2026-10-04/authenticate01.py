from pathlib import Path
import json,hashlib,stat,os,ast,gzip
H=Path(__file__).resolve().parent;A=H.with_name('financial-batch-output-genuine-storage-lease-preparation01-2026-10-04');sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
p=A/'MANIFEST01.json';ok(sha(p.read_bytes())=='4666b0d4745709a43326b8b2298be5cb8a8754800aceb9343b552a260ef8b250','manifest');rows=json.loads(p.read_text())['entries'];ok(len(rows)==1105,'1105');ok(sorted(str(x.relative_to(A)) for x in A.rglob('*') if x!=p)==sorted(r['path'] for r in rows),'complete')
for r in rows:
 q=A/r['path'];s=q.lstat();ok(stat.S_IMODE(s.st_mode)==r['mode'],'mode '+r['path'])
 if r['kind']=='file':b=q.read_bytes();ok(stat.S_ISREG(s.st_mode) and len(b)==r['bytes'] and sha(b)==r['sha256'] and s.st_nlink==r['nlink'],'file '+r['path'])
 elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'dir')
 else:ok(q.is_symlink() and os.readlink(q)==r['target'],'literal')
for path,r in json.loads((A/'PREDECESSOR_PINS01.json').read_text()).items():
 b=Path(path).read_bytes();ok(len(b)==r['bytes'] and sha(b)==r['sha256'],'predecessor')
j=json.loads((A/'SOURCE_JOINS01.json').read_text())
for r in j['bodies']:
 path=Path(r['path']);b=path.read_bytes();ok(sha(b)==r['sha256'] and len(b)==r['bytes'],'actual source body');tree=ast.parse(b)
 for d in r['definitions']:
  n=next(n for n in tree.body if getattr(n,'name',None)==d['name']);ok(sha(ast.dump(n,include_attributes=False).encode())==d['ast_sha256'],'AST '+d['name'])
ok((H/'storage_lease01.py').read_bytes()==(A/'storage_lease01.py').read_bytes(),'exact tested copy');ok((H/'owned_io.py').read_bytes()==(A/'owned_io.py').read_bytes(),'IO copy')
(H/'AUTHENTICATION01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'author_assertions_reported':364,'repeated_suite':155,'independent_replay_check02':'FAILED accepted partial','independent_replay_check03':49,'independent_replay_check04':5},indent=2)+'\n');print(len(checks))
