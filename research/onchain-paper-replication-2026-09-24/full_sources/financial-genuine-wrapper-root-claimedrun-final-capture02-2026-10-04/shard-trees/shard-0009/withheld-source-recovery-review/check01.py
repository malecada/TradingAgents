import ast,hashlib,importlib.util,json,os,re,stat,sys,types,zlib
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'financial-genuine-wrapper-claimedrun-source-recovery-preparation01-2026-10-04';checks=[];refusals=[];witnesses=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(f,n):
 try:f()
 except (ValueError,KeyError,FileExistsError,UnicodeError,IndexError) as e:refusals.append({'case':n,'exception':type(e).__name__,'message':str(e)});check(True,'refusal '+n)
 else:raise AssertionError('not refused '+n)
m=json.loads((P/'MANIFEST01.json').read_bytes());check(sha((P/'MANIFEST01.json').read_bytes())=='d35c8c1e51312e4355f5ab4813056c6398ef7816de835758fe8f102012ab119a','frozen manifest');actual=[]
def scan(p):
 for q in p.iterdir():
  actual.append(q.relative_to(P).as_posix())
  if stat.S_ISDIR(q.lstat().st_mode):scan(q)
scan(P);check(set(actual)=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'complete author evidence')
for r in m['members']:
 p=P/r['path'];s=p.lstat();check(oct(stat.S_IMODE(s.st_mode))==r['mode'],'author mode '+r['path'])
 if r['kind']=='file':check(stat.S_ISREG(s.st_mode) and len(p.read_bytes())==r['bytes'] and sha(p.read_bytes())==r['sha256'],'author body '+r['path'])
 else:check(stat.S_ISDIR(s.st_mode),'author directory')
sys.path.insert(0,str(P));import restore01 as S
from git_objects01 import tree_join
check(sha((P/'restore01.py').read_bytes())=='e465b5b9eaf169eb34f96c433600a2d50bf4103bebfe50f9eaeaf797dd97ca60','exact adapter');check(sha((P/'git_objects01.py').read_bytes())=='693f09b34e4ef87902443a83e5af543c02ed2e8a6adbdfae6e22928dc95e3cc8','exact parser')
q=json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes());refuse(lambda:S.validate_request(q),'null remote/review/release');refuse(lambda:S.run(q),'noninstalled scope')
for name,pin in S.PINS.items():check(sha((P/name).read_bytes())==pin,'exact primitive '+name)
new=ast.parse((P/'restore01.py').read_bytes());old=ast.parse((P/'original-restore01.py').read_bytes())
for name in ('ref','remote_bodies'):
 get=lambda tr:next(n for n in tr.body if isinstance(n,ast.FunctionDef) and n.name==name)
 check(ast.dump(get(new))==ast.dump(get(old)),'unchanged AST '+name)
# Independent reverse unified diff (no patch/git mutation or external tool).
patch=(P/'SOURCE_DELTA01.patch').read_text().splitlines(keepends=True);oldlines=(P/'original-restore01.py').read_text().splitlines(keepends=True);result=[];pos=0;i=2
while i<len(patch):
 header=patch[i];mt=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',header);check(mt is not None,'valid declared delta hunk');start=int(mt[1])-1;result+=oldlines[pos:start];pos=start;i+=1
 while i<len(patch) and not patch[i].startswith('@@ '):
  line=patch[i];i+=1
  if line.startswith(' '):check(oldlines[pos]==line[1:],'delta context');result.append(line[1:]);pos+=1
  elif line.startswith('-'):check(oldlines[pos]==line[1:],'delta old bytes');pos+=1
  elif line.startswith('+'):result.append(line[1:])
  elif line.startswith('\\ No newline'):pass
  else:raise AssertionError('patch line')
result+=oldlines[pos:];check(''.join(result)==(P/'restore01.py').read_text(),'full declared text delta exact')
source={}
def obj(kind,value,store=source):
 body=kind.encode()+b' '+str(len(value)).encode()+b'\0'+value;oid=hashlib.sha1(body).hexdigest();store['.git/objects/'+oid[:2]+'/'+oid[2:]]=zlib.compress(body);return oid
payload=b'opaque independent metadata';blob=obj('blob',payload);tree=obj('tree',b'100644 body\0'+bytes.fromhex(blob));commit=obj('commit',b'tree '+tree.encode()+b'\nauthor O <o@invalid> 0 +0000\ncommitter O <o@invalid> 0 +0000\n\nopaque\n');source['body']=payload;check(tree_join(source.__getitem__,set(source),commit,1)=={'body':('100644',blob)},'valid complete current tree')
for name in tuple(source):
 missing=dict(source);del missing[name];refuse(lambda missing=missing:tree_join(missing.__getitem__,set(missing),commit,1),'missing '+name)
 changed=dict(source);changed[name]=changed[name]+b'trailing';refuse(lambda changed=changed:tree_join(changed.__getitem__,set(changed),commit,1),'changed/trailing '+name)
for bad in ('.git/objects/info/alternates','.git/info/grafts','.git/shallow','.git/objects/pack/any','.git/refs/replace/any'):refuse(lambda bad=bad:tree_join(source.__getitem__,set(source)|{bad},commit,1),'external/rewrite '+bad)
refuse(lambda:tree_join(source.__getitem__,set(source),commit,2),'wrong complete count');refuse(lambda:tree_join(source.__getitem__,set(source),'f'*40,1),'wrong commit');refuse(lambda:tree_join(source.__getitem__,set(source),commit,1,limit=8),'compressed/inflate cap')
for mode,name in [('120000','body'),('160000','body'),('100644','../body'),('100644','a/body'),('100644','.')]:
 t=obj('tree',mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(blob));c=obj('commit',b'tree '+t.encode()+b'\n\nopaque\n');refuse(lambda c=c:tree_join(source.__getitem__,set(source),c,1),'bad mode/path '+mode+name)
# Material semantic completeness witnesses. No fake claim, live-source or Git API.
missingparent='f'*40;c=obj('commit',b'tree '+tree.encode()+b'\nparent '+missingparent.encode()+b'\nauthor O <o@invalid> 0 +0000\ncommitter O <o@invalid> 0 +0000\n\nmissing parent\n');check(tree_join(source.__getitem__,set(source),c,1)=={'body':('100644',blob)},'witness missing parent accepted');witnesses.append({'id':'SR1','case':'missing parent object','commit':c,'missing_parent':missingparent,'accepted':True,'impact':'Parser authenticates current tree only, not complete ancestry or failed claim source/design objects.'})
source['z']=source['a']=payload;t=obj('tree',b'100644 z\0'+bytes.fromhex(blob)+b'100644 a\0'+bytes.fromhex(blob));c=obj('commit',b'tree '+t.encode()+b'\n\nunsorted\n');check(set(tree_join(source.__getitem__,set(source),c,2))=={'z','a'},'witness noncanonical order accepted');witnesses.append({'id':'SR2','case':'unsorted Git tree z then a accepted','commit':c,'accepted':True,'impact':'No canonical Git tree ordering check; fixed known source hash prevents replacing actual source with this witness.'})
# Complete tiny owned R4 pipeline with all opaque loose objects, no actual Source restore.
root=H/'opaque-source';root.mkdir()
for name,body in source.items():p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
manifest=S.R.scan(root);packed=S.R.pack(root,manifest,H/'opaque.tar.gz');destination=H/'opaque-flat';S.reserve(destination);restored=S.R.restore(H/'opaque.tar.gz',packed,manifest,destination);meta=json.loads(S.R.read(destination,restored['metadata_file']));check(set(meta['flat_members'])==set(source),'complete opaque flat denominator')
for name,body in source.items():check(S.R.read(destination,meta['flat_members'][name])==body,'opaque fullflat '+name)
refuse(lambda:S.reserve(destination),'exclusive destination');link=H/'redirect';link.symlink_to(destination,target_is_directory=True);refuse(lambda:S.reserve(link/'fresh'),'redirected parent')
# Descriptor-owned reserve failure: injected mkdir fatal, real closes, later close error.
for prim in (MemoryError,SystemExit,ValueError):
 first=prim('owned mkdir failure');second=OSError('owned close failure');fds=[]
 def op(*a,**k):fd=os.open(*a,**k);fds.append(fd);return fd
 def cl(fd):os.close(fd);raise second
 def mkdir(*a,**k):raise first
 proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in ('O_RDONLY','O_DIRECTORY','O_NOFOLLOW','fstat','fsync')},open=op,close=cl,mkdir=mkdir);ns={'os':proxy,'R':S.R,'stat':stat};fn=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='reserve');exec(compile(ast.Module(body=[fn],type_ignores=[]),'<exact reserve>','exec'),ns)
 try:ns['reserve'](H/('never-created-'+prim.__name__))
 except BaseException as e:check(e is first if prim is not ValueError else isinstance(e,S.R._cleanup.__globals__['CleanupFailure']),'reserve firstfatal '+prim.__name__)
 else:raise AssertionError('reserve no error')
 check(all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in fds),'reserve all descriptors absent '+prim.__name__)
check(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no numeric imports')
out={'decision':'WITHHELD_FULL_ANCESTRY_SEMANTIC_CLAIM_SR1','checks':len(checks),'check_names':checks,'refusals':refusals,'witnesses':witnesses,'qualification':'Pinned actual source/capture bytes are not shown corrupt. Parser current commit/tree/blob joins pass; absent parent/source-design ancestry and canonical tree ordering semantics are separately not enforced. No actual Source recovery/remote/admission/native executed.'};(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('check_names','refusals')}))
