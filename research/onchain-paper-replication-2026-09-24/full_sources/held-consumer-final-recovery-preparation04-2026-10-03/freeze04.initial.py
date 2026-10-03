"""Freeze owned source preparation; lstat special fixture entries without following."""
import ast,hashlib,json,os,stat
from pathlib import Path
P=Path(__file__).resolve().parent;O=P.parent/'held-consumer-final-recovery-preparation03-2026-10-03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(P/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
a=(O/'recovery03.py').read_text();b=(P/'recovery04.py').read_text()
start=b.index('   # TarInfo strips DIR slashes');end=b.index("   require((t.isdir()",start)
reversed_b=b[:start]+"   name=path_name(pending if pending is not None else t.name);pending=None\n"+b[end:]
reversed_b=reversed_b.replace("pending=fields[b'path'];continue","pending=path_name(fields[b'path']);continue")
assert reversed_b==a
oldnodes={x.name:x for x in ast.parse(a).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};newnodes={x.name:x for x in ast.parse(b).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
unchanged=[]
for name,x in oldnodes.items():
 if name!='framed_members':assert ast.dump(x)==ast.dump(newnodes[name]);unchanged.append(name)
copies={n:sha(P/n) for n in ('owned_io.py','bounded_git01.py','REQUEST_TEMPLATE01.json')}
for n,h in copies.items():assert sha(O/n)==h
write('INVERSE04.json',{'schema_version':1,'complete_text_inverse_matches_recovery03':True,'unchanged_ast':unchanged,'copied_bytes':copies,'old_sha256':sha(O/'recovery03.py'),'new_sha256':sha(P/'recovery04.py')})
refs=[O/'recovery03.py',O/'PROTOCOL03.md',P.parent/'held-consumer-final-recovery-review03-2026-10-03'/'REVIEW03.md',P.parent/'held-consumer-final-baseline-root-remote-recovery02-2026-10-03'/'FLAT02.stderr',P/'recovery04.py',P/'PROTOCOL04.md',P/'INVERSE04.json']
write('PINS04.json',{'schema_version':1,'scope':'source preparation only; no actual recovery','files':{str(q.relative_to(P.parent)):sha(q) for q in refs}})
rows=[]
def visit(root):
 for q in sorted(root.iterdir()):
  if q.parent==P and q.name in ('MANIFEST04.json','MANIFEST04.sha256'):continue
  s=q.lstat();r={'path':str(q.relative_to(P)),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink}
  if stat.S_ISDIR(s.st_mode):r['kind']='directory';rows.append(r);visit(q)
  elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(q));rows.append(r)
  elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(q));rows.append(r)
  else:raise AssertionError('unselected type')
visit(P);write('MANIFEST04.json',{'schema_version':1,'root_mode':stat.S_IMODE(P.stat().st_mode),'members':rows});(P/'MANIFEST04.sha256').write_text(sha(P/'MANIFEST04.json')+'  MANIFEST04.json\n')
print(json.dumps({'source':sha(P/'recovery04.py'),'protocol':sha(P/'PROTOCOL04.md'),'manifest':sha(P/'MANIFEST04.json'),'members':len(rows),'inverse':True},sort_keys=True))
