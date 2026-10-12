"""Verify actual three-body return using fixed receipts/raw outputs; no Git/network."""
import hashlib,json,os,stat
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full39-entry-preparation01-2026-10-12/final-metadata-return01'
sha=lambda b:hashlib.sha256(b).hexdigest();evidence={};checks=0
expected=json.loads((P/'ROOT_ACTUAL_EXPECTED01.json').read_text())
def ck(ok):
 global checks
 assert ok;checks+=1
def body(path):
 p=Path(path);before=p.lstat();ck(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=4*1024**2)
 b=p.read_bytes();after=p.lstat();ck(all(getattr(before,k)==getattr(after,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')))
 evidence[str(p.relative_to(R))]=sha(b);return b
load=lambda p:json.loads(body(p))
sr=load(P/'SOURCE_REVIEW01.json');ck(sha((P/'SOURCE_REVIEW01.json').read_bytes())=='ed0d8fe955bb258affa152c1b0810d546c401823f908573b453266bd55b01d3d')
receipt=load(D/'FINAL_METADATA_RETURN01.json');spec=load(D/'INPUT01.json');ops=load(D/'GIT_OPERATIONS01.json');source=expected['source']
ck(spec['source']==receipt['source']==receipt['actual_remote_head']==receipt['actual_fetch_head']==source)
ck(spec['files']==sr['actual_original_bodies'] and spec['prior_recovery']==sr['prior_recovery'] and receipt['prior_recovery']==sr['prior_recovery'])
ck(ops==receipt['operations'] and len(ops)==21)
names=['local_head','remote_get_url','bare_remote_get_url','remote_actual_branch_readback']
for i in range(3):names.extend([f'local_tree_join{i}',f'local_blob{i}'])
names.extend(['actual_external_commit_only_fetch','fetched_head_readback','local_commit_body','actual_external_commit_body'])
for i in range(3):names.extend([f'actual_external_selected_blob_fetch{i}',f'actual_external_blob_return{i}'])
names.append('final_local_head');ck([op['operation'] for op in ops]==names)
raw={}
for op in ops:
 ck(op['exit_code']==0)
 for kind in ('stdout','stderr'):
  b=body(D/(op['operation']+'.'+kind));ck(len(b)==op[kind+'_bytes'] and sha(b)==op[kind+'_sha256']);raw[op['operation']+'.'+kind]=b
for n in ('local_head','fetched_head_readback','final_local_head'):ck(raw[n+'.stdout'].decode().strip()==source)
remote=raw['remote_get_url.stdout'].decode().strip();ck(remote==receipt['actual_external_source']==raw['bare_remote_get_url.stdout'].decode().strip()=='git@github.com:malecada/TradingAgents.git')
ck(raw['remote_actual_branch_readback.stdout'].decode().split()==[source,'refs/heads/research/onchain-paper-replication-2026-09-24'])
commit=raw['actual_external_commit_body.stdout'];ck(commit==raw['local_commit_body.stdout'] and sha(commit)==receipt['commit_body_sha256']);ck(hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest()==source)
ck(len(receipt['returned'])==3)
for i,(ref,returned) in enumerate(zip(spec['files'],receipt['returned'],strict=True)):
 ck(returned['original']==ref and returned['returned_path']==str((D/f'actual_external_blob_return{i}.stdout').relative_to(R)))
 local=body(R/ref['path']);ck(len(local)==ref['bytes'] and sha(local)==ref['sha256'] and format(stat.S_IMODE((R/ref['path']).stat().st_mode),'04o')==ref['mode'])
 recovered=raw[f'actual_external_blob_return{i}.stdout'];ck(local==raw[f'local_blob{i}.stdout']==recovered)
 oid=hashlib.sha1(b'blob '+str(len(recovered)).encode()+b'\0'+recovered).hexdigest();ck(oid==returned['git_blob_oid'])
 mode='100755' if int(ref['mode'],8)&0o111 else '100644';ck(raw[f'local_tree_join{i}.stdout'].decode().strip()==f"{mode} blob {oid}\t{ref['path']}")
prior=load(R/spec['prior_recovery']['path']);ck(sha((R/spec['prior_recovery']['path']).read_bytes())==spec['prior_recovery']['sha256'])
bare=Path(receipt['existing_fresh_bare']);ck(str(bare)==prior['fresh_bare']==sr['existing_bare']);ck(bare.is_dir() and not bare.is_symlink() and bare.resolve()==bare and not os.path.lexists(bare/'objects/info/alternates') and receipt['no_alternates'] is True)
ck((bare/'FETCH_HEAD').read_text().split()[0]==source and 'bare = true' in (bare/'config').read_text())
r={'decision':'accepted','scope':'Actual external return of exactly three final39 public metadata bodies through explicitly reused accepted36 bare. Not a fresh bare or whole-tree preservation claim.','source':source,'operation_count':21,'regular_files':3,'checks':checks,'new_fresh_bare':False,'prior36_recovery_sha256':spec['prior_recovery']['sha256'],'originals_and_returned':receipt['returned'],'actual_receipt':{'path':str((D/'FINAL_METADATA_RETURN01.json').relative_to(R)),'sha256':evidence[str((D/'FINAL_METADATA_RETURN01.json').relative_to(R))]},'evidence':evidence,'helper_git_network_admission_native_numerical_execution':False,'limitations':['The existing36 bare was reused; only current remote branch/commit and three selected returned blobs are authenticated.','No archive reconstruction, historical store copy, credentials, installed runtime, physical reservation, memory fit or new empirical claim.','This review and its own postreturn metadata are outside the three returned bodies.']}
with (P/'RETURN_REVIEW01.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':'accepted','checks':checks,'sha256':sha((P/'RETURN_REVIEW01.json').read_bytes())}))
