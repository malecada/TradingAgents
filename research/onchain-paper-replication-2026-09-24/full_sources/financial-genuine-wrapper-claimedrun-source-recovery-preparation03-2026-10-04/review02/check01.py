import ast,copy,hashlib,importlib.util,json,os,re,stat,sys,zlib
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'financial-genuine-wrapper-claimedrun-source-recovery-preparation02-2026-10-04';OLD=H.parent/'financial-genuine-wrapper-claimedrun-source-recovery-preparation01-2026-10-04';W=H.parent/'financial-genuine-wrapper-claimedrun-source-recovery-review01-2026-10-04';checks=[];refusals=[];witnesses=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(f,n):
 try:f()
 except (ValueError,KeyError,UnicodeError,zlib.error,FileExistsError) as e:refusals.append({'case':n,'message':str(e)});check(True,'refusal '+n)
 else:raise AssertionError('not refused '+n)
def module(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
check(sha((P/'MANIFEST02.json').read_bytes())=='bb6db7b928c92b1a310bbbf759dfcd212b92c8ed031d360069c1c5b91df9a3be','exact frozenmanifest');manifest=json.loads((P/'MANIFEST02.json').read_bytes());actual=[]
def walk(p):
 for q in p.iterdir():
  actual.append(q.relative_to(P).as_posix())
  if stat.S_ISDIR(q.lstat().st_mode):walk(q)
walk(P);check(set(actual)=={r['path'] for r in manifest['members']}|{'MANIFEST02.json'},'complete author members')
for r in manifest['members']:
 p=P/r['path'];s=p.lstat();check(oct(stat.S_IMODE(s.st_mode))==r['mode'],'mode '+r['path'])
 if r['kind']=='file':check(p.is_file() and len(p.read_bytes())==r['bytes'] and sha(p.read_bytes())==r['sha256'],'body '+r['path'])
 elif r['kind']=='symlink':check(os.readlink(p)==r['target'],'literal symlink')
 else:check(stat.S_ISDIR(s.st_mode),'directory')
sys.path.insert(0,str(P));import restore01 as S
from git_objects01 import RecoveredGit,tree_join,claim_join
old=module('oldparser',OLD/'git_objects01.py');check(sha((P/'restore01.py').read_bytes())=='fc913e835921d5b6ab8dfba99b6d1c7ebb376529603c7438edcd73d33264ca84','exact adapter');check(sha((P/'git_objects01.py').read_bytes())=='05af0c620a115429ab3d20bff61beffc392013255cafdec1ea7c124e0647e2f7','exact Git parser')
back=(P/'restore01.py').read_text()
for r in reversed(json.loads((P/'INVERSE02.json').read_bytes())['edits']):check(back.count(r['new'])==1,'unique inverse seam');back=back.replace(r['new'],r['old'])
check(back==(OLD/'restore01.py').read_text(),'full adapter byte inverse');check(ast.dump(ast.parse(back))==ast.dump(ast.parse((OLD/'restore01.py').read_bytes())),'full adapter AST inverse')
for n,pin in S.PINS.items():check(sha((P/n).read_bytes())==pin,'exact helper '+n)
# Reuse the exact independently frozen opaque witness bodies; no actual Source decode.
d={p.relative_to(W/'opaque-source').as_posix():p.read_bytes() for p in (W/'opaque-source').rglob('*') if p.is_file()}
for name,commit,count in [('SR1','20cfb2453f298fe1120b642d8b9973e2aa5e97fa',1),('SR2','64ef24af308b4067814d95df321a04fdcf742764',2)]:
 check(len(old.tree_join(d.__getitem__,set(d),commit,count))==count,'exact old RED '+name);refuse(lambda commit=commit,count=count:tree_join(d.__getitem__,set(d),commit,count),'exact new GREEN '+name)
m={p.relative_to(W/'mode-source').as_posix():p.read_bytes() for p in (W/'mode-source').rglob('*') if p.is_file()};mc='3875a43fb55643c01dee8001e2ff60c4d4af71fa';check(old.tree_join(m.__getitem__,set(m),mc,1)['body'][0]=='100755','exact old RED SR3');refuse(lambda:tree_join(m.__getitem__,set(m),mc,1,manifest_modes={'body':0o600}),'exact new GREEN SR3')
# Authentic opaque two-commit graph: historical bytes/modes must stay historical.
objects={}
def obj(kind,value):
 body=kind.encode()+b' '+str(len(value)).encode()+b'\0'+value;oid=hashlib.sha1(body).hexdigest();objects['.git/objects/'+oid[:2]+'/'+oid[2:]]=zlib.compress(body);return oid
def commit(tree,parents=(),message=b'opaque'):
 return obj('commit',b'tree '+tree.encode()+b'\n'+b''.join(b'parent '+p.encode()+b'\n' for p in parents)+b'author O <o@invalid> 0 +0000\ncommitter O <o@invalid> 0 +0000\n\n'+message+b'\n')
b1=obj('blob',b'old opaque');t1=obj('tree',b'100644 f\0'+bytes.fromhex(b1));c1=commit(t1);b2=obj('blob',b'new opaque');t2=obj('tree',b'100755 f\0'+bytes.fromhex(b2));c2=commit(t2,[c1]);objects['f']=b'new opaque';repo,entries=tree_join(objects.__getitem__,set(objects),c2,1,manifest_modes={'f':0o750});check(len(repo.commits)==2 and repo.obj(b1,'blob')==b'old opaque' and repo.commits[c1]['entries']['f'][0]=='100644','historical distinct bodies/modes retained')
for key in tuple(objects):
 mutated=dict(objects);mutated[key]+=b'\x00';refuse(lambda mutated=mutated:tree_join(mutated.__getitem__,set(mutated),c2,1),'trailing/corrupt '+key)
for forbidden in ('.git/shallow','.git/info/grafts','.git/objects/info/alternates','.git/refs/replace/a','.git/objects/pack/a'):refuse(lambda forbidden=forbidden:tree_join(objects.__getitem__,set(objects)|{forbidden},c2,1),'foreign '+forbidden)
refuse(lambda:tree_join(objects.__getitem__,set(objects),c2,2),'wrong count');refuse(lambda:tree_join(objects.__getitem__,set(objects),c2,1,limit=8),'object cap');refuse(lambda:repo.obj(c1,'blob'),'cached type mismatch')
repo.start-=121;refuse(lambda:repo.obj(c1,'commit'),'deadline elapsed');repo=RecoveredGit(objects.__getitem__,set(objects));repo.state[c2]=1;refuse(lambda:repo.ancestry(c2),'cycle state guard');refuse(lambda:repo.tree(t1,depth=33),'depth33');refuse(lambda:repo.tree(t1,active={t1}),'tree cycle guard')
for mode,name in [('040000','f'),('100664','f'),('120000','f'),('160000','f'),('100644','../f'),('100644','a/f')]:
 t=obj('tree',mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(b1));c=commit(t);refuse(lambda c=c:tree_join(objects.__getitem__,set(objects),c,1),'mode/path '+mode+name)
# Boundary witness: 1024 parents + root =1025 fully hashed commits, depth1.
empty=obj('tree',b'');parents=[commit(empty,message=('parent'+str(i)).encode()) for i in range(1024)];wide=commit(empty,parents,b'root');boundary=RecoveredGit(objects.__getitem__,set(objects));boundary.ancestry(wide);check(len(boundary.commits)==1025,'1025 commit bound witness');witnesses.append({'id':'SR4','commit':wide,'accepted_commit_count':len(boundary.commits),'declared_cap':1024,'reason':'ancestry checks len(self.state)<=1024 before inserting a new commit, allowing1025','fixed_current_source_has_far_fewer_commits':True})
# Write only this finite opaque witness graph, never a claim or scientific array.
root=H/'opaque-objects';root.mkdir()
for name,b in objects.items():p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
# Genuine original claim/schema scalar guards only; no constructed Admission/claim history.
claimpath=H.parent/'financial-genuine-wrapper-claimed-run-correction-preparation01-2026-10-04/actual-claim.json';raw=claimpath.read_bytes();check(sha(raw)=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','genuine actual claim metadata');claim=json.loads(raw);refuse(lambda:claim_join(repo,claim),'genuine claim refuses unrelated opaque repo')
q=json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes());refuse(lambda:S.validate_request(q),'unbound actualremote release');refuse(lambda:S.run(q),'uninstalled freshscope');check(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no numericimports')
out={'decision':'SR1_SR2_SR3_CORRECTED_SR4_CAP_BOUNDARY_FOUND','checks':len(checks),'check_names':checks,'refusals':refusals,'witnesses':witnesses,'actual_Source_Git_objects_decoded':False,'actual747_restore':False,'actual_network':False,'genuine_admission_or_claim':False};(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('check_names','refusals')}))
