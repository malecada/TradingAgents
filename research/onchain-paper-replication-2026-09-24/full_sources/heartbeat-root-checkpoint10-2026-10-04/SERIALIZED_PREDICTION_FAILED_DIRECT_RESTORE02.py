"""Restore exactly the two closed failed receiver increments using accepted R4."""
from pathlib import Path
import sys,json,hashlib,shutil,resource,os
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01');D=F/'financial-wrapper-serialized-prediction-final-direct03-2026-10-05';OUT=F/'financial-wrapper-serialized-prediction-failed-direct-restoration01-2026-10-05'
assert hashlib.sha256((P/'recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a';sys.path.insert(0,str(P));import recovery04 as R
resource.setrlimit(resource.RLIMIT_FSIZE,(R.FILE,R.FILE))
root=json.loads(R.read(D,'ACTUAL_ROOT_EXIT01.json'));assert root['actual_root_exit_code']==0
receipt=json.loads(R.read(D,'REMOTE_RECOVERY01.json'));assert receipt['remote_commit']=='0a12c9cc2442984c5d54e25842f18299a428af52' and receipt['selected_count']==47 and receipt['selected_logical_bytes']==6268031 and len(receipt['operations'])==149
assert all(x['actual_reaped_exit']==0 and x['cleanup_failures']==[] and x['actual_child_limits']=={'pid':x['pid'],'fsize':[4194304,4194304]} for x in receipt['operations'])
refs={r['path']:r for r in receipt['selected_blobs']}
cases=[('failed01','financial-wrapper-serialized-prediction-failed-direct-capture02-2026-10-05',36,47,'dd7959b74bb47929ad70f0a90ab532191f80a5ac80dd8a9bda06c29ebe91ac03','4ed334ae95d4013dde2d9964fb28bd6389db31cb08e6417fcfded0732da99b14'),('failed02','financial-wrapper-serialized-prediction-failed-direct-capture03-2026-10-05',81,92,'77dd1c93c4d89a56fb8813821a08850907c20437f6bacb328930210f4cf691a7','822b996b7020b04f7e32ddb6fbb1c250794de3695a44b8d9a556fbd542a0cdbe')]
assert not os.path.lexists(OUT) and shutil.disk_usage(F).free>=R.FLOOR;OUT.mkdir(mode=0o700);results=[]
for label,name,regular,typed,archive_pin,manifest_pin in cases:
 prefix='research/onchain-paper-replication-2026-09-24/full_sources/'+name
 paths={n:D/'selected'/prefix/n for n in ['failed-increment.tar.gz','archive-manifest.json','CAPTURE01.json']}
 for n,p in paths.items():
  b=R.read(p.parent,p.name);r=refs[p.relative_to(D/'selected').as_posix()];assert len(b)==r['bytes'] and R.digest(b)==r['sha256']
 m=json.loads(R.read(paths['archive-manifest.json'].parent,'archive-manifest.json'));capture=json.loads(R.read(paths['CAPTURE01.json'].parent,'CAPTURE01.json'))
 assert capture['regular_count']==regular and capture['typed_count']==typed and capture['archive']['sha256']==archive_pin and capture['archive']['manifest_sha256']==manifest_pin
 dest=OUT/label;dest.mkdir(mode=0o700);result=R.restore(paths['failed-increment.tar.gz'],capture['archive'],m,dest);assert result['regular_bodies']==regular and result['members']==typed
 results.append({'case':label,'original_source_root':capture['source_root'],'primitive':result,'original_failed_root_exit':1,'original_partial_git_included':True})
 assert shutil.disk_usage(F).free>=R.FLOOR
R.put(OUT/'RECOVERY01.json',{'schema_version':1,'status':'ACTUAL_BOTH_FAILED_DIRECT_BYTE_RECOVERY','remote_receipt_sha256':R.digest(R.read(D,'REMOTE_RECOVERY01.json')),'actual_root_exit_sha256':R.digest(R.read(D,'ACTUAL_ROOT_EXIT01.json')),'cases':results,'numerical_claim_started':False,'qualification':'Exactly the two declared original failed receiver trees recovered from actual remote archives. Both original Root1 dispositions, null and separate -9 stay unchanged. No POSIX/runtime-body/scientific-capacity or numerical release.'})
print(json.dumps({'cases':2,'regular':117,'typed':139,'recovery_sha256':R.digest(R.read(OUT,'RECOVERY01.json'))}))
