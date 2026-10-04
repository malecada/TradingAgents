import ast,hashlib,json,zlib,importlib.util,sys
from pathlib import Path
import restore01 as S
from git_objects01 import tree_join,RecoveredGit,claim_join
H=Path(__file__).resolve().parent;checks=[]
def ok(v,n):assert v,n;checks.append(n)
def refuse(f,n):
 try:f()
 except (ValueError,KeyError,zlib.error):checks.append(n)
 else:raise AssertionError(n)
s=(H/'restore01.py').read_text();old=(H/'predecessor01/restore01.py').read_text();inv=s
for e in reversed(json.loads((H/'INVERSE02.json').read_text())['edits']):ok(inv.count(e['new'])==1,'unique inverse');inv=inv.replace(e['new'],e['old'])
ok(inv==old,'adapter byte inverse');ok(ast.dump(ast.parse(inv))==ast.dump(ast.parse(old)),'adapter AST inverse')
spec=importlib.util.spec_from_file_location('old_git',H/'predecessor01/git_objects01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
def fixture():
 objects={}
 def obj(kind,value):
  b=kind.encode()+b' '+str(len(value)).encode()+b'\0'+value;oid=hashlib.sha1(b).hexdigest();objects['.git/objects/'+oid[:2]+'/'+oid[2:]]=zlib.compress(b);return oid
 return objects,obj
# Complete genuine opaque object graph, two commits with changed historical body.
r,obj=fixture();oldblob=obj('blob',b'old');newblob=obj('blob',b'new');oldtree=obj('tree',b'100644 a\0'+bytes.fromhex(oldblob));oldcommit=obj('commit',b'tree '+oldtree.encode()+b'\n\nold\n');tree=obj('tree',b'100755 a\0'+bytes.fromhex(newblob));commit=obj('commit',b'tree '+tree.encode()+b'\nparent '+oldcommit.encode()+b'\n\nnew\n');r['a']=b'new'
repo,entries=tree_join(r.__getitem__,set(r),commit,1,manifest_modes={'a':0o700});ok(len(repo.commits)==2 and repo.obj(oldblob,'blob')==b'old','all ancestry separate historical body/mode')
missing=dict(r);missing.pop('.git/objects/'+oldcommit[:2]+'/'+oldcommit[2:]);ok(O.tree_join(missing.__getitem__,set(missing),commit,1)['a'][0]=='100755','SR1 exact old missing-parent RED');refuse(lambda:tree_join(missing.__getitem__,set(missing),commit,1),'SR1 new missing-parent GREEN')
ok(O.tree_join(r.__getitem__,set(r),commit,1)['a'][0]=='100755','SR3 old ignores mode metadata');refuse(lambda:tree_join(r.__getitem__,set(r),commit,1,manifest_modes={'a':0o600}),'SR3 new mode refusal')
# Canonical Git order compares directory names with slash, not plain strings.
r2,obj2=fixture();blob=obj2('blob',b'x');empty=obj2('tree',b'');sortedbody=b'100644 a.c\0'+bytes.fromhex(blob)+b'40000 a\0'+bytes.fromhex(empty);tree2=obj2('tree',sortedbody);c2=obj2('commit',b'tree '+tree2.encode()+b'\n\nok\n');r2['a.c']=b'x';ok(tree_join(r2.__getitem__,set(r2),c2,1)[1]['a.c'][1]==blob,'Git directory slash order positive')
unsorted=obj2('tree',b'40000 a\0'+bytes.fromhex(empty)+b'100644 a.c\0'+bytes.fromhex(blob));bad=obj2('commit',b'tree '+unsorted.encode()+b'\n\nbad\n');ok(O.tree_join(r2.__getitem__,set(r2),bad,1)['a.c'][1]==blob,'SR2 old wrong order RED');refuse(lambda:tree_join(r2.__getitem__,set(r2),bad,1),'SR2 new order GREEN')
for mode in ('040000','100664','120000','160000'):
 t=obj2('tree',mode.encode()+b' a\0'+bytes.fromhex(blob));c=obj2('commit',b'tree '+t.encode()+b'\n\nmode\n');refuse(lambda:tree_join(r2.__getitem__,set(r2),c,1),'invalid mode '+mode)
for key in list(r):
 v=dict(r);v[key]=v[key]+b'bad';refuse(lambda:tree_join(v.__getitem__,set(v),commit,1),'corrupt '+key)
for name in ('.git/objects/info/alternates','.git/info/grafts','.git/shallow','.git/refs/replace/a','.git/objects/pack/a'):
 refuse(lambda:tree_join(r.__getitem__,set(r)|{name},commit,1),'foreign ancestry '+name)
# Original actual claim remains opaque metadata; unavailable ancestry refuses.
claimpath=H.parent/'financial-genuine-wrapper-claimed-run-correction-preparation01-2026-10-04/actual-claim.json';raw=claimpath.read_bytes();ok(hashlib.sha256(raw).hexdigest()=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','authentic original claim metadata');refuse(lambda:claim_join(repo,json.loads(raw)),'actual old claim cannot bind unrelated object graph')
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_bytes());refuse(lambda:S.validate_request(q),'draft release refusal')
for n,pin in S.PINS.items():ok(S.R.digest(S.R.read(H,n))==pin,'helper pin '+n)
root=H/'owned02';root.mkdir();(root/'opaque').write_bytes(b'opaque');m=S.R.scan(root);info=S.R.pack(root,m,H/'owned02.tar.gz');out=H/'flat02';S.reserve(out);result=S.R.restore(H/'owned02.tar.gz',info,m,out);ok(result['regular_bodies']==1,'unchanged real tiny R4 pipeline')
ok(not any(n in sys.modules for n in ('torch','numpy','pandas')),'no numerical imports')
(H/'CHECKS02.json').write_bytes(S.R.encode({'count':len(checks),'checks':checks,'actual_capture_restores':0,'actual_claims':0}));print(len(checks))
