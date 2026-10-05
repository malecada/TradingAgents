"""Only the actual failed helper increment; accepted R4 mechanics unchanged."""
from pathlib import Path
import hashlib,importlib.util,json,os,resource,shutil,sys
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources'
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01')
api=P/'recovery04.py'
assert hashlib.sha256(api.read_bytes()).hexdigest()=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
sys.path.insert(0,str(P))
spec=importlib.util.spec_from_file_location('accepted_r4',api);R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
resource.setrlimit(resource.RLIMIT_FSIZE,(R.FILE,R.FILE));assert shutil.disk_usage(F).free>=R.FLOOR
D=F/'financial-wrapper-serialized-prediction-final-direct02-2026-10-05'
assert not (D/'REMOTE_RECOVERY01.json').exists() and (D/'FAILED01.json').is_file()
assert json.loads((D/'ACTUAL_ROOT_EXIT01.json').read_bytes())['actual_root_exit_code']==1
Q=F/'financial-wrapper-serialized-prediction-failed-direct-capture03-2026-10-05';assert not os.path.lexists(Q);Q.mkdir(mode=0o700)
m=R.scan(D);R.put(Q/'archive-manifest.json',m);a=R.pack(D,m,Q/'failed-increment.tar.gz')
R.put(Q/'CAPTURE01.json',{'schema_version':1,'source_root':str(D),'archive':a,'regular_count':sum(r['kind']=='file' for r in m['members']),'typed_count':len(m['members']),'raw_git_included':True,'historical_stores_copied':False,'qualification':'Complete declared failed receiver tree at capture, original source/selection/failure/tool exit/partial bare Git names modes hashes. No selected successful recovery or numerical claim.'})
assert shutil.disk_usage(F).free>=R.FLOOR
print(json.dumps({'archive':a,'regular_count':sum(r['kind']=='file' for r in m['members']),'typed_count':len(m['members'])}))
