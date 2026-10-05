"""Read-only exact closed capture verifier. Stdlib; no restoration or research entry."""
from pathlib import Path
import hashlib,json,os,stat,sys,time,importlib.util
HERE=Path(__file__).resolve().parent
F=HERE.parent; MAIN=F.parents[2]
PREP=F/'financial-wrapper-compatibility-complete100-outcome-capture-preparation03-2026-10-05'
D=F/'financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05'
C=F/'heartbeat-root-checkpoint10-2026-10-04'
PINS={'recovery_pax01.py':'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for n,h in PINS.items():
 p=PREP/'utilities'/n;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4194304
 assert hashlib.sha256(p.read_bytes()).hexdigest()==h
sys.path.insert(0,str(PREP/'utilities'));import recovery_pax01 as R
class Reader:
 def __init__(self):self.pins={};self.trees={};self.total=0;self.start=time.monotonic();self.checks=0
 def need(self,v,msg):
  self.checks+=1
  if not v:raise ValueError(msg)
 def tick(self):self.need(time.monotonic()-self.start<180 and self.total<=512*1024**2 and len(self.pins)<=32768,'finite reviewer read budget')
 def pin(self,p):
  self.tick();p=Path(p);s=p.lstat();self.need(p.resolve(strict=True)==p and (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=R.FILE),'ordinary canonical member');v=R.sig(s)+(s.st_uid,s.st_gid,s.st_blocks)
  self.need(p not in self.pins or self.pins[p]==v,'retained earliest signature changed');self.pins.setdefault(p,v);return v
 def read(self,p,h=None):
  p=Path(p);before=self.pin(p);b=R.read(p.parent,p.name);self.need(self.pin(p)==before,'read cleanup changed member');self.total+=len(b);self.tick()
  if h:self.need(R.digest(b)==h,'exact body pin: '+str(p))
  return b
 def tree(self,root,m,exclude=()):
  root=Path(root);R.validate(m);self.pin(root);seen=[]
  self.need(stat.S_IMODE(root.lstat().st_mode)==m['root_mode'],'original root mode')
  def visit(p,rel):
   self.pin(p);it=None;names=[];primary=None
   try:
    it=os.scandir(p)
    for e in it:self.tick();names.append(e.name);self.need(len(names)+len(seen)<=32768,'bounded namespace')
   except BaseException as e:primary=e
   R._cleanup(() if it is None else (it.close,),primary=primary)
   if primary is not None:raise primary
   self.pin(p);self.trees[p]=tuple(sorted(names))
   for n in sorted(names):
    if not rel and n in exclude:continue
    name=n if not rel else rel+'/'+n;R.path_name(name);q=root/name;v=self.pin(q);s=q.lstat();r={'path':name,'kind':'directory' if stat.S_ISDIR(s.st_mode) else 'file','mode':stat.S_IMODE(s.st_mode)}
    if r['kind']=='file':r['bytes']=s.st_size
    seen.append(r)
    if r['kind']=='directory':visit(q,name)
  visit(root,'');expected=[{k:v for k,v in r.items() if k!='sha256'} for r in m['members']]
  self.need(sorted(seen,key=lambda r:r['path'])==expected,'exact complete original namespace/type/mode/extent')
 def finish(self):
  for p,names in self.trees.items():
   it=None;primary=None;actual=[]
   try:
    it=os.scandir(p)
    for e in it:self.tick();actual.append(e.name)
   except BaseException as e:primary=e
   R._cleanup(() if it is None else (it.close,),primary=primary)
   if primary is not None:raise primary
   self.need(tuple(sorted(actual))==names,'terminal namespace changed')
  for p,v in self.pins.items():self.need(self.pin(p)==v,'terminal sampled signature changed')
  self.tick()
def verify_piece(rd,archive_path,manifest_path,piece,originals,copyroot=None):
 mr=rd.read(manifest_path,piece['archive_pin']['manifest_sha256']);m=json.loads(mr);R.validate(m)
 expected={b['member']:b for b in piece['bodies']};rd.need(len(expected)==len(piece['bodies']) and len(expected)<=256,'piece complete unique members')
 rd.need(m=={'schema_version':1,'root_mode':448,'members':[{'path':n,'kind':'file','mode':384,'bytes':b['bytes'],'sha256':b['sha256']} for n,b in sorted(expected.items())]},'exact canonical private piece manifest')
 ar=rd.read(archive_path,piece['archive_pin']['sha256']);rd.need(len(ar)==piece['archive_pin']['bytes'],'archive extent');rd.need(sum(b['bytes'] for b in expected.values())<=3*1024**2,'piece whole-body bound')
 if copyroot:rd.tree(copyroot,m)
 seen=set();it=R.framed_members(ar);primary=None
 try:
  for n,t,b in it:
   rd.need(n in expected and n not in seen,'archive exact nonduplicate names');row=expected[n];seen.add(n)
   rd.need(t.isfile() and t.mode==384 and t.uid==t.gid==0 and t.uname==t.gname=='' and t.mtime==0 and t.size==len(b)==row['bytes'] and R.digest(b)==row['sha256'],'exact opaque TAR metadata/body')
   if copyroot:rd.need(rd.read(copyroot/n,row['sha256'])==b,'actual retained private body')
   origin=originals[(row['role'],row['path'])];rd.need(rd.read(origin,row['sha256'])==b,'actual original recovered byte join')
 except BaseException as e:primary=e
 R._cleanup((it.close,),primary=primary)
 if primary is not None:raise primary
 rd.need(seen==set(expected),'all piece bodies present')
 if copyroot:
  sink=R.Sink();R.tar_stream(copyroot,m,sink);rd.need(sink.count==len(ar) and sink.hash.hexdigest()==R.digest(ar),'literal canonical PAX gzip recompression')
 return len(seen)
def main():
 rd=Reader();raw=rd.read(D/'CAPTURE01.json','ef82889318080bf2fec673d6c558c4afe3d95260c1a4d783c9b5eb16d8979442');c=json.loads(raw)
 rd.need(c['kind']=='complete-terminal-opaque-sharded-capture-v1' and c['numerical_authority'] is False and c['POSIX_instantiation'] is False and c['exclusions']=={'capsule':['.git'],'parent':[]},'honest captured scope')
 roots={'capsule':Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source'),'parent':Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')}
 originals={};original_rows={}
 for role,v in c['originals'].items():
  rd.need(role in roots and v['root']==str(roots[role]),'fixed actual root');rd.tree(roots[role],v['manifest'],('.git',) if role=='capsule' else ())
  for row in v['manifest']['members']:
   if row['kind']=='file':originals[role,row['path']]=roots[role]/row['path'];original_rows[role,row['path']]=(row['bytes'],row['sha256'])
 mapped={}
 for i,p in enumerate(c['pieces']):
  rd.need(p['id']==i and p['archive']=='piece-%03d.tar.gz'%i and p['manifest']=='piece-%03d.json'%i,'exact26 fixed piece names')
  for b in p['bodies']:
   k=b['role'],b['path'];rd.need(k not in mapped,'no duplicated original');mapped[k]=(b['bytes'],b['sha256'])
 rd.need(len(c['pieces'])==26 and mapped==original_rows and len(mapped)==845 and sum(v[0] for v in mapped.values())==77970429 and sum(len(v['manifest']['members']) for v in c['originals'].values())==1074,'complete845/1074 original denominator')
 n=sum(verify_piece(rd,D/p['archive'],D/p['manifest'],p,originals,D/('piece-%03d'%p['id'])) for p in c['pieces']);rd.need(n==845,'all archive bodies checked')
 refs={
 'root_exit':C/'COMPATIBLE100_CAPTURE01_ACTUAL_ROOT_EXIT.json',
 'request':C/'COMPATIBLE100_CAPTURE_REQUEST01.json',
 'release':F/'financial-wrapper-compatibility-complete100-capture-entry-review03-2026-10-05/CAPTURE_ENTRY_RELEASE01.json',
 'outcome':F/'financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/MACHINE01.json',
 'cleanup':F/'financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/CLEANUP_PROOF01.json',
 'Git407_basis':F/'financial-wrapper-compatibility-baseline-recovery-review02-2026-10-05/BASELINE_FULL_RECOVERY_PROOF01.json'}
 hashes={'request':'c1d0c90db757e80e4dbcb66491575435f21022445344f98ec6bb02103c7642d7','release':'beafb55555a322404c9d43682394f37b4b4e1739de87f11774e3f02a885812a7','outcome':'27e29cab0b784748bdd0fef2ca484215b39b2b025784a469de443f619ae9b124','cleanup':'67d74e5ac68b9957f5e116753730eb698d6167141f0d61dfda558dd424e69e23','Git407_basis':'02900ae11c7053a5f691ef2838fa7427b5befd86778331c19b97143e1c6c2e48'}
 bodies={k:rd.read(p,hashes.get(k)) for k,p in refs.items()};exit=json.loads(bodies['root_exit'])
 rd.need(exit['actual_root_exit']==0 and exit['capture_sha256']==R.digest(raw) and exit['pieces']==26 and exit['opaque_original_files']==845 and exit['original_typed']==1074 and exit['raw_bytes']==77970429 and exit['request']==hashes['request'] and exit['release']==hashes['release'] and exit['source']=='d8b61b8bc45e69da0df50bfa4694c0c0d103aaa5dce6668fccd0686c275958bb','actual Root outcome literal joins')
 head=rd.read(roots['capsule']/'.git/HEAD').decode().strip()
 commit=rd.read(roots['capsule']/'.git'/head.removeprefix('ref: ')).decode().strip() if head.startswith('ref: ') else head
 rd.need(commit=='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41','actual unchanged accepted source')
 rd.finish()
 result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_LOCAL_COMPLETE_OUTCOME_CAPTURE_ONLY','capture_sha256':R.digest(raw),'source':commit,'pieces':26,'original_files':845,'original_typed':1074,'raw_bytes':77970429,'archive_bytes':sum(p['archive_pin']['bytes'] for p in c['pieces']),'literal_PAX_recompression':True,'all_original_modes_and_bytes_joined':True,'Git407':'accepted immutable separate baseline; not reconstructed in this review','refs':{k:{'path':str(p),'sha256':R.digest(bodies[k]),'bytes':len(bodies[k])} for k,p in refs.items()},'checks':rd.checks,'read_bytes':rd.total,'elapsed_seconds':time.monotonic()-rd.start,'sampled_currentness_only':True,'universal_process_history':None,'external_recovery_accepted':False,'numerical_authority':False}
 out=HERE/'CAPTURE_READBACK01.json';out.write_bytes(R.encode(result));print(json.dumps({'decision':result['decision'],'checks':rd.checks,'read_bytes':rd.total,'elapsed_seconds':result['elapsed_seconds'],'sha256':R.digest(out.read_bytes())}))
if __name__=='__main__':main()
