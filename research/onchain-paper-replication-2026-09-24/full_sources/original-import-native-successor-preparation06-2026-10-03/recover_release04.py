"""Freshly recover exact root release/invocation evidence; no empirical replay."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path.cwd();COMMIT=sys.argv[1]
assert len(COMMIT)==40 and all(c in '0123456789abcdef' for c in COMMIT)
def call(args,cwd=ROOT):
 result=subprocess.run(['git',*args],cwd=cwd,capture_output=True,timeout=60)
 assert result.returncode==0 and max(len(result.stdout),len(result.stderr))<=4*1024**2
 return result.stdout
def sha(raw):return hashlib.sha256(raw).hexdigest()
branch='research/onchain-paper-replication-2026-09-24'
assert call(['ls-remote','origin','refs/heads/'+branch]).decode().split()[0]==COMMIT
out=HERE/'release-recovery01';out.mkdir(mode=0o700);repo=out/'repository.git'
call(['init','--bare',str(repo)]);call(['remote','add','origin',call(['remote','get-url','origin']).decode().strip()],repo)
call(['config','remote.origin.promisor','true'],repo);call(['config','remote.origin.partialclonefilter','blob:none'],repo)
call(['fetch','--depth=1','--filter=blob:none','origin',COMMIT],repo);assert call(['rev-parse','FETCH_HEAD'],repo).decode().strip()==COMMIT
names=['release01.json','launch_primary04.py','collect_primary05.py','REVIEW_PRIMARY_RELEASE04.md','REVIEW_REMOTE_PREPARATION_RECOVERY04.md','REMOTE_PREPARATION_RECOVERY01.json','PREPARATION_MANIFEST04.json','ROOT_LAUNCH_PREPARATION04.md','recover_release04.py'];rows=[]
for name in names:
 path=HERE/name;raw=call(['show',COMMIT+':'+str(path.relative_to(ROOT))],repo);assert raw==path.read_bytes()
 with (out/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 rows.append({'path':str(path.relative_to(ROOT)),'sha256':sha(raw),'bytes':len(raw)})
receipt={'schema_version':1,'status':'fresh_remote_root_release_bodies_verified','remote_commit':COMMIT,'selected_bodies':rows,'qualification':'Nine actual remote root release/review/recovery/invocation/retention bodies recovered separately, exact bytes/hash verified. Complete imported engineering source/input/gate/Git/allthreeoriginalfailedraw capsule was separately recovered and reviewed before release. Installedruntime and empiricalstores excluded. No new claim/job/native proof inferred.'}
with (HERE/'REMOTE_RELEASE_RECOVERY01.json').open('x') as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'status':receipt['status'],'remote_commit':COMMIT,'bodies':len(rows)}))
