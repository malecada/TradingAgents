"""Metadata/stat only; never opens model, graph-array, or log bodies."""
from pathlib import Path
import hashlib,json,os,stat,shutil
from datetime import datetime,timezone
root=Path.cwd();out=root/'research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-physical-admission-2026-10-02'
sources=['tradingagents/research/onchain_replication/'+n for n in ('job.py','resources.py','workflow_storage.py','neural_resource.py')]+['tradingagents/research/lifecycle.py','tradingagents/research/admission.py']
pins=[]
for name in sources:
 p=root/name;b=p.read_bytes();pins.append({'path':name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
base=root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'
measurements=[]
for name in ('eth-paper-neighborhood-census-20260930-01','eth-paper-hub-edge-census-20260930-01','eth-paper-graph-resource-20260930-09','eth-paper-graph-resource-20260930-08'):
 directory=base/name
 if not (directory/'guard/final.json').is_file():raise ValueError('retained closed guard metadata missing')
 rows=[]
 for p in [directory,*sorted(directory.rglob('*'))]:
  s=p.lstat()
  if not (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)):raise ValueError('unexpected prior guard entry type')
  rows.append({'path':str(p.relative_to(root)),'kind':'directory' if stat.S_ISDIR(s.st_mode) else 'file','logical_bytes':s.st_size if stat.S_ISREG(s.st_mode) else 0,'allocated_bytes':s.st_blocks*512,'device':s.st_dev,'inode':s.st_ino})
 measurements.append({'name':name,'files':sum(r['kind']=='file' for r in rows),'directories':sum(r['kind']=='directory' for r in rows),'logical_file_bytes':sum(r['logical_bytes'] for r in rows),'allocated_bytes':sum(r['allocated_bytes'] for r in rows),'entries':rows})
mem={k:int(v.strip().split()[0])*1024 for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines()) if k in ('MemAvailable','MemTotal')}
v={'created_utc':datetime.now(timezone.utc).isoformat(),'sources':pins,'retained_guard_stat_observations':measurements,'fresh_host_snapshot':{**mem,'root_disk_free_bytes':shutil.disk_usage(root).free,'allowed_cpu_ids':sorted(os.sched_getaffinity(0)),'root_device':root.stat().st_dev,'allocation_unit_bytes':os.statvfs(root).f_frsize},'qualification':'Unreserved point-in-time metadata and allocated-file observations; not guard admission, whole-run bounds or input availability proof. No graph/model/log body read.'}
(out/'metadata01.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({'status':'PASS','source_pins':len(pins),'closed_guard_directories':len(measurements),'aggregate_allocated_bytes':sum(m['allocated_bytes'] for m in measurements),'empirical_execution':False}))
