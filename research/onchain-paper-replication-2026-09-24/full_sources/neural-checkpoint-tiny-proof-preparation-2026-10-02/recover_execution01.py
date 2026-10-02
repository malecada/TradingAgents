"""Fresh remote source and raw-component recovery, never replay."""
from datetime import datetime,timezone
import hashlib,json,os,resource,shutil,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OUT=HERE/'remote-execution-recovery01';BRANCH='research/onchain-paper-replication-2026-09-24'
NAMES=('retained-execution01.tar.gz','retained-execution01.json','execution-result01.json',
 'REVIEW_EXECUTION01.md','release02.json','source-manifest02.json','protocol01.json','native_launcher03.py',
 'oracle02.py','coordinator02.py','collect_execution01.py','collector01.log','outer-exit01.json','launch01.log',
 'REMOTE_SOURCE_HEAD02.json','REVIEW_NATIVE_RELEASE02.md','REVIEW_PROOF_SOURCE02.md','NATIVE_CORRECTION02.json')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def call(cmd,cwd):
 r=subprocess.run(cmd,cwd=cwd,capture_output=True,timeout=60)
 if r.returncode or max(len(r.stdout),len(r.stderr))>8*1024**2:raise RuntimeError('bounded remote command failed')
 return r.stdout

def main():
 resource.setrlimit(resource.RLIMIT_FSIZE,(8*1024**2,8*1024**2))
 assert shutil.disk_usage(ROOT).free>=10*1024**3
 head=call(['git','rev-parse','HEAD'],ROOT).decode().strip()
 assert call(['git','ls-remote','origin','refs/heads/'+BRANCH],ROOT).decode().split()[0]==head
 release=json.loads((HERE/'release02.json').read_bytes());selected=dict(release['source_files'])
 for name in NAMES:selected[str((HERE/name).relative_to(ROOT))]=digest((HERE/name).read_bytes())
 for name,pin in selected.items():assert digest(call(['git','show',head+':'+name],ROOT))==pin
 url=call(['git','remote','get-url','origin'],ROOT).decode().strip()
 OUT.mkdir(mode=0o700);repo=OUT/'repository.git'
 call(['git','init','--bare',str(repo)],ROOT);call(['git','remote','add','origin',url],repo)
 call(['git','config','remote.origin.promisor','true'],repo);call(['git','config','remote.origin.partialclonefilter','blob:none'],repo)
 call(['git','fetch','--depth=1','--filter=blob:none','origin',head],repo)
 assert call(['git','rev-parse','FETCH_HEAD'],repo).decode().strip()==head
 blobs={}
 for name,pin in sorted(selected.items()):
  raw=call(['git','show',head+':'+name],repo);assert digest(raw)==pin
  blobs[name]={'bytes':len(raw),'sha256':pin}
  if name in {str((HERE/n).relative_to(ROOT)) for n in NAMES}:
   with (OUT/Path(name).name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 inventory=json.loads((OUT/'retained-execution01.json').read_bytes())
 rows={('neural-checkpoint-comparison-20261002-01'+('' if row['path']=='.' else '/'+row['path'])):row for row in inventory['entries']}
 seen=set();files=dirs=body_bytes=0
 with tarfile.open(OUT/'retained-execution01.tar.gz','r|gz') as archive:
  for member in archive:
   assert member.name in rows and member.name not in seen;seen.add(member.name);row=rows[member.name];assert member.mode==row['mode']
   if row['kind']=='directory':assert member.isdir();dirs+=1
   else:
    assert member.isfile() and member.size==row['bytes']<4194304
    stream=archive.extractfile(member);assert stream is not None
    with stream:raw=stream.read(member.size+1)
    assert len(raw)==member.size and digest(raw)==row['sha256'];files+=1;body_bytes+=len(raw)
 assert seen==set(rows) and (files,dirs,body_bytes)==(245,37,7539340)
 result=json.loads((OUT/'execution-result01.json').read_bytes())
 assert result['parent_status']=='failed' and result['numeric_and_profile_components']=='passed' and result['retry'] is False
 report={'schema_version':1,'status':'fresh_remote_recovery_verified','identity':result['identity'],'remote_source_commit':head,
  'execution_source_commit':result['source_commit'],'retrieved_blob_count':len(blobs),'retrieved_blobs':blobs,
  'original_source_git_bodies_recovered':len(release['source_files']),'original_raw_members':len(seen),
  'original_raw_files':files,'original_raw_directories':dirs,'original_raw_body_bytes':body_bytes,
  'parent_status':'failed','numeric_and_profile_components':'passed','no_numeric_replay_or_import':True,
  'verified_utc':datetime.now(timezone.utc).isoformat(),
  'qualification':'Fresh shallow partial bare fetch from actual remote, all142 original selected Git source bodies plus selected closure/release/review blobs and all282 archived raw members verified by bytes/hash/mode without extraction/deserialization/replay. Installed uv runtime and empirical inputs are not remotely recovered. Failed outer parent and separately passed tiny components unchanged; no full-size capacity or financial proof.'}
 with (HERE/'REMOTE_EXECUTION_RECOVERY01.json').open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps({'status':report['status'],'source':head,'blobs':len(blobs),'original_source_bodies':142,'raw_members':len(seen)}))
if __name__=='__main__':main()
