import ast, hashlib, importlib.util, json, os, stat, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'financial-genuine-wrapper-root-recordfix-final-union01-2026-10-04'
spec=importlib.util.spec_from_file_location('capture_source_only',ROOT/'capture02.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
for n,h in c.PINS.items():check(sha((c.PRIMITIVES/n).read_bytes())==h,'primitive '+n)
sys.path.insert(0,str(c.PRIMITIVES));spec=importlib.util.spec_from_file_location('r4_scope',c.PRIMITIVES/'recovery04.py');r4=importlib.util.module_from_spec(spec);spec.loader.exec_module(r4)
check(len(c.SCOPES)==11,'eleven originals')
rows=[]
for scope,root in sorted(c.SCOPES.items()):
 check(root.is_absolute() and root.resolve()==root,'canonical '+scope)
 def visit(p,rel):
  s=p.lstat();before=r4.sig(s);row=dict(scope=scope,path=rel,mode=stat.S_IMODE(s.st_mode))
  if stat.S_ISLNK(s.st_mode):row.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):
   row['kind']='directory';rows.append(row)
   for q in sorted(p.iterdir()):visit(q,q.name if rel=='.' else rel+'/'+q.name)
   check(before==r4.sig(p.lstat()),'stable directory '+scope+'/'+rel);return
  else:
   check(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=c.FILE,'type/links/extent '+scope+'/'+rel)
   b=r4.read(root,rel);row.update(kind='file',bytes=len(b),sha256=sha(b))
  check(before==r4.sig(p.lstat()),'stable member '+scope+'/'+rel);rows.append(row)
 visit(root,'.')
files=[r for r in rows if r['kind']=='file'];logical=sum(r['bytes'] for r in files)
check(logical<c.LIMIT,'actual all original bodies below64MiB')
check(sha((c.SOURCE_CAPTURE/'source-manifest.json').read_bytes())=='26c67e9c9b28dd4cd607ab3833fa14143d6e8e4c7c3617024275294940ffbc53','source manifest')
check(sha((c.SOURCE_CAPTURE/'source.tar.gz').read_bytes())=='8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb','source archive')
m=json.loads((c.SOURCE_CAPTURE/'source-manifest.json').read_bytes());r4.same(c.SOURCE,m);check(len(m['members'])==986,'actual complete Source986')
q=json.loads((c.PARENT/'REQUEST_FINAL02.json').read_bytes());check(sha((c.PARENT/'REQUEST_FINAL02.json').read_bytes())=='28f2ae5340d38ac71450c8947c5b1ad30ac4192481da81596684445c9cf9b52e','actual current request')
for scope,pin in [('actual-verifier-review','c856494d3c46b5f26241a72e66219adf35d79905b1117291cdc5b22e1601814a'),('caller-review','9b82e1c0b5acfdeae8ef5432159396dd911731a7a721be5bcc6cdbfdebc8e1dd'),('verifier-review','434c9a4fa7f0e38d329b9ed4dc77a3e4fe9dade8c528dd21bb4f00f26d11e779')]:check(sha((c.SCOPES[scope]/'MANIFEST01.json').read_bytes())==pin,'full original review '+scope)
check(sha((c.PARENT/'proofs/FULL_RECOVERY_READBACK02.json').read_bytes())=='f86497ee97d6b5d91066db1aa2520d1bed844165b4e08d7169a5917c5bfda4df','actual whole Source recovery proof')
check(sha((c.PARENT/'proofs/FINAL_RELEASE_REVIEW01.json').read_bytes())=='550a5a54b0c067b2ba5c3df833877ddc41dae375ededdc1c3b3dcdee34fdfbcb','actual final release')
check(sha((c.SCOPES['root-verifier-binding']/'MANIFEST_ACTUAL02.json').read_bytes())=='8258937c14573d2f8a51e80b1b8526e6d9da28776da3804893e54ae0436c6a93','actual generation complete manifest')
out=dict(count=len(checks),checks=checks,actual_original_rows=rows,original_trees=len(c.SCOPES),original_members=len(rows),regular_files=len(files),regular_bytes=logical,lexical_links=sum(r['kind']=='lexical-symlink' for r in rows),source_members=len(m['members']),source_regular=sum(r['kind']=='file' for r in m['members']),source_unchanged=True,actual_capture_performed=False)
(HERE/'SCOPE_CHECK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('checks','actual_original_rows')}))
