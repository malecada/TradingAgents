from pathlib import Path
import os,stat,hashlib,json,ast,gzip
H=Path(__file__).resolve().parent;F=H.parent;A=F/'financial-batch-output-genuine-storage-lease-preparation02-2026-10-04';O=F/'financial-batch-output-genuine-storage-lease-preparation01-2026-10-04';V=F/'financial-batch-output-genuine-storage-lease-source-review01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
for root,pin,count in [(A,'68449eb5254ab2500dc24629487ccf3cb78c91609cc224394f497a54d7d9f28e',699),(O,'4666b0d4745709a43326b8b2298be5cb8a8754800aceb9343b552a260ef8b250',1105),(V,'050bb158a3c6d1c3e38976afe3e115609237f6a1ac1007967c619e571ea3cae8',333)]:
 b=(root/'MANIFEST01.json').read_bytes();ok(sha(b)==pin,'seal');d=json.loads(b);rows=d.get('entries',d.get('members'));ok(len(rows)==count,'count');ok(sorted(str(p.relative_to(root)) for p in root.rglob('*') if p!=root/'MANIFEST01.json')==sorted(r['path'] for r in rows),'complete')
 for r in rows:
  p=root/r['path'];s=p.lstat();m=r['mode'];ok(stat.S_IMODE(s.st_mode)==(int(m,8) if type(m)is str else m),'mode')
  if r['kind']=='file':b=p.read_bytes();ok(stat.S_ISREG(s.st_mode) and len(b)==r['bytes'] and sha(b)==r['sha256'],'body');ok(s.st_nlink==r.get('nlink',s.st_nlink),'hardlink count')
  elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'directory')
  else:ok(p.is_symlink() and os.readlink(p)==r['target'],'literal')
new=(A/'storage_lease01.py').read_text();old=(O/'storage_lease01.py').read_text();inv=json.loads((A/'INVERSE_FINAL02.json').read_text());back=new
for e in inv['edits']:ok(back.count(e['after'])==1,'exact unique inverse');back=back.replace(e['after'],e['before'])
ok(inv['added_function'] in back,'helper inverse');back=back.replace(inv['added_function'],'');ok(back==old,'full byte inverse');ok(ast.dump(ast.parse(back))==ast.dump(ast.parse(old)),'AST inverse')
for t in (ast.parse(old),ast.parse(new)):
 node=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='GenuineLease')
 if t is None:pass
 if 'prev' not in globals():prev=ast.dump(node)
 else:ok(prev==ast.dump(node),'genuine class unchanged')
ok((H/'storage_lease01.py').read_text()==new,'tested body exact');ok((H/'owned_io.py').read_bytes()==(O/'owned_io.py').read_bytes(),'IO exact')
(H/'AUTHENTICATION01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'old_rapid_rewrite_replay':'preserved_failed_not_rerun','metadata_only':True},indent=2)+'\n');print(len(checks))
