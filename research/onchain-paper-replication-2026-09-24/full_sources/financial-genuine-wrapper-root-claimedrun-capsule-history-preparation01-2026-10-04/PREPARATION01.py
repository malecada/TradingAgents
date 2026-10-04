import hashlib,importlib.util,json,os,shutil,stat,subprocess,sys,time
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=B/'financial-genuine-wrapper-root-claimedrun-capsule-history-preparation01-2026-10-04'
OLD=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-01');NEW=P/'source';SOURCE='649fb8a11089524aaef7843dffeeb90a3a55ca17';ID='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'
V=B/'financial-genuine-wrapper-claimedrun-history-copy-admission-review01-2026-10-04';A=B/'financial-genuine-wrapper-recordfix-failed-scope-actual-recovery-review01-2026-10-04'
assert hashlib.sha256((A/'MANIFEST03.json').read_bytes()).hexdigest()=='09113794673e1e4ff3016bf545482a9c2d40a23a3945dd2e55590944aeb24f40'
assert hashlib.sha256((V/'CLAIM_COPY_SPEC01.json').read_bytes()).hexdigest()=='2857d64fd1b90bd3787c566051d6e52e093912ef9afb441e1433fb6b62b06545'
assert hashlib.sha256((V/'GIT_ANCESTRY_SPEC01.json').read_bytes()).hexdigest()=='45883032094fb2f2033056755403c08cc12783835bdfa3f2ea78194bbfb6ebee'
assert not os.path.lexists(P) and not os.path.lexists(D);assert shutil.disk_usage(B).free>=10*1024**3
D.mkdir(mode=0o700);(D/'PREPARATION01.py').write_bytes(Path(__file__).read_bytes())
RPATH=B/'held-consumer-final-recovery-preparation04-2026-10-03';sys.path.insert(0,str(RPATH));import recovery04 as R
assert hashlib.sha256((RPATH/'recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
baseline=json.loads(R.read(B/'financial-genuine-wrapper-root-recordfix-failed-scope-capture01-2026-10-04','source-manifest.json'));R.same(OLD,baseline)
spec=json.loads(R.read(V,'CLAIM_COPY_SPEC01.json'));git_spec=json.loads(R.read(V,'GIT_ANCESTRY_SPEC01.json'));calls=[]
def git(args,cwd=M):
 q=subprocess.run(['git','-c','core.hooksPath=/dev/null','-c','gc.auto=0',*args],cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'})
 assert len(q.stdout)<=4*1024**2 and len(q.stderr)<=65536 and q.returncode==0
 calls.append({'args':args,'exit':q.returncode,'stdout_bytes':len(q.stdout),'stderr_bytes':len(q.stderr),'stdout_sha256':R.digest(q.stdout),'stderr_sha256':R.digest(q.stderr)})
 return q.stdout
intent={'pid':os.getpid(),'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'old_root':str(OLD),'new_root':str(NEW),'old_source':SOURCE,'historical_spent_identity':ID,'new_numeric_identity_not_registered':'financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01','full_failed_scope_recovery_review':'09113794673e1e4ff3016bf545482a9c2d40a23a3945dd2e55590944aeb24f40','generator_efcba9d1_invoked':False,'new_claim_or_admission':False,'scope':'ONE fresh ordinary standalone source clone and exact authenticated closed failed history preservation. Original source/caller/job/Owner remains immutable; no scientific checkpoint or future execution authority.'}
R.put(D/'INTENT01.json',intent)
P.mkdir(mode=0o700);assert P.resolve()==P and stat.S_IMODE(P.stat().st_mode)==0o700
git(['clone','--no-hardlinks','str-placeholder'],M) if False else None
git(['clone','--no-hardlinks',str(OLD),str(NEW)])
assert (NEW/'.git').is_dir() and not (NEW/'.git').is_symlink() and not (NEW/'.git/objects/info/alternates').exists()
assert git(['rev-parse','HEAD'],NEW).decode().strip()==SOURCE
lines=git(['rev-list','--parents',SOURCE],NEW).decode().splitlines();assert lines==git_spec['ancestry_lines']
for row in git_spec['objects']:
 raw=git(['cat-file',row['type'],row['oid']],NEW)
 assert len(raw)==row['bytes'] and R.digest(raw)==row['content_sha256']
 assert hashlib.sha1(row['type'].encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['oid']
tree=git(['ls-tree','-r','-z',SOURCE],NEW);tracked=[]
for item in tree.split(b'\0')[:-1]:
 left,n=item.split(b'\t',1);mode,kind,oid=left.decode().split();name=n.decode();raw=R.read(NEW,name)
 assert kind=='blob' and R.read(OLD,name)==raw and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid
 assert stat.S_IMODE((OLD/name).lstat().st_mode)==stat.S_IMODE((NEW/name).lstat().st_mode)
 assert (OLD/name).lstat().st_ino!=(NEW/name).lstat().st_ino
 tracked.append({'path':name,'git_mode':mode,'git_object':oid,'sha256':R.digest(raw)})
assert len(tracked)==325
ledger=NEW/'research_runs';ledger.mkdir(mode=stat.S_IMODE((OLD/'research_runs').stat().st_mode));os.chmod(ledger,stat.S_IMODE((OLD/'research_runs').stat().st_mode))
for row in spec['members']:
 dst=NEW/row['destination_relative_path'];src=Path(row['origin']);assert src.resolve()==src
 if row['kind']=='directory':dst.mkdir(mode=row['mode']);os.chmod(dst,row['mode'])
 else:
  raw=R.read(src.parent,src.name);assert len(raw)==row['bytes']and R.digest(raw)==row['sha256']
  with R.new_file(dst) as fd:
   off=0
   while off<len(raw):n=os.write(fd,raw[off:]);assert n>0;off+=n
   os.fsync(fd)
  os.chmod(dst,row['mode']);assert R.read(dst.parent,dst.name)==raw
 assert stat.S_IMODE(dst.lstat().st_mode)==row['mode']
assert list((ledger/ID/'outputs').iterdir())==[]
lock_raw=R.read(OLD/'research_runs','.lock');assert lock_raw==b''
with R.new_file(ledger/'.lock') as fd:os.fsync(fd)
os.chmod(ledger/'.lock',stat.S_IMODE((OLD/'research_runs/.lock').lstat().st_mode))
verify_path=NEW/'tradingagents/research/verify.py';assert R.digest(R.read(verify_path.parent,verify_path.name))=='3a45746a388307d1b375c885bb2fd7a22c2a60f139df714d2bbe98906d57d7eb'
module_spec=importlib.util.spec_from_file_location('actual_claim_history_verifier',verify_path);v=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(v)
claim=v.verify_claim(ledger/ID);run=v.verify_run(ledger/ID);assert claim==json.loads(R.read(OLD/'research_runs'/ID,'claim.json')) and run['status']=='failed'
assert {p.name for p in ledger.iterdir()if not p.name.startswith('.')}=={ID}
assert not any(n=='numpy' or n.startswith('numpy.')or n=='torch'or n.startswith('torch.')or n=='scipy'or n.startswith('scipy.')or n=='pandas'or n.startswith('pandas.')for n in sys.modules)
R.same(OLD,baseline)
R.put(D/'RELOCATION01.json',{'old_root':str(OLD),'new_root':str(NEW),'same_global_spent_claim':ID,'copied_claim_sha256':'4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','copied_failed_sha256':'35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450','copied_relative_claim_tree':spec['members'],'literal_historical_absolute_paths_unchanged':True,'historical_owner_or_job_runtime_authority_transferred':False,'scientific_checkpoint_present_or_relocated':False,'new_current_source':SOURCE,'new_corrected_source_or_gate':None,'actual_cumulative19_admission':None,'actual_new_identity_registration':None,'actual_new_caller_or_native_release':None})
R.put(D/'READBACK01.json',{'status':'ACTUAL_ORIGINAL_SOURCE_AND_CLOSED_HISTORY_PREPARED_NOT_RELEASED','original_source':SOURCE,'new_current_source_before_correction':SOURCE,'all_tracked_original_bodies_modes':tracked,'tracked':325,'authenticated_original_git_objects':len(git_spec['objects']),'original_git_ancestry_commits':len(lines),'complete_copied_claim_nodes':4,'copied_regular_claim_files':2,'copied_claim_bytes':54951,'copied_empty_outputs':True,'sibling_lock_preserved':True,'genuine_actual_destination_verified_claim_identity':claim['experiment_id'],'genuine_actual_destination_verify_run':run,'destination_unique_spent_claims':1,'global_unique_spent_claims':1,'current_highest_actual_budget':18,'original_whole_source_unchanged':True,'original_source_manifest_sha256':'c00c9722b1f0fa3956e339a4f4a29edd4b41ff5f6b361ec05fcc9f1149c54d1b','new_wrapper_still_original_e2_not_released':True,'unsafe_handoff_generator_invoked':False,'new_claim_or_numerical_or_admission':False,'full_new_source_recovery':False,'free_after':shutil.disk_usage(B).free,'git_calls':calls})
assert shutil.disk_usage(B).free>=10*1024**3
print(json.dumps({'actual_new_root':str(NEW),'original_current_source':SOURCE,'tracked325_verified':True,'actual_historical_spent_claims':1,'new_claim_or_numeric':False,'new_source_correction_or_19_admission':False}))
