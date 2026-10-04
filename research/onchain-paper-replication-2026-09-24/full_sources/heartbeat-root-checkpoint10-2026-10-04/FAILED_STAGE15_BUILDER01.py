import datetime,gzip,hashlib,importlib.util,io,json,os,stat,subprocess,sys,tarfile
from pathlib import Path
M=Path.cwd();S=M/'research/onchain-paper-replication-2026-09-24';B=S/'full_sources';C=B/'heartbeat-root-checkpoint10-2026-10-04'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='2ac9383c2086003e27f28391340832184f9a7221'
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
T=B/'financial-genuine-wrapper-recordfix-final-union-capture-review01-2026-10-04';assert hashlib.sha256((T/'MANIFEST02.json').read_bytes()).hexdigest()=='2c7048e0515841ef31e5f7a5a69b3b43aca46e748e3a91c610f1d175b64883e0'
D=B/'financial-genuine-wrapper-root-recordfix-final-review-snapshot01-2026-10-04';assert not D.exists();D.mkdir();rows=[];total=0
P=B/'held-consumer-final-recovery-preparation04-2026-10-03';sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('stage15_r4',P/'recovery04.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
assert hashlib.sha256((P/'recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
def inventory():
 out=[]
 def visit(p,n):
  nonlocal total
  before=R.sig(p.lstat());r={'path':n,'mode':stat.S_IMODE(p.lstat().st_mode)}
  if p.is_symlink():r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(p.lstat().st_mode):
   r['kind']='directory';out.append(r)
   for child in sorted(p.iterdir(),key=lambda x:x.name):visit(child,child.name if n=='.' else n+'/'+child.name)
   assert R.sig(p.lstat())==before
   return
  else:
   raw=R.read(T,n);total+=len(raw);assert total<=64*1024**2;r.update(kind='file',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
  assert R.sig(p.lstat())==before;out.append(r)
 visit(T,'.');return sorted(out,key=lambda r:r['path'])
rows=inventory();mapping={'schema_version':1,'original_root':str(T),'original_review_manifest_sha256':'2c7048e0515841ef31e5f7a5a69b3b43aca46e748e3a91c610f1d175b64883e0','members':rows,'links_followed_or_extracted':False};R.put(D/'manifest.json',mapping)
buffer=io.BytesIO();gz=gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0,filename='');tf=tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT)
try:
 for r in rows:
  if r['path']=='.':continue
  t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
  if r['kind']=='directory':t.type=tarfile.DIRTYPE;tf.addfile(t)
  elif r['kind']=='lexical-symlink':t.type=tarfile.SYMTYPE;t.linkname=r['target'];tf.addfile(t)
  else:
   raw=R.read(T,r['path']);assert hashlib.sha256(raw).hexdigest()==r['sha256'];t.size=len(raw);tf.addfile(t,io.BytesIO(raw))
finally:R._cleanup((tf.close,gz.close))
archive=buffer.getvalue();assert len(archive)<=4*1024**2
with R.new_file(D/'review.tar.gz') as fd:
 offset=0
 while offset<len(archive):n=os.write(fd,archive[offset:]);assert n>0;offset+=n
 os.fsync(fd)
total=0;assert inventory()==rows
R.put(D/'AUTHENTICATION01.json',{'schema_version':1,'archive_sha256':hashlib.sha256(archive).hexdigest(),'archive_bytes':len(archive),'manifest_sha256':hashlib.sha256((D/'manifest.json').read_bytes()).hexdigest(),'original_review_manifest_sha256':mapping['original_review_manifest_sha256'],'typed_members_including_root':len(rows),'regular_bodies':sum(r['kind']=='file' for r in rows),'literal_links':sum(r['kind']=='lexical-symlink' for r in rows),'actual_external_recovery':False,'links_followed_or_extracted':False,'native_or_numerical_started':False})
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
top=f'''# Current execution checkpoint — October 4, 2026

**TOP {stamp}: the final released caller, concrete verifier and complete applicable witness trees were captured successfully and independently accepted. Final external and flat recovery is the next step; no native numerical job or paper fit is active.** The last confirmed Main/remote origin is2ac9383c2086003e27f28391340832184f9a7221. Current receipts are local pending this commit.

The concrete verifier02eb149a/bindinge3557a48 was accepted by different-author reviewc856494d after467 checks against actual final request28f2ae53, Parent82d79e1a, release550a5a54 and current Source649. Actual final union capture03 1fd5699e ran ONCE: session23613/start42e314/completionc071a7 exit0. Actual parent PID305468/ticks14723198 was observed before same-PID exec and is absent. Full11 original trees306nodes/275bodies3,764,962B were recovered into307 ordinary nodes/276bodies3,853,463B including exact original mode/path metadata. Archive441fe2bb20203213d72fac1d2b0b59e1ada3c8a608bf1a5474a02464a0214237 is952,348B; manifesta76f2b4e/auth68a08e81. Different-author actual acceptance2c7048e0/5e0fadf4 passed5,111 actual plus646 source checks, including exact canonical recompression, complete original Parent and verifier witness namespaces, actual request/proofs/binding and unchanged Source986/713. Original capture01 CF1 late-extra omission and02 CF2 fatal masking were withheld before execution; their exact bodies, real review witnesses and corrected03 inverse are retained. Original group-history completeness and earlier Source capture PID history remain unavailable.

Actual corrected Source325 full external/flat recovery542af8a9/f86497ee remains accepted. The current final supplement includes complete installed Parent, Root adoption, final release review, concrete generated verifier and review, original caller and verifier source/witness trees, and binder preparation/review. The capture-review snapshot preserves every new witness body and ten literal link records without following or extracting links. This remains byte preservation; no installed-runtime body recovery, POSIX instantiation, empirical result or capacity follows.

Final-union flat adapter2bda6b41/preparation4cdd415f is source acceptedc8de8680/e2b8f329 after133 independent checks and four real reservation descriptor controls. Its original reviewer masking expectation was disproved by actual owned_io implicit sys.exception(); original failed harness and corrected controls remain. Root copied accepted remote0b397ccd byte-identically into a fresh final-remote namespace; no new transport algorithm or network operation has run. Next: commit/push and authenticate the complete bounded selection; independently verify every selected archive/witness; ONE fresh remote recovery; genuine exact final flat request/release; ONE full276-body recovery and independent final Source+caller+review union acceptance. Fresh source/runtime/process/namespace/native/resource eligibility then precedes at most ONE fixed financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01 engineering case. A planned failed checkpoint must remain failed and spent and be fully preserved/reviewed/recovered before dependent work.

Current read-only observation033c7095/537f28: MemAvailable7,418,343,424B, disk18,356,142,080B, zero exact capsule jobs and all fresh case/Parent attempt namespaces absent. This is not a release or whole-fit capacity proof. All1,420 paper financial fits remain pending525BTC895ETH,45initial included. Paper36closed27COMPLETE9FAILED/highest64/no65/coverage77of109/resource7COMPLETE102UNAVAILABLE; original import5FAILED/highest6/unusedslot6 untransferred; neural04permanentFAILED3.75GiB/all9unavailable; tinyouterFAILED/3realcomponentspassed3,823bitwise; coldtwoexhausted remain unchanged. Engineering numerical18/prior0/claims0 and19 operational definitions including unavailable oldouter remain distinct, no refund/transfer/amendment to19. All13tasks/C01–C18/original32motifs512spent/full motif dictionary→MCM→GAT→attention LSTM/bothassets/history/comparisons/all32Task8requirements27variants16classes/full eligible populations/coldancestry/jointgradients/15asset-years5,480dates/fund350 historical65-address/vintage remain required. Physical16GB/10GiBfloor fixed;55,439,818,752B MCM still requires authenticated tails AND batch/output streaming or offload and full recovery before deletion. Root alone integrates live sources, owns registrations/accounting/STATE/Git/external recovery and ONE numerical launcher. No credentials/pay/contact/trading/deployment/VPS systemd SSH.
'''
for p in (S/'STATE.md',B/'parallel-execution-2026-10-02/COORDINATION.md'):p.write_text(top+'\n---\n\n'+p.read_text())
R.put(C/'TOP17.json',{'time_utc':stamp,'main_parent_commit':'2ac9383c2086003e27f28391340832184f9a7221','top_sha256':hashlib.sha256(top.encode()).hexdigest(),'actual_final_union_capture_exit':0,'actual_capture_review_manifest':'2c7048e0515841ef31e5f7a5a69b3b43aca46e748e3a91c610f1d175b64883e0','actual_final_union_external_recovery':False,'current_source_full_recovery':True,'native_active':False,'paper_financial_fits':0,'next':'committed selected union verification and ONE fresh actual final remote/flat recovery before ONE engineering case'})
paths=[S/'STATE.md',B/'parallel-execution-2026-10-02/COORDINATION.md']
scopes=['financial-genuine-wrapper-recordfix-actual-recovery-review01-2026-10-04','financial-genuine-wrapper-recordfix-dependent-source-investigation01-2026-10-04','financial-genuine-wrapper-recordfix-dependent-source-review01-2026-10-04','financial-genuine-wrapper-recordfix-final-parent-review01-2026-10-04','financial-genuine-wrapper-recordfix-generated-verifier-review01-2026-10-04','financial-genuine-wrapper-recordfix-selection-review01-2026-10-04','financial-genuine-wrapper-root-recordfix-flat01-2026-10-04','financial-genuine-wrapper-root-recordfix-parent-adoption01-2026-10-04','financial-genuine-wrapper-root-recordfix-remote01-2026-10-04','financial-genuine-wrapper-root-recordfix-verifier-binding01-2026-10-04','financial-genuine-wrapper-root-recordfix-final-union01-2026-10-04','financial-genuine-wrapper-recordfix-final-union-capture-review01-2026-10-04','financial-genuine-wrapper-root-recordfix-final-review-snapshot01-2026-10-04','financial-genuine-wrapper-root-recordfix-final-remote01-2026-10-04','financial-genuine-wrapper-recordfix-final-union-recovery-preparation01-2026-10-04','financial-genuine-wrapper-recordfix-final-union-recovery-review01-2026-10-04']
for tree in [C,*[B/n for n in scopes]]:
 for root,dirs,files in os.walk(tree,followlinks=False):
  # Actual fresh bare Git and recovered duplicates are immutable local proof;
  # originals and their full opaque archives are preserved separately.
  dirs[:]=[n for n in dirs if not n.endswith('.git') and n not in ('selected','flat-source01','union-bytes01','__pycache__')]
  paths.extend(Path(root)/n for n in files)
  paths.extend(Path(root)/n for n in dirs if (Path(root)/n).is_symlink())
copied=C/'STAGE15_BUILDER01.py';assert not copied.exists();copied.write_bytes(Path(__file__).read_bytes());paths.append(copied)
stage=[]
for p in sorted(set(paths)):
 s=p.lstat();row={'path':p.relative_to(M).as_posix()}
 if stat.S_ISLNK(s.st_mode):row.update(kind='lexical-symlink',target=os.readlink(p))
 else:assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2;row.update(kind='file',bytes=s.st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 stage.append(row)
R.put(C/'STAGE15.json',{'scope':'explicit closed actual Source recovery/final-caller capture and independently frozen sources/reviews; no active namespaces','rows':stage,'count':len(stage),'native_started':False})
finite=[r['path'] for r in stage]+[(C/'STAGE15.json').relative_to(M).as_posix()]
for start in range(0,len(finite),80):subprocess.run(['git','add','-f','--',*finite[start:start+80]],check=True)
print(json.dumps({'staged':len(finite),'snapshot_regular':sum(r['kind']=='file' for r in rows),'snapshot_links':sum(r['kind']=='lexical-symlink' for r in rows),'snapshot_archive_bytes':len(archive),'snapshot_archive_sha256':hashlib.sha256(archive).hexdigest(),'native_or_network_started':False}))
