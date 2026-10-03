"""Offline verification of actual failed recovery prefix; no retries/fetch."""
import hashlib,json,os,stat,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;MAIN=HERE.parents[3];OUT=HERE.parent/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03';REC=OUT/'outcome-recovery01';COMMIT='3841b46660c703d4202ab51c88cec8b09fe8751c'
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304;return p.read_bytes()
def git(*args):
 r=subprocess.run(['git','-c','remote.origin.promisor=false','-c','protocol.allow=never','-C',str(REC/'repository.git'),*args],env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'},capture_output=True,timeout=20);assert r.returncode==0 and len(r.stdout)<=4194304 and len(r.stderr)<=65536;return r.stdout
assert git('rev-parse','FETCH_HEAD').decode().strip()==COMMIT
rows=[]
for p in sorted((REC/'selected').rglob('*')):
 if p.is_dir():continue
 name=p.relative_to(REC/'selected').as_posix();b=read(p);assert b==read(MAIN/name)==git('show',COMMIT+':'+name);rows.append({'path':name,'bytes':len(b),'sha256':digest(b)})
assert len(rows)==79
members=list((REC/'collection').rglob('*'));assert len(members)==1 and members[0].name=='collection.json';assert read(members[0])==read(OUT/'collection01/collection.json');assert not (OUT/'REMOTE_OUTCOME_RECOVERY01.json').exists()
retention=json.loads(read(OUT/'OUTCOME_RETENTION01.json'));assert digest(read(OUT/'comparison-outcome01.tar.gz'))==retention['archive_sha256']=='0df30abe430dced727edec3687a49bad739e743d62290b7972e76a8ee5d8774d'
result={'schema_version':1,'status':'ACTUAL_REMOTE_PREFIX_VERIFIED_FULL_RECOVERY_FAILED','original_session':84635,'original_exit_code_reported_by_coordinator':1,'failure':'KeyError(bytes) in helper02 directory branch','remote_commit':COMMIT,'selected_blobs':rows,'selected_count':79,'restored_member_count':1,'restored_collection_sha256':digest(read(members[0])),'original_archive_unchanged':True,'complete_remote_recovery':False,'research_attempts_added':0,'reviewer_fetch_network_numeric_replay':False}
(HERE/'PARTIAL_READBACK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='selected_blobs'},sort_keys=True))
