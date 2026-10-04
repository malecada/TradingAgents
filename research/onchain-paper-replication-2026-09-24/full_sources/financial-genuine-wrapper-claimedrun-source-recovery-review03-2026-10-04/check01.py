import ast,hashlib,importlib.util,json,os,stat,sys,zlib
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;P=B/'financial-genuine-wrapper-claimedrun-source-recovery-preparation03-2026-10-04';O=B/'financial-genuine-wrapper-claimedrun-source-recovery-preparation02-2026-10-04';W=B/'financial-genuine-wrapper-claimedrun-source-recovery-review02-2026-10-04';checks=[];outcomes=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(f,n,reason):
 try:f()
 except ValueError as e:check(str(e)==reason,n);outcomes.append({'case':n,'refused':str(e)})
 else:raise AssertionError('not refused '+n)
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=json.loads((P/'MANIFEST01.json').read_bytes());check(sha((P/'MANIFEST01.json').read_bytes())=='8ae5ecff843ea2bec4960d88ed9314f8cbd06cfe5c32efb11b430079cc0ecf79','exact author manifest');actual=[]
def scan(p):
 for q in p.iterdir():
  actual.append(q.relative_to(P).as_posix())
  if stat.S_ISDIR(q.lstat().st_mode):scan(q)
scan(P);check(set(actual)=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'complete author witness evidence')
for r in m['members']:
 p=P/r['path'];s=p.lstat();check(oct(stat.S_IMODE(s.st_mode))==r['mode'],'mode '+r['path'])
 if r['kind']=='file':check(stat.S_ISREG(s.st_mode) and len(p.read_bytes())==r['bytes'] and sha(p.read_bytes())==r['sha256'],'body '+r['path'])
 elif r['kind']=='symlink':check(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'literal link')
 else:check(stat.S_ISDIR(s.st_mode),'directory')
newraw=(P/'git_objects01.py').read_bytes();oldraw=(O/'git_objects01.py').read_bytes();check(sha(newraw)=='c364269be9c112dbc9501a41c8f9cf21def9a95b33cf2b9054f4384ae3888a4a','exact Git helper');before=b'depth<=128 and len(self.state)<=1024';after=b'depth<=128 and (oid in self.state or len(self.state)<1024)';check(newraw.count(after)==1 and newraw.replace(after,before)==oldraw,'single predicate complete byte inverse');check(ast.dump(ast.parse(newraw.replace(after,before)))==ast.dump(ast.parse(oldraw)),'full helper AST inverse')
restore=(P/'restore01.py').read_bytes();check(sha(restore)=='9e21e92ca69fad038dc77324b8fcc9f7600380293e55a90b7c0fd5b8ae95c1fc','exact adapter');back=restore.replace(sha(newraw).encode(),sha(oldraw).encode());check(back==(O/'restore01.py').read_bytes(),'adapter only exact helper hash delta');check(ast.dump(ast.parse(back))==ast.dump(ast.parse((O/'restore01.py').read_bytes())),'adapter AST inverse')
for n in ('recovery04.py','owned_io.py','bounded_git01.py','CAPTURE_PINS01.json','REQUEST_TEMPLATE01.json'):check((P/n).read_bytes()==(O/n).read_bytes(),'unchanged '+n)
old=module('oldgit',O/'git_objects01.py');new=module('newgit',P/'git_objects01.py');data={p.relative_to(W/'opaque-objects').as_posix():p.read_bytes() for p in (W/'opaque-objects').rglob('*') if p.is_file()};oid='534e8a76252e2bbf8aa35a6180303e2db522be42';a=old.RecoveredGit(data.__getitem__,set(data));a.ancestry(oid);check(len(a.commits)==1025,'actual prior witness RED1025');b=new.RecoveredGit(data.__getitem__,set(data));refuse(lambda:b.ancestry(oid),'same witness GREEN1025 refusal','finite ancestry');check(len(b.state)==1024 and len(b.commits)==1023,'no1025state inserted on refusal')
# Genuine SHA1-valid opaque boundary graph, changing parent count only.
raw=zlib.decompress(data['.git/objects/'+oid[:2]+'/'+oid[2:]]).split(b'\0',1)[1];headers,message=raw.split(b'\n\n',1);lines=headers.split(b'\n');parents=[x for x in lines if x.startswith(b'parent ')];check(len(parents)==1024,'exact original1024parents');kept=[];removed=False
for line in lines:
 if line==parents[-1] and not removed:removed=True;continue
 kept.append(line)
value=b'\n'.join(kept)+b'\n\n'+message;body=b'commit '+str(len(value)).encode()+b'\0'+value;boundary=hashlib.sha1(body).hexdigest();compressed=zlib.compress(body);key='.git/objects/'+boundary[:2]+'/'+boundary[2:];data[key]=compressed;(H/'boundary-commit.zlib').write_bytes(compressed)
c=new.RecoveredGit(data.__getitem__,set(data));root=c.ancestry(boundary);check(len(c.state)==len(c.commits)==1024,'exact1024 accepts');check(c.ancestry(boundary) is root and len(c.state)==1024,'completed root cache hit atcapacity');parent=parents[0][7:].decode();check(c.ancestry(parent) is c.commits[parent] and len(c.state)==1024,'completed ancestor cache hit atcapacity');missing=parents[-1][7:].decode();check(missing not in c.state,'fresh rejected node actually absent before');refuse(lambda:c.ancestry(missing),'fresh state aftercapacity refuses','finite ancestry');check(missing not in c.state and len(c.state)==1024,'freshrefusal leaves no state');saved=c.state[parent];c.state[parent]=1;refuse(lambda:c.ancestry(parent),'existing cycle atcapacity retains distinct diagnostic','commit cycle');c.state[parent]=saved;check(c.ancestry(parent) is c.commits[parent],'cache restored after isolated cycle control');refuse(lambda:c.ancestry(boundary,depth=129),'depth129 cache stillrefuses','finite ancestry');check(c.ancestry(boundary,depth=128) is root,'depth128 cached boundary passes')
check(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no numericalimports')
out={'decision':'ACCEPTED_SOURCE_ONLY_STRICT1024_CORRECTION','checks':len(checks),'check_names':checks,'outcomes':outcomes,'original1025_commit':oid,'new1024_boundary_commit':boundary,'old1025_accepted':True,'new1025_refused_before_extra_state':True,'new1024_accepted':True,'existing_done_and_cycle_atcapacity_checked':True,'complete_byte_AST_inverse':True,'actual_SourceGit_decode':False,'actual747restore':False,'actual_remote':None,'actual_release':None};(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('check_names','outcomes')}))
