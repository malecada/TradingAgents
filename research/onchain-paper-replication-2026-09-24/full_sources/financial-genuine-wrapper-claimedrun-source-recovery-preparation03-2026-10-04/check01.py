import ast,hashlib,importlib.util,json,zlib,sys
from pathlib import Path
H=Path(__file__).resolve().parent
import git_objects01 as N
import restore01 as S
spec=importlib.util.spec_from_file_location('accepted02',H/'predecessor02/git_objects01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
checks=[]
def ok(v,n):assert v,n;checks.append(n)
def refuses(f,n):
 try:f()
 except ValueError as e:ok(str(e)=='finite ancestry',n)
 else:raise AssertionError(n)
v=json.loads((H/'INVERSE03.json').read_bytes());old=(H/'predecessor02/git_objects01.py').read_text();new=(H/'git_objects01.py').read_text();ok(new.replace(v['predicate_new'],v['predicate_old'])==old,'single predicate byte inverse');ok(ast.dump(ast.parse(new.replace(v['predicate_new'],v['predicate_old'])))==ast.dump(ast.parse(old)),'single predicate AST inverse');ok((H/'restore01.py').read_text().replace(v['helper_pin_new'],v['helper_pin_old'])==(H/'predecessor02/restore01.py').read_text(),'adapter only helper pin inverse')
ok(hashlib.sha256((H/'review02/MANIFEST01.json').read_bytes()).hexdigest()=='ee1e4aa23cc0d37f4db3c6607638db27a29ff1285b8cc4943089efd390687c47','genuine accepted-narrow review manifest')
r=H/'review02/opaque-objects';objects={f.relative_to(r).as_posix():f.read_bytes() for f in r.rglob('*') if f.is_file()};wide=json.loads((H/'review02/READBACK01.json').read_bytes())['witnesses'][0]['commit']
a=O.RecoveredGit(objects.__getitem__,set(objects));a.ancestry(wide);ok(len(a.commits)==1025,'actual original reviewer SR4 RED1025')
a=N.RecoveredGit(objects.__getitem__,set(objects));refuses(lambda:a.ancestry(wide),'successor GREEN refuses1025');ok(len(a.state)==1024,'no1025th state inserted')
oldcommit=O.RecoveredGit(objects.__getitem__,set(objects)).obj(wide,'commit');lines=oldcommit.splitlines(keepends=True);parent_indices=[i for i,l in enumerate(lines) if l.startswith(b'parent ')];ok(len(parent_indices)==1024,'authentic witness1024 parents');del lines[parent_indices[-1]];value=b''.join(lines);body=b'commit '+str(len(value)).encode()+b'\0'+value;root=hashlib.sha1(body).hexdigest();name='.git/objects/'+root[:2]+'/'+root[2:];objects[name]=zlib.compress(body);out=H/'boundary1024-object';out.write_bytes(objects[name]);a=N.RecoveredGit(objects.__getitem__,set(objects));result=a.ancestry(root);ok(len(a.commits)==len(a.state)==1024,'1023parents plus root1024 accepted');ok(a.ancestry(root) is result,'completed cache accepted at cap');parent=next(iter(result['parents']));ok(a.ancestry(parent) is a.commits[parent],'completed parent cache at cap')
for n,pin in S.PINS.items():ok(hashlib.sha256((H/n).read_bytes()).hexdigest()==pin,'exact helper '+n)
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_bytes())
try:S.validate_request(q)
except ValueError:ok(True,'missing actual authority still refuses')
else:raise AssertionError('release')
ok(not any(n in sys.modules for n in ('torch','numpy','pandas')),'no numerical imports')
(H/'CHECKS01.json').write_bytes(S.R.encode({'count':len(checks),'checks':checks,'actual_restores':0,'new_claims':0,'boundary1024_commit':root,'reviewer1025_commit':wide}));print(len(checks))
