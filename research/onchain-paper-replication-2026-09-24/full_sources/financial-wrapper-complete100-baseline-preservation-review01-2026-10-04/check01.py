import hashlib,io,json,os,stat,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;ROOT=F.parents[2];C=F/'financial-wrapper-complete100-baseline-capture01-2026-10-04';P=F/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sys.path.insert(0,str(P));import recovery04 as R
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
raw=(C/'CAPTURE01.json').read_bytes();cap=json.loads(raw);ok(sha(raw)=='7d65c2bac832832df5d62d49a41b31b7d54b33b52a448d048cd94b9541f8a176','actual capture pin')
for n,h in [('recovery04.py','b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'),('owned_io.py','09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'),('bounded_git01.py','db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f')]:ok(sha((P/n).read_bytes())==h,'unchanged primitive '+n)
roles=[];manifests={}
def live_manifest(root,exclude_git=False):
 if not exclude_git:return R.scan(root)
 rows=[]
 for p in root.rglob('*'):
  rel=p.relative_to(root).as_posix()
  if rel.split('/')[0]=='.git':continue
  s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISDIR(s.st_mode):r['kind']='directory'
  else:ok(stat.S_ISREG(s.st_mode)and s.st_nlink==1,'live original plainfile '+rel);b=R.read(root,rel);r.update(kind='file',bytes=len(b),sha256=sha(b))
  rows.append(r)
 return {'schema_version':1,'root_mode':stat.S_IMODE(root.stat().st_mode),'members':sorted(rows,key=lambda x:x['path'])}
for role,s in cap['scopes'].items():
 mraw=(C/(role.upper()+'_MANIFEST01.json')).read_bytes();m=json.loads(mraw);manifests[role]=m;snap=Path(s['snapshot']);archive=(C/('complete-'+role+'01.tar.gz')).read_bytes();ok(sha(mraw)==s['manifest_sha256']and R.encode(m)==mraw,'canonical complete manifest '+role);ok(R.scan(snap)==m,'whole snapshot '+role)
 if 'origin'in s:ok(live_manifest(Path(s['origin']),s['git_directory_excluded'])==m,'whole actual current original '+role)
 ok(len(m['members'])==s['typed_members']and sum(r['kind']=='file'for r in m['members'])==s['regular_bodies']and sum(r.get('bytes',0)for r in m['members'])==s['regular_bytes'],'exact finite scope '+role)
 ok(sha(archive)==s['archive']['sha256']and len(archive)==s['archive']['bytes']<=R.FILE,'archive bounds+pin '+role)
 frames=list(R.framed_members(archive));ok(len(frames)==len(m['members']),'raw bounded framing member cardinality '+role)
 for (name,t,body),row in zip(frames,m['members']):
  ok(name==row['path']and t.mode==row['mode']and t.uid==t.gid==0 and t.uname==t.gname==''and t.mtime==0,'complete canonical TAR header '+role+'/'+name)
  ok(row['kind']=='directory'and t.isdir()and body==b''or row['kind']=='file'and t.isfile()and len(body)==row['bytes']and sha(body)==row['sha256'],'opaque archive body '+role+'/'+name)
 sink=io.BytesIO();R.tar_stream(snap,m,sink);ok(sink.getvalue()==archive,'whole exact canonical gzip recompression '+role);ok(R.scan(snap)==m,'snapshot stable after reencoding '+role)
 roles.append({'role':role,'members':len(m['members']),'files':s['regular_bodies'],'body_bytes':s['regular_bytes'],'archive_sha256':sha(archive),'archive_bytes':len(archive),'manifest_sha256':sha(mraw)})
# Whole four original review roots and seven named Root receipts, no copied-path substitution.
origins=json.loads(R.read(C/'support-snapshot','SUPPORT_ORIGINS01.json'));ok(len(origins)==4,'exact four original support roots')
for label,row in origins.items():
 root=Path(row['origin']);ok(R.scan(root)==row['manifest']==R.scan(C/'support-snapshot'/label),'full support original-current-copy equality '+label)
rootreceipts=C/'support-snapshot/root-receipts';names=sorted(p.name for p in rootreceipts.iterdir());ok(len(names)==7,'seven exact Root receipts')
for n in names:
 original=F/'heartbeat-root-checkpoint10-2026-10-04'/n;copy=rootreceipts/n;ok(original.read_bytes()==copy.read_bytes()and stat.S_IMODE(original.stat().st_mode)==stat.S_IMODE(copy.stat().st_mode),'actual Root receipt original '+n)
# Complete original reachable Git objects. No reconstruction or writes to Git.
S=Path(cap['scopes']['capsule']['origin']);env=dict(os.environ);env['GIT_NO_REPLACE_OBJECTS']='1';calls=[]
def git(args,data=None,limit=16*1024**2):
 p=subprocess.run(['git','--no-replace-objects','-C',str(S),*args],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=15)
 ok(p.returncode==0 and not p.stderr and len(p.stdout)<=limit,'bounded local Git '+args[0]);calls.append({'args':args,'exit':p.returncode,'stdout_sha256':sha(p.stdout),'bytes':len(p.stdout)});return p.stdout
ok(git(['rev-parse','HEAD']).decode().strip()==cap['source'],'current source9dc5')
indexraw=(C/'GIT_OBJECTS01.json').read_bytes();censusraw=(C/'GIT_CENSUS01.json').read_bytes();index=json.loads(indexraw);census=json.loads(censusraw);ok(sha(indexraw)==cap['git_object_index_sha256']and sha(censusraw)==cap['git_object_census_sha256'],'literal object index/census pins');objs=index['reachable_objects'];oids=[r['git_object']for r in objs];ok(oids==sorted(set(oids))and len(oids)==385,'385 sorted unique objects')
reachable=git(['rev-list','--objects',cap['source']]);ok(sorted({x.split()[0].decode()for x in reachable.splitlines()})==oids,'ALL actual reachable object identity set')
actual=git(['cat-file','--batch'],(''.join(oid+'\n'for oid in oids)).encode());offset=0;total=0;bodies={}
for row in objs:
 end=actual.index(b'\n',offset);oid,kind,size=actual[offset:end].decode().split();n=int(size);b=actual[end+1:end+1+n];ok(actual[end+1+n:end+2+n]==b'\n','Git batch framing '+oid);offset=end+2+n;ok(oid==row['git_object']and kind==row['kind']and n==row['bytes'],'actual object type extent '+oid);ok(hashlib.sha1(kind.encode()+b' '+str(n).encode()+b'\0'+b).hexdigest()==oid and sha(b)==row['sha256'],'actual Git object OID+SHA '+oid);ok(R.read(C/(row['scope']+'-snapshot'),row['path'])==b,'whole preserved original Git body '+oid);bodies[oid]=(kind,b);total+=n
ok(offset==len(actual)and total==7807097==index['object_body_bytes']==census['actual_object_body_bytes'],'entire Git stream no extra+total')
ok([{k:r[k]for k in ('bytes','git_object','kind')}for r in objs]==census['reachable_objects'],'complete original census index join')
# Deterministic sorted 3MiB logical partition including whole indivisible bodies.
partition=1;used=0;counts={}
for r in objs:
 if used+r['bytes']>3*1024**2:partition+=1;used=0
 ok(r['scope']=='git'+str(partition),'deterministic Git body partition '+r['git_object']);used+=r['bytes'];counts[r['scope']]=counts.get(r['scope'],0)+1
ok(counts=={'git1':212,'git2':53,'git3':120},'deterministic212+53+120')
# Parse authentic current commit/tree bytes directly, with no new Git store.
commitbody=bodies[cap['source']][1];treeoid=next(x[5:].decode()for x in commitbody.splitlines()if x.startswith(b'tree '));tracked={}
def visit(oid,prefix):
 kind,body=bodies[oid];ok(kind=='tree','reachable actual tree '+oid);i=0
 while i<len(body):
  sp=body.index(b' ',i);nul=body.index(b'\0',sp);mode=body[i:sp].decode();name=body[sp+1:nul].decode();child=body[nul+1:nul+21].hex();i=nul+21;path=prefix+name
  if mode=='40000':visit(child,path+'/')
  else:ok(mode in ('100644','100755')and bodies[child][0]=='blob','tree plain blob '+path);tracked[path]=(mode,child)
visit(treeoid,'');ok(len(tracked)==339,'authentic current tree339')
capby={r['path']:r for r in manifests['capsule']['members']}
for path,(mode,oid)in tracked.items():ok(bodies[oid][1]==R.read(C/'capsule-snapshot',path)and bool(capby[path]['mode']&0o111)==(mode=='100755'),'current tree ↔ complete capsule bytes/mode '+path)
parent=C/'parent-snapshot';draft=json.loads(R.read(parent,'REQUEST_DRAFT01.json'));ok(draft['source']==draft['design_source']==cap['source']and draft['final_review']is None and draft['proofs']['full_recovery']is None and draft['status']=='DRAFT_NOT_RELEASED','honest draft unresolved final/recovery')
ok(sha(R.read(parent,'parent01.py'))==draft['caller_sha256']=='7f28cee688b661584e57466838ecdb79f0e17aa52be7d6f2c04f374326de9fb3','actual Parent7f28')
for n,pin in draft['helper_hashes'].items():ok(sha(R.read(parent,n))==pin,'exact Parent helper '+n)
ok(len(draft['source_files'])==338 and len(draft['input_hashes'])==8 and len(draft['runtime_mapping']['distribution_records'])==251,'338/eight/251metadata denominators')
for n,h in draft['source_files'].items():ok(sha(R.read(C/'capsule-snapshot',n))==h,'draft complete source body '+n)
required=json.loads((C/'REQUIRED_BODIES01.json').read_bytes());ok(len(required)==16 and sum(x['bytes']for x in required.values())==5316791,'exact16/5316791 required transport bodies')
for n,r in required.items():b=(ROOT/n).read_bytes();ok(len(b)==r['bytes']and sha(b)==r['sha256']and len(b)<=R.FILE,'required current body '+n)
ok(not cap['actual_external_recovery']and not cap['final_request_or_release_captured'],'capture limits honest')
ok(not any(x in sys.modules for x in ('numpy','torch','scipy')),'no numerical imports');ok(git(['rev-parse','HEAD']).decode().strip()==cap['source'],'source unchanged at end')
(D/'READBACK01.json').write_bytes(R.encode({'checks':len(checks),'checks_detail':checks,'roles':roles,'git_calls':calls,'git_objects':385,'git_object_bytes':total,'git_partition_counts':counts,'source':cap['source'],'capture_sha256':sha(raw),'actual_external_recovery':False,'actual_git_reconstruction':False,'final_request_release_present':False,'root_receipts':names}));print(json.dumps({'checks':len(checks),'scope_count':len(roles),'git_objects':385,'canonical_archives':6}))
