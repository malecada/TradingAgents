import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;R=Path.cwd();F=H.parent;D=F/'real-data-pilot-outcome21-scope01-2026-10-08';N=F/'real-data-pilot-final21-2026-10-08';p=D/'SELECTION01.json';raw=p.read_bytes();pin=hashlib.sha256(raw).hexdigest();assert pin=='62164022b84311c5986c690131bc93ed3ee6762d93b50456a98b5105b03aeb4d';s=json.loads(raw);name='eth-paper-real-data-end-to-end-resource-20261008-21';wf='db8a30b46d4a51935c063f6ab718cab337aca2e15be0d9c49460466aae02ca15'
roots=[f'research_runs/{name}',f'research_artifacts/onchain-paper-replication-2026-09-24/runs/{name}',f'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent/{name}','research_artifacts/archive-dispatch-ethpilot-20261008-21',f'research_artifacts/onchain_representations/{wf}/{name}',f'research_artifacts/onchain_compact_mcm/{wf}/{name}'];assert s['roots']==roots
files=set();dirs=set()
for root in roots:
 for parent,children,names in os.walk(R/root,followlinks=False):
  parent=Path(parent);assert not parent.is_symlink();dirs.add(str(parent.relative_to(R)))
  for child in children:assert not (parent/child).is_symlink()
  files.update(str((parent/n).relative_to(R)) for n in names)
fixed=['ROOT_LAUNCH01.stdout','ROOT_LAUNCH01.stderr','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ACTIVE_OBSERVATION01.json','EXEC_HANDLE01.json','launch-attempt01.json','ROOT_TERMINAL01.json']+[f'ACTIVE_OBSERVATION{i:02d}.json' for i in range(2,11)]+[f'DIAGNOSTIC_SAMPLE{i:02d}.json' for i in range(1,4)]
files.update(str((N/n).relative_to(R)) for n in fixed)
assert len(s['rows'])==len({x['path'] for x in s['rows']})==87 and files=={x['path'] for x in s['rows']}
assert len(s['directories'])==len(dirs)==31 and dirs=={x['path'] for x in s['directories']}
for row in s['rows']:
 p=R/row['path'];a=p.lstat();assert stat.S_ISREG(a.st_mode) and a.st_nlink==1 and not p.is_symlink() and row['type']=='regular' and format(stat.S_IMODE(a.st_mode),'04o')==row['mode'];body=p.read_bytes();b=p.lstat();assert all(getattr(a,k)==getattr(b,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink'));assert len(body)==row['bytes'] and hashlib.sha256(body).hexdigest()==row['sha256']
for row in s['directories']:
 p=R/row['path'];assert row['type']=='directory' and p.is_dir() and not p.is_symlink() and format(stat.S_IMODE(p.stat().st_mode),'04o')==row['mode']
assert sum(x['bytes'] for x in s['rows'])==s['body_bytes']==1090330
out=json.loads((H/'OUTCOME_REVIEW01.json').read_text());assert not any((Path('/proc')/pid).exists() for pid in out['pid_observation'])
guard=json.loads((R/roots[1]/'guard/final.json').read_text());assert not Path(guard['cgroup']).exists()
for k,v in out['evidence'].items():assert hashlib.sha256((R/k).read_bytes()).hexdigest()==v
supp=json.loads((H/'ARTIFACT_JOIN02.json').read_text())
for k,v in supp['evidence'].items():assert hashlib.sha256((R/k).read_bytes()).hexdigest()==v
result={'decision':'accepted-original-public-selection','identity':name,'selection':{'path':str((D/'SELECTION01.json').relative_to(R)),'sha256':pin,'files':87,'body_bytes':1090330,'directories':31},'outcome_review_sha256':hashlib.sha256((H/'OUTCOME_REVIEW01.json').read_bytes()).hexdigest(),'artifact_join_sha256':hashlib.sha256((H/'ARTIFACT_JOIN02.json').read_bytes()).hexdigest(),'checks':['exact six declared roots and20explicitRootfiles','complete current typed-name sets and unique rows','all original regular body hashes/lengths/modes with before-after inode metadata stability','all31directory modes','terminal/outcome/representation joins still exact','all4originalPIDs and cgroup absent'],'qualification':'Opaque public body preservation only.2048events and1023tail remain metadata, not binary semantic authentication. Original scientific stores/private transport/runtime/temp/unchanged sources excluded. No external recovery, POSIX reconstruction, global writer exclusion or deletion proof. Capture/returned recovery pending.'}
(H/'SELECTION_REVIEW03.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'sha256':hashlib.sha256((H/'SELECTION_REVIEW03.json').read_bytes()).hexdigest()}))
