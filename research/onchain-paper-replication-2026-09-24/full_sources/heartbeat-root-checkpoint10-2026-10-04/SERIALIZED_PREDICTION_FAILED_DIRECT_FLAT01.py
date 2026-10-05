"""Fresh failed-helper byte restoration using unchanged accepted R4."""
from pathlib import Path
import sys,json,hashlib,shutil,resource,os
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01');D=F/'financial-wrapper-serialized-prediction-final-direct02-2026-10-05';OUT=F/'financial-wrapper-serialized-prediction-failed-direct-flat01-2026-10-05'
assert hashlib.sha256((P/'recovery04.py').read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a';sys.path.insert(0,str(P));import recovery04 as R
resource.setrlimit(resource.RLIMIT_FSIZE,(R.FILE,R.FILE))
root=json.loads(R.read(D,'ACTUAL_ROOT_EXIT01.json'));assert root['actual_root_exit_code']==0
receipt=json.loads(R.read(D,'REMOTE_RECOVERY01.json'));assert receipt['remote_commit']=='3ea5d7c2d0117f519fdd9cff3f9e6c78b5a60e69' and receipt['selected_count']==36 and receipt['selected_logical_bytes']==3360961 and len(receipt['operations'])==117
assert all(x['actual_reaped_exit']==0 and x['cleanup_failures']==[] and x['actual_child_limits']=={'pid':x['pid'],'fsize':[4194304,4194304]} for x in receipt['operations'])
refs={r['path']:r for r in receipt['selected_blobs']};prefix='research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-serialized-prediction-failed-direct-capture02-2026-10-05';paths={n:D/'selected'/prefix/n for n in ['failed-increment.tar.gz','archive-manifest.json','CAPTURE01.json']}
for n,p in paths.items():
 b=R.read(p.parent,p.name);r=refs[p.relative_to(D/'selected').as_posix()];assert len(b)==r['bytes'] and R.digest(b)==r['sha256']
m=json.loads(R.read(paths['archive-manifest.json'].parent,'archive-manifest.json'));capture=json.loads(R.read(paths['CAPTURE01.json'].parent,'CAPTURE01.json'))
assert capture['regular_count']==36 and capture['typed_count']==47 and capture['archive']['sha256']=='dd7959b74bb47929ad70f0a90ab532191f80a5ac80dd8a9bda06c29ebe91ac03' and capture['archive']['manifest_sha256']=='4ed334ae95d4013dde2d9964fb28bd6389db31cb08e6417fcfded0732da99b14'
assert not os.path.lexists(OUT) and shutil.disk_usage(F).free>=R.FLOOR;OUT.mkdir(mode=0o700);(OUT/'flat').mkdir(mode=0o700)
result=R.restore(paths['failed-increment.tar.gz'],capture['archive'],m,OUT/'flat');assert result['regular_bodies']==36 and result['members']==47
R.put(OUT/'RECOVERY01.json',{'schema_version':1,'status':'ACTUAL_FAILED_DIRECT_BYTE_RECOVERY','remote_receipt_sha256':R.digest(R.read(D,'REMOTE_RECOVERY01.json')),'actual_root_exit_sha256':R.digest(R.read(D,'ACTUAL_ROOT_EXIT01.json')),'primitive':result,'original_failed_root_exit':1,'original_partial_git_included':True,'numerical_claim_started':False,'qualification':'Actual complete declared original failed receiver bytes/names/modes via fresh remote archive. Original Root1 stays FAILED. No POSIX/runtime-body/full scientific capacity or numerical release.'})
assert shutil.disk_usage(F).free>=R.FLOOR
print(json.dumps({'regular':36,'typed':47,'recovery_sha256':R.digest(R.read(OUT,'RECOVERY01.json'))}))
