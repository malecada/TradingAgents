import datetime,hashlib,json,os,stat
from pathlib import Path
R=Path.cwd();NAME='eth-paper-real-data-end-to-end-resource-20261008-20';F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final20-2026-10-08';H=Path(__file__).resolve().parent
roots=[R/'research_runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/NAME,R/'research_artifacts/archive-dispatch-ethpilot-20261008-20']
fixed=['ROOT_LAUNCH02.stdout','ROOT_LAUNCH02.stderr','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ACTIVE_OBSERVATION01.json','EXEC_HANDLE02.json','launch-attempt01.json']
paths=set();dirs=set()
for root in roots:
 assert root.is_dir() and not root.is_symlink();dirs.add(root)
 for parent,children,files in os.walk(root,followlinks=False):
  for name in children:
   p=Path(parent)/name;assert not p.is_symlink();dirs.add(p)
  paths.update(Path(parent)/name for name in files)
for name in fixed:
 p=N/name;assert p.is_file(),p;paths.add(p)
rows=[]
for p in sorted(paths):
 before=p.lstat();assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and not p.is_symlink();data=p.read_bytes();after=p.lstat();fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_nlink');assert all(getattr(before,k)==getattr(after,k) for k in fields)
 rows.append({'path':str(p.relative_to(R)),'type':'regular','mode':format(stat.S_IMODE(before.st_mode),'04o'),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
result={'schema_version':1,'identity':NAME,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roots':[str(p.relative_to(R)) for p in roots],'files':len(rows),'body_bytes':sum(r['bytes'] for r in rows),'rows':rows,'directories':[{'path':str(p.relative_to(R)),'type':'directory','mode':format(stat.S_IMODE(p.stat().st_mode),'04o')} for p in sorted(dirs)],'qualification':'Original complete failed20 public increment roots plus explicit RootCLI/handle/closure/postlaunch controls. Original regular bodies read only as opaque hashes; metadata reviewed separately. Private transport/runtime/temp, unchanged source and original scientific stores excluded. Original modes are inventory facts, not a Gitarchive POSIX reconstruction promise. No deletion or external recovery established by selection.'}
(H/'SELECTION01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'files':len(rows),'body_bytes':result['body_bytes'],'selection_sha256':hashlib.sha256((H/'SELECTION01.json').read_bytes()).hexdigest()}))
