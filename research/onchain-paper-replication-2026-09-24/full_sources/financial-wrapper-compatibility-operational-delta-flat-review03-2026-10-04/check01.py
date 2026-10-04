import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
P=Path(__file__).absolute().parent;B=P.parent;A=B/'financial-wrapper-compatibility-operational-delta-flat-successor03-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
new=load('flat_review03',P/'restore01.py');old=load('flat_review02',P/'ORIGINAL_restore01.py');R=new.R;checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n);(P/'PROGRESS01.json').write_text(json.dumps(checks,indent=2)+'\n')
manifest=json.loads((A/'MANIFEST01.json').read_bytes());actual=[]
def walk(p):
 for q in p.iterdir():
  rel=q.relative_to(A).as_posix()
  if rel in ('MANIFEST01.json','SEAL01.out','SEAL01.err'):continue
  actual.append(rel)
  if stat.S_ISDIR(q.lstat().st_mode):walk(q)
walk(A);ck('full-author-population',set(actual)=={r['path'] for r in manifest['members']})
for row in manifest['members']:
 p=A/row['path'];s=p.lstat();ck('mode:'+row['path'],stat.S_IMODE(s.st_mode)==row['mode'])
 if row['kind']=='file':ck('body:'+row['path'],s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'])
 elif row['kind']=='directory':ck('directory:'+row['path'],stat.S_ISDIR(s.st_mode))
 elif row['kind']=='symlink':ck('link:'+row['path'],os.readlink(p)==row['target'])
 else:ck('typed-special:'+row['path'],not stat.S_ISREG(s.st_mode))
ck('exact03source',sha((P/'restore01.py').read_bytes())=='6d7688080efb716b7a79d1291b4f27e62e0315e5d7a8153b2890d1f9fab35214')
for name,pin in new.PINS.items():ck('actualdependency:'+name,sha((P/name).read_bytes())==pin)
ck('watch-independent-review',sha((B/'financial-wrapper-operational-forensic-watch-review04-2026-10-04/MANIFEST01.json').read_bytes())=='7a94ef046588cb9a10a978d63865302e0b12a25e60db98190aea9927ecc59f47')
ck('bounds-unchanged',(new.LOGICAL,new.ALLOCATION,new.REQUIRED,new.W.POLICY)==(old.LOGICAL,old.ALLOCATION,old.REQUIRED,old.W.POLICY))
bundle=B/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04';failed=B/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';cap,man=new.load_capture(bundle);fc,fm=new.load_failed_capture(failed)
O=P/'owned01';O.mkdir(mode=0o700)
stable=O/'stable';stable.mkdir(mode=0o700)
def boundary():new.W.census(stable)
r1=new.restore_delta(bundle,cap,man,stable,boundary);r2=new.restore_failed_delta(failed,fc,fm,stable,boundary);cohort=new.VerifiedCohort()
new.verify_flat(stable/new.OUTPUT,r1,cap,man,boundary,cohort);new.verify_flat(stable/new.FAILED_OUTPUT,r2,fc,fm,boundary,cohort);cohort.check()
ck('genuine-both-local-canonical-roundtrip',r1['regular_bodies']==33 and r2['regular_bodies']==31 and len(list((stable/new.OUTPUT).iterdir()))+len(list((stable/new.FAILED_OUTPUT).iterdir()))==66)
results=[]
def mutate(path,kind,root):
 if kind in ('bytes','cross-scope','metadata'):
  raw=path.read_bytes();path.write_bytes(bytes([raw[0]^1])+raw[1:]);s=path.stat();os.utime(path,ns=(s.st_atime_ns,s.st_mtime_ns+1000000000))
 elif kind=='mode':os.chmod(path,0o644)
 else:(root/'foreign.body').write_bytes(b'owned extra')
def witness(module,kind,label):
 root=O/label;root.mkdir(mode=0o700);d=root/'flat';d.mkdir(mode=0o700);r=R.restore(failed/'failed-remote02.tar.gz',fc['archive'],fm,d);md=json.loads((d/r['metadata_file']).read_bytes());files=list(md['flat_members'].values());target=d/files[0]
 if kind=='metadata':target=d/r['metadata_file']
 c=module.VerifiedCohort() if hasattr(module,'VerifiedCohort') else None
 if kind=='cross-scope':
  earlier=root/'earlier';earlier.mkdir(mode=0o700);rr=R.restore(bundle/'operational-delta01.tar.gz',cap['archive'],man,earlier);em=json.loads((earlier/rr['metadata_file']).read_bytes());target=earlier/next(iter(em['flat_members'].values()))
  if c:module.verify_flat(earlier,rr,cap,man,lambda:new.W.census(root),c)
  else:module.verify_flat(earlier,rr,cap,man,lambda:new.W.census(root))
 last=d/files[-1];inode=last.stat().st_ino;realclose=R.os.close;fired=False;closed=[]
 def close(fd):
  nonlocal fired
  match=os.fstat(fd).st_ino==inode;realclose(fd);closed.append(fd)
  if match and not fired:fired=True;mutate(target,kind,d)
 R.os.close=close;error=None
 try:
  if c:module.verify_flat(d,r,fc,fm,lambda:new.W.census(root),c)
  else:module.verify_flat(d,r,fc,fm,lambda:new.W.census(root))
 except BaseException as e:error=type(e).__name__
 finally:R.os.close=realclose
 ck('actual-close-fired:'+label,fired)
 for fd in set(closed):
  try:os.fstat(fd)
  except OSError:pass
  else:raise AssertionError('open fd')
 return {'label':label,'kind':kind,'error':error,'closed':len(closed),'original_first_object':fm['members'][0]['path']}
for kind in ('bytes','mode','foreign','metadata','cross-scope'):
 a=witness(old,kind,'old-'+kind);b=witness(new,kind,'new-'+kind);results.extend((a,b));ck('RED-GREEN:'+kind,a['error'] is None and b['error']=='ValueError')
ck('noNUM',not any(n.split('.')[0] in ('numpy','torch','scipy','pandas') for n in sys.modules))
(P/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'real_witness_pairs':results,'actual_two_local_archives':[r1,r2],'no_actual_remote_receipt_or_success_fabricated':True,'public_entry_not_executed':True},indent=2)+'\n');print(json.dumps({'checks':len(checks),'status':'PASS_SOURCE_CONTROLS'}))
